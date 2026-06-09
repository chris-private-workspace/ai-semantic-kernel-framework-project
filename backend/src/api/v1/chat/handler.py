"""
File: backend/src/api/v1/chat/handler.py
Purpose: Builders that wire AgentLoopImpl with provider + tools by ChatMode.
Category: api/v1/chat
Scope: Phase 50 / Sprint 50.2 (Day 1.4)

Description:
    Handler factories return a fully-wired AgentLoopImpl instance ready to be
    `run()` by the router. Each factory selects the ChatClient adapter
    appropriate for the requested mode:

    - `build_echo_demo_handler()` — MockChatClient with a 2-step scripted
      response: turn 1 calls echo_tool(text=<message>), turn 2 returns the
      echoed text + END_TURN. No env requirements; works offline.

    - `build_real_llm_handler()` — AzureOpenAIAdapter; requires
      AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY + AZURE_OPENAI_DEPLOYMENT_NAME
      env vars (validated at build time, NOT inside loop). System prompt
      instructs the model to use echo_tool for Phase 50.2 demo correctness.

    Tool layer is the same across modes: 50.1 InMemoryToolRegistry +
    InMemoryToolExecutor with echo_tool registered.

Key Components:
    - build_echo_demo_handler(message: str) -> AgentLoopImpl
    - build_real_llm_handler() -> AgentLoopImpl
    - build_handler(mode: ChatMode, message: str) -> AgentLoopImpl  (dispatcher)

Created: 2026-04-30 (Sprint 50.2 Day 1.4)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Sprint 57.93 — OutputKeywordEscalationGuardrail (output pre-delivery pause)
    - 2026-06-08: Sprint 57.92 — BetweenTurnsKeywordGuardrail + note_tool (between-turns pause)
    - 2026-06-08: Sprint 57.91 — wire KeywordEscalationGuardrail (input-ESCALATE pause trigger)
    - 2026-06-08: Sprint 57.88 Day-4 — ToolGuardrail (registry matrix) gates echo_tool ESCALATE
    - 2026-06-08: Sprint 57.88 US-1 — chat path opts into hitl_deferred=True (durable pause-resume)
    - 2026-06-02: Sprint 57.71 — thread tracer param through build_handler to loop (A-4 Tier 0)
    - 2026-06-02: Sprint 57.70 Stage-1a — await async per-tenant resolve_persona
    - 2026-06-02: Sprint 57.69 A-3b — append carried_context block to resolved persona (fail-open)
    - 2026-06-02: Sprint 57.68 A-3b — per-session persona (agent_role) resolution for HANDOFF child
    - 2026-06-01: Sprint 57.65 — share executor's MemoryRetrieval into prompt builder (A-1)
    - 2026-06-01: Sprint 57.64 Day 2 — register Cat 3 memory + Cat 11 subagent tools; thread user_id
    - 2026-06-01: Sprint 57.64 Day 1 — inject Cat 5 prompt_builder (keystone)
    - 2026-05-04: (Sprint 55.2 Day 3.4) build_handler + build_echo_demo_handler
      + build_real_llm_handler now accept `business_factory_provider`. Threaded
      to make_default_executor → register_all_business_tools → 5 register_*_tools
      to enable service-mode business-domain handlers in chat main flow.
    - 2026-04-30: Initial creation (Sprint 50.2 Day 1.4) — echo_demo via
        MockChatClient + scripted responses; real_llm via AzureOpenAIAdapter.

Related:
    - .router (calls build_handler)
    - .schemas.ChatMode
    - 50.1 agent_harness.tools._inmemory.make_echo_executor
    - 50.1 agent_harness.orchestrator_loop.AgentLoopImpl
    - 49.4 adapters.azure_openai.adapter.AzureOpenAIAdapter
    - 49.4 adapters._testing.mock_clients.MockChatClient
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

from adapters._base.chat_client import ChatClient
from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    StopReason,
    ToolCall,
)
from agent_harness.guardrails import build_default_guardrail_engine
from agent_harness.guardrails.between_turns import BetweenTurnsKeywordGuardrail
from agent_harness.guardrails.input import KeywordEscalationGuardrail
from agent_harness.guardrails.output import OutputKeywordEscalationGuardrail
from agent_harness.guardrails.tool.capability_matrix import CapabilityMatrix, PermissionRule
from agent_harness.guardrails.tool.tool_guardrail import ToolGuardrail
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from business_domain._register_all import make_default_executor
from core.config import get_settings

from ._category_factories import (
    make_chat_compactor,
    make_chat_error_deps,
    make_chat_memory_deps,
    make_chat_prompt_builder,
    make_chat_state_deps,
    make_chat_subagent_dispatcher,
    make_chat_verifier_registry,
)
from .schemas import ChatMode

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from agent_harness.hitl import HITLManager
    from agent_harness.observability import Tracer
    from agent_harness.verification import VerifierRegistry
    from business_domain._service_factory import BusinessServiceFactory
    from platform_layer.governance.service_factory import ServiceFactory

# Phase 50.2 demo system prompt — instructs the model to use echo_tool when the
# user explicitly asks to "echo" something. Real LLM only.
# Sprint 57.92 (Slice 3 leg 2): also drives note_tool for "note" requests — a
# NON-escalate deterministic tool whose completed-turn output trips the
# between-turns guardrail (so the between-turns pause is reachable on 主流量).
DEMO_SYSTEM_PROMPT = (
    "You are a Sprint 50.2 demonstration agent. When the user asks you to "
    "'echo' some text, you MUST call the `echo_tool` function with that text "
    "as the `text` argument, then return the tool's output verbatim as your "
    "final answer. When the user asks you to 'note' some text, you MUST call "
    "the `note_tool` function with that text as the `text` argument, then "
    "return the tool's output verbatim as your final answer. Do not paraphrase. "
    "When the user asks you to share or state something confidential, your final "
    "answer MUST contain the word 'confidential'. "
    "For any other request, answer directly."
)

# Sprint 57.88 (Day-4): tools that require human approval on the real chat path.
# A call to one of these makes the Cat 9 ToolGuardrail return ESCALATE → the loop
# enters the deferred-HITL branch (checkpoint + ApprovalRequested + terminate with
# stop_reason="awaiting_approval"), powering the durable pause-resume drive-through.
# echo_tool is the demo's DETERMINISTIC trigger — DEMO_SYSTEM_PROMPT already drives
# the LLM to call it on "echo X", so a real "echo hello" reliably pauses for
# approval. Production per-tenant policy would source this from capability_matrix.yaml
# (deferred — design note open question); the chat path derives the matrix from the
# live tool registry instead (see build_real_llm_handler).
CHAT_HITL_ESCALATE_TOOLS = frozenset({"echo_tool"})

# Sprint 57.91 (地基 A Slice 3 leg 1): input phrases that ESCALATE the loop-start
# input guardrail → a durable HITL pause BEFORE any LLM call (the generalized
# input-ESCALATE pause point built on _emit_deferred_pause). The KeywordEscalation
# Guardrail (input chain) returns ESCALATE on a case-insensitive substring match,
# so a real "approval required: <question>" reliably pauses for approval of the
# input itself. Deterministic demo trigger (analogous to echo_tool on the tool
# path); production per-tenant escalation phrases would source from policy
# (deferred AD). Only wired when a HITLManager is present (deferred pause needs it).
CHAT_HITL_ESCALATE_INPUT_PHRASES = frozenset({"approval required"})

# Sprint 57.92 (地基 A Slice 3 leg 2): output phrases that ESCALATE the between-turns
# guardrail → a durable HITL pause at the loop top, AFTER ≥1 completed turn and BEFORE
# the next LLM call. The BetweenTurnsKeywordGuardrail (BETWEEN_TURNS chain) returns
# ESCALATE on a case-insensitive substring match against the just-completed turn's
# output. The demo drives it via note_tool: a "note the word checkpoint" request runs
# note_tool("checkpoint") in turn 0 (note_tool is NOT escalate-gated, so it executes
# end-to-end), then the between-turns gate matches "checkpoint" at the top of turn 1
# and pauses. The phrase MUST NOT contain CHAT_HITL_ESCALATE_INPUT_PHRASES so the input
# gate does not pre-empt. Only wired when a HITLManager is present (deferred pause).
CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES = frozenset({"checkpoint"})

# Sprint 57.93 (地基 A Slice 3 output-guardrail leg): phrases that ESCALATE the OUTPUT
# guardrail on a FINAL answer → a durable HITL pause BEFORE the answer is delivered
# (before LLMResponded renders the AnswerBlock in the UI). The OutputKeywordEscalation
# Guardrail (OUTPUT chain) returns ESCALATE on a case-insensitive substring match
# against the final answer. DEMO_SYSTEM_PROMPT drives the LLM to put "confidential" in
# a final answer when asked to share something confidential, so a real "tell me
# something confidential" reliably pauses for approval of DELIVERY. Registered at
# priority=5 (before the default Toxicity p10 / SensitiveInfo p20 detectors). The
# phrase MUST NOT contain the input ("approval required") or between-turns
# ("checkpoint") phrases so those gates do not pre-empt. Only wired with a HITLManager.
CHAT_HITL_ESCALATE_OUTPUT_PHRASES = frozenset({"confidential"})


def build_echo_demo_handler(
    message: str,
    *,
    hitl_manager: "HITLManager | None" = None,
    hitl_timeout_s: int = 14400,
    business_factory_provider: Callable[[], "BusinessServiceFactory"] | None = None,
) -> tuple[AgentLoopImpl, "VerifierRegistry | None"]:
    """Wire AgentLoopImpl with a MockChatClient pre-scripted to call echo_tool.

    The mock responds with TOOL_USE on turn 1 (echo_tool with the user's
    message text) and END_TURN with the echoed content on turn 2.

    Sprint 53.6 US-4: optional `hitl_manager` opts the loop into Cat 9 Stage 3
    HITL escalation. None preserves 53.3 baseline behavior (no HITL pause).

    Sprint 55.2 US-3: optional `business_factory_provider` enables service-mode
    business domain handlers (settings.business_domain_mode='service' path).
    None preserves PoC mock-mode behavior.

    Sprint 57.63 Day 2 (Cat 10, approach A): returns `(loop, verifier_registry)`.
    echo_demo always returns `registry=None` (no verification on the demo path).
    """
    registry, executor = make_default_executor(factory_provider=business_factory_provider)
    parser = OutputParserImpl()

    scripted: list[ChatResponse] = [
        ChatResponse(
            model="mock-model",
            content="",
            tool_calls=[
                ToolCall(
                    id="call_echo_demo_1",
                    name="echo_tool",
                    arguments={"text": message},
                ),
            ],
            stop_reason=StopReason.TOOL_USE,
        ),
        ChatResponse(
            model="mock-model",
            content=message,
            stop_reason=StopReason.END_TURN,
        ),
    ]
    chat_client: ChatClient = MockChatClient(responses=scripted)

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        system_prompt=DEMO_SYSTEM_PROMPT,
        max_turns=4,  # Echo demo never needs more than 2 turns; 4 = safety margin.
        hitl_manager=hitl_manager,
        hitl_timeout_s=hitl_timeout_s,
    )
    return loop, None


def build_real_llm_handler(
    *,
    hitl_manager: "HITLManager | None" = None,
    hitl_timeout_s: int = 14400,
    business_factory_provider: Callable[[], "BusinessServiceFactory"] | None = None,
    db: "AsyncSession | None" = None,
    session_id: "UUID | None" = None,
    tenant_id: "UUID | None" = None,
    user_id: "UUID | None" = None,
    system_prompt: str = DEMO_SYSTEM_PROMPT,
    tracer: "Tracer | None" = None,
) -> tuple[AgentLoopImpl, "VerifierRegistry | None"]:
    """Wire AgentLoopImpl with AzureOpenAIAdapter. Requires env vars.

    Sprint 55.2 US-3: optional `business_factory_provider` enables service-mode
    business domain handlers. See build_echo_demo_handler for full description.

    Sprint 57.63 Day 2 (Cat 10, approach A): returns `(loop, verifier_registry)`.
    When `settings.chat_verification_mode == "enabled"`, builds a registry with a
    real `LLMJudgeVerifier` sharing THIS handler's adapter (the same ChatClient
    the loop runs on); otherwise returns `registry=None` (wrapper passthrough).

    Sprint 57.64 Day 2 (Cat 3 + Cat 11): registers the REAL memory tools
    (memory_search / memory_write) and the FORK/TEAMMATE/AS_TOOL subagent tools
    on the chat executor. Both via opt-in deps to make_default_executor:
      - memory: make_chat_memory_deps() builds the 5-scope layer map; tenant /
        user / session scoping is supplied per-call by the loop's
        ExecutionContext (built from the request TraceContext), so memory stays
        tenant-isolated even though layers are constructed once per request.
      - subagent: make_chat_subagent_dispatcher(chat_client) shares THIS adapter;
        task_spawn binds to `session_id` for parent attribution. HANDOFF excluded.
    `user_id` is threaded into the TraceContext by the router so memory reads /
    writes attribute to the authenticated user.

    Raises:
        RuntimeError: when any of AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY /
            AZURE_OPENAI_DEPLOYMENT_NAME is missing.
    """
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            "Cannot build real_llm handler — missing env vars: "
            + ", ".join(missing)
            + ". Configure .env or use mode='echo_demo'."
        )

    # Late import — keeps unit tests free of azure SDK weight when only echo_demo is exercised.
    from adapters.azure_openai.adapter import AzureOpenAIAdapter
    from adapters.azure_openai.config import AzureOpenAIConfig

    # AzureOpenAIConfig is a BaseSettings — pulls AZURE_OPENAI_* from env automatically.
    chat_client: ChatClient = AzureOpenAIAdapter(AzureOpenAIConfig())

    # Sprint 57.64 Day 2: Cat 3 memory tools (REAL handlers, not placeholder) +
    # Cat 11 FORK/TEAMMATE/AS_TOOL subagent tools, registered via opt-in deps.
    # Both fall back to absent when their inputs are missing (e.g. session_id is
    # required for the subagent task_spawn parent attribution).
    memory_retrieval, memory_layers = make_chat_memory_deps(db)
    subagent_dispatcher = (
        make_chat_subagent_dispatcher(chat_client) if session_id is not None else None
    )
    registry, executor = make_default_executor(
        factory_provider=business_factory_provider,
        memory_retrieval=memory_retrieval,
        memory_layers=memory_layers,
        subagent_dispatcher=subagent_dispatcher,
        parent_session_id=session_id,
    )
    parser = OutputParserImpl()

    # Sprint 57.2 US-3 (closes AD-Cat9-1-WireDetectors): production
    # handler wires GuardrailEngine with default 4-detector chain (PII +
    # Jailbreak input; Toxicity + SensitiveInfo output). Echo demo handler
    # left without engine to keep test fixtures predictable.
    #
    # Sprint 57.63 Day 1: Cat 4 (context compaction) + Cat 7 (state reducer +
    # checkpointer) activate by injection alone (AgentLoopImpl opt-in deps;
    # loop.py call-sites verified Day 0). Cat 7 is all-three-or-nothing —
    # make_chat_state_deps returns (None, None) when db / session_id /
    # tenant_id is missing (legacy / test callers), preserving baseline.
    compactor = make_chat_compactor(chat_client)
    # Sprint 57.64 Day 1: Cat 5 (KEYSTONE) — inject DefaultPromptBuilder so the
    # loop takes its structured build() path (loop.py:881 true-branch, emits
    # PromptBuilt) instead of the naked fallback. Closes the AP-8 / AP-2
    # false-green: before this, self._prompt_builder was always None on the
    # production chat path.
    #
    # Sprint 57.65 (A-1 Tier2): share the SAME MemoryRetrieval already built for
    # the executor's memory tools (above) so the prompt renders a per-turn,
    # capped (≤2000-token) memory summary + verify-before-use rules from the same
    # 5-scope layers the tools read/write — one retrieval, no second instance.
    prompt_builder = make_chat_prompt_builder(chat_client, memory_retrieval=memory_retrieval)
    reducer, checkpointer = make_chat_state_deps(db, session_id, tenant_id)
    # Sprint 57.63 Day 2: Cat 8 (error handling) — the 5 deps activate
    # `_handle_tool_error` (classify → budget → terminator) on the production
    # tool path; always injected (no DB / env required to construct).
    (
        error_policy,
        retry_policy,
        circuit_breaker,
        error_budget,
        error_terminator,
    ) = make_chat_error_deps()

    # Sprint 57.88 (Day-4): wire the REAL Cat 9 ToolGuardrail + CapabilityMatrix onto
    # the chat path so tool calls are gated by per-tool policy. The matrix is derived
    # from THIS request's tool registry — every registered tool (echo_tool + memory +
    # subagent + business) gets a PASS rule EXCEPT CHAT_HITL_ESCALATE_TOOLS, which get
    # requires_approval=True → ESCALATE. Deriving from the registry (not a static YAML)
    # guarantees every EXPOSED tool has a rule, so memory / subagent / business tools
    # never trip ToolGuardrail's unknown-tool → BLOCK default. Combined with
    # hitl_deferred (below), an echo_tool call pauses the loop for durable approval.
    guardrail_engine = build_default_guardrail_engine()
    tool_rules = {
        spec.name: PermissionRule(requires_approval=spec.name in CHAT_HITL_ESCALATE_TOOLS)
        for spec in registry.list()
    }
    guardrail_engine.register(
        ToolGuardrail(CapabilityMatrix(capability_to_tools={}, permission_rules=tool_rules)),
        priority=10,
    )
    # Sprint 57.91 (Slice 3 leg 1): wire the input-ESCALATE pause trigger only when
    # a HITLManager is present (the deferred pause needs it; without it an ESCALATE
    # would fail closed to BLOCK). Priority 5 runs it before PII / Jailbreak — it
    # PASSes any non-trigger input, so the rest of the input chain still runs.
    if hitl_manager is not None:
        guardrail_engine.register(
            KeywordEscalationGuardrail(CHAT_HITL_ESCALATE_INPUT_PHRASES),
            priority=5,
        )
        # Sprint 57.92 (Slice 3 leg 2): between-turns-ESCALATE pause trigger (same
        # deferred-pause requirement). Registers on the BETWEEN_TURNS chain (its own
        # guardrail_type) so it does NOT double-fire with the per-response OUTPUT
        # check; the loop runs it at the loop top after ≥1 completed turn.
        guardrail_engine.register(
            BetweenTurnsKeywordGuardrail(CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES),
        )
        # Sprint 57.93 (地基 A Slice 3 output-guardrail leg): output-ESCALATE
        # pre-delivery pause trigger. Registers on the OUTPUT chain at priority=5
        # so it runs BEFORE the default Toxicity (p10) / SensitiveInfo (p20)
        # detectors (_run_chain is fail-fast-first-non-PASS) — its ESCALATE on a
        # final answer containing the phrase wins; a non-matching answer PASSes
        # through to the defaults unchanged. The loop's pre-delivery gate pauses
        # the flagged answer BEFORE LLMResponded renders it.
        guardrail_engine.register(
            OutputKeywordEscalationGuardrail(CHAT_HITL_ESCALATE_OUTPUT_PHRASES),
            priority=5,
        )

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        # Sprint 57.71 (A-4 Tier 0): inject the router's real OTelTracer so the
        # loop's root span + per-turn span tree run on a real tracer instead of
        # the NoOpTracer fallback. None preserves the pre-57.71 baseline (NoOp).
        # The loop is the single trace-tree owner; the adapter / executor /
        # parser internal tracers stay NoOp (not wired) → no double spans (D8).
        tracer=tracer,
        # Sprint 57.68 A-3b (US-3): a HANDOFF-booted child session runs as its
        # target persona, NOT the demo persona (= Potemkin). The router resolves
        # the session's meta_data["agent_role"] → persona prompt and passes it
        # here; absent an agent_role it stays DEMO_SYSTEM_PROMPT (the default).
        system_prompt=system_prompt,
        max_turns=8,
        hitl_manager=hitl_manager,
        hitl_timeout_s=hitl_timeout_s,
        # Sprint 57.88 US-1 (decision A): the chat path opts into DEFERRED HITL
        # pause-resume whenever a HITLManager is wired. A tool ESCALATE then
        # checkpoints + emits ApprovalRequested + terminates with
        # stop_reason="awaiting_approval" (releasing the SSE connection) instead
        # of blocking on wait_for_decision — a human approval may take hours/days.
        # When hitl_manager is None (HITL_ENABLED=false / no factory) this is
        # False → 53.5 baseline (the deferred branch is a no-op anyway since it
        # needs the manager). The later POST /chat/{id}/resume drives resume().
        hitl_deferred=(hitl_manager is not None),
        guardrail_engine=guardrail_engine,
        compactor=compactor,
        prompt_builder=prompt_builder,
        reducer=reducer,
        checkpointer=checkpointer,
        tenant_id=tenant_id,
        error_policy=error_policy,
        retry_policy=retry_policy,
        circuit_breaker=circuit_breaker,
        error_budget=error_budget,
        error_terminator=error_terminator,
    )

    # Sprint 57.63 Day 2: Cat 10 — build a real verifier registry only when
    # enabled; it shares THIS adapter (LLM-neutral; same ChatClient as the loop).
    settings = get_settings()
    verifier_registry: VerifierRegistry | None = None
    if settings.chat_verification_mode == "enabled":
        verifier_registry = make_chat_verifier_registry(
            chat_client, settings.chat_verification_judge_template
        )
    return loop, verifier_registry


def build_handler(
    mode: ChatMode,
    message: str,
    *,
    service_factory: "ServiceFactory | None" = None,
    hitl_timeout_s: int = 14400,
    business_factory_provider: Callable[[], "BusinessServiceFactory"] | None = None,
    db: "AsyncSession | None" = None,
    session_id: "UUID | None" = None,
    tenant_id: "UUID | None" = None,
    user_id: "UUID | None" = None,
    system_prompt: str = DEMO_SYSTEM_PROMPT,
    tracer: "Tracer | None" = None,
) -> tuple[AgentLoopImpl, "VerifierRegistry | None"]:
    """Dispatch to the per-mode builder. Single entry-point for the router.

    Sprint 57.63 Day 2 (Cat 10, approach A): returns `(loop, verifier_registry)`
    — the per-mode builder's tuple is passed through unchanged.

    Sprint 53.6 US-4: when `service_factory` is provided AND env flag
    HITL_ENABLED is not "false", resolves the production HITLManager from the
    factory and injects it into AgentLoopImpl. Without the factory (legacy
    callers, tests) the loop runs with 53.3 baseline behavior.

    Sprint 55.2 US-3: optional `business_factory_provider` enables service-mode
    business-domain handlers (settings.business_domain_mode='service' path).
    None preserves PoC mock-mode behavior — see _register_all.make_default_executor.
    """
    hitl_manager: "HITLManager | None" = None
    if service_factory is not None and _hitl_enabled():
        hitl_manager = service_factory.get_hitl_manager()
    if mode == "echo_demo":
        return build_echo_demo_handler(
            message,
            hitl_manager=hitl_manager,
            hitl_timeout_s=hitl_timeout_s,
            business_factory_provider=business_factory_provider,
        )
    if mode == "real_llm":
        return build_real_llm_handler(
            hitl_manager=hitl_manager,
            hitl_timeout_s=hitl_timeout_s,
            business_factory_provider=business_factory_provider,
            db=db,
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            system_prompt=system_prompt,
            # Sprint 57.71 (A-4 Tier 0): thread the router's real tracer through
            # to the loop. echo_demo path is unaffected (no tracer arg).
            tracer=tracer,
        )
    raise ValueError(f"Unsupported mode: {mode!r}")


def _hitl_enabled() -> bool:
    """Feature toggle. Default ON; explicit `HITL_ENABLED=false` disables wiring."""
    return os.environ.get("HITL_ENABLED", "true").strip().lower() != "false"


# === resolve_session_persona: HANDOFF-booted child runs as its target persona ==
# Why (Sprint 57.68 A-3b US-3): a HANDOFF boots a child session carrying
# meta_data["agent_role"] = target_agent (HandoffService). When the client later
# resumes THAT child session via POST /chat, the loop must run as the target
# persona (researcher / reviewer / planner) — NOT the demo persona, which would
# make the whole handover a Potemkin feature. The router resolves this BEFORE
# build_handler so the builders stay sync (no async DB import in the wiring
# layer). Tenant-scoped lookup (multi-tenant 鐵律). Returns DEMO_SYSTEM_PROMPT
# for ordinary (non-handoff) sessions and on any miss / DB flake (fail-open to
# the demo persona — a resolution failure must not break chat).
async def resolve_session_persona(
    db: "AsyncSession | None",
    session_id: "UUID | None",
    tenant_id: "UUID | None",
) -> str:
    """Resolve a session's persona system prompt from meta_data["agent_role"].

    Returns the target persona's system prompt when the session row carries an
    `agent_role` that resolves in the persona registry; otherwise (no DB /
    missing row / no agent_role / unknown persona / lookup error) returns
    DEMO_SYSTEM_PROMPT.

    Sprint 57.69 A-3b slice 2: when the session also carries a
    meta_data["carried_context"] (the parent's conversation captured at
    HANDOFF), the rendered carried-context block is appended to the resolved
    persona prompt so the child agent sees the prior conversation. A nested
    fail-open guard ensures a malformed carried_context NEVER loses the resolved
    persona (the persona prompt is returned without the block on any render error).
    """
    if db is None or session_id is None or tenant_id is None:
        return DEMO_SYSTEM_PROMPT
    try:
        from infrastructure.db.repositories.session_repository import SessionRepository
        from platform_layer.handoff.context_carry import render_carried_context_block
        from platform_layer.handoff.persona_registry import resolve_persona

        session = await SessionRepository(db).get_session(
            session_id=session_id, tenant_id=tenant_id
        )
        if session is None:
            return DEMO_SYSTEM_PROMPT
        meta = session.meta_data or {}
        agent_role = meta.get("agent_role")
        if not agent_role:
            return DEMO_SYSTEM_PROMPT
        # Sprint 57.70: per-tenant DB catalog → hardcoded defaults → None
        # (async, tenant-scoped). db + tenant_id are non-None here (guarded above).
        persona = await resolve_persona(db, tenant_id, str(agent_role))
        prompt = persona if persona is not None else DEMO_SYSTEM_PROMPT

        # Append the carried parent conversation (if any) to the persona prompt.
        # Nested fail-open: a malformed carried_context must not crash resolution
        # nor lose the persona — fall back to the persona prompt alone.
        carried = meta.get("carried_context")
        if carried:
            try:
                block = render_carried_context_block(carried)
                if block:
                    prompt = f"{prompt}\n\n{block}"
            except Exception:  # noqa: BLE001
                return prompt
        return prompt
    except Exception:  # noqa: BLE001
        return DEMO_SYSTEM_PROMPT
