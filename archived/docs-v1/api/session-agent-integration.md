# Session-Agent Integration API

> Phase 11: Agent-Session Integration - Complete API Reference

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket API](#websocket-api)
5. [Error Codes](#error-codes)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)

---

## Overview

The Session-Agent Integration API provides a unified interface for managing conversational sessions with AI agents. It supports:

- **Session Management**: Create, retrieve, update, and end sessions
- **Chat Operations**: Send messages and receive agent responses
- **Tool Execution**: Invoke agent tools with optional approval workflow
- **Streaming**: Real-time response streaming via SSE or WebSocket
- **History**: Access conversation history and message retrieval

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

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password"
}
```

**Response:**

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

---

## REST API Endpoints

### Sessions

#### Create Session

Creates a new conversation session.

```http
POST /api/v1/sessions/
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Session title (auto-generated if not provided) |
| `agent_id` | string | No | Agent to use for this session |
| `metadata` | object | No | Custom metadata |
| `require_approval` | boolean | No | Require approval for tool calls (default: false) |

**Example Request:**

```json
{
    "title": "Customer Support Session",
    "agent_id": "support-agent-v1",
    "metadata": {
        "customer_id": "C12345",
        "priority": "high"
    }
}
```

**Example Response:**

```json
{
    "id": "sess_abc123def456",
    "title": "Customer Support Session",
    "status": "active",
    "agent_id": "support-agent-v1",
    "created_at": "2025-12-24T10:00:00Z",
    "metadata": {
        "customer_id": "C12345",
        "priority": "high"
    }
}
```

---

#### Get Session

Retrieves session details.

```http
GET /api/v1/sessions/{session_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session identifier |

**Response:**

```json
{
    "id": "sess_abc123def456",
    "title": "Customer Support Session",
    "status": "active",
    "agent_id": "support-agent-v1",
    "created_at": "2025-12-24T10:00:00Z",
    "updated_at": "2025-12-24T10:05:00Z",
    "message_count": 5,
    "metadata": {}
}
```

---

#### List Sessions

Lists all sessions with pagination.

```http
GET /api/v1/sessions/
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `status` | string | - | Filter by status |
| `agent_id` | string | - | Filter by agent |

**Response:**

```json
{
    "data": [
        {
            "id": "sess_abc123def456",
            "title": "Customer Support Session",
            "status": "active",
            "created_at": "2025-12-24T10:00:00Z"
        }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20
}
```

---

#### End Session

Ends an active session.

```http
POST /api/v1/sessions/{session_id}/end
```

**Response:**

```json
{
    "id": "sess_abc123def456",
    "status": "ended",
    "ended_at": "2025-12-24T11:00:00Z"
}
```

---

### Chat

#### Send Message

Sends a message and receives agent response.

```http
POST /api/v1/sessions/{session_id}/chat
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Message content |
| `stream` | boolean | No | Enable streaming (default: false) |
| `attachments` | array | No | File attachments |

**Example Request:**

```json
{
    "content": "What is the status of order #12345?",
    "stream": false
}
```

**Example Response (Non-streaming):**

```json
{
    "session_id": "sess_abc123def456",
    "message_id": "msg_xyz789",
    "role": "assistant",
    "content": "Order #12345 is currently in transit and expected to arrive on December 26th.",
    "tool_calls": [],
    "created_at": "2025-12-24T10:05:30Z",
    "usage": {
        "prompt_tokens": 45,
        "completion_tokens": 28,
        "total_tokens": 73
    }
}
```

---

#### Stream Chat Response

Sends a message and receives streaming response via SSE.

```http
POST /api/v1/sessions/{session_id}/chat/stream
```

**Request Body:**

```json
{
    "content": "Tell me a story about a brave knight."
}
```

**Response (SSE Stream):**

```
data: {"type": "content", "delta": "Once upon"}
data: {"type": "content", "delta": " a time,"}
data: {"type": "content", "delta": " there was"}
data: {"type": "tool_call", "tool": "search", "args": {...}}
data: {"type": "done", "usage": {"total_tokens": 150}}
```

---

### Messages

#### Get Messages

Retrieves message history for a session.

```http
GET /api/v1/sessions/{session_id}/messages
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max messages to return |
| `before` | string | - | Cursor for pagination |
| `after` | string | - | Cursor for pagination |

**Response:**

```json
{
    "data": [
        {
            "id": "msg_001",
            "role": "user",
            "content": "Hello!",
            "created_at": "2025-12-24T10:00:00Z"
        },
        {
            "id": "msg_002",
            "role": "assistant",
            "content": "Hello! How can I help you today?",
            "created_at": "2025-12-24T10:00:05Z"
        }
    ],
    "has_more": false
}
```

---

### Approvals

#### List Pending Approvals

Lists pending tool call approvals.

```http
GET /api/v1/sessions/{session_id}/approvals
```

**Response:**

```json
{
    "data": [
        {
            "id": "appr_123",
            "tool_name": "send_email",
            "arguments": {
                "to": "customer@example.com",
                "subject": "Order Update"
            },
            "status": "pending",
            "created_at": "2025-12-24T10:10:00Z",
            "expires_at": "2025-12-24T10:40:00Z"
        }
    ]
}
```

---

#### Approve Tool Call

Approves a pending tool call.

```http
POST /api/v1/sessions/{session_id}/approvals/{approval_id}/approve
```

**Request Body:**

```json
{
    "comment": "Approved by supervisor"
}
```

**Response:**

```json
{
    "id": "appr_123",
    "status": "approved",
    "approved_by": "user@example.com",
    "approved_at": "2025-12-24T10:15:00Z"
}
```

---

#### Reject Tool Call

Rejects a pending tool call.

```http
POST /api/v1/sessions/{session_id}/approvals/{approval_id}/reject
```

**Request Body:**

```json
{
    "reason": "Invalid recipient email",
    "comment": "Please verify the email address"
}
```

**Response:**

```json
{
    "id": "appr_123",
    "status": "rejected",
    "rejected_by": "user@example.com",
    "rejected_at": "2025-12-24T10:15:00Z",
    "reason": "Invalid recipient email"
}
```

---

## WebSocket API

### Connection

```
wss://api.ipa-platform.com/ws/sessions/{session_id}
```

### Authentication

Include token in query parameter or first message:

```javascript
// Option 1: Query parameter
const ws = new WebSocket('wss://api.ipa-platform.com/ws/sessions/sess_123?token=<access_token>');

// Option 2: First message
ws.send(JSON.stringify({
    type: 'auth',
    token: '<access_token>'
}));
```

### Message Types

#### Client → Server

| Type | Description | Payload |
|------|-------------|---------|
| `auth` | Authentication | `{token: string}` |
| `message` | Send message | `{content: string, attachments?: array}` |
| `ping` | Keep-alive | `{}` |
| `cancel` | Cancel operation | `{operation_id?: string}` |

#### Server → Client

| Type | Description | Payload |
|------|-------------|---------|
| `auth_success` | Auth successful | `{session_id: string}` |
| `message_start` | Response start | `{message_id: string}` |
| `content_delta` | Content chunk | `{delta: string}` |
| `tool_call` | Tool invocation | `{tool: string, args: object}` |
| `tool_result` | Tool result | `{tool: string, result: any}` |
| `approval_required` | Needs approval | `{approval_id: string, tool: string}` |
| `message_end` | Response complete | `{usage: object}` |
| `error` | Error occurred | `{code: string, message: string}` |
| `pong` | Keep-alive response | `{}` |

### Example WebSocket Flow

```javascript
const ws = new WebSocket('wss://api.ipa-platform.com/ws/sessions/sess_123');

ws.onopen = () => {
    // Authenticate
    ws.send(JSON.stringify({ type: 'auth', token: 'your_token' }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'auth_success':
            console.log('Connected to session:', data.session_id);
            break;
        case 'content_delta':
            process.stdout.write(data.delta);
            break;
        case 'approval_required':
            console.log('Approval needed for:', data.tool);
            break;
        case 'message_end':
            console.log('\nTokens used:', data.usage.total_tokens);
            break;
        case 'error':
            console.error('Error:', data.message);
            break;
    }
};

// Send a message
ws.send(JSON.stringify({
    type: 'message',
    content: 'Hello, how can you help me?'
}));
```

---

## Error Codes

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource state conflict |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Server Error |

### Session Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SESSION_NOT_FOUND` | 404 | Session does not exist |
| `SESSION_ENDED` | 409 | Cannot operate on ended session |
| `SESSION_SUSPENDED` | 409 | Session is suspended |
| `SESSION_CREATE_FAILED` | 500 | Failed to create session |
| `SESSION_UPDATE_FAILED` | 500 | Failed to update session |

### Message Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `MESSAGE_EMPTY` | 400 | Message content is empty |
| `MESSAGE_TOO_LONG` | 400 | Message exceeds max length |
| `MESSAGE_INVALID` | 400 | Invalid message format |
| `MESSAGE_SEND_FAILED` | 500 | Failed to send message |

### Agent Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AGENT_NOT_FOUND` | 404 | Agent does not exist |
| `AGENT_UNAVAILABLE` | 503 | Agent is not available |
| `AGENT_ERROR` | 500 | Agent processing error |
| `AGENT_TIMEOUT` | 504 | Agent response timeout |

### Tool Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TOOL_NOT_FOUND` | 404 | Tool does not exist |
| `TOOL_EXEC_FAILED` | 500 | Tool execution failed |
| `TOOL_TIMEOUT` | 504 | Tool execution timeout |
| `TOOL_APPROVAL_REQUIRED` | 403 | Tool requires approval |
| `TOOL_APPROVAL_DENIED` | 403 | Tool approval was denied |
| `TOOL_APPROVAL_EXPIRED` | 410 | Approval request expired |

### Approval Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `APPROVAL_NOT_FOUND` | 404 | Approval request not found |
| `APPROVAL_EXPIRED` | 410 | Approval request expired |
| `APPROVAL_ALREADY_PROCESSED` | 409 | Already approved/rejected |
| `APPROVAL_INVALID` | 400 | Invalid approval action |

### WebSocket Error Codes

| Code | Description |
|------|-------------|
| `WS_AUTH_FAILED` | WebSocket authentication failed |
| `WS_SESSION_INVALID` | Invalid session for WebSocket |
| `WS_CONNECTION_CLOSED` | Connection closed unexpectedly |
| `WS_MESSAGE_INVALID` | Invalid WebSocket message format |

---

## Usage Examples

### cURL

#### Create Session and Send Message

```bash
# Create session
SESSION=$(curl -s -X POST "http://localhost:8000/api/v1/sessions/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}' | jq -r '.id')

echo "Session ID: $SESSION"

# Send message
curl -X POST "http://localhost:8000/api/v1/sessions/$SESSION/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, how are you?"}'
```

#### Streaming Response

```bash
curl -N -X POST "http://localhost:8000/api/v1/sessions/$SESSION/chat/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"content": "Tell me a joke"}'
```

---

### Python

#### Basic Usage

```python
import httpx
import asyncio

API_BASE = "http://localhost:8000/api/v1"
TOKEN = "your_access_token"

async def main():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Create session
        response = await client.post(
            f"{API_BASE}/sessions/",
            headers=headers,
            json={"title": "Python Test Session"}
        )
        session = response.json()
        session_id = session["id"]
        print(f"Created session: {session_id}")

        # Send message
        response = await client.post(
            f"{API_BASE}/sessions/{session_id}/chat",
            headers=headers,
            json={"content": "What is 2 + 2?"}
        )
        result = response.json()
        print(f"Agent response: {result['content']}")

        # End session
        await client.post(
            f"{API_BASE}/sessions/{session_id}/end",
            headers=headers
        )
        print("Session ended")

asyncio.run(main())
```

#### Streaming with SSE

```python
import httpx
import asyncio

async def stream_chat(session_id: str, content: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{API_BASE}/sessions/{session_id}/chat/stream",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"content": content}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data["type"] == "content":
                        print(data["delta"], end="", flush=True)
                    elif data["type"] == "done":
                        print(f"\n[Tokens: {data['usage']['total_tokens']}]")
```

#### WebSocket Client

```python
import asyncio
import websockets
import json

async def websocket_chat():
    uri = f"wss://api.ipa-platform.com/ws/sessions/{session_id}"

    async with websockets.connect(uri) as ws:
        # Authenticate
        await ws.send(json.dumps({"type": "auth", "token": TOKEN}))

        auth_response = await ws.recv()
        print(f"Auth: {auth_response}")

        # Send message
        await ws.send(json.dumps({
            "type": "message",
            "content": "Hello via WebSocket!"
        }))

        # Receive responses
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(message)

                if data["type"] == "content_delta":
                    print(data["delta"], end="", flush=True)
                elif data["type"] == "message_end":
                    print("\n[Complete]")
                    break
                elif data["type"] == "error":
                    print(f"\nError: {data['message']}")
                    break
            except asyncio.TimeoutError:
                break

asyncio.run(websocket_chat())
```

---

### JavaScript

#### Fetch API

```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const TOKEN = 'your_access_token';

async function chat(sessionId, content) {
    const response = await fetch(`${API_BASE}/sessions/${sessionId}/chat`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    });

    return response.json();
}

// Usage
const session = await createSession();
const result = await chat(session.id, 'Hello!');
console.log(result.content);
```

#### EventSource for SSE

```javascript
function streamChat(sessionId, content) {
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(
            `${API_BASE}/sessions/${sessionId}/chat/stream`,
            {
                headers: { 'Authorization': `Bearer ${TOKEN}` }
            }
        );

        let fullContent = '';

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'content':
                    fullContent += data.delta;
                    console.log(data.delta);
                    break;
                case 'done':
                    eventSource.close();
                    resolve({ content: fullContent, usage: data.usage });
                    break;
            }
        };

        eventSource.onerror = (error) => {
            eventSource.close();
            reject(error);
        };
    });
}
```

#### WebSocket Client

```javascript
class SessionWebSocket {
    constructor(sessionId, token) {
        this.ws = new WebSocket(`wss://api.ipa-platform.com/ws/sessions/${sessionId}`);
        this.token = token;
        this.messageHandlers = [];

        this.ws.onopen = () => {
            this.ws.send(JSON.stringify({ type: 'auth', token: this.token }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(data));
        };
    }

    send(content) {
        this.ws.send(JSON.stringify({ type: 'message', content }));
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    close() {
        this.ws.close();
    }
}

// Usage
const ws = new SessionWebSocket('sess_123', 'your_token');
ws.onMessage((data) => {
    if (data.type === 'content_delta') {
        document.getElementById('output').textContent += data.delta;
    }
});
ws.send('Hello!');
```

---

## Best Practices

### 1. Session Management

- **Reuse Sessions**: For multi-turn conversations, reuse the same session
- **End Sessions**: Always end sessions when done to free resources
- **Metadata**: Use metadata for tracking and analytics
- **Timeouts**: Handle session timeouts gracefully

```python
# Good: Reuse session for conversation
session = await create_session()
for message in conversation:
    await send_message(session.id, message)
await end_session(session.id)

# Bad: Create new session for each message
for message in conversation:
    session = await create_session()
    await send_message(session.id, message)
    # Session left dangling
```

### 2. Error Handling

- **Retry Strategy**: Implement exponential backoff for transient errors
- **Error Logging**: Log error codes and details for debugging
- **User Feedback**: Provide meaningful error messages to users

```python
async def send_with_retry(session_id, content, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await send_message(session_id, content)
        except HTTPError as e:
            if e.status_code == 429:  # Rate limited
                await asyncio.sleep(2 ** attempt)
            elif e.status_code >= 500:  # Server error
                await asyncio.sleep(1)
            else:
                raise  # Client error, don't retry
    raise MaxRetriesExceeded()
```

### 3. Streaming

- **Buffer Management**: Process chunks efficiently
- **Connection Handling**: Handle disconnections gracefully
- **Cancellation**: Support cancelling long-running streams

```javascript
// Good: Handle stream cancellation
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000);

try {
    await streamChat(sessionId, content, controller.signal);
} finally {
    clearTimeout(timeoutId);
}
```

### 4. Approvals

- **Timeout Handling**: Handle approval timeouts appropriately
- **User Notification**: Notify users of pending approvals promptly
- **Audit Trail**: Log all approval decisions

```python
async def handle_approval_required(approval):
    # Notify approvers
    await notify_approvers(approval)

    # Set timeout handler
    asyncio.create_task(check_approval_timeout(approval.id, approval.expires_at))
```

### 5. Performance

- **Connection Pooling**: Use connection pooling for HTTP clients
- **Caching**: Cache session metadata when appropriate
- **Pagination**: Use pagination for large result sets

```python
# Good: Use connection pooling
client = httpx.AsyncClient(limits=httpx.Limits(max_connections=100))

# Good: Paginate large results
async def get_all_sessions():
    sessions = []
    page = 1
    while True:
        result = await get_sessions(page=page, page_size=100)
        sessions.extend(result['data'])
        if not result['has_more']:
            break
        page += 1
    return sessions
```

### 6. Security

- **Token Storage**: Store tokens securely
- **Token Refresh**: Implement token refresh before expiration
- **Input Validation**: Validate all user inputs
- **Rate Limiting**: Respect rate limits

```javascript
// Good: Refresh token before expiration
class TokenManager {
    async getToken() {
        if (this.isTokenExpired()) {
            await this.refreshToken();
        }
        return this.token;
    }
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Session Create | 10 | 1 minute |
| Chat Message | 60 | 1 minute |
| Chat Stream | 30 | 1 minute |
| Get Session | 120 | 1 minute |
| List Sessions | 30 | 1 minute |

When rate limited, the API returns:

```json
{
    "error": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after": 30
}
```

---

## Changelog

### v1.0.0 (2025-12-24)

- Initial release of Session-Agent Integration API
- Session CRUD operations
- Chat with streaming support
- Tool approval workflow
- WebSocket real-time communication
- Comprehensive error handling

---

**Last Updated**: 2025-12-24
**API Version**: 1.0.0
**Sprint**: S47-4 (Phase 11)
