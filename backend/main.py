import json
import logging
import asyncio
import base64
import os
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from conversation_manager import ConversationManager
from llm_engine import LLMEngine
from voice_engine import ASREngine, TTSEngine
from retrieval.retriever import DocumentRetriever
from tool_orchestrator import ToolOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
llm_engine: LLMEngine = None
conversation_manager: ConversationManager = None
asr_engine: ASREngine = None
tts_engine: TTSEngine = None
retriever: DocumentRetriever = None
orchestrator: ToolOrchestrator = None

# Voice jobs are CPU-heavy; keep the WebSocket event loop responsive.
voice_executor = ThreadPoolExecutor(max_workers=4)

# ─── Path configuration (from env or sensible defaults) ──────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", os.path.join(_BASE_DIR, "..", "chroma_db"))
_CRM_DB_PATH = os.environ.get("CRM_DB_PATH", os.path.join(_BASE_DIR, "..", "crm.db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_engine, conversation_manager, asr_engine, tts_engine, retriever, orchestrator

    model_path = os.environ.get("MODEL_PATH", "models/qwen2.5-0.5b-instruct-q4_k_m.gguf")
    try:
        llm_engine = LLMEngine(model_path=model_path)
        logger.info("LLM Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Engine: {e}")

    conversation_manager = ConversationManager(max_history=10)

    # RAG retriever — loads embedding model + connects to ChromaDB
    try:
        retriever = DocumentRetriever(chroma_persist_dir=_CHROMA_DIR, top_k=3)
        retriever.load()
        logger.info("RAG Retriever initialized successfully.")
    except Exception as e:
        logger.warning(f"RAG Retriever not available (run index_documents.py first): {e}")
        retriever = None

    # Tool Orchestrator — pharmacy tools (CRM, drug interaction, dosage, med info)
    try:
        orchestrator = ToolOrchestrator(crm_db_path=_CRM_DB_PATH)
        logger.info("Tool Orchestrator initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Tool Orchestrator: {e}")
        orchestrator = None

    # Voice engines: local ASR + local TTS (CPU pipeline).
    try:
        asr_engine = ASREngine(model_dir="models/vosk-model-en-us-daanzu-20200905")
        logger.info("ASR Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize ASR Engine: {e}")

    try:
        tts_engine = TTSEngine(
            onnx_path="models/piper-voices/en/en_US/ryan/low/en_US-ryan-low.onnx"
        )
        logger.info("TTS Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize TTS Engine: {e}")
    yield
    logger.info("Shutting down gracefully.")


async def _enrich_message(user_content: str, session_id: str):
    """
    Run RAG retrieval and tool orchestration concurrently before LLM generation.
    Returns (rag_context_str, tool_name, tool_result_str).
    All three operations complete before the LLM starts — preserves streaming.
    """
    rag_task = asyncio.create_task(_rag_retrieve(user_content))
    tool_task = asyncio.create_task(_tool_dispatch(user_content, session_id))

    rag_context, (tool_name, tool_result_text) = await asyncio.gather(rag_task, tool_task)
    return rag_context, tool_name, tool_result_text


async def _rag_retrieve(query: str) -> str:
    if retriever is None or not retriever.is_ready():
        return ""
    try:
        chunks = retriever.retrieve(query)
        return retriever.format_context(chunks)
    except Exception as e:
        logger.warning(f"RAG retrieval error: {e}")
        return ""


async def _tool_dispatch(message: str, session_id: str):
    if orchestrator is None:
        return (None, "")
    try:
        tool_name, tool_result = await orchestrator.process(message, session_id)
        if tool_name and tool_result:
            result_text = orchestrator.format_tool_result(tool_name, tool_result)
            return (tool_name, result_text)
        return (None, "")
    except Exception as e:
        logger.warning(f"Tool dispatch error: {e}")
        return (None, "")

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

                    # Enrich: RAG retrieval + tool call (concurrent, before LLM starts)
                    rag_context, tool_name, tool_result_text = await _enrich_message(content, session_id)
                    messages = conversation_manager.build_augmented_messages(
                        session_id,
                        rag_context=rag_context,
                        tool_name=tool_name or "",
                        tool_result_text=tool_result_text,
                    )

                    full_response = ""
                    await websocket.send_json({"type": "start"})
                    if tool_name:
                        await websocket.send_json({"type": "tool_used", "tool": tool_name})

                    try:
                        async for token in llm_engine.stream_chat(messages):
                            full_response += token
                            await websocket.send_json({"type": "token", "content": token})

                        await websocket.send_json({"type": "end"})
                        conversation_manager.add_assistant_message(session_id, full_response)

                    except Exception as e:
                        logger.error(f"Generation error: {e}")
                        await websocket.send_json({"type": "error", "content": "Sorry, I encountered an error generating a response."})

                if msg_type in ("voice", "voice_message"):
                    if asr_engine is None or tts_engine is None:
                        await websocket.send_json(
                            {"type": "error", "content": "Voice engines not initialized on the server."}
                        )
                        continue

                    audio_b64 = payload.get("audio_base64")
                    input_ext = payload.get("input_ext", "webm")
                    if not audio_b64:
                        await websocket.send_json({"type": "error", "content": "Missing audio_base64."})
                        continue

                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                    except Exception:
                        await websocket.send_json({"type": "error", "content": "Invalid base64 audio."})
                        continue

                    loop = asyncio.get_running_loop()
                    try:
                        transcript = await loop.run_in_executor(
                            voice_executor,
                            asr_engine.transcribe_audio_bytes,
                            audio_bytes,
                            input_ext,
                        )
                    except Exception as e:
                        logger.error(f"ASR error: {e}")
                        await websocket.send_json(
                            {"type": "error", "content": "Sorry, I could not transcribe your audio."}
                        )
                        continue

                    transcript = (transcript or "").strip()
                    if not transcript:
                        await websocket.send_json({"type": "error", "content": "No speech detected in the audio."})
                        continue

                    conversation_manager.add_user_message(session_id, transcript)
                    await websocket.send_json({"type": "voice_transcript", "content": transcript})

                    # Enrich: RAG retrieval + tool call (concurrent, before LLM starts)
                    rag_context, tool_name, tool_result_text = await _enrich_message(transcript, session_id)
                    messages = conversation_manager.build_augmented_messages(
                        session_id,
                        rag_context=rag_context,
                        tool_name=tool_name or "",
                        tool_result_text=tool_result_text,
                    )
                    if tool_name:
                        await websocket.send_json({"type": "tool_used", "tool": tool_name})

                    full_response = ""
                    tts_buffer = ""
                    audio_seq = 0

                    async def _tts_and_send(seq: int, chunk_text: str):
                        try:
                            audio_bytes_out = await loop.run_in_executor(
                                voice_executor,
                                tts_engine.synthesize_wav_bytes,
                                chunk_text,
                            )
                            await websocket.send_json(
                                {
                                    "type": "audio_chunk",
                                    "seq": seq,
                                    "audio_base64": base64.b64encode(audio_bytes_out).decode("ascii"),
                                }
                            )
                        except Exception as e:
                            logger.error(f"TTS error: {e}")

                    await websocket.send_json({"type": "start"})

                    def _extract_ready_chunk(buf: str) -> tuple[str, str]:
                        """
                        Chunk text for TTS with sentence boundaries when possible.
                        """

                        min_chars = 60
                        max_chars = 160
                        if len(buf) < min_chars:
                            return "", buf

                        if len(buf) >= max_chars:
                            cut = max(buf.rfind("."), buf.rfind("!"), buf.rfind("?"))
                            if cut < min_chars:
                                cut = max_chars - 1
                            chunk = buf[: cut + 1].strip()
                            rest = buf[cut + 1 :]
                            return chunk, rest

                        cut = max(buf.rfind("."), buf.rfind("!"), buf.rfind("?"))
                        if cut >= min_chars:
                            chunk = buf[: cut + 1].strip()
                            rest = buf[cut + 1 :]
                            return chunk, rest

                        return "", buf

                    pending_audio_tasks = []
                    try:
                        async for token in llm_engine.stream_chat(messages):
                            full_response += token
                            await websocket.send_json({"type": "token", "content": token})
                            tts_buffer += token

                            while True:
                                chunk, new_buf = _extract_ready_chunk(tts_buffer)
                                if not chunk:
                                    tts_buffer = new_buf
                                    break
                                tts_buffer = new_buf
                                seq = audio_seq
                                audio_seq += 1
                                pending_audio_tasks.append(
                                    asyncio.create_task(_tts_and_send(seq, chunk))
                                )

                        if tts_buffer.strip():
                            seq = audio_seq
                            audio_seq += 1
                            pending_audio_tasks.append(
                                asyncio.create_task(_tts_and_send(seq, tts_buffer.strip()))
                            )

                        # Wait for all TTS chunks to finish before signalling end.
                        # This ensures audio is fully delivered and the voice_executor
                        # is free before the next request can begin.
                        if pending_audio_tasks:
                            await asyncio.gather(*pending_audio_tasks, return_exceptions=True)

                        await websocket.send_json({"type": "end"})
                        conversation_manager.add_assistant_message(session_id, full_response)

                    except Exception as e:
                        logger.error(f"Voice generation error: {e}")
                        # Cancel any in-flight TTS tasks so they don't linger
                        for t in pending_audio_tasks:
                            t.cancel()
                        await websocket.send_json(
                            {"type": "error", "content": "Sorry, I encountered an error generating a response."}
                        )

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON format."})

    except WebSocketDisconnect:
        logger.info(f"WS disconnected. Session: {session_id}")
        # NOTE: We intentionally keep the session alive in memory so the client
        # can reconnect and continue the conversation.
