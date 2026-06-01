"""
File: backend/src/agent_harness/prompt_builder/templates.py
Purpose: Cat 5 prompt section templates + shared format helpers.
Category: 範疇 5 (Prompt Construction)
Scope: Phase 52 / Sprint 52.2 (Day 1.5)

Description:
    String templates and pure-function format helpers used by
    DefaultPromptBuilder and all 3 PositionStrategy implementations:
    - SYSTEM_ROLE_TEMPLATE: default agent system role
    - MEMORY_SECTION_HEADER / MEMORY_HINT_FORMAT: layer header + hint line
    - _memory_as_messages: dict[layer -> hints] → list[Message]
    - _summarize: truncate Message.content for LostInMiddle echo anchor

    All helpers are stateless and IO-free. Memory layer ordering is the
    caller's responsibility (DefaultPromptBuilder pre-sorts by time_scale
    priority before calling _memory_as_messages).

Created: 2026-05-01 (Sprint 52.2 Day 1.5)
Last Modified: 2026-06-01

Modification History (newest-first):
    - 2026-06-01: Sprint 57.65 — enrich hint line + verify-before-use header (A-1)

Related:
    - sprint-52-2-plan.md §2.4 / §2.5
    - 01-eleven-categories-spec.md §範疇 5 — Lost-in-Middle
"""

from __future__ import annotations

from agent_harness._contracts import ContentBlock, MemoryHint, Message

# ---------------------------------------------------------------------------
# Templates (constants)
# ---------------------------------------------------------------------------

SYSTEM_ROLE_TEMPLATE = (
    "You are an enterprise AI agent. Follow tool calling conventions "
    "and respect HITL approval gates. Stay grounded in the provided "
    "memory and refuse out-of-scope requests."
)
"""Default system role for DefaultPromptBuilder._build_system_section()."""

MEMORY_SECTION_HEADER = "=== {layer} Memory ==="
"""Header prefix for each memory layer's system message."""

MEMORY_HINT_FORMAT = "- {summary} (confidence {confidence:.2f}{verified})"
"""Single-line format for one MemoryHint inside a layer section.

Sprint 57.65 (A-1 Tier2): enriched from bare ``- {summary}`` to surface the
hint's intrinsic ``confidence`` and (when present) ``last_verified_at`` so the
model can weight stale / low-credibility hints. ``{verified}`` is a pre-formatted
suffix ("", or ", last verified <iso>") supplied by ``_format_hint_line``.
"""

VERIFY_BEFORE_USE_HEADER = (
    "Some memory hints below are marked verify-before-use: confirm them against "
    "live state before acting, and correct via memory_write on mismatch. Hints to "
    "verify:"
)
"""Lead-then-verify instruction injected into the system prompt whenever any
rendered hint carries verify_before_use=True (Sprint 57.65, per 10.md §原則3)."""

# ---------------------------------------------------------------------------
# Format helpers (used by DefaultPromptBuilder + PositionStrategy implementations)
# ---------------------------------------------------------------------------


def _format_hint_line(hint: MemoryHint) -> str:
    """Render one MemoryHint as a single deterministic prompt line.

    Sprint 57.65 (A-1 Tier2): surfaces summary + confidence + last_verified_at
    (when present) so the model can weight credibility. The summary is the only
    text inlined — full_content_pointer is a DB / vector ref and is NOT inlined
    (it would be a wasted, unusable token cost; resolve on demand via tools).
    """
    verified = (
        f", last verified {hint.last_verified_at.isoformat()}"
        if hint.last_verified_at is not None
        else ""
    )
    return MEMORY_HINT_FORMAT.format(
        summary=hint.summary, confidence=hint.confidence, verified=verified
    )


def _memory_as_messages(memory_layers: dict[str, list[MemoryHint]]) -> list[Message]:
    """Convert memory hints grouped by layer into system messages.

    Each non-empty layer becomes one system message containing the formatted
    hints. Caller controls layer ordering (DefaultPromptBuilder emits the layers
    in the fixed system→tenant→role→user→session order so the rendered block is
    deterministic across builds).

    Args:
        memory_layers: dict[layer_name -> list[MemoryHint]]. Layer names are
            from 51.2 MemoryHint.layer (e.g., "system", "tenant", "role",
            "user", "session"). Empty layers are skipped.

    Returns:
        One Message per non-empty layer, in dict insertion order.
    """
    out: list[Message] = []
    for layer_name, hints in memory_layers.items():
        if not hints:
            continue
        lines = [MEMORY_SECTION_HEADER.format(layer=layer_name.title())]
        for h in hints:
            # MemoryHint uses `summary` (token-cheap text); see _contracts/memory.py
            lines.append(_format_hint_line(h))
        out.append(
            Message(
                role="system",
                content="\n".join(lines),
                metadata={"memory_layer": layer_name, "hint_count": len(hints)},
            )
        )
    return out


def _content_to_text(content: str | list[ContentBlock]) -> str:
    """Best-effort flatten of Message.content to plain text for summarization."""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            parts.append(str(text))
    return " ".join(parts)


def _summarize(content: str | list[ContentBlock], *, max_chars: int = 200) -> str:
    """Truncate content to max_chars (with ellipsis) for the LostInMiddle echo."""
    text = _content_to_text(content)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
