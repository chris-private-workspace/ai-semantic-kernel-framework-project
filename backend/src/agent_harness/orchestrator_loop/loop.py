"""
File: backend/src/agent_harness/orchestrator_loop/loop.py
Purpose: Cat 1 concrete AgentLoop — TAO/ReAct main loop (while-true driven).
Category: 範疇 1 (Orchestrator Loop)
Scope: Phase 50 / Sprint 50.1 (Day 2.2)

Description:
    Concrete `AgentLoopImpl(AgentLoop)` implementing the Think-Act-Observe
    cycle. This is the V2 cure for AP-1 (Pipeline disguised as Loop): the
    iteration is `while True` driven by `StopReason` / 4 termination
    conditions, NOT a fixed-step `for step in steps:` pipeline.

    Per-turn flow:
        1. Check 3 pre-LLM terminators (max_turns / token_budget / cancellation)
        2. Build ChatRequest from current messages + registered tools
        3. await chat_client.chat(request) — provider-neutral via adapter
        4. Update tokens_used from response.usage
        5. parser.parse(response) → ParsedOutput
        6. yield Thinking(text=parsed.text)
        7. Check stop_reason terminator (END_TURN exit)
        8. classify_output(response) → branch:
             - FINAL    → yield LoopCompleted(end_turn) + return
             - HANDOFF  → yield LoopCompleted(handoff_not_implemented) + return  [Cat 11 stub]
             - TOOL_USE → for each tool_call:
                              yield ToolCallRequested
                              await tool_executor.execute(tc)
                              append Message(role="tool", tool_call_id=tc.id, content=...)
                          turn_count += 1; continue
        9. Cancellation: asyncio.CancelledError caught at chat() / execute()
           boundary → yield LoopCompleted(cancelled) + raise.

    All cross-cat collaborators are CTOR-injected:
        - ChatClient (adapter; provider-neutral)
        - OutputParser (Cat 6; Day 1)
        - ToolExecutor (Cat 2; Day 3 InMemory impl, real impl Phase 51.1)
        - ToolRegistry (Cat 2; Day 3 InMemory impl)
        - Tracer (Cat 12; NoOpTracer fallback)

    System prompt + token budget + max_turns are CTOR-configured (per-Loop)
    rather than per-`run()` because the 49.1 ABC sig only allows
    (session_id, user_input, trace_context). Phase 53.1+ State Mgmt may
    revisit if per-run override is needed.

Created: 2026-04-30 (Sprint 50.1 Day 2.2)
Last Modified: 2026-06-01

Modification History (newest-first):
    - 2026-06-01: Sprint 57.65 A-2 — accumulate cached_input_tokens + emit cache_hit_rate
    - 2026-06-01: Sprint 57.65 — scope PromptBuilder.build user_id to ctx.user_id (A-1 Tier2)
    - 2026-05-05: Sprint 55.6 — close AD-Cat8-2 (retry wrap at L1044+L1092 — Option H)
    - 2026-05-05: Sprint 55.4 — close AD-Cat8-3 narrow Option C (error_class_str param)
    - 2026-05-02: Cat 7 State Mgmt integration (Sprint 53.1 Day 3) — optional
        ctor kwargs `reducer`, `checkpointer`, `tenant_id`. When all three
        provided, AgentLoopImpl builds an internal LoopState snapshot at
        each safe point (post-LLM, post-tool) and emits StateCheckpointed
        events with monotonic DB chain version. tenant_id ctor kwarg also
        supersedes the prior `tenant_id=session_id` placeholder in
        compactor + prompt_builder LoopState building blocks (lines marked
        "Phase 53.1 wires real tenant"). Backward-compat: when reducer /
        checkpointer / tenant_id are None, behavior is identical to 52.x
        baseline (51.x integration tests stay green). Full sole-mutator
        refactor (every messages.append → reducer.merge) is deferred to
        Phase 54.x — see Sprint 53.1 retrospective Audit Debt.
    - 2026-05-01: Inject Cat 5 PromptBuilder (Sprint 52.2 Day 3.1) — optional
        ctor kwarg `prompt_builder: PromptBuilder | None = None`. When set,
        per-turn (post-compaction) call build() to rebuild chat() messages
        and forward artifact.cache_breakpoints to ChatClient.chat (already
        a 51.1 ABC kwarg). Emit PromptBuilt with full payload (messages_count
        / estimated_input_tokens / cache_breakpoints_count / memory_layers_used
        / position_strategy_used / duration_ms). When None, falls back to
        50.x baseline messages → backward-compat preserved (50.x tests intact).
    - 2026-04-30: Yield 5 additional LoopEvents per turn (Sprint 50.2 Day 2.4):
        TurnStarted at top of while → LLMRequested before chat() → LLMResponded
        after parse (canonical SSE llm_response carrier) → ToolCallExecuted
        (success) / ToolCallFailed (error) per tool call. Thinking emit retained
        for 50.1 test backward compat. Event sequence now Cat 1+2+6 cooperate.
    - 2026-04-30: Switch ToolExecutor/ToolRegistry import to public path
        `agent_harness.tools` (Sprint 50.2 Day 1.5) — clears
        check_cross_category_import lint warning per category-boundaries.md
        (re-export already in tools/__init__.py since 50.1).
    - 2026-04-30: Initial creation (Sprint 50.1 Day 2.2) — while-true main
        loop + 4 termination conditions + 3-way dispatch + cancellation safety.

Related:
    - ._abc (AgentLoop ABC; 49.1)
    - .termination (4 terminators + TerminationReason)
    - 01-eleven-categories-spec.md §範疇 1 (TAO loop spec)
    - 04-anti-patterns.md AP-1 (must use while, not for-step)
    - 17-cross-category-interfaces.md §4.1 (LoopEvent emit ownership)
"""

from __future__ import annotations

import asyncio
import time

# Local import to avoid circular: only used at runtime for state placeholders
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID, uuid4

