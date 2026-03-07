"""
Unit tests for ConversationManager.

These tests exercise every method of ConversationManager in isolation —
no FastAPI app, no LLM engine, no network I/O required.
"""

import pytest
from conversation_manager import ConversationManager, SYSTEM_PROMPT


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def cm():
    """Fresh ConversationManager with default max_history=10."""
    return ConversationManager(max_history=10)


@pytest.fixture
def cm_small():
    """ConversationManager with max_history=3 to make pruning easy to trigger."""
    return ConversationManager(max_history=3)


# ─── Session Creation ─────────────────────────────────────────────────────────

class TestCreateSession:

    def test_returns_a_string_id(self, cm):
        sid = cm.create_session()
        assert isinstance(sid, str) and len(sid) > 0

    def test_auto_generates_uuid_when_no_id_given(self, cm):
        sid1 = cm.create_session()
        sid2 = cm.create_session()
        assert sid1 != sid2

    def test_uses_explicit_id_when_provided(self, cm):
        sid = cm.create_session(session_id="my-custom-id")
        assert sid == "my-custom-id"

    def test_explicit_id_is_stored_as_session(self, cm):
        cm.create_session(session_id="abc-123")
        assert "abc-123" in cm.sessions

    def test_resumes_existing_session_without_overwriting(self, cm):
        sid = cm.create_session(session_id="resume-me")
        cm.add_user_message(sid, "first message")
        # Second create with same ID must return the same session, not reset it.
        sid2 = cm.create_session(session_id="resume-me")
        assert sid2 == "resume-me"
        msgs = cm.get_messages("resume-me")
        assert any(m["content"] == "first message" for m in msgs)

    def test_new_session_injects_system_prompt_at_index_0(self, cm):
        sid = cm.create_session()
        msgs = cm.get_messages(sid)
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == SYSTEM_PROMPT

    def test_new_session_metadata_title_is_new_chat(self, cm):
        sid = cm.create_session()
        meta = cm.metadata[sid]
        assert meta["title"] == "New Chat"

    def test_new_session_metadata_message_count_is_zero(self, cm):
        sid = cm.create_session()
        assert cm.metadata[sid]["message_count"] == 0

    def test_new_session_metadata_has_created_at(self, cm):
        sid = cm.create_session()
        assert "created_at" in cm.metadata[sid]


# ─── Adding Messages ──────────────────────────────────────────────────────────

class TestAddMessages:

    def test_add_user_message_appends_correct_role_and_content(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "hello")
        msgs = cm.get_messages(sid)
        assert msgs[-1] == {"role": "user", "content": "hello"}

    def test_add_assistant_message_appends_correct_role_and_content(self, cm):
        sid = cm.create_session()
        cm.add_assistant_message(sid, "how can I help?")
        msgs = cm.get_messages(sid)
        assert msgs[-1] == {"role": "assistant", "content": "how can I help?"}

    def test_multi_turn_order_is_preserved(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "turn 1 user")
        cm.add_assistant_message(sid, "turn 1 assistant")
        cm.add_user_message(sid, "turn 2 user")
        cm.add_assistant_message(sid, "turn 2 assistant")

        msgs = cm.get_messages(sid)
        # Index 0 is always system prompt
        assert msgs[0]["role"] == "system"
        assert msgs[1] == {"role": "user", "content": "turn 1 user"}
        assert msgs[2] == {"role": "assistant", "content": "turn 1 assistant"}
        assert msgs[3] == {"role": "user", "content": "turn 2 user"}
        assert msgs[4] == {"role": "assistant", "content": "turn 2 assistant"}

    def test_add_user_message_increments_message_count(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "ping")
        assert cm.metadata[sid]["message_count"] == 1

    def test_add_assistant_message_increments_message_count(self, cm):
        sid = cm.create_session()
        cm.add_assistant_message(sid, "pong")
        assert cm.metadata[sid]["message_count"] == 1

    def test_add_user_message_to_unknown_session_creates_it(self, cm):
        """add_user_message should auto-create a session if it doesn't exist."""
        cm.add_user_message("brand-new-id", "hello")
        assert "brand-new-id" in cm.sessions

    def test_add_assistant_message_to_unknown_session_is_safe(self, cm):
        """add_assistant_message on an unknown session should not raise."""
        cm.add_assistant_message("nonexistent", "silent drop")
        # No session should be created for add_assistant_message
        assert "nonexistent" not in cm.sessions


# ─── Auto-Title ───────────────────────────────────────────────────────────────

class TestAutoTitle:

    def test_title_set_from_first_user_message(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "What are your hours?")
        assert cm.metadata[sid]["title"] == "What are your hours?"

    def test_title_truncated_at_40_chars_with_ellipsis(self, cm):
        sid = cm.create_session()
        long_msg = "A" * 50
        cm.add_user_message(sid, long_msg)
        assert cm.metadata[sid]["title"] == "A" * 40 + "…"

    def test_title_not_overwritten_by_second_message(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "First message")
        cm.add_user_message(sid, "Second message")
        assert cm.metadata[sid]["title"] == "First message"


