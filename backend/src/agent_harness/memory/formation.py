"""
File: backend/src/agent_harness/memory/formation.py
Purpose: Combine post-send memory formation into ONE cheap-tier LLM call.
Category: 範疇 3 (Memory) / post-send formation coordinator
Scope: Phase 57 / Sprint 57.152

Description:
    MemoryFormationWorker COMPOSES the two existing post-send formation workers
    (MemoryExtractor, 57.149 — durable user facts → UserLayer; SessionSummarizer,
    57.151 — rolling conversation summary → memory_session_summary) and, by
    default, makes ONE combined cheap-tier LLM call that returns BOTH the facts
    array AND the summary object, halving the per-send background token + latency
    (the two callers previously read the SAME ledger twice). Closes
    AD-Memory-Formation-Combine-Extract-Summarize.

    It does NOT replace or delete the two workers — it reuses their extracted
    dispatch halves (MemoryExtractor.write_facts / SessionSummarizer.store_summary)
    so the combined parse feeds the SAME write code, and the combined=False
    fallback path delegates to their full single-call methods. Both workers thus
    stay live on the chat path (no AP-2 / AP-4 orphaning).

    Provider-neutral: the combined call goes through the ChatClient ABC
    (agent_harness must NOT import openai/anthropic). The worker builds its own
    task-specific combined prompt, so it is allowlisted in the AP-8 lint alongside
    extraction.py / session_summarizer.py (a background utility-LLM caller, not the
    main agent loop).

Key Components:
    - MemoryFormationWorker: form() — combined (1 call) or separate (2 calls) path

Created: 2026-06-30 (Sprint 57.152)
Last Modified: 2026-06-30

Modification History:
    - 2026-06-30: Initial creation (Sprint 57.152) — combined extract + summarize worker

Related:
    - extraction.py:MemoryExtractor.write_facts — the facts dispatch half (reused)
    - session_summarizer.py:SessionSummarizer.store_summary — the summary dispatch half
    - api/v1/chat/router.py:_maybe_auto_extract — post-send seam (calls form())
    - api/v1/chat/handler.py:build_chat_memory_extractor — builds the worker
    - 55-memory-combined-formation-design.md — the combined-vs-separate decision
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import ChatRequest, Message, TraceContext
from agent_harness.memory.extraction import MemoryExtractor
from agent_harness.memory.session_summarizer import SessionSummarizer

logger = logging.getLogger(__name__)

# Combined prompt field-spec lines, emitted only for the enabled sections so the
# model is asked for exactly what the wired collaborators can store.
_FACTS_FIELD = (
    '  - "facts": array of durable user preferences/facts to remember across '
    'sessions; each item {"content": <1-sentence fact>, "confidence": <float '
    "0.0-1.0>}; [] if none"
)
_SUMMARY_FIELDS = (
    '  - "summary": 1-3 sentences capturing the topic and where the conversation '
    "left off\n"
    '  - "key_decisions": array of short strings (decisions made; [] if none)\n'
    '  - "unresolved_issues": array of short strings (open questions / next steps; '
    "[] if none)"
)
_PROMPT_HEADER = (
    "You are a memory formation assistant. Read the conversation messages and "
    "return a STRICT JSON object (no prose outside it) with these fields:\n"
)
_PROMPT_TAIL = "\n\nReturn only the JSON object.\n{known_block}\nConversation:\n{conversation}\n"


# === MemoryFormationWorker: one combined post-send formation call ===
# Why (Sprint 57.152): the chat post-send hook made TWO cheap-tier LLM calls over
# the SAME ledger — one to extract user facts (57.149), one to summarize the
# conversation (57.151). Asking for both in ONE structured-JSON call halves the
# background token + latency per send. Composing (not rewriting) the two workers
# keeps their write logic + tests intact and lets a single env flag fall back to
# the proven two-call path if the combined prompt ever degrades quality.
# Alternative considered:
#   - Replace both workers with one monolithic former — rejected: orphans
#     SessionSummarizer (AP-2/AP-4) + duplicates the write/dispatch logic.
#   - Inline the combined call in the chat router — rejected: AP-3 scattering
#     (formation logic belongs in 範疇 3, not the api layer).
# Reference: AD-Memory-Formation-Combine-Extract-Summarize; 55-memory-combined-formation-design.md.
class MemoryFormationWorker:
    """Form post-send memory (facts + summary) in one combined call (best-effort)."""

    def __init__(
        self,
        chat_client: ChatClient,
        *,
        extractor: MemoryExtractor | None = None,
        summarizer: SessionSummarizer | None = None,
        combined: bool = True,
    ) -> None:
        self._chat_client = chat_client
        self._extractor = extractor
        self._summarizer = summarizer
        self._combined = combined

    @property
    def wants_user_facts(self) -> bool:
        """True when a user-fact extractor is wired (the router gates the
        profile() known-facts read on this)."""
        return self._extractor is not None

    async def form(
        self,
        *,
        messages: list[Message],
        session_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None = None,
        known_facts: list[str] | None = None,
        trace_context: TraceContext | None = None,
    ) -> None:
        """Form memory from the session ledger. No-op on an empty ledger or when
        no collaborator is wired. Combined (default) = ONE LLM call covering both
        sections; separate = the proven two-call path (env fallback)."""
        if not messages:
            return
        if self._extractor is None and self._summarizer is None:
            return
        if self._combined:
            await self._form_combined(
                messages=messages,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id=user_id,
                known_facts=known_facts,
                trace_context=trace_context,
            )
        else:
            await self._form_separate(
                messages=messages,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id=user_id,
                known_facts=known_facts,
                trace_context=trace_context,
            )

    async def _form_combined(
        self,
        *,
        messages: list[Message],
        session_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None,
        known_facts: list[str] | None,
        trace_context: TraceContext | None,
    ) -> None:
        want_facts = self._extractor is not None and user_id is not None
        want_summary = self._summarizer is not None
        if not want_facts and not want_summary:
            return

        prompt = self._build_prompt(
            messages=messages,
            want_facts=want_facts,
            want_summary=want_summary,
            known_facts=known_facts,
        )
        request = ChatRequest(
            messages=[Message(role="user", content=prompt)],
            temperature=0.0,  # formation is deterministic-ish
        )
        response = await self._chat_client.chat(request, trace_context=trace_context)

        facts, summary = self._parse_combined(
            self._content_text(response.content),
            want_facts=want_facts,
            want_summary=want_summary,
        )
        if want_facts and facts and self._extractor is not None and user_id is not None:
            await self._extractor.write_facts(
                facts,
                tenant_id=tenant_id,
                user_id=user_id,
                trace_context=trace_context,
            )
        if want_summary and summary is not None and self._summarizer is not None:
            await self._summarizer.store_summary(summary, session_id=session_id)

    async def _form_separate(
        self,
        *,
        messages: list[Message],
        session_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None,
        known_facts: list[str] | None,
        trace_context: TraceContext | None,
    ) -> None:
        """The proven two-call path (env fallback) — delegate to each worker's
        full single-call method. Keeps both methods live on the chat path."""
        if self._extractor is not None and user_id is not None:
            await self._extractor.extract_session_to_user(
                session_id=session_id,
                tenant_id=tenant_id,
                user_id=user_id,
                messages=messages,
                known_facts=known_facts,
                trace_context=trace_context,
            )
        if self._summarizer is not None:
            await self._summarizer.summarize_and_store(
                messages=messages,
                session_id=session_id,
                trace_context=trace_context,
            )

    def _build_prompt(
        self,
        *,
        messages: list[Message],
        want_facts: bool,
        want_summary: bool,
        known_facts: list[str] | None,
    ) -> str:
        fields: list[str] = []
        if want_facts:
            fields.append(_FACTS_FIELD)
        if want_summary:
            fields.append(_SUMMARY_FIELDS)
        known_block = self._build_known_block(known_facts) if want_facts else ""
        return (
            _PROMPT_HEADER
            + "\n".join(fields)
            + _PROMPT_TAIL.format(
                known_block=known_block,
                conversation=self._render_messages(messages),
            )
        )

    @staticmethod
    def _build_known_block(known_facts: list[str] | None) -> str:
        """The dedup block listing already-remembered facts (mirrors the
        MemoryExtractor 57.149 known-facts block). Empty / None → "" so the
        prompt has no dedup section."""
        if not known_facts:
            return ""
        listed = "\n".join(f"  - {fact}" for fact in known_facts if fact and fact.strip())
        if not listed:
            return ""
        return (
            "\nALREADY REMEMBERED (do NOT repeat these in facts; emit only NEW "
            "durable facts not already covered here):\n" + listed + "\n"
        )

    def _parse_combined(
        self,
        raw: str,
        *,
        want_facts: bool,
        want_summary: bool,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Parse the combined JSON object into (facts items, summary dict).

        Tolerant: extracts the first JSON object substring if extra prose
        surrounds it. Returns ([], None) on an unusable object. Each half is
        only populated for an enabled section, mirroring the per-worker parse
        shapes (facts = dict items only; summary needs a non-blank string)."""
        text = raw.strip()
        if not text:
            return ([], None)
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                logger.warning("MemoryFormationWorker: no JSON object found in response")
                return ([], None)
            try:
                obj = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                logger.warning("MemoryFormationWorker: response is not valid JSON")
                return ([], None)

        if not isinstance(obj, dict):
            return ([], None)

        facts: list[dict[str, Any]] = []
        if want_facts:
            raw_facts = obj.get("facts")
            if isinstance(raw_facts, list):
                facts = [item for item in raw_facts if isinstance(item, dict)]

        summary: dict[str, Any] | None = None
        if want_summary:
            raw_summary = obj.get("summary")
            if isinstance(raw_summary, str) and raw_summary.strip():
                summary = {
                    "summary": raw_summary,
                    "key_decisions": self._coerce_str_list(obj.get("key_decisions")),
                    "unresolved_issues": self._coerce_str_list(obj.get("unresolved_issues")),
                }
        return (facts, summary)

    @staticmethod
    def _coerce_str_list(value: object) -> list[str]:
        """Coerce a JSON value to a list[str] (drop non-string / blank items)."""
        if not isinstance(value, list):
            return []
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        return out

    @staticmethod
    def _render_messages(messages: list[Message]) -> str:
        lines: list[str] = []
        for msg in messages:
            text = MemoryFormationWorker._content_text(msg.content)
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


__all__ = ["MemoryFormationWorker"]