# Need imports from sibling adapter / tools / output_parser modules:
from adapters._base.chat_client import ChatClient
from agent_harness._contracts import (
    ApprovalReceived,
    ApprovalRequested,
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    ContentBlock,
    ContextCompacted,
    DurableState,
    ErrorRetried,
    ExecutionContext,
    GuardrailTriggered,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    LoopState,
    LoopTerminated,
    Message,
    PromptBuilt,
    SpanCategory,
    StateCheckpointed,
    StateVersion,
    Thinking,
    ToolCall,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    ToolResult,
    TraceContext,
    TransientState,
    TripwireTriggered,
    TurnStarted,
)
from agent_harness._contracts.hitl import (
    ApprovalDecision,
    ApprovalRequest,
    DecisionType,
    RiskLevel,
)
from agent_harness.context_mgmt import Compactor
from agent_harness.error_handling import (
    DefaultCircuitBreaker,
    DefaultErrorTerminator,
    ErrorClass,
    ErrorPolicy,
    RetryPolicyMatrix,
    TenantErrorBudget,
)
from agent_harness.error_handling import TerminationReason as Cat8TerminationReason
from agent_harness.error_handling import (
    compute_backoff,
)
from agent_harness.guardrails import (
    CapabilityMatrix,
    GuardrailAction,
    GuardrailEngine,
    Tripwire,
    WORMAuditLog,
)
from agent_harness.hitl import HITLManager
from agent_harness.observability import NoOpTracer, Tracer
from agent_harness.output_parser import OutputParser, OutputType, classify_output
from agent_harness.prompt_builder import PromptBuilder
from agent_harness.state_mgmt import Checkpointer, Reducer
from agent_harness.tools import ToolExecutor, ToolRegistry  # public path per category-boundaries.md

from ._abc import AgentLoop
from ._metrics import LoopMetricsAccumulator
from .termination import (
    TerminationReason,
    should_terminate_by_cancellation,
    should_terminate_by_stop_reason,
    should_terminate_by_tokens,
    should_terminate_by_turns,
)


