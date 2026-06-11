# Swarm API Reference

Agent Swarm Status API for monitoring multi-agent collaboration.

## Overview

The Swarm API provides REST endpoints for querying the status of Agent Swarm executions, including overall swarm progress, individual worker states, tool calls, and extended thinking content.

## Base URL

```
/api/v1/swarm
```

## Endpoints

### Get Swarm Status

Get the current status of a swarm including all workers.

**Endpoint:** `GET /swarm/{swarm_id}`

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| swarm_id | string | path | Yes | Unique identifier of the swarm |

**Response:** `200 OK`

```json
{
  "swarm_id": "swarm-123",
  "mode": "parallel",
  "status": "running",
  "overall_progress": 65,
  "workers": [
    {
      "worker_id": "worker-1",
      "worker_name": "Research Agent",
      "worker_type": "research",
      "role": "Data Gatherer",
      "status": "running",
      "progress": 80,
      "current_task": "Searching for relevant data",
      "tool_calls_count": 3,
      "started_at": "2024-01-01T12:00:00Z",
      "completed_at": null
    },
    {
      "worker_id": "worker-2",
      "worker_name": "Writer Agent",
      "worker_type": "writer",
      "role": "Content Creator",
      "status": "pending",
      "progress": 0,
      "current_task": null,
      "tool_calls_count": 0,
      "started_at": null,
      "completed_at": null
    }
  ],
  "total_tool_calls": 3,
  "completed_tool_calls": 2,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null
}
```

**Error Response:** `404 Not Found`

```json
{
  "detail": "Swarm not found: swarm-123"
}
```

---

### List Swarm Workers

Get a list of all workers in a swarm.

**Endpoint:** `GET /swarm/{swarm_id}/workers`

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| swarm_id | string | path | Yes | Unique identifier of the swarm |

**Response:** `200 OK`

```json
{
  "swarm_id": "swarm-123",
  "workers": [
    {
      "worker_id": "worker-1",
      "worker_name": "Research Agent",
      "worker_type": "research",
      "role": "Data Gatherer",
      "status": "completed",
      "progress": 100,
      "current_task": null,
      "tool_calls_count": 5,
      "started_at": "2024-01-01T12:00:00Z",
      "completed_at": "2024-01-01T12:05:00Z"
    }
  ],
  "total": 1
}
```

**Error Response:** `404 Not Found`

---

### Get Worker Details

Get detailed information about a specific worker.

**Endpoint:** `GET /swarm/{swarm_id}/workers/{worker_id}`

**Parameters:**

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| swarm_id | string | path | Yes | Unique identifier of the swarm |
| worker_id | string | path | Yes | Unique identifier of the worker |

**Response:** `200 OK`

```json
{
  "worker_id": "worker-1",
  "worker_name": "Research Agent",
  "worker_type": "research",
  "role": "Data Gatherer",
  "status": "running",
  "progress": 75,
  "current_task": "Analyzing search results",
  "tool_calls": [
    {
      "tool_id": "tc-1",
      "tool_name": "web_search",
      "is_mcp": true,
      "input_params": {"query": "AI news 2024"},
      "status": "completed",
      "result": {"results": ["item1", "item2"]},
      "error": null,
      "started_at": "2024-01-01T12:01:00Z",
      "completed_at": "2024-01-01T12:01:30Z",
      "duration_ms": 30000
    },
    {
      "tool_id": "tc-2",
      "tool_name": "read_url",
      "is_mcp": true,
      "input_params": {"url": "https://example.com/article"},
      "status": "running",
      "result": null,
      "error": null,
      "started_at": "2024-01-01T12:02:00Z",
      "completed_at": null,
      "duration_ms": null
    }
  ],
  "thinking_contents": [
    {
      "content": "Analyzing the search results to identify the most relevant articles about AI developments...",
      "timestamp": "2024-01-01T12:01:35Z",
      "token_count": 150
    },
    {
      "content": "Cross-referencing findings with the user's requirements to ensure relevance...",
      "timestamp": "2024-01-01T12:02:15Z",
      "token_count": 100
    }
  ],
  "messages": [
    {
      "role": "assistant",
      "content": "I'm searching for the latest AI developments...",
      "timestamp": "2024-01-01T12:01:00Z"
    },
    {
      "role": "assistant",
      "content": "Found 15 relevant articles. Analyzing content...",
      "timestamp": "2024-01-01T12:01:45Z"
    }
  ],
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null,
  "error": null
}
```

**Error Responses:**

- `404 Not Found` - Swarm or worker not found

---

## Data Models

### SwarmMode

Execution mode for the swarm.

