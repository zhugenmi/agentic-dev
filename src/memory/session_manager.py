"""Session manager for managing user sessions and memory"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class Session:
    """Session class for managing user session data"""

    def __init__(self, session_id: str, summary: str = ""):
        """Initialize a session"""
        self.session_id = session_id
        self.summary = summary  # 会话摘要
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()
        self.conversation_history = []
        self.task_history = []

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now().isoformat()

    def add_task(self, task_description: str, result):
        """Add a task to the task history"""
        self.task_history.append({
            "task_description": task_description,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now().isoformat()

    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.conversation_history)

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "summary": self.summary,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "conversation_history": self.conversation_history,
            "task_history": self.task_history
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create session from dictionary"""
        session = cls(data["session_id"], data.get("summary", ""))
        session.created_at = data.get("created_at")
        session.last_activity = data.get("last_activity")
        session.conversation_history = data.get("conversation_history", [])
        session.task_history = data.get("task_history", [])
        return session


class SessionManager:
    """Session manager for managing user sessions"""

    def __init__(self):
        """Initialize session manager"""
        self.redis_client = None
        self.redis_enabled = False
        self.sessions = {}

        # Check if Redis is enabled via environment variable
        use_redis = os.getenv("USE_REDIS", "false").lower() == "true"

        if use_redis:
            self._init_redis()
        else:
            # Check if Redis is available even when not forced
            self._try_init_redis()

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            import redis
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.redis_enabled = True
            print("Session manager: Using Redis storage")
        except Exception as e:
            print(f"Redis initialization failed: {e}, using in-memory session storage")
            self.redis_enabled = False

    def _try_init_redis(self):
        """Try to initialize Redis if available"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            import redis
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.redis_enabled = True
        except Exception as e:
            print(f"Redis not available, using in-memory session storage: {e}")
            self.redis_enabled = False

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get or create a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        if self.redis_enabled:
            try:
                session_data = self.redis_client.get(f"session:{session_id}")
                if session_data:
                    session = Session.from_dict(json.loads(session_data))
                    self.sessions[session_id] = session
                    return session
            except Exception as e:
                print(f"Redis error: {e}")
                self.redis_enabled = False

        session = Session(session_id)
        self.sessions[session_id] = session
        self._save_session(session)
        return session

    def _save_session(self, session: Session):
        """Save session to Redis or memory"""
        if self.redis_enabled:
            try:
                self.redis_client.set(
                    f"session:{session.session_id}",
                    json.dumps(session.to_dict())
                )
                self.redis_client.expire(f"session:{session.session_id}", 86400)
            except Exception as e:
                print(f"Redis save error: {e}")
                self.redis_enabled = False

    def update_session(self, session: Session):
        """Update session"""
        self._save_session(session)

    def update_summary(self, session_id: str, summary: str):
        """Update session summary"""
        session = self.get_session(session_id)
        if session:
            session.summary = summary
            self._save_session(session)

    def list_sessions(self):
        """List all sessions with summary info"""
        sessions_list = []

        # Load from memory_store files
        memory_store = Path(__file__).parent.parent.parent / "memory_store"
        if memory_store.exists():
            for f in memory_store.glob("session_*.json"):
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                        session_id = data.get("session_id", f.stem.replace("session_", ""))
                        summary = data.get("summary", "")
                        created_at = data.get("created_at", "")
                        last_activity = data.get("last_activity", "")
                        conv = data.get("conversation", [])
                        message_count = len(conv) if isinstance(conv, list) else 0
                        sessions_list.append({
                            "session_id": session_id,
                            "summary": summary,
                            "created_at": created_at,
                            "last_activity": last_activity,
                            "message_count": message_count
                        })
                except Exception:
                    pass

        # Also check in-memory sessions
        for session_id, session in self.sessions.items():
            if not any(s["session_id"] == session_id for s in sessions_list):
                sessions_list.append({
                    "session_id": session_id,
                    "summary": session.summary,
                    "created_at": session.created_at,
                    "last_activity": session.last_activity,
                    "message_count": session.get_message_count()
                })

        # Sort by last_activity descending
        sessions_list.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        return sessions_list

    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

        if self.redis_enabled:
            try:
                self.redis_client.delete(f"session:{session_id}")
            except Exception:
                pass

        # Also delete file
        memory_store = Path(__file__).parent.parent.parent / "memory_store"
        session_file = memory_store / f"session_{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
            except Exception:
                pass