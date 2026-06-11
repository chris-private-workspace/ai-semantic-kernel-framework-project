# Sprint 63: Mode Switching & State Management

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 63 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Duration** | 3-4 days |
| **Total Points** | 30 |
| **Focus** | AG-UI SSE integration and real-time state management |

## Sprint Goals

1. Integrate AG-UI SSE event stream with the unified chat interface
2. Implement real-time mode detection from backend IntentRouter
3. Build comprehensive message handling with streaming support
4. Enable state persistence across sessions

## Prerequisites

- Sprint 62 completed (Core Architecture & Adaptive Layout)
- AG-UI SSE endpoint operational (`/api/v1/ag-ui`)
- Hybrid orchestrator API endpoints ready

---

## Stories

### S63-1: useUnifiedChat Hook (8 pts)

**Description**: Create the main orchestration hook that manages AG-UI connection, message handling, and state coordination.

**Acceptance Criteria**:
- [ ] Create `useUnifiedChat` hook as main entry point
- [ ] Manage SSE connection lifecycle (connect, disconnect, reconnect)
- [ ] Handle all AG-UI event types
- [ ] Provide message send functionality
- [ ] Coordinate with `useHybridMode` for mode updates
- [ ] Support streaming message updates

**Technical Details**:
```typescript
interface UseUnifiedChatReturn {
  // State
  messages: ChatMessage[];
  isConnected: boolean;
  isStreaming: boolean;
  error: Error | null;

  // Actions
  sendMessage: (content: string, attachments?: File[]) => Promise<void>;
  cancelStream: () => void;
  clearMessages: () => void;
  reconnect: () => void;

  // Mode integration
  currentMode: ExecutionMode;
  workflowState: WorkflowState | null;

  // Approvals
  pendingApprovals: PendingApproval[];
}
```

**Files to Create**:
- `frontend/src/hooks/useUnifiedChat.ts`

**Dependencies**:
- AG-UI SSE endpoint
- Zustand store from Sprint 62

---

### S63-2: AG-UI Event Integration (11 pts) ⬆️ Enhanced

**Description**: Implement comprehensive AG-UI event handling for all 15 event types with full Shared State and Predictive State Updates support.

**Acceptance Criteria**:
- [ ] Handle lifecycle events (RUN_STARTED, RUN_FINISHED, RUN_ERROR)
- [ ] Process message events (TEXT_MESSAGE_START, CONTENT, END)
- [ ] Process tool events (TOOL_CALL_START, ARGS, END)
- [ ] Handle state events (STATE_SNAPSHOT, STATE_DELTA, CUSTOM)
- [ ] Update Zustand store based on events
- [ ] Support optimistic updates with version control
- [ ] **🆕 STATE_SNAPSHOT**: Complete state replacement from backend
- [ ] **🆕 STATE_DELTA**: Incremental state merge with conflict detection
- [ ] **🆕 useSharedState**: Hook for bidirectional state synchronization
- [ ] **🆕 Optimistic Concurrency**: Version-based conflict resolution

**Technical Details**:
```typescript
// Event handler mapping
const eventHandlers: Record<AGUIEventType, EventHandler> = {
  RUN_STARTED: handleRunStarted,
  RUN_FINISHED: handleRunFinished,
  RUN_ERROR: handleRunError,
  TEXT_MESSAGE_START: handleMessageStart,
  TEXT_MESSAGE_CONTENT: handleMessageContent,
  TEXT_MESSAGE_END: handleMessageEnd,
  TOOL_CALL_START: handleToolCallStart,
  TOOL_CALL_ARGS: handleToolCallArgs,
  TOOL_CALL_END: handleToolCallEnd,
  STATE_SNAPSHOT: handleStateSnapshot,
  STATE_DELTA: handleStateDelta,
  CUSTOM: handleCustomEvent,
  // ... more
};
```

**Files to Modify**:
- `frontend/src/hooks/useUnifiedChat.ts` - Add event handlers
- `frontend/src/stores/unifiedChatStore.ts` - Add event-driven updates

