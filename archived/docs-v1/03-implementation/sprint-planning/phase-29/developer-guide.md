# Agent Swarm Visualization Developer Guide

## Overview

This guide provides comprehensive documentation for developers integrating with or extending the Agent Swarm visualization system implemented in Phase 29.

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ AgentSwarm   │   │ WorkerDetail │   │  Extended    │        │
│  │    Panel     │   │   Drawer     │   │   Thinking   │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│           │                 │                  │                 │
│           └─────────────────┼──────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │   SwarmStore    │                          │
│                    │    (Zustand)    │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │ useSwarmEvents  │                          │
│                    │   (SSE Hook)    │                          │
│                    └────────┬────────┘                          │
└─────────────────────────────┼───────────────────────────────────┘
                              │ SSE
┌─────────────────────────────┼───────────────────────────────────┐
│                         Backend (FastAPI)                        │
├─────────────────────────────┼───────────────────────────────────┤
│                    ┌────────▼────────┐                          │
│                    │ SwarmEventEmitter│                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│  ┌──────────────┐   ┌──────▼───────┐   ┌──────────────┐        │
│  │  Swarm API   │   │ SwarmTracker │   │ AG-UI Events │        │
│  │   Routes     │◄──│              │──►│              │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Backend: ClaudeCoordinator starts multi-agent task
        │
        ▼
2. Backend: SwarmIntegration creates swarm in SwarmTracker
        │
        ▼
3. Backend: SwarmEventEmitter emits swarm_created event
        │
        ▼ (SSE)
4. Frontend: useSwarmEvents receives event
        │
        ▼
5. Frontend: useSwarmEventHandler updates SwarmStore
        │
        ▼
6. Frontend: Components re-render with new state
```

## Backend Integration

### SwarmTracker Usage

The `SwarmTracker` is the central state manager for all swarm operations.

```python
from src.integrations.swarm import (
    SwarmTracker,
    SwarmMode,
    WorkerType,
    set_swarm_tracker,
    get_swarm_tracker,
)

# Get or create tracker
tracker = get_swarm_tracker()

# Create a new swarm
swarm = tracker.create_swarm(
    swarm_id="swarm-123",
    mode=SwarmMode.PARALLEL,
    metadata={"task": "ETL Analysis"},
)

# Start a worker
tracker.start_worker(
    swarm_id="swarm-123",
    worker_id="worker-1",
    worker_name="DiagnosticWorker",
    worker_type=WorkerType.ANALYST,
    role="diagnostic",
    current_task="Analyzing pipeline errors",
)

# Update progress
tracker.update_worker_progress("swarm-123", "worker-1", 50)

# Add thinking content
tracker.add_worker_thinking(
    "swarm-123", "worker-1",
    content="Analyzing error patterns...",
    token_count=120,
)

# Add tool call
tracker.add_worker_tool_call(
    "swarm-123", "worker-1",
    tool_id="tc-001",
    tool_name="azure:query_adf_logs",
    is_mcp=True,
    input_params={"pipeline": "APAC_ETL"},
)

# Update tool call result
tracker.update_tool_call_result(
    "swarm-123", "worker-1", "tc-001",
    result={"error_count": 47},
)

# Complete worker
tracker.complete_worker("swarm-123", "worker-1")

# Complete swarm
tracker.complete_swarm("swarm-123")
```

### SwarmEventEmitter Usage

The `SwarmEventEmitter` converts tracker state changes to SSE events.

```python
from src.integrations.swarm.events import create_swarm_emitter

async def event_callback(event):
    """Send event via SSE."""
    await send_sse_event(event)

# Create emitter
emitter = create_swarm_emitter(
    event_callback=event_callback,
    throttle_interval_ms=200,  # Throttle rapid events
    batch_size=5,              # Batch non-priority events
)

# Start emitter
await emitter.start()

# Emit events
swarm = tracker.get_swarm("swarm-123")
await emitter.emit_swarm_created(swarm, session_id="session-456")

worker = swarm.get_worker_by_id("worker-1")
await emitter.emit_worker_started("swarm-123", worker)
await emitter.emit_worker_progress("swarm-123", worker)
await emitter.emit_worker_thinking("swarm-123", worker, "Thinking...", 50)

# Stop emitter (flushes pending events)
await emitter.stop()
```

### SwarmIntegration for ClaudeCoordinator

The `SwarmIntegration` class provides hooks for the ClaudeCoordinator.

```python
from src.integrations.swarm.swarm_integration import SwarmIntegration

