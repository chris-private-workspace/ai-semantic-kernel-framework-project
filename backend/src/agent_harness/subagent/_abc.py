"""
File: backend/src/agent_harness/subagent/_abc.py
Purpose: Category 11 ABC — SubagentDispatcher (4 modes, NO worktree).
Category: 範疇 11 (Subagent Orchestration)
Scope: Phase 49 / Sprint 49.1 (stub; impl in Phase 54.2)

Description:
    Dispatches subagents: fork (parallel), teammate (mailbox), as_tool
    (LLM calls as tool). HANDOFF (transfer control) is NOT dispatcher-served:
    the loop's output classifier terminates the run with stop_reason="handoff"
    and the platform layer boots the child session (Sprint 57.107 B3).

    Worktree mode (CC has it) is INTENTIONALLY OMITTED for V2 — server
    runs in single workspace; no per-process git checkout.

Owner: 01-eleven-categories-spec.md §範疇 11
Single-source: 17.md §2.1

Created: 2026-04-29 (Sprint 49.1)

Modification History:
    - 2026-06-12: Sprint 57.107 (B3) — drop handoff() ABC method (loop-intercepted path)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from agent_harness._contracts import (
    SubagentBudget,
    SubagentMode,
    SubagentResult,
    TraceContext,
)


class SubagentDispatcher(ABC):
    """Dispatch subagents in fork/teammate/as_tool mode (handoff = loop-intercepted)."""

    @abstractmethod
    async def spawn(
        self,
        *,
        mode: SubagentMode,
        task: str,
        parent_session_id: UUID,
        budget: SubagentBudget | None = None,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        """Returns the subagent_id; subagent runs async."""
        ...

    @abstractmethod
    async def wait_for(
        self,
        subagent_id: UUID,
        *,
        timeout_s: int | None = None,
        trace_context: TraceContext | None = None,
    ) -> SubagentResult: ...
