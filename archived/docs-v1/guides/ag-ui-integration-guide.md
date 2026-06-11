# AG-UI Protocol Integration Guide

> Phase 15: AG-UI Protocol Integration - Developer Guide (Sprint 58-60)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Frontend Integration](#frontend-integration)
5. [Backend Integration](#backend-integration)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

The AG-UI (Agent-UI) Protocol provides a standardized way for AI agents to interact with user interfaces. This guide covers:

- **Sprint 58**: Core AG-UI infrastructure (protocol events, bridge, converters)
- **Sprint 59**: Feature extensions (tool rendering, generative UI)
- **Sprint 60**: Advanced features (shared state, optimistic updates)

### Key Benefits

- **Standardized Events**: Common event format for all agent interactions
- **Streaming Support**: Real-time SSE streaming for responsive UIs
- **State Management**: Thread-scoped state with optimistic concurrency
- **Generative UI**: Dynamic UI components based on agent responses
- **Tool Approval**: Human-in-the-loop workflow for sensitive operations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │useSharedState│   │useOptimistic │   │CustomUIRenderer│   │
│  │    Hook     │    │  State Hook  │    │   Component   │   │
│  └─────────────┘    └──────────────┘    └───────────────┘   │
│         │                  │                    │            │
│         ▼                  ▼                    ▼            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   AG-UI Components                       │ │
│  │  DynamicForm | DynamicChart | DynamicCard | DynamicTable │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────┘
                                │ SSE / REST
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │ AG-UI Routes│───→│ AG-UI Bridge │───→│Event Converters│  │
│  └─────────────┘    └──────────────┘    └───────────────┘   │
│         │                  │                    │            │
│         ▼                  ▼                    ▼            │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │SharedState  │    │ToolApproval  │    │GenerativeUI   │   │
│  │  Handler    │    │  Handler     │    │   Handler     │   │
│  └─────────────┘    └──────────────┘    └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- Redis (for state storage)

### Installation

#### Frontend

```bash
cd frontend
npm install
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Basic Usage

#### 1. Create a Thread

```typescript
// Frontend
const threadId = `thread-${Date.now()}`;
```

#### 2. Send a Message

```typescript
// Using useSharedState hook
import { useSharedState } from '@/hooks/useSharedState';

function ChatComponent() {
  const { state, set, isConnected } = useSharedState(threadId);

  const sendMessage = async (input: string) => {
    const response = await fetch('/api/v1/ag-ui/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, input })
    });
    return response.json();
  };

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <button onClick={() => sendMessage('Hello!')}>Send</button>
    </div>
  );
}
```

#### 3. Stream Response

```typescript
// Using SSE streaming
const eventSource = new EventSource(
  `/api/v1/ag-ui/stream?thread_id=${threadId}&input=${encodeURIComponent(input)}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};

eventSource.onerror = () => {
  eventSource.close();
};
```

---

## Frontend Integration

### Components

#### CustomUIRenderer

Renders dynamic UI components based on agent responses.

```tsx
import { CustomUIRenderer } from '@/components/ag-ui/advanced';

function AgentResponse({ components }) {
  return (
    <CustomUIRenderer
      components={components}
      onComponentEvent={(event) => console.log(event)}
    />
  );
}
```

#### DynamicForm

Renders forms with validation and submission handling.

```tsx
import { DynamicForm } from '@/components/ag-ui/advanced';

<DynamicForm
  formId="user-form"
  fields={[
    { name: 'email', type: 'email', label: 'Email', required: true },
    { name: 'message', type: 'textarea', label: 'Message' }
  ]}
  onSubmit={(data) => console.log(data)}
/>
```

#### DynamicChart

Renders charts using Recharts.

```tsx
import { DynamicChart } from '@/components/ag-ui/advanced';

<DynamicChart
  chartType="bar"
  data={[
    { name: 'Jan', value: 100 },
    { name: 'Feb', value: 150 }
  ]}
  xAxisKey="name"
  yAxisKey="value"
/>
```

### Hooks

#### useSharedState

Manages shared state with server synchronization.

```tsx
import { useSharedState } from '@/hooks/useSharedState';

function StateManager() {
  const {
    state,           // Current state
    get,             // Get value by path
    set,             // Set value at path
    remove,          // Remove value at path
    isConnected,     // SSE connection status
    isSyncing,       // Sync in progress
    error,           // Last error
    forceSync,       // Force sync with server
    version          // Current version
  } = useSharedState('thread-123', {
    syncInterval: 5000,      // Auto-sync every 5s
    enableSSE: true,         // Enable SSE
    onConflict: 'server-wins' // Conflict resolution
  });

  return (
    <div>
      <p>Counter: {get('counter', 0)}</p>
      <button onClick={() => set('counter', get('counter', 0) + 1)}>
        Increment
      </button>
    </div>
  );
}
```

#### useOptimisticState

Manages optimistic updates with rollback support.

```tsx
import { useOptimisticState } from '@/hooks/useOptimisticState';

function OptimisticCounter() {
  const {
    state,              // Current state (including pending)
    confirmedState,     // Last confirmed state
    pendingPredictions, // Pending predictions
    optimisticUpdate,   // Apply optimistic update
    confirmPrediction,  // Confirm a prediction
    rollbackPrediction, // Rollback a prediction
    hasPending          // Has pending predictions
  } = useOptimisticState({
    counter: 0
  }, {
    predictionTimeout: 5000,
    maxPendingPredictions: 10
  });

  const increment = () => {
    const predictionId = optimisticUpdate(
      { counter: state.counter + 1 },
      'increment'
    );

    // Simulate server confirmation
    setTimeout(() => {
      confirmPrediction(predictionId);
    }, 1000);
  };

  return (
    <div>
      <p>Counter: {state.counter}</p>
      {hasPending && <span>Saving...</span>}
      <button onClick={increment}>+1</button>
    </div>
  );
}
```

### StateDebugger

Debug component for visualizing state.

```tsx
import { StateDebugger } from '@/components/ag-ui/advanced';

<StateDebugger
  state={state}
  pendingPredictions={pendingPredictions}
  confirmedState={confirmedState}
  isConnected={isConnected}
/>
```

---

## Backend Integration

### Routes

The AG-UI routes are registered at `/api/v1/ag-ui/`:

```python
# backend/src/api/v1/ag_ui/routes.py
from fastapi import APIRouter
from .routes import router as ag_ui_router

# In main.py or api/__init__.py
app.include_router(ag_ui_router, prefix="/api/v1/ag-ui", tags=["AG-UI"])
```

### Handlers

#### SharedStateHandler

```python
from src.integrations.ag_ui.shared_state import SharedStateHandler

handler = SharedStateHandler()

# Get state
state = await handler.get_state(thread_id)

# Update state
new_state = await handler.update_state(
    thread_id=thread_id,
    state={"counter": 5},
    version=1
)

# Delete state
await handler.delete_state(thread_id)
```

#### ToolApprovalHandler

```python
from src.integrations.ag_ui.tool_approval import ToolApprovalHandler

handler = ToolApprovalHandler()

# Create approval request
approval_id = await handler.create_approval(
    thread_id=thread_id,
    tool_name="file_write",
    tool_args={"path": "/tmp/test.txt"}
)

# List pending
pending = await handler.list_pending(thread_id=thread_id)

# Approve/Reject
await handler.approve(approval_id)
await handler.reject(approval_id, reason="Not authorized")
```

#### GenerativeUIHandler

```python
from src.integrations.ag_ui.generative_ui import GenerativeUIHandler

handler = GenerativeUIHandler()

# Render UI component
component = await handler.render_component(
    component_type="chart",
    props={
        "chart_type": "bar",
        "data": [{"x": 1, "y": 10}]
    }
)
```

### Event Converters

Convert between internal events and AG-UI protocol events:

```python
from src.integrations.ag_ui.converters import AGUIEventConverter

converter = AGUIEventConverter()

# Convert internal event to AG-UI event
ag_ui_event = converter.to_ag_ui_event(internal_event)

# Convert AG-UI event to internal event
internal_event = converter.from_ag_ui_event(ag_ui_event)
```

---

## Advanced Features

### 1. Optimistic Concurrency

Handle concurrent updates with version tracking:

```typescript
const { set, version } = useSharedState(threadId);

try {
  await set('counter', newValue, { version });
} catch (error) {
  if (error.code === 'VERSION_CONFLICT') {
    // Handle conflict - refresh and retry
    await forceSync();
  }
}
```

### 2. Conflict Resolution

Configure conflict resolution strategy:

```typescript
const { state } = useSharedState(threadId, {
  onConflict: 'server-wins' | 'client-wins' | 'manual',
  conflictResolver: (clientState, serverState) => {
    // Custom merge logic
    return { ...serverState, ...clientState };
  }
});
```

### 3. Predictive Updates

Track prediction lifecycle:

```typescript
const { pendingPredictions } = useOptimisticState(initialState);

// Each prediction has:
// - id: Unique identifier
// - status: 'pending' | 'confirmed' | 'rolled_back' | 'expired' | 'conflicted'
// - createdAt: Timestamp
// - expiresAt: Expiration timestamp
```

### 4. State Diffs

Apply incremental state updates:

```typescript
const diffs: StateDiff[] = [
  { op: 'add', path: '/items/-', value: 'new item' },
  { op: 'replace', path: '/counter', value: 10 },
  { op: 'remove', path: '/temp' }
];

await applyDiffs(diffs);
```

### 5. Tool Approval Workflow

Handle sensitive operations:

```python
# Backend: Create approval request
async def handle_tool_call(tool_name: str, tool_args: dict):
    if tool_name in SENSITIVE_TOOLS:
        approval_id = await approval_handler.create_approval(
            thread_id=thread_id,
            tool_name=tool_name,
            tool_args=tool_args
        )
        # Wait for approval or timeout
        return await approval_handler.wait_for_decision(
            approval_id,
            timeout=300  # 5 minutes
        )
    else:
        # Execute immediately
        return await execute_tool(tool_name, tool_args)
```

```typescript
// Frontend: Show approval UI
function ApprovalPanel() {
  const [pending, setPending] = useState<Approval[]>([]);

  useEffect(() => {
    const fetchPending = async () => {
      const response = await fetch('/api/v1/ag-ui/approvals/pending');
      setPending(await response.json());
    };
    fetchPending();
    const interval = setInterval(fetchPending, 5000);
    return () => clearInterval(interval);
  }, []);

  const approve = async (id: string) => {
    await fetch(`/api/v1/ag-ui/approvals/${id}/approve`, {
      method: 'POST'
    });
  };

  return (
    <div>
      {pending.map(approval => (
        <div key={approval.id}>
          <p>Tool: {approval.tool_name}</p>
          <button onClick={() => approve(approval.id)}>Approve</button>
        </div>
      ))}
    </div>
  );
}
```

---

## Troubleshooting

### Common Issues

#### 1. SSE Connection Drops

**Problem**: SSE connection frequently disconnects.

**Solution**:
```typescript
// Implement reconnection logic
const connect = () => {
  const eventSource = new EventSource(url);

  eventSource.onerror = () => {
    eventSource.close();
    setTimeout(connect, 3000); // Reconnect after 3s
  };
};
```

#### 2. Version Conflicts

**Problem**: Frequent version conflicts in state updates.

**Solution**:
- Reduce sync interval
- Implement client-side merge
- Use optimistic updates with rollback

#### 3. State Too Large

**Problem**: State exceeds size limits.

**Solution**:
- Store large data separately (files, database)
- Use references instead of embedding
- Implement pagination for lists

#### 4. Tool Approval Timeout

**Problem**: Tool approvals expire before decision.

**Solution**:
- Increase timeout duration
- Implement notifications
- Show pending approvals prominently

### Debug Mode

Enable debug mode for detailed logging:

```typescript
// Frontend
const { state } = useSharedState(threadId, {
  debug: true  // Logs all state changes
});
```

```python
# Backend
import logging
logging.getLogger('ag_ui').setLevel(logging.DEBUG)
```

### Performance Tips

1. **Batch State Updates**: Combine multiple updates into single request
2. **Debounce Sync**: Don't sync on every keystroke
3. **Use Diffs**: Send incremental updates instead of full state
4. **Cache Locally**: Store state in localStorage for fast reload
5. **Lazy Load Components**: Load heavy components on demand

---

## Related Documentation

- [AG-UI API Reference](./ag-ui-api-reference.md)
- [Session-Agent Integration](../api/session-agent-integration.md)
- [Hybrid Architecture Guide](./hybrid-architecture-guide.md)

---

**Last Updated**: 2026-01-05
**Version**: 1.0.0
**Sprint**: 60 (S60-4)