class MyCoordinator:
    def __init__(self):
        self.swarm_integration = SwarmIntegration(
            tracker=get_swarm_tracker(),
            emitter=my_emitter,
        )

    async def coordinate(self, task: str, session_id: str):
        # Create swarm
        swarm_id = await self.swarm_integration.on_coordination_started(
            session_id=session_id,
            mode="parallel",
            subtasks=["Diagnose", "Analyze", "Remediate"],
        )

        # Start subtask
        await self.swarm_integration.on_subtask_started(
            swarm_id=swarm_id,
            worker_id="worker-1",
            worker_name="DiagnosticWorker",
            role="diagnostic",
            task_description="Analyzing errors...",
        )

        # Update progress
        await self.swarm_integration.on_subtask_progress(
            swarm_id=swarm_id,
            worker_id="worker-1",
            progress=50,
        )

        # Handle thinking
        await self.swarm_integration.on_thinking(
            swarm_id=swarm_id,
            worker_id="worker-1",
            content="Analyzing the problem...",
            token_count=120,
        )

        # Handle tool call
        await self.swarm_integration.on_tool_call(
            swarm_id=swarm_id,
            worker_id="worker-1",
            tool_id="tc-001",
            tool_name="query_logs",
            input_params={"query": "SELECT * FROM errors"},
            result={"count": 47},
        )

        # Complete subtask
        await self.swarm_integration.on_subtask_completed(
            swarm_id=swarm_id,
            worker_id="worker-1",
        )

        # Complete coordination
        await self.swarm_integration.on_coordination_completed(swarm_id=swarm_id)
```

## Frontend Integration

### SwarmStore (Zustand)

The SwarmStore manages all swarm state on the frontend.

```typescript
import { useSwarmStore } from '@/stores/swarmStore';

// Access state
const swarmStatus = useSwarmStore((state) => state.swarmStatus);
const selectedWorkerId = useSwarmStore((state) => state.selectedWorkerId);
const isDrawerOpen = useSwarmStore((state) => state.isDrawerOpen);

// Use selectors for optimized access
import { selectRunningWorkers, selectSwarmProgress } from '@/stores/swarmStore';

const runningWorkers = useSwarmStore(selectRunningWorkers);
const progress = useSwarmStore(selectSwarmProgress);

// Actions
const { setSwarmStatus, addWorker, updateWorkerProgress, selectWorker } = useSwarmStore();

// Update state
setSwarmStatus(newSwarmStatus);
addWorker(workerSummary);
updateWorkerProgress(workerId, 75);
selectWorker(workerId);
```

### useSwarmStatus Hook

The `useSwarmStatus` hook provides computed properties and stable handlers.

```typescript
import { useSwarmStatus } from '@/components/unified-chat/agent-swarm/hooks';

function MyComponent() {
  const {
    // State
    swarmStatus,
    selectedWorkerId,
    selectedWorkerDetail,
    isDrawerOpen,
    isLoading,
    error,

    // Computed properties
    isSwarmActive,
    isSwarmCompleted,
    completedWorkers,
    runningWorkers,
    pendingWorkers,
    failedWorkers,
    totalProgress,
    workersCount,

    // Actions
    handleWorkerSelect,
    handleDrawerClose,
    reset,
  } = useSwarmStatus();

  return (
    <div>
      {isSwarmActive && <p>Swarm is running...</p>}
      <p>Progress: {totalProgress}%</p>
      <p>Workers: {workersCount.completed}/{workersCount.total}</p>
      {runningWorkers.map(worker => (
        <WorkerCard
          key={worker.workerId}
          worker={worker}
          onClick={() => handleWorkerSelect(worker.workerId)}
        />
      ))}
    </div>
  );
}
```

### useSwarmEvents Hook

The `useSwarmEvents` hook connects to SSE and parses events.

```typescript
import { useSwarmEvents } from '@/components/unified-chat/agent-swarm/hooks';

function MyComponent({ sessionId }: { sessionId: string }) {
  const { events, isConnected, error } = useSwarmEvents(sessionId);

  // Events are parsed CustomEvent objects
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      console.log('New event:', latestEvent.eventName, latestEvent.payload);
    }
  }, [events]);

  return (
    <div>
      {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      {error && <p>Error: {error.message}</p>}
    </div>
  );
}
```

### useSwarmEventHandler Hook

The `useSwarmEventHandler` hook bridges SSE events to the store.

```typescript
import { useSwarmEventHandler } from '@/components/unified-chat/agent-swarm/hooks';

