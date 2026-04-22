"""
services/memory_store.py  (v2 — session metadata added)
--------------------------------------------------------
In-memory conversation history store.

CHANGE LOG (v2):
  - Added _meta dict to store per-session metadata
  - Added get_meta(session_id) — returns metadata dict for a session
  - Added update_meta(session_id, data) — merges data into session metadata
  - All existing methods (add, get, trim, clear, session_count) UNCHANGED
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

# Maximum number of messages (user + assistant combined) kept per session.
# 6 messages = 3 full user↔assistant turns of context.
MAX_HISTORY: int = 6


# ── Data model (unchanged) ────────────────────────────────────────────────────

@dataclass
class Message:
    """A single turn in the conversation."""
    role:    Literal["user", "assistant"]
    content: str


# ── Store ─────────────────────────────────────────────────────────────────────

class MemoryStore:
    """
    Lightweight in-memory store for conversation histories and session metadata.

    Conversation methods (unchanged):
        add(session_id, role, content)
        get(session_id) → list[Message]
        trim(session_id)
        clear(session_id)
        session_count() → int

    Metadata methods (new in v2):
        get_meta(session_id) → dict
        update_meta(session_id, data: dict)
    """

    def __init__(self, max_history: int = MAX_HISTORY) -> None:
        self._max_history = max_history
        # defaultdict avoids KeyError on first access for any session
        self._store: dict[str, list[Message]] = defaultdict(list)
        # Stores per-session metadata: last_decision, last_state, etc.
        self._meta:  dict[str, dict] = defaultdict(dict)

    # ── Conversation API (unchanged) ──────────────────────────────

    def add_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> None:
        """Append one message. Does NOT trim — call trim() after the full turn."""
        self._store[session_id].append(Message(role=role, content=content))

    def get_history(self, session_id: str) -> list[Message]:
        """Return a shallow copy of the session's message history."""
        return list(self._store.get(session_id, []))

    def trim(self, session_id: str) -> None:
        """Keep only the last MAX_HISTORY messages. No-op if under limit."""
        history = self._store.get(session_id)
        if history and len(history) > self._max_history:
            self._store[session_id] = history[-self._max_history :]

    def clear(self, session_id: str) -> None:
        """Delete all history and metadata for a session."""
        self._store.pop(session_id, None)
        self._meta.pop(session_id, None)

    def session_count(self) -> int:
        """Return number of active sessions."""
        return len(self._store)

    # ── Metadata API (new in v2) ──────────────────────────────────

    def get_meta(self, session_id: str) -> dict:
        """
        Return a shallow copy of the metadata dict for a session.
        Returns an empty dict for unknown sessions — never raises.

        Keys populated by ai_service:
            last_decision (str)  — e.g. "ask", "respond", "escalate"
            last_state    (dict) — the interpreted dict from last turn
        """
        return dict(self._meta.get(session_id, {}))

    def update_meta(self, session_id: str, data: dict) -> None:
        """
        Merge `data` into the session's metadata dict.
        Existing keys are overwritten; unmentioned keys are preserved.
        """
        self._meta[session_id].update(data)


# ── Module-level singleton ────────────────────────────────────────────────────
# Imported by ai_service.py as: from services.memory_store import memory_store

memory_store = MemoryStore()
