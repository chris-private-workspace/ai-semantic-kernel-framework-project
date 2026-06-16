"""
File: backend/src/agent_harness/_contracts/message_serde.py
Purpose: Message <-> JSONB-safe dict serde — shared by pause-resume + the messages ledger.
Category: 範疇 3 adjacent (Cat-3 Message contract serde; provider-neutral)
Scope: Phase 57 / Sprint 57.127

Description:
    Serializes the Cat-3 `Message` dataclass (role / content / tool_calls /
    tool_call_id / name) to a JSONB-safe dict and back. Relocated here from
    `orchestrator_loop/loop.py` (Sprint 57.127) so it can be imported by BOTH:
      1. the deferred-HITL pause path (`loop.messages_from_metadata`, 57.88), and
      2. the new `messages`-table ledger (`state_mgmt.message_store.DBMessageStore`,
         57.127 — live multi-turn rehydration).
    Living in the `_contracts` leaf lets `state_mgmt` import it WITHOUT importing
    the heavy `orchestrator_loop.loop` module (circular-import safety).

    Fidelity note: `metadata` (the Message's local-bookkeeping flags — NOT sent to
    the LLM provider) is NOT round-tripped (it never was — the 57.88 pause path
    has the same limitation). Rehydrated messages lose their compaction/prompt
    tags; this does not affect the LLM's context (content/role/tool_calls are
    preserved). `list[ContentBlock]` content is round-tripped best-effort.

Key Components:
    - _message_to_dict(msg): Message -> JSONB-safe dict
    - _message_from_dict(data): dict -> Message
    - _content_block_to_dict(block): ContentBlock -> dict (internal)

Created: 2026-06-16 (Sprint 57.127)
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Initial creation (Sprint 57.127) — relocated from loop.py; shared serde

Related:
    - _contracts/chat.py — the Message / ContentBlock / ToolCall dataclasses
    - orchestrator_loop/loop.py §messages_from_metadata — the 57.88 pause consumer
    - state_mgmt/message_store.py — the 57.127 messages-table ledger consumer
"""

from __future__ import annotations

from typing import Any

from agent_harness._contracts.chat import ContentBlock, Message, ToolCall


def _message_to_dict(msg: Message) -> dict[str, Any]:
    """Serialize a Message to a JSONB-safe dict (57.88 US-2)."""
    content: Any
    if isinstance(msg.content, str):
        content = msg.content
    else:
        # list[ContentBlock] — best-effort (not on the pause happy-path).
        content = [_content_block_to_dict(b) for b in msg.content]
    return {
        "role": msg.role,
        "content": content,
        "tool_calls": (
            [
                {"id": tc.id, "name": tc.name, "arguments": dict(tc.arguments)}
                for tc in msg.tool_calls
            ]
            if msg.tool_calls
            else None
        ),
        "tool_call_id": msg.tool_call_id,
        "name": msg.name,
    }


def _content_block_to_dict(block: ContentBlock) -> dict[str, Any]:
    """Serialize a ContentBlock to a JSONB-safe dict (best-effort, 57.88 US-2)."""
    return {
        "type": block.type,
        "text": block.text,
        "image_url": block.image_url,
        "tool_use_id": block.tool_use_id,
        "tool_use_name": block.tool_use_name,
        "tool_use_input": block.tool_use_input,
        "tool_result_for_id": block.tool_result_for_id,
        "tool_result_content": block.tool_result_content,
    }


def _message_from_dict(data: dict[str, Any]) -> Message:
    """Rebuild a Message from a `_message_to_dict` payload (57.88 US-2)."""
    raw_content = data.get("content", "")
    content: str | list[ContentBlock]
    if isinstance(raw_content, list):
        content = [ContentBlock(**{k: v for k, v in b.items()}) for b in raw_content]
    else:
        content = str(raw_content)
    raw_calls = data.get("tool_calls")
    tool_calls = (
        [
            ToolCall(
                id=str(c.get("id", "")),
                name=str(c.get("name", "")),
                arguments=dict(c.get("arguments", {})),
            )
            for c in raw_calls
        ]
        if raw_calls
        else None
    )
    return Message(
        role=data.get("role", "user"),
        content=content,
        tool_calls=tool_calls,
        tool_call_id=data.get("tool_call_id"),
        name=data.get("name"),
    )
