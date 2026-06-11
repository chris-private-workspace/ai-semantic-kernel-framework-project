# AG-UI Protocol API Reference

> Phase 15: AG-UI Protocol Integration - Complete API Reference (Sprint 58-60)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [SSE Streaming](#sse-streaming)
5. [State Management](#state-management)
6. [Approval Workflow](#approval-workflow)
7. [Error Codes](#error-codes)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)

---

## Overview

The AG-UI Protocol API provides a unified interface for agent-user interaction following the AG-UI Protocol specification. It supports:

- **Agent Execution**: Run agents with streaming or synchronous responses
- **State Management**: Thread-scoped state with optimistic concurrency control
- **Tool Approval**: Human-in-the-loop approval workflow for sensitive operations
- **Generative UI**: Dynamic UI component rendering based on agent responses
- **Shared State**: Bidirectional state synchronization via SSE

### Base URL

```
Production: https://api.ipa-platform.com/api/v1
Development: http://localhost:8000/api/v1
```

### API Versioning

The API uses URL path versioning. Current version: `v1`

---

## Authentication

All API requests require authentication via Bearer token.

### Request Header

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## REST API Endpoints

### Health Check

#### Get Health Status

Returns the health status of the AG-UI service.

```http
GET /api/v1/ag-ui/health
```

**Response:**

```json
{
    "status": "ok",
    "service": "ag-ui",
    "version": "1.0.0",
    "timestamp": "2026-01-05T10:00:00Z"
}
```

---

### Agent Execution

#### Run Agent (Streaming)

Execute an agent with SSE streaming response.

```http
POST /api/v1/ag-ui
Accept: text/event-stream
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | string | Yes | Unique thread identifier |
| `input` | string | Yes | User input message |
| `config` | object | No | Agent configuration overrides |
| `stream` | boolean | No | Enable streaming (default: true) |

**Example Request:**

```json
{
    "thread_id": "thread-123-abc",
    "input": "What is the weather today?",
    "config": {
        "temperature": 0.7,
        "max_tokens": 1000
    },
    "stream": true
}
```

**SSE Response Events:**

```
event: run_started
data: {"run_id": "run-456", "thread_id": "thread-123-abc"}

event: text_message_content
data: {"content": "The weather today is sunny with..."}

event: tool_call_start
data: {"tool_call_id": "tc-789", "tool_name": "weather_api", "tool_args": {"city": "Taipei"}}

event: tool_call_end
data: {"tool_call_id": "tc-789", "result": {"temp": 25, "condition": "sunny"}}

event: run_finished
data: {"run_id": "run-456", "status": "completed"}
```

#### Run Agent (Synchronous)

Execute an agent and wait for complete response.

```http
POST /api/v1/ag-ui/sync
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | string | Yes | Unique thread identifier |
| `input` | string | Yes | User input message |
| `config` | object | No | Agent configuration overrides |

**Response:**

```json
{
    "run_id": "run-456",
    "thread_id": "thread-123-abc",
    "response": "The weather today is sunny with a high of 25°C.",
    "tool_calls": [
        {
            "tool_call_id": "tc-789",
            "tool_name": "weather_api",
            "tool_args": {"city": "Taipei"},
            "result": {"temp": 25, "condition": "sunny"}
        }
    ],
    "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 30,
        "total_tokens": 80
    }
}
```

---

### State Management

#### Get Thread State

Retrieve the current state for a thread.

```http
GET /api/v1/ag-ui/threads/{thread_id}/state
```

**Response:**

```json
{
    "thread_id": "thread-123-abc",
    "state": {
        "counter": 5,
        "user_preferences": {
            "theme": "dark",
            "language": "zh-TW"
        }
    },
    "version": 3,
    "updated_at": "2026-01-05T10:00:00Z"
}
```

#### Update Thread State

Update the state for a thread with optimistic concurrency control.

```http
PATCH /api/v1/ag-ui/threads/{thread_id}/state
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | object | Yes | State data to update |
| `version` | integer | No | Expected version for optimistic locking |
| `metadata` | object | No | State metadata |

**Example Request:**

```json
{
    "state": {
        "counter": 6,
        "user_preferences": {
            "theme": "light"
        }
    },
    "version": 3
}
```

**Response:**

```json
{
    "thread_id": "thread-123-abc",
    "state": {
        "counter": 6,
        "user_preferences": {
            "theme": "light",
            "language": "zh-TW"
        }
    },
    "version": 4,
    "updated_at": "2026-01-05T10:01:00Z"
}
```

**Version Conflict Response (409):**

```json
{
    "error": "VERSION_CONFLICT",
    "message": "State was modified by another client",
    "current_version": 5,
    "your_version": 3
}
```

#### Delete Thread State

Delete all state for a thread.

```http
DELETE /api/v1/ag-ui/threads/{thread_id}/state
```

**Response:** `204 No Content`

---

### Approval Workflow

#### List Pending Approvals

Get all pending tool call approvals.

```http
GET /api/v1/ag-ui/approvals/pending
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `thread_id` | string | Filter by thread ID |
| `limit` | integer | Maximum results (default: 50) |
| `offset` | integer | Pagination offset |

**Response:**

```json
{
    "approvals": [
        {
            "id": "approval-001",
            "thread_id": "thread-123-abc",
            "tool_name": "file_write",
            "tool_args": {
                "path": "/data/report.txt",
                "content": "Monthly report..."
            },
            "reason": "Agent wants to write a file",
            "created_at": "2026-01-05T10:00:00Z",
            "expires_at": "2026-01-05T10:30:00Z"
        }
    ],
    "total": 1
}
```

#### Approve Tool Call

Approve a pending tool call.

```http
POST /api/v1/ag-ui/approvals/{approval_id}/approve
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Reason for approval |

**Response:**

```json
{
    "id": "approval-001",
    "status": "approved",
    "approved_by": "user@example.com",
    "approved_at": "2026-01-05T10:05:00Z"
}
```

#### Reject Tool Call

Reject a pending tool call.

```http
POST /api/v1/ag-ui/approvals/{approval_id}/reject
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Reason for rejection |

**Response:**

```json
{
    "id": "approval-001",
    "status": "rejected",
    "rejected_by": "user@example.com",
    "rejected_at": "2026-01-05T10:05:00Z",
    "reason": "File path not authorized"
}
```

#### Cancel Tool Call

Cancel a pending tool call.

```http
POST /api/v1/ag-ui/approvals/{approval_id}/cancel
```

**Response:**

```json
{
    "id": "approval-001",
    "status": "cancelled",
    "cancelled_at": "2026-01-05T10:05:00Z"
}
```

---

## SSE Streaming

### Event Types

The AG-UI streaming API emits the following event types:

| Event | Description |
|-------|-------------|
| `run_started` | Agent run has started |
| `text_message_start` | Text message generation started |
| `text_message_content` | Incremental text content |
| `text_message_end` | Text message generation completed |
| `tool_call_start` | Tool call initiated |
| `tool_call_args` | Tool call arguments (incremental) |
| `tool_call_end` | Tool call completed |
| `state_snapshot` | Full state snapshot |
| `state_delta` | Incremental state update |
| `run_error` | Error during execution |
| `run_finished` | Agent run completed |

### Event Format

```
event: <event_type>
data: <json_payload>

```

### Example Stream

```
event: run_started
data: {"run_id": "run-001", "thread_id": "thread-123"}

event: text_message_start
data: {"message_id": "msg-001"}

event: text_message_content
data: {"content": "Let me check "}

event: text_message_content
data: {"content": "the weather for you."}

event: text_message_end
data: {"message_id": "msg-001"}

event: tool_call_start
data: {"tool_call_id": "tc-001", "tool_name": "weather", "tool_args": {}}

event: tool_call_args
data: {"tool_call_id": "tc-001", "args_delta": "{\"city\": \"Taipei\"}"}

event: tool_call_end
data: {"tool_call_id": "tc-001", "result": {"temp": 25}}

event: run_finished
data: {"run_id": "run-001", "status": "completed"}
```

---

## State Management

### Optimistic Concurrency Control

The state management API uses optimistic concurrency control with version tracking:

1. **Read**: Get current state with version number
2. **Modify**: Make local changes
3. **Write**: Submit with expected version
4. **Conflict**: If version mismatch, handle conflict

### State Diff Operations

State updates can use diff operations for efficient updates:

| Operation | Description | Example |
|-----------|-------------|---------|
| `add` | Add new property | `{"op": "add", "path": "/items/-", "value": "new"}` |
| `remove` | Remove property | `{"op": "remove", "path": "/items/0"}` |
| `replace` | Replace value | `{"op": "replace", "path": "/counter", "value": 5}` |
| `move` | Move property | `{"op": "move", "from": "/old", "path": "/new"}` |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_THREAD_ID` | 400 | Invalid thread ID format |
| `INVALID_STATE` | 400 | Invalid state data |
| `THREAD_NOT_FOUND` | 404 | Thread does not exist |
| `APPROVAL_NOT_FOUND` | 404 | Approval request not found |
| `VERSION_CONFLICT` | 409 | Optimistic concurrency conflict |
| `APPROVAL_EXPIRED` | 410 | Approval request has expired |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Usage Examples

### Python

```python
import httpx
import json

# Synchronous request
async def run_agent_sync(thread_id: str, input: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ag-ui/sync",
            json={"thread_id": thread_id, "input": input},
            headers={"Authorization": "Bearer <token>"}
        )
        return response.json()

# Streaming request
async def run_agent_stream(thread_id: str, input: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/ag-ui",
            json={"thread_id": thread_id, "input": input, "stream": True},
            headers={
                "Authorization": "Bearer <token>",
                "Accept": "text/event-stream"
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    print(data)
```

### JavaScript/TypeScript

```typescript
// Synchronous request
const response = await fetch('/api/v1/ag-ui/sync', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer <token>',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        thread_id: 'thread-123',
        input: 'Hello!'
    })
});
const data = await response.json();

// Streaming request with EventSource
const eventSource = new EventSource('/api/v1/ag-ui?thread_id=thread-123&input=Hello');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};
```

### cURL

```bash
# Health check
curl -X GET http://localhost:8000/api/v1/ag-ui/health

# Run agent (sync)
curl -X POST http://localhost:8000/api/v1/ag-ui/sync \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"thread_id": "thread-123", "input": "Hello!"}'

# Get thread state
curl -X GET http://localhost:8000/api/v1/ag-ui/threads/thread-123/state \
    -H "Authorization: Bearer <token>"

# Update thread state
curl -X PATCH http://localhost:8000/api/v1/ag-ui/threads/thread-123/state \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"state": {"counter": 5}, "version": 1}'
```

---

## Best Practices

### 1. Thread ID Management

- Use UUID or structured IDs (e.g., `user-123-conv-456`)
- Store thread IDs for session continuity
- Clean up old threads periodically

### 2. State Management

- Use optimistic concurrency for concurrent access
- Implement client-side conflict resolution
- Keep state size reasonable (< 1MB)

### 3. Error Handling

- Handle version conflicts gracefully (retry with fresh state)
- Implement exponential backoff for rate limits
- Log errors for debugging

### 4. Streaming

- Use EventSource for browser clients
- Implement reconnection logic
- Handle partial events

### 5. Approval Workflow

- Set reasonable expiration times
- Implement notification system for pending approvals
- Log all approval decisions for audit

---

**Last Updated**: 2026-01-05
**Version**: 1.0.0
**Sprint**: 60 (S60-4)
