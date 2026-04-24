import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

# ─── SNR: known low-information filler phrases ────────────────────────────────
# User messages whose normalised text matches one of these are treated as noise
# and suppressed from the older portion of the context window before sending to
# the LLM.  The raw session store is never modified — only the LLM view changes.
_FILLER_PATTERNS = {
    "ok", "okay", "sure", "yes", "no", "thanks", "thank you",
    "got it", "alright", "fine", "great", "cool", "yep", "nope",
    "lol", "haha", "hmm", "i see", "understood", "makes sense",
    "good", "nice", "perfect", "sounds good", "not really",
}

# How many most-recent messages are always kept verbatim (never noise-filtered)
_RECENT_CUTOFF = 4

SYSTEM_PROMPT = """You are a pharmacy assistant at HealthFirst Community Pharmacy. Speak directly to the customer. Never describe what you are doing or summarise your own response.

Example of WRONG response: "The customer asked about acetaminophen. I confirmed availability."
Example of CORRECT response: "Yes, we carry paracetamol in 325 mg, 500 mg, and 650 mg tablets."

Rules:
- Respond directly to the customer in plain English.
- Answer only what was asked. Availability question → confirm yes/no and form/strength only.
- Maximum 2 sentences for simple questions. No bullet lists unless the customer asks for details.
- Never narrate, never summarise, never refer to yourself in third person.
- Do not prescribe or diagnose. Refer to a pharmacist or doctor if needed.
- Business hours: Mon-Sat 8AM-9PM, Sun 10AM-6PM.
- If the question is not related to pharmacy, medications, health, or this pharmacy's services, reply with exactly: "I can only help with pharmacy-related questions. Is there anything I can help you with regarding medications or our services?"
- Never invent people, facts, or information not provided in the reference context. If you don't know, say so.
"""

class ConversationManager:
    def __init__(self, max_history: int = 10):
        # Maps session_id -> list of message dicts: {"role": "...", "content": "..."}
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        # Maps session_id -> metadata dict
        self.metadata: Dict[str, Dict] = {}
        self.max_history = max_history

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session, or restore an existing one if session_id is provided."""
        if session_id and session_id in self.sessions:
            # Session already exists; just return it (resume behaviour)
            return session_id

        sid = session_id or str(uuid.uuid4())
        self.sessions[sid] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.metadata[sid] = {
            "title": "New Chat",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message_count": 0,
        }
        return sid

    # ─── SNR helpers ──────────────────────────────────────────────────────────

    def _is_noise(self, message: str) -> bool:
        """
        Return True if the user message carries negligible semantic content.

        A message is noise if:
        - Its normalised form matches a known filler phrase, OR
        - It is very short (≤ 8 chars) AND does not contain a question mark
          (short questions like "Why?" or "How?" are always signal).
        """
        cleaned = message.strip().lower().rstrip("!.,?")
        if cleaned in _FILLER_PATTERNS:
            return True
        if len(cleaned) <= 8 and "?" not in message:
            return True
        return False

    # ─── Context retrieval ────────────────────────────────────────────────────

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """
        Return context messages for the LLM, with noise filtered from older turns.

        Strategy (Signal-to-Noise filtering):
        - The system prompt is always kept at index 0.
        - The most recent `_RECENT_CUTOFF` messages are always kept verbatim so
          the model has immediate conversational context with full fidelity.
        - Messages older than that cutoff are passed through `_is_noise()`: filler
          user turns are dropped, freeing context budget for substantive history.
        - The raw session store (self.sessions) is never mutated by this method.
        """
        if session_id not in self.sessions:
            return []
        history = self.sessions[session_id]
        system = [history[0]]       # index 0 is always the system prompt
        conversation = history[1:]  # everything after the system prompt

        # Short sessions: nothing old enough to filter yet
        if len(conversation) <= _RECENT_CUTOFF:
            return system + conversation

        older = conversation[:-_RECENT_CUTOFF]
        recent = conversation[-_RECENT_CUTOFF:]

        filtered_older = [
            m for m in older
            if not (m["role"] == "user" and self._is_noise(m["content"]))
        ]

        return system + filtered_older + recent

    def get_display_history(self, session_id: str) -> List[Dict[str, str]]:
        """Return only user/assistant messages (skip system prompt) for frontend rendering."""
        if session_id not in self.sessions:
            return []
        return [m for m in self.sessions[session_id] if m["role"] != "system"]

    def list_sessions(self) -> List[Dict]:
        """Return metadata for all sessions, newest first."""
        result = []
        for sid, meta in self.metadata.items():
            result.append({
                "session_id": sid,
                "title": meta["title"],
                "created_at": meta["created_at"],
                "message_count": meta["message_count"],
            })
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return result

    def add_user_message(self, session_id: str, message: str):
        if session_id not in self.sessions:
            self.create_session(session_id)
        self.sessions[session_id].append({"role": "user", "content": message})
        # Auto-title: use first user message (truncated) as the chat title
        meta = self.metadata.setdefault(session_id, {"title": "New Chat", "created_at": datetime.now(timezone.utc).isoformat(), "message_count": 0})
        if meta["title"] == "New Chat":
            meta["title"] = message[:40] + ("…" if len(message) > 40 else "")
        meta["message_count"] += 1
        self._prune_history(session_id)

    def add_assistant_message(self, session_id: str, message: str):
        if session_id in self.sessions:
            self.sessions[session_id].append({"role": "assistant", "content": message})
            self.metadata.setdefault(session_id, {})["message_count"] = \
                self.metadata[session_id].get("message_count", 0) + 1
            self._prune_history(session_id)

    def _prune_history(self, session_id: str):
        """
        Ensures the context window doesn't grow infinitely.
        Keeps the system prompt (index 0) and the last `max_history` messages.
        """
        history = self.sessions[session_id]
        if len(history) > self.max_history + 1:
            self.sessions[session_id] = [history[0]] + history[-self.max_history:]

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        if session_id in self.metadata:
            self.metadata[session_id]["title"] = "New Chat"
            self.metadata[session_id]["message_count"] = 0

    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)
        self.metadata.pop(session_id, None)

    def build_augmented_messages(
        self,
        session_id: str,
        rag_context: str = "",
        tool_name: str = "",
        tool_result_text: str = "",
    ) -> List[Dict[str, str]]:
        """
        Return the LLM message list with RAG chunks and tool results injected
        as a context block immediately before the last user message.

        This keeps streaming intact: all enrichment happens before generation starts.
        """
        messages = self.get_messages(session_id)
        if not messages:
            return messages

        # Nothing to inject
        if not rag_context and not tool_result_text:
            return messages

        # Find the last user message index
        last_user_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_idx = i
                break

        if last_user_idx is None:
            return messages

        # Build the context injection block
        context_parts = []
        if rag_context:
            context_parts.append(rag_context)
        if tool_result_text:
            context_parts.append(tool_result_text)

        context_block = "\n\n".join(context_parts)

        # Insert context as a system message immediately before the last user message.
        # Using "system" role keeps the model from treating it as content to repeat.
        augmented = list(messages)
        augmented.insert(last_user_idx, {"role": "system", "content": context_block})
        return augmented