**Event Types Reference**:
- Lifecycle: `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR`
- Messages: `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`
- Tools: `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`
- State: `STATE_SNAPSHOT`, `STATE_DELTA`, `CUSTOM`

**🆕 Shared State Implementation**:
```typescript
// STATE_SNAPSHOT - Complete state replacement
const handleStateSnapshot = (event: StateSnapshotEvent) => {
  const { state, version } = event;
  setSharedState(state);
  setStateVersion(version);
  console.log(`[Shared State] Snapshot applied, version: ${version}`);
};

// STATE_DELTA - Incremental state merge with conflict detection
const handleStateDelta = (event: StateDeltaEvent) => {
  const { delta, version, baseVersion } = event;

  // Conflict detection
  if (baseVersion !== currentVersion) {
    console.warn(`[Shared State] Version conflict: expected ${baseVersion}, got ${currentVersion}`);
    // Request full snapshot on conflict
    requestStateSnapshot();
    return;
  }

  setSharedState(prev => ({ ...prev, ...delta }));
  setStateVersion(version);
};

// useSharedState hook for bidirectional sync
interface UseSharedStateReturn<T> {
  state: T;
  version: number;
  updateState: (partial: Partial<T>) => Promise<void>;
  isStale: boolean;
}
```

**🆕 Optimistic Concurrency Control**:
```typescript
// Optimistic update with version tracking
const optimisticUpdate = async <T>(
  key: string,
  update: Partial<T>,
  currentVersion: number
) => {
  const optimisticVersion = currentVersion + 1;

  // Apply optimistic update immediately
  setOptimisticState(prev => ({ ...prev, ...update }));
  setOptimisticVersion(optimisticVersion);

  try {
    // Send to backend
    const result = await api.updateState(key, update, currentVersion);
    // Backend confirms with new version
    setConfirmedVersion(result.version);
  } catch (error) {
    if (error.code === 'VERSION_CONFLICT') {
      // Rollback and request fresh state
      rollbackOptimisticUpdate();
      requestStateSnapshot();
    }
  }
};
```

---

### S63-3: Real Mode Detection (6 pts) ⬆️ Enhanced

**Description**: Integrate with backend IntentRouter to receive and apply mode detection results with full switch reason display.

**Acceptance Criteria**:
- [ ] Listen for `CUSTOM` events with mode detection payload
- [ ] Update `autoMode` in `useHybridMode` based on IntentRouter results
- [ ] Respect manual override preference
- [ ] Show mode change notification/indicator
- [ ] Log mode changes for debugging
- [ ] **🆕 Display switch reason**: Show why mode was automatically switched
- [ ] **🆕 Confidence indicator**: Display confidence level for mode detection

**Technical Details**:
```typescript
// Custom event payload for mode detection
interface ModeDetectionPayload {
  type: 'MODE_DETECTED';
  mode: 'chat' | 'workflow';
  confidence: number;
  reason?: string;
}

// 🆕 Enhanced ModeState with switch reason
interface ModeState {
  autoMode: ExecutionMode;
  manualOverride: ExecutionMode | null;
  switchReason: string | null;       // 🆕 Why mode was switched
  switchConfidence: number;          // 🆕 Detection confidence (0-1)
  lastSwitchAt: string | null;       // 🆕 Timestamp of last switch
}

// Update useHybridMode to accept external updates
const handleModeDetection = (event: CustomAGUIEvent) => {
  if (event.payload.type === 'MODE_DETECTED') {
    const { mode, confidence, reason } = event.payload;
    // Only update if confidence > threshold
    if (confidence >= 0.7) {
      setAutoMode(mode);
      setSwitchReason(reason || null);      // 🆕 Store reason
      setSwitchConfidence(confidence);       // 🆕 Store confidence
      setLastSwitchAt(new Date().toISOString());

      // 🆕 Show notification with reason
      if (reason) {
        showModeChangeNotification(mode, reason, confidence);
      }
    }
  }
};
```

