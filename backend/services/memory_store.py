"""
services/memory_store.py
------------------------
In-memory conversation history store.

Responsibilities (single):
  - Store and retrieve per-session message history
  - Enforce a maximum of MAX_HISTORY messages per session
  - Expose a clean interface so no other service touches raw dicts

Design notes:
  - A plain dict is sufficient for a single-process server.
  - For multi-process / multi-pod deployments, swap the dict for
    a Redis client — only this file needs to change.
  - Thread-safety: Python's GIL protects simple dict operations in
    CPython, but the trim step uses a list slice which is also atomic.
    For production async workloads under high concurrency, wrap
    mutations in asyncio.Lock() if needed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

# Maximum number of messages (user + assistant combined) kept per session.
# 6 messages = 3 full user↔assistant turns of context.
MAX_HISTORY: int = 6


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Message:
    """
    A single turn in the conversation.

    Attributes:
        role:    "user" or "assistant"
        content: The raw text of the message
    """
    role:    Literal["user", "assistant"]
    content: str


# ── Store ─────────────────────────────────────────────────────────────────────

class MemoryStore:
    """
    Lightweight in-memory store for conversation histories.

    Each session_id maps to an ordered list of Message objects.
    The list is kept trimmed to the last MAX_HISTORY entries so
    memory usage stays bounded even in long conversations.

    Usage:
        store = MemoryStore()                               # one instance, shared
        store.add(session_id, role="user", content="...")
        history = store.get(session_id)                    # list[Message]
        store.trim(session_id)                             # prune to MAX_HISTORY
    """

    def __init__(self, max_history: int = MAX_HISTORY) -> None:
        self._max_history = max_history
        # defaultdict avoids KeyError on first access for any session
        self._store: dict[str, list[Message]] = defaultdict(list)

    # ── Public API ────────────────────────────────────────────────

    def add(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> None:
        """
        Append one message to a session's history.
        Does NOT trim automatically — call trim() explicitly after
        the full turn (user + assistant) is complete so the assistant
        reply is always included before pruning.
        """
        self._store[session_id].append(Message(role=role, content=content))

    def get(self, session_id: str) -> list[Message]:
        """
        Return a shallow copy of the session's history.
        Returns an empty list for unknown session IDs.
        """
        return list(self._store.get(session_id, []))

    def trim(self, session_id: str) -> None:
        """
        Keep only the last MAX_HISTORY messages for the session.
        Oldest messages are discarded first (FIFO eviction).
        No-op if the session has fewer than MAX_HISTORY messages.
        """
        history = self._store.get(session_id)
        if history and len(history) > self._max_history:
            # Slice in-place: keeps the list object, replacing its contents
            self._store[session_id] = history[-self._max_history :]

    def clear(self, session_id: str) -> None:
        """
        Delete all history for a session.
        Useful for explicit "new chat" actions from the frontend.
        """
        self._store.pop(session_id, None)

    def session_count(self) -> int:
        """Return the number of active sessions (useful for monitoring)."""
        return len(self._store)

memory_store = MemoryStore()