| Value | Description |
|-------|-------------|
| `sequential` | Workers execute one after another |
| `parallel` | Workers execute simultaneously |
| `hierarchical` | Workers execute in a tree structure |

### SwarmStatus

Overall status of the swarm.

| Value | Description |
|-------|-------------|
| `initializing` | Swarm is being set up |
| `running` | Swarm is actively executing |
| `paused` | Swarm is paused |
| `completed` | Swarm finished successfully |
| `failed` | Swarm failed |

### WorkerType

Type of worker.

| Value | Description |
|-------|-------------|
| `research` | Research/data gathering agent |
| `writer` | Content writing agent |
| `designer` | Design agent |
| `reviewer` | Review/validation agent |
| `coordinator` | Coordination agent |
| `analyst` | Analysis agent |
| `coder` | Coding agent |
| `tester` | Testing agent |
| `custom` | Custom agent type |

### WorkerStatus

Status of an individual worker.

| Value | Description |
|-------|-------------|
| `pending` | Worker has not started |
| `running` | Worker is actively executing |
| `thinking` | Worker is in extended thinking |
| `tool_calling` | Worker is calling a tool |
| `completed` | Worker finished successfully |
| `failed` | Worker failed |
| `cancelled` | Worker was cancelled |

### ToolCallStatus

Status of a tool call.

| Value | Description |
|-------|-------------|
| `pending` | Tool call not started |
| `running` | Tool call in progress |
| `completed` | Tool call completed |
| `failed` | Tool call failed |

---

## Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 404 | NOT_FOUND | Swarm or worker not found |
| 500 | INTERNAL_ERROR | Server error |

---

## Example Usage

### Python

```python
import httpx

# Get swarm status
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/api/v1/swarm/swarm-123")
    swarm = response.json()
    print(f"Swarm progress: {swarm['overall_progress']}%")

    # Get worker details
    for worker in swarm['workers']:
        if worker['status'] == 'running':
            detail_response = await client.get(
                f"http://localhost:8000/api/v1/swarm/swarm-123/workers/{worker['worker_id']}"
            )
            worker_detail = detail_response.json()
            print(f"Worker {worker_detail['worker_name']}: {worker_detail['current_task']}")
```

### JavaScript/TypeScript

```typescript
// Get swarm status
const response = await fetch('/api/v1/swarm/swarm-123');
const swarm = await response.json();

console.log(`Swarm progress: ${swarm.overall_progress}%`);

// Get worker details for active workers
for (const worker of swarm.workers) {
  if (worker.status === 'running') {
    const detailResponse = await fetch(
      `/api/v1/swarm/swarm-123/workers/${worker.worker_id}`
    );
    const workerDetail = await detailResponse.json();
    console.log(`Worker ${workerDetail.worker_name}: ${workerDetail.current_task}`);

    // Display extended thinking
    for (const thinking of workerDetail.thinking_contents) {
      console.log(`  💭 ${thinking.content}`);
    }
  }
}
```

### cURL

```bash
# Get swarm status
curl -X GET "http://localhost:8000/api/v1/swarm/swarm-123"

# Get all workers
curl -X GET "http://localhost:8000/api/v1/swarm/swarm-123/workers"

# Get worker details
curl -X GET "http://localhost:8000/api/v1/swarm/swarm-123/workers/worker-1"
```

---

## SSE Events

Real-time swarm events are delivered via Server-Sent Events (SSE) through the AG-UI CustomEvent format.

### Event Format

All swarm events follow the AG-UI CustomEvent structure:

```
data: {"type":"CUSTOM","event_name":"swarm_created","payload":{...}}
```

### Event Types

#### Swarm Lifecycle Events

| Event Name | Description | Priority |
|------------|-------------|----------|
| `swarm_created` | Swarm was created | High (immediate) |
| `swarm_status_update` | Swarm status snapshot | Throttled |
| `swarm_completed` | Swarm finished | High (immediate) |

#### Worker Lifecycle Events

| Event Name | Description | Priority |
|------------|-------------|----------|
| `worker_started` | Worker started execution | High (immediate) |
| `worker_progress` | Worker progress updated | Throttled |
| `worker_thinking` | Extended thinking content | Throttled |
| `worker_tool_call` | Tool call started/completed | High (immediate) |
| `worker_message` | Worker message added | Batched |
| `worker_completed` | Worker finished | High (immediate) |

### Event Payloads

#### swarm_created

```json
{
  "swarm_id": "swarm-123",
  "session_id": "session-456",
  "mode": "parallel",
  "workers": [
    {
      "worker_id": "worker-1",
      "worker_name": "DiagnosticWorker",
      "worker_type": "analyst",
      "role": "diagnostic"
    }
  ],
  "created_at": "2026-01-29T10:00:00Z"
}
```

