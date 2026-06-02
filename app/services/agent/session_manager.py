"""
Agent 会话管理器 (Redis + 内存 fallback)
"""
import json
import uuid
from app.core.config import get_settings
from app.utils.redis_client import get_redis

settings = get_settings()

_memory_store: dict[str, dict] = {}


class SessionManager:
    def __init__(self):
        self.ttl = settings.AGENT_SESSION_TTL
        self.max_history = settings.AGENT_MAX_HISTORY

    async def create_session(self, user_id: str, role: str) -> str:
        session_id = uuid.uuid4().hex[:16]
        data = {
            "user_id": user_id,
            "role": role,
            "current_game": None,
            "game_state": None,
            "pending_operation": None,
            "last_intent": None,
            "history": [],
        }
        try:
            redis = await get_redis()
            await redis.hset(f"agent:session:{session_id}", mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else (str(v) if v is not None else "")
                for k, v in data.items()
            })
            await redis.expire(f"agent:session:{session_id}", self.ttl)
        except Exception:
            _memory_store[session_id] = data
        return session_id

    async def get_session(self, session_id: str) -> dict | None:
        if session_id in _memory_store:
            return _memory_store[session_id]
        try:
            redis = await get_redis()
            raw = await redis.hgetall(f"agent:session:{session_id}")
            if not raw:
                return None
            data = {}
            for k, v in raw.items():
                if k in ("game_state", "pending_operation", "history") and v:
                    try:
                        data[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        data[k] = None if k != "history" else []
                else:
                    data[k] = v
            await redis.expire(f"agent:session:{session_id}", self.ttl)
            return data
        except Exception:
            return None

    async def update_session(self, session_id: str, **kwargs):
        if session_id in _memory_store:
            for k, v in kwargs.items():
                _memory_store[session_id][k] = v
            return
        try:
            redis = await get_redis()
            key = f"agent:session:{session_id}"
            update = {}
            for k, v in kwargs.items():
                update[k] = json.dumps(v) if isinstance(v, (dict, list)) else v
            if update:
                await redis.hset(key, mapping=update)
                await redis.expire(key, self.ttl)
        except Exception:
            pass

    async def add_to_history(self, session_id: str, role: str, content: str):
        if session_id in _memory_store:
            h = _memory_store[session_id].get("history", [])
            h.append({"role": role, "content": content})
            if len(h) > self.max_history * 2:
                h = h[-self.max_history * 2:]
            _memory_store[session_id]["history"] = h
            return
        try:
            redis = await get_redis()
            key = f"agent:session:{session_id}"
            history_str = await redis.hget(key, "history")
            history = json.loads(history_str) if history_str else []
            history.append({"role": role, "content": content})
            if len(history) > self.max_history * 2:
                history = history[-self.max_history * 2:]
            await redis.hset(key, "history", json.dumps(history))
            await redis.expire(key, self.ttl)
        except Exception:
            pass

    async def get_history(self, session_id: str) -> list[dict]:
        session = await self.get_session(session_id)
        if session:
            return session.get("history", [])
        return []

    async def clear_session(self, session_id: str):
        if session_id in _memory_store:
            del _memory_store[session_id]
            return
        try:
            redis = await get_redis()
            await redis.delete(f"agent:session:{session_id}")
        except Exception:
            pass
