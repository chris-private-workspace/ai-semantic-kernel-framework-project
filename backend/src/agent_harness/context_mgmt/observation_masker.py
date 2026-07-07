"""
File: backend/src/agent_harness/context_mgmt/observation_masker.py
Purpose: DefaultObservationMasker — redacts old role="tool" message bodies while keeping tool_calls intact.  # noqa: E501
Category: 範疇 4 (Context Management)
Scope: Phase 52 / Sprint 52.1 Day 3

Description:
    DefaultObservationMasker preserves the *fact* that tools were called by
    keeping every assistant message's `tool_calls` field, but replaces the
    body of old `role="tool"` messages (older than `keep_recent` user→
    assistant turns) with a tombstone string of the form:

        "[REDACTED: tool {name} result; bytes={n}]"

    Effect: the agent still knows it called tool X, but the heavy result
    blob no longer occupies tokens. role="user" / "system" / "assistant"
    content is never touched.

Why this exists:
    V1 ignored context rot (AP-7). Long conversations blew context windows
    not on user/assistant text but on stale tool result blobs that no
    longer matter. Masking is a cheap structural mitigation that runs
    before LLM-driven semantic compaction.

Owner: 01-eleven-categories-spec.md §範疇 4
Single-source: 17-cross-category-interfaces.md §2.1 (ObservationMasker row)

Related:
    - _abc.py ObservationMasker ABC
    - compactor/structural.py (Day 3.3 — wires injection of this masker)
    - 04-anti-patterns.md AP-7 (Context Rot Ignored — root motivation)

Created: 2026-05-01 (Sprint 52.1 Day 3.1)

Modification History:
    - 2026-07-07: Sprint 57.160 — add opt-in tool-result-recency anchor mode (closes AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path)
    - 2026-05-01: Initial creation (Sprint 52.1 Day 3.1) — default masker impl
"""

from __future__ import annotations

from dataclasses import replace

from agent_harness._contracts import Message
from agent_harness.context_mgmt._abc import ObservationMasker


def _tombstone(msg: Message) -> Message:
    """Replace a role="tool" message body with a size tombstone; keep the rest of the message."""
    tool_name = msg.name or "unknown"
    content_str = msg.content if isinstance(msg.content, str) else "[content blocks]"
    byte_count = len(content_str) if isinstance(content_str, str) else 0
    return replace(msg, content=f"[REDACTED: tool {tool_name} result; bytes={byte_count}]")


class DefaultObservationMasker(ObservationMasker):
    """Tombstone-style masker; keeps tool_calls field, redacts old tool bodies.

    Anchor modes (Sprint 57.160):
      - user-anchored (default, tool_anchor_keep=None): the keep-window is measured
        in USER-message count — the recent keep_recent user turns stay intact. The
        original Sprint 52.1 behaviour (byte-identical when tool_anchor_keep is None).
      - tool-anchored (tool_anchor_keep=N >= 1, opt-in via the factory env lever
        CHAT_COMPACTION_TOOL_ANCHORED_MASKING): the keep-window is measured in
        role="tool" RESULT recency — the last N tool results stay intact, older tool
        blobs are tombstoned — so masking reduces WITHIN a single user turn. Fixes
        AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path (57.159): the chat main flow
        runs one user message per send, so the user-anchored window never fires inside
        a long single-user-turn tool run (observation was 4k->35k, 8 no-op compactions).
    """

    def __init__(self, *, tool_anchor_keep: int | None = None) -> None:
        # None = original user-anchored path (byte-identical). >= 1 = switch to
        # tool-result-recency anchoring (keep the last N tool results intact).
        self.tool_anchor_keep = tool_anchor_keep

    def mask_old_results(
        self,
        messages: list[Message],
        *,
        keep_recent: int = 5,
    ) -> list[Message]:
        if not messages:
            return []
        if self.tool_anchor_keep is not None:
            return self._mask_tool_anchored(messages)
        return self._mask_user_anchored(messages, keep_recent=keep_recent)

    def _mask_user_anchored(self, messages: list[Message], *, keep_recent: int) -> list[Message]:
        # Anchor "turn" boundaries on user messages: the keep_recent-th-from-last
        # user message marks the cutoff. Everything from that user onwards is
        # untouched; older role="tool" messages get tombstoned.
        user_indices = [i for i, m in enumerate(messages) if m.role == "user"]
        if len(user_indices) <= keep_recent:
            return list(messages)

        cutoff_idx = user_indices[-keep_recent]

        out: list[Message] = []
        for i, msg in enumerate(messages):
            if msg.role == "tool" and i < cutoff_idx:
                out.append(_tombstone(msg))
            else:
                out.append(msg)
        return out

    def _mask_tool_anchored(self, messages: list[Message]) -> list[Message]:
        # Anchor the keep-window on tool-RESULT recency: keep the last N role="tool"
        # results intact, tombstone every older tool result. Independent of user-turn
        # count, so it reduces within a single-user-turn tool run. system / user /
        # assistant (incl. tool_calls provenance) are never touched.
        keep = self.tool_anchor_keep or 0
        if keep < 1:
            # Defensive: a non-positive anchor is a passthrough (the factory env
            # reader already floors at 1; guards the tool_indices[-0]==[0] footgun).
            return list(messages)

        tool_indices = [i for i, m in enumerate(messages) if m.role == "tool"]
        if len(tool_indices) <= keep:
            return list(messages)

        cutoff_idx = tool_indices[-keep]

        out: list[Message] = []
        for i, msg in enumerate(messages):
            if msg.role == "tool" and i < cutoff_idx:
                out.append(_tombstone(msg))
            else:
                out.append(msg)
        return out
