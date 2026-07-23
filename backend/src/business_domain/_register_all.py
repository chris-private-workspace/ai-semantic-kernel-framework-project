"""
File: backend/src/business_domain/_register_all.py
Purpose: One-call aggregator registering all 5 business domain tools (18 ToolSpec total).
Category: Business domain / aggregator
Scope: Phase 51 / Sprint 51.0 Day 3.5

Description:
    `register_all_business_tools(registry, handlers, *, mock_url)` calls each
    domain's register_<domain>_tools function in sequence. Used by:
    - runtime/workers/agent_loop_worker.py — Day 4 worker startup hook (51.0)
    - api/v1/chat/handler.py — chat dev mode default tools (51.0)
    - tests/integration/test_business_tools_via_registry.py — Day 4 verify

    Design: each domain's register_*_tools mutates the same registry + handlers
    dict. Order doesn't matter (no inter-domain dependencies), but established
    here as patrol -> correlation -> rootcause -> audit -> incident matching
    08b-business-tools-spec.md §Domain 1-5 numbering.

Lifecycle:
    Sprint 55 Phase: when real enterprise integrations replace mock_executors,
    register_all_business_tools function signature stays the same — only
    each domain's mock_executor.py gets swapped.

Created: 2026-04-30 (Sprint 51.0 Day 3)
Last Modified: 2026-07-23

Modification History:
    - 2026-07-23: Sprint 57.167 — mark mock-mode business results `_mock` (de-Potemkin 1)
    - 2026-06-26: Sprint 57.145 — opt-in knowledge_root (registers knowledge_search tool)
    - 2026-06-24: Sprint 57.140 — opt-in todo_store (registers write_todos task-primitive tool)
    - 2026-06-18: FIX-033 — chat python_sandbox → Docker default_sandbox() (Win Selector fail)
    - 2026-06-15: Sprint 57.118 — opt-in skill_registry also registers run_skill_script (exec)
    - 2026-06-13: Sprint 57.113 — opt-in skill_registry (registers read_skill lazy-load tool)
    - 2026-06-12: Sprint 57.107 (B3) — opt-in handoff_targets (registers spec-only handoff)
    - 2026-06-11: Sprint 57.102 (B2a) — opt-in teammate_mailbox (registers send_to_parent)
    - 2026-06-01: Sprint 57.64 Day 2 — make_default_executor opt-in Cat 3 + Cat 11 deps
    - 2026-05-04: (Sprint 55.2 Day 3.1) Uniform mode/factory_provider threading
      to all 5 register_*_tools (was incident-only in 55.1; closes
      AD-BusinessDomainPartialSwap-1 at the aggregator layer).
    - 2026-05-04: (Sprint 55.1 Day 3) Added mode + factory_provider kwargs.
    - 2026-04-30: Initial creation (Sprint 51.0 Day 3).
"""

from __future__ import annotations

import functools
import json
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from agent_harness._contracts import AgentSpec, SubagentFailurePolicy, ToolCall
from agent_harness.observability import Tracer
from agent_harness.skills import (
    READ_SKILL_TOOL_SPEC,
    RUN_SKILL_SCRIPT_TOOL_SPEC,
    make_read_skill_handler,
    make_run_skill_script_handler,
)
from agent_harness.subagent import (
    make_handoff_spec,
    make_send_to_parent_tool,
    make_task_spawn_tool,
)
from agent_harness.tools import (
    WRITE_TODOS_SPEC,
    ToolExecutorImpl,
    ToolHandler,
    ToolRegistry,
    ToolRegistryImpl,
    make_write_todos_handler,
    register_builtin_tools,
)
from agent_harness.tools.echo_tool import ECHO_TOOL_SPEC, echo_handler
from agent_harness.tools.note_tool import NOTE_TOOL_SPEC, note_handler
from agent_harness.tools.sandbox import SandboxBackend, default_sandbox

from ._service_factory import BusinessServiceFactory

