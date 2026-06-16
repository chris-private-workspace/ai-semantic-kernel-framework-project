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
             - HANDOFF  → yield LoopCompleted(handoff, handoff_target/reason) + return  [Cat 11]
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
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Sprint 57.127 — multi-turn rehydration via MessageStore dep; serde → _contracts
    - 2026-06-15: Sprint 57.122 — tool HITL reads tenant risk-threshold policy (load-bearing)
    - 2026-06-13: Sprint 57.111 A3 — _cat10_verify_gate threads real trace_state to the judge
    - 2026-06-12: Sprint 57.109 C2 — ContextCompacted yield carries summarize usage/model
    - 2026-06-12: Sprint 57.108 — 5 ApprovalRequested yields +reason= (tool site also +tool_name=)
    - 2026-06-11: Sprint 57.101 B1 — +message_inbox; _run_turns drains before between-turns gate
    - 2026-06-10: Sprint 57.100 — 5 ApprovalRequested yields +kind= (pause kind on the wire)
    - 2026-06-10: Sprint 57.99 A2 — resume() verify-kind: APPROVE replays / REJECT 1 coached turn
    - 2026-06-10: Sprint 57.99 A2 — verification-ESCALATE pause swaps the max-fail terminal (toggle)
    - 2026-06-10: Sprint 57.98 A1 US-3 — durable verification_attempts via checkpoint metadata
    - 2026-06-10: Sprint 57.98 A1 — in-loop Cat 10 verify gate (ctor registry + _cat10_verify_gate)
    - 2026-06-08: Sprint 57.93 — output-guardrail ESCALATE pre-delivery pause point (Slice 3)
    - 2026-06-08: Sprint 57.92 — between-turns guardrail ESCALATE pause point (Slice 3 leg 2)
    - 2026-06-08: Sprint 57.91 — _emit_deferred_pause primitive + input-ESCALATE pause point
    - 2026-06-08: Sprint 57.90 Slice 2 — resume() drives shared _run_turns; delete the reduced copy
    - 2026-06-08: Sprint 57.89 Slice 1 — extract per-turn body into re-enterable _run_turns()
    - 2026-06-08: Sprint 57.88 US-2 D2 — pause checkpoint self-contains messages (decision B)
    - 2026-06-08: Sprint 57.88 US-1/US-3 — deferred-HITL pause branch + resume() impl
    - 2026-06-03: Sprint 57.75 A-5c — emit SpanStarted/Ended (6 sites) + MemoryAccessed per-hint
    - 2026-06-02: Sprint 57.71 — add PROMPT_BUILD + COMPACTION spans (A-4 Tier 1 Stage 2)
    - 2026-06-02: Sprint 57.71 — root span as-child + TURN/LLM_CALL/TOOL_EXEC spans (A-4 Tier 1)
    - 2026-06-02: Sprint 57.69 A-3b — HANDOFF branch carries handoff_context (in-memory msgs)
    - 2026-06-02: Sprint 57.68 A-3b — HANDOFF branch yields stop_reason=handoff + target/reason
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
from dataclasses import dataclass

# Local import to avoid circular: only used at runtime for state placeholders
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, AsyncIterator
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
    MemoryAccessed,
    Message,
    MessageInjected,
    PromptBuilt,
    SpanCategory,
    SpanEnded,
    SpanStarted,
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
    VerificationResult,
)
from agent_harness._contracts.events import VerificationFailed, VerificationPassed
from agent_harness._contracts.hitl import (
    ApprovalDecision,
    ApprovalRequest,
    DecisionType,
    HITLPolicy,
    RiskLevel,
    decide_tool_hitl,
    resolve_tool_risk,
)
from agent_harness._contracts.message_serde import _message_from_dict, _message_to_dict
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
from agent_harness.output_parser import (
    HANDOFF_TOOL_NAME,
    OutputParser,
    OutputType,
    classify_output,
)
from agent_harness.prompt_builder import PromptBuilder
from agent_harness.state_mgmt import Checkpointer, MessageStore, Reducer
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

if TYPE_CHECKING:
    # Sprint 57.98 A1: VerifierRegistry is a type-only annotation, imported under
    # TYPE_CHECKING so the loop module carries no runtime dependency on the Cat 10
    # package for a forward-ref. Imported from the PACKAGE (not the private
    # submodule) per the cross-category import rule (17.md §1). The gate consumes
    # the registry by duck-typing (get_all()/len()); the persistence helper is
    # lazy-imported inside the gate (also from the package) to keep the loop
    # module's import-time dependency on Cat 10 to zero.
    # Sprint 57.101 B1: MessageInbox is a type-only annotation (the loop drains it
    # but never constructs it — the concrete backing is ctor-injected). Imported
    # from the PACKAGE per 17.md §1; TYPE_CHECKING keeps it a pure forward-ref.
    from agent_harness._contracts import MessageInbox
    from agent_harness.verification import VerifierRegistry

# Sprint 57.98 A1: stop-reason for LoopCompleted when the in-loop self-correction
# budget is exhausted (mirrors the retired correction_loop.py wrapper constant).
# A plain string, not a TerminationReason enum value — no consumer switches on it.
VERIFICATION_FAILED_STOP_REASON = "verification_failed"


# === Message <-> JSONB serde — moved to _contracts/message_serde.py (57.127) ==
# Why: the serde is now shared by TWO consumers — the deferred-HITL pause path
# (`messages_from_metadata`, below; 57.88) AND the new `messages`-table ledger
# (`state_mgmt.message_store.DBMessageStore`, 57.127 — live multi-turn
# rehydration), which CLOSES the "production should use a dedicated `messages`
# table" SPIKE NOTE this comment used to carry. Relocated to the `_contracts`
# leaf so `state_mgmt` can import it WITHOUT importing this heavy loop module
# (circular-import safety). `_message_to_dict` / `_message_from_dict` are
# imported at the top of this file; `_content_block_to_dict` stays internal to
# message_serde.


def messages_from_metadata(metadata: dict[str, Any]) -> list[Message]:
    """Rebuild the messages buffer from a paused checkpoint's metadata (57.88 US-2).

    Reads ``metadata["resume_messages"]`` (a list of `_message_to_dict` payloads
    persisted by the deferred-pause branch) and returns the rehydrated
    ``list[Message]``. Returns ``[]`` when absent / malformed (defensive — a
    checkpoint without resume_messages cannot be resumed; the caller terminates).
    """
    raw = metadata.get("resume_messages")
    if not isinstance(raw, list):
        return []
    out: list[Message] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(_message_from_dict(item))
    return out


@dataclass
class _VerifyVerdict:
    """Outcome of the in-loop Cat 10 verification gate (Sprint 57.98 A1).

    `outcome` drives the caller in `_run_turns`:
        - "pass"       → all verifiers passed; fall through to deliver.
        - "correct"    → ≥1 failed AND attempt < max; `correction_block` carries
                         the feedback to append before continuing the loop.
        - "failed_max" → ≥1 failed AND attempt == max; emit verification_failed.
    `events` are the VerificationPassed/Failed events the caller yields; the
    verif_* fields are the accumulated judge-token usage (Sprint 57.82) the
    caller stamps onto the terminal LoopCompleted.
    """

    outcome: str
    events: list[LoopEvent]
    correction_block: str | None
    verif_in: int
    verif_out: int
    verif_model: str | None


