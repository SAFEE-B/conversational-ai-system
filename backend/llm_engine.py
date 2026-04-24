import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llama_cpp import Llama

class LLMEngine:
    def __init__(self, model_path: str):
        print(f"Loading model from {model_path}...")
        self.llm = Llama(
            model_path=model_path,
            n_threads=max(1, os.cpu_count() - 1),
            n_ctx=4096,
            verbose=False,
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
        # Created lazily on first call so it binds to the correct running event loop.
        self._lock: asyncio.Lock | None = None

    async def stream_chat(self, messages: list):
        """
        Asynchronously streams the chat completion response to avoid blocking the event loop.
        Concurrent callers queue up behind _lock so only one generation runs at a time.
        """
        # Lazy init: Lock must be created inside a running event loop.
        if self._lock is None:
            self._lock = asyncio.Lock()

        loop = asyncio.get_running_loop()

        async with self._lock:
            queue: asyncio.Queue = asyncio.Queue()

            def run_generation():
                try:
                    response = self.llm.create_chat_completion(
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=512,
                    )
                    for chunk in response:
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            loop.call_soon_threadsafe(queue.put_nowait, delta['content'])
                except Exception as e:
                    loop.call_soon_threadsafe(queue.put_nowait, {"error": str(e)})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            # Await the executor future so exceptions from run_generation are surfaced
            # and the lock is never left held indefinitely on thread failure.
            fut = loop.run_in_executor(self.executor, run_generation)

            try:
                while True:
                    token = await queue.get()
                    if token is None:
                        break
                    if isinstance(token, dict) and "error" in token:
                        raise RuntimeError(token["error"])
                    yield token
            finally:
                # Ensure the worker thread is always joined, even if the caller
                # breaks out of the async for early (e.g. WebSocket disconnect).
                await fut
