from typing import Any, Dict
from uuid import uuid4
from datetime import datetime, timedelta
from src.config.pkg_config import PkgConfig
from ...models.session.session import Session


class SessionHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        config = PkgConfig()
        self._ttl_seconds = config.api_info.ttl_session_cache_seconds
        self.sessions: Dict[str, Session] = {}
        self.expiry: Dict[str, datetime] = {}
        self.ttl = timedelta(seconds=self._ttl_seconds)
        self._initialized = True

    def _update_access(self, session_id: str):
        if session_id in self.sessions:
            now = datetime.now().astimezone()
            self.sessions[session_id].last_accessed = now.isoformat()
            self.expiry[session_id] = now + self.ttl

    def create_session(self) -> str:
        session_id = str(uuid4())
        now = datetime.now().astimezone()
        self.sessions[session_id] = Session(
            started_at=now.isoformat(),
            last_accessed=now.isoformat(),
            session_id=session_id,
            data={},
        )
        self.expiry[session_id] = now + self.ttl
        return session_id

    def has_session(self, session_id: str) -> bool:
        self.cleanup_expired()
        return session_id in self.sessions

    def get_session(self, session_id: str) -> Session | None:
        self.cleanup_expired()
        session = self.sessions.get(session_id)
        if session:
            self._update_access(session_id)
        return session

    def set_data(self, session_id: str, key: str, value: Any) -> bool:
        self.cleanup_expired()
        if session_id in self.sessions:
            self.sessions[session_id].data[key] = value
            self._update_access(session_id)
            return True
        return False

    def get_data(self, session_id: str, key: str) -> Any:
        self.cleanup_expired()
        session = self.sessions.get(session_id)
        if session:
            self._update_access(session_id)
            return session.data.get(key)
        return None

    def cleanup_expired(self):
        now = datetime.now().astimezone()
        expired = [sid for sid, exp in self.expiry.items() if exp < now]
        for sid in expired:
            self.sessions.pop(sid, None)
            self.expiry.pop(sid, None)

    # region Properties
    @property
    def ttl_seconds(self) -> int:
        return self._ttl_seconds

    # endregion Properties
