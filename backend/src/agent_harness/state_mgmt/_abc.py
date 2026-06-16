"""
File: backend/src/agent_harness/state_mgmt/_abc.py
Purpose: Category 7 ABCs — Checkpointer + Reducer + MessageStore.
Category: 範疇 7 (State Management)
Scope: Phase 49 / Sprint 49.1 (stub; impl in Phase 53.1)

Description:
    State is split transient (in-memory) / durable (DB). Checkpointer
    snapshots durable state at safe points (after tool, after verify,
    on HITL pause). Reducer is the ONLY mutator of LoopState — all
    other categories read state, produce updates, and Reducer merges
    them with monotonic versioning.

    Time-travel: load any past version via Checkpointer.

Owner: 01-eleven-categories-spec.md §範疇 7
Single-source: 17.md §2.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Sprint 57.127 — add MessageStore ABC (per-session message ledger)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent_harness._contracts import LoopState, Message, StateVersion, TraceContext


class Checkpointer(ABC):
    """Persists LoopState snapshots; supports time-travel."""

    @abstractmethod
    async def save(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> StateVersion: ...

    @abstractmethod
    async def load(
        self,
        *,
        version: int,
        trace_context: TraceContext | None = None,
    ) -> LoopState: ...

    @abstractmethod
    async def time_travel(
        self,
        *,
        target_version: int,
        trace_context: TraceContext | None = None,
    ) -> LoopState:
        """Reload state at a past version. Used for debugging + replay."""
        ...


class MessageStore(ABC):
    """Persists + rehydrates the per-session Cat-3 Message ledger (Sprint 57.127).

    The durable conversation history a follow-up send rehydrates so the live
    loop keeps multi-turn context (closes `AD-ChatV2-Live-MultiTurn-Context`).
    An impl is bound to one (session_id, tenant_id) at construction (mirrors the
    Checkpointer binding); the loop self-loads at run() start + appends the run's
    NEW messages at clean completion. Provider-neutral — operates only on the
    Cat-3 Message dataclass (no provider / DB type in this contract).

    Distinct from Checkpointer (which snapshots durable LoopState, EXCLUDING the
    message buffer per the US-3 split) and from the `message_events` SSE-replay
    ledger (57.125/126, for the frontend history UI) — this is the verbatim
    Message ledger the loop consumes.
    """

    @abstractmethod
    async def load(self) -> list[Message]:
        """Return the bound session's prior messages, oldest-first (by sequence)."""
        ...

    @abstractmethod
    async def append(self, messages: list[Message], *, turn_num: int) -> None:
        """Append NEW messages to the ledger (sequence_num continues from the
        session MAX). Best-effort — a persistence failure MUST NOT break the loop."""
        ...


class Reducer(ABC):
    """The ONLY mutator of LoopState. Categories submit updates here."""

    @abstractmethod
    async def merge(
        self,
        state: LoopState,
        update: dict[str, Any],
        *,
        source_category: str,
        trace_context: TraceContext | None = None,
    ) -> LoopState:
        """Apply update with monotonic version increment + audit trail."""
        ...
