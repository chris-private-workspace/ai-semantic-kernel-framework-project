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
    - build_memory_block(accesses, *, char_budget): the injected-memory grounding formatter (57.153)
    - _content_to_text(): collapse str | list[ContentBlock] to a one-line string

LLM Provider Neutrality: operates on the neutral `Message` dataclass only; no SDK import.

Created: 2026-06-13 (Sprint 57.111 A3)
Last Modified: 2026-07-01

Modification History (newest-first):
    - 2026-07-01: Sprint 57.153 — add build_memory_block (memory-aware judge grounding)
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

# Sprint 57.153: memory-grounding block bounds (independent of the trace bounds — the
# memory block is a separate, smaller grounding section; env override below).
_DEFAULT_MEMORY_CHAR_BUDGET = 1500
_PER_MEMORY_CAP = 300


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


def build_memory_block(
    accesses: list[Any],
    *,
    char_budget: int | None = None,
) -> str:
    """Render the memory injected into this turn's prompt as a bounded grounding block.

    The in-loop Cat 10 judge (Sprint 57.153, AD-Verification-Judge-Memory-Inject-Blind)
    reads this so a recall grounded in injected memory is NOT false-positive-rejected as
    fabrication. The injected memory (57.148 `profile()` + 57.151 `recent_sessions()`)
    lives in the per-turn PromptBuilder artifact (the system prompt), never in `messages`,
    and `build_trace_block` drops system messages — so the verify gate threads the captured
    `memory_accesses` (builder.py:397 — `{scope, time_scale, key, summary}`; `summary` is the
    MemoryHint's PII-safe capped summary, NOT raw content) here instead, as a section the
    judge weighs alongside `{output}` and `{trace}`.

    Renders each access as `[memory:{scope}] {summary}` (one capped line). Returns "" when
    there is nothing to show (empty list / budget 0 / no non-empty summaries) — the judge
    then critiques the output + trace alone, byte-identical to pre-57.153. When the joined
    block exceeds `char_budget` the LOWEST-priority (tail) lines are dropped, keeping the
    head: `memory_accesses` is top-k confidence-ordered within a layer, so the head carries
    the most relevant grounding. Env override: CHAT_VERIFICATION_MEMORY_CHAR_BUDGET.
    """
    if char_budget is None:
        char_budget = _env_int("CHAT_VERIFICATION_MEMORY_CHAR_BUDGET", _DEFAULT_MEMORY_CHAR_BUDGET)
    if not accesses or char_budget <= 0:
        return ""

    lines: list[str] = []
    for acc in accesses:
        # Defensive .get — the access dicts come from builder.py layer_metadata, but a
        # future producer shape change should degrade gracefully, not crash the judge.
        get = acc.get if isinstance(acc, dict) else (lambda _k, _d="": _d)
        scope = str(get("scope", "") or "")
        summary = str(get("summary", "") or "").strip().replace("\n", " ")
        if not summary:
            continue
        if len(summary) > _PER_MEMORY_CAP:
            summary = summary[:_PER_MEMORY_CAP] + "…"
        prefix = f"[memory:{scope}] " if scope else "[memory] "
        lines.append(prefix + summary)
    if not lines:
        return ""

    block = "\n".join(lines)
    if len(block) > char_budget:
        # Keep the highest-priority head; drop the trailing partial line so we never end
        # mid-sentence (opposite of the trace block, which keeps the recent tail).
        block = block[:char_budget]
        nl = block.rfind("\n")
        if nl != -1:
            block = block[:nl]
    return block
