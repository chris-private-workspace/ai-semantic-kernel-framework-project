"""
File: backend/src/adapters/azure_openai/adapter.py
Purpose: AzureOpenAIAdapter — concrete ChatClient implementation for Azure OpenAI.
Category: Adapters / Azure OpenAI
Scope: Phase 49 / Sprint 49.4

Description:
    Implements all 6 ChatClient ABC methods using Azure OpenAI's Python SDK.
    All openai SDK imports are confined to this file + error_mapper.py +
    tool_converter.py — agent_harness/ stays SDK-free per llm-provider-neutrality.md.

    Token counting uses tiktoken (OpenAI's official tokenizer) which matches
    Azure's billing tokenizer for GPT family models.

    Cancellation support: asyncio.CancelledError propagates through the SDK call
    and the adapter cleans up — caller decides retry vs surface.

    Tracing: trace_context (range cat 12) is logged as span attributes when
    provided; full OTel hookup happens in Day 3 setup.py.

Created: 2026-04-29 (Sprint 49.4)
Last Modified: 2026-05-01

Modification History (newest-first):
    - 2026-06-04: Sprint 57.79 — gpt-5.x max_completion_tokens param branch (C-11 billing gap 2)
    - 2026-05-01: Compute deterministic prompt_cache_key from CacheBreakpoint
        section_ids (Sprint 52.2 Day 3.5) and forward via extra_body to Azure
        OpenAI for auto-prompt-caching. Stream path mirrors chat. Helper
        `_compute_prompt_cache_key` returns None when no section_ids → safe
        no-op for 51.1 callers / pre-PromptBuilder Loop fallback.
    - 2026-04-29: Initial creation (Sprint 49.4) — full ChatClient ABC implementation

Related:
    - chat_client.py — ABC contract owner
    - config.py / error_mapper.py / tool_converter.py — sibling helpers
    - adapters-layer.md (.claude/rules/) §5 步上架 SOP / §Azure OpenAI 特定細節
    - llm-provider-neutrality.md (.claude/rules/) — SDK confinement
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import TYPE_CHECKING, AsyncIterator, Literal

if TYPE_CHECKING:
    from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter
    from agent_harness.observability import Tracer

import tiktoken
from openai import AsyncAzureOpenAI

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StreamEvent
from adapters.azure_openai.config import AzureOpenAIConfig
from adapters.azure_openai.error_mapper import AzureOpenAIErrorMapper
from adapters.azure_openai.tool_converter import (
    azure_tool_call_to_neutral,
    messages_to_azure,
    tool_specs_to_azure,
)
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    Message,
    ToolSpec,
    TraceContext,
)
from agent_harness._contracts.chat import StopReason, TokenUsage

logger = logging.getLogger(__name__)


_AZURE_FINISH_REASON_MAP: dict[str, StopReason] = {
    "stop": StopReason.END_TURN,
    "tool_calls": StopReason.TOOL_USE,
    "length": StopReason.MAX_TOKENS,
    "content_filter": StopReason.SAFETY_REFUSAL,
    "function_call": StopReason.TOOL_USE,  # legacy
}


def _compute_prompt_cache_key(
    cache_breakpoints: list[CacheBreakpoint] | None,
) -> str | None:
    """Sprint 52.2 Day 3.5: Deterministic Azure OpenAI prompt_cache_key from breakpoints.

    Per plan §3.5: key = sha256(":".join(bp.section_id for bp with section_id)).
    Returns None when:
      - cache_breakpoints is None / empty
      - no breakpoints carry section_id (Cat 4 logical metadata absent)

    Azure OpenAI auto-caches prompts that share prompt_cache_key; deterministic
    derivation across turns means stable hits without manual cache management.
    """
    if not cache_breakpoints:
        return None
    section_ids = [bp.section_id for bp in cache_breakpoints if bp.section_id]
    if not section_ids:
        return None
    return hashlib.sha256(":".join(section_ids).encode("utf-8")).hexdigest()


def _max_tokens_param_name(model_name: str) -> str:
    """Return the token-cap kwarg name for an Azure model (C-11 billing gap 2).

    gpt-5.x rejects ``max_tokens`` (HTTP 400: "use ``max_completion_tokens``");
    gpt-4.x and earlier accept ``max_tokens``. Keyed off model_name (not
    deployment_name — deployment ids carry no model-generation guarantee), so
    model_name must reflect the real deployment generation.
    """
    return "max_completion_tokens" if model_name.startswith("gpt-5") else "max_tokens"


class AzureOpenAIAdapter(ChatClient):
    """Azure OpenAI ChatClient implementation."""

    def __init__(
        self,
        config: AzureOpenAIConfig | None = None,
        *,
        tracer: "Tracer | None" = None,
    ) -> None:
        self.config = config or AzureOpenAIConfig()
        self._client: AsyncAzureOpenAI | None = None
        self._tokenizer: tiktoken.Encoding | None = None
        # 52.1 Day 3.10: lazy Cat 4 token counter (replaces inline tiktoken loop)
        self._token_counter: "TiktokenCounter | None" = None
        # Sprint 52.5 P0 #16: tracer injection for the LLM-call span.
        # NoOpTracer is the lazy default used when no tracer is wired in
        # (unit tests + dev paths). Production wiring goes through
        # api/v1/chat/handler.py which builds an OTelTracer once per process.
        if tracer is None:
            from agent_harness.observability import NoOpTracer

            tracer = NoOpTracer()
        self._tracer: "Tracer" = tracer

    # -- lazy clients ------------------------------------------------------

    def _get_client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            if not self.config.is_configured():
                raise ValueError(
                    "AzureOpenAIConfig missing required env vars: "
                    "AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / "
                    "AZURE_OPENAI_DEPLOYMENT_NAME"
                )
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                api_version=self.config.api_version,
                azure_endpoint=self.config.endpoint,
                timeout=self.config.timeout_sec,
                max_retries=self.config.max_retries,
            )
        return self._client

    def _get_tokenizer(self) -> tiktoken.Encoding:
        if self._tokenizer is None:
            try:
                self._tokenizer = tiktoken.encoding_for_model(self.config.model_name)
            except KeyError:
                self._tokenizer = tiktoken.get_encoding("o200k_base")  # GPT-4o family
        return self._tokenizer

    # -- core: chat --------------------------------------------------------

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        """Single non-streaming completion.

        Sprint 52.5 P0 #16: wraps the LLM call in `tracer.start_span("llm_chat")`
        so the span hierarchy includes the SDK call as a child of the loop's
        outer span. Pre-refactor, audit W4P-1 found `trace_context` reached
        adapter (8 hits) but no `tracer.start_span` ever fired here — the
        adapter was a span-tree dead end.
        """
        # Lazy import — keeps module-load cost down for non-tracing test paths.
        from agent_harness._contracts import SpanCategory

        client = self._get_client()
        azure_messages = messages_to_azure(request.messages)
        azure_tools = tool_specs_to_azure(list(request.tools)) if request.tools else None

        if trace_context is not None:
            logger.debug(
                "azure_openai chat: trace_id=%s tenant=%s model=%s",
                trace_context.trace_id,
                trace_context.tenant_id,
                self.config.model_name,
            )

        async with self._tracer.start_span(
            name="llm_chat",
            category=SpanCategory.ORCHESTRATOR,
            trace_context=trace_context,
            attributes={
                "provider": "azure_openai",
                "model": self.config.model_name,
                "deployment": self.config.deployment_name,
                "stream": "false",
                "has_tools": "true" if azure_tools else "false",
            },
        ):
            try:
                kwargs: dict[str, object] = {
                    "model": self.config.deployment_name,
                    "messages": azure_messages,
                    "temperature": request.temperature,
                }
                if azure_tools:
                    kwargs["tools"] = azure_tools
                    kwargs["tool_choice"] = request.tool_choice
                if request.max_tokens is not None:
                    kwargs[_max_tokens_param_name(self.config.model_name)] = request.max_tokens
                # Sprint 52.2 Day 3.5: forward Cat 5 cache_breakpoints as Azure
                # OpenAI's deterministic prompt_cache_key (extra_body). Per plan §3.5:
                # key = sha256(":".join(bp.section_id for bp with section_id present)).
                # Azure OpenAI auto-caches prompts that share the same prompt_cache_key.
                cache_key = _compute_prompt_cache_key(cache_breakpoints)
                if cache_key is not None:
                    kwargs["extra_body"] = {"prompt_cache_key": cache_key}

                response = await client.chat.completions.create(**kwargs)  # type: ignore[call-overload]  # noqa: E501
            except asyncio.CancelledError:
                logger.info("azure_openai chat cancelled")
                raise
            except Exception as exc:  # noqa: BLE001
                raise AzureOpenAIErrorMapper.map(exc) from exc

            return self._parse_response(response)

    # -- core: stream ------------------------------------------------------

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Streaming completion. Returns async iterator of StreamEvent."""
        return self._stream_impl(
            request,
            cache_breakpoints=cache_breakpoints,
            trace_context=trace_context,
        )

    async def _stream_impl(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None,
    ) -> AsyncIterator[StreamEvent]:
        # Sprint 52.5 P0 #16: span wraps the full stream lifetime — opens
        # before the SDK request, stays open while consumer iterates, closes
        # when the generator is exhausted / cancelled / errors.
        from agent_harness._contracts import SpanCategory

        client = self._get_client()
        azure_messages = messages_to_azure(request.messages)
        azure_tools = tool_specs_to_azure(list(request.tools)) if request.tools else None

        async with self._tracer.start_span(
            name="llm_chat_stream",
            category=SpanCategory.ORCHESTRATOR,
            trace_context=trace_context,
            attributes={
                "provider": "azure_openai",
                "model": self.config.model_name,
                "deployment": self.config.deployment_name,
                "stream": "true",
                "has_tools": "true" if azure_tools else "false",
            },
        ):
            try:
                kwargs: dict[str, object] = {
                    "model": self.config.deployment_name,
                    "messages": azure_messages,
                    "temperature": request.temperature,
                    "stream": True,
                }
                if azure_tools:
                    kwargs["tools"] = azure_tools
                if request.max_tokens is not None:
                    kwargs[_max_tokens_param_name(self.config.model_name)] = request.max_tokens
                # Sprint 52.2 Day 3.5: stream path mirrors chat() prompt_cache_key.
                cache_key = _compute_prompt_cache_key(cache_breakpoints)
                if cache_key is not None:
                    kwargs["extra_body"] = {"prompt_cache_key": cache_key}

                stream = await client.chat.completions.create(**kwargs)  # type: ignore[call-overload]  # noqa: E501
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise AzureOpenAIErrorMapper.map(exc) from exc

            try:
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    delta = choice.delta

                    if delta.content:
                        yield StreamEvent(
                            event_type="content_delta",
                            payload={"text": delta.content},
                        )
                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            yield StreamEvent(
                                event_type="tool_call_delta",
                                payload={
                                    "id": getattr(tc_delta, "id", None),
                                    "name": (
                                        getattr(tc_delta.function, "name", None)
                                        if tc_delta.function
                                        else None
                                    ),
                                    "arguments_delta": (
                                        getattr(tc_delta.function, "arguments", None)
                                        if tc_delta.function
                                        else None
                                    ),
                                },
                            )
                    if choice.finish_reason:
                        stop = _AZURE_FINISH_REASON_MAP.get(
                            choice.finish_reason, StopReason.PROVIDER_ERROR
                        )
                        yield StreamEvent(
                            event_type="stop",
                            payload={"stop_reason": stop.value},
                        )
            except asyncio.CancelledError:
                logger.info("azure_openai stream cancelled mid-flight")
                raise
            except Exception as exc:  # noqa: BLE001
                raise AzureOpenAIErrorMapper.map(exc) from exc

    # -- token / pricing / capability --------------------------------------

    async def count_tokens(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> int:
        """Count tokens via Cat 4 TiktokenCounter (single-source per 17.md §2.1).

        Sprint 52.1 Day 3.10: previously this method had its own inline tiktoken
        loop (per_message_overhead=4, simplified schema serialisation). It now
        delegates to TiktokenCounter, the canonical Cat 4 implementation, with
        per_message_overhead=4 + per_request_overhead=0 to preserve the 51.1
        adapter contract (count([])==0 / single short message > 4).
        """
        counter = self._get_token_counter()
        return counter.count(messages=messages, tools=tools)

    def _get_token_counter(self) -> "TiktokenCounter":
        if self._token_counter is None:
            from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter

            self._token_counter = TiktokenCounter(
                model=self.config.model_name,
                # Preserve 51.1 adapter contract:
                # - count_tokens([]) == 0 (no per_request overhead on empty input;
                #   TiktokenCounter already short-circuits empty, but we also keep
                #   per_request_overhead at 0 for any future code path consistency)
                # - per_message overhead = 4 (matches the OpenAI cookbook value
                #   used by 51.1 adapter; tests in test_token_counting.py assume this)
                per_message_overhead=4,
                per_request_overhead=0,
            )
        return self._token_counter

    def get_pricing(self) -> PricingInfo:
        return PricingInfo(
            input_per_million=self.config.pricing_input_per_million,
            output_per_million=self.config.pricing_output_per_million,
            cached_input_per_million=self.config.pricing_cached_input_per_million,
        )

    def supports_feature(
        self,
        feature: Literal[
            "thinking",
            "caching",
            "vision",
            "audio",
            "computer_use",
            "structured_output",
            "parallel_tool_calls",
        ],
    ) -> bool:
        return {
            "thinking": self.config.supports_thinking,
            "caching": self.config.supports_caching,
            "vision": self.config.supports_vision,
            "audio": False,  # not currently supported by Azure GPT family in this adapter
            "computer_use": False,  # Anthropic-specific
            "structured_output": self.config.supports_structured_output,
            "parallel_tool_calls": self.config.supports_parallel_tool_calls,
        }[feature]

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_name=self.config.model_name,
            model_family=self.config.model_family,
            provider="azure_openai",
            context_window=self.config.context_window,
            max_output_tokens=self.config.max_output_tokens,
            knowledge_cutoff=None,
        )

    # -- response parsing --------------------------------------------------

    def _parse_response(self, response: object) -> ChatResponse:
        """Parse Azure OpenAI ChatCompletion response into neutral ChatResponse."""
        choices = getattr(response, "choices", [])
        if not choices:
            raise AzureOpenAIErrorMapper.map(RuntimeError("Azure OpenAI returned no choices"))

        choice = choices[0]
        msg = choice.message
        content = getattr(msg, "content", None) or ""
        finish = getattr(choice, "finish_reason", "stop") or "stop"
        stop_reason = _AZURE_FINISH_REASON_MAP.get(finish, StopReason.PROVIDER_ERROR)

        tool_calls = None
        if getattr(msg, "tool_calls", None):
            tool_calls = [azure_tool_call_to_neutral(tc) for tc in msg.tool_calls]
            stop_reason = StopReason.TOOL_USE

        usage_obj = getattr(response, "usage", None)
        usage = None
        if usage_obj is not None:
            cached = 0
            prompt_details = getattr(usage_obj, "prompt_tokens_details", None)
            if prompt_details is not None:
                cached = getattr(prompt_details, "cached_tokens", 0) or 0
            usage = TokenUsage(
                prompt_tokens=getattr(usage_obj, "prompt_tokens", 0),
                completion_tokens=getattr(usage_obj, "completion_tokens", 0),
                cached_input_tokens=cached,
                total_tokens=getattr(usage_obj, "total_tokens", 0),
            )

        return ChatResponse(
            model=getattr(response, "model", self.config.model_name),
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=usage,
        )

    # -- lifecycle ---------------------------------------------------------

    async def aclose(self) -> None:
        """Release the underlying httpx pool. Idempotent."""
        if self._client is not None:
            await self._client.close()
            self._client = None
