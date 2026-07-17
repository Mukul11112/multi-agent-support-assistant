"""
Persistence for users, sessions, and messages (Modules 1 and 8).

MongoDB is the primary store. If it is unreachable at startup we fall back to an
in-memory store with the same interface, so a grader can clone the repo and run
it without installing Mongo. The fallback loses everything on restart and says
so loudly in /health - it is a convenience, not a deployment mode.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from backend import config

log = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class InMemoryDB:
    """Dict-backed stand-in with the same surface as MongoDB()."""

    backend = "in-memory (data is lost on restart)"

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.messages: list[dict] = []

    # users
    def get_user_by_email(self, email: str) -> dict | None:
        return next((u for u in self.users.values() if u["email"] == email), None)

    def get_user(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def create_user(self, doc: dict) -> dict:
        self.users[doc["id"]] = doc
        return doc

    # messages
    def insert_message(self, doc: dict) -> dict:
        self.messages.append(doc)
        return doc

    def get_messages(self, session_id: str, user_id: str, limit: int = 200) -> list[dict]:
        rows = [m for m in self.messages
                if m["session_id"] == session_id and m["user_id"] == user_id]
        rows.sort(key=lambda m: m["timestamp"])
        return rows[-limit:]

    def get_sessions(self, user_id: str) -> list[dict]:
        by_session: dict[str, list[dict]] = {}
        for m in self.messages:
            if m["user_id"] == user_id:
                by_session.setdefault(m["session_id"], []).append(m)
        out = []
        for sid, msgs in by_session.items():
            msgs.sort(key=lambda m: m["timestamp"])
            first_user = next((m for m in msgs if m["role"] == "user"), None)
            out.append({
                "session_id": sid,
                "title": (first_user["content"][:60] if first_user else "New chat"),
                "message_count": len(msgs),
                "updated_at": msgs[-1]["timestamp"],
            })
        out.sort(key=lambda s: s["updated_at"], reverse=True)
        return out

    def delete_session(self, session_id: str, user_id: str) -> int:
        before = len(self.messages)
        self.messages = [m for m in self.messages
                         if not (m["session_id"] == session_id and m["user_id"] == user_id)]
        return before - len(self.messages)

    def all_messages(self) -> list[dict]:
        return list(self.messages)


class MongoDB:
    backend = "mongodb"

    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.client.admin.command("ping")  # fail fast if unreachable
        self.db = self.client[db_name]
        self.users_col = self.db["users"]
        self.messages_col = self.db["messages"]
        self.users_col.create_index([("email", ASCENDING)], unique=True)
        self.messages_col.create_index([("session_id", ASCENDING),
                                        ("timestamp", ASCENDING)])
        self.messages_col.create_index([("user_id", ASCENDING)])
        self.backend = f"mongodb ({db_name})"

    def _strip(self, doc: dict | None) -> dict | None:
        if doc:
            doc.pop("_id", None)
        return doc

    def get_user_by_email(self, email: str) -> dict | None:
        return self._strip(self.users_col.find_one({"email": email}))

    def get_user(self, user_id: str) -> dict | None:
        return self._strip(self.users_col.find_one({"id": user_id}))

    def create_user(self, doc: dict) -> dict:
        self.users_col.insert_one(dict(doc))
        return doc

    def insert_message(self, doc: dict) -> dict:
        self.messages_col.insert_one(dict(doc))
        return doc

    def get_messages(self, session_id: str, user_id: str, limit: int = 200) -> list[dict]:
        cur = self.messages_col.find(
            {"session_id": session_id, "user_id": user_id}
        ).sort("timestamp", ASCENDING).limit(limit)
        return [self._strip(d) for d in cur]

    def get_sessions(self, user_id: str) -> list[dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"timestamp": ASCENDING}},
            {"$group": {
                "_id": "$session_id",
                "message_count": {"$sum": 1},
                "updated_at": {"$max": "$timestamp"},
                "first_message": {"$first": "$content"},
            }},
            {"$sort": {"updated_at": -1}},
        ]
        return [{
            "session_id": r["_id"],
            "title": (r.get("first_message") or "New chat")[:60],
            "message_count": r["message_count"],
            "updated_at": r["updated_at"],
        } for r in self.messages_col.aggregate(pipeline)]

    def delete_session(self, session_id: str, user_id: str) -> int:
        res = self.messages_col.delete_many({"session_id": session_id, "user_id": user_id})
        return res.deleted_count

    def all_messages(self) -> list[dict]:
        return [self._strip(d) for d in self.messages_col.find({})]


_db: MongoDB | InMemoryDB | None = None


def get_db() -> MongoDB | InMemoryDB:
    global _db
    if _db is not None:
        return _db
    try:
        _db = MongoDB(config.MONGO_URI, config.MONGO_DB)
        log.info("Database: %s", _db.backend)
    except (ServerSelectionTimeoutError, PyMongoError) as exc:
        log.warning(
            "MongoDB unreachable at %s (%s). Falling back to IN-MEMORY storage - "
            "chat history will NOT survive a restart. Start Mongo or set MONGO_URI "
            "to a MongoDB Atlas connection string.",
            config.MONGO_URI, type(exc).__name__,
        )
        _db = InMemoryDB()
    return _db


def reset_db() -> None:
    global _db
    _db = None
