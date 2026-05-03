"""Shared fixtures and WebSocket helpers for the eval suite."""
import sys
import os
import json
import pytest
import httpx

# Load .env from repo root so GOOGLE_API_KEY etc. are available without exporting
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # python-dotenv not installed; rely on shell env

# Make backend importable from every test module
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import CHATBOT_BASE_URL, CHATBOT_WS_URL  # noqa: E402 (after sys.path patch)

# ── Results directory (created once per session) ───────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ── Server connectivity ────────────────────────────────────────────────────

def _server_is_up() -> bool:
    try:
        r = httpx.get(f"{CHATBOT_BASE_URL}/sessions", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def live_server():
    """Session-scoped fixture. Skips the entire test if server is unreachable."""
    if not _server_is_up():
        pytest.skip(f"Chatbot server not reachable at {CHATBOT_BASE_URL}. Start the backend first.")


# ── WebSocket helpers ──────────────────────────────────────────────────────

async def ws_chat_turn(
    content: str,
    session_id: str | None = None,
) -> dict:
    """
    Open a WebSocket connection, send one user message, and collect the response.

    Returns:
        {
            "response":   full assistant text,
            "tool_used":  tool name or None,
            "session_id": resolved session ID,
        }
    """
    import websockets

    async with websockets.connect(CHATBOT_WS_URL, open_timeout=10) as ws:
        await ws.send(json.dumps({"session_id": session_id}))
        init = json.loads(await ws.recv())
        sid = init["session_id"]

        if not content.strip():
            return {"response": "", "tool_used": None, "session_id": sid}

        await ws.send(json.dumps({"type": "message", "content": content}))

        full_response = ""
        tool_used = None

        async for raw in ws:
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "token":
                full_response += msg.get("content", "")
            elif t == "tool_used":
                tool_used = msg.get("tool")
            elif t == "end":
                break
            elif t == "error":
                raise RuntimeError(f"Server error: {msg.get('content')}")

        return {"response": full_response, "tool_used": tool_used, "session_id": sid}


async def ws_multi_turn(turns: list[str]) -> list[dict]:
    """
    Send multiple messages in a single WebSocket session (shared conversation context).
    Returns a list of {"response": str, "tool_used": str | None} — one entry per turn.
    """
    import websockets

    results = []
    async with websockets.connect(CHATBOT_WS_URL, open_timeout=10) as ws:
        await ws.send(json.dumps({"session_id": None}))
        await ws.recv()  # consume session_init

        for content in turns:
            if not content.strip():
                results.append({"response": "", "tool_used": None})
                continue

            await ws.send(json.dumps({"type": "message", "content": content}))

            full_response = ""
            tool_used = None

            async for raw in ws:
                msg = json.loads(raw)
                t = msg.get("type")
                if t == "token":
                    full_response += msg.get("content", "")
                elif t == "tool_used":
                    tool_used = msg.get("tool")
                elif t == "end":
                    break
                elif t == "error":
                    raise RuntimeError(f"Server error: {msg.get('content')}")

            results.append({"response": full_response, "tool_used": tool_used})

    return results


# ── CRM fixture (direct, no server) ───────────────────────────────────────

@pytest.fixture
def crm_db(tmp_path):
    """Fresh SQLite path for each test — never touches the real crm.db."""
    return str(tmp_path / "crm_test.db")


@pytest.fixture
def crm(crm_db):
    from tools.crm_tool import CRMTool
    return CRMTool(db_path=crm_db)