class AgentLoopImpl(AgentLoop):
    """Concrete TAO/ReAct loop. While-true driven, StopReason-terminated."""

    def __init__(
        self,
        *,
        chat_client: ChatClient,
        output_parser: OutputParser,
        tool_executor: ToolExecutor,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_turns: int = 50,
        token_budget: int = 100_000,
        tracer: Tracer | None = None,
        compactor: Compactor | None = None,
        prompt_builder: PromptBuilder | None = None,
        reducer: Reducer | None = None,
        checkpointer: Checkpointer | None = None,
        tenant_id: UUID | None = None,
        error_policy: ErrorPolicy | None = None,
        retry_policy: RetryPolicyMatrix | None = None,
        circuit_breaker: DefaultCircuitBreaker | None = None,
        error_budget: TenantErrorBudget | None = None,
        error_terminator: DefaultErrorTerminator | None = None,
        # 53.3 Day 4 Cat 9 integration: 4 opt-in deps. When any is None
        # the corresponding Cat 9 path is skipped (preserves 53.2 baseline).
        # See `agent_harness.guardrails` for production wiring.
        guardrail_engine: "GuardrailEngine | None" = None,
        tripwire: "Tripwire | None" = None,
        audit_log: "WORMAuditLog | None" = None,
        capability_matrix: "CapabilityMatrix | None" = None,
        # 53.5 US-3 §HITL Centralization wiring: opt-in. When set, Cat 9
        # ESCALATE branch pauses the loop, calls HITLManager.request_approval,
        # waits for the reviewer's decision, and resumes / blocks based on
        # outcome. When None, ESCALATE remains a soft-block (53.3 baseline).
        hitl_manager: "HITLManager | None" = None,
        hitl_timeout_s: int = 14400,  # 4hr cross-session window
    ) -> None:
        self._chat_client = chat_client
        self._output_parser = output_parser
        self._tool_executor = tool_executor
        self._tool_registry = tool_registry
        self._system_prompt = system_prompt
        self._max_turns = max_turns
        self._token_budget = token_budget
        self._tracer = tracer or NoOpTracer()
        # 52.1 Day 2.7: compactor is OPTIONAL for backward-compat with 50.x callers.
        # When None, compaction step is a no-op; pre-existing tests stay green.
        self._compactor = compactor
        # 52.2 Day 3.1: prompt_builder is OPTIONAL for 50.x backward-compat.
        # When None, per-turn LLM call uses raw `messages` (50.x baseline).
        # When set, Cat 5 build() runs each turn, replacing chat()'s messages
        # with artifact.messages and forwarding artifact.cache_breakpoints to
        # the adapter (Anthropic cache_control / OpenAI prompt_cache_key).
        self._prompt_builder = prompt_builder
        # 53.1 Day 3 Cat 7 integration: Reducer + Checkpointer + tenant_id are
        # OPTIONAL. When all three provided, AgentLoopImpl persists a state
        # snapshot at each safe point (post-LLM, post-tool) via reducer.merge
        # → checkpointer.save → emit StateCheckpointed. When any is None,
        # the integration is no-op (preserves 51.x baseline). tenant_id
        # also fixes the prior `tenant_id=session_id` placeholder in the
        # compactor + prompt_builder LoopState building blocks.
        self._reducer = reducer
        self._checkpointer = checkpointer
        self._tenant_id = tenant_id
        # 53.2 Day 3 Cat 8 integration: 5 opt-in deps. When any is None
        # the corresponding Cat 8 path is skipped (preserves 53.1
        # baseline). Day 4 wires `_handle_tool_error` into the main tool
        # execution path. Until then the helper exists but is unused —
        # explicitly opt-in via constructor.
        self._error_policy = error_policy
        self._retry_policy = retry_policy
        self._circuit_breaker = circuit_breaker
        self._error_budget = error_budget
        self._error_terminator = error_terminator
        # 53.3 Day 4 Cat 9
        self._guardrail_engine = guardrail_engine
        self._tripwire = tripwire
        self._audit_log = audit_log
        self._capability_matrix = capability_matrix
        # 53.5 US-3 §HITL Centralization
        self._hitl_manager = hitl_manager
        self._hitl_timeout_s = hitl_timeout_s

    async def _handle_tool_error(
        self,
        *,
        error: BaseException,
        tool_name: str,
        attempt_num: int,
        state_version: int | None,
        trace_context: TraceContext,
        error_class_str: str | None = None,
    ) -> tuple[bool, ErrorClass | None, Cat8TerminationReason | None, str | None]:
        """Cat 8 chain: classify → record budget → check terminator.

        Day 3 helper (Day 4 wires into main loop). Returns:
            (should_terminate, error_class, termination_reason, detail)

        When Cat 8 deps are None, returns (False, None, None, None) — caller
        re-raises (preserves 53.1 behavior).

        Sprint 55.4 (closes AD-Cat8-3 narrow Option C): when ``error_class_str``
        is provided (soft-failure ToolResult path where original Exception
        type is lost — see loop.py:1072 synthetic), use
        ``classify_by_string()`` so the FQ class name preserved on
        ``ToolResult.error_class`` (53.3 US-9 mechanism) drives
        classification instead of MRO walk on the generic synthetic
        Exception (which would always return FATAL). Default ``None``
        preserves existing MRO classification for hard-exception path.
        """
        if self._error_policy is None:
            return False, None, None, None

        from agent_harness._contracts.errors import ErrorContext

        # 1. Classify — prefer string-based when provided (soft-failure path
        #    closes AD-Cat8-3 narrow Option C; type info preserved via
        #    ToolResult.error_class FQ class name set by ToolExecutorImpl).
        if error_class_str is not None:
            cls = self._error_policy.classify_by_string(error_class_str)
        else:
            cls = self._error_policy.classify(error)

        # 2. Record budget (skip FATAL — bug, not tenant-attributable)
        if self._error_budget is not None and self._tenant_id is not None:
            await self._error_budget.record(self._tenant_id, cls)

        # 3. Check terminator
        if self._error_terminator is not None and self._tenant_id is not None:
            decision = await self._error_terminator.evaluate(
                error=error,
                error_class=cls,
                context=ErrorContext(
                    source_category="tools",
                    tool_name=tool_name,
                    attempt_num=attempt_num,
                    state_version=state_version,
                    tenant_id=self._tenant_id,
                ),
                tenant_id=self._tenant_id,
            )
            if decision.terminate:
                return True, cls, decision.reason, decision.detail

        return False, cls, None, None

    async def _should_retry_tool_error(
        self,
        *,
        error: BaseException,
        error_class: ErrorClass | None,
        tool_name: str,
        attempt: int,
    ) -> tuple[bool, float]:
        """Cat 8 retry consultation per 53.2 spec docstring steps 2-4.

        Sprint 55.6 (closes AD-Cat8-2 — Option H): consults
        ``error_policy.should_retry`` (gate) → ``retry_policy.get_policy``
        (per-tool/class RetryConfig) → ``compute_backoff`` (sleep duration).
        Returns ``(should_retry, backoff_seconds)``. Step 5 (emit
        ``ErrorRetried`` + ``asyncio.sleep``) is the caller's responsibility
        so the retry loop can yield events into the SSE stream.

        Backwards-compat: returns ``(False, 0.0)`` whenever any Cat 8 dep is
        missing or the error class is unknown, preserving 53.1 baseline.
        """
        # Cat 8 deps None → preserve 53.1 baseline (no retry)
        if self._error_policy is None or self._retry_policy is None or error_class is None:
            return False, 0.0

        # Step 2: gate via error_class param (already classified by caller).
        # Per Cat 8 spec semantics: HITL_RECOVERABLE / FATAL never retry.
        # Sprint 55.6 D10: use error_class param directly instead of
        # error_policy.should_retry(error, attempt) re-classification.
        # Reason: soft-failure path passes a synthetic Exception whose MRO
        # walk (via DefaultErrorPolicy.classify) returns FATAL, but caller's
        # error_class came from classify_by_string(result.error_class) per
        # AD-Cat8-3 narrow Option C (Sprint 55.4). Trusting the param
        # honors both hard-exception (MRO classify) and soft-failure
        # (classify_by_string) paths uniformly.
        if error_class in (ErrorClass.HITL_RECOVERABLE, ErrorClass.FATAL):
            return False, 0.0

        # Step 3: per-(tool, class) RetryConfig lookup (matrix → defaults)
        config = self._retry_policy.get_policy(tool_name, error_class)

        # Defensive: avoid compute_backoff call when attempts already at cap.
        # `attempt` is 1-indexed (caller starts at 1; first retry = 2 onwards).
        # Treat attempt >= max_attempts as exhausted.
        if attempt >= config.max_attempts:
            return False, 0.0

        # Step 4: compute backoff (returns 0.0 when max_attempts == 0; defensive
        # double-check above already covers that path).
        backoff = compute_backoff(config, attempt)
        return True, backoff

    # === Cat 9 helpers (53.3 Day 4 US-7) =================================

    async def _audit_log_safe(
        self,
        *,
        event_type: str,
        content: dict[str, Any],
        ctx: TraceContext,
    ) -> None:
        """WORM append. Sprint 53.7 (closes AD-Cat9-7) made this fail-closed:
        if the WORM append raises (e.g. ``AuditAppendError`` from the underlying
        DB layer), the exception **propagates** to AgentLoop's top-level handler
        which treats it as FATAL (no retry, loop terminates).

        Compliance rationale: WORM audit log is non-negotiable. Allowing the
        loop to continue without an audit record (the 53.3 best-effort behavior)
        would leave Cat 9 events undetectable in post-incident audit. The
        method name is kept as ``_audit_log_safe`` for call-site compatibility
        but the semantics are now strict.
        """
        if self._audit_log is None or self._tenant_id is None:
            return
        # No try/except: AuditAppendError (or any other exception from
        # audit_log.append) propagates to AgentLoop run() handler, which
        # surfaces it as a fatal LoopFailed event. See 53.3 docstring on
        # WORMAuditLog: 'caller must escalate to ErrorTerminator FATAL'.
        await self._audit_log.append(
            tenant_id=self._tenant_id,
            event_type=event_type,
            content=content,
            user_id=ctx.user_id,
            session_id=ctx.session_id,
        )

    async def _cat9_input_check(
        self,
        *,
        user_input: str,
        ctx: TraceContext,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 loop-start gating. Yields GuardrailTriggered/TripwireTriggered
        + LoopCompleted on block; nothing on PASS.
        """
        if self._guardrail_engine is not None:
            g_result = await self._guardrail_engine.check_input(user_input, trace_context=ctx)
            if g_result.action != GuardrailAction.PASS:
                await self._audit_log_safe(
                    event_type=f"guardrail.input.{g_result.action.value}",
                    content={
                        "action": g_result.action.value,
                        "reason": g_result.reason or "",
                        "risk_level": g_result.risk_level,
                    },
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="input",
                    action=g_result.action.value,
                    reason=g_result.reason or "",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=0,
                    trace_context=ctx,
                )
                return

        if self._tripwire is not None:
            if await self._tripwire.trigger_check(content=user_input, trace_context=ctx):
                await self._audit_log_safe(
                    event_type="tripwire.input.triggered",
                    content={"content_excerpt": user_input[:200]},
                    ctx=ctx,
                )
                yield TripwireTriggered(
                    violation_type="input",
                    detail=f"input length={len(user_input)}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.TRIPWIRE.value,
                    total_turns=0,
                    trace_context=ctx,
                )
                return

    async def _cat9_tool_check(
        self,
        *,
        tc: ToolCall,
        ctx: TraceContext,
        turn_count: int,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 per-tool_call gating. Yields:
        GuardrailTriggered (action=BLOCK/ESCALATE/SANITIZE/REROLL) when
            guardrail returns non-PASS — caller wraps result as error
            ToolResult so LLM can adjust.
        TripwireTriggered + LoopCompleted(TRIPWIRE) when tripwire fires.
        """
        if self._guardrail_engine is not None:
            g_result = await self._guardrail_engine.check_tool_call(tc, trace_context=ctx)
            if g_result.action != GuardrailAction.PASS:
                # 53.5 US-3: ESCALATE → HITL pause + wait_for_decision when
                # hitl_manager wired. APPROVED → continue (no block); REJECTED
                # / ESCALATED / TIMEOUT → fall through to existing block path.
                # Other non-PASS actions (BLOCK / SANITIZE / REROLL) keep 53.3
                # baseline behavior (soft block, caller injects error ToolResult).
                if g_result.action == GuardrailAction.ESCALATE and self._hitl_manager is not None:
                    async for ev in self._cat9_hitl_branch(
                        tc=tc,
                        ctx=ctx,
                        guardrail_reason=g_result.reason or "escalated",
                    ):
                        yield ev
                    # _cat9_hitl_branch yields GuardrailTriggered(block) only
                    # when rejected/timeout — when approved, it returns
                    # without yielding so the caller flows to normal tool exec.
                    return

                await self._audit_log_safe(
                    event_type=f"guardrail.tool.{g_result.action.value}",
                    content={
                        "tool": tc.name,
                        "action": g_result.action.value,
                        "reason": g_result.reason or "",
                    },
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="tool",
                    action=g_result.action.value,
                    reason=g_result.reason or "blocked",
                    trace_context=ctx,
                )
                # Caller injects an error ToolResult after seeing this
                # event; we don't yield LoopCompleted here (only Tripwire
                # terminates the loop on tool calls — soft block continues).

        if self._tripwire is not None:
            if await self._tripwire.trigger_check(content=tc, trace_context=ctx):
                await self._audit_log_safe(
                    event_type="tripwire.tool.triggered",
                    content={"tool": tc.name},
                    ctx=ctx,
                )
                yield TripwireTriggered(
                    violation_type="tool",
                    detail=f"tool={tc.name}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.TRIPWIRE.value,
                    total_turns=turn_count,
                    trace_context=ctx,
                )
                return

    async def _cat9_hitl_branch(
        self,
        *,
        tc: ToolCall,
        ctx: TraceContext,
        guardrail_reason: str,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 ESCALATE → HITL pause + wait_for_decision (Sprint 53.5 US-3).

        Yields:
            ApprovalRequested  — request created, awaiting reviewer.
            ApprovalReceived   — reviewer decision (or timeout fallback).
            GuardrailTriggered(block) — only when REJECTED / ESCALATED / TIMEOUT.
                When APPROVED, no GuardrailTriggered is yielded — caller
                flows to normal tool execution.

        Risk level defaults to HIGH (escalation implies human review). Future
        sprints may pull from RiskPolicy via a callable injected at ctor time;
        keeping the default here avoids importing platform_layer/governance/risk
        from agent_harness (per category-boundaries.md backwards-import rule).

        Tenant + session context come from `self._tenant_id` and `ctx.session_id`.
        Both must be present; otherwise we fall back to the soft-block path
        (yielding GuardrailTriggered) since ApprovalRequest requires both.
        """
        if self._hitl_manager is None:  # defensive; caller already checked
            return

        tenant_id = self._tenant_id or ctx.tenant_id
        session_id = ctx.session_id
        if tenant_id is None or session_id is None:
            # Cannot build ApprovalRequest without identity; fail closed by
            # treating as block + audit + GuardrailTriggered. This is rare —
            # production wiring always supplies tenant_id (52.5 P0 #14).
            await self._audit_log_safe(
                event_type="guardrail.tool.escalate.no_identity",
                content={"tool": tc.name, "reason": guardrail_reason},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="tool",
                action="block",
                reason=f"escalation requires identity context: {guardrail_reason}",
                trace_context=ctx,
            )
            return

        request_id = uuid4()
        risk_level = RiskLevel.HIGH  # ESCALATE default; see method docstring
        sla_deadline = datetime.now(timezone.utc) + timedelta(seconds=self._hitl_timeout_s)
        approval_req = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            requester="guardrails",
            risk_level=risk_level,
            payload={
                "tool_name": tc.name,
                "tool_arguments": tc.arguments,
                "reason": guardrail_reason,
                "summary": f"approve tool call: {tc.name}",
            },
            sla_deadline=sla_deadline,
            context_snapshot={"tool_call_id": tc.id, "trace_id": ctx.trace_id},
        )

        # 1. Persist request via single-source HITLManager.
        try:
            await self._hitl_manager.request_approval(approval_req, trace_context=ctx)
        except Exception as exc:  # noqa: BLE001 — fail closed on persistence error
            await self._audit_log_safe(
                event_type="guardrail.tool.escalate.persist_failed",
                content={"tool": tc.name, "error": str(exc)},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="tool",
                action="block",
                reason=f"approval persistence failed: {exc}",
                trace_context=ctx,
            )
            return

        await self._audit_log_safe(
            event_type="guardrail.tool.escalate.requested",
            content={
                "tool": tc.name,
                "request_id": str(request_id),
                "risk_level": risk_level.value,
                "reason": guardrail_reason,
            },
            ctx=ctx,
        )
        yield ApprovalRequested(
            approval_request_id=request_id,
            risk_level=risk_level.value,
            trace_context=ctx,
        )

        # 2. Block for reviewer decision (cross-session resume supported by DB
        #    polling inside HITLManager.wait_for_decision).
        try:
            decision = await self._hitl_manager.wait_for_decision(
                request_id,
                timeout_s=self._hitl_timeout_s,
                trace_context=ctx,
            )
            outcome = decision.decision
        except TimeoutError:
            outcome = DecisionType.REJECTED
            decision = ApprovalDecision(
                request_id=request_id,
                decision=DecisionType.REJECTED,
                reviewer="system_timeout",
                decided_at=datetime.now(timezone.utc),
                reason="approval timeout",
            )

        await self._audit_log_safe(
            event_type=f"guardrail.tool.escalate.{outcome.value.lower()}",
            content={
                "tool": tc.name,
                "request_id": str(request_id),
                "decision": outcome.value,
                "reviewer": decision.reviewer,
                "reason": decision.reason or "",
            },
            ctx=ctx,
        )
        yield ApprovalReceived(
            approval_request_id=request_id,
            decision=outcome.value,
            trace_context=ctx,
        )

        if outcome == DecisionType.APPROVED:
            # No GuardrailTriggered → caller flows to normal tool execution.
            return

        # REJECTED / ESCALATED → block tool; LLM sees error ToolResult.
        yield GuardrailTriggered(
            guardrail_type="tool",
            action="block",
            reason=f"approval {outcome.value.lower()}: {decision.reason or 'no reason'}",
            trace_context=ctx,
        )

    async def _cat9_output_check(
        self,
        *,
        output_text: str,
        ctx: TraceContext,
        turn_count: int,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 loop-end output gating.

        BLOCK   → terminate with GUARDRAIL_BLOCKED (refuse output)
        SANITIZE/REROLL → emit GuardrailTriggered + continue (53.3 doesn't
                          mutate output text in-place; production wiring or
                          Cat 10 self-correction handles replacement)
        Tripwire → terminate with TRIPWIRE
        """
        if self._guardrail_engine is not None:
            g_result = await self._guardrail_engine.check_output(output_text, trace_context=ctx)
            if g_result.action == GuardrailAction.BLOCK:
                await self._audit_log_safe(
                    event_type="guardrail.output.block",
                    content={"reason": g_result.reason or ""},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="output",
                    action="block",
                    reason=g_result.reason or "",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=turn_count,
                    trace_context=ctx,
                )
                return
            elif g_result.action in (
                GuardrailAction.SANITIZE,
                GuardrailAction.REROLL,
                GuardrailAction.ESCALATE,
            ):
                await self._audit_log_safe(
                    event_type=f"guardrail.output.{g_result.action.value}",
                    content={"reason": g_result.reason or ""},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="output",
                    action=g_result.action.value,
                    reason=g_result.reason or "",
                    trace_context=ctx,
                )
                # Continue — caller's flow proceeds to LoopCompleted END_TURN.
                # Cat 10 self-correction loop (54.1) will replay LLM call on REROLL.

        if self._tripwire is not None:
            if await self._tripwire.trigger_check(content=output_text, trace_context=ctx):
                await self._audit_log_safe(
                    event_type="tripwire.output.triggered",
                    content={"text_excerpt": output_text[:200]},
                    ctx=ctx,
                )
                yield TripwireTriggered(
                    violation_type="output",
                    detail="output content tripped tripwire",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.TRIPWIRE.value,
                    total_turns=turn_count,
                    trace_context=ctx,
                )
                return

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """TAO main loop. Yields LoopEvent stream until terminated."""
        ctx = trace_context or TraceContext.create_root()
        messages: list[Message] = []
        if self._system_prompt:
            messages.append(Message(role="system", content=self._system_prompt))
        messages.append(Message(role="user", content=user_input))

        turn_count = 0
        tokens_used = 0
        # Sprint 57.2 US-1+US-2 bundled: per-run metrics accumulator
        # (closes AD-Cost-Ledger-Token-Split + Provider-Attribution +
        # Cat10-Cat11-LoopMetricsAccumulator). Local var (per-run, not
        # per-instance) so concurrent run() calls don't share state.
        metrics_acc = LoopMetricsAccumulator()

        async with self._tracer.start_span(
            name="agent_loop.run",
            category=SpanCategory.ORCHESTRATOR,
            trace_context=ctx,
        ):
            yield LoopStarted(session_id=session_id, trace_context=ctx)

            # === Cat 9 input guardrail check (53.3 Day 4 US-7) ============
            # Runs once at loop start (before any LLM call). Per plan §US-7:
            #   guardrail BLOCK/ESCALATE → GuardrailTriggered + audit
            #                              + LoopCompleted(GUARDRAIL_BLOCKED)
            #   tripwire trigger         → TripwireTriggered + audit
            #                              + LoopCompleted(TRIPWIRE)
            # No-op when corresponding deps are None (53.2 baseline).
            async for ev in self._cat9_input_check(user_input=user_input, ctx=ctx):
                yield ev
                if isinstance(ev, LoopCompleted):
                    return

            while True:
                # === Pre-LLM termination checks ============================
                if should_terminate_by_turns(turn_count, self._max_turns):
                    yield LoopCompleted(
                        stop_reason=TerminationReason.MAX_TURNS.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        trace_context=ctx,
                    )
                    return
                if should_terminate_by_tokens(tokens_used, self._token_budget):
                    yield LoopCompleted(
                        stop_reason=TerminationReason.TOKEN_BUDGET.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        trace_context=ctx,
                    )
                    return
                if should_terminate_by_cancellation():
                    yield LoopCompleted(
                        stop_reason=TerminationReason.CANCELLED.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        trace_context=ctx,
                    )
                    return

                # === Compaction check (Sprint 52.1 Day 2.7) =================
                # Cat 4 Compactor: Pre-LLM context compaction. Optional injection
                # — when None, this is a no-op (50.x backward compat).
                if self._compactor is not None:
                    compact_state = LoopState(
                        transient=TransientState(
                            messages=list(messages),
                            current_turn=turn_count,
                            token_usage_so_far=tokens_used,
                        ),
                        durable=DurableState(
                            session_id=session_id,
                            # 53.1: real tenant when ctor-injected; else session_id fallback
                            tenant_id=self._tenant_id or session_id,
                        ),
                        version=StateVersion(
                            version=turn_count,
                            parent_version=turn_count - 1 if turn_count > 0 else None,
                            created_at=datetime.now(),
                            created_by_category="orchestrator_loop",
                        ),
                    )
                    compaction_result = await self._compactor.compact_if_needed(
                        compact_state, trace_context=ctx
                    )
                    if (
                        compaction_result.triggered
                        and compaction_result.compacted_state is not None
                    ):
                        messages = list(compaction_result.compacted_state.transient.messages)
                        tokens_used = compaction_result.tokens_after
                        strategy_label = (
                            compaction_result.strategy_used.value
                            if compaction_result.strategy_used is not None
                            else "unknown"
                        )
                        yield ContextCompacted(
                            tokens_before=compaction_result.tokens_before,
                            tokens_after=compaction_result.tokens_after,
                            compaction_strategy=strategy_label,
                            messages_compacted=compaction_result.messages_compacted,
                            duration_ms=compaction_result.duration_ms,
                            trace_context=ctx,
                        )

                # === Per-turn marker (Sprint 50.2) ==========================
                yield TurnStarted(turn_num=turn_count, trace_context=ctx)

                # === Cat 5 PromptBuilder (Sprint 52.2 Day 3.1) ==============
                # When prompt_builder is injected, build a per-turn artifact
                # replacing the raw `messages` list at LLM call time. Conversation
                # accumulator (`messages`) continues to grow with assistant + tool
                # messages — only the chat() input is rebuilt each turn.
                # When None, falls back to 50.x baseline (raw messages, no cache).
                chat_messages: list[Message] = messages
                cache_breakpoints: list[CacheBreakpoint] | None = None
                if self._prompt_builder is not None:
                    build_state = LoopState(
                        transient=TransientState(
                            messages=list(messages),
                            current_turn=turn_count,
                            token_usage_so_far=tokens_used,
                        ),
                        durable=DurableState(
                            session_id=session_id,
                            # 53.1: real tenant when ctor-injected; else session_id fallback
                            tenant_id=self._tenant_id or session_id,
                        ),
                        version=StateVersion(
                            version=turn_count,
                            parent_version=turn_count - 1 if turn_count > 0 else None,
                            created_at=datetime.now(),
                            created_by_category="orchestrator_loop",
                        ),
                    )
                    t0 = time.perf_counter()
                    artifact = await self._prompt_builder.build(
                        state=build_state,
                        tenant_id=self._tenant_id or session_id,  # 53.1: real tenant when set
                        # 57.65 (A-1 Tier2): scope the user-layer memory to the
                        # authenticated user from the request TraceContext.
                        user_id=ctx.user_id,
                        tools=self._tool_registry.list(),
                        trace_context=ctx,
                    )
                    duration_ms = (time.perf_counter() - t0) * 1000.0
                    chat_messages = list(artifact.messages)
                    cache_breakpoints = (
                        list(artifact.cache_breakpoints) if artifact.cache_breakpoints else None
                    )
                    layers_used = artifact.layer_metadata.get("memory_layers_used", [])
                    strategy_used = artifact.layer_metadata.get("position_strategy", "")
                    yield PromptBuilt(
                        messages_count=len(artifact.messages),
                        estimated_input_tokens=artifact.estimated_input_tokens,
                        cache_breakpoints_count=len(artifact.cache_breakpoints),
                        memory_layers_used=(
                            tuple(layers_used) if isinstance(layers_used, (list, tuple)) else ()
                        ),
                        position_strategy_used=str(strategy_used),
                        duration_ms=duration_ms,
                        trace_context=ctx,
                    )

                # === LLM call ===============================================
                model_name = self._chat_client.model_info().model_name
                yield LLMRequested(
                    model=model_name,
                    tokens_in=0,  # Phase 52.1 wires count_tokens()
                    trace_context=ctx,
                )
                try:
                    request = ChatRequest(
                        messages=chat_messages,
                        tools=self._tool_registry.list(),
                    )
                    response: ChatResponse = await self._chat_client.chat(
                        request,
                        cache_breakpoints=cache_breakpoints,
                        trace_context=ctx,
                    )
                except asyncio.CancelledError:
                    yield LoopCompleted(
                        stop_reason=TerminationReason.CANCELLED.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        trace_context=ctx,
                    )
                    raise

                # Update token usage
                if response.usage is not None:
                    tokens_used += response.usage.total_tokens

                # Sprint 57.2 US-1+US-2 bundled: capture per-call metadata for
                # LoopCompleted aggregation (provider via adapter.model_info(),
                # model from ChatResponse, input/output split from usage).
                _provider = self._chat_client.model_info().provider
                _input_tokens = response.usage.prompt_tokens if response.usage else 0
                _output_tokens = response.usage.completion_tokens if response.usage else 0
                # Sprint 57.65 A-2 Tier2: cached-input tokens (prompt-cache
                # observability). Neutral signal from TokenUsage; dropped before
                # 57.65 (flowed only to billing). Feeds LoopCompleted.cache_hit_rate.
                _cached_input_tokens = response.usage.cached_input_tokens if response.usage else 0
                metrics_acc.cumulative_input_tokens += _input_tokens
                metrics_acc.cumulative_output_tokens += _output_tokens
                metrics_acc.cumulative_cached_input_tokens += _cached_input_tokens
                if _provider:
                    metrics_acc.last_provider = _provider
                if response.model:
                    metrics_acc.last_model = response.model
                metrics_acc.total_turns += 1

                # === Parse + emit LLMResponded + Thinking ==================
                parsed = await self._output_parser.parse(response, trace_context=ctx)
                # 50.2: LLMResponded carries the canonical (content, tool_calls, thinking) tuple
                # per 02-architecture-design.md §SSE llm_response schema. Thinking event is kept
                # for 50.1 test backward compatibility but no longer the SSE-canonical form.
                # 57.2: per-call provider/model/input_tokens/output_tokens added.
                yield LLMResponded(
                    content=parsed.text,
                    tool_calls=tuple(parsed.tool_calls),
                    thinking=None,
                    provider=_provider,
                    model=response.model,
                    input_tokens=_input_tokens,
                    output_tokens=_output_tokens,
                    cached_input_tokens=_cached_input_tokens,
                    trace_context=ctx,
                )
                yield Thinking(text=parsed.text, trace_context=ctx)

                # === Cat 7 post-LLM checkpoint (53.1 Day 3) =================
                # When reducer + checkpointer + tenant_id all set, persist a
                # state snapshot after LLM response so verifier / HITL pause /
                # error recovery have a recent restore point. No-op when any
                # is None (51.x backward-compat path).
                post_llm_event = await self._emit_state_checkpoint(
                    session_id=session_id,
                    messages=messages,
                    turn_count=turn_count,
                    tokens_used=tokens_used,
                    source_category="orchestrator_loop:post_llm",
                    ctx=ctx,
                )
                if post_llm_event is not None:
                    yield post_llm_event

                # === Cat 9 output guardrail check (53.3 Day 4 US-7) ========
                # Runs once per LLM response, BEFORE stop_reason terminator
                # so BLOCK / SANITIZE / REROLL can decide before LoopCompleted
                # fires. Tripwire on output → terminate. No-op when deps None.
                output_terminated = False
                async for ev in self._cat9_output_check(
                    output_text=parsed.text, ctx=ctx, turn_count=turn_count
                ):
                    yield ev
                    if isinstance(ev, LoopCompleted):
                        output_terminated = True
                if output_terminated:
                    return

                # === stop_reason terminator =================================
                if should_terminate_by_stop_reason(response):
                    yield LoopCompleted(
                        stop_reason=TerminationReason.END_TURN.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        # Sprint 57.2 US-1+US-2 bundled: accumulator-sourced split
                        input_tokens=metrics_acc.cumulative_input_tokens,
                        output_tokens=metrics_acc.cumulative_output_tokens,
                        provider=metrics_acc.last_provider,
                        model=metrics_acc.last_model,
                        # Sprint 57.65 A-2 Tier2: prompt-cache observability
                        cached_input_tokens=metrics_acc.cumulative_cached_input_tokens,
                        cache_hit_rate=metrics_acc.cache_hit_rate,
                        trace_context=ctx,
                    )
                    return

                # === Dispatch on OutputType =================================
                output_type = classify_output(response)

                if output_type == OutputType.FINAL:
                    yield LoopCompleted(
                        stop_reason=TerminationReason.END_TURN.value,
                        total_turns=turn_count,
                        total_tokens=tokens_used,
                        # Sprint 57.2 US-1+US-2 bundled: accumulator-sourced split
                        input_tokens=metrics_acc.cumulative_input_tokens,
                        output_tokens=metrics_acc.cumulative_output_tokens,
                        provider=metrics_acc.last_provider,
                        model=metrics_acc.last_model,
                        # Sprint 57.65 A-2 Tier2: prompt-cache observability
                        cached_input_tokens=metrics_acc.cumulative_cached_input_tokens,
                        cache_hit_rate=metrics_acc.cache_hit_rate,
                        trace_context=ctx,
                    )
                    return

                if output_type == OutputType.HANDOFF:
                    # Cat 11 not implemented yet; reserve enum for Phase 54.2.
                    yield LoopCompleted(
                        stop_reason=TerminationReason.HANDOFF_NOT_IMPLEMENTED.value,
                        total_turns=turn_count,
                        trace_context=ctx,
                    )
                    return

                # output_type == TOOL_USE
                # Append assistant message carrying the tool_calls so the
                # next chat() round-trip can correlate tool_call_id.
                messages.append(
                    Message(
                        role="assistant",
                        content=parsed.text,
                        tool_calls=parsed.tool_calls,
                    )
                )

                for tc in parsed.tool_calls:
                    yield ToolCallRequested(
                        tool_call_id=tc.id,
                        tool_name=tc.name,
                        arguments=tc.arguments,
                        trace_context=ctx,
                    )

                    # === Cat 9 per tool_call check (53.3 Day 4 US-7) ====
                    # tool guardrail BLOCK/ESCALATE → inject error ToolResult
                    #   so LLM sees failure + can self-correct (no loop terminate).
                    # tripwire trigger → emit TripwireTriggered + LoopCompleted.
                    cat9_blocked: ToolResult | None = None
                    cat9_terminated = False
                    async for ev in self._cat9_tool_check(tc=tc, ctx=ctx, turn_count=turn_count):
                        yield ev
                        if isinstance(ev, LoopCompleted):
                            cat9_terminated = True
                        elif isinstance(ev, GuardrailTriggered):
                            cat9_blocked = ToolResult(
                                tool_call_id=tc.id,
                                tool_name=tc.name,
                                content=(f"tool blocked by guardrail: {ev.reason}"),
                                success=False,
                                error=ev.reason,
                                duration_ms=0.0,
                            )
                    if cat9_terminated:
                        return
                    if cat9_blocked is not None:
                        result = cat9_blocked
                        result_text = self._tool_result_to_text(result.content)
                        # Append result to messages and skip tool execution.
                        # (Falls through to the result-append code below.)
                        messages.append(
                            Message(
                                role="tool",
                                content=result_text,
                                tool_call_id=tc.id,
                            )
                        )
                        yield ToolCallExecuted(
                            tool_call_id=tc.id,
                            tool_name=tc.name,
                            duration_ms=0.0,
                            result_content=result_text,
                            trace_context=ctx,
                        )
                        continue

                    # Sprint 55.6 — AD-Cat8-2 retry loop wrap (Option H).
                    # `attempt_num` starts at 1 (1-indexed per 53.2 docstring).
                    # On retry: yield ErrorRetried + asyncio.sleep(backoff) +
                    # increment + `continue`. `break` exits to post-execute
                    # path (tool_content / yield ToolCallExecuted-or-Failed /
                    # messages.append) which stays at original indent level.
                    # When Cat 8 deps None → _should_retry_tool_error returns
                    # (False, 0.0) → break on first iteration → 53.1 baseline.
                    attempt_num = 1
                    while True:
                        try:
                            # Sprint 52.5 P0 #18: build ExecutionContext from
                            # trace_context so memory_tools (and future scoped
                            # tools) get server-authoritative tenant_id /
                            # user_id / session_id instead of trusting LLM args.
                            exec_ctx = ExecutionContext(
                                tenant_id=ctx.tenant_id,
                                user_id=ctx.user_id,
                                session_id=ctx.session_id or session_id,
                            )
                            result = await self._tool_executor.execute(
                                tc, trace_context=ctx, context=exec_ctx
                            )
                        except asyncio.CancelledError:
                            yield LoopCompleted(
                                stop_reason=TerminationReason.CANCELLED.value,
                                total_turns=turn_count,
                                trace_context=ctx,
                            )
                            raise
                        except Exception as exc:
                            # 53.2 Day 4 Cat 8 chain: classify → record budget →
                            # check terminator. When Cat 8 deps None → re-raise
                            # (preserves 53.1 baseline).
                            # Sprint 55.6 D7 fix: pass real attempt_num (was hardcoded =1).
                            terminate, err_class, term_reason, term_detail = (
                                await self._handle_tool_error(
                                    error=exc,
                                    tool_name=tc.name,
                                    attempt_num=attempt_num,
                                    state_version=None,
                                    trace_context=ctx,
                                )
                            )
                            if self._error_policy is None:
                                # Opt-out path: no Cat 8 deps → preserve 53.1 raise behavior
                                raise
                            if terminate:
                                yield LoopTerminated(
                                    reason=(term_reason.value if term_reason is not None else ""),
                                    detail=term_detail,
                                    last_state_version=None,
                                    trace_context=ctx,
                                )
                                return

                            # Sprint 55.6 — AD-Cat8-2 (Option H) retry consultation
                            # on hard-exception path.
                            should_retry, backoff_s = await self._should_retry_tool_error(
                                error=exc,
                                error_class=err_class,
                                tool_name=tc.name,
                                attempt=attempt_num,
                            )
                            if should_retry:
                                yield ErrorRetried(
                                    attempt=attempt_num,
                                    error_class=err_class.value if err_class else "",
                                    backoff_ms=backoff_s * 1000.0,
                                    trace_context=ctx,
                                )
                                await asyncio.sleep(backoff_s)
                                attempt_num += 1
                                continue  # retry tool execution

                            # No retry → fall through to LLM-recoverable synthesis.
                            # Synthesize LLM-recoverable error ToolResult so the
                            # LLM sees the failure on next turn and can self-correct
                            # (Cat 8 §LLM-recoverable; Anthropic / LangGraph pattern).
                            # Note: ToolResult is now imported at module top (53.3 Day 4).
                            result = ToolResult(
                                tool_call_id=tc.id,
                                tool_name=tc.name,
                                content=f"Error: {exc!r}. Please adjust your approach.",
                                success=False,
                                error=repr(exc),
                                duration_ms=0.0,
                            )

                        # 53.2 Day 4 Cat 8 chain on soft failure: ToolExecutorImpl
                        # catches handler exceptions internally → ToolResult(success=
                        # False). Reconstruct a synthetic exception so the Cat 8
                        # chain can classify + check terminator. When deps None →
                        # fall through to existing 53.1 baseline (LLM-recoverable
                        # via tool message).
                        # Sprint 55.4 (AD-Cat8-3 narrow Option C): pass
                        # `result.error_class` (FQ class name set by ToolExecutorImpl
                        # per 53.3 US-9) so classification flows through
                        # classify_by_string() instead of MRO walk on the generic
                        # synthetic Exception (which would always return FATAL).
                        # Sprint 55.6 D7 fix: pass real attempt_num (was hardcoded =1).
                        if not result.success and self._error_policy is not None:
                            synthetic = Exception(result.error or "tool soft failure")
                            terminate, err_class, term_reason, term_detail = (
                                await self._handle_tool_error(
                                    error=synthetic,
                                    tool_name=tc.name,
                                    attempt_num=attempt_num,
                                    state_version=None,
                                    trace_context=ctx,
                                    error_class_str=result.error_class,
                                )
                            )
                            if terminate:
                                yield LoopTerminated(
                                    reason=(term_reason.value if term_reason is not None else ""),
                                    detail=term_detail,
                                    last_state_version=None,
                                    trace_context=ctx,
                                )
                                return

                            # Sprint 55.6 — AD-Cat8-2 (Option H) retry consultation
                            # on soft-failure path.
                            should_retry, backoff_s = await self._should_retry_tool_error(
                                error=synthetic,
                                error_class=err_class,
                                tool_name=tc.name,
                                attempt=attempt_num,
                            )
                            if should_retry:
                                yield ErrorRetried(
                                    attempt=attempt_num,
                                    error_class=err_class.value if err_class else "",
                                    backoff_ms=backoff_s * 1000.0,
                                    trace_context=ctx,
                                )
                                await asyncio.sleep(backoff_s)
                                attempt_num += 1
                                continue  # retry tool execution

                        # Success or no-retry path → exit retry loop. Post-execute
                        # code (tool_content / yield ToolCallExecuted-or-Failed /
                        # messages.append) follows at original indent level.
                        break

                    # Feed back as tool message — KEY V2 cure for AP-1.
                    tool_content = self._tool_result_to_text(result.content)

                    # 50.2: emit Cat 2-owned completion event so SSE / frontend
                    # see tool result text + success/failure.
                    if result.success:
                        yield ToolCallExecuted(
                            tool_call_id=tc.id,
                            tool_name=tc.name,
                            duration_ms=result.duration_ms or 0.0,
                            result_content=tool_content,
                            trace_context=ctx,
                        )
                    else:
                        yield ToolCallFailed(
                            tool_call_id=tc.id,
                            tool_name=tc.name,
                            error=result.error or "unknown tool error",
                            trace_context=ctx,
                        )

                    messages.append(
                        Message(
                            role="tool",
                            content=tool_content,
                            tool_call_id=tc.id,
                        )
                    )

                # === Cat 7 post-tool checkpoint (53.1 Day 3) ================
                # After all tool results are appended for this turn, persist
                # a snapshot so HITL pause / replay can resume from
                # complete-tool-batch boundary. No-op when not configured.
                post_tool_event = await self._emit_state_checkpoint(
                    session_id=session_id,
                    messages=messages,
                    turn_count=turn_count,
                    tokens_used=tokens_used,
                    source_category="orchestrator_loop:post_tool",
                    ctx=ctx,
                )
                if post_tool_event is not None:
                    yield post_tool_event

                turn_count += 1
                # loop continues to next while iteration

    async def resume(
        self,
        *,
        state: LoopState,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """Resume from checkpointed state.

        50.1 Day 2 stub — full implementation in Phase 53.1 when
        Checkpointer + State Mgmt land. Until then, calling resume()
        yields a single LoopCompleted with reason=ERROR and a clear
        message rather than silently breaking.
        """
        yield LoopCompleted(
            stop_reason=TerminationReason.ERROR.value,
            total_turns=0,
            trace_context=trace_context,
        )

    async def _emit_state_checkpoint(
        self,
        *,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
        tokens_used: int,
        source_category: str,
        ctx: TraceContext,
    ) -> StateCheckpointed | None:
        """Build LoopState from loop locals, reducer.merge → checkpointer.save.

        Returns StateCheckpointed event with DB chain version (caller yields).
        Returns None if reducer/checkpointer/tenant_id not all configured
        (i.e., 51.x backward-compat caller path). Errors are NOT swallowed;
        the loop should fail loud rather than silently miss a checkpoint.
        """
        if self._reducer is None or self._checkpointer is None or self._tenant_id is None:
            return None

        # Build snapshot state from current loop locals.
        snapshot_state = LoopState(
            transient=TransientState(
                messages=list(messages),
                current_turn=turn_count,
                token_usage_so_far=tokens_used,
            ),
            durable=DurableState(
                session_id=session_id,
                tenant_id=self._tenant_id,
            ),
            version=StateVersion(
                version=turn_count,
                parent_version=turn_count - 1 if turn_count > 0 else None,
                created_at=datetime.now(),
                created_by_category=source_category,
            ),
        )

        # In-memory version bump via Reducer (audit trail).
        bumped = await self._reducer.merge(
            snapshot_state,
            {"transient": {"current_turn": turn_count, "token_usage_so_far": tokens_used}},
            source_category=source_category,
            trace_context=ctx,
        )

        # Persist to DB; persisted version is from DB chain (authoritative).
        persisted = await self._checkpointer.save(bumped, trace_context=ctx)
        return StateCheckpointed(version=persisted.version, trace_context=ctx)

    @staticmethod
    def _tool_result_to_text(
        content: str | list[dict[str, object]] | list[ContentBlock],
    ) -> str:
        """Convert ToolResult.content to plain text for the next LLM round-trip.

        ToolResult.content can be `str` or `list[dict]` (per 49.1 spec).
        50.1 normalizes to str — image / json blocks left for Phase 51.1.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text_val = item.get("text") or item.get("content") or str(item)
                    parts.append(str(text_val))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)
