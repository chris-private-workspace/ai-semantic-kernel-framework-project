"""Category 2: Tool Layer — production registry + executor + sandbox + 6 built-in tools.

Sprint 51.1 (Day 5): InMemoryToolRegistry / InMemoryToolExecutor /
make_echo_executor have been removed (CARRY-017 closeout). All consumers
should use ToolRegistryImpl + ToolExecutorImpl directly, or call
register_builtin_tools() / business_domain.make_default_executor().
"""

from collections.abc import Awaitable, Callable
from typing import Any

# Sprint 52.5 P0 #18: handlers may take EITHER (call) or (call, context).
# Mirror the Union from tools/executor.py so dict[str, ToolHandler] accepts
# both arities. Single-arg legacy handlers continue to work; new handlers
# (memory_search/write/placeholder) supply the 2-arg form.
from agent_harness._contracts import ExecutionContext, ToolCall
from agent_harness.tools._abc import ToolExecutor, ToolRegistry
from agent_harness.tools._error_taxonomy import (
    ErrorTaxonomy,
    classify_tool_error,
    render_reflection,
    tool_error_reflection_enabled,
)
from agent_harness.tools.echo_tool import ECHO_TOOL_SPEC, echo_handler, make_echo_executor
from agent_harness.tools.exec_tools import (
    PYTHON_SANDBOX_SPEC,
    make_python_sandbox_handler,
)
from agent_harness.tools.executor import ToolExecutorImpl
from agent_harness.tools.hitl_tools import (
    REQUEST_APPROVAL_SPEC,
    make_request_approval_handler,
    request_approval_handler,
)
from agent_harness.tools.memory_tools import (
    MEMORY_SEARCH_SPEC,
    MEMORY_TOOL_SPECS,
    MEMORY_WRITE_SPEC,
    make_memory_search_handler,
    make_memory_write_handler,
    memory_placeholder_handler,
)
from agent_harness.tools.registry import ToolRegistryImpl
from agent_harness.tools.sandbox import (
    SandboxBackend,
    SandboxResult,
    SubprocessSandbox,
)
from agent_harness.tools.search_tools import (
    WEB_SEARCH_SPEC,
    WebSearchConfigError,
    make_web_search_handler,
)
from agent_harness.tools.todo_tools import (
    WRITE_TODOS_SPEC,
    make_write_todos_handler,
)

ToolHandler = (
    Callable[[ToolCall], Awaitable[str | dict[str, Any]]]
    | Callable[[ToolCall, ExecutionContext], Awaitable[str | dict[str, Any]]]
)


def register_builtin_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    sandbox_backend: SandboxBackend | None = None,
    memory_retrieval: object | None = None,
    memory_layers: dict[str, object] | None = None,
) -> None:
    """Register 6 built-in ToolSpecs + handlers (echo + python_sandbox + web_search +
    request_approval + memory_search/write).

    `handlers` is mutated in place — caller passes a (possibly pre-populated)
    handlers dict that will receive the new entries. Duplicate registration
    raises via ToolRegistryImpl.register; caller is responsible for ensuring
    a clean registry.

    Memory handler wiring (51.2 Day 4):
      - If both `memory_retrieval` and `memory_layers` are provided, real
        handlers route into Cat 3 (MemoryRetrieval.search +
        MemoryLayer.write).
      - Otherwise, falls back to memory_placeholder_handler which returns
        an error JSON. Phase 51.2 Day 4 unblocks the real path; production
        deployment must wire both kwargs.

    The kwargs are typed as `object | None` here to avoid a registry-level
    import cycle (agent_harness.tools -> agent_harness.memory.retrieval ->
    agent_harness._contracts is fine, but importing MemoryRetrieval at this
    module would tighten coupling unnecessarily). The factory functions in
    memory_tools.py do the proper isinstance routing.
    """
    registry.register(ECHO_TOOL_SPEC)
    handlers["echo_tool"] = echo_handler

    registry.register(PYTHON_SANDBOX_SPEC)
    handlers["python_sandbox"] = make_python_sandbox_handler(sandbox_backend)

    registry.register(WEB_SEARCH_SPEC)
    handlers["web_search"] = make_web_search_handler()

    registry.register(REQUEST_APPROVAL_SPEC)
    handlers["request_approval"] = request_approval_handler

    # Memory tools: real handlers if Cat 3 backend wired, else placeholder
    real_memory_wired = memory_retrieval is not None and memory_layers is not None
    if real_memory_wired:
        # Imports postponed to keep this module's load graph minimal
        from agent_harness.memory import MemoryLayer, MemoryRetrieval

        if not isinstance(memory_retrieval, MemoryRetrieval):
            raise TypeError("memory_retrieval must be a MemoryRetrieval instance")
        # Validate each layer is a MemoryLayer subclass instance
        validated_layers: dict[str, MemoryLayer] = {}
        for scope, layer in (memory_layers or {}).items():
            if not isinstance(layer, MemoryLayer):
                raise TypeError(f"memory_layers[{scope!r}] must be a MemoryLayer instance")
            validated_layers[scope] = layer

        registry.register(MEMORY_SEARCH_SPEC)
        handlers["memory_search"] = make_memory_search_handler(memory_retrieval)
        registry.register(MEMORY_WRITE_SPEC)
        handlers["memory_write"] = make_memory_write_handler(validated_layers)
    else:
        for spec in MEMORY_TOOL_SPECS:
            registry.register(spec)
            handlers[spec.name] = memory_placeholder_handler


__all__ = [
    "ECHO_TOOL_SPEC",
    "ErrorTaxonomy",
    "MEMORY_SEARCH_SPEC",
    "MEMORY_TOOL_SPECS",
    "MEMORY_WRITE_SPEC",
    "PYTHON_SANDBOX_SPEC",
    "REQUEST_APPROVAL_SPEC",
    "SandboxBackend",
    "SandboxResult",
    "SubprocessSandbox",
    "ToolExecutor",
    "ToolExecutorImpl",
    "ToolHandler",
    "ToolRegistry",
    "ToolRegistryImpl",
    "WEB_SEARCH_SPEC",
    "WRITE_TODOS_SPEC",
    "WebSearchConfigError",
    "classify_tool_error",
    "echo_handler",
    "make_echo_executor",
    "make_memory_search_handler",
    "make_memory_write_handler",
    "make_python_sandbox_handler",
    "make_request_approval_handler",
    "make_web_search_handler",
    "make_write_todos_handler",
    "memory_placeholder_handler",
    "register_builtin_tools",
    "render_reflection",
    "request_approval_handler",
    "tool_error_reflection_enabled",
]
