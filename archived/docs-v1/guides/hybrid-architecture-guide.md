# Hybrid MAF + Claude SDK Architecture Guide

> **Phase 13-14**: Hybrid Architecture for IPA Platform
> **Version**: 1.0.0
> **Last Updated**: 2026-01-03

---

## Overview

The IPA Platform implements a **Hybrid Architecture** that combines Microsoft Agent Framework (MAF) with Claude Agent SDK, enabling intelligent routing between structured workflows and conversational interactions.

### Architecture Goals

1. **Seamless Integration**: Unified execution layer for both MAF and Claude SDK
2. **Intelligent Routing**: Automatic detection of workflow vs. chat intent
3. **State Persistence**: Cross-framework checkpoint and recovery
4. **Risk-Driven HITL**: Human-in-the-loop decisions based on risk assessment
5. **Dynamic Mode Switching**: Real-time switching between execution modes

---

## Core Components

### 1. HybridOrchestratorV2

The central orchestrator that coordinates all hybrid operations.

```
┌─────────────────────────────────────────────────────────────┐
│                   HybridOrchestratorV2                       │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │IntentRouter │───→│Context Bridge│───→│UnifiedToolExec│   │
│  └─────────────┘    └──────────────┘    └───────────────┘   │
│         │                  │                    │            │
│         ▼                  ▼                    ▼            │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │Mode Switcher│    │  MAF Adapter │    │ Claude Client │   │
│  └─────────────┘    └──────────────┘    └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `WORKFLOW_MODE` | MAF-led structured execution | Multi-step workflows, approvals |
| `CHAT_MODE` | Claude SDK conversational | Interactive queries, exploration |
| `HYBRID_MODE` | Dynamic routing | Complex tasks requiring both |

#### Orchestrator Modes

| Mode | Description |
|------|-------------|
| `V1_COMPAT` | Backward compatibility with v1 API |
| `V2_FULL` | Full v2 features enabled |
| `V2_MINIMAL` | Lightweight execution without optional features |

### 2. IntentRouter

Analyzes user input to determine the appropriate execution mode.

```python
from src.integrations.hybrid.routing.intent_router import (
    IntentRouter,
    IntentSignal,
    RouterConfig,
)

# Create router with configuration
config = RouterConfig(
    workflow_keywords=["execute", "run workflow", "process"],
    chat_keywords=["explain", "help", "what is"],
    confidence_threshold=0.7,
)
router = IntentRouter(config)

# Route user input
result = router.route("Run the approval workflow for document #123")
# result.mode = ExecutionMode.WORKFLOW_MODE
# result.confidence = 0.92
```

### 3. ContextBridge

Synchronizes state between MAF and Claude SDK.

```python
from src.integrations.hybrid.context.bridge import ContextBridge

bridge = ContextBridge()

# Sync MAF state to Claude
claude_context = bridge.maf_to_claude(maf_state)

# Sync Claude state to MAF
maf_context = bridge.claude_to_maf(claude_state)

# Bidirectional sync
unified_context = bridge.sync_bidirectional(maf_state, claude_state)
```

### 4. UnifiedToolExecutor

Executes tools through Claude SDK regardless of origin.

```python
from src.integrations.hybrid.tools.unified_executor import UnifiedToolExecutor

executor = UnifiedToolExecutor()

# Register tools from different sources
executor.register_maf_tools(maf_tool_definitions)
executor.register_claude_tools(claude_tool_definitions)

# Execute tool call
result = await executor.execute(
    tool_name="search_documents",
    arguments={"query": "quarterly report"},
    context=execution_context,
)
```

---

## Execution Flow

### Standard Execution Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  IntentRouter   │──→ Analyze intent and confidence
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RiskAssessment  │──→ Evaluate operation risk
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
WORKFLOW   CHAT
 MODE      MODE
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│  MAF   │ │ Claude │
│Adapter │ │  SDK   │
└────┬───┘ └────┬───┘
     │         │
     └────┬────┘
          │
          ▼
    ┌───────────┐
    │ Checkpoint│──→ Persist state
    └─────┬─────┘
          │
          ▼
      Response
```

### Mode Switching Flow

```python
from src.integrations.hybrid.switching.switcher import (
    ModeSwitcher,
    SwitchTrigger,
    MigrationDirection,
)

switcher = ModeSwitcher()

# Detect switch trigger
trigger = switcher.detect_trigger(current_state, new_input)

if trigger.should_switch:
    # Create checkpoint before switch
    checkpoint = await switcher.create_switch_checkpoint(current_state)

    # Migrate state
    new_state = await switcher.migrate_state(
        source_state=current_state,
        direction=MigrationDirection.WORKFLOW_TO_CHAT,
    )

    # Continue in new mode
    result = await orchestrator.execute(new_input, mode=new_state.mode)
```

---

## Configuration

### OrchestratorConfig

```python
from src.integrations.hybrid.orchestrator_v2 import OrchestratorConfig

config = OrchestratorConfig(
    # Mode settings
    default_mode=ExecutionMode.HYBRID_MODE,
    orchestrator_mode=OrchestratorMode.V2_FULL,

    # Auto-switching
    auto_switch_enabled=True,
    switch_confidence_threshold=0.8,

    # Timeouts
    execution_timeout_seconds=300,
    tool_timeout_seconds=60,

    # Retry settings
    max_retries=3,
    retry_delay_seconds=1.0,

    # HITL settings
    require_approval_for_high_risk=True,
    approval_timeout_seconds=3600,
)
```