if TYPE_CHECKING:
    from agent_harness.memory import MemoryLayer, MemoryRetrieval
    from agent_harness.skills import SkillRegistry
    from agent_harness.state_mgmt import TodoStore
    from agent_harness.subagent import DefaultSubagentDispatcher, MailboxStore

    from .knowledge.vector_index import KnowledgeVectorIndex
from .audit_domain.tools import register_audit_tools
from .correlation.tools import register_correlation_tools
from .incident.tools import register_incident_tools
from .knowledge import register_knowledge_tools
from .patrol.tools import register_patrol_tools
from .rootcause.tools import register_rootcause_tools

# Default mock backend URL (overridable per-call)
DEFAULT_MOCK_URL = "http://localhost:8001"


# === Shared python_sandbox backend (Docker when reachable) ===================
# Why (drive-through 2026-06-18 / FIX-033): the chat 主流量 wired python_sandbox to the
# LEGACY SubprocessSandbox (register_builtin_tools default). On Windows uvicorn's
# SelectorEventLoop, SubprocessSandbox.execute's asyncio.create_subprocess_exec raises
# NotImplementedError (empty message) at 0ms -> surfaced as "unknown tool error", so
# python_sandbox never ran on chat. default_sandbox() returns DockerSandbox when the
# daemon is reachable (loop-agnostic: docker SDK via asyncio.to_thread) and falls back to
# SubprocessSandbox on hosts without Docker (CI parity preserved). W4P-3 audit already
# mandates Docker for production; SubprocessSandbox is "decorative on Windows".
# Process-wide singleton (mirrors skills/tool.py) probes Docker once, not per request.
_shared_sandbox_singleton: SandboxBackend | None = None


def _get_shared_sandbox() -> SandboxBackend:
    """Return the process-wide python_sandbox backend (Docker when reachable, else fallback).

    Sprint 57.137 (AD-Guardrail-Detect-To-Restrict): reads SANDBOX_REQUIRE_ISOLATION
    — when set, a Docker-less host fails closed (refusing _FailClosedSandbox) instead
    of silently degrading to the production-unsafe SubprocessSandbox. Default OFF
    keeps the dev/CI fallback byte-unchanged.
    """
    global _shared_sandbox_singleton
    if _shared_sandbox_singleton is None:
        from core.config import get_settings

        _shared_sandbox_singleton = default_sandbox(
            require_isolation=get_settings().sandbox_require_isolation
        )
    return _shared_sandbox_singleton


def register_all_business_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    mock_url: str = DEFAULT_MOCK_URL,
    mode: str = "mock",
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
) -> None:
    """Register all 18 business domain ToolSpecs + 18 handlers.

    Sprint 55.1 (US-4): added `mode` + `factory_provider` kwargs (incident only).
    Sprint 55.2 (US-2): mode/factory_provider now uniformly threaded to all 5
        register_*_tools. AD-BusinessDomainPartialSwap-1 closed.
        - mode='mock' (default): 51.0 HTTP-backed pathway via mock_executor.
        - mode='service': production pathway. All 5 domains accept `mode='service'`
          + factory_provider. Per-domain handler split (1 real + N sentinel)
          documented in each domain's tools.py module docstring.

    Domain breakdown (per 08b-business-tools-spec.md):
      - patrol:        4 tools (08b §Domain 1) — service-aware (1 real: get_results)
      - correlation:   3 tools (08b §Domain 2) — service-aware (1 real: get_related)
      - rootcause:     3 tools (08b §Domain 3) — service-aware (1 real: diagnose)
      - audit:         3 tools (08b §Domain 4) — service-aware (1 real: query_logs)
      - incident:      5 tools (08b §Domain 5) — fully service-backed
      Total:          18 tools
    """
    if mode not in ("mock", "service"):
        raise ValueError(f"register_all_business_tools: invalid mode {mode!r}")
    if mode == "service" and factory_provider is None:
        raise ValueError("register_all_business_tools(mode='service') requires factory_provider")

    # Sprint 57.167: snapshot the keys so the mock-marking pass below can act on
    # EXACTLY the tools these 5 calls add (callers pass a `handlers` dict that
    # already holds echo / sandbox / memory / write_todos / knowledge).
    _before = set(handlers)

    # All 5 domains: mode-aware as of Sprint 55.2.
    register_patrol_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )
    register_correlation_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )
    register_rootcause_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )
    register_audit_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )
    register_incident_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )

    # de-Potemkin 1 (Sprint 57.167): mark every mock-sourced result so the agent
    # AND the human reading it can tell fabricated data from real. Applied by
    # KEY-DIFF — only the tools these 5 calls just added — so co-registered
    # builtins (echo / python_sandbox / memory / write_todos / knowledge) are
    # never touched. mode="service" wraps nothing → byte-identical to pre-57.167.
    if mode == "mock":
        for name in set(handlers) - _before:
            handlers[name] = _mark_mock_result(handlers[name])


