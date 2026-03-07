"""
Unit tests for ConversationManager.

These tests exercise every method of ConversationManager in isolation —
no FastAPI app, no LLM engine, no network I/O required.
"""

import pytest
from conversation_manager import (
    ConversationManager,
    SYSTEM_PROMPT,
    _FILLER_PATTERNS,
    _RECENT_CUTOFF,
)


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


# ─── SNR: _is_noise() ────────────────────────────────────────────────────

class TestIsNoise:

    def test_known_filler_word_is_noise(self, cm):
        for word in ["ok", "sure", "thanks", "yep", "got it", "alright"]:
            assert cm._is_noise(word) is True, f"Expected '{word}' to be noise"

    def test_filler_with_punctuation_is_noise(self, cm):
        # Trailing punctuation should be stripped before matching
        assert cm._is_noise("ok!") is True
        assert cm._is_noise("thanks.") is True
        assert cm._is_noise("sure,") is True

    def test_filler_with_surrounding_whitespace_is_noise(self, cm):
        assert cm._is_noise("  ok  ") is True

    def test_filler_is_case_insensitive(self, cm):
        assert cm._is_noise("OK") is True
        assert cm._is_noise("Thanks") is True
        assert cm._is_noise("SURE") is True

    def test_very_short_non_question_is_noise(self, cm):
        # 8 chars or fewer and no '?' → noise
        assert cm._is_noise("hi") is True
        assert cm._is_noise("bye") is True
        assert cm._is_noise("lol") is True

    def test_short_question_is_signal(self, cm):
        # Short but contains '?' → NOT noise (e.g. "Why?" "How?" "Hours?")
        assert cm._is_noise("Why?") is False
        assert cm._is_noise("How?") is False
        assert cm._is_noise("Hours?") is False

    def test_substantive_question_is_signal(self, cm):
        assert cm._is_noise("Do you carry ibuprofen?") is False
        assert cm._is_noise("What are your opening hours?") is False
        assert cm._is_noise("Can I get vitamin C supplements?") is False

    def test_substantive_statement_is_signal(self, cm):
        assert cm._is_noise("I have a headache and need something for pain.") is False
        assert cm._is_noise("Tell me about your OTC allergy medicines.") is False

    def test_all_filler_patterns_recognised(self, cm):
        """Every entry in _FILLER_PATTERNS must be classified as noise."""
        for phrase in _FILLER_PATTERNS:
            assert cm._is_noise(phrase) is True, f"'{phrase}' should be noise"


# ─── SNR: get_messages() context filtering ─────────────────────────────────────

