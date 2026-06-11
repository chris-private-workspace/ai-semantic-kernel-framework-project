# Checkpoint Management Guide

> **Phase 14**: Unified Checkpoint System for IPA Platform
> **Version**: 1.0.0
> **Last Updated**: 2026-01-03

---

## Overview

The Unified Checkpoint System provides state persistence and recovery for hybrid MAF + Claude SDK operations. It supports both MAF workflow state and Claude SDK conversation state in a single checkpoint structure.

### Key Features

- **Dual-State Storage**: Persist MAF and Claude states together
- **Multi-Backend Support**: Redis, PostgreSQL, Filesystem, In-Memory
- **Compression**: ZLIB, GZIP, LZ4 algorithms
- **Version Migration**: Automatic v1→v2 migration
- **TTL Management**: Configurable expiration and cleanup
- **Risk Snapshots**: Capture risk assessment state

---

## Checkpoint Structure

### HybridCheckpoint

The main checkpoint class that holds both MAF and Claude states:

```python
from src.integrations.hybrid.checkpoint.models import (
    HybridCheckpoint,
    MAFCheckpointState,
    ClaudeCheckpointState,
    CheckpointType,
    CheckpointStatus,
)

# Create a hybrid checkpoint
checkpoint = HybridCheckpoint(
    checkpoint_id="chk-12345",
    session_id="session-abc",
    execution_mode="WORKFLOW_MODE",
    checkpoint_type=CheckpointType.AUTO,

    # MAF workflow state
    maf_state=MAFCheckpointState(
        workflow_id="wf-001",
        current_step=3,
        total_steps=5,
        agent_states={"agent1": {"status": "active"}},
        variables={"input": "data"},
    ),

    # Claude SDK state
    claude_state=ClaudeCheckpointState(
        session_id="session-abc",
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ],
        tool_call_history=[],
        context_variables={"user_name": "John"},
    ),
)
```

### Checkpoint Types

| Type | Description | Use Case |
|------|-------------|----------|
| `AUTO` | Automatic periodic checkpoint | Regular state preservation |
| `MANUAL` | User-triggered checkpoint | Before risky operations |
| `MODE_SWITCH` | Before mode transition | Workflow ↔ Chat switch |
| `HITL` | Human-in-the-loop checkpoint | Approval workflow |
| `RECOVERY` | After error recovery | Post-failure state |

### Checkpoint Status

| Status | Description |
|--------|-------------|
| `ACTIVE` | Checkpoint is valid and can be restored |
| `EXPIRED` | TTL exceeded, may be cleaned up |
| `RESTORED` | Has been used for restoration |
| `DELETED` | Marked for deletion |
| `CORRUPTED` | Data integrity check failed |

---

## MAF Checkpoint State

Captures Microsoft Agent Framework workflow state:

```python
from src.integrations.hybrid.checkpoint.models import MAFCheckpointState

maf_state = MAFCheckpointState(
    # Workflow identification
    workflow_id="invoice-approval-001",
    workflow_name="Invoice Approval",
    workflow_version="1.2.0",

    # Execution progress
    current_step=3,
    total_steps=5,
    step_name="manager_approval",

    # Agent states (per-agent data)
    agent_states={
        "classifier": {"last_classification": "urgent"},
        "approver": {"pending_items": 2},
    },

    # Workflow variables
    variables={
        "invoice_id": "INV-2026-001",
        "amount": 5000.00,
        "status": "pending_approval",
    },

    # Pending approvals
    pending_approvals=["manager_approval"],

    # Custom metadata
    metadata={
        "source": "email",
        "priority": "high",
    },
)
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | str | Unique workflow instance ID |
| `current_step` | int | Current step number (0-indexed) |
| `agent_states` | Dict[str, Any] | Per-agent state data |
| `variables` | Dict[str, Any] | Workflow variables |
| `pending_approvals` | List[str] | Outstanding approval requests |

---

## Claude Checkpoint State

Captures Claude SDK conversation and tool state:

```python
from src.integrations.hybrid.checkpoint.models import ClaudeCheckpointState

