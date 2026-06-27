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
Last Modified: 2026-06-14

Modification History (newest-first):
    - 2026-06-14: Sprint 57.115 — force_load_skill param → "## Active Skill" deterministic injection
    - 2026-06-13: Sprint 57.110 B4 — child loops inherit the composed guardrail engine
    - 2026-06-12: Sprint 57.109 C2 — compactor runs on profile.cheap (semantic summarize tier)
    - 2026-06-12: Sprint 57.107 B3 — register spec-only handoff tool (policy-gated, parent only)
    - 2026-06-11: Sprint 57.104 C1 — resolve per-tenant ModelPolicy → build per-tenant ModelProfile
    - 2026-06-11: Sprint 57.103 B2b — teammate inbox_factory → inbox_scope (register child queue)
    - 2026-06-11: Sprint 57.102 B2a — wire teammate child-loop factory + inbox_factory
    - 2026-06-11: Sprint 57.101 B1 — wire QueueMessageInbox (between-turns injection) into loop ctor
    - 2026-06-10: Sprint 57.99 A2 — thread chat_verification_escalate_on_max into loop ctor
    - 2026-06-10: Sprint 57.98 A1 US-5 — inject verifier_registry into loop ctor; return loop
    - 2026-06-09: Sprint 57.97 — ModelProfile{action,cheap}; verification on profile.cheap
    - 2026-06-09: Sprint 57.95 — wire subagent_event_emitter on chat path (SSE relay)
    - 2026-06-09: Sprint 57.94 — child-loop factory for real FORK/AS_TOOL child loops
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
from typing import TYPE_CHECKING, cast

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
from agent_harness.guardrails.tool.risky_action_detector import RiskyActionDetector
from agent_harness.guardrails.tool.tool_guardrail import ToolGuardrail
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.skills import render_catalog_block, render_skill_instructions
from agent_harness.subagent import MailboxStore
from agent_harness.verification.templates import list_templates
from business_domain._register_all import make_default_executor
from core.config import get_settings
from platform_layer.governance.harness_policy import HarnessPolicy
from platform_layer.handoff.persona_registry import DEFAULT_AGENTS

from ._category_factories import (
    make_chat_compactor,
    make_chat_error_deps,
    make_chat_memory_deps,
    make_chat_message_store,
    make_chat_prompt_builder,
    make_chat_state_deps,
    make_chat_subagent_dispatcher,
    make_chat_todo_store,
    make_chat_verifier_registry,
)
from .injection_registry import (
    QueueMessageInbox,
    get_default_injection_registry,
    make_teammate_inbox_scope,
)
from .schemas import ChatMode

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from adapters._base.model_policy import ModelPolicy
    from agent_harness._contracts import (
        MessageInbox,
        SubagentBudget,
        SubagentFailurePolicy,
        TeammateInboxScope,
    )
    from agent_harness.hitl import HITLManager
    from agent_harness.observability import Tracer
    from agent_harness.orchestrator_loop._abc import AgentLoop
    from agent_harness.skills import SkillRegistry
    from agent_harness.subagent.dispatcher import DefaultSubagentDispatcher, SubagentEventEmitter
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
    "For any MULTI-STEP task, FIRST call the `write_todos` tool to lay out a plan "
    "of 3 or more todos, then update each todo's status (pending -> in_progress -> "
    "completed) by calling `write_todos` again with the WHOLE updated list as you "
    "finish each step. Use the plan as your single source of truth — do not keep a "
    "separate prose checklist. "
    "For questions about company knowledge or internal documents, FIRST call "
    "the `knowledge_search` tool, then ground your answer in the returned "
    "snippets and cite their source paths. Do not answer company-knowledge "
    "questions from memory alone. "
    "For any other request, answer directly."
)

