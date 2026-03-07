"""
Integration tests for the FastAPI backend — REST endpoints and WebSocket flow.

Strategy
--------
- The lifespan hook (which loads the GGUF model) is NOT invoked; the TestClient
  is instantiated without entering its context manager.
- `main.conversation_manager` is injected via the `client` fixture (see conftest.py).
- Tests that exercise the WebSocket LLM path replace `main.llm_engine` with a
  lightweight mock whose `stream_chat` is an async generator stub.
"""

import pytest
from unittest.mock import MagicMock

import main


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_mock_llm(*tokens):
    """
    Return a MagicMock whose stream_chat method is an async generator
    that yields each item in *tokens in order.
    """
    async def _stream(messages):
        for tok in tokens:
            yield tok

    mock = MagicMock()
    mock.stream_chat = _stream
    return mock


def _make_error_llm(partial_token="partial"):
    """
    Return a mock LLM whose stream_chat yields one token then raises.
    """
    async def _stream(messages):
        yield partial_token
        raise RuntimeError("Simulated LLM failure")

    mock = MagicMock()
    mock.stream_chat = _stream
    return mock


def _ws_init(ws, session_id=None):
    """Send the handshake init message and return the session_init payload."""
    ws.send_json({"session_id": session_id})
    return ws.receive_json()


# ─── REST: GET /sessions ──────────────────────────────────────────────────────

class TestGetSessions:

    def test_returns_200_with_sessions_key(self, client):
        c, _ = client
        resp = c.get("/sessions")
        assert resp.status_code == 200
        assert "sessions" in resp.json()

    def test_empty_list_when_no_sessions(self, client):
        c, _ = client
        resp = c.get("/sessions")
        assert resp.json()["sessions"] == []

    def test_session_appears_after_creation(self, client):
        c, cm = client
        cm.create_session("listed-session")
        resp = c.get("/sessions")
        ids = [s["session_id"] for s in resp.json()["sessions"]]
        assert "listed-session" in ids

    def test_session_not_listed_after_deletion(self, client):
        c, cm = client
        cm.create_session("temp-session")
        cm.delete_session("temp-session")
        ids = [s["session_id"] for s in c.get("/sessions").json()["sessions"]]
        assert "temp-session" not in ids


# ─── REST: GET /history/{session_id} ─────────────────────────────────────────

class TestGetHistory:

    def test_404_for_unknown_session(self, client):
        c, _ = client
        resp = c.get("/history/nonexistent-id")
        assert resp.status_code == 404

    def test_200_and_messages_key_for_known_session(self, client):
        c, cm = client
        cm.create_session("hist-session")
        resp = c.get("/history/hist-session")
        assert resp.status_code == 200
        assert "messages" in resp.json()

    def test_system_prompt_excluded_from_display_history(self, client):
        c, cm = client
        cm.create_session("hist-session")
        cm.add_user_message("hist-session", "hello")
        data = c.get("/history/hist-session").json()
        roles = [m["role"] for m in data["messages"]]
        assert "system" not in roles

    def test_user_and_assistant_messages_present(self, client):
        c, cm = client
        sid = cm.create_session("hist-session-2")
        cm.add_user_message(sid, "user turn")
        cm.add_assistant_message(sid, "assistant turn")
        data = c.get(f"/history/{sid}").json()
        assert len(data["messages"]) == 2

    def test_session_id_echoed_in_response(self, client):
        c, cm = client
        cm.create_session("echo-session")
        data = c.get("/history/echo-session").json()
        assert data["session_id"] == "echo-session"


# ─── REST: DELETE /sessions/{session_id} ─────────────────────────────────────

class TestDeleteSession:

    def test_200_and_deleted_key_on_success(self, client):
        c, cm = client
        cm.create_session("del-session")
        resp = c.delete("/sessions/del-session")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == "del-session"

    def test_session_gone_after_delete(self, client):
        c, cm = client
        cm.create_session("gone-session")
        c.delete("/sessions/gone-session")
        assert "gone-session" not in cm.sessions

    def test_404_for_unknown_session(self, client):
        c, _ = client
        resp = c.delete("/sessions/ghost")
        assert resp.status_code == 404


# ─── WebSocket: session initialisation ───────────────────────────────────────

class TestWebSocketInit:

    def test_new_session_init_returns_session_id(self, client):
        c, _ = client
        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws, session_id=None)
            assert init["type"] == "session_init"
            assert isinstance(init["session_id"], str)
            assert len(init["session_id"]) > 0

    def test_explicit_session_id_is_echoed_back(self, client):
        c, cm = client
        # Pre-create the session so the handler can resume it
        cm.create_session("explicit-id")
        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws, session_id="explicit-id")
            assert init["session_id"] == "explicit-id"

    def test_new_session_is_registered_in_manager(self, client):
        c, cm = client
        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]
        assert sid in cm.sessions

    def test_two_connections_receive_different_session_ids(self, client):
        c, _ = client
        with c.websocket_connect("/ws/chat") as ws1:
            id1 = _ws_init(ws1)["session_id"]
        with c.websocket_connect("/ws/chat") as ws2:
            id2 = _ws_init(ws2)["session_id"]
        assert id1 != id2