# === Mock-result marking (de-Potemkin 1, Sprint 57.167) ===
# Why: `business_domain_mode` defaults to "mock", and NOTHING distinguished a
# fabricated answer from a real one (grep for [MOCK]/is_mock across the repo:
# 0 hits before this sprint) — the reality audit's most trust-damaging Potemkin.
#
# Why HERE and not in the 5 mock_executor.py: this is the one place that already
# knows `mode` and owns all 18 handlers; per-domain marking would be 10 edit
# sites over differing payload shapes, and a future service-mode swap would then
# need un-marking work. Here, `mode` alone decides.
#
# Why an in-JSON key and NOT a "[MOCK] " string prefix (Day-0 revision): every
# domain handler returns json.dumps(...), and integration tests + real consumers
# json.loads the result (test_business_tools_via_registry.py, 6+ sites). A prefix
# would emit `[MOCK] {...}` — no longer valid JSON. Marking inside keeps the
# payload parseable while staying visible in chat-v2's ToolBlock output.
#
# Why functools.wraps is load-bearing: ToolExecutorImpl detects 1-arg vs 2-arg
# handlers via inspect.signature (executor.py:320) — which follows __wrapped__.
# A naked `async def w(*args)` would report 0 positional params → a context-taking
# handler would be dispatched with the wrong arity.
_MOCK_PREFIX = "[MOCK] "
_MOCK_KEY = "_mock"


def _marked_payload(parsed: Any) -> Any:  # noqa: ANN401 — arbitrary decoded JSON
    """Add the mock marker to decoded JSON, preserving its shape.

    A dict gains the key. A LIST gains it on each dict element — list results are
    the common shape for the `*_list` / `*_query` tools (drive-through 2026-07-23
    found `mock_incident_list` returning a bare JSON array, so an object-only
    branch would have shipped those tools UNMARKED). Anything else (scalar, list
    of scalars) is returned untouched: there is nowhere to put the key, and
    reshaping would break callers that json.loads the result.
    """
    if isinstance(parsed, dict):
        return {**parsed, _MOCK_KEY: True}
    if isinstance(parsed, list):
        return [{**item, _MOCK_KEY: True} if isinstance(item, dict) else item for item in parsed]
    return parsed


def _mark_mock_result(handler: ToolHandler) -> ToolHandler:
    """Wrap a business handler so its result declares that it came from the mock backend."""

    @functools.wraps(handler)
    async def marked(*args: Any) -> Any:  # noqa: ANN401 — passthrough of ToolHandler's union
        result = await handler(*args)
        if isinstance(result, dict | list):
            return _marked_payload(result)
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except (ValueError, TypeError):
                return _MOCK_PREFIX + result
            marked_payload = _marked_payload(parsed)
            if marked_payload is parsed:
                # Nothing could be marked (scalar / list of scalars) — return the
                # original string rather than a re-serialized equivalent.
                return result
            return json.dumps(marked_payload)
        return result

    return marked