claude_state = ClaudeCheckpointState(
    # Session identification
    session_id="session-abc123",

    # Conversation history
    conversation_history=[
        {"role": "user", "content": "Process invoice #123"},
        {"role": "assistant", "content": "I'll process that for you."},
        {"role": "tool_call", "tool": "get_invoice", "args": {"id": "123"}},
        {"role": "tool_result", "result": {"amount": 500}},
    ],

    # Tool execution history
    tool_call_history=[
        {
            "tool_name": "get_invoice",
            "arguments": {"id": "123"},
            "result": {"amount": 500},
            "timestamp": "2026-01-03T10:00:00Z",
        }
    ],

    # Context variables
    context_variables={
        "current_invoice": "123",
        "user_permissions": ["read", "approve"],
    },

    # Current tool state
    current_tool_state={
        "active_tool": None,
        "pending_approval": False,
    },

    # Metadata
    metadata={
        "model": "claude-3-opus",
        "temperature": 0.7,
    },
)
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | str | Claude session identifier |
| `conversation_history` | List[Dict] | Full conversation messages |
| `tool_call_history` | List[Dict] | Executed tool calls |
| `context_variables` | Dict[str, Any] | Session context |

---

## Risk Snapshot

Captures risk assessment state for audit and recovery:

```python
from src.integrations.hybrid.checkpoint.models import RiskSnapshot
from src.integrations.hybrid.risk.models import RiskLevel

risk_snapshot = RiskSnapshot(
    overall_risk_level=RiskLevel.MEDIUM,
    risk_score=0.45,
    risk_factors=[
        {
            "factor_type": "OPERATION",
            "score": 0.3,
            "description": "Database write operation",
        },
        {
            "factor_type": "DATA",
            "score": 0.5,
            "description": "Sensitive data access",
        },
    ],
    assessment_time="2026-01-03T10:00:00Z",
    requires_approval=False,
)
```

---

## Storage Backends

### Redis Storage (Recommended)

Fast access, ideal for active checkpoints:

```python
from src.integrations.hybrid.checkpoint.backends.redis import RedisCheckpointStorage
from src.integrations.hybrid.checkpoint.storage import StorageConfig, StorageBackend

config = StorageConfig(
    backend=StorageBackend.REDIS,
    ttl_seconds=86400,  # 24 hours
    enable_compression=True,
)

storage = RedisCheckpointStorage(
    config=config,
    redis_url="redis://localhost:6379/0",
)
```

### PostgreSQL Storage

Persistent storage for compliance and audit:

```python
from src.integrations.hybrid.checkpoint.backends.postgres import PostgresCheckpointStorage

storage = PostgresCheckpointStorage(
    config=config,
    connection_string="postgresql://user:pass@localhost/ipa_platform",
)
```

### Filesystem Storage

Backup and archive storage:

```python
from src.integrations.hybrid.checkpoint.backends.filesystem import FilesystemCheckpointStorage

storage = FilesystemCheckpointStorage(
    config=config,
    base_path="/data/checkpoints",
)
```

### In-Memory Storage

For testing and development:

```python
from src.integrations.hybrid.checkpoint.backends.memory import MemoryCheckpointStorage

storage = MemoryCheckpointStorage(config=config)
```

---

## Basic Operations

### Save Checkpoint

```python
# Create checkpoint
checkpoint = HybridCheckpoint(
    checkpoint_id=str(uuid.uuid4()),
    session_id="session-123",
    execution_mode="WORKFLOW_MODE",
    checkpoint_type=CheckpointType.AUTO,
    maf_state=maf_state,
    claude_state=claude_state,
)

# Save to storage
checkpoint_id = await storage.save(checkpoint)
print(f"Saved checkpoint: {checkpoint_id}")
```

### Load Checkpoint

```python
# Load by ID
checkpoint = await storage.load(checkpoint_id)

if checkpoint:
    print(f"Loaded: {checkpoint.session_id}")
    print(f"MAF Step: {checkpoint.maf_state.current_step}")
    print(f"Claude Messages: {len(checkpoint.claude_state.conversation_history)}")
else:
    print("Checkpoint not found")
```

### Query Checkpoints

```python
from src.integrations.hybrid.checkpoint.storage import CheckpointQuery

# Query by session
query = CheckpointQuery(
    session_id="session-123",
    status=CheckpointStatus.ACTIVE,
    limit=10,
)
checkpoints = await storage.query(query)

# Query by type
query = CheckpointQuery(
    checkpoint_type=CheckpointType.HITL,
    created_after=datetime.utcnow() - timedelta(hours=24),
)
hitl_checkpoints = await storage.query(query)
```