# ─── WebSocket: message streaming flow ───────────────────────────────────────

class TestWebSocketMessaging:

    def test_message_produces_start_token_end_sequence(self, client):
        c, _ = client
        main.llm_engine = _make_mock_llm("Hello", " there")

        with c.websocket_connect("/ws/chat") as ws:
            _ws_init(ws)
            ws.send_json({"type": "message", "content": "Hi"})

            start = ws.receive_json()
            assert start["type"] == "start"

            token1 = ws.receive_json()
            assert token1["type"] == "token"
            assert token1["content"] == "Hello"

            token2 = ws.receive_json()
            assert token2["type"] == "token"
            assert token2["content"] == " there"

            end = ws.receive_json()
            assert end["type"] == "end"

    def test_assistant_response_stored_in_session_after_end(self, client):
        c, cm = client
        main.llm_engine = _make_mock_llm("Sure thing!")

        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]
            ws.send_json({"type": "message", "content": "Hello"})
            ws.receive_json()  # start
            ws.receive_json()  # token
            ws.receive_json()  # end

        msgs = cm.get_display_history(sid)
        assert any(m["role"] == "assistant" and "Sure thing!" in m["content"]
                   for m in msgs)

    def test_user_message_stored_in_session(self, client):
        c, cm = client
        main.llm_engine = _make_mock_llm("OK")

        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]
            ws.send_json({"type": "message", "content": "test user input"})
            ws.receive_json()  # start
            ws.receive_json()  # token
            ws.receive_json()  # end

        msgs = cm.get_display_history(sid)
        assert any(m["role"] == "user" and m["content"] == "test user input"
                   for m in msgs)

    def test_multi_turn_context_accumulated_across_messages(self, client):
        """After two exchanges the session must contain both user turns."""
        c, cm = client
        main.llm_engine = _make_mock_llm("Response")

        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]

            for user_msg in ("First question", "Second question"):
                ws.send_json({"type": "message", "content": user_msg})
                ws.receive_json()  # start
                ws.receive_json()  # token
                ws.receive_json()  # end

        user_turns = [m for m in cm.get_display_history(sid) if m["role"] == "user"]
        assert len(user_turns) == 2
        assert user_turns[0]["content"] == "First question"
        assert user_turns[1]["content"] == "Second question"

    def test_empty_content_message_produces_no_response(self, client):
        """
        Sending a whitespace-only message must be silently ignored.
        We verify this by following up with a reset and confirming the
        reset response arrives immediately (no stray start/token/end in between).
        """
        c, _ = client
        main.llm_engine = _make_mock_llm("should not appear")

        with c.websocket_connect("/ws/chat") as ws:
            _ws_init(ws)
            ws.send_json({"type": "message", "content": "   "})
            ws.send_json({"type": "reset"})
            response = ws.receive_json()
            assert response["type"] == "system"
            assert response["content"] == "Session reset."

    def test_invalid_json_returns_error_message(self, client):
        c, _ = client

        with c.websocket_connect("/ws/chat") as ws:
            _ws_init(ws)
            ws.send_text("this is not { json")
            error = ws.receive_json()
            assert error["type"] == "error"
            assert "Invalid JSON" in error["content"]

    def test_llm_exception_returns_error_message(self, client):
        """If the LLM raises mid-stream, the client should receive an error frame."""
        c, _ = client
        main.llm_engine = _make_error_llm("partial token")

        with c.websocket_connect("/ws/chat") as ws:
            _ws_init(ws)
            ws.send_json({"type": "message", "content": "trigger error"})

            start = ws.receive_json()
            assert start["type"] == "start"

            partial = ws.receive_json()
            assert partial["type"] == "token"
            assert partial["content"] == "partial token"

            error = ws.receive_json()
            assert error["type"] == "error"
            assert "error" in error["content"].lower()


# ─── WebSocket: reset ─────────────────────────────────────────────────────────

class TestWebSocketReset:

    def test_reset_returns_system_message(self, client):
        c, _ = client

        with c.websocket_connect("/ws/chat") as ws:
            _ws_init(ws)
            ws.send_json({"type": "reset"})
            resp = ws.receive_json()
            assert resp["type"] == "system"
            assert resp["content"] == "Session reset."

    def test_history_empty_after_reset(self, client):
        c, cm = client
        main.llm_engine = _make_mock_llm("Hi!")

        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]

            # Exchange one message
            ws.send_json({"type": "message", "content": "Hello"})
            ws.receive_json()  # start
            ws.receive_json()  # token
            ws.receive_json()  # end

            # Reset
            ws.send_json({"type": "reset"})
            ws.receive_json()  # system ack

        display = cm.get_display_history(sid)
        assert display == []

    def test_session_remains_open_after_reset(self, client):
        """The session ID must still exist in the manager after a reset."""
        c, cm = client

        with c.websocket_connect("/ws/chat") as ws:
            init = _ws_init(ws)
            sid = init["session_id"]
            ws.send_json({"type": "reset"})
            ws.receive_json()

        assert sid in cm.sessions
