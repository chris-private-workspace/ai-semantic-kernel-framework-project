"""
File: backend/src/agent_harness/verification/_trace.py
Purpose: Build a bounded trace block (recent turns + tool errors) for the trace-aware judge.
Category: 範疇 10 (Verification Loops)
Scope: Phase 57 / Sprint 57.111 (A3)

Description:
    A1 (57.98) moved the verify gate in-loop and laid the `Verifier.verify(*, output,
    state, trace_context)` plumbing, but the gate passed `state=None` so the judge only
    ever saw the final answer string. A3 makes the LLM judge trace-aware: the gate now
    passes the real loop state, and this module turns its `messages` into a compact
    `{trace}` block the judge weighs alongside `{output}` — so a critique can reference
    a mid-trace tool error or a prior turn, not just the final string.

    Bounded by design (the judge runs on the cheap tier, but an unbounded history would
    inflate cost): a recent-message window + a per-message + total char budget. The
    candidate answer is NOT in the trace — the gate calls this BEFORE appending it
    (loop.py:2552), so there is no double-counting.

Key Components:
    - build_trace_block(messages, *, max_messages, char_budget): the formatter
    - _content_to_text(): collapse str | list[ContentBlock] to a one-line string

LLM Provider Neutrality: operates on the neutral `Message` dataclass only; no SDK import.

Created: 2026-06-13 (Sprint 57.111 A3)

Modification History (newest-first):
    - 2026-06-13: Initial creation (Sprint 57.111 A3) — trace-aware judge input builder

Related:
    - verification/llm_judge.py (the consumer — substitutes the block into {trace})
    - orchestrator_loop/loop.py:_cat10_verify_gate (builds the trace_state passed to verify)
    - 25-verification-in-loop-design.md §2.6 (A3 trace-aware invariant)
"""

from __future__ import annotations

import os
from typing import Any

from agent_harness._contracts.chat import Message

# Why module constants + env override (not core.config Settings / not per-tenant):
# these are internal judge-input tuning knobs, not tenant policy (per-tenant verification
# is C3, out of scope for A3). Keeping them here avoids touching core/config and keeps
# the trace concern inside the verification package. Tests pass explicit args for
# determinism; production reads the env override.
_DEFAULT_MAX_MESSAGES = 8
_DEFAULT_CHAR_BUDGET = 2000
_PER_MESSAGE_CAP = 400


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def _content_to_text(content: str | list[Any], *, per_msg_cap: int) -> str:
    """Collapse a Message.content (str OR list[ContentBlock]) to a single trimmed line."""
    if isinstance(content, str):
        text = content
    else:
        # list[ContentBlock]: join any text-bearing blocks; tolerate unknown block shapes.
        parts: list[str] = []
        for block in content:
            t = getattr(block, "text", None)
            if isinstance(t, str) and t:
                parts.append(t)
        text = " ".join(parts) if parts else ""
    text = text.strip().replace("\n", " ")
    if len(text) > per_msg_cap:
        text = text[:per_msg_cap] + "…"
    return text


def build_trace_block(
    messages: list[Message],
    *,
    max_messages: int | None = None,
    char_budget: int | None = None,
) -> str:
    """Render the recent non-system messages (incl. tool results) as a bounded trace.

    Returns "" when there is nothing to show (the judge then critiques the output alone,
    byte-identical to the pre-A3 final-string-only behavior). System messages are dropped
    (the judge already has its own instructions); assistant tool calls are annotated so a
    `[tool] error...` result reads in context of the call that produced it.

    Bounds: the last `max_messages` messages, each capped at `_PER_MESSAGE_CAP` chars,
    the whole block capped at `char_budget` (the OLDEST lines are dropped first — recency
    is what a critique needs). All bounds have env overrides
    (CHAT_VERIFICATION_TRACE_MAX_MESSAGES / _CHAR_BUDGET).
    """
    if max_messages is None:
        max_messages = _env_int("CHAT_VERIFICATION_TRACE_MAX_MESSAGES", _DEFAULT_MAX_MESSAGES)
    if char_budget is None:
        char_budget = _env_int("CHAT_VERIFICATION_TRACE_CHAR_BUDGET", _DEFAULT_CHAR_BUDGET)
    if not messages or max_messages <= 0 or char_budget <= 0:
        return ""

    relevant = [m for m in messages if m.role != "system"]
    if not relevant:
        return ""
    window = relevant[-max_messages:]

    lines: list[str] = []
    for m in window:
        text = _content_to_text(m.content, per_msg_cap=_PER_MESSAGE_CAP)
        if m.role == "assistant" and m.tool_calls:
            called = ", ".join(tc.name for tc in m.tool_calls)
            text = (f"{text} [called: {called}]").strip()
        lines.append(f"[{m.role}] {text}")

    block = "\n".join(lines)
    if len(block) > char_budget:
        # Keep the most recent tail; drop the leading partial line so we never start
        # mid-sentence.
        block = block[-char_budget:]
        nl = block.find("\n")
        if nl != -1:
            block = block[nl + 1 :]
    return block
