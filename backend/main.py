import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from conversation_manager import ConversationManager
from llm_engine import LLMEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
llm_engine: LLMEngine = None
conversation_manager: ConversationManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_engine, conversation_manager
    model_path = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    try:
        llm_engine = LLMEngine(model_path=model_path)
        logger.info("LLM Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Engine: {e}")

    conversation_manager = ConversationManager(max_history=10)
    yield
    logger.info("Shutting down gracefully.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/sessions")
async def list_sessions():
    """List all active sessions with metadata for the frontend sidebar."""
    return {"sessions": conversation_manager.list_sessions()}

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Return the display history (user + assistant messages) for a given session."""
    if session_id not in conversation_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": conversation_manager.get_display_history(session_id)}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its history."""
    if session_id not in conversation_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    conversation_manager.delete_session(session_id)
    return {"deleted": session_id}

# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # The first message from the client must carry the session_id (or null for a new one).
    try:
        init_raw = await websocket.receive_text()
        init_payload = json.loads(init_raw)
    except Exception:
        await websocket.close()
        return

    requested_sid = init_payload.get("session_id")  # may be None
    session_id = conversation_manager.create_session(session_id=requested_sid)

    # Acknowledge with the resolved session_id so the client knows which to persist
    await websocket.send_json({"type": "session_init", "session_id": session_id})
    logger.info(f"WS connected. Session: {session_id} (requested: {requested_sid})")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                msg_type = payload.get("type")

                if msg_type == "reset":
                    conversation_manager.reset_session(session_id)
                    await websocket.send_json({"type": "system", "content": "Session reset."})
                    continue

                if msg_type == "message":
                    content = payload.get("content", "").strip()
                    if not content:
                        continue

                    conversation_manager.add_user_message(session_id, content)
                    messages = conversation_manager.get_messages(session_id)

                    full_response = ""
                    await websocket.send_json({"type": "start"})

                    try:
                        async for token in llm_engine.stream_chat(messages):
                            full_response += token
                            await websocket.send_json({"type": "token", "content": token})

                        await websocket.send_json({"type": "end"})
                        conversation_manager.add_assistant_message(session_id, full_response)

                    except Exception as e:
                        logger.error(f"Generation error: {e}")
                        await websocket.send_json({"type": "error", "content": "Sorry, I encountered an error generating a response."})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON format."})

    except WebSocketDisconnect:
        logger.info(f"WS disconnected. Session: {session_id}")
        # NOTE: We intentionally keep the session alive in memory so the client
        # can reconnect and continue the conversation.