function ChatContainer({ sessionId }: { sessionId: string }) {
  const { events, isConnected } = useSwarmEvents(sessionId);

  // Automatically updates SwarmStore when events arrive
  useSwarmEventHandler(events, {
    debug: true, // Log events to console
    onSwarmCreated: (payload) => console.log('Swarm created:', payload.swarmId),
    onSwarmCompleted: (payload) => console.log('Swarm completed:', payload.status),
    onError: (error) => console.error('Event error:', error),
  });

  return <OrchestrationPanel showSwarmPanel={true} />;
}
```

### Component Usage

#### AgentSwarmPanel

```typescript
import { AgentSwarmPanel } from '@/components/unified-chat/agent-swarm';

<AgentSwarmPanel
  swarmStatus={swarmStatus}
  onWorkerClick={handleWorkerSelect}
/>
```

#### WorkerDetailDrawer

```typescript
import { WorkerDetailDrawer } from '@/components/unified-chat/agent-swarm';

<WorkerDetailDrawer
  open={isDrawerOpen}
  onClose={handleDrawerClose}
  swarmId={swarmStatus?.swarmId}
  worker={selectedWorker}
/>
```

#### ExtendedThinkingPanel

```typescript
import { ExtendedThinkingPanel } from '@/components/unified-chat/agent-swarm';

<ExtendedThinkingPanel
  thinkingContents={workerDetail.thinkingContents}
  isLoading={isThinkingLoading}
/>
```

## State Management

### Store Structure

```typescript
interface SwarmState {
  // Core state
  swarmStatus: UIAgentSwarmStatus | null;
  selectedWorkerId: string | null;
  selectedWorkerDetail: WorkerDetail | null;
  isDrawerOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Swarm actions
  setSwarmStatus: (status: UIAgentSwarmStatus | null) => void;
  updateSwarmProgress: (progress: number) => void;
  completeSwarm: (status: string) => void;

  // Worker actions
  addWorker: (worker: UIWorkerSummary) => void;
  updateWorkerProgress: (workerId: string, progress: number) => void;
  updateWorkerThinking: (workerId: string, thinking: string) => void;
  updateWorkerToolCall: (workerId: string, toolCall: ToolCallUpdate) => void;
  completeWorker: (workerId: string, status: string) => void;

  // UI actions
  selectWorker: (workerId: string | null) => void;
  setWorkerDetail: (detail: WorkerDetail | null) => void;
  openDrawer: () => void;
  closeDrawer: () => void;