# === Subagent tool adapter (Cat 11 → Cat 2) ===
# Why: Cat 11's subagent tool factories (make_task_spawn_tool / as_tool_factory)
# return handlers with the signature `(args: dict) -> dict` (their native shape;
# subagent/tools.py:93 + modes/as_tool.py:94). The Cat 2 ToolExecutorImpl, by
# contrast, invokes handlers as `(call: ToolCall) -> str | dict` (executor.py:225).
# This thin adapter bridges the two WITHOUT modifying the Cat 11 module: it pulls
# `call.arguments` into the dict the subagent handler expects and JSON-encodes the
# returned dict (the executor would otherwise str()-coerce it into a non-JSON
# repr). Lives in the registration layer (not agent_harness) so the two category
# owners stay decoupled — no cross-category hashing.
_SubagentDictHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def _adapt_subagent_handler(dict_handler: _SubagentDictHandler) -> ToolHandler:
    """Wrap a Cat 11 `(dict) -> dict` handler as a Cat 2 `(ToolCall) -> str` handler."""

    async def adapted(call: ToolCall) -> str:
        result = await dict_handler(dict(call.arguments))
        return json.dumps(result)

    return adapted


def make_default_executor(
    *,
    mock_url: str = DEFAULT_MOCK_URL,
    tracer: Tracer | None = None,
    mode: str | None = None,
    factory_provider: Callable[[], BusinessServiceFactory] | None = None,
    memory_retrieval: "MemoryRetrieval | None" = None,
    memory_layers: "dict[str, MemoryLayer] | None" = None,
    subagent_dispatcher: "DefaultSubagentDispatcher | None" = None,
    parent_session_id: UUID | None = None,
    teammate_mailbox: "MailboxStore | None" = None,
    handoff_targets: Sequence[str] | None = None,
    subagent_failure_policy: SubagentFailurePolicy = "fail_soft",
    skill_registry: "SkillRegistry | None" = None,
    todo_store: "TodoStore | None" = None,
    knowledge_root: str | None = None,
    knowledge_vector_index: "KnowledgeVectorIndex | None" = None,
) -> tuple[ToolRegistryImpl, ToolExecutorImpl]:
    """Build a registry+executor pair with echo_tool + 18 business tools (19 total).

    Sprint 51.1 Day 5: switched from InMemoryToolRegistry / InMemoryToolExecutor
    to production Cat 2 implementations (ToolRegistryImpl + ToolExecutorImpl
    with JSONSchema validation + concurrency-aware batch; tool gating (HITL / risk /
    destructive) is owned by the loop's _cat9 + per-tenant HITLPolicy since 57.124).

    Sprint 55.1 (US-4): added `mode` + `factory_provider`. When `mode is None`,
    settings.business_domain_mode (env: BUSINESS_DOMAIN_MODE) is read.
    Explicit kwarg wins over env (test override path).

    Sprint 57.64 Day 2: added OPT-IN Cat 3 memory deps + Cat 11 subagent dispatcher.
    Both are backward-compatible — when absent, the registry is byte-identical to
    the 55.2 behavior (echo + 18 business tools only). When present:

      - memory_retrieval + memory_layers (BOTH required together) → calls
        ``register_builtin_tools(registry, handlers, memory_retrieval=...,
        memory_layers=...)`` which adds python_sandbox + web_search +
        request_approval + the REAL memory_search / memory_write handlers (NOT
        the placeholder stub; AP-4 Potemkin guard). Echo is re-registered by
        register_builtin_tools, so when memory deps are present echo is NOT
        pre-registered here (avoids the ToolRegistryImpl duplicate-name raise).
      - subagent_dispatcher → registers the Cat 11 `task_spawn` tool (FORK /
        TEAMMATE via make_task_spawn_tool) + one AS_TOOL wrapper
        (``agent_researcher`` via dispatcher.as_tool_factory). Requires
        `parent_session_id` for task_spawn's parent attribution.
      - handoff_targets (Sprint 57.107 B3) → registers the SPEC-ONLY `handoff`
        tool (make_handoff_spec): the loop's output classifier intercepts the
        tool_call (stop_reason="handoff") before execution and the platform
        layer boots the child session. None = tool absent (per-tenant
        handoff_enabled=false / echo / child executors).

    Args:
        mock_url: Override for the mock_services backend URL.
        tracer: Optional Tracer (defaults to NoOp via ToolExecutorImpl).
        mode: 'mock' / 'service' / None (read settings).
        factory_provider: required when mode resolves to 'service'.
        memory_retrieval: Cat 3 retrieval coordinator (opt-in; pair with memory_layers).
        memory_layers: Cat 3 scope→MemoryLayer map (opt-in; pair with memory_retrieval).
        subagent_dispatcher: Cat 11 dispatcher (opt-in; FORK/TEAMMATE/AS_TOOL tools).
        parent_session_id: required when subagent_dispatcher is supplied (task_spawn).
        teammate_mailbox: Cat 11 (B2a) mailbox for the teammate child's send_to_parent
            tool (opt-in; requires parent_session_id). Set only when building the
            teammate child executor (NOT the parent / FORK child).
        handoff_targets: suggested handoff targets for the spec-only `handoff`
            tool's description (opt-in; parent executor only — children cannot
            hand off, depth-bound by design).

    Returns:
        (registry, executor) — wired with the tools selected by the opt-in deps.
    """
    if mode is None:
        from core.config import get_settings

        mode = get_settings().business_domain_mode

    registry = ToolRegistryImpl()
    handlers: dict[str, ToolHandler] = {}

    memory_wired = memory_retrieval is not None and memory_layers is not None
    if memory_wired:
        # register_builtin_tools registers echo + python_sandbox + web_search +
        # request_approval + REAL memory tools (since both memory deps present).
        # `memory_layers` is widened to dict[str, object] to match the
        # register_builtin_tools signature (typed `object` there to avoid a
        # Cat 2 → Cat 3 import cycle; it isinstance-validates each layer at runtime).
        widened_layers: dict[str, object] = dict(memory_layers or {})
        register_builtin_tools(
            registry,
            handlers,
            memory_retrieval=memory_retrieval,
            memory_layers=widened_layers,
            sandbox_backend=_get_shared_sandbox(),
        )
    else:
        # echo_tool (50.1 built-in for bring-up tests; migrated out of _inmemory in 51.1)
        registry.register(ECHO_TOOL_SPEC)
        handlers["echo_tool"] = echo_handler

    # Sprint 57.92 (地基 A Slice 3 leg 2): note_tool — a NON-escalate deterministic
    # demo tool (mirror of echo_tool minus CHAT_HITL_ESCALATE_TOOLS) so a
    # between-turns boundary is reachable on 主流量: turn 0 runs note_tool
    # end-to-end INSIDE the loop → turn_count → 1 → the between-turns gate fires
    # at the top of turn 1 on note_tool's deterministic output. Registered
    # unconditionally (both branches above register echo; this adds note once,
    # regardless of memory deps).
    registry.register(NOTE_TOOL_SPEC)
    handlers["note_tool"] = note_handler

    # 18 business tools
    register_all_business_tools(
        registry,
        handlers,
        mock_url=mock_url,
        mode=mode,
        factory_provider=factory_provider,
    )

    # Sprint 57.107 (B3): the spec-only `handoff` trigger tool. The handler never
    # runs (loop-intercepted); registration is the per-tenant on/off gate.
    if handoff_targets is not None:
        handoff_spec, handoff_handler = make_handoff_spec(suggested_targets=handoff_targets)
        registry.register(handoff_spec)
        handlers[handoff_spec.name] = _adapt_subagent_handler(handoff_handler)

    # Sprint 57.113: the read_skill lazy-load tool (opt-in). When a skill registry
    # is supplied, register read_skill so the model can load a skill's full
    # instructions on demand (the system prompt advertises them cheaply via
    # render_catalog_block). The chat path's registry-derived permission matrix
    # auto-grants a PASS rule (handler.py builds rules from registry.list()).
    #
    # Sprint 57.118: run_skill_script runs a system-bundled skill's SERVER-controlled
    # executable script (Skill.script) via the existing SandboxBackend. The handler
    # resolves default_sandbox() lazily (process-wide singleton in skills/tool.py) so
    # this per-request build does not probe Docker. Same risk-blind matrix → auto-PASS.
    if skill_registry is not None:
        registry.register(READ_SKILL_TOOL_SPEC)
        handlers["read_skill"] = make_read_skill_handler(skill_registry)
        registry.register(RUN_SKILL_SCRIPT_TOOL_SPEC)
        handlers["run_skill_script"] = make_run_skill_script_handler(skill_registry)

    # Sprint 57.140: the write_todos task-primitive tool (opt-in). When a per-request
    # session todo store is supplied (make_chat_todo_store, all-three-or-nothing), the
    # agent records/updates a whole structured plan that survives across sends (the
    # durable task spine). risk=LOW + destructive=False → the registry-derived matrix
    # auto-PASSes it (no HITL prompt), so the agent maintains the list freely in-loop.
    if todo_store is not None:
        registry.register(WRITE_TODOS_SPEC)
        handlers["write_todos"] = make_write_todos_handler(todo_store)

    # Sprint 57.145: the knowledge_search tool — the platform's FIRST real external
    # data-source connector (opt-in). When a knowledge_root is supplied, register a
    # read-only search tool over a LocalDocsConnector(root). risk=LOW + read_only →
    # the registry-derived matrix auto-PASSes it (no HITL), so the agent searches the
    # company docs folder freely and grounds answers in real snippets + source paths.
    # A missing/invalid root (connector raises ValueError) → skip registration so the
    # agent degrades gracefully (knowledge_search absent), never breaking the build.
    if knowledge_root:
        try:
            register_knowledge_tools(
                registry,
                handlers,
                docs_root=knowledge_root,
                vector_index=knowledge_vector_index,
            )
        except ValueError:
            pass

    # Cat 11 (A-3a) subagent tools — FORK/TEAMMATE via task_spawn + one AS_TOOL
    # wrapper. HANDOFF is loop-intercepted (spec-only tool above; Sprint 57.107).
    if subagent_dispatcher is not None:
        if parent_session_id is None:
            raise ValueError(
                "make_default_executor(subagent_dispatcher=...) requires parent_session_id"
            )
        task_spec, task_handler = make_task_spawn_tool(
            dispatcher=subagent_dispatcher,
            parent_session_id=parent_session_id,
            # Sprint 57.110 (B4): tenant-resolved spawn failure semantics (the
            # caller resolves HarnessPolicy.subagent_failure_policy; LLM cannot
            # choose it — governance belongs to the tenant).
            failure_policy=subagent_failure_policy,
        )
        registry.register(task_spec)
        handlers[task_spec.name] = _adapt_subagent_handler(task_handler)

        # One AS_TOOL subagent role exposed by default (agents-as-tools pattern).
        as_tool_spec, as_tool_handler = subagent_dispatcher.as_tool_factory(
            AgentSpec(role="researcher")
        )
        registry.register(as_tool_spec)
        handlers[as_tool_spec.name] = _adapt_subagent_handler(as_tool_handler)

    # Sprint 57.102 (B2a): the TEAMMATE child loop's send_to_parent tool. Opt-in like
    # subagent_dispatcher above (same pattern): when teammate_mailbox is given, register
    # send_to_parent so the teammate child can report to its parent mid-loop (the
    # TeammateExecutor drains the parent mailbox + folds the reports into the summary).
    # Registered ONLY on the teammate child executor (the handler passes teammate_mailbox
    # only when building _make_teammate_child_loop) — NOT on the parent / FORK child.
    if teammate_mailbox is not None:
        if parent_session_id is None:
            raise ValueError(
                "make_default_executor(teammate_mailbox=...) requires parent_session_id"
            )
        sp_spec, sp_handler = make_send_to_parent_tool(
            mailbox=teammate_mailbox,
            parent_session_id=parent_session_id,
        )
        registry.register(sp_spec)
        handlers[sp_spec.name] = _adapt_subagent_handler(sp_handler)

    # ToolExecutorImpl handler signature is `Callable[[ToolCall], Awaitable[str]]`;
    # business handlers return `str | dict` and ToolExecutorImpl coerces to str.
    executor = ToolExecutorImpl(
        registry=registry,
        handlers=handlers,
        tracer=tracer,
    )
    return registry, executor


__all__ = [
    "register_all_business_tools",
    "make_default_executor",
    "DEFAULT_MOCK_URL",
]
