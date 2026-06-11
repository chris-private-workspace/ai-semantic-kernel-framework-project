# Hybrid API Reference

> **Phase 13-14**: REST API Reference for Hybrid MAF + Claude SDK
> **Version**: 1.0.0
> **Base URL**: `/api/v1/hybrid`
> **Last Updated**: 2026-01-03

---

## Authentication

All endpoints require authentication via API key header:

```http
Authorization: Bearer <api_key>
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/execute` | Execute hybrid operation |
| POST | `/execute/stream` | Execute with SSE streaming |
| GET | `/sessions/{id}` | Get session details |
| DELETE | `/sessions/{id}` | End session |
| POST | `/switch-mode` | Switch execution mode |
| POST | `/checkpoints` | Create checkpoint |
| GET | `/checkpoints/{id}` | Get checkpoint |
| POST | `/checkpoints/{id}/restore` | Restore checkpoint |
| GET | `/risk/assess` | Assess operation risk |

---

## Execute Endpoint

### Execute Hybrid Operation

Execute an operation with automatic or forced mode selection.

**POST** `/api/v1/hybrid/execute`

#### Request Body

```json
{
  "input_text": "Process invoice #123 for approval",
  "session_id": "session-abc123",
  "force_mode": null,
  "config": {
    "auto_switch_enabled": true,
    "require_approval_for_high_risk": true,
    "execution_timeout_seconds": 300
  },
  "context": {
    "user_id": "user-001",
    "permissions": ["read", "write", "approve"]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input_text` | string | Yes | User input to process |
| `session_id` | string | No | Session ID (auto-generated if omitted) |
| `force_mode` | string | No | Force specific mode: `WORKFLOW_MODE`, `CHAT_MODE` |
| `config` | object | No | Execution configuration |
| `context` | object | No | Additional context variables |

#### Response

```json
{
  "success": true,
  "execution_id": "exec-12345",
  "session_id": "session-abc123",
  "execution_mode": "WORKFLOW_MODE",
  "output": {
    "type": "workflow_result",
    "message": "Invoice #123 has been submitted for approval",
    "data": {
      "invoice_id": "INV-123",
      "status": "pending_approval",
      "next_approver": "manager@company.com"
    }
  },
  "requires_approval": false,
  "checkpoint_id": "chk-67890",
  "metrics": {
    "execution_time_ms": 1250,
    "tokens_used": 450,
    "tool_calls": 2
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether execution succeeded |
| `execution_id` | string | Unique execution identifier |
| `session_id` | string | Session identifier |
| `execution_mode` | string | Mode used for execution |
| `output` | object | Execution output |
| `requires_approval` | boolean | If HITL approval needed |
| `approval_reason` | string | Reason for approval (if required) |
| `checkpoint_id` | string | Auto-created checkpoint ID |
| `metrics` | object | Execution metrics |

#### Error Responses

**400 Bad Request**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input: input_text is required",
  "details": {
    "field": "input_text",
    "issue": "Field is required"
  }
}
```

**408 Request Timeout**
```json
{
  "error": "EXECUTION_TIMEOUT",
  "message": "Execution exceeded timeout of 300 seconds",
  "checkpoint_id": "chk-67890"
}
```

---

### Execute with Streaming

Execute operation with Server-Sent Events (SSE) streaming.

**POST** `/api/v1/hybrid/execute/stream`

#### Request Body

Same as `/execute` endpoint.

#### Response (SSE Stream)

```
event: start
data: {"execution_id": "exec-12345", "session_id": "session-abc123"}

event: mode_detected
data: {"mode": "WORKFLOW_MODE", "confidence": 0.92}

event: step_started
data: {"step": 1, "name": "classify_document", "total_steps": 3}

event: tool_call
data: {"tool": "get_invoice", "arguments": {"id": "123"}}

event: tool_result
data: {"tool": "get_invoice", "result": {"amount": 500, "status": "pending"}}

event: step_completed
data: {"step": 1, "name": "classify_document", "duration_ms": 250}

event: output
data: {"type": "partial", "content": "Processing invoice..."}

event: complete
data: {"success": true, "output": {...}, "checkpoint_id": "chk-67890"}
```

#### Event Types

| Event | Description |
|-------|-------------|
| `start` | Execution started |
| `mode_detected` | Execution mode determined |
| `step_started` | Workflow step started |
| `tool_call` | Tool being called |
| `tool_result` | Tool execution result |
| `step_completed` | Workflow step completed |
| `output` | Partial output content |
| `approval_required` | HITL approval needed |
| `error` | Error occurred |
| `complete` | Execution completed |

---

## Session Endpoints

### Get Session Details

**GET** `/api/v1/hybrid/sessions/{session_id}`

#### Response