### Delete Checkpoint

```python
# Delete single checkpoint
deleted = await storage.delete(checkpoint_id)

# Delete all for session
count = await storage.delete_by_session("session-123")
print(f"Deleted {count} checkpoints")
```

---

## Advanced Operations

### Restore from Checkpoint

```python
# Restore with full result
result = await storage.restore(checkpoint_id)

if result.success:
    print(f"Restored checkpoint: {result.checkpoint_id}")
    print(f"MAF restored: {result.restored_maf}")
    print(f"Claude restored: {result.restored_claude}")
    print(f"Restore time: {result.restore_time_ms}ms")
else:
    print(f"Restore failed: {result.error_message}")
```

### Save with Named Restore Point

```python
# Create named restore point
checkpoint_id = await storage.save_with_restore_point(
    checkpoint=checkpoint,
    restore_point_name="before_database_update",
)
```

### Load Latest for Session

```python
# Get most recent checkpoint
latest = await storage.load_latest("session-123")

if latest:
    print(f"Latest checkpoint: {latest.created_at}")
```

### Enforce Retention Policy

```python
# Remove old checkpoints beyond limit
removed = await storage.enforce_retention("session-123")
print(f"Removed {removed} old checkpoints")
```

### Cleanup Expired Checkpoints

```python
# Remove all expired checkpoints
cleaned = await storage.cleanup_expired()
print(f"Cleaned {cleaned} expired checkpoints")
```

---

## Serialization & Compression

### Default Serialization

```python
from src.integrations.hybrid.checkpoint.serialization import (
    CheckpointSerializer,
    SerializationConfig,
)

config = SerializationConfig(
    compression=CompressionAlgorithm.ZLIB,
    compression_level=6,
    include_checksum=True,
)

serializer = CheckpointSerializer(config)

# Serialize
result = serializer.serialize(checkpoint)
print(f"Serialized size: {len(result.data)} bytes")
print(f"Compression ratio: {result.compression_ratio:.2%}")

# Deserialize
restored = serializer.deserialize(result.data)
```

### Compression Algorithms

| Algorithm | Speed | Ratio | Use Case |
|-----------|-------|-------|----------|
| `NONE` | Fastest | 0% | Development, small data |
| `ZLIB` | Fast | 50-60% | General purpose (default) |
| `GZIP` | Medium | 55-65% | Archive storage |
| `LZ4` | Very Fast | 40-50% | High-throughput scenarios |

---

## Version Migration

### Automatic Migration

```python
from src.integrations.hybrid.checkpoint.version import CheckpointVersionMigrator

migrator = CheckpointVersionMigrator()

# Check if migration needed
if migrator.needs_migration(checkpoint_data):
    migrated = migrator.migrate(checkpoint_data)
    print(f"Migrated from v{migrator.get_version(checkpoint_data)} to v2")
```

### Migration Hooks

```python
# Register custom migration logic
def custom_v1_to_v2_migration(data: dict) -> dict:
    # Transform v1 fields to v2 format
    if "old_field" in data:
        data["new_field"] = data.pop("old_field")
    return data

migrator.register_migration_hook("1_to_2", custom_v1_to_v2_migration)
```

---

## Usage Patterns

### Auto-Checkpoint Pattern

```python
class WorkflowExecutor:
    def __init__(self, storage: UnifiedCheckpointStorage):
        self.storage = storage
        self.checkpoint_interval = 5  # Every 5 steps

    async def execute_workflow(self, workflow_id: str):
        step = 0
        while not self.is_complete():
            await self.execute_step(step)

            # Auto-checkpoint every N steps
            if step % self.checkpoint_interval == 0:
                await self.create_checkpoint(CheckpointType.AUTO)

            step += 1
```

### Pre-Risk Checkpoint Pattern

```python
async def execute_with_risk_checkpoint(operation, risk_engine, storage):
    # Assess risk
    assessment = risk_engine.assess(operation)

    # Create checkpoint before high-risk operation
    if assessment.overall_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        await storage.save_with_restore_point(
            checkpoint=create_current_checkpoint(),
            restore_point_name=f"before_{operation.name}",
        )

    # Execute operation
    try:
        result = await operation.execute()
    except Exception as e:
        # Restore on failure
        await restore_latest_checkpoint()
        raise

    return result
```

