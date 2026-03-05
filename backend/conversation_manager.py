import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

SYSTEM_PROMPT = """You are a helpful, professional Pharmacy Assistant at 'HealthFirst Community Pharmacy'.
Your role is to assist customers with:
- Checking general availability of over-the-counter (OTC) medications.
- Providing information about pharmacy business hours (Mon-Sat 8AM to 9PM, Sun 10AM to 6PM).
- Giving general, non-diagnostic wellness advice.

IMPORTANT CONSTRAINTS (You must strictly follow these):
- You CANNOT and WILL NOT prescribe medication.
- You CANNOT provide medical diagnoses.
- If a user asks for prescription drugs or a medical diagnosis, politely inform them that you are an AI assistant and they should consult a licensed doctor or pharmacist in person.
- Keep your answers concise, empathetic, and professional.
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

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id]

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