class TestGetMessagesNoiseFiltration:

    def _build_session(self, cm, turns):
        """Helper: create a session and add (role, content) turns in order."""
        sid = cm.create_session()
        for role, content in turns:
            if role == "user":
                cm.add_user_message(sid, content)
            else:
                cm.add_assistant_message(sid, content)
        return sid

    def test_system_prompt_always_present_at_index_0(self, cm):
        sid = self._build_session(cm, [
            ("user", "ok"), ("assistant", "How can I help?"),
            ("user", "thanks"), ("assistant", "You're welcome!"),
            ("user", "Do you carry paracetamol?"),
        ])
        msgs = cm.get_messages(sid)
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == SYSTEM_PROMPT

    def test_short_session_returns_all_messages_unfiltered(self, cm):
        """Sessions with <= _RECENT_CUTOFF conversation turns are never filtered."""
        sid = cm.create_session()
        cm.add_user_message(sid, "ok")              # noise, but recent
        cm.add_assistant_message(sid, "How can I help?")
        msgs = cm.get_messages(sid)
        # system + 2 messages, nothing dropped
        assert len(msgs) == 3

    def test_noise_in_older_turns_is_filtered_out(self, cm):
        """
        Filler user messages outside the recent window must be dropped from the
        LLM context (but NOT from self.sessions).
        """
        turns = [
            ("user",      "Do you carry ibuprofen?"),   # signal — old
            ("assistant", "Yes, we stock ibuprofen."),
            ("user",      "thanks"),                    # noise — old
            ("assistant", "You're welcome!"),
            # ─── recent cutoff boundary ───
            ("user",      "ok"),                        # noise — but recent: kept
            ("assistant", "Anything else?"),
            ("user",      "What are your hours?"),       # signal — recent: kept
            ("assistant", "Mon–Sat 8AM–9PM."),
        ]
        sid = self._build_session(cm, turns)
        msgs = cm.get_messages(sid)
        contents = [m["content"] for m in msgs]

        # The old filler "thanks" must be gone from LLM context
        assert "thanks" not in contents
        # The old signal must still be present
        assert "Do you carry ibuprofen?" in contents
        # Recent noise ("ok") must still be present
        assert "ok" in contents

    def test_substantive_older_messages_are_not_filtered(self, cm):
        turns = [
            ("user",      "Can I get vitamin D?"),       # signal — old
            ("assistant", "Yes, we carry vitamin D3."),
            ("user",      "sure"),                      # noise — old
            ("assistant", "Let me know if you need more info."),
            ("user",      "What about vitamin C?"),      # signal — recent
            ("assistant", "Yes, we have that too."),
            ("user",      "Great, thanks"),
            ("assistant", "Happy to help!"),
        ]
        sid = self._build_session(cm, turns)
        msgs = cm.get_messages(sid)
        contents = [m["content"] for m in msgs]
        assert "Can I get vitamin D?" in contents

    def test_raw_session_store_unaffected_by_noise_filtering(self, cm):
        """
        get_messages() must not mutate self.sessions — the raw store must
        still contain the filler messages even after filtering.
        """
        turns = [
            ("user",      "Do you carry aspirin?"),
            ("assistant", "Yes."),
            ("user",      "ok"),
            ("assistant", "Anything else?"),
            ("user",      "Do you carry ibuprofen?"),
            ("assistant", "Yes."),
            ("user",      "sure"),
            ("assistant", "Let me know!"),
        ]
        sid = self._build_session(cm, turns)
        cm.get_messages(sid)   # trigger filtering view
        # Raw store must still contain all messages
        raw_contents = [m["content"] for m in cm.sessions[sid]]
        assert "ok" in raw_contents
        assert "sure" in raw_contents

    def test_recent_cutoff_messages_never_filtered_even_if_noise(self, cm):
        """
        The last _RECENT_CUTOFF messages must always be kept, even if they
        are all filler.
        """
        # Build enough turns to push something into the 'older' window
        turns = [
            ("user",      "Do you carry aspirin?"),   # old — signal
            ("assistant", "Yes."),
        ] + [
            (m, "ok") if m == "user" else (m, "sure thing")
            for m in ["user", "assistant"] * (_RECENT_CUTOFF // 2)
        ]
        sid = self._build_session(cm, turns)
        msgs = cm.get_messages(sid)
        # The last _RECENT_CUTOFF messages must all still be there
        recent_contents = [m["content"] for m in msgs[-_RECENT_CUTOFF:]]
        # They came from our filler turns but must be present
        assert len(recent_contents) == _RECENT_CUTOFF

    def test_multiple_noise_turns_all_filtered_from_older_window(self, cm):
        # 10 conversation turns: _RECENT_CUTOFF=4 means turns 1-6 are "older",
        # turns 7-10 are "recent". All three noise turns (1, 3, 5) are in older.
        turns = [
            ("user",      "ok"),                       # noise — old
            ("assistant", "reply 1"),
            ("user",      "sure"),                     # noise — old
            ("assistant", "reply 2"),
            ("user",      "yep"),                      # noise — old
            ("assistant", "reply 3"),
            # ── recent cutoff boundary ──────────────────
            ("user",      "Do you have paracetamol?"), # signal — recent
            ("assistant", "Yes we do."),
            ("user",      "What about aspirin?"),      # signal — recent
            ("assistant", "Yes, aspirin too."),
        ]
        sid = self._build_session(cm, turns)
        msgs = cm.get_messages(sid)
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
        # All three old filler turns must be gone
        assert "ok" not in user_msgs
        assert "sure" not in user_msgs
        assert "yep" not in user_msgs
        # The substantive recent turns must survive
        assert "Do you have paracetamol?" in user_msgs
        assert "What about aspirin?" in user_msgs

    def test_assistant_messages_never_noise_filtered(self, cm):
        """
        Noise filtering applies only to user messages; assistant messages
        in the older window must always be kept.
        """
        turns = [
            ("user",      "Do you have aspirin?"),
            ("assistant", "Yes."),          # short assistant reply — must NOT be filtered
            ("user",      "ok"),
            ("assistant", "ok"),            # looks like filler but role=assistant
            ("user",      "What are your hours?"),
            ("assistant", "Mon–Sat 8–9PM."),
            ("user",      "Any Sunday hours?"),
            ("assistant", "Sun 10AM–6PM."),
        ]
        sid = self._build_session(cm, turns)
        msgs = cm.get_messages(sid)
        assistant_contents = [m["content"] for m in msgs if m["role"] == "assistant"]
        # Short assistant replies like "Yes." and "ok" must still be present
        assert "Yes." in assistant_contents
