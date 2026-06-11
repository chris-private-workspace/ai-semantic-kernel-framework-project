"""
File: backend/src/agent_harness/_contracts/inbox.py
Purpose: MessageInbox — the between-turns message inbox the loop drains at each turn boundary.
Category: 範疇 1 (Orchestrator Loop)
Scope: Phase 57 / Sprint 57.101 (B1 — between-turns message injection primitive)

Description:
    A small Cat 1 contract: an optional source of `Message`s the AgentLoop drains
    at the TOP of each turn iteration (the 57.92 between-turns seam), BEFORE the
    between-turns guardrail — so anything injected mid-run joins the conversation
    at the NEXT turn boundary (it cannot interrupt an in-flight LLM/tool call) and
    is Cat 9-checked for free. The loop depends only on this ABC, not on any
    concrete backing:
      - chat live-injection (B1): backed by a module-level InjectionRegistry queue
        keyed by session_id (api/v1/chat/injection_registry.py); the inject POST
        and the streaming run are SEPARATE HTTP requests, so the backing must be
        process-level (a per-request mailbox cannot bridge them).
      - TEAMMATE parent→child (B2, future): the child loop's inbox is a view over
        the parent's mailbox channel — same ABC, different backing.

Key Components:
    - MessageInbox: ABC; `async def drain() -> list[Message]` (non-blocking — return
      all currently-queued messages, [] if none).

Created: 2026-06-11 (Sprint 57.101)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.101) — MessageInbox between-turns drain contract

Related:
    - 01-eleven-categories-spec.md §範疇 1
    - 17-cross-category-interfaces.md §1 (Cat 1 contracts)
    - orchestrator_loop/loop.py (_run_turns drains the inbox before the Cat 9 between-turns gate)
    - api/v1/chat/injection_registry.py (the B1 chat backing: InjectionRegistry + QueueMessageInbox)
    - claudedocs/1-planning/harness-deepening-proposal-20260610.md §2.2 (B1)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_harness._contracts.chat import Message


# === MessageInbox: between-turns message source ============================
# Why: the user (B1) — or a parent agent (B2) — may want to add an instruction
# while the loop is already running. The loop can only act on it at a turn
# boundary (interrupting an in-flight LLM call would be a lie about what the loop
# can do), so the loop drains an inbox at the top of each iteration. Keeping this
# an ABC (not a concrete queue) lets the same loop seam serve both the chat
# InjectionRegistry backing and the future TEAMMATE mailbox backing.
class MessageInbox(ABC):
    """An optional source of mid-run messages the loop drains at each turn boundary."""

    @abstractmethod
    async def drain(self) -> list[Message]:
        """Return all currently-queued messages (non-blocking); `[]` if none.

        Called at the TOP of every `_run_turns` iteration (before the between-turns
        guardrail). MUST NOT block waiting for new messages — it returns whatever is
        queued right now so the loop never stalls on an empty inbox.
        """
        ...