# ─── History Retrieval ────────────────────────────────────────────────────────

class TestGetHistory:

    def test_get_messages_returns_all_including_system(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "hi")
        msgs = cm.get_messages(sid)
        assert msgs[0]["role"] == "system"
        assert len(msgs) == 2

    def test_get_messages_unknown_session_returns_empty_list(self, cm):
        assert cm.get_messages("does-not-exist") == []

    def test_get_display_history_excludes_system_prompt(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "hi")
        cm.add_assistant_message(sid, "hello")
        display = cm.get_display_history(sid)
        assert all(m["role"] != "system" for m in display)
        assert len(display) == 2

    def test_get_display_history_unknown_session_returns_empty_list(self, cm):
        assert cm.get_display_history("ghost") == []


# ─── History Pruning ──────────────────────────────────────────────────────────

class TestPruneHistory:

    def test_no_pruning_when_at_or_below_limit(self, cm_small):
        """With max_history=3, up to 3 messages should not be pruned."""
        sid = cm_small.create_session()
        for i in range(3):
            cm_small.add_user_message(sid, f"msg {i}")
        msgs = cm_small.get_messages(sid)
        # system + 3 = 4 total; limit is 3+1=4, not exceeded
        assert len(msgs) == 4

    def test_pruning_triggers_when_over_limit(self, cm_small):
        """Adding a 4th message (beyond max_history=3) should prune the oldest."""
        sid = cm_small.create_session()
        for i in range(4):
            cm_small.add_user_message(sid, f"msg {i}")
        msgs = cm_small.get_messages(sid)
        # Must be system + 3 = 4 (oldest conv message dropped)
        assert len(msgs) == 4

    def test_system_prompt_always_at_index_0_after_pruning(self, cm_small):
        sid = cm_small.create_session()
        for i in range(6):
            cm_small.add_user_message(sid, f"msg {i}")
        msgs = cm_small.get_messages(sid)
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == SYSTEM_PROMPT

    def test_most_recent_messages_are_retained_after_pruning(self, cm_small):
        """After pruning, the last max_history messages must be msg 2, 3, 4."""
        sid = cm_small.create_session()
        for i in range(5):
            cm_small.add_user_message(sid, f"msg {i}")
        msgs = cm_small.get_messages(sid)
        content_list = [m["content"] for m in msgs[1:]]  # skip system
        assert content_list == ["msg 2", "msg 3", "msg 4"]


# ─── Reset Session ────────────────────────────────────────────────────────────

class TestResetSession:

    def test_reset_clears_all_conversation_messages(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "hello")
        cm.add_assistant_message(sid, "hi there")
        cm.reset_session(sid)
        msgs = cm.get_messages(sid)
        # Only the system prompt should remain
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"

    def test_reset_re_injects_system_prompt(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "test")
        cm.reset_session(sid)
        msgs = cm.get_messages(sid)
        assert msgs[0]["content"] == SYSTEM_PROMPT

    def test_reset_restores_title_to_new_chat(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "some question")
        cm.reset_session(sid)
        assert cm.metadata[sid]["title"] == "New Chat"

    def test_reset_zeroes_message_count(self, cm):
        sid = cm.create_session()
        cm.add_user_message(sid, "msg1")
        cm.reset_session(sid)
        assert cm.metadata[sid]["message_count"] == 0

    def test_reset_on_unknown_session_does_not_raise(self, cm):
        cm.reset_session("nonexistent-id")  # should be a no-op


# ─── Delete Session ───────────────────────────────────────────────────────────

class TestDeleteSession:

    def test_delete_removes_session_from_sessions(self, cm):
        sid = cm.create_session()
        cm.delete_session(sid)
        assert sid not in cm.sessions

    def test_delete_removes_session_from_metadata(self, cm):
        sid = cm.create_session()
        cm.delete_session(sid)
        assert sid not in cm.metadata

    def test_delete_on_unknown_session_does_not_raise(self, cm):
        cm.delete_session("ghost-session")  # should be a no-op


# ─── List Sessions ────────────────────────────────────────────────────────────

class TestListSessions:

    def test_empty_when_no_sessions(self, cm):
        assert cm.list_sessions() == []

    def test_returns_all_sessions(self, cm):
        cm.create_session("s1")
        cm.create_session("s2")
        ids = {s["session_id"] for s in cm.list_sessions()}
        assert ids == {"s1", "s2"}

    def test_each_entry_has_required_keys(self, cm):
        sid = cm.create_session()
        result = cm.list_sessions()
        assert len(result) == 1
        entry = result[0]
        for key in ("session_id", "title", "created_at", "message_count"):
            assert key in entry

    def test_deleted_session_not_included(self, cm):
        sid = cm.create_session("will-be-deleted")
        cm.delete_session(sid)
        ids = [s["session_id"] for s in cm.list_sessions()]
        assert "will-be-deleted" not in ids
