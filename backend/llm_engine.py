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
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def stream_chat(self, messages: list):
        """
        Asynchronously streams the chat completion response to avoid blocking the event loop.
        """
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        
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
                        # Use call_soon_threadsafe to put items in the queue from the worker thread
                        loop.call_soon_threadsafe(queue.put_nowait, delta['content'])
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, {"error": str(e)})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None) # EOF marker
                
        # Start generation in a separate thread
        loop.run_in_executor(self.executor, run_generation)
        
        # Yield tokens as they arrive in the queue
        while True:
            token = await queue.get()
            if token is None:
                break
            if isinstance(token, dict) and "error" in token:
                raise RuntimeError(token["error"])
            yield token