# Sprint 57.94 (地基 A payoff): the FORK / AS_TOOL child loop persona + turn cap.
# A child runs a real multi-turn TAO loop with a recursion-safe tool subset
# (no task_spawn / handoff). A small turn cap bounds it; the SubagentBudget caps
# its tokens. Kept lean (no guardrail / verifier / checkpointer) for this slice.
CHILD_SUBAGENT_SYSTEM_PROMPT = (
    "You are a focused sub-task worker spawned to complete one delegated task. "
    "Use the available tools when they help, then report a concise result as your "
    "final answer. Do not ask the user questions; you are autonomous."
)
CHILD_SUBAGENT_MAX_TURNS = 4

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
) -> AgentLoopImpl:
    """Wire AgentLoopImpl with a MockChatClient pre-scripted to call echo_tool.

    The mock responds with TOOL_USE on turn 1 (echo_tool with the user's
    message text) and END_TURN with the echoed content on turn 2.

    Sprint 53.6 US-4: optional `hitl_manager` opts the loop into Cat 9 Stage 3
    HITL escalation. None preserves 53.3 baseline behavior (no HITL pause).

    Sprint 55.2 US-3: optional `business_factory_provider` enables service-mode
    business domain handlers (settings.business_domain_mode='service' path).
    None preserves PoC mock-mode behavior.

    Sprint 57.98 A1 (US-5): returns the wired `AgentLoopImpl`. echo_demo never
    verifies (no registry injected → the loop's Cat 10 gate stays dormant).
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
    return loop


def build_real_llm_handler(
    *,
    hitl_manager: "HITLManager | None" = None,
    hitl_timeout_s: int = 14400,
    business_factory_provider: Callable[[], "BusinessServiceFactory"] | None = None,
    db: "AsyncSession | None" = None,
    session_id: "UUID | None" = None,
    tenant_id: "UUID | None" = None,
    model_policy: "ModelPolicy | None" = None,
    harness_policy: "HarnessPolicy | None" = None,
    user_id: "UUID | None" = None,
    system_prompt: str = DEMO_SYSTEM_PROMPT,
    tracer: "Tracer | None" = None,
    subagent_event_emitter: "SubagentEventEmitter | None" = None,
    skill_registry: "SkillRegistry | None" = None,
    force_load_skill: str | None = None,
) -> AgentLoopImpl:
    """Wire AgentLoopImpl with AzureOpenAIAdapter. Requires env vars.

    Sprint 55.2 US-3: optional `business_factory_provider` enables service-mode
    business domain handlers. See build_echo_demo_handler for full description.

    Sprint 57.98 A1 (US-5): returns the wired `AgentLoopImpl`. When
    `settings.chat_verification_mode == "enabled"`, builds a registry with a real
    `LLMJudgeVerifier` (sharing the cheap-tier ChatClient, 57.97) and INJECTS it
    into the loop ctor so the loop runs the in-loop Cat 10 verification gate;
    otherwise the gate is dormant (registry None). The retired
    run_with_verification wrapper used to run this AROUND loop.run().

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
    from adapters.azure_openai.profile import build_azure_model_profile

    # Sprint 57.104 (C1): build the per-tenant ModelProfile from the resolved policy.
    # The router resolved it via resolve_tenant_model_policy BEFORE build_handler (the
    # resolve_session_persona pattern), so this stays sync. Tier consumer map:
    # `chat_client` IS profile.action — the tenant's strong tier — and the loop /
    # prompt builder / subagents / memory extraction run on it; the verifier (below,
    # 57.97) AND the compactor's semantic summarize (57.109 C2) route to profile.cheap
    # (the tenant's, or env, cheap deployment). A None / all-None policy is
    # byte-identical to the Sprint 57.97 env-only path (cheap is action when unset);
    # the cheap tier saves on the per-request llm_judge call (default-ON since 57.83)
    # and the compaction summarize call without touching the user-facing turn.
    profile = build_azure_model_profile(model_policy)
    chat_client: ChatClient = profile.action
    parser = OutputParserImpl()  # built early — the Sprint 57.94 child-loop factory needs it

    # Sprint 57.64 Day 2: Cat 3 memory tools (REAL handlers, not placeholder) +
    # Cat 11 FORK/TEAMMATE/AS_TOOL subagent tools, registered via opt-in deps.
    # Both fall back to absent when their inputs are missing (e.g. session_id is
    # required for the subagent task_spawn parent attribution).
    memory_retrieval, memory_layers = make_chat_memory_deps(db)

    # Sprint 57.94 (地基 A payoff): when subagents are reachable (session_id present),
    # build a child-loop factory so a FORK / AS_TOOL subagent runs a REAL child loop
    # (multi-turn, tool-capable) instead of a single-shot chat. The child carries a
    # recursion-safe tool subset — make_default_executor WITHOUT a subagent_dispatcher
    # omits task_spawn + the agent_researcher AS_TOOL, so a child cannot itself spawn
    # (depth bounded at 1). The factory closes over the same Cat 1 deps the parent
    # uses; loop.py is unchanged (the child reuses run()/_run_turns).
    if session_id is not None:
        child_registry, child_executor = make_default_executor(
            factory_provider=business_factory_provider,
            memory_retrieval=memory_retrieval,
            memory_layers=memory_layers,
            subagent_dispatcher=None,
            parent_session_id=None,
        )

        def _make_child_loop(budget: SubagentBudget) -> AgentLoop:
            # Sprint 57.110 (B4): the child inherits the parent's COMPOSED guardrail
            # engine (late-bound closure — `guardrail_engine` is assembled below with
            # the tenant's C3 policy guardrails) so a child is never a Cat 9 bypass.
            # No HITL wiring in the child → any ESCALATE fail-closes to BLOCK
            # (loop.py's existing invariant). The factory only runs at spawn time,
            # after this builder completes, so the late binding is safe.
            return AgentLoopImpl(
                chat_client=chat_client,
                output_parser=parser,
                tool_executor=child_executor,
                tool_registry=child_registry,
                system_prompt=CHILD_SUBAGENT_SYSTEM_PROMPT,
                tenant_id=tenant_id,
                tracer=tracer,
                max_turns=CHILD_SUBAGENT_MAX_TURNS,
                token_budget=budget.max_tokens,
                guardrail_engine=guardrail_engine,
            )

        # Sprint 57.102 (B2a): the TEAMMATE child loop — a real multi-turn child (like
        # FORK) but with a send_to_parent tool + the B1 MessageInbox. ONE shared per-
        # request MailboxStore is threaded to the dispatcher (the executor's drain) AND
        # to the teammate child executor's send_to_parent tool (via teammate_mailbox) so
        # both use the SAME instance. Sprint 57.103 (B2b): the inbox_scope (below) binds +
        # registers the child's MessageInbox queue (B1 InjectionRegistry, keyed by
        # subagent_id) for the child's lifetime so a chat-user inject reaches a LIVE
        # teammate; the scope is None without a tenant (the InjectionRegistry is
        # tenant-scoped).
        teammate_mailbox = MailboxStore()
        teammate_registry, teammate_executor = make_default_executor(
            factory_provider=business_factory_provider,
            memory_retrieval=memory_retrieval,
            memory_layers=memory_layers,
            subagent_dispatcher=None,  # recursion-safe (no task_spawn) — depth bound 1
            parent_session_id=session_id,  # send_to_parent attribution
            teammate_mailbox=teammate_mailbox,  # registers send_to_parent on this child
        )

        def _make_teammate_child_loop(
            budget: SubagentBudget, inbox: "MessageInbox | None"
        ) -> AgentLoop:
            # Sprint 57.110 (B4): same composed-engine inheritance as _make_child_loop
            # above (late-bound; ESCALATE-in-child fail-closes to BLOCK).
            return AgentLoopImpl(
                chat_client=chat_client,
                output_parser=parser,
                tool_executor=teammate_executor,
                tool_registry=teammate_registry,
                system_prompt=CHILD_SUBAGENT_SYSTEM_PROMPT,
                tenant_id=tenant_id,
                tracer=tracer,
                max_turns=CHILD_SUBAGENT_MAX_TURNS,
                token_budget=budget.max_tokens,
                message_inbox=inbox,
                guardrail_engine=guardrail_engine,
            )

        teammate_inbox_scope: "TeammateInboxScope | None" = None
        if tenant_id is not None:
            teammate_inbox_scope = make_teammate_inbox_scope(
                get_default_injection_registry(), tenant_id
            )

        # Explicit Optional annotation: the B4 late-bound closure capture above
        # defers mypy's re-analysis of this function, which re-infers this
        # conditional assignment strictly (None in the else branch below).
        subagent_dispatcher: "DefaultSubagentDispatcher | None" = make_chat_subagent_dispatcher(
            chat_client,
            child_loop_factory=_make_child_loop,
            # Sprint 57.95: the chat path now wires the emitter so SubagentSpawned/
            # Completed reach the SSE stream (Inspector Tree node). None on legacy
            # callers → dispatcher emission no-ops (pre-57.95 behavior).
            event_emitter=subagent_event_emitter,
            # Sprint 57.102 (B2a): TEAMMATE real child loop + B1 inbox + shared mailbox.
            teammate_child_loop_factory=_make_teammate_child_loop,
            inbox_scope=teammate_inbox_scope,
            mailbox=teammate_mailbox,
        )
    else:
        subagent_dispatcher = None

    # Sprint 57.107 (B3): resolve the C3 policy EARLY — the spec-only `handoff`
    # registration below needs it before the executor build (the rest of the
    # C3 sourcing block further down reuses this same `policy`).
    policy = harness_policy or HarnessPolicy()

    # Sprint 57.107 (B3): the spec-only `handoff` trigger tool. Registered unless
    # the tenant turned it off (handoff_enabled=False → tool absent, zero-cost
    # off). The description suggests the tenant's allowlist (or the 3 default
    # personas) — guidance only; HandoffService boot-time validation is
    # authoritative. No hot-path DB read: DEFAULT_AGENTS is the hardcoded
    # persona seed (per-tenant catalog targets still boot via resolve_persona).
    # Child / teammate executors never get this (depth-bound: no nested handoff).
    handoff_targets: list[str] | None = None
    if policy.handoff_enabled is not False:
        handoff_targets = (
            list(policy.handoff_target_allowlist)
            if policy.handoff_target_allowlist
            else sorted(DEFAULT_AGENTS)
        )

    # Sprint 57.110 (B4): tenant-resolved spawn failure semantics. The PUT-side
    # literal validation guarantees the stored value; cast narrows str|None to
    # the Literal for the factory chain (None → the fail_soft default).
    subagent_failure_policy = cast(
        "SubagentFailurePolicy", policy.subagent_failure_policy or "fail_soft"
    )

    # Sprint 57.140 (research #1 task primitive): the per-session durable todo
    # store, built once here. Passed to make_default_executor so the write_todos
    # tool can persist (opt-in), to the system prompt below for the run-start
    # "## Active Plan" re-injection, AND to AgentLoopImpl so the loop emits
    # TodosUpdated. None for legacy / test callers (missing db/session/tenant).
    todo_store = make_chat_todo_store(db, session_id, tenant_id)

    # Sprint 57.145: the first real external data-source connector. The
    # knowledge_search tool reads a configured docs folder (settings.knowledge_docs_root,
    # default = in-repo planning docs; prod overrides via env). Threaded as an opt-in
    # root string; make_default_executor skips registration if the root is missing.
    knowledge_root = get_settings().knowledge_docs_root or None
    # Sprint 57.146: when KNOWLEDGE_VECTOR_ENABLED + an embedding deployment + Qdrant
    # are configured, the process-wide vector index makes knowledge_search semantic
    # (keyword fail-soft fallback). None (flag off / unconfigured) → 57.145 keyword.
    from api.v1.chat.knowledge_index import get_knowledge_vector_index

    knowledge_vector_index = get_knowledge_vector_index()

    registry, executor = make_default_executor(
        factory_provider=business_factory_provider,
        memory_retrieval=memory_retrieval,
        memory_layers=memory_layers,
        subagent_dispatcher=subagent_dispatcher,
        parent_session_id=session_id,
        handoff_targets=handoff_targets,
        subagent_failure_policy=subagent_failure_policy,
        skill_registry=skill_registry,
        todo_store=todo_store,
        knowledge_root=knowledge_root,
        knowledge_vector_index=knowledge_vector_index,
    )

    # Sprint 57.113: advertise the available skills cheaply in the system prompt
    # (names + descriptions only) so the model self-selects + calls read_skill to
    # lazy-load the full instructions. Rides the persona system_prompt seam (the
    # loop prepends it as the system message → reaches the LLM). Empty registry →
    # "" → system_prompt byte-identical to the no-skills path.
    if skill_registry is not None:
        skills_block = render_catalog_block(skill_registry.list())
        if skills_block:
            system_prompt = f"{system_prompt}\n\n{skills_block}"

    # Sprint 57.115 (force-load / slash-command): when the user explicitly picked
    # a skill via the /skill-name composer command, the router validated it
    # against this registry and threads its name here. Append its FULL instructions
    # under "## Active Skill" so the skill loads DETERMINISTICALLY — the model does
    # NOT need to self-select read_skill (the drive-through proves read_skill 0×
    # yet the output follows). None / a stale name → no block (byte-identical to
    # the no-force-load path). read_skill stays registered for other skills.
    if force_load_skill and skill_registry is not None:
        forced_skill = skill_registry.get(force_load_skill)
        if forced_skill is not None:
            system_prompt = (
                f"{system_prompt}\n\n## Active Skill\n"
                f'The user explicitly selected the "{forced_skill.name}" skill for '
                f"this request. Follow its instructions:\n\n"
                f"{render_skill_instructions(forced_skill)}"
            )

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
    # Sprint 57.109 (C2): the semantic summarize runs on the CHEAP tier —
    # compaction is summarisation, not user-facing reasoning (cheap unset →
    # cheap is action → byte-identical).
    compactor = make_chat_compactor(profile.cheap)
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
    # Sprint 57.127 (AD-ChatV2-Live-MultiTurn-Context): the per-session message
    # ledger — the main chat loop rehydrates prior conversation from it + persists
    # new messages (multi-turn context). None for legacy / test callers (missing
    # db/session/tenant). Subagent child loops below are built WITHOUT a store.
    message_store = make_chat_message_store(db, session_id, tenant_id)
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
    # Sprint 57.106 (C3): resolve the per-tenant HarnessPolicy overrides. Each
    # field falls back to the module default when the tenant did not set it
    # (None = not-set); an explicit empty tuple is a real "off" override (e.g.
    # escalate_tools=() turns the escalate list off). A tenant with no policy is
    # byte-identical to the pre-57.106 hardcoded path. The frozenset names below
    # are the SYSTEM DEFAULTS (kept as-is — they are referenced by name in two
    # other modules' comments; renaming would churn unrelated files per the
    # surgical-changes rule). `policy` itself is resolved earlier (57.107 moved
    # it above the executor build for the handoff spec registration).
    escalate_tools = (
        frozenset(policy.escalate_tools)
        if policy.escalate_tools is not None
        else CHAT_HITL_ESCALATE_TOOLS
    )
    escalate_input_phrases = (
        frozenset(policy.escalate_input_phrases)
        if policy.escalate_input_phrases is not None
        else CHAT_HITL_ESCALATE_INPUT_PHRASES
    )
    escalate_between_turns_phrases = (
        frozenset(policy.escalate_between_turns_phrases)
        if policy.escalate_between_turns_phrases is not None
        else CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES
    )
    escalate_output_phrases = (
        frozenset(policy.escalate_output_phrases)
        if policy.escalate_output_phrases is not None
        else CHAT_HITL_ESCALATE_OUTPUT_PHRASES
    )

    guardrail_engine = build_default_guardrail_engine()
    tool_rules = {
        spec.name: PermissionRule(requires_approval=spec.name in escalate_tools)
        for spec in registry.list()
    }
    guardrail_engine.register(
        ToolGuardrail(CapabilityMatrix(capability_to_tools={}, permission_rules=tool_rules)),
        priority=10,
    )
    # Sprint 57.106 (C3): the risky-action detector screens python_sandbox code +
    # tenant extra patterns into the existing Cat 9 HITL approval flow (ESCALATE,
    # never BLOCK). Default ON; a tenant disables it via risky_action_enabled=False
    # → not registered (zero-cost off). Priority 8 runs it before ToolGuardrail (p10)
    # so a risky sandbox call escalates even if its per-tool rule is PASS. Independent
    # of hitl_manager presence at registration, but the actual pause needs HITL (an
    # ESCALATE without a deferred-pause manager fails closed to BLOCK in the loop —
    # acceptable for a risky action).
    if policy.risky_action_enabled is not False:
        guardrail_engine.register(
            RiskyActionDetector(extra_patterns=policy.risky_action_extra_patterns or ()),
            priority=8,
        )
    # Sprint 57.91 (Slice 3 leg 1): wire the input-ESCALATE pause trigger only when
    # a HITLManager is present (the deferred pause needs it; without it an ESCALATE
    # would fail closed to BLOCK). Priority 5 runs it before PII / Jailbreak — it
    # PASSes any non-trigger input, so the rest of the input chain still runs.
    if hitl_manager is not None:
        guardrail_engine.register(
            KeywordEscalationGuardrail(escalate_input_phrases),
            priority=5,
        )
        # Sprint 57.92 (Slice 3 leg 2): between-turns-ESCALATE pause trigger (same
        # deferred-pause requirement). Registers on the BETWEEN_TURNS chain (its own
        # guardrail_type) so it does NOT double-fire with the per-response OUTPUT
        # check; the loop runs it at the loop top after ≥1 completed turn.
        guardrail_engine.register(
            BetweenTurnsKeywordGuardrail(escalate_between_turns_phrases),
        )
        # Sprint 57.93 (地基 A Slice 3 output-guardrail leg): output-ESCALATE
        # pre-delivery pause trigger. Registers on the OUTPUT chain at priority=5
        # so it runs BEFORE the default Toxicity (p10) / SensitiveInfo (p20)
        # detectors (_run_chain is fail-fast-first-non-PASS) — its ESCALATE on a
        # final answer containing the phrase wins; a non-matching answer PASSes
        # through to the defaults unchanged. The loop's pre-delivery gate pauses
        # the flagged answer BEFORE LLMResponded renders it.
        guardrail_engine.register(
            OutputKeywordEscalationGuardrail(escalate_output_phrases),
            priority=5,
        )

    # Sprint 57.98 A1 (US-5): build the Cat 10 verifier registry BEFORE the loop
    # and inject it into the ctor so the loop OWNS the in-loop verification gate
    # (the retired run_with_verification wrapper used to run it AROUND loop.run()).
    # Built only when enabled; the judge shares the CHEAP tier (profile.cheap,
    # 57.97) — it fires every request, the highest-value cheap-tier target, while
    # the user-facing action turn stays on profile.action. None → the gate is
    # dormant (byte-identical to a non-verified run). resume() now covers the
    # resumed continuation for free (the loop's shared _run_turns carries the gate).
    # Sprint 57.106 (C3): the tenant may override verification mode / judge template
    # / escalate-on-max. mode + escalate_on_max fall back to the env settings when
    # not set; the template override is honored ONLY when it names a shipped template
    # (list_templates() — an unknown name from a hand-edited meta_data row falls back
    # to the env default rather than crashing load_template at judge time; the admin
    # PUT rejects an unknown name with 422 up front).
    settings = get_settings()
    verification_mode = policy.verification_mode or settings.chat_verification_mode
    judge_template = settings.chat_verification_judge_template
    if (
        policy.verification_judge_template
        and policy.verification_judge_template in list_templates()
    ):
        judge_template = policy.verification_judge_template
    verification_escalate_on_max = (
        policy.verification_escalate_on_max
        if policy.verification_escalate_on_max is not None
        else settings.chat_verification_escalate_on_max
    )
    # Sprint 57.136: in-loop correction-context strategy (settings-only — no
    # per-tenant override, anti-AP-6). Unknown value → "keep" (byte-identical to
    # pre-57.136). See AgentLoopImpl correction_context_strategy.
    correction_context_strategy = settings.chat_verification_correction_strategy
    if correction_context_strategy not in ("keep", "summarize"):
        correction_context_strategy = "keep"
    verifier_registry: VerifierRegistry | None = None
    if verification_mode == "enabled":
        verifier_registry = make_chat_verifier_registry(profile.cheap, judge_template)

    # Sprint 57.101 B1: wire the between-turns injection inbox over the module
    # InjectionRegistry for this (tenant, session) so a mid-run POST /{id}/inject
    # reaches the loop. Built only when both ids are present (the chat path always
    # has them); None otherwise → the loop drain is a no-op (byte-identical to pre-57.101).
    message_inbox: QueueMessageInbox | None = None
    if session_id is not None and tenant_id is not None:
        message_inbox = QueueMessageInbox(get_default_injection_registry(), tenant_id, session_id)

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        # Sprint 57.98 A1 (US-5): the loop owns the Cat 10 gate (was the router's
        # run_with_verification wrapper). None → dormant gate.
        verifier_registry=verifier_registry,
        # Sprint 57.99 A2 (US-1): when True, a max-attempts verification failure
        # ESCALATEs to a human HITL pause (deliver-as-is on APPROVE, one coached
        # retry on REJECT-with-note) instead of the A1 verification_failed terminal.
        # Effective only with a registry + hitl_manager; default False = A1.
        # Sprint 57.106 (C3): per-tenant override (falls back to the env setting).
        verification_escalate_on_max=verification_escalate_on_max,
        # Sprint 57.136 §correction-context hygiene: keep (default) re-shows the
        # failed answer; summarize drops it to break self-conditioning.
        correction_context_strategy=correction_context_strategy,
        # Sprint 57.101 B1: the between-turns injection inbox (None = no-op drain).
        message_inbox=message_inbox,
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
        message_store=message_store,
        todo_store=todo_store,
        tenant_id=tenant_id,
        error_policy=error_policy,
        retry_policy=retry_policy,
        circuit_breaker=circuit_breaker,
        error_budget=error_budget,
        error_terminator=error_terminator,
    )

    return loop


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
    model_policy: "ModelPolicy | None" = None,
    harness_policy: "HarnessPolicy | None" = None,
    user_id: "UUID | None" = None,
    system_prompt: str = DEMO_SYSTEM_PROMPT,
    tracer: "Tracer | None" = None,
    subagent_event_emitter: "SubagentEventEmitter | None" = None,
    skill_registry: "SkillRegistry | None" = None,
    force_load_skill: str | None = None,
) -> AgentLoopImpl:
    """Dispatch to the per-mode builder. Single entry-point for the router.

    Sprint 57.98 A1 (US-5): returns the wired `AgentLoopImpl` — the per-mode
    builder injects the Cat 10 verifier registry into the loop ctor (the gate is
    in-loop now; the retired run_with_verification wrapper is gone).

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
            # Sprint 57.104 (C1): the router resolved the per-tenant model policy
            # (resolve_tenant_model_policy) and threads it here → the per-tenant
            # ModelProfile. None / echo path → env-only (byte-identical to 57.97).
            model_policy=model_policy,
            # Sprint 57.106 (C3): the per-tenant harness policy (escalate phrases /
            # tools / verification overrides + risky-action detector). None → the
            # system-default path (byte-identical to pre-57.106).
            harness_policy=harness_policy,
            user_id=user_id,
            system_prompt=system_prompt,
            # Sprint 57.113: thread the skill registry → build_real_llm_handler
            # advertises the skills in the system prompt + registers read_skill.
            skill_registry=skill_registry,
            # Sprint 57.115: the user-picked /skill-name (validated by the router
            # against skill_registry) → deterministic force-load. echo path never
            # receives it (force-load is real_llm-only, a structural no-op on echo).
            force_load_skill=force_load_skill,
            # Sprint 57.71 (A-4 Tier 0): thread the router's real tracer through
            # to the loop. echo_demo path is unaffected (no tracer arg).
            tracer=tracer,
            # Sprint 57.95 (Cat 11 → Cat 12 SSE relay): thread the subagent event
            # emitter so SubagentSpawned/Completed reach the SSE stream. echo_demo
            # builds no subagent dispatcher → the arg is simply not forwarded.
            subagent_event_emitter=subagent_event_emitter,
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
