"""
File: backend/src/platform_layer/handoff/context_carry.py
Purpose: LLM-neutral helpers to cap/serialize + render a parent's conversation for a HANDOFF child.
Category: platform_layer (Cat 11 HANDOFF support — agent-side context carry)
Scope: Phase 57 / Sprint 57.69 (A-3b backend slice, Stage 1)

Description:
    When a Cat 11 HANDOFF ends the parent loop, the parent's in-memory
    conversation is snapshotted onto LoopCompleted.handoff_context (a list of
    neutral Message). This module turns that snapshot into a compact,
    JSON-serializable form for storage in the booted child's
    meta_data["carried_context"], and renders the stored form into a
    system-prompt block the child agent reads as its prior context.

    The cap is a last-N MESSAGE COUNT (not a token budget) so this module stays
    ChatClient-free and LLM-provider-neutral — no tokenizer / SDK import. The
    oldest messages are dropped when the conversation exceeds the cap.

Key Components:
    - DEFAULT_MAX_CARRY_MESSAGES: int — last-N message-count cap (20)
    - cap_and_serialize(messages, *, max_messages): list[dict[str, str]]
    - render_carried_context_block(carried): str — system-prompt block

Created: 2026-06-02 (Sprint 57.69 A-3b)
Last Modified: 2026-06-02

Modification History (newest-first):
    - 2026-06-02: Initial creation (Sprint 57.69 A-3b) — cap/serialize + render carried context

Related:
    - agent_harness/_contracts/chat.py — Message / ContentBlock (neutral)
    - agent_harness/_contracts/events.py — LoopCompleted.handoff_context (source)
    - platform_layer/handoff/service.py — boot_handoff stores carried_context
    - api/v1/chat/handler.py — resolve_session_persona renders the block
    - sprint-57-69-plan.md §3 — agent-side context carry
"""

from __future__ import annotations

from agent_harness._contracts.chat import ContentBlock, Message

# Last-N message-count cap for carried context. A message COUNT (not a token
# budget) keeps this module ChatClient-free / LLM-provider-neutral — no
# tokenizer import. Messages over the cap are dropped oldest-first.
DEFAULT_MAX_CARRY_MESSAGES = 20

# Header line that prefixes the rendered carried-context block. Lets the child
# handler detect (and tests assert) the carried block in the persona prompt.
_CARRIED_CONTEXT_HEADER = "## Prior conversation (handed off from the previous agent)"


# === _render_content: flatten a Message.content to plain text ===============
# Why: a Message.content is either a plain str or a list[ContentBlock]
# (multimodal). The carried context is text-only (it seeds a system prompt), so
# block content collapses to the non-empty `.text` of each block joined by
# newlines. Non-text blocks (image / tool_use) contribute no text.
def _render_content(content: str | list[ContentBlock]) -> str:
    """Flatten a Message.content (str or list[ContentBlock]) to plain text."""
    if isinstance(content, str):
        return content
    parts = [block.text for block in content if block.text]
    return "\n".join(parts)


# === cap_and_serialize: snapshot -> JSON-serializable carried context =======
# Why: LoopCompleted.handoff_context is a list of neutral Message objects (not
# JSON-serializable for meta_data storage). This caps to the last-N messages
# (drop oldest over budget) and maps each to a {"role", "content"} dict so the
# booted child's meta_data["carried_context"] is compact + persistable.
def cap_and_serialize(
    messages: list[Message] | None,
    *,
    max_messages: int = DEFAULT_MAX_CARRY_MESSAGES,
) -> list[dict[str, str]]:
    """Cap to the last `max_messages` and serialize to {"role", "content"} dicts.

    Args:
        messages: the parent's snapshotted conversation (or None / empty).
        max_messages: keep at most this many of the MOST RECENT messages;
            messages over the budget are dropped oldest-first.

    Returns:
        A list of {"role": ..., "content": ...} dicts (oldest-to-newest within
        the kept window). Empty list for None / empty input.
    """
    if not messages:
        return []
    kept = messages[-max_messages:] if max_messages > 0 else []
    return [{"role": message.role, "content": _render_content(message.content)} for message in kept]


# === render_carried_context_block: carried dicts -> system-prompt block =====
# Why: the booted child runs as its target persona; the carried conversation is
# appended to that persona prompt so the child sees the prior context. Renders
# the stored {"role", "content"} dicts into a readable, header-prefixed block.
def render_carried_context_block(carried: list[dict[str, str]]) -> str:
    """Render carried {"role", "content"} dicts into a system-prompt block.

    Args:
        carried: the stored carried context (from
            meta_data["carried_context"]).

    Returns:
        A header-prefixed block (header + one `[role] content` line per entry),
        or "" when there is nothing to render.
    """
    if not carried:
        return ""
    lines = [_CARRIED_CONTEXT_HEADER]
    for entry in carried:
        role = entry.get("role", "")
        content = entry.get("content", "")
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_MAX_CARRY_MESSAGES",
    "cap_and_serialize",
    "render_carried_context_block",
]
