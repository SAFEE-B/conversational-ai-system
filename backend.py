import os
import re
import asyncio
from typing import List, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from llama_cpp import Llama


# ---- Shared LLM setup (same logic as main.py) ----


def load_config() -> dict:
    load_dotenv()
    model_path = os.getenv("MODEL_PATH", "models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf")
    n_ctx = int(os.getenv("N_CTX", "4096"))
    n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))

    return {
        "model_path": model_path,
        "n_ctx": n_ctx,
        "n_gpu_layers": n_gpu_layers,
    }


def create_model(config: dict) -> Llama:
    model_path = config["model_path"]

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found at '{model_path}'. "
            "Please download a Qwen GGUF model and update MODEL_PATH in .env."
        )

    print(f"[backend] Loading model from: {model_path}")
    llm = Llama(
        model_path=model_path,
        n_ctx=config["n_ctx"],
        n_gpu_layers=config["n_gpu_layers"],
        verbose=True,
    )
    return llm


def build_system_prompt() -> str:
    from main import build_system_prompt as _build  # reuse exact same prompt

    return _build()


def format_messages(history: List[Tuple[str, str]], system_prompt: str) -> str:
    from main import format_messages as _fmt  # reuse exact same formatting

    return _fmt(history, system_prompt)


def extract_first_question(raw_reply: str) -> str:
    """
    Same post-processing logic as in main.py: keep only the first question.
    """
    question = raw_reply.strip()
    q_index = question.find("?")
    if q_index != -1:
        question = question[: q_index + 1]
    if q_index == -1:
        for sep in [".", "!", "\n"]:
            s_index = question.find(sep)
            if s_index != -1:
                question = question[: s_index + 1]
                break
    return question.strip()


# ---- Helper for de-duplicating questions ----


def normalize_question(text: str) -> str:
    """
    Normalize question text to detect near-duplicates.
    Strips numbering and boilerplate prefixes and lowercases.
    """
    s = text.strip().lower()
    # Remove our own "from a different angle..." prefix if present
    s = re.sub(r"^from a different angle( on [^,]+)?,\s*", "", s)
    # Drop leading numbering like "1." or "2)" or "3 -"
    s = re.sub(r"^\d+[\).\-\s]+", "", s)
    # Strip trailing punctuation
    s = s.rstrip(" ?!.")
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s


# ---- FastAPI app & WebSocket endpoint ----


app = FastAPI(title="AI Interview Backend", version="0.1.0")

llm: Llama | None = None
# Base system prompt shared across all connections. Each WebSocket
# connection can further specialize this with a user-selected topic.
base_system_prompt: str = ""
llm_lock = asyncio.Lock()


@app.on_event("startup")
def startup_event() -> None:
    global llm, base_system_prompt
    config = load_config()
    llm = create_model(config)
    base_system_prompt = build_system_prompt()
    print("[backend] Model and system prompt initialized.")


@app.get("/")
async def index() -> FileResponse:
    """
    Serve the frontend HTML page.
    """
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    return FileResponse(frontend_path)


@app.get("/api/health")
async def health() -> dict:
    """
    Simple healthcheck endpoint for monitoring / readiness.
    """
    return {
        "status": "ok",
        "model_loaded": llm is not None,
        "prompt_loaded": bool(base_system_prompt),
    }


@app.post("/api/chat")
async def chat_once(payload: dict) -> dict:
    """
    Non-streaming, single-turn chat endpoint mainly for testing via REST/Postman.

    Request JSON:
    - "history": list of {"role": "candidate"|"interviewer", "content": "..."} items (optional)
    - "message": latest candidate message (required)
    - "topic": optional topic string
    """
    from time import perf_counter

    assert llm is not None

    raw_history = payload.get("history") or []
    message = (payload.get("message") or "").strip()
    topic = (payload.get("topic") or "").strip()

    history: List[Tuple[str, str]] = []
    for item in raw_history:
        role = (item.get("role") or "").strip()
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if role.lower() == "candidate":
            history.append(("Candidate", content))
        elif role.lower() == "interviewer":
            history.append(("Interviewer", content))

    system_prompt = base_system_prompt
    if topic:
        topic_clause = (
            f"Additional constraint: The interview topic is '{topic}'.\n"
            f"- You MUST only ask questions that are directly about this topic and its very closely related subtopics.\n"
            f"- Do NOT ask generic AI/ML questions.\n"
            f"- If you are unsure, prefer asking how this topic applies in different real-world scenarios."
        )
        system_prompt = base_system_prompt + "\n\n" + topic_clause

    if message:
        history.append(("Candidate", message))

    prompt_str = format_messages(history, system_prompt)

    try:
        t0 = perf_counter()
        async with llm_lock:
            output = llm(
                prompt_str,
                max_tokens=256,
                temperature=0.4,
                top_p=0.9,
                stop=["Candidate:", "System:"],
            )
        elapsed = perf_counter() - t0
    except Exception as e:  # noqa: BLE001
        return {
            "error": str(e),
            "history": [{"role": r, "content": c} for (r, c) in history],
        }

    raw_reply = output["choices"][0]["text"].strip()
    question = extract_first_question(raw_reply)

    history.append(("Interviewer", question))

    return {
        "question": question,
        "latency_seconds": elapsed,
        "history": [{"role": r, "content": c} for (r, c) in history],
    }


