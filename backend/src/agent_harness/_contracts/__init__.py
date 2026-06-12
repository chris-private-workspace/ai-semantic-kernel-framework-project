"""
File: backend/src/agent_harness/_contracts/__init__.py
Purpose: Unified re-export of all single-source cross-category types.
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Usage:
    from agent_harness._contracts import (
        Message, ChatRequest, ChatResponse, StopReason,
        ToolSpec, ToolCall, ToolResult, ToolAnnotations, ConcurrencyPolicy, ToolHITLPolicy,
        LoopState, TransientState, DurableState, StateVersion,
        LoopEvent, ToolCallRequested, ToolCallExecuted,
        MemoryHint,
        PromptArtifact, CacheBreakpoint,
        VerificationResult,
        SubagentBudget, SubagentResult, SubagentMode,
        TraceContext, MetricEvent, SpanCategory,
        ApprovalRequest, ApprovalDecision, HITLPolicy, RiskLevel, DecisionType,
    )

DO NOT redefine these types anywhere else; always import from here.

Owner: 17-cross-category-interfaces.md §1
Created: 2026-04-29 (Sprint 49.1)
"""

from agent_harness._contracts.cache import CachePolicy
from agent_harness._contracts.chat import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    ContentBlock,
    Message,
    StopReason,
    TokenUsage,
    ToolCall,
)
from agent_harness._contracts.compaction import (
    CompactionResult,
    CompactionStrategy,
)
from agent_harness._contracts.errors import (
    AuthenticationError,
    ErrorContext,
    MissingDataError,
    ToolExecutionError,
)
from agent_harness._contracts.events import (
    AgentHandoff,
    ApprovalReceived,
    ApprovalRequested,
    ContextCompacted,
    ErrorRetried,
    GuardrailTriggered,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    LoopTerminated,
    MemoryAccessed,
    MessageInjected,
    MetricRecorded,
    PromptBuilt,
    SpanEnded,
    SpanStarted,
    StateCheckpointed,
    SubagentChildEvent,
    SubagentCompleted,
    SubagentSpawned,
    Thinking,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    TripwireTriggered,
    TurnStarted,
    VerificationFailed,
    VerificationPassed,
)
from agent_harness._contracts.hitl import (
    ApprovalDecision,
    ApprovalRequest,
    DecisionType,
    HITLPolicy,
    RiskLevel,
)
from agent_harness._contracts.inbox import MessageInbox
from agent_harness._contracts.memory import MemoryHint
from agent_harness._contracts.observability import (
    MetricEvent,
    SpanCategory,
    TraceContext,
)
from agent_harness._contracts.prompt import PromptArtifact
from agent_harness._contracts.state import (
    DurableState,
    LoopState,
    StateVersion,
    TransientState,
)
from agent_harness._contracts.subagent import (
    SUBAGENT_FAILURE_POLICIES,
    AgentSpec,
    ChildLoopFactory,
    SubagentBudget,
    SubagentFailurePolicy,
    SubagentMode,
    SubagentResult,
    TeammateChildLoopFactory,
    TeammateInboxScope,
)
from agent_harness._contracts.tools import (
    ConcurrencyPolicy,
    ExecutionContext,
    ToolAnnotations,
    ToolHITLPolicy,
    ToolResult,
    ToolSpec,
)
from agent_harness._contracts.verification import VerificationResult

__all__ = [
    # chat
    "Message",
    "ChatRequest",
    "ChatResponse",
    "StopReason",
    "ContentBlock",
    "ToolCall",
    "TokenUsage",
    "CacheBreakpoint",
    # compaction (Cat 4)
    "CompactionStrategy",
    "CompactionResult",
    # cache (Cat 4)
    "CachePolicy",
    # errors (Cat 8)
    "ErrorContext",
    "AuthenticationError",
    "MissingDataError",
    "ToolExecutionError",
    # tools
    "ToolSpec",
    "ToolResult",
    "ToolAnnotations",
    "ConcurrencyPolicy",
    "ToolHITLPolicy",
    "ExecutionContext",
    # state
    "LoopState",
    "TransientState",
    "DurableState",
    "StateVersion",
    # events
    "LoopEvent",
    "LoopStarted",
    "TurnStarted",
    "LLMRequested",
    "LLMResponded",
    "Thinking",
    "LoopCompleted",
    "ToolCallRequested",
    "ToolCallExecuted",
    "ToolCallFailed",
    "MemoryAccessed",
    "ContextCompacted",
    "PromptBuilt",
    "StateCheckpointed",
    "ErrorRetried",
    "LoopTerminated",
    "GuardrailTriggered",
    "TripwireTriggered",
    "VerificationPassed",
    "VerificationFailed",
    "SubagentSpawned",
    "SubagentCompleted",
    "SubagentChildEvent",
    "AgentHandoff",
    "ApprovalRequested",
    "ApprovalReceived",
    "MessageInjected",
    "SpanStarted",
    "SpanEnded",
    "MetricRecorded",
    # inbox (Cat 1 — between-turns injection)
    "MessageInbox",
    # memory
    "MemoryHint",
    # prompt
    "PromptArtifact",
    # verification
    "VerificationResult",
    # subagent
    "SUBAGENT_FAILURE_POLICIES",
    "SubagentBudget",
    "SubagentFailurePolicy",
    "SubagentResult",
    "SubagentMode",
    "AgentSpec",
    "ChildLoopFactory",
    "TeammateChildLoopFactory",
    "TeammateInboxScope",
    # observability
    "TraceContext",
    "MetricEvent",
    "SpanCategory",
    # hitl
    "ApprovalRequest",
    "ApprovalDecision",
    "HITLPolicy",
    "RiskLevel",
    "DecisionType",
]
