"""
CRM Tool — stores and retrieves patient information across sessions.
Backend: SQLite via aiosqlite for async-safe access.

Schema:
    users(user_id TEXT PK, name TEXT, contact TEXT, preferences TEXT JSON,
          last_visit TEXT, interaction_history TEXT JSON, created_at TEXT)
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiosqlite

logger = logging.getLogger(__name__)

TOOL_NAME = "crm_tool"
TOOL_DESCRIPTION = (
    "Stores and retrieves patient information (name, contact, preferences, visit history) "
    "keyed by session/user ID. Use this to greet returning customers by name and personalise responses."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["get_user", "create_user", "update_user"],
            "description": "Action to perform on the CRM.",
        },
        "user_id": {"type": "string", "description": "Unique session or user identifier."},
        "name": {"type": "string", "description": "Patient's full name (for create_user)."},
        "contact": {"type": "string", "description": "Contact info, e.g. phone or email (optional)."},
        "field": {"type": "string", "description": "Field name to update (for update_user)."},
        "value": {"type": "string", "description": "New value for the field (for update_user)."},
    },
    "required": ["action", "user_id"],
}


class CRMTool:
    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    schema = TOOL_SCHEMA

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def _init_db(self, conn: aiosqlite.Connection):
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                contact TEXT,
                preferences TEXT DEFAULT '{}',
                last_visit TEXT,
                interaction_history TEXT DEFAULT '[]',
                created_at TEXT
            )
        """)
        await conn.commit()

    async def execute(self, action: str, user_id: str, **kwargs) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._init_db(conn)

            if action == "get_user":
                return await self._get_user(conn, user_id)
            elif action == "create_user":
                return await self._create_user(conn, user_id, **kwargs)
            elif action == "update_user":
                return await self._update_user(conn, user_id, **kwargs)
            else:
                return {"error": f"Unknown action: {action}"}

    async def _get_user(self, conn: aiosqlite.Connection, user_id: str) -> Dict[str, Any]:
        async with conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            return {"found": False, "user_id": user_id}

        # Update last_visit on every retrieval
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute("UPDATE users SET last_visit = ? WHERE user_id = ?", (now, user_id))
        await conn.commit()

        return {
            "found": True,
            "user_id": user_id,
            "name": row["name"],
            "contact": row["contact"],
            "preferences": json.loads(row["preferences"] or "{}"),
            "last_visit": now,
            "interaction_history": json.loads(row["interaction_history"] or "[]"),
            "created_at": row["created_at"],
        }

    async def _create_user(
        self,
        conn: aiosqlite.Connection,
        user_id: str,
        name: str = "",
        contact: str = "",
        preferences: Optional[Dict] = None,
        **_,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        prefs_json = json.dumps(preferences or {})
        try:
            await conn.execute(
                "INSERT INTO users (user_id, name, contact, preferences, last_visit, interaction_history, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, name, contact, prefs_json, now, "[]", now),
            )
            await conn.commit()
            return {"created": True, "user_id": user_id, "name": name}
        except aiosqlite.IntegrityError:
            return {"created": False, "error": "User already exists", "user_id": user_id}

    async def _update_user(
        self,
        conn: aiosqlite.Connection,
        user_id: str,
        field: str = "",
        value: str = "",
        **_,
    ) -> Dict[str, Any]:
        allowed_fields = {"name", "contact", "preferences", "interaction_history"}
        if field not in allowed_fields:
            return {"error": f"Field '{field}' is not updatable. Allowed: {sorted(allowed_fields)}"}

        if field in {"preferences", "interaction_history"}:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return {"error": f"Value for '{field}' must be valid JSON"}

        await conn.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?",  # field is validated above
            (value, user_id),
        )
        if conn.total_changes == 0:
            return {"updated": False, "error": "User not found", "user_id": user_id}
        await conn.commit()
        return {"updated": True, "user_id": user_id, "field": field}

    async def append_interaction(self, user_id: str, summary: str):
        """Append a brief interaction summary to the user's history (max 10 entries kept)."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._init_db(conn)
            async with conn.execute(
                "SELECT interaction_history FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
            if not row:
                return
            history = json.loads(row["interaction_history"] or "[]")
            history.append({"time": datetime.now(timezone.utc).isoformat(), "summary": summary})
            history = history[-10:]  # Keep last 10 interactions
            await conn.execute(
                "UPDATE users SET interaction_history = ? WHERE user_id = ?",
                (json.dumps(history), user_id),
            )
            await conn.commit()