  // Utility actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}
```

### Selectors

```typescript
// Available selectors
export const selectSwarmStatus = (state: SwarmState) => state.swarmStatus;
export const selectSelectedWorkerId = (state: SwarmState) => state.selectedWorkerId;
export const selectSelectedWorkerDetail = (state: SwarmState) => state.selectedWorkerDetail;
export const selectIsDrawerOpen = (state: SwarmState) => state.isDrawerOpen;
export const selectIsLoading = (state: SwarmState) => state.isLoading;
export const selectError = (state: SwarmState) => state.error;
export const selectWorkers = (state: SwarmState) => state.swarmStatus?.workers ?? [];
export const selectSwarmProgress = (state: SwarmState) => state.swarmStatus?.overallProgress ?? 0;
export const selectRunningWorkers = (state: SwarmState) =>
  state.swarmStatus?.workers?.filter(w => w.status === 'running') ?? [];
export const selectCompletedWorkers = (state: SwarmState) =>
  state.swarmStatus?.workers?.filter(w => w.status === 'completed') ?? [];
export const selectSelectedWorker = (state: SwarmState) =>
  state.swarmStatus?.workers?.find(w => w.workerId === state.selectedWorkerId);
```

## Event Handling

### Event Name Mapping

```typescript
const EVENT_HANDLERS = {
  swarm_created: 'handleSwarmCreated',
  swarm_status_update: 'handleSwarmStatusUpdate',
  swarm_completed: 'handleSwarmCompleted',
  worker_started: 'handleWorkerStarted',
  worker_progress: 'handleWorkerProgress',
  worker_thinking: 'handleWorkerThinking',
  worker_tool_call: 'handleWorkerToolCall',
  worker_message: 'handleWorkerMessage',
  worker_completed: 'handleWorkerCompleted',
};
```

### Field Mapping (snake_case → camelCase)

```typescript
function convertPayload(payload: Record<string, unknown>) {
  return {
    swarmId: payload.swarm_id,
    sessionId: payload.session_id,
    workerId: payload.worker_id,
    workerName: payload.worker_name,
    workerType: payload.worker_type,
    toolCallId: payload.tool_call_id,
    toolName: payload.tool_name,
    inputArgs: payload.input_args,
    outputResult: payload.output_result,
    thinkingContent: payload.thinking_content,
    tokenCount: payload.token_count,
    currentAction: payload.current_action,
    durationMs: payload.duration_ms,
    // ... etc
  };
}
```

## Extension Guide

### Adding a New Worker Type

1. **Backend**: Add to `WorkerType` enum

```python
# backend/src/integrations/swarm/models.py
class WorkerType(str, Enum):
    # ... existing types
    MY_NEW_TYPE = "my_new_type"
```

2. **Frontend**: Add type definition and icon

```typescript
// frontend/src/components/unified-chat/agent-swarm/types/index.ts
export type WorkerType =
  | 'research'
  | 'writer'
  // ... existing types
  | 'my_new_type';

// frontend/src/components/unified-chat/agent-swarm/WorkerCard.tsx
const workerIcons: Record<WorkerType, ReactNode> = {
  // ... existing icons
  my_new_type: <MyNewIcon className="h-4 w-4" />,
};
```

### Adding a New Event Type

1. **Backend**: Define payload and emit method

```python
# backend/src/integrations/swarm/events/types.py
@dataclass
class MyNewEventPayload:
    swarm_id: str
    my_field: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# backend/src/integrations/swarm/events/emitter.py
async def emit_my_new_event(self, swarm_id: str, data: str) -> None:
    payload = MyNewEventPayload(
        swarm_id=swarm_id,
        my_field=data,
        timestamp=datetime.utcnow().isoformat(),
    )
    event = CustomEvent(event_name="my_new_event", payload=payload.to_dict())
    await self._emit(event, priority=True)
```

2. **Frontend**: Handle the event

```typescript
// frontend/src/components/unified-chat/agent-swarm/hooks/useSwarmEventHandler.ts
case 'my_new_event':
  const { myField } = payload;
  // Update store or trigger action
  break;
```

### Adding Custom Visualization

1. Create new component

```typescript
// frontend/src/components/unified-chat/agent-swarm/MyCustomPanel.tsx
import { useSwarmStore } from '@/stores/swarmStore';

export function MyCustomPanel() {
  const swarmStatus = useSwarmStore(selectSwarmStatus);

  return (
    <div data-testid="my-custom-panel">
      {/* Custom visualization */}
    </div>
  );
}
```

2. Add to parent component

```typescript
// frontend/src/components/unified-chat/OrchestrationPanel.tsx
import { MyCustomPanel } from './agent-swarm/MyCustomPanel';

// In render
{showMyCustomPanel && <MyCustomPanel />}
```

## Testing

### Backend Unit Tests

```python
# backend/tests/unit/swarm/test_my_feature.py
import pytest
from src.integrations.swarm import SwarmTracker, SwarmMode

def test_my_feature(tracker):
    swarm = tracker.create_swarm("test", SwarmMode.SEQUENTIAL)
    # Test assertions
    assert swarm is not None
```

### Frontend Unit Tests

```typescript
// frontend/src/components/unified-chat/agent-swarm/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByTestId('my-component')).toBeInTheDocument();
  });
});
```

### E2E Tests

```typescript
// frontend/tests/e2e/swarm.spec.ts
test('my feature works', async ({ page }) => {
  await page.goto('/');
  // Test steps
  await expect(page.locator('[data-testid="my-feature"]')).toBeVisible();
});
```

## Performance Considerations

1. **Use selectors** - Access only needed state slices
2. **Memoize components** - Use React.memo for worker cards
3. **Throttle updates** - Backend throttles rapid events
4. **Lazy load** - Worker details load on demand
5. **Virtual lists** - Use virtualization for long lists

## Troubleshooting

### Common Issues

1. **Events not arriving**
   - Check SSE connection status
   - Verify session ID matches
   - Check browser console for errors

2. **State not updating**
   - Verify store actions are called
   - Check devtools for store updates
   - Ensure selectors return new references

3. **Performance issues**
   - Reduce render frequency with selectors
   - Check for unnecessary re-renders
   - Profile with React DevTools

---

**Last Updated**: 2026-01-29
**Version**: 1.0.0
**Sprint**: 106 (Phase 29)
