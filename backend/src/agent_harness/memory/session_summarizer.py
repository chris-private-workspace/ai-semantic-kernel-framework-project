"""
File: backend/src/agent_harness/memory/session_summarizer.py
Purpose: Cheap-tier rolling summarizer — conversation ledger -> memory_session_summary.
Category: 範疇 3 (Memory) / Layer 5 session summary formation
Scope: Phase 57 / Sprint 57.151

Description:
    SessionSummarizer reads a session's message ledger, prompts the LLM (via the
    neutral ChatClient ABC — agent_harness must NOT import openai/anthropic), and
    upserts a rolling per-session summary into memory_session_summary via
    DBSessionSummaryStore. It is the formation half of cross-session conversation
    recall (AD-Memory-Formation-Session-Recall, 缺口 2).

    Wiring (Sprint 57.151): driven from the chat main flow after every real_llm
    send, riding the SAME post-send BackgroundTask seam as the 57.149 auto-extract
    (router._maybe_auto_extract). The summary is "rolling" — re-derived from the
    full ledger each send and upserted onto the one row keyed by the session_id
    UNIQUE — so it stays current as the conversation grows, and a chat session
    needs no clean "end" event.

    Mirrors MemoryExtractor (51.2 / 57.149): same provider-neutral ChatClient ABC,
    same tolerant JSON parse, same best-effort contract (the caller swallows). The
    difference: it asks for a STRUCTURED summary object {summary, key_decisions,
    unresolved_issues} (the designed memory_session_summary columns) rather than a
    list of user facts, and writes via DBSessionSummaryStore rather than UserLayer.

Key Components:
    - SessionSummarizer: summarize_and_store()

Created: 2026-06-30 (Sprint 57.151)
Last Modified: 2026-06-30

Modification History:
    - 2026-06-30: Sprint 57.152 — extract store_summary() dispatch half (combined-formation reuse)
    - 2026-06-30: Initial creation (Sprint 57.151) — rolling session summarizer

Related:
    - agent_harness/memory/extraction.py:MemoryExtractor — the mirrored shape (51.2/57.149)
    - agent_harness/memory/session_summary_store.py:DBSessionSummaryStore — the writer
    - api/v1/chat/router.py:_maybe_auto_extract — the post-send BackgroundTask seam
    - 09-db-schema-design.md L481-498 — the designed memory_session_summary columns
    - sprint-57-151-plan.md §3.3
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import ChatRequest, Message, TraceContext
from agent_harness.memory.session_summary_store import DBSessionSummaryStore

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = """You are a session memory assistant. Read the conversation \
messages and write a compact summary that a future session could use to recall \
what was worked on. Return a STRICT JSON object (no prose outside it) with these \
fields:
  - "summary": 1-3 sentences capturing the topic and where the conversation left off
  - "key_decisions": array of short strings (decisions made; [] if none)
  - "unresolved_issues": array of short strings (open questions / next steps; [] if none)

Return only the JSON object.

Conversation:
{conversation}
"""


# === SessionSummarizer: rolling per-session conversation summary ===
# Why: the 5-layer memory recalls discrete user facts (57.148/149/150) but never
# the conversation arc of a prior session. This forms that arc — a rolling summary
# re-derived from the ledger each send — so recent_sessions() can recall it.
# Alternative considered:
#   - Summarize only once when a session "ends" — rejected: a chat session has no
#     clean end event; rolling-per-send keeps it current + reuses the loaded ledger.
#   - Reuse MemoryExtractor's user-fact output — rejected: a conversation summary
#     (topic + decisions + open issues) is a different shape than durable user facts.
# Reference: AD-Memory-Formation-Session-Recall; sprint-57-151-plan.md §3.3.
class SessionSummarizer:
    """Summarize a session's ledger into memory_session_summary (best-effort)."""

    def __init__(self, chat_client: ChatClient, store: DBSessionSummaryStore) -> None:
        self._chat_client = chat_client
        self._store = store

    async def summarize_and_store(
        self,
        *,
        messages: list[Message],
        session_id: UUID,
        trace_context: TraceContext | None = None,
    ) -> None:
        """Render the ledger, summarize via the cheap tier, upsert the one row.

        No-op on an empty ledger or a blank/unparseable summary. Best-effort: the
        caller (the post-send BackgroundTask) swallows + logs.
        """
        if not messages:
            return

        prompt = _SUMMARY_PROMPT.format(conversation=self._render_messages(messages))
        request = ChatRequest(
            messages=[Message(role="user", content=prompt)],
            temperature=0.0,  # summarization is deterministic-ish
        )
        response = await self._chat_client.chat(request, trace_context=trace_context)

        parsed = self._parse_summary(self._content_text(response.content))
        if parsed is None:
            return
        await self.store_summary(parsed, session_id=session_id)

    async def store_summary(
        self,
        parsed: dict[str, Any],
        *,
        session_id: UUID,
    ) -> None:
        """Upsert an already-parsed {summary, key_decisions, unresolved_issues}.

        The dispatch half of summarization — split out (Sprint 57.152) so the
        combined MemoryFormationWorker can reuse the SAME store code (the
        blank-summary guard + the rolling upsert keyed on session_id) after a
        single combined LLM call. summarize_and_store remains the standalone
        single-call API (it now ends with this method). No-op on a blank summary.
        """
        summary = parsed["summary"]
        if not summary.strip():
            return
        await self._store.upsert_summary(
            session_id=session_id,
            summary=summary.strip(),
            key_decisions=parsed["key_decisions"],
            unresolved_issues=parsed["unresolved_issues"],
        )

    @staticmethod
    def _render_messages(messages: list[Message]) -> str:
        lines: list[str] = []
        for msg in messages:
            text = SessionSummarizer._content_text(msg.content)
            lines.append(f"[{msg.role}] {text}")
        return "\n".join(lines)

    @staticmethod
    def _content_text(content: object) -> str:
        """Plain text from a Message.content that may be str or list[ContentBlock]."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    parts.append(text)
            return "\n".join(parts)
        return str(content)

    @staticmethod
    def _parse_summary(raw: str) -> dict[str, Any] | None:
        """Parse the LLM response into {summary, key_decisions, unresolved_issues}.

        Tolerant: extracts the first JSON object substring if extra prose surrounds
        it. Returns None if no usable object / no string summary. Non-list / non-str
        decision items are coerced or dropped so the JSONB columns stay clean.
        """
        text = raw.strip()
        if not text:
            return None
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                logger.warning("SessionSummarizer: no JSON object found in response")
                return None
            try:
                obj = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                logger.warning("SessionSummarizer: response is not valid JSON")
                return None

        if not isinstance(obj, dict):
            return None
        summary = obj.get("summary")
        if not isinstance(summary, str):
            return None
        return {
            "summary": summary,
            "key_decisions": SessionSummarizer._string_list(obj.get("key_decisions")),
            "unresolved_issues": SessionSummarizer._string_list(obj.get("unresolved_issues")),
        }

    @staticmethod
    def _string_list(value: object) -> list[str]:
        """Coerce a JSON value to a list[str] (drop non-string / blank items)."""
        if not isinstance(value, list):
            return []
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        return out


__all__ = ["SessionSummarizer"]