```json
{
  "session_id": "session-abc123",
  "created_at": "2026-01-03T10:00:00Z",
  "updated_at": "2026-01-03T10:30:00Z",
  "current_mode": "WORKFLOW_MODE",
  "execution_count": 5,
  "checkpoint_count": 3,
  "maf_state": {
    "workflow_id": "wf-001",
    "current_step": 3,
    "status": "running"
  },
  "claude_state": {
    "message_count": 12,
    "tool_call_count": 4
  },
  "metadata": {
    "user_id": "user-001",
    "client_ip": "192.168.1.100"
  }
}
```

### End Session

**DELETE** `/api/v1/hybrid/sessions/{session_id}`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `create_final_checkpoint` | boolean | true | Create checkpoint before ending |
| `cleanup_checkpoints` | boolean | false | Delete all session checkpoints |

#### Response

```json
{
  "success": true,
  "session_id": "session-abc123",
  "final_checkpoint_id": "chk-final-123",
  "checkpoints_deleted": 0,
  "ended_at": "2026-01-03T11:00:00Z"
}
```

---

## Mode Switching Endpoint

### Switch Execution Mode

Manually trigger mode switch between WORKFLOW and CHAT modes.

**POST** `/api/v1/hybrid/switch-mode`

#### Request Body

```json
{
  "session_id": "session-abc123",
  "target_mode": "CHAT_MODE",
  "reason": "User requested conversational interaction",
  "preserve_context": true,
  "create_checkpoint": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Session to switch |
| `target_mode` | string | Yes | Target mode: `WORKFLOW_MODE`, `CHAT_MODE` |
| `reason` | string | No | Reason for switch |
| `preserve_context` | boolean | No | Preserve context during switch (default: true) |
| `create_checkpoint` | boolean | No | Create checkpoint before switch (default: true) |

#### Response

```json
{
  "success": true,
  "session_id": "session-abc123",
  "previous_mode": "WORKFLOW_MODE",
  "current_mode": "CHAT_MODE",
  "checkpoint_id": "chk-switch-456",
  "context_preserved": true,
  "switch_time_ms": 150
}
```

---

## Checkpoint Endpoints

### Create Checkpoint

**POST** `/api/v1/hybrid/checkpoints`

#### Request Body

```json
{
  "session_id": "session-abc123",
  "checkpoint_type": "MANUAL",
  "name": "before_database_update",
  "metadata": {
    "reason": "User requested checkpoint",
    "operation": "database_migration"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Session ID |
| `checkpoint_type` | string | No | Type: `MANUAL`, `AUTO`, `MODE_SWITCH`, `HITL`, `RECOVERY` |
| `name` | string | No | Human-readable name |
| `metadata` | object | No | Additional metadata |

#### Response

```json
{
  "checkpoint_id": "chk-12345",
  "session_id": "session-abc123",
  "checkpoint_type": "MANUAL",
  "created_at": "2026-01-03T10:30:00Z",
  "expires_at": "2026-01-04T10:30:00Z",
  "size_bytes": 2048,
  "compressed": true,
  "has_maf_state": true,
  "has_claude_state": true
}
```

### Get Checkpoint

**GET** `/api/v1/hybrid/checkpoints/{checkpoint_id}`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_state` | boolean | false | Include full state data |

#### Response

```json
{
  "checkpoint_id": "chk-12345",
  "session_id": "session-abc123",
  "execution_mode": "WORKFLOW_MODE",
  "checkpoint_type": "MANUAL",
  "status": "ACTIVE",
  "created_at": "2026-01-03T10:30:00Z",
  "expires_at": "2026-01-04T10:30:00Z",
  "has_maf_state": true,
  "has_claude_state": true,
  "risk_snapshot": {
    "overall_level": "MEDIUM",
    "risk_score": 0.45
  },
  "metadata": {
    "name": "before_database_update"
  }
}
```

### List Session Checkpoints

**GET** `/api/v1/hybrid/checkpoints`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | string | Required | Filter by session |
| `checkpoint_type` | string | - | Filter by type |
| `status` | string | - | Filter by status |
| `limit` | integer | 20 | Max results |
| `offset` | integer | 0 | Pagination offset |

#### Response

```json
{
  "data": [
    {
      "checkpoint_id": "chk-12345",
      "checkpoint_type": "MANUAL",
      "status": "ACTIVE",
      "created_at": "2026-01-03T10:30:00Z"
    },
    {
      "checkpoint_id": "chk-12344",
      "checkpoint_type": "AUTO",
      "status": "ACTIVE",
      "created_at": "2026-01-03T10:25:00Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### Restore Checkpoint

**POST** `/api/v1/hybrid/checkpoints/{checkpoint_id}/restore`

#### Request Body

```json
{
  "restore_mode": "FULL",
  "target_session_id": null,
  "resume_execution": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `restore_mode` | string | No | `FULL`, `MAF_ONLY`, `CLAUDE_ONLY` |
| `target_session_id` | string | No | Restore to different session |
| `resume_execution` | boolean | No | Resume after restore (default: false) |

#### Response

```json
{
  "success": true,
  "checkpoint_id": "chk-12345",
  "session_id": "session-abc123",
  "restored_maf": true,
  "restored_claude": true,
  "restored_mode": "WORKFLOW_MODE",
  "restore_time_ms": 125,
  "resumed": true,
  "resume_execution_id": "exec-67890"
}
```

### Delete Checkpoint

**DELETE** `/api/v1/hybrid/checkpoints/{checkpoint_id}`

#### Response

```json
{
  "success": true,
  "checkpoint_id": "chk-12345",
  "deleted_at": "2026-01-03T11:00:00Z"
}
```

---

## Risk Assessment Endpoint

### Assess Operation Risk

**POST** `/api/v1/hybrid/risk/assess`

#### Request Body

```json
{
  "operation": {
    "tool_name": "Bash",
    "command": "rm -rf /tmp/test",
    "target_path": "/tmp/test"
  },
  "context": {
    "session_id": "session-abc123",
    "environment": "production",
    "user_permissions": ["admin"]
  }
}
```

#### Response

```json
{
  "overall_level": "HIGH",
  "overall_score": 0.78,
  "requires_approval": true,
  "approval_reason": "High risk level (high) | Destructive file operation | Production environment",
  "factors": [
    {
      "factor_type": "OPERATION",
      "score": 0.8,
      "weight": 0.3,
      "description": "Destructive file operation: rm -rf",
      "source": "command_analyzer"
    },
    {
      "factor_type": "ENVIRONMENT",
      "score": 0.7,
      "weight": 0.2,
      "description": "Production environment",
      "source": "context_analyzer"
    }
  ],
  "assessment_time": "2026-01-03T10:30:00Z",
  "assessment_id": "risk-12345"
}
```

#### Risk Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| `LOW` | 0.0 - 0.3 | Safe operation, no approval needed |
| `MEDIUM` | 0.3 - 0.6 | Moderate risk, optional approval |
| `HIGH` | 0.6 - 0.8 | High risk, approval recommended |
| `CRITICAL` | 0.8 - 1.0 | Critical risk, approval required |

---

## Approval Endpoints

### Submit Approval Decision

**POST** `/api/v1/hybrid/approvals/{approval_id}`

#### Request Body

```json
{
  "decision": "APPROVED",
  "approver_id": "user-manager-001",
  "comments": "Approved for processing",
  "conditions": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision` | string | Yes | `APPROVED`, `REJECTED`, `ESCALATED` |
| `approver_id` | string | Yes | Approver user ID |
| `comments` | string | No | Decision comments |
| `conditions` | object | No | Conditional approval terms |

#### Response

```json
{
  "success": true,
  "approval_id": "apr-12345",
  "execution_id": "exec-67890",
  "decision": "APPROVED",
  "decided_at": "2026-01-03T10:35:00Z",
  "execution_resumed": true
}
```

### Get Pending Approvals

**GET** `/api/v1/hybrid/approvals`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | string | - | Filter by session |
| `status` | string | `PENDING` | Filter by status |
| `limit` | integer | 20 | Max results |

#### Response

```json
{
  "data": [
    {
      "approval_id": "apr-12345",
      "execution_id": "exec-67890",
      "session_id": "session-abc123",
      "risk_level": "HIGH",
      "reason": "Destructive file operation",
      "requested_at": "2026-01-03T10:30:00Z",
      "expires_at": "2026-01-03T11:30:00Z"
    }
  ],
  "total": 1
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `SESSION_NOT_FOUND` | 404 | Session does not exist |
| `CHECKPOINT_NOT_FOUND` | 404 | Checkpoint does not exist |
| `CHECKPOINT_EXPIRED` | 410 | Checkpoint has expired |
| `MODE_SWITCH_FAILED` | 500 | Failed to switch execution mode |
| `EXECUTION_TIMEOUT` | 408 | Execution exceeded timeout |
| `APPROVAL_TIMEOUT` | 408 | Approval not received in time |
| `STORAGE_ERROR` | 500 | Checkpoint storage error |
| `RISK_ASSESSMENT_FAILED` | 500 | Risk assessment error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/execute` | 100 req/min |
| `/execute/stream` | 50 req/min |
| `/checkpoints` | 200 req/min |
| `/risk/assess` | 300 req/min |

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704276000
```

---

## Related Documentation

- [Hybrid Architecture Guide](../guides/hybrid-architecture-guide.md)
- [Checkpoint Management Guide](../guides/checkpoint-management.md)
- [Phase 13-14 Sprint Planning](../03-implementation/sprint-planning/phase-13/README.md)

---

**Last Updated**: 2026-01-03
**Authors**: IPA Platform Team