**🆕 Mode Switch Notification UI**:
```typescript
// Display mode switch reason in UI
const ModeIndicator: FC<{ mode: ModeState }> = ({ mode }) => (
  <div className="flex items-center gap-2">
    <Badge variant={mode.autoMode === 'workflow' ? 'default' : 'secondary'}>
      {mode.autoMode}
    </Badge>
    {mode.switchReason && (
      <Tooltip>
        <TooltipTrigger>
          <Info className="h-4 w-4 text-muted-foreground" />
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <p className="font-medium">Auto-switched to {mode.autoMode}</p>
            <p className="text-sm text-muted-foreground">{mode.switchReason}</p>
            <p className="text-xs">Confidence: {(mode.switchConfidence * 100).toFixed(0)}%</p>
          </div>
        </TooltipContent>
      </Tooltip>
    )}
  </div>
);
```

**Files to Modify**:
- `frontend/src/hooks/useHybridMode.ts` - Add external update support
- `frontend/src/hooks/useUnifiedChat.ts` - Add mode detection handling

---

### S63-4: State Persistence (5 pts)

**Description**: Implement conversation and state persistence across browser sessions.

**Acceptance Criteria**:
- [ ] Persist messages to localStorage/sessionStorage
- [ ] Persist mode preference
- [ ] Restore state on page reload
- [ ] Handle storage quota limits
- [ ] Provide clear history functionality
- [ ] Support multiple threads (by threadId)

**Technical Details**:
```typescript
// Zustand persist middleware
const useUnifiedChatStore = create(
  persist(
    devtools((set, get) => ({
      // ... state
    })),
    {
      name: 'unified-chat-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        messages: state.messages.slice(-100), // Keep last 100 messages
        mode: state.mode,
        manualOverride: state.manualOverride,
      }),
    }
  )
);
```

**Files to Modify**:
- `frontend/src/stores/unifiedChatStore.ts` - Add persistence middleware

---

## Technical Notes

### SSE Connection Management

```typescript
// Connection with automatic reconnection
const connectSSE = (threadId: string) => {
  const eventSource = new EventSource(
    `/api/v1/ag-ui?thread_id=${threadId}`
  );

  eventSource.onopen = () => setIsConnected(true);
  eventSource.onerror = (e) => {
    setIsConnected(false);
    // Exponential backoff reconnection
    scheduleReconnect();
  };
  eventSource.onmessage = (e) => {
    const event = JSON.parse(e.data);
    handleEvent(event);
  };

  return eventSource;
};
```

### Message Streaming

```typescript
// Streaming message accumulation
const handleMessageContent = (event: TextMessageContentEvent) => {
  updateMessage(event.messageId, (msg) => ({
    ...msg,
    content: msg.content + event.delta,
  }));
};
```

### State Update Pattern

```typescript
// Optimistic update with rollback
const sendMessage = async (content: string) => {
  const optimisticId = generateId();

  // Optimistic update
  addMessage({
    id: optimisticId,
    role: 'user',
    content,
    status: 'sending',
  });

  try {
    const response = await api.sendMessage(content);
    updateMessage(optimisticId, { status: 'sent', id: response.id });
  } catch (error) {
    updateMessage(optimisticId, { status: 'error' });
  }
};
```

---

## Dependencies

### From Previous Sprints
- Sprint 62: UnifiedChat page, useHybridMode hook, Zustand store

### External
- AG-UI SSE endpoint (`POST /api/v1/ag-ui`)
- IntentRouter for mode detection
- Thread/Session management API

---

## Definition of Done

- [ ] All 4 stories completed and tested
- [ ] SSE connection works reliably
- [ ] Messages stream in real-time
- [ ] Mode detection updates layout automatically
- [ ] State persists across page reloads
- [ ] No memory leaks from SSE connections
- [ ] Error states handled gracefully

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSE connection instability | Medium | Implement robust reconnection logic |
| State sync issues | Medium | Use optimistic updates with rollback |
| Storage quota exceeded | Low | Limit persisted messages, handle gracefully |

---

## Sprint Velocity Reference

Based on Sprint 62: 30 pts completed in ~3 days
Expected completion: 3-4 days for 30 pts (enhanced with AG-UI Shared State integration)