### Mode Switch Checkpoint Pattern

```python
async def switch_mode_with_checkpoint(
    from_mode: ExecutionMode,
    to_mode: ExecutionMode,
    storage: UnifiedCheckpointStorage,
):
    # Create mode switch checkpoint
    checkpoint = HybridCheckpoint(
        checkpoint_type=CheckpointType.MODE_SWITCH,
        execution_mode=from_mode.value,
        maf_state=get_current_maf_state(),
        claude_state=get_current_claude_state(),
        metadata={
            "from_mode": from_mode.value,
            "to_mode": to_mode.value,
        },
    )
    await storage.save(checkpoint)

    # Perform mode switch
    new_state = await migrate_state(from_mode, to_mode)
    return new_state
```

---

## Storage Statistics

```python
# Get storage statistics
stats = await storage.get_stats()

print(f"Total checkpoints: {stats.total_checkpoints}")
print(f"Active checkpoints: {stats.active_checkpoints}")
print(f"Expired checkpoints: {stats.expired_checkpoints}")
print(f"Total size: {stats.total_size_bytes / 1024:.2f} KB")
print(f"Unique sessions: {stats.sessions_count}")
print(f"Oldest: {stats.oldest_checkpoint}")
print(f"Newest: {stats.newest_checkpoint}")
```

---

## Configuration Reference

### StorageConfig

```python
@dataclass
class StorageConfig:
    backend: StorageBackend = StorageBackend.REDIS
    ttl_seconds: int = 86400  # 24 hours
    max_checkpoints_per_session: int = 100
    enable_compression: bool = True
    enable_encryption: bool = False  # Future feature
    cleanup_interval_seconds: int = 3600  # 1 hour
    serialization_config: Optional[SerializationConfig] = None
```

### SerializationConfig

```python
@dataclass
class SerializationConfig:
    compression: CompressionAlgorithm = CompressionAlgorithm.ZLIB
    compression_level: int = 6  # 1-9
    include_checksum: bool = True
    checksum_algorithm: str = "sha256"
```

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `CheckpointNotFoundError` | Checkpoint doesn't exist | Check ID, may be expired |
| `StorageConnectionError` | Cannot connect to backend | Check backend service |
| `StorageCapacityError` | Storage limit exceeded | Cleanup or increase capacity |
| `ChecksumMismatchError` | Data corruption detected | Re-save or use backup |

### Error Handling Pattern

```python
from src.integrations.hybrid.checkpoint.storage import (
    StorageError,
    CheckpointNotFoundError,
    StorageConnectionError,
)

try:
    checkpoint = await storage.load(checkpoint_id)
except CheckpointNotFoundError:
    # Handle missing checkpoint
    checkpoint = await create_new_checkpoint()
except StorageConnectionError:
    # Fallback to alternative storage
    checkpoint = await fallback_storage.load(checkpoint_id)
except StorageError as e:
    logger.error(f"Storage error: {e}")
    raise
```

---

## Best Practices

### 1. Checkpoint Strategy

- Use `AUTO` checkpoints for regular preservation (every 5-10 steps)
- Use `MANUAL` checkpoints before risky operations
- Use `MODE_SWITCH` checkpoints during transitions
- Configure appropriate TTL based on workflow duration

### 2. Storage Selection

- **Redis**: Active sessions, fast access
- **PostgreSQL**: Long-term storage, audit requirements
- **Filesystem**: Backup, disaster recovery
- **Memory**: Testing and development only

### 3. Performance Optimization

- Enable compression for large states
- Use LZ4 for high-throughput scenarios
- Configure appropriate retention limits
- Schedule regular cleanup jobs

### 4. Security Considerations

- Do not store sensitive data in checkpoints
- Use encryption for production (when available)
- Implement access controls on storage backends
- Audit checkpoint access for compliance

---

## Related Documentation

- [Hybrid Architecture Guide](./hybrid-architecture-guide.md)
- [Hybrid API Reference](../api/hybrid-api-reference.md)
- [Phase 14 Sprint Planning](../03-implementation/sprint-planning/phase-14/README.md)

---

**Last Updated**: 2026-01-03
**Authors**: IPA Platform Team