### RouterConfig

```python
from src.integrations.hybrid.routing.intent_router import RouterConfig

router_config = RouterConfig(
    # Keyword detection
    workflow_keywords=["execute", "run", "process", "workflow"],
    chat_keywords=["explain", "help", "what", "how", "why"],

    # Confidence thresholds
    confidence_threshold=0.7,
    ambiguity_threshold=0.3,

    # LLM-based routing (optional)
    use_llm_router=True,
    llm_router_model="gpt-4o-mini",
)
```

---

## Usage Examples

### Basic Hybrid Execution

```python
from src.integrations.hybrid.orchestrator_v2 import (
    create_orchestrator_v2,
    OrchestratorConfig,
)

# Create orchestrator
config = OrchestratorConfig(default_mode=ExecutionMode.HYBRID_MODE)
orchestrator = create_orchestrator_v2(config)

# Execute with automatic routing
result = await orchestrator.execute(
    input_text="Help me understand the approval workflow",
    session_id="session-123",
)

print(f"Executed in: {result.execution_mode}")
print(f"Response: {result.output}")
```

### Forced Mode Execution

```python
# Force workflow mode
result = await orchestrator.execute(
    input_text="Process invoice #456",
    session_id="session-123",
    force_mode=ExecutionMode.WORKFLOW_MODE,
)

# Force chat mode
result = await orchestrator.execute(
    input_text="What are the steps in invoice processing?",
    session_id="session-123",
    force_mode=ExecutionMode.CHAT_MODE,
)
```

### With Risk Assessment

```python
from src.integrations.hybrid.risk.engine import create_engine, RiskConfig

# Create risk engine
risk_config = RiskConfig(
    high_risk_threshold=0.7,
    critical_risk_threshold=0.9,
)
risk_engine = create_engine(config=risk_config)

# Create orchestrator with risk engine
orchestrator = create_orchestrator_v2(
    config=config,
    risk_engine=risk_engine,
)

# Execute - high-risk operations will trigger HITL
result = await orchestrator.execute(
    input_text="Delete all records from database",
    session_id="session-123",
)

if result.requires_approval:
    print(f"Approval required: {result.approval_reason}")
    # Wait for human approval...
```

### With Checkpoint Recovery

```python
from src.integrations.hybrid.checkpoint.storage import (
    UnifiedCheckpointStorage,
    StorageConfig,
    StorageBackend,
)

# Configure storage
storage_config = StorageConfig(
    backend=StorageBackend.REDIS,
    ttl_seconds=86400,  # 24 hours
    enable_compression=True,
)

# Create orchestrator with checkpoint storage
orchestrator = create_orchestrator_v2(
    config=config,
    checkpoint_storage=storage,
)

# Execute with auto-checkpoint
result = await orchestrator.execute(
    input_text="Run complex multi-step workflow",
    session_id="session-123",
    auto_checkpoint=True,
)

# Recover from checkpoint if needed
if result.failed:
    restored = await orchestrator.restore_from_checkpoint(
        session_id="session-123",
    )
    result = await orchestrator.resume_execution(restored)
```

---

## Best Practices

### 1. Mode Selection

- Use `WORKFLOW_MODE` for structured, multi-step processes
- Use `CHAT_MODE` for exploratory, conversational interactions
- Use `HYBRID_MODE` when intent is uncertain or mixed

### 2. Risk Management

- Configure risk thresholds based on your use case
- Always enable HITL for production environments
- Log all risk assessments for audit purposes

### 3. Checkpoint Strategy

- Enable auto-checkpoint for long-running workflows
- Use manual checkpoints before risky operations
- Configure appropriate TTL for your use case

### 4. Performance Optimization

- Use `V2_MINIMAL` mode for simple operations
- Configure appropriate timeouts for your workload
- Enable compression for large state objects

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ModeDetectionError` | Cannot determine execution mode | Provide clearer input or force mode |
| `StateMigrationError` | Failed to migrate between modes | Check state compatibility |
| `CheckpointNotFoundError` | Checkpoint expired or deleted | Increase TTL or re-execute |
| `ApprovalTimeoutError` | Human approval not received | Increase timeout or auto-approve |

### Error Handling Pattern

```python
from src.integrations.hybrid.orchestrator_v2 import (
    HybridExecutionError,
    ModeDetectionError,
    StateMigrationError,
)

try:
    result = await orchestrator.execute(input_text, session_id)
except ModeDetectionError as e:
    # Fallback to default mode
    result = await orchestrator.execute(
        input_text,
        session_id,
        force_mode=ExecutionMode.CHAT_MODE,
    )
except StateMigrationError as e:
    # Recover from last checkpoint
    result = await orchestrator.restore_and_resume(session_id)
except HybridExecutionError as e:
    logger.error(f"Execution failed: {e}")
    raise
```

---

## Related Documentation

- [Checkpoint Management Guide](./checkpoint-management.md)
- [Hybrid API Reference](../api/hybrid-api-reference.md)
- [Phase 13-14 Sprint Planning](../03-implementation/sprint-planning/phase-13/README.md)

---

**Last Updated**: 2026-01-03
**Authors**: IPA Platform Team