@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for conversational AI interview.

    Protocol (JSON over WebSocket):
    - Client sends: {"message": "<candidate text>"}
      - Special case: first message can be empty or a greeting; server responds with opening question.
      - To end: client sends message that is exactly "exit" or "quit" (case-insensitive).
    - Server responds after each client message with:
      {"role": "interviewer", "message": "<single AI/ML question>"}

    Conversation state (history) is kept per WebSocket connection only.
    """
    await websocket.accept()
    history: List[Tuple[str, str]] = []
    asked_questions: set[str] = set()

    # Each WebSocket connection keeps its own specialized system prompt
    # that can depend on the user-selected topic.
    system_prompt = base_system_prompt

    try:
        while True:
            data = await websocket.receive_json()
            user_message = (data.get("message") or "").strip()
            topic = (data.get("topic") or "").strip()

            # If a topic is provided and this is the first turn,
            # specialize the system prompt for this connection.
            if topic and not history:
                topic_clause = (
                    f"Additional constraint: The interview topic is '{topic}'.\n"
                    f"- You MUST only ask questions that are directly about this topic and its very closely related subtopics.\n"
                    f"- Do NOT ask generic AI/ML questions.\n"
                    f"- If you are unsure, prefer asking how this topic applies in different real-world scenarios."
                )
                system_prompt = base_system_prompt + "\n\n" + topic_clause

                # Seed the conversation once per connection after topic selection
                history.append(
                    (
                        "Candidate",
                        f"Hi, I'm ready to start an interview focused on '{topic}'. Please begin.",
                    )
                )

            if user_message.lower() in {"exit", "quit"}:
                await websocket.send_json(
                    {
                        "role": "interviewer",
                        "message": "That's all for today. Thank you for your time, and good luck with your preparation.",
                    }
                )
                await websocket.close()
                break

            if user_message:
                history.append(("Candidate", user_message))

            # Build prompt and stream interviewer question token by token.
            prompt_str = format_messages(history, system_prompt)

            # Find the most recent interviewer question, if any, so we can
            # avoid sending the exact same text twice in a row.
            last_interviewer_question = None
            for role, content in reversed(history):
                if role == "Interviewer":
                    last_interviewer_question = content
                    break
            assert llm is not None

            buffer = ""
            last_sent = 0

            try:
                async with llm_lock:
                    # llama_cpp provides a normal (sync) generator when stream=True,
                    # so we iterate with a standard for-loop inside this async function.
                    for chunk in llm(
                        prompt_str,
                        max_tokens=256,
                        temperature=0.4,
                        top_p=0.9,
                        stop=["Candidate:", "System:"],
                        stream=True,
                    ):
                        token = chunk["choices"][0]["text"]
                        if not token:
                            continue

                        buffer += token
                        q_index = buffer.find("?")
                        limit = q_index + 1 if q_index != -1 else len(buffer)

                        delta = buffer[last_sent:limit]
                        if delta:
                            await websocket.send_json(
                                {
                                    "role": "interviewer",
                                    "delta": delta,
                                    "done": False,
                                }
                            )
                            last_sent = limit

                        if q_index != -1:
                            # We have the first full question; stop streaming more tokens.
                            break
            except Exception as e:  # noqa: BLE001
                await websocket.send_json(
                    {
                        "role": "system",
                        "error": str(e),
                        "done": True,
                    }
                )
                await websocket.close()
                break

            final_question = buffer[:last_sent].strip()
            if not final_question:
                final_question = extract_first_question(buffer)

            # If the model still repeated the last interviewer question exactly,
            # lightly rewrite the question text so the user does not see the
            # exact same string twice in a row.
            if last_interviewer_question and final_question == last_interviewer_question:
                if topic:
                    final_question = (
                        f"From a different angle on {topic}, "
                        + last_interviewer_question
                    )
                else:
                    final_question = (
                        "From a different angle, " + last_interviewer_question
                    )

            # If the base question text has already been asked in this session,
            # synthesize a different-style follow-up so the user does not see
            # the same semantic question repeatedly.
            base_q = normalize_question(final_question)
            if base_q:
                if base_q in asked_questions:
                    if topic:
                        final_question = (
                            f"Thinking about a real-world application of {topic}, "
                            "can you describe a practical system where these ideas are used and "
                            "explain the main design trade-offs?"
                        )
                    else:
                        final_question = (
                            "Can you describe a real-world project where you applied these ideas "
                            "and discuss the main design trade-offs?"
                        )
                    base_q = normalize_question(final_question)
                asked_questions.add(base_q)

            history.append(("Interviewer", final_question))

            # Send a final "done" message with the full question text
            await websocket.send_json(
                {
                    "role": "interviewer",
                    "message": final_question,
                    "done": True,
                }
            )

    except WebSocketDisconnect:
        # Client disconnected; nothing more to do.
        return