#### swarm_status_update

```json
{
  "swarm_id": "swarm-123",
  "session_id": "session-456",
  "mode": "parallel",
  "status": "running",
  "total_workers": 3,
  "overall_progress": 65,
  "workers": [
    {
      "worker_id": "worker-1",
      "worker_name": "DiagnosticWorker",
      "worker_type": "analyst",
      "role": "diagnostic",
      "status": "completed",
      "progress": 100,
      "current_action": null,
      "tool_calls_count": 3
    }
  ],
  "metadata": {}
}
```

#### swarm_completed

```json
{
  "swarm_id": "swarm-123",
  "status": "completed",
  "summary": "Analysis complete with 3 issues found",
  "total_duration_ms": 45000,
  "completed_at": "2026-01-29T10:00:45Z"
}
```

#### worker_started

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "worker_name": "DiagnosticWorker",
  "worker_type": "analyst",
  "role": "diagnostic",
  "task_description": "Analyzing ETL Pipeline errors",
  "started_at": "2026-01-29T10:00:01Z"
}
```

#### worker_progress

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "progress": 65,
  "current_action": "Querying error logs",
  "status": "running",
  "updated_at": "2026-01-29T10:00:15Z"
}
```

#### worker_thinking

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "thinking_content": "I need to analyze the error patterns in the APAC region...",
  "token_count": 245,
  "timestamp": "2026-01-29T10:00:10Z"
}
```

#### worker_tool_call

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "tool_call_id": "tc-001",
  "tool_name": "azure:query_adf_logs",
  "status": "completed",
  "input_args": {
    "pipeline": "APAC_Glider",
    "time_range": "24h"
  },
  "output_result": {
    "error_count": 47,
    "errors": ["Connection timeout"]
  },
  "error": null,
  "duration_ms": 1245,
  "timestamp": "2026-01-29T10:00:12Z"
}
```

#### worker_message

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "role": "assistant",
  "content": "Found 47 connection timeout errors in the APAC region.",
  "tool_call_id": null,
  "timestamp": "2026-01-29T10:00:20Z"
}
```

#### worker_completed

```json
{
  "swarm_id": "swarm-123",
  "worker_id": "worker-1",
  "status": "completed",
  "result": null,
  "error": null,
  "duration_ms": 30000,
  "completed_at": "2026-01-29T10:00:31Z"
}
```

### Event Throttling

To prevent overwhelming clients, some events are throttled:

| Event Type | Throttle Interval | Notes |
|------------|-------------------|-------|
| `worker_progress` | 200ms | Only latest progress sent |
| `worker_thinking` | 200ms | Only latest thinking sent |
| `swarm_status_update` | 200ms | Full status snapshot |

### Consuming SSE Events

#### JavaScript/TypeScript

```typescript
const eventSource = new EventSource('/api/v1/ag-ui?session_id=session-123');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'CUSTOM') {
    const { event_name, payload } = data;

    switch (event_name) {
      case 'swarm_created':
        console.log('Swarm created:', payload.swarm_id);
        break;
      case 'worker_progress':
        console.log(`Worker ${payload.worker_id}: ${payload.progress}%`);
        break;
      case 'worker_thinking':
        console.log(`Thinking: ${payload.thinking_content}`);
        break;
      // ... handle other events
    }
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};
```

#### Python

```python
import httpx
import json

async def consume_events(session_id: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'GET',
            f'http://localhost:8000/api/v1/ag-ui?session_id={session_id}'
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    event_data = json.loads(line[6:])

                    if event_data.get('type') == 'CUSTOM':
                        event_name = event_data['event_name']
                        payload = event_data['payload']

                        if event_name == 'worker_thinking':
                            print(f"💭 {payload['thinking_content']}")
                        elif event_name == 'worker_progress':
                            print(f"📊 Worker {payload['worker_id']}: {payload['progress']}%")
```

---

## Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| SSE Event Latency | < 100ms | For priority events |
| API Response Time (P95) | < 200ms | GET /swarm/{id} |
| Worker Detail API (P95) | < 300ms | GET /swarm/{id}/workers/{id} |
| Event Throughput | > 50 events/sec | Sustained load |
| Memory Usage | < 50MB | Per 1000 events |

---

## Rate Limiting

Currently, no rate limiting is applied to the Swarm API. For production deployments, consider implementing:

- Request rate limiting per session
- Event throttling for high-frequency updates
- Connection limits for SSE streams

---

**Last Updated:** 2026-01-29
**Version:** 1.1.0
**Sprint:** 106 (Phase 29)
