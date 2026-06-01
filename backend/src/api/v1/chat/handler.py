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
Last Modified: 2026-06-01

Modification History (newest-first):
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
    from agent_harness.verification import VerifierRegistry
    from business_domain._service_factory import BusinessServiceFactory
    from platform_layer.governance.service_factory import ServiceFactory

# Phase 50.2 demo system prompt — instructs the model to use echo_tool when the
# user explicitly asks to "echo" something. Real LLM only.
DEMO_SYSTEM_PROMPT = (
    "You are a Sprint 50.2 demonstration agent. When the user asks you to "
    "'echo' some text, you MUST call the `echo_tool` function with that text "
    "as the `text` argument, then return the tool's output verbatim as your "
    "final answer. Do not paraphrase. For any other request, answer directly."
)


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
    # production chat path. Cat 5 works standalone (no memory_provider yet; Day 2).
    prompt_builder = make_chat_prompt_builder(chat_client)
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

    loop = AgentLoopImpl(
        chat_client=chat_client,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        system_prompt=DEMO_SYSTEM_PROMPT,
        max_turns=8,
        hitl_manager=hitl_manager,
        hitl_timeout_s=hitl_timeout_s,
        guardrail_engine=build_default_guardrail_engine(),
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
        )
    raise ValueError(f"Unsupported mode: {mode!r}")


def _hitl_enabled() -> bool:
    """Feature toggle. Default ON; explicit `HITL_ENABLED=false` disables wiring."""
    return os.environ.get("HITL_ENABLED", "true").strip().lower() != "false"