def _build_correction_block(failures: list[VerificationResult]) -> str:
    """Build the correction-feedback block appended as a user Message in-loop.

    Sprint 57.98 A1: the in-loop equivalent of the retired wrapper's
    _build_correction_input, MINUS the original input (the conversation —
    including the just-failed assistant answer — is already in `messages`, so
    only the feedback block is appended as a fresh user turn).
    """
    reasons = [f.reason or "unspecified" for f in failures]
    corrections = [f.suggested_correction for f in failures if f.suggested_correction]
    parts = [f"Previous attempt failed verification: {'; '.join(reasons)}"]
    if corrections:
        parts.append(f"Suggested: {' / '.join(corrections)}")
    parts.append("Please retry.")
    return "[" + ". ".join(parts) + "]"


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
        message_store: MessageStore | None = None,
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
        # 57.88 US-1 §durable HITL pause-resume: when True, a Cat 9 ESCALATE
        # checkpoints + emits ApprovalRequested + terminates the run with
        # stop_reason=awaiting_approval (releasing the SSE connection) instead
        # of blocking on wait_for_decision. Default False preserves the 53.5
        # blocking behavior for every existing caller / test.
        hitl_deferred: bool = False,
        # 57.98 A1 §Verification into the loop: opt-in Cat 10 registry. When set
        # (+ non-empty), the in-loop _cat10_verify_gate runs AFTER the output
        # guardrail and BEFORE the FINAL terminator; on FAIL it re-injects a
        # correction Message and continues the SAME loop (the in-loop critique),
        # exhausting at max_correction_attempts → stop_reason=verification_failed.
        # When None / empty, the gate is skipped (byte-identical to pre-57.98).
        # Replaces the run_with_verification wrapper (Cat 10 moves in-loop).
        verifier_registry: "VerifierRegistry | None" = None,
        max_correction_attempts: int = 2,
        # 57.99 A2 §Verification-ESCALATE: when True (+ a verifier registry +
        # hitl_deferred wiring), a max-attempts verification failure ESCALATEs to a
        # durable human HITL pause instead of the A1 verification_failed terminal.
        # APPROVE delivers the held failed answer (human overrides the judge);
        # REJECT-with-note re-injects the reviewer note as ONE human-coached turn
        # (a 2nd failure terminates, bounded by a durable verification_escalated
        # flag). Default False → the A1 terminal is byte-identical (the toggle
        # gates it; resume() drives the same gated _run_turns).
        verification_escalate_on_max: bool = False,
        # 57.101 B1 §between-turns injection: an optional message inbox the loop
        # drains at the TOP of each turn (before the between-turns guardrail), so a
        # mid-run injected message joins the conversation at the NEXT turn boundary
        # and is Cat 9-checked for free. When None, no drain runs (byte-identical to
        # pre-57.101). The concrete backing is ctor-injected (the chat path wires a
        # QueueMessageInbox over the module InjectionRegistry; B2 will back it with
        # the TEAMMATE mailbox — same ABC).
        message_inbox: "MessageInbox | None" = None,
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
        # Sprint 57.127 (AD-ChatV2-Live-MultiTurn-Context): the per-session Cat-3
        # message ledger. When None (subagent child loops / legacy callers) the
        # loop neither rehydrates prior context nor persists — baseline behavior.
        self._message_store = message_store
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
        # 57.88 US-1 §durable HITL pause-resume (see ctor docstring above).
        self._hitl_deferred = hitl_deferred
        # 57.98 A1 §Verification into the loop (see ctor docstring above).
        self._verifier_registry = verifier_registry
        self._max_correction_attempts = max_correction_attempts
        # 57.99 A2 §Verification-ESCALATE (see ctor docstring above).
        self._verification_escalate_on_max = verification_escalate_on_max
        # 57.101 B1 §between-turns injection (see ctor docstring above).
        self._message_inbox = message_inbox
        # 57.122 §HITL policy read-side (AD-HITL-Policy-ReadSide-Potemkin-Phase58):
        # the per-tenant HITLPolicy resolved ONCE per run (tenant_id is stable) +
        # cached, so the tool-call HITL decision reads the tenant's risk thresholds
        # without a DB round-trip per tool call. None until first Cat 9 tool check.
        self._hitl_policy_cache: HITLPolicy | None = None

    async def _resolve_hitl_policy(self, ctx: TraceContext) -> HITLPolicy:
        """Resolve + cache the per-tenant HITLPolicy for this run (Sprint 57.122).

        Reads ``hitl_manager.get_policy(tenant_id)`` (the production manager is wired
        with the DBHITLPolicyStore — service_factory.py). Fail-open: any store error,
        a missing manager, or a missing tenant_id falls back to the conservative
        DEFAULT policy (auto=LOW / require=MEDIUM) = the pre-57.122 effective
        behavior (a flagged tool floors to MEDIUM → escalates). Cached per run.
        """
        if self._hitl_policy_cache is not None:
            return self._hitl_policy_cache
        tenant_id = self._tenant_id or ctx.tenant_id
        policy: HITLPolicy | None = None
        if self._hitl_manager is not None and tenant_id is not None:
            try:
                policy = await self._hitl_manager.get_policy(tenant_id, trace_context=ctx)
            except Exception:  # noqa: BLE001 — fail-open to the conservative default
                policy = None
        if policy is None:
            policy = HITLPolicy(
                tenant_id=tenant_id or ctx.tenant_id or uuid4(),
                auto_approve_max_risk=RiskLevel.LOW,
                require_approval_min_risk=RiskLevel.MEDIUM,
            )
        self._hitl_policy_cache = policy
        return policy

    def _resolve_tool_call_risk(self, tool_name: str, *, flagged: bool) -> RiskLevel:
        """Resolve the effective risk of a tool call from its ToolSpec (57.122/57.124).

        Reads ``ToolSpec.risk_level`` + ``annotations.destructive`` from the registry;
        ``resolve_tool_risk`` applies the destructive HIGH-floor (57.124) + the per-rule
        flag MEDIUM-floor + the unknown-tool fallback.
        """
        spec = self._tool_registry.get(tool_name) if self._tool_registry is not None else None
        spec_risk = spec.risk_level if spec is not None else None
        destructive = spec.annotations.destructive if spec is not None else False
        return resolve_tool_risk(spec_risk, rule_requires_approval=flagged, destructive=destructive)

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
        session_id: UUID,
        messages: list[Message],
        turn_count: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 loop-start gating. Yields GuardrailTriggered/TripwireTriggered
        + LoopCompleted on block; nothing on PASS.

        Sprint 57.91 (Slice 3 leg 1): an input-guardrail ESCALATE with the
        deferred-HITL wiring PAUSES the loop (durable HITL) before any LLM call,
        awaiting human approval of the input itself — the first generalized pause
        point built on the _emit_deferred_pause primitive. `session_id` / `messages`
        / `turn_count` are threaded so the pause can persist a resumable checkpoint
        (input check runs at turn 0; the buffer is [system?, user]).
        """
        if self._guardrail_engine is not None:
            g_result = await self._guardrail_engine.check_input(user_input, trace_context=ctx)
            if g_result.action != GuardrailAction.PASS:
                # ESCALATE + deferred wiring → durable input pause. Otherwise
                # (BLOCK / SANITIZE / REROLL, or ESCALATE WITHOUT the HITL wiring)
                # fall through to the soft block below — fail closed: an ESCALATE
                # that cannot pause must NOT silently proceed.
                if (
                    g_result.action == GuardrailAction.ESCALATE
                    and self._hitl_manager is not None
                    and self._hitl_deferred
                    and self._checkpointer is not None
                    and self._reducer is not None
                ):
                    async for ev in self._cat9_input_hitl_pause(
                        user_input=user_input,
                        reason=g_result.reason or "escalated",
                        ctx=ctx,
                        session_id=session_id,
                        messages=messages,
                        turn_count=turn_count,
                    ):
                        yield ev
                    return

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

    async def _cat9_input_hitl_pause(
        self,
        *,
        user_input: str,
        reason: str,
        ctx: TraceContext,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 input-guardrail ESCALATE → durable HITL pause (Sprint 57.91).

        The input analogue of the tool-call _cat9_hitl_branch deferred path:
        build an input ApprovalRequest, emit ApprovalRequested, and pause via the
        generalized _emit_deferred_pause primitive with an INPUT-kind
        pending_approval (no tool_call). resume() of an input-kind pause runs no
        tool — the approved input simply proceeds to the first LLM turn. The
        caller (_cat9_input_check) gates on hitl_manager + hitl_deferred +
        checkpointer + reducer; this method handles the remaining no-identity /
        persist-failure cases by failing closed to a soft block
        (GuardrailTriggered(input, block) + GUARDRAIL_BLOCKED) — an ESCALATE that
        cannot pause must not proceed. risk_level defaults to HIGH (escalation
        implies human review), mirroring _cat9_hitl_branch.
        """
        if self._hitl_manager is None:  # defensive; caller already checked
            return

        tenant_id = self._tenant_id or ctx.tenant_id
        session_id_eff = ctx.session_id or session_id
        if tenant_id is None or session_id_eff is None:
            await self._audit_log_safe(
                event_type="guardrail.input.escalate.no_identity",
                content={"reason": reason},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="input",
                action="block",
                reason=f"escalation requires identity context: {reason}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        request_id = uuid4()
        risk_level = RiskLevel.HIGH  # ESCALATE default; mirror _cat9_hitl_branch
        sla_deadline = datetime.now(timezone.utc) + timedelta(seconds=self._hitl_timeout_s)
        approval_req = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id_eff,
            requester="guardrails",
            risk_level=risk_level,
            payload={
                "kind": "input",
                "input_excerpt": user_input[:200],
                "reason": reason,
                "summary": "approve user input",
            },
            sla_deadline=sla_deadline,
            context_snapshot={"trace_id": ctx.trace_id},
        )

        try:
            await self._hitl_manager.request_approval(approval_req, trace_context=ctx)
        except Exception as exc:  # noqa: BLE001 — fail closed on persistence error
            await self._audit_log_safe(
                event_type="guardrail.input.escalate.persist_failed",
                content={"error": str(exc)},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="input",
                action="block",
                reason=f"approval persistence failed: {exc}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        await self._audit_log_safe(
            event_type="guardrail.input.escalate.requested",
            content={
                "request_id": str(request_id),
                "risk_level": risk_level.value,
                "reason": reason,
            },
            ctx=ctx,
        )
        yield ApprovalRequested(
            approval_request_id=request_id,
            risk_level=risk_level.value,
            kind="input",
            reason=reason,
            trace_context=ctx,
        )

        pending_approval = {
            "kind": "input",
            "approval_request_id": str(request_id),
            "turn": turn_count,
        }
        async for ev in self._emit_deferred_pause(
            request_id=request_id,
            pending_approval=pending_approval,
            messages=messages,
            turn_count=turn_count,
            session_id=session_id_eff,
            audit_event_type="guardrail.input.escalate.deferred",
            audit_content={"request_id": str(request_id), "turn": turn_count},
            ctx=ctx,
        ):
            yield ev

    async def _cat9_tool_check(
        self,
        *,
        tc: ToolCall,
        ctx: TraceContext,
        turn_count: int,
        session_id: UUID,
        messages: list[Message],
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 per-tool_call gating. Yields:
        GuardrailTriggered (action=BLOCK/ESCALATE/SANITIZE/REROLL) when
            guardrail returns non-PASS — caller wraps result as error
            ToolResult so LLM can adjust.
        TripwireTriggered + LoopCompleted(TRIPWIRE) when tripwire fires.

        57.88 US-1: `session_id` + `messages` are threaded through so the
        deferred-HITL ESCALATE branch can build + persist a resumable
        checkpoint before terminating with ``awaiting_approval``.
        """
        if self._guardrail_engine is not None:
            g_result = await self._guardrail_engine.check_tool_call(tc, trace_context=ctx)
            action = g_result.action
            if action in (
                GuardrailAction.BLOCK,
                GuardrailAction.SANITIZE,
                GuardrailAction.REROLL,
            ):
                # 53.3 baseline soft block — caller injects an error ToolResult so
                # the LLM can adjust (only Tripwire terminates the loop on tools).
                await self._audit_log_safe(
                    event_type=f"guardrail.tool.{action.value}",
                    content={
                        "tool": tc.name,
                        "action": action.value,
                        "reason": g_result.reason or "",
                    },
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="tool",
                    action=action.value,
                    reason=g_result.reason or "blocked",
                    trace_context=ctx,
                )
            elif action in (GuardrailAction.PASS, GuardrailAction.ESCALATE):
                # 57.122 §HITL policy read-side (AD-HITL-Policy-ReadSide-Potemkin-
                # Phase58): the tenant's HITLPolicy thresholds now DECIDE escalate
                # vs auto-approve. `flagged` = the capability-matrix requires_approval
                # signal (guardrail ESCALATE). Using the tool's ToolSpec.risk_level:
                # a high-risk UNFLAGGED tool can now escalate (require_approval_min_
                # risk) and a flagged LOW-risk tool can auto-approve (auto_approve_
                # max_risk) — both previously ignored (a flat `if requires_approval:
                # ESCALATE` + hardcoded HIGH). Backward-compatible under the DEFAULT
                # policy (the flag floors risk to MEDIUM → still escalates).
                flagged = action == GuardrailAction.ESCALATE
                if self._hitl_manager is not None:
                    risk = self._resolve_tool_call_risk(tc.name, flagged=flagged)
                    policy = await self._resolve_hitl_policy(ctx)
                    if decide_tool_hitl(risk, policy, rule_requires_approval=flagged):
                        async for ev in self._cat9_hitl_branch(
                            tc=tc,
                            ctx=ctx,
                            guardrail_reason=g_result.reason
                            or ("escalated" if flagged else "risk threshold"),
                            turn_count=turn_count,
                            session_id=session_id,
                            messages=messages,
                            verification_attempts=verification_attempts,
                            risk=risk,
                        ):
                            yield ev
                        # _cat9_hitl_branch yields GuardrailTriggered(block) only
                        # when rejected/timeout; when approved (blocking) it returns
                        # without yielding (caller flows to normal tool exec); in
                        # deferred mode it yields LoopCompleted(awaiting_approval).
                        return
                    # else: the tenant policy auto-approves this tool → fall through
                    # to the tripwire check + normal tool execution (no event).
                elif flagged:
                    # ESCALATE but no HITL manager → fail-closed soft block (an
                    # escalation that cannot be serviced must not silently run).
                    await self._audit_log_safe(
                        event_type=f"guardrail.tool.{action.value}",
                        content={
                            "tool": tc.name,
                            "action": action.value,
                            "reason": g_result.reason or "",
                        },
                        ctx=ctx,
                    )
                    yield GuardrailTriggered(
                        guardrail_type="tool",
                        action=action.value,
                        reason=g_result.reason or "blocked",
                        trace_context=ctx,
                    )

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
        turn_count: int = 0,
        session_id: UUID | None = None,
        messages: list[Message] | None = None,
        verification_attempts: int = 0,
        risk: RiskLevel | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 ESCALATE → HITL pause (Sprint 53.5 US-3 + 57.88 US-1).

        Two modes (selected by ``self._hitl_deferred``):

        Blocking mode (default, 53.5 baseline):
            ApprovalRequested  — request created, awaiting reviewer.
            ApprovalReceived   — reviewer decision (or timeout fallback).
            GuardrailTriggered(block) — only when REJECTED / ESCALATED / TIMEOUT.
                When APPROVED, no GuardrailTriggered is yielded — caller
                flows to normal tool execution. (in-process ``wait_for_decision``)

        Deferred mode (57.88 US-1 — chat path durable pause-resume):
            ApprovalRequested  — request created.
            LoopCompleted(stop_reason="awaiting_approval") — after persisting an
                enriched checkpoint (pending tool call + approval_request_id +
                turn) so a later ``resume()`` can re-enter. NO blocking
                ``wait_for_decision`` call — the SSE connection is released and
                the human may take hours/days. Requires reducer + checkpointer +
                tenant_id wired (Cat 7); if any is missing the deferred branch
                falls back to blocking mode (it cannot persist a checkpoint).

        Risk level: 57.122 threads the tenant-policy-resolved ``risk`` in from
        _cat9_tool_check (ToolSpec.risk_level + the requires_approval MEDIUM-floor;
        AD-HITL-Policy-ReadSide-Potemkin-Phase58) so the ApprovalRequest + reviewer
        routing + SLA flow from the real risk. ``risk=None`` (no caller threads it)
        falls back to HIGH (escalation implies human review) — the pre-57.122
        default. This avoids importing platform_layer/governance/risk from
        agent_harness (per category-boundaries.md backwards-import rule).

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
        risk_level = risk if risk is not None else RiskLevel.HIGH  # 57.122: policy-resolved
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
            kind="tool",
            tool_name=tc.name,
            reason=guardrail_reason,
            trace_context=ctx,
        )

        # 2a. 57.88 US-1 — DEFERRED mode: persist a resumable checkpoint and
        #     terminate with ``awaiting_approval`` (release the connection) so a
        #     later resume() can re-enter. No blocking wait. Requires Cat 7
        #     (reducer + checkpointer + tenant_id); without it we cannot persist
        #     the resume payload, so we fall through to blocking mode.
        if (
            self._hitl_deferred
            and self._checkpointer is not None
            and self._reducer is not None
            and session_id is not None
        ):
            # Sprint 57.91 (Slice 3 leg 1): route through the generalized
            # _emit_deferred_pause primitive. The `kind` discriminator lets
            # resume() pick the tool re-entry path (exec the pending tool) vs the
            # input path (no tool). Behavior here is byte-identical to 57.88.
            pending_approval = {
                "kind": "tool",
                "tool_call": {
                    "name": tc.name,
                    "arguments": dict(tc.arguments),
                    "tool_call_id": tc.id,
                },
                "approval_request_id": str(request_id),
                "turn": turn_count,
            }
            async for ev in self._emit_deferred_pause(
                request_id=request_id,
                pending_approval=pending_approval,
                messages=messages if messages is not None else [],
                turn_count=turn_count,
                session_id=session_id,
                audit_event_type="guardrail.tool.escalate.deferred",
                audit_content={
                    "tool": tc.name,
                    "request_id": str(request_id),
                    "turn": turn_count,
                },
                ctx=ctx,
                verification_attempts=verification_attempts,
            ):
                yield ev
            return

        # 2b. Block for reviewer decision (cross-session resume supported by DB
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

    async def _emit_deferred_pause(
        self,
        *,
        request_id: UUID,
        pending_approval: dict[str, Any],
        messages: list[Message],
        turn_count: int,
        session_id: UUID,
        audit_event_type: str,
        audit_content: dict[str, Any],
        ctx: TraceContext,
        verification_attempts: int = 0,
        verification_escalated: bool = False,
    ) -> AsyncIterator[LoopEvent]:
        """Generalized durable-pause tail (Sprint 57.91, 地基 A Slice 3 leg 1).

        The shared end of EVERY durable pause: persist a resumable checkpoint
        carrying ``pending_approval`` (+ the message buffer, via
        _emit_state_checkpoint) in the existing state_snapshots JSONB (no
        migration), audit, and terminate with ``awaiting_approval`` — releasing
        the SSE connection so a later resume() can re-enter. Decoupled from WHAT
        is being approved: the caller has already created + persisted the
        ApprovalRequest, yielded ApprovalRequested, and built the
        ``pending_approval`` payload (``kind`` discriminator: "tool" carries a
        tool_call resume() re-executes, "input" carries none — resume() just
        continues to the first LLM turn). Shared by the tool-call ESCALATE branch
        (_cat9_hitl_branch) and the input-guardrail ESCALATE branch
        (_cat9_input_check). Requires Cat 7 (reducer + checkpointer + tenant_id);
        the caller gates on that — if a checkpoint cannot persist, the caller
        falls back to its block path (it cannot offer a resumable pause).
        """
        checkpoint_event = await self._emit_state_checkpoint(
            session_id=session_id,
            messages=messages,
            turn_count=turn_count,
            tokens_used=0,
            source_category="orchestrator_loop:hitl_pause",
            ctx=ctx,
            pending_approval=pending_approval,
            verification_attempts=verification_attempts,
            verification_escalated=verification_escalated,
        )
        if checkpoint_event is not None:
            yield checkpoint_event
        await self._audit_log_safe(
            event_type=audit_event_type,
            content=audit_content,
            ctx=ctx,
        )
        yield LoopCompleted(
            stop_reason=TerminationReason.AWAITING_APPROVAL.value,
            total_turns=turn_count,
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

    @staticmethod
    def _latest_output_text(messages: list[Message]) -> str:
        """Return the just-completed turn's output text for the between-turns check.

        The content of the last assistant/tool message with truthy content (a
        completed TOOL_USE turn ends with a tool result; an assistant turn may
        carry text). Empty string when none — the between-turns guardrail then
        sees no trigger and PASSes. (Sprint 57.92, 地基 A Slice 3 leg 2.)
        """
        for msg in reversed(messages):
            if msg.role in ("assistant", "tool") and msg.content:
                return str(msg.content)
        return ""

    async def _cat9_between_turns_check(
        self,
        *,
        messages: list[Message],
        ctx: TraceContext,
        turn_count: int,
        session_id: UUID,
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 between-turns gating (Sprint 57.92, 地基 A Slice 3 leg 2).

        Runs at the _run_turns loop top after ≥1 completed turn (turn_count > 0),
        BEFORE the next LLM call, on the just-completed turn's output (the last
        assistant/tool message text). An ESCALATE with the deferred-HITL wiring
        PAUSES the loop durably for human approval of CONTINUING — the second
        generalized pause point on the _emit_deferred_pause primitive; resume()
        continues to the next turn's LLM call (which has NOT run, so no
        re-generation). Any other non-PASS (BLOCK, or ESCALATE WITHOUT the HITL
        wiring) fails closed to GUARDRAIL_BLOCKED — an ESCALATE that cannot pause
        must NOT silently proceed. PASS → nothing (the loop runs the next turn).
        """
        if self._guardrail_engine is None:
            return
        content = self._latest_output_text(messages)
        g_result = await self._guardrail_engine.check_between_turns(content, trace_context=ctx)
        if g_result.action == GuardrailAction.PASS:
            return
        if (
            g_result.action == GuardrailAction.ESCALATE
            and self._hitl_manager is not None
            and self._hitl_deferred
            and self._checkpointer is not None
            and self._reducer is not None
        ):
            async for ev in self._cat9_between_turns_hitl_pause(
                output_excerpt=content,
                reason=g_result.reason or "escalated",
                ctx=ctx,
                session_id=session_id,
                messages=messages,
                turn_count=turn_count,
                verification_attempts=verification_attempts,
            ):
                yield ev
            return
        await self._audit_log_safe(
            event_type=f"guardrail.between_turns.{g_result.action.value}",
            content={
                "action": g_result.action.value,
                "reason": g_result.reason or "",
                "risk_level": g_result.risk_level,
            },
            ctx=ctx,
        )
        yield GuardrailTriggered(
            guardrail_type="between_turns",
            action=g_result.action.value,
            reason=g_result.reason or "",
            trace_context=ctx,
        )
        yield LoopCompleted(
            stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
            total_turns=turn_count,
            trace_context=ctx,
        )

    async def _cat9_between_turns_hitl_pause(
        self,
        *,
        output_excerpt: str,
        reason: str,
        ctx: TraceContext,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 between-turns ESCALATE → durable HITL pause (Sprint 57.92).

        The between-turns analogue of _cat9_input_hitl_pause: build a between-turns
        ApprovalRequest, emit ApprovalRequested, and pause via the generalized
        _emit_deferred_pause primitive with a BETWEEN_TURNS-kind pending_approval
        (no tool_call). resume() of a between-turns pause runs no tool — the
        approved continuation proceeds to the next turn's LLM call with the gate
        skipped once (so the same boundary does not re-escalate). The caller
        (_cat9_between_turns_check) gates on hitl_manager + hitl_deferred +
        checkpointer + reducer; this method fails closed on the remaining
        no-identity / persist-failure cases (GuardrailTriggered(between_turns,
        block) + GUARDRAIL_BLOCKED). risk_level defaults to HIGH (escalation
        implies human review), mirroring _cat9_input_hitl_pause.
        """
        if self._hitl_manager is None:  # defensive; caller already checked
            return

        tenant_id = self._tenant_id or ctx.tenant_id
        session_id_eff = ctx.session_id or session_id
        if tenant_id is None or session_id_eff is None:
            await self._audit_log_safe(
                event_type="guardrail.between_turns.escalate.no_identity",
                content={"reason": reason},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="between_turns",
                action="block",
                reason=f"escalation requires identity context: {reason}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        request_id = uuid4()
        risk_level = RiskLevel.HIGH  # ESCALATE default; mirror _cat9_input_hitl_pause
        sla_deadline = datetime.now(timezone.utc) + timedelta(seconds=self._hitl_timeout_s)
        approval_req = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id_eff,
            requester="guardrails",
            risk_level=risk_level,
            payload={
                "kind": "between_turns",
                "output_excerpt": output_excerpt[:200],
                "reason": reason,
                "summary": "approve continuation",
            },
            sla_deadline=sla_deadline,
            context_snapshot={"trace_id": ctx.trace_id},
        )

        try:
            await self._hitl_manager.request_approval(approval_req, trace_context=ctx)
        except Exception as exc:  # noqa: BLE001 — fail closed on persistence error
            await self._audit_log_safe(
                event_type="guardrail.between_turns.escalate.persist_failed",
                content={"error": str(exc)},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="between_turns",
                action="block",
                reason=f"approval persistence failed: {exc}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        await self._audit_log_safe(
            event_type="guardrail.between_turns.escalate.requested",
            content={
                "request_id": str(request_id),
                "risk_level": risk_level.value,
                "reason": reason,
            },
            ctx=ctx,
        )
        yield ApprovalRequested(
            approval_request_id=request_id,
            risk_level=risk_level.value,
            kind="between_turns",
            reason=reason,
            trace_context=ctx,
        )

        pending_approval = {
            "kind": "between_turns",
            "approval_request_id": str(request_id),
            "turn": turn_count,
        }
        async for ev in self._emit_deferred_pause(
            request_id=request_id,
            pending_approval=pending_approval,
            messages=messages,
            turn_count=turn_count,
            session_id=session_id_eff,
            audit_event_type="guardrail.between_turns.escalate.deferred",
            audit_content={"request_id": str(request_id), "turn": turn_count},
            ctx=ctx,
            verification_attempts=verification_attempts,
        ):
            yield ev

    async def _cat9_output_escalate_pause(
        self,
        *,
        output_text: str,
        response_snapshot: dict[str, Any],
        ctx: TraceContext,
        turn_count: int,
        session_id: UUID,
        messages: list[Message],
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 output-guardrail ESCALATE → pre-delivery HITL pause (Sprint 57.93).

        The pre-delivery gate for a FINAL answer: runs the EXISTING OUTPUT chain
        (check_output) BEFORE LLMResponded renders the answer (the frontend draws
        the AnswerBlock from llm_response, so a pause after that point would be a
        Potemkin). On ESCALATE it durably pauses for human approval of DELIVERING
        the answer — the third generalized pause point on the _emit_deferred_pause
        primitive; resume() re-emits the held answer (no LLM re-call) on approval,
        or withholds it (GUARDRAIL_BLOCKED) on rejection. Any non-ESCALATE result
        returns (no-op): the caller falls through to the unchanged LLMResponded +
        per-response _cat9_output_check (BLOCK / SANITIZE / REROLL / tripwire). The
        caller gates this on is_final_answer + the full deferred-HITL wiring so
        non-HITL / non-final paths never enter here.
        """
        if self._guardrail_engine is None:
            return
        g_result = await self._guardrail_engine.check_output(output_text, trace_context=ctx)
        if g_result.action == GuardrailAction.ESCALATE:
            async for ev in self._cat9_output_hitl_pause(
                answer_text=output_text,
                response_snapshot=response_snapshot,
                reason=g_result.reason or "escalated",
                ctx=ctx,
                session_id=session_id,
                messages=messages,
                turn_count=turn_count,
                verification_attempts=verification_attempts,
            ):
                yield ev
        # else: no-op — the caller falls through to LLMResponded + _cat9_output_check.

    async def _cat9_output_hitl_pause(
        self,
        *,
        answer_text: str,
        response_snapshot: dict[str, Any],
        reason: str,
        ctx: TraceContext,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 9 output ESCALATE → durable pre-delivery HITL pause (Sprint 57.93).

        The output analogue of _cat9_between_turns_hitl_pause: build an output
        ApprovalRequest, emit ApprovalRequested, and pause via the generalized
        _emit_deferred_pause primitive with an OUTPUT-kind pending_approval (no
        tool_call) carrying the held-answer snapshot so resume() can re-emit the
        answer WITHOUT re-calling the LLM. The caller (_cat9_output_escalate_pause)
        gates on hitl_manager + hitl_deferred + checkpointer + reducer; this method
        fails closed on the remaining no-identity / persist-failure cases
        (GuardrailTriggered(output, block) + GUARDRAIL_BLOCKED). risk_level defaults
        to HIGH (escalation implies human review).
        """
        if self._hitl_manager is None:  # defensive; caller already checked
            return

        tenant_id = self._tenant_id or ctx.tenant_id
        session_id_eff = ctx.session_id or session_id
        if tenant_id is None or session_id_eff is None:
            await self._audit_log_safe(
                event_type="guardrail.output.escalate.no_identity",
                content={"reason": reason},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="output",
                action="block",
                reason=f"escalation requires identity context: {reason}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        request_id = uuid4()
        risk_level = RiskLevel.HIGH  # ESCALATE default; mirror _cat9_between_turns_hitl_pause
        sla_deadline = datetime.now(timezone.utc) + timedelta(seconds=self._hitl_timeout_s)
        approval_req = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id_eff,
            requester="guardrails",
            risk_level=risk_level,
            payload={
                "kind": "output",
                "output_excerpt": answer_text[:200],
                "reason": reason,
                "summary": "approve delivery",
            },
            sla_deadline=sla_deadline,
            context_snapshot={"trace_id": ctx.trace_id},
        )

        try:
            await self._hitl_manager.request_approval(approval_req, trace_context=ctx)
        except Exception as exc:  # noqa: BLE001 — fail closed on persistence error
            await self._audit_log_safe(
                event_type="guardrail.output.escalate.persist_failed",
                content={"error": str(exc)},
                ctx=ctx,
            )
            yield GuardrailTriggered(
                guardrail_type="output",
                action="block",
                reason=f"approval persistence failed: {exc}",
                trace_context=ctx,
            )
            yield LoopCompleted(
                stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        await self._audit_log_safe(
            event_type="guardrail.output.escalate.requested",
            content={
                "request_id": str(request_id),
                "risk_level": risk_level.value,
                "reason": reason,
            },
            ctx=ctx,
        )
        yield ApprovalRequested(
            approval_request_id=request_id,
            risk_level=risk_level.value,
            kind="output",
            reason=reason,
            trace_context=ctx,
        )

        pending_approval = {
            "kind": "output",
            "approval_request_id": str(request_id),
            "turn": turn_count,
            "response_snapshot": response_snapshot,
        }
        async for ev in self._emit_deferred_pause(
            request_id=request_id,
            pending_approval=pending_approval,
            messages=messages,
            turn_count=turn_count,
            session_id=session_id_eff,
            audit_event_type="guardrail.output.escalate.deferred",
            audit_content={"request_id": str(request_id), "turn": turn_count},
            ctx=ctx,
            verification_attempts=verification_attempts,
        ):
            yield ev

    async def _cat10_verify_gate(
        self,
        *,
        output_text: str,
        messages: list[Message],
        turn_count: int,
        session_id: UUID,
        attempt: int,
        ctx: TraceContext,
    ) -> _VerifyVerdict:
        """Run the Cat 10 verifiers on a FINAL candidate answer (Sprint 57.98 A1).

        The in-loop replacement for the run_with_verification wrapper's verify
        block. Runs every registered verifier on `output_text`; collects a
        VerificationPassed / VerificationFailed event per result (the caller
        yields them); best-effort persists each (Sprint 57.11); accumulates judge
        tokens (Sprint 57.82). Returns a verdict the caller acts on (pass /
        correct / failed_max — see _VerifyVerdict). Caller-gated on
        `self._verifier_registry` being set + non-empty.

        The persistence helper is lazy-imported (not module-level) from the Cat 10
        package so the loop module carries no import-time dependency on Cat 10 (see
        the TYPE_CHECKING note above; imported from the package per 17.md §1).
        """
        from agent_harness.verification import persist_verification_event

        registry = self._verifier_registry
        assert registry is not None  # caller-gated (registry set + non-empty)
        events: list[LoopEvent] = []
        failures: list[VerificationResult] = []
        verif_in = 0
        verif_out = 0
        verif_model: str | None = None
        # A3 (57.111): build the loop-state snapshot the trace-aware judge reads
        # (recent turns + tool errors via transient.messages). Mirrors the Cat 4
        # compactor's state build. The candidate answer is NOT in `messages` here —
        # the caller appends it AFTER this gate (see _run_turns ~:2552) → the trace
        # carries only the PRIOR turns, no double-count. A None-state path stays for
        # the Cat 9 fallback judge sites (they have no loop → string-only critique).
        trace_state = LoopState(
            transient=TransientState(messages=list(messages), current_turn=turn_count),
            durable=DurableState(
                session_id=session_id,
                tenant_id=self._tenant_id or session_id,
            ),
            version=StateVersion(
                version=turn_count,
                parent_version=turn_count - 1 if turn_count > 0 else None,
                created_at=datetime.now(),
                created_by_category="orchestrator_loop",
            ),
        )
        for verifier in registry.get_all():
            result = await verifier.verify(
                output=output_text,
                state=trace_state,
                trace_context=ctx,
            )
            if result.passed:
                events.append(
                    VerificationPassed(
                        verifier=result.verifier_name,
                        score=result.score,
                        verifier_type=result.verifier_type,
                        trace_context=ctx,
                    )
                )
            else:
                events.append(
                    VerificationFailed(
                        verifier=result.verifier_name,
                        reason=result.reason,
                        suggested_correction=result.suggested_correction,
                        verifier_type=result.verifier_type,
                        correction_attempt=attempt,
                        trace_context=ctx,
                    )
                )
                failures.append(result)
            # Sprint 57.82: accumulate judge tokens (pass OR fail — the LLM call
            # was chargeable either way; rules-based verifiers contribute 0).
            verif_in += result.input_tokens
            verif_out += result.output_tokens
            if result.model:
                verif_model = result.model
            # Sprint 57.11 (migrated in-loop 57.98): best-effort verification_log
            # row per verifier so a single crash does not orphan its siblings.
            await persist_verification_event(
                tenant_id=ctx.tenant_id,
                session_id=session_id,
                turn_index=turn_count,
                verifier_name=result.verifier_name,
                verifier_type=result.verifier_type,
                passed=result.passed,
                score=result.score,
                reason=result.reason,
                suggested_correction=result.suggested_correction,
                correction_attempt=attempt,
            )
        if not failures:
            return _VerifyVerdict("pass", events, None, verif_in, verif_out, verif_model)
        if attempt >= self._max_correction_attempts:
            return _VerifyVerdict("failed_max", events, None, verif_in, verif_out, verif_model)
        return _VerifyVerdict(
            "correct",
            events,
            _build_correction_block(failures),
            verif_in,
            verif_out,
            verif_model,
        )

    async def _cat10_verification_escalate_pause(
        self,
        *,
        answer_text: str,
        response_snapshot: dict[str, Any],
        verdict: "_VerifyVerdict",
        ctx: TraceContext,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
        verification_attempts: int = 0,
    ) -> AsyncIterator[LoopEvent]:
        """Cat 10 max-attempts verification failure → human ESCALATE pause (57.99 A2).

        The verification analogue of _cat9_output_hitl_pause: when in-loop
        self-correction is exhausted (verdict.outcome == "failed_max") AND the
        chat_verification_escalate_on_max toggle is on AND this run has not already
        escalated, pause for a human instead of the A1 verification_failed terminal.
        Build a "verification"-kind pending_approval carrying the held failed-answer
        snapshot (the _replay_approved_output field set) so resume() can DELIVER the
        held answer on APPROVE (human overrides the judge — NO LLM re-call) or
        re-inject the reviewer note as one human-coached turn on REJECT. Persists the
        durable verification_escalated=True so a REJECT continuation that fails again
        takes the A1 terminal (the bound: exactly one coached turn). The caller gates
        on the full HITL wiring (hitl_manager + hitl_deferred + checkpointer +
        reducer); this method fails closed on the remaining no-identity / persist-
        failure cases by falling back to the A1 verification_failed terminal (it
        cannot offer a resumable pause). risk_level defaults to HIGH.
        """
        if self._hitl_manager is None:  # defensive; caller already checked
            return

        tenant_id = self._tenant_id or ctx.tenant_id
        session_id_eff = ctx.session_id or session_id
        if tenant_id is None or session_id_eff is None:
            await self._audit_log_safe(
                event_type="verification.escalate.no_identity",
                content={"attempts": verification_attempts},
                ctx=ctx,
            )
            # Fall back to the A1 terminal — cannot pause without identity context.
            yield LoopCompleted(
                stop_reason=VERIFICATION_FAILED_STOP_REASON,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        # Human-readable reason from the failed verifiers (the verdict for a
        # failed_max outcome carries the per-verifier VerificationFailed events).
        reasons = [
            ev.reason for ev in verdict.events if isinstance(ev, VerificationFailed) and ev.reason
        ]
        reason = "; ".join(reasons) if reasons else "verification failed at max attempts"

        request_id = uuid4()
        risk_level = RiskLevel.HIGH  # ESCALATE default; mirror _cat9_output_hitl_pause
        sla_deadline = datetime.now(timezone.utc) + timedelta(seconds=self._hitl_timeout_s)
        approval_req = ApprovalRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id_eff,
            requester="verification",
            risk_level=risk_level,
            payload={
                "kind": "verification",
                "output_excerpt": answer_text[:200],
                "reason": reason,
                "summary": "approve delivery (override the verifier) or reject with a note",
            },
            sla_deadline=sla_deadline,
            context_snapshot={"trace_id": ctx.trace_id},
        )

        try:
            await self._hitl_manager.request_approval(approval_req, trace_context=ctx)
        except Exception as exc:  # noqa: BLE001 — fail closed to the A1 terminal
            await self._audit_log_safe(
                event_type="verification.escalate.persist_failed",
                content={"error": str(exc)},
                ctx=ctx,
            )
            yield LoopCompleted(
                stop_reason=VERIFICATION_FAILED_STOP_REASON,
                total_turns=turn_count,
                trace_context=ctx,
            )
            return

        await self._audit_log_safe(
            event_type="verification.escalate.requested",
            content={
                "request_id": str(request_id),
                "risk_level": risk_level.value,
                "reason": reason,
                "attempts": verification_attempts,
            },
            ctx=ctx,
        )
        yield ApprovalRequested(
            approval_request_id=request_id,
            risk_level=risk_level.value,
            kind="verification",
            reason=reason,
            trace_context=ctx,
        )

        pending_approval = {
            "kind": "verification",
            "approval_request_id": str(request_id),
            "turn": turn_count,
            "response_snapshot": response_snapshot,
        }
        async for ev in self._emit_deferred_pause(
            request_id=request_id,
            pending_approval=pending_approval,
            messages=messages,
            turn_count=turn_count,
            session_id=session_id_eff,
            audit_event_type="verification.escalate.deferred",
            audit_content={"request_id": str(request_id), "turn": turn_count},
            ctx=ctx,
            verification_attempts=verification_attempts,
            verification_escalated=True,
        ):
            yield ev

    async def _persist_to_ledger(self, msgs: list[Message], *, turn_num: int) -> None:
        """Append NEW messages to the durable per-session ledger (best-effort,
        no-op without a store). Sprint 57.127 — used by run() for the user prompt
        at send start + the final assistant answer at end_turn so a follow-up send
        rehydrates them. ONLY new messages are passed (never system / prior /
        intra-turn tool round-trips — the final answer is the cross-send unit)."""
        if self._message_store is not None and msgs:
            await self._message_store.append(msgs, turn_num=turn_num)

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """TAO main loop. Yields LoopEvent stream until terminated."""
        ctx = trace_context or TraceContext.create_root()
        # Sprint 57.127 (AD-ChatV2-Live-MultiTurn-Context): rehydrate prior
        # conversation so a follow-up send keeps multi-turn context (the 57.126
        # drive-through found turn 2 "its population?" could not resolve "it"→Paris).
        # The injected MessageStore (bound to this session+tenant) self-loads the
        # verbatim Cat-3 ledger; absent (subagent child loops / legacy callers) → []
        # = today's single-turn behavior. system is reconstructed fresh each run
        # (NEVER persisted); prior rows are NOT re-persisted.
        prior_messages: list[Message] = (
            await self._message_store.load() if self._message_store is not None else []
        )
        messages: list[Message] = list(prior_messages)
        if self._system_prompt:
            messages.insert(0, Message(role="system", content=self._system_prompt))
        messages.append(Message(role="user", content=user_input))
        # Persist this send's user prompt immediately (turn 0) so the question is
        # remembered even if the run fails before an answer (mirrors the 57.126
        # message_events user_message persist). NEW only — never system / prior.
        await self._persist_to_ledger([messages[-1]], turn_num=0)

        turn_count = 0
        tokens_used = 0
        # Sprint 57.2 US-1+US-2 bundled: per-run metrics accumulator
        # (closes AD-Cost-Ledger-Token-Split + Provider-Attribution +
        # Cat10-Cat11-LoopMetricsAccumulator). Local var (per-run, not
        # per-instance) so concurrent run() calls don't share state.
        metrics_acc = LoopMetricsAccumulator()

        # Sprint 57.71 (A-4 Tier 1): bind the root span `as root_ctx` so the
        # per-turn TURN spans nest UNDER it (the prior code discarded the yielded
        # child → all spans were flat siblings — the D1 nesting bug). The TURN
        # span (and through it LLM_CALL / TOOL_EXEC) thread root_ctx → turn_ctx
        # so a RecordingTracer can reconstruct LOOP→TURN→operation. Other `ctx`
        # uses (event trace_context, downstream operation calls whose own spans
        # land in Stage 2) are left on the request ctx for this stage.
        #
        # Sprint 57.75 (A-5c Trace tab): each of the 6 span sites also EMITS a
        # SpanStarted (on enter, carrying span_id + parent_span_id + span_type) +
        # SpanEnded (on exit, carrying span_type + loop-measured duration_ms) as
        # SSE LoopEvents so the chat-v2 Inspector Trace tab can render the
        # waterfall live. The SpanEnded sits in a `try/finally` INSIDE the span's
        # `async with` body so every exit path (return / break / continue / raise)
        # emits it — R3 (a max-turns return inside LOOP, a tool-error raise inside
        # TOOL_EXEC, a LoopTerminated return inside TURN all still close their
        # span). The async-generator finally-after-yield is safe here: the SSE
        # driver consumes the generator to completion. duration_ms is
        # loop-measured (time.monotonic), independent of OTel's own span timing —
        # the SSE waterfall is a diagnostic view, not the OTel trace.
        async with self._tracer.start_span(
            name="agent_loop.run",
            category=SpanCategory.ORCHESTRATOR,
            trace_context=ctx,
            attributes={"span_type": "LOOP"},
        ) as root_ctx:
            _root_ctx_t0 = time.monotonic()
            try:
                # LoopStarted stays the FIRST event (public SSE contract:
                # the stream opens with `loop_start`). The diagnostic LOOP
                # SpanStarted trails it by one frame — the span still brackets
                # the whole loop body (SpanEnded fires in this try's finally).
                yield LoopStarted(session_id=session_id, trace_context=ctx)
                yield SpanStarted(
                    span_name="agent_loop.run",
                    span_id=root_ctx.span_id,
                    parent_span_id=root_ctx.parent_span_id or "",
                    span_type="LOOP",
                    trace_context=root_ctx,
                )

                # === Cat 9 input guardrail check (53.3 Day 4 US-7) ============
                # Runs once at loop start (before any LLM call). Per plan §US-7:
                #   guardrail BLOCK/ESCALATE → GuardrailTriggered + audit
                #                              + LoopCompleted(GUARDRAIL_BLOCKED)
                #   tripwire trigger         → TripwireTriggered + audit
                #                              + LoopCompleted(TRIPWIRE)
                # No-op when corresponding deps are None (53.2 baseline).
                async for ev in self._cat9_input_check(
                    user_input=user_input,
                    ctx=ctx,
                    session_id=session_id,
                    messages=messages,
                    turn_count=turn_count,
                ):
                    yield ev
                    if isinstance(ev, LoopCompleted):
                        return

                async for ev in self._run_turns(
                    session_id=session_id,
                    messages=messages,
                    turn_count=turn_count,
                    tokens_used=tokens_used,
                    metrics_acc=metrics_acc,
                    ctx=ctx,
                    root_ctx=root_ctx,
                ):
                    yield ev
            finally:
                yield SpanEnded(
                    span_name="agent_loop.run",
                    span_id=root_ctx.span_id,
                    span_type="LOOP",
                    duration_ms=(time.monotonic() - _root_ctx_t0) * 1000.0,
                    trace_context=root_ctx,
                )

    async def _run_turns(
        self,
        *,
        session_id: UUID,
        messages: list[Message],
        turn_count: int,
        tokens_used: int,
        metrics_acc: LoopMetricsAccumulator,
        ctx: TraceContext,
        root_ctx: TraceContext,
        skip_between_turns_once: bool = False,
        verification_attempts: int = 0,
        verification_escalated: bool = False,
    ) -> AsyncIterator[LoopEvent]:
        """Re-enterable per-turn loop (Sprint 57.89 Slice 1).

        The verbatim per-turn body extracted from run() so a SINGLE source of
        truth drives both run() (now) and resume() (Slice 2). Pure extraction:
        zero behavior change. Operates on the raw per-run locals the caller owns
        (session_id / messages / turn_count / tokens_used / metrics_acc) plus the
        LOOP span ctx (root_ctx) the caller opened, so the per-turn TURN spans
        nest under it. A `return` here ends the generator; the caller's LOOP-span
        try/finally still fires SpanEnded(LOOP) on every exit path.

        Sprint 57.98 A1: `verification_attempts` is the running in-loop
        self-correction count (0 for a fresh run; resume() passes the
        checkpointed value so a pause mid-correction keeps counting — US-3).
        `verif_*` accumulate judge-token usage across attempts (Sprint 57.82)
        to stamp the terminal LoopCompleted.

        Sprint 57.99 A2: `verification_escalated` is the durable "this run already
        ESCALATEd a max-attempts verification failure to a human" flag (False for a
        fresh run; resume() passes the checkpointed value). When True, a subsequent
        max-attempts failure takes the A1 verification_failed terminal instead of a
        2nd escalate — bounding REJECT-with-note to exactly ONE human-coached turn.
        """
        verif_in = 0
        verif_out = 0
        verif_model: str | None = None
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

            # === Cat 1 between-turns injection drain (Sprint 57.101 B1) =
            # Drain the optional message inbox at the loop TOP so a mid-run injected
            # message joins the conversation at THIS turn boundary — it never
            # interrupts an in-flight LLM/tool call (that would be a lie about what
            # the loop can do); an injection during turn N lands at the N→N+1
            # boundary. Each injected message is an INPUT, so it runs the Cat 9 INPUT
            # guardrail — NOT the between-turns gate below, which checks the
            # just-completed turn's OUTPUT (_latest_output_text skips user messages;
            # Sprint 57.101 D-DAY1-1). A non-PASS injection is DROPPED (not appended)
            # + a GuardrailTriggered tells the UI, and the run continues without it
            # (a bad side-instruction must not kill the main task). MessageInjected
            # fires on DRAIN (proof it landed), not on the POST. No inbox → no-op
            # (byte-identical to pre-57.101). The drain runs every iteration (gated
            # only on an inbox being present, NOT on turn_count).
            if self._message_inbox is not None:
                for injected in await self._message_inbox.drain():
                    injected_text = injected.content if isinstance(injected.content, str) else ""
                    if self._guardrail_engine is not None:
                        inj_g = await self._guardrail_engine.check_input(
                            injected_text, trace_context=ctx
                        )
                        if inj_g.action != GuardrailAction.PASS:
                            yield GuardrailTriggered(
                                guardrail_type="input",
                                action=inj_g.action.value,
                                reason=inj_g.reason or "blocked injected message",
                                trace_context=ctx,
                            )
                            continue  # drop the blocked injection; the run continues
                    messages.append(injected)
                    yield MessageInjected(text=injected_text, trace_context=ctx)

            # === Cat 9 between-turns gate (Sprint 57.92, Slice 3 leg 2) =
            # After ≥1 completed turn (turn_count > 0), BEFORE the next LLM call,
            # a between-turns guardrail may ESCALATE → durably pause the loop for
            # human approval of CONTINUING (the 2nd generalized pause point on the
            # _emit_deferred_pause primitive). The seam is the loop TOP (not the
            # mid-turn _cat9_output_check) so a resume continues by making the next
            # turn's LLM call — which has NOT run — with no re-generation.
            # `skip_between_turns_once` (set by a between-turns resume) skips the
            # just-approved boundary for the FIRST re-entered iteration, then is
            # consumed below so subsequent boundaries still gate.
            if turn_count > 0 and not skip_between_turns_once:
                between_turns_terminated = False
                async for ev in self._cat9_between_turns_check(
                    messages=messages,
                    ctx=ctx,
                    turn_count=turn_count,
                    session_id=session_id,
                    verification_attempts=verification_attempts,
                ):
                    yield ev
                    if isinstance(ev, LoopCompleted):
                        between_turns_terminated = True
                if between_turns_terminated:
                    return
            skip_between_turns_once = False

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
                # Sprint 57.71 (A-4 Tier 1, Stage 2): COMPACTION span brackets
                # the compaction check. Opened only when a compactor is injected
                # (gated above) — so a None-compactor turn emits no empty span.
                # compact_if_needed always does real work when present (token
                # counting + threshold eval), so the span is non-empty even on a
                # no-trigger turn. The compactor's own internal tracer stays NoOp
                # (loop is the single trace-tree owner, D8). NESTING: this check
                # runs structurally BEFORE the per-turn TURN span opens (a
                # surgical, no-control-flow-change wrap), so COMPACTION nests
                # under root_ctx (the pre-turn loop-level position) rather than
                # turn_ctx — faithfully reflecting the loop's real structure.
                async with self._tracer.start_span(
                    name="agent_loop.compaction",
                    category=SpanCategory.CONTEXT_MGMT,
                    trace_context=root_ctx,
                    attributes={"span_type": "COMPACTION"},
                ) as compaction_ctx:
                    _compaction_ctx_t0 = time.monotonic()
                    yield SpanStarted(
                        span_name="agent_loop.compaction",
                        span_id=compaction_ctx.span_id,
                        parent_span_id=compaction_ctx.parent_span_id or "",
                        span_type="COMPACTION",
                        trace_context=compaction_ctx,
                    )
                    try:
                        compaction_result = await self._compactor.compact_if_needed(
                            compact_state, trace_context=ctx
                        )
                    finally:
                        yield SpanEnded(
                            span_name="agent_loop.compaction",
                            span_id=compaction_ctx.span_id,
                            span_type="COMPACTION",
                            duration_ms=(time.monotonic() - _compaction_ctx_t0) * 1000.0,
                            trace_context=compaction_ctx,
                        )
                if compaction_result.triggered and compaction_result.compacted_state is not None:
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
                        # Sprint 57.109 (C2): summarize-call usage rides the event
                        # (server-side fields; not on the wire) so the router can
                        # bill the `_compaction` sub_type on the cheap tier.
                        input_tokens=compaction_result.input_tokens,
                        output_tokens=compaction_result.output_tokens,
                        model=compaction_result.model,
                        trace_context=ctx,
                    )

            # === Per-turn marker (Sprint 50.2) ==========================
            # Sprint 57.71 (A-4 Tier 1): TURN span per turn — wraps the
            # genuine per-turn work (post-termination/compaction) so
            # LLM_CALL / TOOL_EXEC nest under it (root_ctx -> turn_ctx ->
            # operation). Opened AFTER the pre-LLM terminators so a final
            # MAX_TURNS / budget exit does not emit an empty TURN span.
            async with self._tracer.start_span(
                name="agent_loop.turn",
                category=SpanCategory.ORCHESTRATOR,
                trace_context=root_ctx,
                attributes={"span_type": "TURN", "turn": turn_count},
            ) as turn_ctx:
                _turn_ctx_t0 = time.monotonic()
                yield SpanStarted(
                    span_name="agent_loop.turn",
                    span_id=turn_ctx.span_id,
                    parent_span_id=turn_ctx.parent_span_id or "",
                    span_type="TURN",
                    trace_context=turn_ctx,
                )
                try:
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
                                # 53.1: real tenant when ctor-injected; else session_id
                                # fallback
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
                        # Sprint 57.71 (A-4 Tier 1, Stage 2): PROMPT_BUILD span
                        # brackets the Cat 5 build() call, nested under turn_ctx.
                        # Opened only inside the `prompt_builder is not None` branch
                        # → the naked-fallback turn (no builder) emits no empty span.
                        # NOTE: any memory-layer injection happens INSIDE build()
                        # (the prompt builder's 5-scope render), so a standalone
                        # loop-level MEMORY_OP span has no clean call boundary here
                        # (memory tools go through tool_executor.execute → already
                        # covered by TOOL_EXEC). MEMORY_OP is therefore N/A at the
                        # loop level this sprint — deferred (plan §9 carryover).
                        # The builder's own internal tracer stays NoOp (loop is the
                        # single trace-tree owner, D8).
                        async with self._tracer.start_span(
                            name="agent_loop.prompt_build",
                            category=SpanCategory.PROMPT_BUILDER,
                            trace_context=turn_ctx,
                            attributes={"span_type": "PROMPT_BUILD"},
                        ) as prompt_ctx:
                            _prompt_ctx_t0 = time.monotonic()
                            yield SpanStarted(
                                span_name="agent_loop.prompt_build",
                                span_id=prompt_ctx.span_id,
                                parent_span_id=prompt_ctx.parent_span_id or "",
                                span_type="PROMPT_BUILD",
                                trace_context=prompt_ctx,
                            )
                            try:
                                artifact = await self._prompt_builder.build(
                                    state=build_state,
                                    tenant_id=self._tenant_id
                                    or session_id,  # 53.1: real tenant when set
                                    # 57.65 (A-1 Tier2): scope the user-layer memory to the
                                    # authenticated user from the request TraceContext.
                                    user_id=ctx.user_id,
                                    tools=self._tool_registry.list(),
                                    trace_context=ctx,
                                )
                            finally:
                                yield SpanEnded(
                                    span_name="agent_loop.prompt_build",
                                    span_id=prompt_ctx.span_id,
                                    span_type="PROMPT_BUILD",
                                    duration_ms=(time.monotonic() - _prompt_ctx_t0) * 1000.0,
                                    trace_context=prompt_ctx,
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
                        # Sprint 57.75 (A-5c Memory tab): emit one
                        # MemoryAccessed per retrieved hint so the chat-v2
                        # Inspector Memory tab shows which memories the
                        # agent read this turn. Sourced from the builder's
                        # layer_metadata["memory_accesses"] (built from the
                        # same hints it injected — no extra search()).
                        # operation="read" (build-time retrieval); write /
                        # evict happen inside memory tools, already under
                        # TOOL_EXEC (plan §9 carryover). echo_demo path has
                        # no prompt_builder → this branch never runs → the
                        # Memory tab shows an honest empty state (D-DAY0-5).
                        # summary is the hint's capped summary (PII-safe).
                        for _acc in artifact.layer_metadata.get("memory_accesses", []):
                            yield MemoryAccessed(
                                layer=_acc["scope"],
                                operation="read",
                                key=_acc["key"],
                                summary=_acc["summary"],
                                time_scale=_acc["time_scale"],
                                trace_context=turn_ctx,
                            )

                    # === LLM call ===============================================
                    model_name = self._chat_client.model_info().model_name
                    yield LLMRequested(
                        model=model_name,
                        tokens_in=0,  # Phase 52.1 wires count_tokens()
                        trace_context=ctx,
                    )
                    # Sprint 57.71 (A-4 Tier 1): LLM_CALL span brackets the
                    # chat() call (latency from span timing; ERROR status +
                    # record_exception fire automatically when an exception
                    # propagates through the tracer's `async with` body — see
                    # OTelTracer._span_cm). Token attributes are written into
                    # `llm_attrs` AFTER the response (this ABC has no dynamic
                    # set-attribute; the dict is shared with the tracer so a
                    # recording tracer that keeps it by reference observes the
                    # post-response tokens, and OTel sees model/span_type at
                    # open — full per-attribute OTel token export awaits Tier 2).
                    # Cost (cost_usd) is intentionally NOT computed here: it
                    # stays a Stage-2 carry to avoid adapter-pricing coupling +
                    # double-counting with the router cost ledger (span attrs
                    # never feed the ledger). The CancelledError path keeps the
                    # 57.x clean-shutdown contract (LoopCompleted + re-raise).
                    llm_attrs: dict[str, Any] = {
                        "span_type": "LLM_CALL",
                        "model": model_name,
                    }
                    async with self._tracer.start_span(
                        name="agent_loop.llm_call",
                        category=SpanCategory.ORCHESTRATOR,
                        trace_context=turn_ctx,
                        attributes=llm_attrs,
                    ) as llm_ctx:
                        _llm_ctx_t0 = time.monotonic()
                        yield SpanStarted(
                            span_name="agent_loop.llm_call",
                            span_id=llm_ctx.span_id,
                            parent_span_id=llm_ctx.parent_span_id or "",
                            span_type="LLM_CALL",
                            trace_context=llm_ctx,
                        )
                        try:
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
                            # Token attrs known only post-response → write into the
                            # shared attrs dict before the span closes (span-only;
                            # never to the cost ledger — D8 double-count guard).
                            if response.usage is not None:
                                llm_attrs["prompt_tokens"] = response.usage.prompt_tokens
                                llm_attrs["completion_tokens"] = response.usage.completion_tokens
                                llm_attrs["cached_input_tokens"] = (
                                    response.usage.cached_input_tokens
                                )
                                llm_attrs["total_tokens"] = response.usage.total_tokens
                        finally:
                            yield SpanEnded(
                                span_name="agent_loop.llm_call",
                                span_id=llm_ctx.span_id,
                                span_type="LLM_CALL",
                                duration_ms=(time.monotonic() - _llm_ctx_t0) * 1000.0,
                                trace_context=llm_ctx,
                            )

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
                    _cached_input_tokens = (
                        response.usage.cached_input_tokens if response.usage else 0
                    )
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

                    # === Cat 9 output-guardrail ESCALATE pre-delivery pause ====
                    # (Sprint 57.93, 地基 A Slice 3 output-guardrail leg). For a
                    # FINAL answer, run the OUTPUT chain BEFORE LLMResponded (the
                    # frontend renders the AnswerBlock from llm_response, so a pause
                    # AFTER it would be a Potemkin). On ESCALATE + the full
                    # deferred-HITL wiring, pause durably for human approval to
                    # DELIVER the answer; resume() re-emits the held answer (no LLM
                    # re-call) on APPROVED. Gated on is_final_answer + the wiring so
                    # non-HITL / non-final turns are byte-unchanged (LLMResponded +
                    # the per-response _cat9_output_check below still run as before).
                    if (
                        (
                            should_terminate_by_stop_reason(response)
                            or classify_output(response) == OutputType.FINAL
                        )
                        and self._guardrail_engine is not None
                        and self._hitl_manager is not None
                        and self._hitl_deferred
                        and self._checkpointer is not None
                        and self._reducer is not None
                    ):
                        output_pause_terminated = False
                        response_snapshot: dict[str, Any] = {
                            "answer_text": parsed.text,
                            "input_tokens": _input_tokens,
                            "output_tokens": _output_tokens,
                            "cached_input_tokens": _cached_input_tokens,
                            "provider": _provider,
                            "model": response.model,
                            "cache_hit_rate": metrics_acc.cache_hit_rate,
                            "total_tokens": tokens_used,
                        }
                        async for ev in self._cat9_output_escalate_pause(
                            output_text=parsed.text,
                            response_snapshot=response_snapshot,
                            ctx=ctx,
                            turn_count=turn_count,
                            session_id=session_id,
                            messages=messages,
                            verification_attempts=verification_attempts,
                        ):
                            yield ev
                            if isinstance(ev, LoopCompleted):
                                output_pause_terminated = True
                        if output_pause_terminated:
                            return

                    # 50.2: LLMResponded carries the canonical (content, tool_calls,
                    # thinking) tuple
                    # per 02-architecture-design.md §SSE llm_response schema. Thinking event
                    # is kept
                    # for 50.1 test backward compatibility but no longer the SSE-canonical
                    # form.
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

                    # === Cat 10 in-loop verification gate (Sprint 57.98 A1) =====
                    # Runs AFTER the Cat 9 output guardrail (locked order
                    # guardrail->verification) and BEFORE the stop_reason / FINAL
                    # terminator. For a FINAL candidate answer: verify it; on PASS
                    # fall through to deliver; on FAIL with budget left, append the
                    # failed answer + a correction-feedback Message and `continue`
                    # (turn_count++) — the NEXT turn re-answers in the SAME loop
                    # (the in-loop critique; prefix-stable for the Cat 4 cache); on
                    # FAIL at the budget, emit verification_failed. Gated on the
                    # registry so a non-verified run (echo/demo, or
                    # chat_verification_mode off) is byte-unchanged. Replaces the
                    # retired run_with_verification wrapper; resume() covers the
                    # resume path automatically (shared _run_turns). Judge tokens
                    # accumulate (verif_*) to stamp the terminal LoopCompleted (57.82).
                    if (
                        (
                            should_terminate_by_stop_reason(response)
                            or classify_output(response) == OutputType.FINAL
                        )
                        and self._verifier_registry is not None
                        and len(self._verifier_registry) > 0
                    ):
                        verdict = await self._cat10_verify_gate(
                            output_text=parsed.text,
                            messages=messages,
                            turn_count=turn_count,
                            session_id=session_id,
                            attempt=verification_attempts,
                            ctx=ctx,
                        )
                        for vev in verdict.events:
                            yield vev
                        verif_in += verdict.verif_in
                        verif_out += verdict.verif_out
                        if verdict.verif_model:
                            verif_model = verdict.verif_model
                        if verdict.outcome == "correct":
                            # In-loop critique: append the failed answer + the
                            # correction feedback, then re-answer as the NEXT turn.
                            messages.append(Message(role="assistant", content=parsed.text))
                            messages.append(
                                Message(role="user", content=verdict.correction_block or "")
                            )
                            verification_attempts += 1
                            turn_count += 1
                            continue
                        if verdict.outcome == "failed_max":
                            # 57.99 A2: conditionally ESCALATE to a human pause
                            # instead of the A1 verification_failed terminal, when
                            # the toggle is ON, this run hasn't already escalated
                            # (the bound — a REJECT-with-note re-enters with
                            # verification_escalated=True so a 2nd failure takes the
                            # A1 terminal below: exactly one human-coached turn), and
                            # the full HITL deferred-pause wiring is present (no
                            # resumable pause possible without it → fall back to A1).
                            if (
                                self._verification_escalate_on_max
                                and not verification_escalated
                                and self._hitl_manager is not None
                                and self._hitl_deferred
                                and self._checkpointer is not None
                                and self._reducer is not None
                            ):
                                response_snapshot = {
                                    # The held failed answer — resume() APPROVE
                                    # delivers it verbatim via _replay_approved_output
                                    # (human overrides the judge; the output-pause
                                    # snapshot field set so the same replay path works).
                                    "answer_text": parsed.text,
                                    "provider": metrics_acc.last_provider,
                                    "model": metrics_acc.last_model,
                                    "input_tokens": metrics_acc.cumulative_input_tokens,
                                    "output_tokens": metrics_acc.cumulative_output_tokens,
                                    "cached_input_tokens": (
                                        metrics_acc.cumulative_cached_input_tokens
                                    ),
                                    "cache_hit_rate": metrics_acc.cache_hit_rate,
                                    "total_tokens": tokens_used,
                                }
                                async for ev in self._cat10_verification_escalate_pause(
                                    answer_text=parsed.text,
                                    response_snapshot=response_snapshot,
                                    verdict=verdict,
                                    ctx=ctx,
                                    session_id=session_id,
                                    messages=messages,
                                    turn_count=turn_count,
                                    verification_attempts=verification_attempts,
                                ):
                                    yield ev
                                return
                            yield LoopCompleted(
                                stop_reason=VERIFICATION_FAILED_STOP_REASON,
                                total_turns=turn_count,
                                total_tokens=tokens_used,
                                input_tokens=metrics_acc.cumulative_input_tokens,
                                output_tokens=metrics_acc.cumulative_output_tokens,
                                provider=metrics_acc.last_provider,
                                model=metrics_acc.last_model,
                                cached_input_tokens=metrics_acc.cumulative_cached_input_tokens,
                                cache_hit_rate=metrics_acc.cache_hit_rate,
                                verification_input_tokens=verif_in,
                                verification_output_tokens=verif_out,
                                verification_model=verif_model,
                                trace_context=ctx,
                            )
                            return
                        # outcome == "pass" → fall through to the terminator below.

                    # === stop_reason terminator =================================
                    if should_terminate_by_stop_reason(response):
                        # Sprint 57.127: persist the final answer to the ledger
                        # (it is NOT in `messages` — the loop ends without it) so a
                        # follow-up send rehydrates it. Covers run() + resume().
                        await self._persist_to_ledger(
                            [Message(role="assistant", content=parsed.text)],
                            turn_num=turn_count,
                        )
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
                            # Sprint 57.98 A1: stamp accumulated judge tokens (0 on a
                            # non-verified run) so the cost ledger attributes them.
                            verification_input_tokens=verif_in,
                            verification_output_tokens=verif_out,
                            verification_model=verif_model,
                            trace_context=ctx,
                        )
                        return

                    # === Dispatch on OutputType =================================
                    output_type = classify_output(response)

                    if output_type == OutputType.FINAL:
                        # Sprint 57.127: persist the final answer to the ledger
                        # (the FINAL branch ends without appending it to `messages`)
                        # so a follow-up send rehydrates it. Covers run() + resume().
                        await self._persist_to_ledger(
                            [Message(role="assistant", content=parsed.text)],
                            turn_num=turn_count,
                        )
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
                            # Sprint 57.98 A1: stamp accumulated judge tokens (0 on a
                            # non-verified run) so the cost ledger attributes them.
                            verification_input_tokens=verif_in,
                            verification_output_tokens=verif_out,
                            verification_model=verif_model,
                            trace_context=ctx,
                        )
                        return

                    if output_type == OutputType.HANDOFF:
                        # Cat 11 HANDOFF (Sprint 57.68 A-3b): control transfer to a
                        # target agent. The "handoff" tool_call carries target_agent
                        # + reason in its arguments dict (classifier matches
                        # tc.name == HANDOFF_TOOL_NAME). The loop only terminates
                        # with a `handoff` stop_reason carrying the parsed intent;
                        # booting the child session is the platform layer's job
                        # (router post-loop hook) — server-side-first layering keeps
                        # DB / session knowledge out of the loop.
                        handoff_tc = next(
                            (tc for tc in parsed.tool_calls if tc.name == HANDOFF_TOOL_NAME),
                            None,
                        )
                        handoff_args = handoff_tc.arguments if handoff_tc is not None else {}
                        yield LoopCompleted(
                            stop_reason=TerminationReason.HANDOFF.value,
                            total_turns=turn_count,
                            handoff_target=str(handoff_args.get("target_agent", "")),
                            handoff_reason=str(handoff_args.get("reason", "")),
                            # Sprint 57.69 A-3b slice 2: shallow snapshot of the
                            # in-memory conversation so the platform layer can seed
                            # the booted child with the prior context (carried only;
                            # not on the loop_end wire schema).
                            handoff_context=list(messages),
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
                        async for ev in self._cat9_tool_check(
                            tc=tc,
                            ctx=ctx,
                            turn_count=turn_count,
                            session_id=session_id,
                            messages=messages,
                            verification_attempts=verification_attempts,
                        ):
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
                                # Sprint 57.71 (A-4 Tier 1): TOOL_EXEC span per
                                # execute() call, nested under turn_ctx. Latency
                                # comes from span timing; on a raised exception
                                # the tracer sets ERROR status + record_exception
                                # automatically as it propagates through the
                                # `async with` body (caught by the surrounding
                                # except clauses afterwards). Parallel / multiple
                                # tool calls in one turn are sibling TOOL_EXEC
                                # spans under the same TURN. The span is the loop's
                                # own (the executor's internal tracer stays NoOp —
                                # loop is the single trace-tree owner, D8 no double
                                # spans).
                                async with self._tracer.start_span(
                                    name=f"agent_loop.tool.{tc.name}",
                                    category=SpanCategory.TOOLS,
                                    trace_context=turn_ctx,
                                    attributes={"span_type": "TOOL_EXEC", "tool": tc.name},
                                ) as tool_ctx:
                                    _tool_ctx_t0 = time.monotonic()
                                    yield SpanStarted(
                                        span_name=f"agent_loop.tool.{tc.name}",
                                        span_id=tool_ctx.span_id,
                                        parent_span_id=tool_ctx.parent_span_id or "",
                                        span_type="TOOL_EXEC",
                                        trace_context=tool_ctx,
                                    )
                                    try:
                                        result = await self._tool_executor.execute(
                                            tc, trace_context=ctx, context=exec_ctx
                                        )
                                    finally:
                                        yield SpanEnded(
                                            span_name=f"agent_loop.tool.{tc.name}",
                                            span_id=tool_ctx.span_id,
                                            span_type="TOOL_EXEC",
                                            duration_ms=(time.monotonic() - _tool_ctx_t0) * 1000.0,
                                            trace_context=tool_ctx,
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
                                # Sprint 55.6 D7 fix: pass real attempt_num (was hardcoded
                                # =1).
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
                                    # Opt-out path: no Cat 8 deps → preserve 53.1 raise
                                    # behavior
                                    raise
                                if terminate:
                                    yield LoopTerminated(
                                        reason=(
                                            term_reason.value if term_reason is not None else ""
                                        ),
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
                                # Note: ToolResult is now imported at module top (53.3 Day
                                # 4).
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
                                        reason=(
                                            term_reason.value if term_reason is not None else ""
                                        ),
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
                finally:
                    yield SpanEnded(
                        span_name="agent_loop.turn",
                        span_id=turn_ctx.span_id,
                        span_type="TURN",
                        duration_ms=(time.monotonic() - _turn_ctx_t0) * 1000.0,
                        trace_context=turn_ctx,
                    )

            turn_count += 1
            # loop continues to next while iteration

    async def resume(
        self,
        *,
        state: LoopState,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """Resume a loop that paused on a deferred HITL approval (57.88 US-3).

        Replaces the 50.1 abstract stub. The caller (platform ResumeService)
        rebuilds `state` from a paused checkpoint: `state.durable.metadata
        ["pending_approval"]` carries the pending tool call + approval_request_id
        + turn (persisted by the deferred ESCALATE branch, see
        `_cat9_hitl_branch`), and `state.transient.messages` is rehydrated by
        ResumeService from `state.durable.metadata["resume_messages"]` (decision
        B: the US-3 checkpointer does NOT persist the buffer and this codebase
        has no `messages` table, so the deferred-pause checkpoint self-contains
        the buffer in its metadata — a SPIKE shortcut, see _emit_state_checkpoint
        + messages_from_metadata; production → `messages` table, plan §9).

        Flow:
            1. Read pending_approval; if absent → LoopCompleted(ERROR).
            2. Non-blocking `HITLManager.get_decision(approval_request_id)`.
                - undecided / no manager → LoopCompleted(ERROR) (caller should
                  have gated on decided; defensive).
                - APPROVED → branch on pending_approval["kind"] (Sprint 57.91):
                    tool-kind  → execute the pending tool → append the observation
                      as a tool message → drive the shared `_run_turns` to end_turn.
                    input-kind → no tool; the approved input proceeds to the first
                      LLM turn via the shared `_run_turns` drive.
                    output-kind (57.93) / verification-kind (57.99 A2) → DELIVER the
                      held answer via _replay_approved_output (TERMINAL, no LLM
                      re-call); a verification APPROVE = the human overriding the
                      verifier.
                - REJECTED / ESCALATED → for input/between_turns/output/tool kinds:
                  GuardrailTriggered(block) + LoopCompleted(GUARDRAIL_BLOCKED);
                  nothing is executed. EXCEPTION — verification-kind REJECT (57.99
                  A2) re-injects the reviewer's note as a correction and drives
                  EXACTLY ONE human-coached turn (verification_attempts forced to
                  max + durable verification_escalated=True bind a 2nd failure to
                  the A1 terminal — no second pause).

        Sprint 57.90 Slice 2 (closes AD-Resume-Continuation-Fidelity): after
        executing the pre-approved pending tool ONCE (outside the loop — already
        HITL-APPROVED, so it must NOT re-enter `_cat9_hitl_branch`; the locked
        analysis-note §6.1 option (b)), resume() drives the SAME `_run_turns`
        run() uses (inside a fresh metrics_acc + LOOP span). The resumed
        continuation therefore gains Cat 4 compaction / Cat 7 checkpoints / Cat 8
        retry / Cat 9 per-tool deferred-pause + output guardrail / Cat 12 spans /
        HANDOFF, and a 2nd ESCALATE in the continuation checkpoints + pauses AGAIN
        (multi-pause-per-run). The prior `_resume_continuation` reduced copy is
        deleted — single source of truth for the per-turn loop.
        """
        ctx = trace_context or TraceContext.create_root()
        session_id = state.durable.session_id
        messages: list[Message] = list(state.transient.messages)
        turn_count = state.transient.current_turn
        tokens_used = state.transient.token_usage_so_far
        # Sprint 57.98 A1 (US-3): rehydrate the in-loop self-correction count so a
        # pause that landed mid-correction continues the SAME correction budget
        # rather than resetting it. The pause checkpoint stored it under
        # metadata["verification_attempts"] (D-DAY2-1: rides metadata, not a
        # DurableState scalar field — the checkpoint (de)serializer round-trips
        # metadata verbatim, so no serializer / migration change). A fresh run()
        # never writes it → absent → 0.
        verification_attempts = int(state.durable.metadata.get("verification_attempts", 0))
        # Sprint 57.99 A2 (US-5): rehydrate the durable escalate flag. A
        # verification-kind escalate pause persisted metadata["verification_
        # escalated"]=True (mirrors verification_attempts above — rides metadata,
        # no migration). A REJECT continuation re-drives _run_turns with this True
        # so a 2nd failed_max takes the A1 terminal instead of re-pausing (the
        # bound: exactly one human-coached turn). Absent on every other pause kind
        # and on a fresh run() → False → byte-identical to A1.
        verification_escalated = bool(state.durable.metadata.get("verification_escalated", False))

        yield LoopStarted(session_id=session_id, trace_context=ctx)

        pending = state.durable.metadata.get("pending_approval")
        if not isinstance(pending, dict):
            # No resumable approval on this checkpoint — defensive.
            yield LoopCompleted(
                stop_reason=TerminationReason.ERROR.value,
                total_turns=turn_count,
                total_tokens=tokens_used,
                trace_context=ctx,
            )
            return

        request_id_raw = pending.get("approval_request_id")
        request_id = UUID(str(request_id_raw)) if request_id_raw is not None else None

        # --- Read the recorded decision (non-blocking) -----------------------
        decision: ApprovalDecision | None = None
        if self._hitl_manager is not None and request_id is not None:
            decision = await self._hitl_manager.get_decision(request_id, trace_context=ctx)

        if decision is None:
            # Undecided (caller should have gated) or no manager → fail closed.
            yield LoopCompleted(
                stop_reason=TerminationReason.ERROR.value,
                total_turns=turn_count,
                total_tokens=tokens_used,
                trace_context=ctx,
            )
            return

        yield ApprovalReceived(
            approval_request_id=request_id,
            decision=decision.decision.value,
            trace_context=ctx,
        )

        # Sprint 57.91 (Slice 3 leg 1): branch on the pause kind. An input-kind
        # pause (no tool_call) was an input-guardrail ESCALATE before the first
        # LLM call — APPROVED resumes by continuing to the first LLM turn (NO tool
        # exec); the approved input proceeds exactly as it would have un-paused. A
        # tool-kind pause (the 57.88 path) execs the pre-approved pending tool
        # once, OUTSIDE the loop (already HITL-APPROVED → no re-escalation, the
        # locked analysis-note §6.1 option (b)). Both kinds then drive the SHARED
        # _run_turns. Default "tool" preserves any in-flight 57.88-era checkpoints.
        kind = str(pending.get("kind", "tool"))
        # Sprint 57.92 (Slice 3 leg 2): a between-turns resume continues to the
        # next turn with the gate skipped once (set in the between_turns branch).
        skip_between_turns_once = False
        if kind == "input":
            if decision.decision != DecisionType.APPROVED:
                await self._audit_log_safe(
                    event_type=f"resume.input.{decision.decision.value.lower()}",
                    content={"request_id": str(request_id)},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="input",
                    action="block",
                    reason=f"approval {decision.decision.value.lower()}: "
                    f"{decision.reason or 'no reason'}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=turn_count,
                    total_tokens=tokens_used,
                    trace_context=ctx,
                )
                return
            # APPROVED → no tool to execute; the approved input proceeds to the
            # first LLM turn via the shared _run_turns drive below.
            await self._audit_log_safe(
                event_type="resume.input.approved",
                content={"request_id": str(request_id)},
                ctx=ctx,
            )
        elif kind == "between_turns":
            # Sprint 57.92 (Slice 3 leg 2): a between-turns pause (no tool_call) was
            # a between-turns-guardrail ESCALATE at the loop top. APPROVED resumes by
            # continuing to the next turn's LLM call (NO tool exec), with the gate
            # skipped once so the just-approved boundary does not re-escalate.
            if decision.decision != DecisionType.APPROVED:
                await self._audit_log_safe(
                    event_type=f"resume.between_turns.{decision.decision.value.lower()}",
                    content={"request_id": str(request_id)},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="between_turns",
                    action="block",
                    reason=f"approval {decision.decision.value.lower()}: "
                    f"{decision.reason or 'no reason'}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=turn_count,
                    total_tokens=tokens_used,
                    trace_context=ctx,
                )
                return
            await self._audit_log_safe(
                event_type="resume.between_turns.approved",
                content={"request_id": str(request_id)},
                ctx=ctx,
            )
            skip_between_turns_once = True
        elif kind == "output":
            # Sprint 57.93 (Slice 3 output-guardrail leg): an output-kind pause (no
            # tool_call) was an output-guardrail ESCALATE on a FINAL answer, held
            # BEFORE LLMResponded. This branch is TERMINAL — it re-emits (APPROVED)
            # or withholds (REJECTED) the held answer and RETURNS before the shared
            # _run_turns drive below (the turn already produced its terminal answer;
            # there is nothing more to run, and re-driving would re-call the LLM).
            snap_raw = pending.get("response_snapshot", {})
            snap: dict[str, Any] = snap_raw if isinstance(snap_raw, dict) else {}
            if decision.decision != DecisionType.APPROVED:
                await self._audit_log_safe(
                    event_type=f"resume.output.{decision.decision.value.lower()}",
                    content={"request_id": str(request_id)},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="output",
                    action="block",
                    reason=f"approval {decision.decision.value.lower()}: "
                    f"{decision.reason or 'no reason'}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=turn_count,
                    total_tokens=tokens_used,
                    trace_context=ctx,
                )
                return
            # APPROVED → deliver the held answer (no LLM re-call, no further turns).
            await self._audit_log_safe(
                event_type="resume.output.approved",
                content={"request_id": str(request_id)},
                ctx=ctx,
            )
            async for ev in self._replay_approved_output(
                answer_text=str(snap.get("answer_text", "")),
                snap=snap,
                turn_count=turn_count,
                ctx=ctx,
            ):
                yield ev
            return
        elif kind == "verification":
            # Sprint 57.99 A2 (US-3/US-4): a verification-kind pause held a FINAL
            # answer that the in-loop Cat 10 self-correction (A1) exhausted
            # (failed_max). Two human outcomes:
            #   APPROVED → the human OVERRIDES the verifier → DELIVER the held
            #     failed answer verbatim. TERMINAL replay (no LLM re-call), reusing
            #     the 57.93 output-pause _replay_approved_output (the escalate-pause
            #     snapshot set the same answer_text/provider/model/token fields).
            #   REJECTED → re-inject the reviewer's note as a correction message and
            #     run EXACTLY ONE human-coached turn (falls through to the shared
            #     _run_turns drive below). The bound: verification_attempts is forced
            #     to max + the durable verification_escalated flag (rehydrated above)
            #     is True, so if the coached turn's answer fails verification AGAIN
            #     the swap-point guard `not verification_escalated` is False → the A1
            #     verification_failed terminal fires (no second pause).
            vsnap_raw = pending.get("response_snapshot", {})
            vsnap: dict[str, Any] = vsnap_raw if isinstance(vsnap_raw, dict) else {}
            if decision.decision == DecisionType.APPROVED:
                await self._audit_log_safe(
                    event_type="resume.verification.approved",
                    content={"request_id": str(request_id)},
                    ctx=ctx,
                )
                async for ev in self._replay_approved_output(
                    answer_text=str(vsnap.get("answer_text", "")),
                    snap=vsnap,
                    turn_count=turn_count,
                    ctx=ctx,
                ):
                    yield ev
                return
            # REJECTED / ESCALATED → coach one more turn, then bind to A1 terminal.
            await self._audit_log_safe(
                event_type="resume.verification.rejected",
                content={"request_id": str(request_id)},
                ctx=ctx,
            )
            messages.append(
                Message(
                    role="user",
                    content=(
                        f"[Verification rejected by reviewer: "
                        f"{decision.reason or 'no reason'}. Please revise the answer.]"
                    ),
                )
            )
            verification_attempts = self._max_correction_attempts
            verification_escalated = True
        else:
            tc_data = pending.get("tool_call", {})
            pending_tc = ToolCall(
                id=str(tc_data.get("tool_call_id", "")),
                name=str(tc_data.get("name", "")),
                arguments=dict(tc_data.get("arguments", {})),
            )
            if decision.decision != DecisionType.APPROVED:
                # REJECTED / ESCALATED → block the pending tool; terminate.
                await self._audit_log_safe(
                    event_type=f"resume.approval.{decision.decision.value.lower()}",
                    content={"tool": pending_tc.name, "request_id": str(request_id)},
                    ctx=ctx,
                )
                yield GuardrailTriggered(
                    guardrail_type="tool",
                    action="block",
                    reason=f"approval {decision.decision.value.lower()}: "
                    f"{decision.reason or 'no reason'}",
                    trace_context=ctx,
                )
                yield LoopCompleted(
                    stop_reason=TerminationReason.GUARDRAIL_BLOCKED.value,
                    total_turns=turn_count,
                    total_tokens=tokens_used,
                    trace_context=ctx,
                )
                return

            # --- APPROVED → execute the pending tool, then continue ----------
            await self._audit_log_safe(
                event_type="resume.approval.approved",
                content={"tool": pending_tc.name, "request_id": str(request_id)},
                ctx=ctx,
            )
            yield ToolCallRequested(
                tool_call_id=pending_tc.id,
                tool_name=pending_tc.name,
                arguments=pending_tc.arguments,
                trace_context=ctx,
            )
            exec_ctx = ExecutionContext(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                session_id=ctx.session_id or session_id,
            )
            result = await self._tool_executor.execute(
                pending_tc, trace_context=ctx, context=exec_ctx
            )
            tool_content = self._tool_result_to_text(result.content)
            if result.success:
                yield ToolCallExecuted(
                    tool_call_id=pending_tc.id,
                    tool_name=pending_tc.name,
                    duration_ms=result.duration_ms or 0.0,
                    result_content=tool_content,
                    trace_context=ctx,
                )
            else:
                yield ToolCallFailed(
                    tool_call_id=pending_tc.id,
                    tool_name=pending_tc.name,
                    error=result.error or "unknown tool error",
                    trace_context=ctx,
                )
            messages.append(Message(role="tool", content=tool_content, tool_call_id=pending_tc.id))

        # --- Drive the SHARED re-enterable loop (Sprint 57.90 Slice 2) -------
        # Per kind, the approval-specific prep is done above: a tool-kind pause
        # executed its pre-approved pending tool OUTSIDE the loop (locked
        # analysis-note §6.1 option (b); its observation is now in `messages`) so
        # it does NOT re-enter `_cat9_hitl_branch` and cannot re-escalate; an
        # input-kind pause has no tool to run (the approved input just continues
        # to the first LLM turn). Both now drive the SAME `_run_turns` run() uses, so
        # the resumed continuation gains Cat 4 compaction / Cat 7 checkpoints /
        # Cat 8 retry / Cat 9 per-tool deferred-pause + output guardrail / Cat 12
        # spans / HANDOFF — and a 2nd ESCALATE in the continuation checkpoints +
        # pauses AGAIN (multi-pause-per-run) because `_run_turns` carries the same
        # `_cat9_hitl_branch` deferred branch. A fresh `metrics_acc` is built (the
        # continuation's per-run metrics start clean, like a fresh run()), and a
        # LOOP span is opened so the continuation TURN spans nest under it (mirror
        # run()'s `start_span` + SpanStarted/SpanEnded bracket; the SpanEnded fires
        # in `finally` on every exit path, incl. a 2nd-pause return).
        metrics_acc = LoopMetricsAccumulator()
        async with self._tracer.start_span(
            name="agent_loop.run",
            category=SpanCategory.ORCHESTRATOR,
            trace_context=ctx,
            attributes={"span_type": "LOOP"},
        ) as root_ctx:
            _root_ctx_t0 = time.monotonic()
            try:
                yield SpanStarted(
                    span_name="agent_loop.run",
                    span_id=root_ctx.span_id,
                    parent_span_id=root_ctx.parent_span_id or "",
                    span_type="LOOP",
                    trace_context=root_ctx,
                )
                async for ev in self._run_turns(
                    session_id=session_id,
                    messages=messages,
                    turn_count=turn_count,
                    tokens_used=tokens_used,
                    metrics_acc=metrics_acc,
                    ctx=ctx,
                    root_ctx=root_ctx,
                    skip_between_turns_once=skip_between_turns_once,
                    verification_attempts=verification_attempts,
                    verification_escalated=verification_escalated,
                ):
                    yield ev
            finally:
                yield SpanEnded(
                    span_name="agent_loop.run",
                    span_id=root_ctx.span_id,
                    span_type="LOOP",
                    duration_ms=(time.monotonic() - _root_ctx_t0) * 1000.0,
                    trace_context=root_ctx,
                )

    async def _replay_approved_output(
        self,
        *,
        answer_text: str,
        snap: dict[str, Any],
        turn_count: int,
        ctx: TraceContext,
    ) -> AsyncIterator[LoopEvent]:
        """Re-emit a held final answer after output-pause APPROVAL (Sprint 57.93).

        An output-kind pause held the FINAL answer BEFORE LLMResponded; on APPROVED
        resume() calls this to DELIVER it: re-emit the withheld LLMResponded (so the
        UI now renders the AnswerBlock) + Thinking + LoopCompleted(END_TURN), carrying
        the per-call token/provider metrics from the checkpoint snapshot so the cost
        ledger is written at resume (the paused run never emitted END_TURN). NO LLM
        re-call, NO further turns — the turn already produced its terminal answer; this
        only replays it. Spike simplification: no fresh LOOP span over the single
        re-emit (the resumed END_TURN is not nested under a new trace span).
        """
        # Snapshot values come from JSONB (Any); default to type-correct zeros so
        # the strict event field types (non-Optional str/int/float) hold.
        provider = str(snap.get("provider", ""))
        model = str(snap.get("model", ""))
        input_tokens = int(snap.get("input_tokens", 0))
        output_tokens = int(snap.get("output_tokens", 0))
        cached_input_tokens = int(snap.get("cached_input_tokens", 0))
        cache_hit_rate = float(snap.get("cache_hit_rate", 0.0))
        total_tokens = int(snap.get("total_tokens", 0))
        yield LLMResponded(
            content=answer_text,
            tool_calls=(),
            thinking=None,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            trace_context=ctx,
        )
        yield Thinking(text=answer_text, trace_context=ctx)
        yield LoopCompleted(
            stop_reason=TerminationReason.END_TURN.value,
            total_turns=turn_count,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model=model,
            cached_input_tokens=cached_input_tokens,
            cache_hit_rate=cache_hit_rate,
            trace_context=ctx,
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
        pending_approval: dict[str, Any] | None = None,
        verification_attempts: int = 0,
        verification_escalated: bool = False,
    ) -> StateCheckpointed | None:
        """Build LoopState from loop locals, reducer.merge → checkpointer.save.

        Returns StateCheckpointed event with DB chain version (caller yields).
        Returns None if reducer/checkpointer/tenant_id not all configured
        (i.e., 51.x backward-compat caller path). Errors are NOT swallowed;
        the loop should fail loud rather than silently miss a checkpoint.

        57.88 US-2: when ``pending_approval`` is provided (HITL deferred pause),
        it is stored in ``DurableState.metadata["pending_approval"]`` so the
        existing checkpointer JSONB (de)serializer round-trips it WITHOUT a
        migration or a Checkpointer-signature change (the metadata dict already
        persists per _serialize_state_for_db). resume() reads it back.

        57.88 US-2 (decision B): the pause checkpoint ALSO stores the current
        conversation buffer under ``metadata["resume_messages"]`` (serialized via
        _message_to_dict). The US-3 checkpointer split drops the transient
        messages buffer, and this codebase has no `messages` table — so the
        deferred-pause path self-contains the buffer in the checkpoint metadata
        for resume() / ResumeService to rehydrate. This is a SPIKE shortcut;
        production should use a `messages` table / bounded summary (plan §9
        checkpoint-bloat open question). Only the pause case (pending_approval set)
        pays this cost; ordinary post_llm / post_tool checkpoints do NOT store
        messages (metadata stays empty → no size regression on the happy path).
        """
        if self._reducer is None or self._checkpointer is None or self._tenant_id is None:
            return None

        # Build the metadata payload. Only the deferred-pause path (pending_approval
        # set) carries the resumable extras (pending tool call + message buffer);
        # ordinary checkpoints keep metadata empty to avoid bloat.
        metadata: dict[str, Any] = {}
        if pending_approval is not None:
            metadata["pending_approval"] = pending_approval
            metadata["resume_messages"] = [_message_to_dict(m) for m in messages]
        # Sprint 57.98 A1 (US-3): the in-loop self-correction count rides the
        # checkpoint metadata (mirrors the 57.88 pending_approval pattern — the
        # JSONB (de)serializer already round-trips `metadata` verbatim, so no
        # DurableState scalar field / serializer allowlist / migration change is
        # needed; D-DAY2-1). Stored only when > 0 so ordinary checkpoints stay
        # empty (no happy-path size regression). resume() reads it back so a
        # pause that lands mid-correction keeps the correction budget instead of
        # resetting it (a fresh run() never sets it → starts at 0).
        if verification_attempts > 0:
            metadata["verification_attempts"] = verification_attempts
        # Sprint 57.99 A2 (US-5): the durable "this run already escalated a
        # max-attempts verification failure to a human" flag rides the same
        # checkpoint metadata (same precedent as verification_attempts — no
        # serializer/migration change). resume() reads it back so a REJECT-with-note
        # continuation re-enters _run_turns with verification_escalated=True, making
        # a 2nd max-attempts failure take the A1 verification_failed terminal (the
        # bound: exactly one human-coached turn). Stored only when True (happy-path
        # checkpoints stay empty).
        if verification_escalated:
            metadata["verification_escalated"] = True

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
                metadata=metadata,
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
