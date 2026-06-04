"""
File: backend/src/agent_harness/prompt_builder/builder.py
Purpose: DefaultPromptBuilder — concrete impl of PromptBuilder ABC (Cat 5).
Category: 範疇 5 (Prompt Construction)
Scope: Phase 52 / Sprint 52.2 (Day 1.6 — skeleton; Day 2 wires memory/cache)

Description:
    DefaultPromptBuilder is the single entry point for LLM prompt assembly.
    It assembles 6 sections (system / tools / memory_layers / conversation /
    user_message), runs them through a PositionStrategy, builds cache
    breakpoints, estimates tokens, and returns a PromptArtifact.

    Day 1 scope (this commit):
      - Constructor accepts 7 DI (memory_retrieval / cache_manager /
        token_counter / tracer / default_strategy / default_cache_policy /
        templates_overrides)
      - build() entry emits tracer span + child TraceContext (W3-2 carryover)
      - 4 sections wired (system / tools passthrough / conversation / user)
      - Memory injection STUB (returns {}; Day 2.1 wires real call)
      - Cache breakpoint STUB (returns []; Day 2.3 wires real call)
      - Position strategy applied + token estimation real

    Day 2+ wires _inject_memory_layers + _build_cache_breakpoints to real
    51.2 MemoryRetrieval + 52.1 PromptCacheManager.

    Anti-pattern AP-8 (No Centralized PromptBuilder) — V1 violated by
    scattering prompt assembly. V2 forbids ad-hoc messages = [{...}]
    construction; CI lint rule enforces in 52.2 Day 4.

    W3-2 audit carryover (multi-tenant + observability cross-cutting):
      - tenant_id REQUIRED (per multi-tenant-data.md tri-rule)
      - tracer span emitted at build() entry
      - trace_context propagated to memory_retrieval / cache_manager
      - NO process-wide cache fallback (per plan §2.5)

Owner: 01-eleven-categories-spec.md §範疇 5

Created: 2026-05-01 (Sprint 52.2 Day 1.6)
Last Modified: 2026-06-04

Modification History (newest-first):
    - 2026-06-04: Sprint 57.80 — tool-call adjacency invariant after arrange() (orphan-tool 400)
    - 2026-06-03: Sprint 57.75 A-5c — add layer_metadata["memory_accesses"] per-hint detail
    - 2026-06-01: Sprint 57.65 — memory render enrich + token cap + verify_before_use (A-1)

Related:
    - sprint-52-2-plan.md §2.4 / §2.5 / §2.6
    - claudedocs/5-status/V2-AUDIT-WEEK3-SUMMARY.md §3 (W3-2 critical findings)
    - .claude/rules/observability-instrumentation.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, replace
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from agent_harness._contracts import (
    CacheBreakpoint,
    CachePolicy,
    LoopState,
    MemoryHint,
    Message,
    PromptArtifact,
    ToolSpec,
    TraceContext,
)
from agent_harness.context_mgmt import PromptCacheManager, TokenCounter
from agent_harness.memory import MemoryRetrieval
from agent_harness.prompt_builder._abc import PromptBuilder
from agent_harness.prompt_builder.strategies import (
    LostInMiddleStrategy,
    PositionStrategy,
    PromptSections,
)
from agent_harness.prompt_builder.templates import (
    SYSTEM_ROLE_TEMPLATE,
    VERIFY_BEFORE_USE_HEADER,
    _format_hint_line,
    _memory_as_messages,
)

_logger = logging.getLogger(__name__)

# Time scale priority for memory layer ordering (per plan §2.5).
# Lower number = higher priority (rendered first in prompt).
# 51.2 MemoryHint.time_scale ∈ {"short_term", "long_term", "semantic"}.
_TIME_SCALE_PRIORITY: dict[str, int] = {
    "long_term": 0,  # durable knowledge → most important
    "semantic": 1,  # vector matches → middle
    "short_term": 2,  # working memory → least important
}

# Fixed scope render order for the memory block (Sprint 57.65 A-1 Tier2).
# Broadest scope first (system) → narrowest (session) so the prompt reads
# deterministically across builds regardless of MemoryRetrieval merge order.
_LAYER_RENDER_ORDER: tuple[str, ...] = ("system", "tenant", "role", "user", "session")

# ---------------------------------------------------------------------------
# Tracer protocol (Cat 12 Day 1 minimal stub; replaced by real OTel in 53.x)
# ---------------------------------------------------------------------------


@runtime_checkable
class _Span(Protocol):
    """Duck-typed span; real impl in Cat 12 module (Phase 53.x)."""

    span_id: str

    def end(self) -> None: ...


@runtime_checkable
class Tracer(Protocol):
    """Duck-typed tracer; real impl in Cat 12 module (Phase 53.x).

    Day 1.6 default = NoOpTracer (below). DefaultPromptBuilder.__init__
    accepts any object satisfying this Protocol — tests can inject
    MockTracer for span assertions, real OTel SDK arrives in 53.x.
    """

    def start_span(
        self,
        *,
        name: str,
        parent_span_id: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> _Span: ...


@dataclass
class _NoOpSpan:
    """No-op span used when builder constructed without tracer."""

    span_id: str = field(default_factory=lambda: uuid4().hex[:16])
    _start: float = field(default_factory=time.perf_counter)

    @property
    def duration_seconds(self) -> float:
        return time.perf_counter() - self._start

    def end(self) -> None:
        return None


class _NoOpTracer:
    """No-op tracer: produces _NoOpSpan; no metric emission."""

    def start_span(
        self,
        *,
        name: str,
        parent_span_id: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> _Span:
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# DefaultPromptBuilder
# ---------------------------------------------------------------------------


class DefaultPromptBuilder(PromptBuilder):
    """6-section layered prompt assembly with strategy + cache + memory injection.

    Constructor DI (per plan §2.4 + W3-2 carryover Day 1.6 update):
      - memory_retrieval: 51.2 MemoryRetrieval (cross-layer search coordinator)
      - cache_manager: 52.1 PromptCacheManager (tenant-scoped breakpoint hints)
      - token_counter: 52.1 TokenCounter (per-provider exact / approx)
      - tracer: Cat 12 Tracer protocol (default = _NoOpTracer)
      - default_strategy: PositionStrategy (default = LostInMiddleStrategy)
      - default_cache_policy: CachePolicy (default = CachePolicy() with all flags)
      - system_role_text: override of SYSTEM_ROLE_TEMPLATE for tenant-specific role
      - max_memory_tokens: budget cap for the rendered memory block (Sprint 57.65;
        default 2000). When the retrieved hints exceed this, the builder drops the
        lowest-confidence (then oldest) hints until the block fits.
    """

    def __init__(
        self,
        *,
        memory_retrieval: MemoryRetrieval,
        cache_manager: PromptCacheManager,
        token_counter: TokenCounter,
        tracer: Tracer | None = None,
        default_strategy: PositionStrategy | None = None,
        default_cache_policy: CachePolicy | None = None,
        system_role_text: str | None = None,
        max_memory_tokens: int = 2000,
    ) -> None:
        self._memory_retrieval = memory_retrieval
        self._cache_manager = cache_manager
        self._token_counter = token_counter
        self._tracer: Tracer = tracer if tracer is not None else _NoOpTracer()
        self._default_strategy: PositionStrategy = (
            default_strategy if default_strategy is not None else LostInMiddleStrategy()
        )
        self._default_cache_policy: CachePolicy = (
            default_cache_policy if default_cache_policy is not None else CachePolicy()
        )
        self._system_role_text = system_role_text or SYSTEM_ROLE_TEMPLATE
        self._max_memory_tokens = max_memory_tokens

    async def build(
        self,
        *,
        state: LoopState,
        tenant_id: UUID,
        user_id: UUID | None = None,
        tools: list[ToolSpec] | None = None,
        cache_policy: CachePolicy | None = None,
        position_strategy: PositionStrategy | None = None,
        trace_context: TraceContext | None = None,
    ) -> PromptArtifact:
        """Assemble PromptArtifact with span + propagation (W3-2 carryover)."""
        # --- Step 0: tracer span + child TraceContext (W3-2) ---
        span = self._tracer.start_span(
            name="prompt_builder.build",
            parent_span_id=trace_context.span_id if trace_context else None,
            attributes={
                "tenant_id": str(tenant_id),
                "agent": self.__class__.__name__,
            },
        )
        child_ctx = TraceContext(
            trace_id=trace_context.trace_id if trace_context else uuid4().hex,
            span_id=span.span_id,
            parent_span_id=trace_context.span_id if trace_context else None,
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=trace_context.session_id if trace_context else None,
        )

        try:
            # --- Step 1: build sections ---
            tools_list: list[ToolSpec] = tools if tools is not None else []
            user_msg = self._extract_last_user_message(state)
            query_text = self._message_to_query(user_msg) if user_msg else ""

            memory_layers = await self._inject_memory_layers(
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=state.durable.session_id,
                query=query_text,
                trace_context=child_ctx,
            )
            # Sprint 57.65 (A-1 Tier2): cap the rendered memory block to
            # max_memory_tokens (drop lowest-confidence / oldest first). The cap
            # applies to the memory block only — system / tools / conversation
            # are not counted against it.
            memory_layers = self._apply_memory_budget(memory_layers, tools=tools_list)

            sections = PromptSections(
                system=self._build_system_section(memory_layers),
                tools=tools_list,
                memory_layers=memory_layers,
                conversation=self._extract_conversation(state, user_msg),
                user_message=user_msg,
            )

            # --- Step 2: position strategy ---
            strategy = (
                position_strategy if position_strategy is not None else self._default_strategy
            )
            messages = strategy.arrange(sections)
            # Sprint 57.80: enforce the provider hard-constraint that every
            # role='tool' message immediately follows its owning assistant
            # tool_calls. A PositionStrategy (e.g. LostInMiddleStrategy) may
            # reorder the conversation and split a tool result from its
            # assistant; this single post-arrange pass re-anchors them so NO
            # strategy can emit an orphan-tool sequence. Closes the real_llm
            # chat 400 (AD-Chat-RealLLM-Orphan-Tool-Message).
            messages = self._enforce_tool_adjacency(messages)

            # --- Step 3: cache breakpoints ---
            cache_breakpoints = await self._build_cache_breakpoints(
                tenant_id=tenant_id,
                policy=cache_policy if cache_policy is not None else self._default_cache_policy,
                sections=sections,
                trace_context=child_ctx,
            )

            # --- Step 4: token estimation (graceful degrade per W3-2 theme) ---
            try:
                estimated_tokens = self._token_counter.count(messages=messages, tools=tools_list)
            except Exception as exc:  # pragma: no cover - defensive degrade path
                _logger.warning(
                    "TokenCounter.count failed (tenant=%s); estimated_tokens=0: %s",
                    tenant_id,
                    exc,
                )
                estimated_tokens = 0

            # Sprint 57.75 (A-5c Memory tab): surface per-hint access detail so
            # the Loop can emit one MemoryAccessed event per retrieved hint (the
            # chat-v2 Inspector Memory tab). `memory_layers_used` (above) is only
            # the layer-key list; this carries the 4 fields the Memory ops row
            # renders: scope (layer) / time_scale (雙軸 2nd axis) / key / summary.
            # `summary` is the MemoryHint's capped token-cheap summary (NOT raw
            # content — PII-safe by construction per _contracts/memory.py); `key`
            # is the hint's full_content_pointer (DB ref / vector_id). Reads the
            # SAME `memory_layers` dict already retrieved + budget-trimmed above,
            # so no extra MemoryRetrieval.search() call.
            memory_accesses: list[dict[str, str]] = [
                {
                    "scope": layer,
                    "time_scale": hint.time_scale,
                    "key": hint.full_content_pointer,
                    "summary": hint.summary,
                }
                for layer, hints in memory_layers.items()
                for hint in hints
            ]
            return PromptArtifact(
                messages=messages,
                cache_breakpoints=cache_breakpoints,
                estimated_input_tokens=estimated_tokens,
                layer_metadata={
                    "memory_layers_used": list(memory_layers.keys()),
                    "memory_accesses": memory_accesses,
                    "position_strategy": strategy.__class__.__name__,
                    "cache_sections": [bp.section_id for bp in cache_breakpoints if bp.section_id],
                    "trace_id": child_ctx.trace_id,
                },
            )
        finally:
            span.end()

    # ------------------------------------------------------------------
    # Tool-call adjacency invariant (Sprint 57.80)
    # ------------------------------------------------------------------
    # Why: OpenAI / Azure / Anthropic all require a role='tool' message to
    # immediately follow the assistant message bearing the matching tool_calls.
    # A PositionStrategy is free to reorder the conversation — LostInMiddleStrategy
    # in particular moves recent assistant messages to the tail while their tool
    # results stay in mid-history, orphaning the tool (real_llm chat 400
    # "messages[N] role 'tool' must follow tool_calls"). Rather than make every
    # strategy tool-aware, the builder enforces the invariant ONCE after arrange()
    # (AP-8 single enforcement point) so current + future strategies are all safe.
    # Alternative considered:
    #   - Fix LostInMiddleStrategy in isolation — rejected: leaves the hard
    #     constraint unguaranteed; a new strategy could reintroduce the orphan.
    #   - Stop re-anchoring the user message for tool turns — rejected: user-after-
    #     tool is valid (not a 400); the re-anchor is the deliberate lost-in-middle
    #     design. Out of scope for an orphan-tool fix.
    # Reference: 04-anti-patterns.md §AP-8 / §AP-10 (mock vs real divergence — the
    #   MockChatClient never validated adjacency, so this was invisible until real
    #   Azure; Sprint 57.79 Day-3).
    @staticmethod
    def _enforce_tool_adjacency(messages: list[Message]) -> list[Message]:
        """Re-anchor every role='tool' message right after its owning assistant.

        Builds a tool_call_id → emitting-assistant map, then rebuilds the list so
        each tool message directly follows the assistant whose tool_calls carries
        the matching id, preserving all other relative order. A tool message whose
        tool_call_id resolves to no assistant in the list (defensive — does not
        occur on the loop path, where the assistant is always emitted before its
        tool) is left in place rather than dropped (never silently lose a message).
        No-op (returns the same list) when no assistant carries tool_calls or no
        tool message resolves to an owner — zero overhead for plain chat turns.

        Strategies rearrange the same Message object references (no copy), so the
        owner lookup by object identity is stable.
        """
        owner_by_id: dict[str, Message] = {}
        for m in messages:
            if m.role == "assistant" and m.tool_calls:
                for tc in m.tool_calls:
                    owner_by_id[tc.id] = m
        if not owner_by_id:
            return messages

        held_tools: dict[int, list[Message]] = {}
        held_ids: set[int] = set()
        for m in messages:
            if m.role == "tool" and m.tool_call_id is not None:
                owner = owner_by_id.get(m.tool_call_id)
                if owner is not None:
                    held_tools.setdefault(id(owner), []).append(m)
                    held_ids.add(id(m))
        if not held_ids:
            return messages

        result: list[Message] = []
        for m in messages:
            if id(m) in held_ids:
                continue  # re-emitted right after its owning assistant below
            result.append(m)
            if m.role == "assistant" and id(m) in held_tools:
                result.extend(held_tools[id(m)])
        return result

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_system_section(
        self, memory_layers: dict[str, list[MemoryHint]] | None = None
    ) -> Message:
        """Default system role; override via system_role_text constructor arg.

        Sprint 57.65 (A-1 Tier2): when any post-cap hint carries
        verify_before_use=True, a static lead-then-verify instruction block plus
        the flagged hint summaries are appended to the system role so the model
        is told to confirm stale hints against live state before acting. Absent
        when no flagged hint exists (the system role is byte-identical to the
        pre-57.65 default — keeps the no-memory path unchanged).
        """
        text = self._system_role_text
        verify_block = self._build_verify_before_use_block(memory_layers or {})
        if verify_block:
            text = f"{text}\n\n{verify_block}"
        return Message(role="system", content=text)

    @staticmethod
    def _build_verify_before_use_block(memory_layers: dict[str, list[MemoryHint]]) -> str:
        """Lead-then-verify instruction + flagged summaries, or "" when none flagged."""
        flagged = [h for hints in memory_layers.values() for h in hints if h.verify_before_use]
        if not flagged:
            return ""
        lines = [VERIFY_BEFORE_USE_HEADER]
        lines.extend(_format_hint_line(h) for h in flagged)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Memory budget cap (Sprint 57.65 A-1 Tier2)
    # ------------------------------------------------------------------

    def _apply_memory_budget(
        self,
        memory_layers: dict[str, list[MemoryHint]],
        *,
        tools: list[ToolSpec],
    ) -> dict[str, list[MemoryHint]]:
        """Cap the rendered memory block to self._max_memory_tokens.

        The rendered memory block = the system messages _memory_as_messages()
        produces for these layers. We measure it with the injected token_counter
        (the neutral count() path — no provider SDK) and, while over budget, drop
        the single least-valuable hint: lowest confidence first, ties broken by
        oldest timestamp. Empty / already-fitting input is returned unchanged.

        The cap is memory-block-only: tools are passed to count() purely so the
        per-tool overhead does not skew the per-message arithmetic — they are not
        themselves capped here.
        """
        if not memory_layers:
            return memory_layers
        if self._measure_memory_tokens(memory_layers, tools=tools) <= self._max_memory_tokens:
            return memory_layers

        # Work on a mutable copy; drop one hint at a time until under budget.
        trimmed: dict[str, list[MemoryHint]] = {
            layer: list(hints) for layer, hints in memory_layers.items()
        }
        while self._measure_memory_tokens(trimmed, tools=tools) > self._max_memory_tokens:
            victim = self._least_valuable_hint(trimmed)
            if victim is None:
                break  # nothing left to drop (defensive; loop guard)
            layer_name, hint = victim
            trimmed[layer_name].remove(hint)
            if not trimmed[layer_name]:
                del trimmed[layer_name]
        return trimmed

    def _measure_memory_tokens(
        self, memory_layers: dict[str, list[MemoryHint]], *, tools: list[ToolSpec]
    ) -> int:
        """Token cost of the rendered memory messages (0 when no layers).

        Counts ONLY the memory system messages, not tools — `tools` is forwarded
        to count() only so its overhead model is consistent; we subtract a
        tools-only baseline so the returned number is the memory block's marginal
        cost.
        """
        memory_msgs = _memory_as_messages(memory_layers)
        if not memory_msgs:
            return 0
        try:
            with_memory = self._token_counter.count(messages=memory_msgs, tools=None)
        except Exception as exc:  # pragma: no cover - defensive degrade path
            _logger.warning("TokenCounter.count failed during memory budget cap: %s", exc)
            return 0
        return with_memory

    @staticmethod
    def _least_valuable_hint(
        memory_layers: dict[str, list[MemoryHint]],
    ) -> tuple[str, MemoryHint] | None:
        """Pick (layer, hint) to drop first: lowest confidence, then oldest."""
        candidates: list[tuple[str, MemoryHint]] = [
            (layer, h) for layer, hints in memory_layers.items() for h in hints
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda pair: (pair[1].confidence, pair[1].timestamp))

    def _extract_last_user_message(self, state: LoopState) -> Message | None:
        """Return the last role='user' message from transient.messages, or None."""
        for msg in reversed(state.transient.messages):
            if msg.role == "user":
                return msg
        return None

    def _extract_conversation(
        self, state: LoopState, current_user_msg: Message | None
    ) -> list[Message]:
        """Conversation = transient messages minus the current user message (last user)."""
        if current_user_msg is None:
            return list(state.transient.messages)
        # Exclude the current user message by identity to avoid duplication
        return [m for m in state.transient.messages if m is not current_user_msg]

    def _message_to_query(self, msg: Message) -> str:
        """Extract plain text from Message.content for memory query."""
        if isinstance(msg.content, str):
            return msg.content
        parts: list[str] = []
        for block in msg.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Memory injection (Day 1.6 STUB; Day 2.1 wires real)
    # ------------------------------------------------------------------

    async def _inject_memory_layers(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        session_id: UUID | None,
        query: str,
        trace_context: TraceContext | None = None,
    ) -> dict[str, list[MemoryHint]]:
        """Real call to 51.2 MemoryRetrieval.search() with trace propagation.

        Returns hints grouped by layer (system / tenant / role / user / session)
        and sorted within each layer by time_scale priority (long_term first,
        then semantic, then short_term per _TIME_SCALE_PRIORITY).

        Multi-tenant safety (W3-2 + W1-2 carryover):
        - tenant_id is REQUIRED at builder entry (build() signature)
        - 51.2 MemoryRetrieval enforces tenant_id filter at storage level
        - Empty query returns {} (no memory injection)

        Graceful degradation (per plan §2.5):
        - Any failure during retrieval → log warning + return {} (does not crash
          build()). The prompt falls back to system + tools + conversation only.

        Trace propagation (W3-2 carryover):
        - trace_context is forwarded as-is to MemoryRetrieval.search() so OTel
          spans link memory queries back to the build() span.
        """
        if not query.strip():
            return {}

        try:
            hints = await self._memory_retrieval.search(
                query=query,
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                scopes=("system", "tenant", "role", "user", "session"),
                time_scales=("short_term", "long_term", "semantic"),
                top_k=10,
                trace_context=trace_context,
            )
        except Exception as exc:  # pragma: no cover - defensive degrade path
            _logger.warning(
                "MemoryRetrieval.search failed (tenant=%s); degrading to no memory injection: %s",
                tenant_id,
                exc,
            )
            return {}

        grouped: dict[str, list[MemoryHint]] = {}
        for h in hints:
            grouped.setdefault(h.layer, []).append(h)

        for layer_name in grouped:
            grouped[layer_name].sort(key=lambda h: _TIME_SCALE_PRIORITY.get(h.time_scale, 99))

        # Emit in fixed scope order (system→tenant→role→user→session) so the
        # rendered block is deterministic across builds (Sprint 57.65 A-1 Tier2);
        # any unexpected layer name falls to the end in insertion order.
        by_layer: dict[str, list[MemoryHint]] = {
            layer: grouped[layer] for layer in _LAYER_RENDER_ORDER if layer in grouped
        }
        for layer_name, layer_hints in grouped.items():
            if layer_name not in by_layer:
                by_layer[layer_name] = layer_hints
        return by_layer

    # ------------------------------------------------------------------
    # Cache breakpoint builder (Day 1.6 STUB; Day 2.3 wires real)
    # ------------------------------------------------------------------

    async def _build_cache_breakpoints(
        self,
        *,
        tenant_id: UUID,
        policy: CachePolicy,
        sections: PromptSections,
        trace_context: TraceContext | None = None,
    ) -> list[CacheBreakpoint]:
        """Real call to 52.1 PromptCacheManager.get_cache_breakpoints with trace propagation.

        52.1 PromptCacheManager enforces tenant isolation at the cache key level
        (4 red-team verified); 52.2 PromptBuilder relies on that contract and adds
        content_hash from current sections so 52.1 cache_manager can detect
        invalidation when section content changes between builds.

        Graceful degradation:
        - cache_policy.enabled = False → return [] (no cache markers)
        - Any failure during cache_manager call → log warning + return [] (cache miss
          is non-fatal; LLM call still proceeds without caching)

        Trace propagation (W3-2 carryover): trace_context forwarded as-is to
        52.1 cache_manager (52.1 ABC extended Day 2.3 to accept trace_context kwarg).
        """
        if not policy.enabled:
            return []

        try:
            breakpoints = await self._cache_manager.get_cache_breakpoints(
                tenant_id=tenant_id,
                policy=policy,
                trace_context=trace_context,
            )
        except Exception as exc:  # pragma: no cover - defensive degrade path
            _logger.warning(
                "PromptCacheManager.get_cache_breakpoints failed (tenant=%s); cache disabled: %s",
                tenant_id,
                exc,
            )
            return []

        enhanced: list[CacheBreakpoint] = []
        for bp in breakpoints:
            content_hash = self._compute_section_hash(bp.section_id, sections)
            enhanced.append(replace(bp, content_hash=content_hash))
        return enhanced

    def _compute_section_hash(self, section_id: str | None, sections: PromptSections) -> str | None:
        """SHA256 hash for the named section's current content.

        Used to populate CacheBreakpoint.content_hash (52.1 logical metadata).
        52.1 cache_manager can compare hashes across builds to detect when a
        cached section's content changed and the entry should be invalidated.

        Section ID mapping (matches 52.1 _sections_from_policy):
        - "system_prompt" → hash of sections.system.content
        - "tool_definitions" → hash of stable JSON of tool name+schema list
        - "memory_layers" → hash of layer_name:hint_count fingerprint
        - other / None → None (forward-compat for new section types)
        """
        if section_id is None:
            return None
        if section_id == "system_prompt":
            text = str(sections.system.content)
        elif section_id == "tool_definitions":
            text = json.dumps(
                [{"name": t.name, "schema": t.input_schema} for t in sections.tools],
                sort_keys=True,
            )
        elif section_id == "memory_layers":
            text = ",".join(
                f"{layer}:{len(hints)}" for layer, hints in sorted(sections.memory_layers.items())
            )
        else:
            return None
        return hashlib.sha256(text.encode()).hexdigest()
