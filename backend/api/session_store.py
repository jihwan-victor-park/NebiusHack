"""
In-memory session store.
Each session holds conversation history + last scored product list.
"""
import uuid
from dataclasses import dataclass, field


@dataclass
class SessionData:
    id: str
    messages: list        # [{role, content}]  — raw history for LLM
    products: list        # last scored product dicts
    intent: dict | None   # last ParsedIntent as dict


_store: dict[str, SessionData] = {}


def create() -> SessionData:
    sid = str(uuid.uuid4())[:8]
    s = SessionData(id=sid, messages=[], products=[], intent=None)
    _store[sid] = s
    return s


def get(sid: str) -> SessionData | None:
    return _store.get(sid)
