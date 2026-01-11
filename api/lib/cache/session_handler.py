from typing import Any, Dict
from uuid import uuid4
from datetime import datetime, timedelta


class SessionHandler:
    def __init__(self, ttl_seconds: int = 3600):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.expiry: Dict[str, datetime] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def create_session(self) -> str:
        session_id = str(uuid4())
        now = datetime.now().astimezone()
        self.sessions[session_id] = {"started_at": now.isoformat(), "data": {}}
        self.expiry[session_id] = now + self.ttl
        return session_id

    def get_session(self, session_id: str) -> Dict[str, Any] | None:
        self.cleanup_expired()
        return self.sessions.get(session_id)

    def set_data(self, session_id: str, key: str, value: Any) -> bool:
        self.cleanup_expired()
        if session_id in self.sessions:
            self.sessions[session_id]["data"][key] = value
            return True
        return False

    def get_data(self, session_id: str, key: str) -> Any:
        self.cleanup_expired()
        return self.sessions.get(session_id, {}).get("data", {}).get(key)

    def cleanup_expired(self):
        now = datetime.now().astimezone()
        expired = [sid for sid, exp in self.expiry.items() if exp < now]
        for sid in expired:
            self.sessions.pop(sid, None)
            self.expiry.pop(sid, None)
