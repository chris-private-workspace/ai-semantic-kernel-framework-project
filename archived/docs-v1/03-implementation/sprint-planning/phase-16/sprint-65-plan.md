# Sprint 65: Metrics, Checkpoints & Polish

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 65 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Duration** | 2-3 days |
| **Total Points** | 24 |
| **Focus** | Execution metrics, checkpoint integration, and UI polish |

## Sprint Goals

1. Implement comprehensive execution metrics tracking
2. Integrate checkpoint save/restore functionality
3. Add robust error handling and recovery
4. Polish UI with animations and accessibility improvements
5. **🆕 Integrate CustomUIRenderer** for dynamic UI components from AG-UI

## Prerequisites

- Sprint 62-64 completed
- Checkpoint API endpoints operational
- Metrics available from AG-UI events

---

## Stories

### S65-1: useExecutionMetrics Hook (6 pts)

**Description**: Create a hook for tracking and displaying execution metrics including token usage, time, and tool call statistics.

**Acceptance Criteria**:
- [ ] Create `useExecutionMetrics` hook
- [ ] Track token usage (used, limit, percentage)
- [ ] Track execution time (total, running status)
- [ ] Count tool calls and their statuses
- [ ] Count total messages
- [ ] Update metrics from AG-UI events
- [ ] Provide formatted display values

**Technical Details**:
```typescript
interface UseExecutionMetricsReturn {
  // Token metrics
  tokens: {
    used: number;
    limit: number;
    percentage: number;
    formatted: string; // "1.2K/4K"
  };

  // Time metrics
  time: {
    total: number; // milliseconds
    isRunning: boolean;
    formatted: string; // "3.5s"
  };

  // Tool metrics
  tools: {
    total: number;
    completed: number;
    failed: number;
    pending: number;
  };

  // Message metrics
  messages: {
    total: number;
    user: number;
    assistant: number;
  };

  // Actions
  resetMetrics: () => void;
  startTimer: () => void;
  stopTimer: () => void;
}
```

**Files to Create**:
- `frontend/src/hooks/useExecutionMetrics.ts`

**Files to Modify**:
- `frontend/src/components/unified-chat/StatusBar.tsx` - Integrate metrics display

---

### S65-2: Checkpoint Integration (6 pts)

**Description**: Integrate checkpoint save and restore functionality with the backend API.

**Acceptance Criteria**:
- [ ] Create `useCheckpoints` hook
- [ ] Load checkpoints from AG-UI STATE events
- [ ] Implement restore checkpoint API call
- [ ] Show restore confirmation dialog
- [ ] Handle restore success/failure
- [ ] Update UI after restore
- [ ] Disable restore during active execution

**Technical Details**:
```typescript
interface UseCheckpointsReturn {
  checkpoints: Checkpoint[];
  currentCheckpoint: string | null;
  isRestoring: boolean;
  canRestore: boolean;

  restoreCheckpoint: (checkpointId: string) => Promise<void>;
  loadCheckpoints: () => Promise<void>;
}

interface Checkpoint {
  id: string;
  timestamp: string;
  label?: string;
  stepIndex?: number;
  canRestore: boolean;
}
```

**Files to Create**:
- `frontend/src/hooks/useCheckpoints.ts`

**Files to Modify**:
- `frontend/src/components/unified-chat/CheckpointList.tsx` - API integration
- `frontend/src/api/endpoints/ag-ui.ts` - Checkpoint endpoints

**API Endpoints**:
```typescript
// Restore checkpoint
POST /api/v1/ag-ui/checkpoints/:checkpointId/restore
Response: { success: true, restoredState: {...} }
```

---

### S65-3: Error Handling & Recovery (4 pts)

**Description**: Implement comprehensive error handling, reconnection logic, and user feedback systems.

**Acceptance Criteria**:
- [ ] SSE reconnection with exponential backoff
- [ ] Network error detection and display
- [ ] API error handling with user feedback
- [ ] Graceful degradation for missing features
- [ ] Error boundary for component crashes
- [ ] Manual reconnect button

**Technical Details**:
```typescript
// Reconnection logic
const reconnectSSE = () => {
  const backoffMs = Math.min(1000 * Math.pow(2, retryCount), 30000);
  setTimeout(() => {
    retryCount++;
    connectSSE();
  }, backoffMs);
};

// Error types
type UnifiedChatError =
  | { type: 'CONNECTION_ERROR'; message: string }
  | { type: 'API_ERROR'; message: string; status: number }
  | { type: 'PARSE_ERROR'; message: string }
  | { type: 'TIMEOUT_ERROR'; message: string };
```

**Files to Create**:
- `frontend/src/components/unified-chat/ErrorBoundary.tsx`
- `frontend/src/components/unified-chat/ConnectionStatus.tsx`

**Files to Modify**:
- `frontend/src/hooks/useUnifiedChat.ts` - Add reconnection logic
- `frontend/src/components/unified-chat/ChatHeader.tsx` - Connection indicator

---

### S65-4: UI Polish & Accessibility (4 pts)

**Description**: Add finishing touches including animations, keyboard support, and accessibility improvements.

**Acceptance Criteria**:
- [ ] Smooth mode transition animations
- [ ] Message appear animations
- [ ] Loading skeleton states
- [ ] Keyboard shortcuts (Cmd/Ctrl+Enter to send)
- [ ] Focus management in dialog
- [ ] Screen reader announcements
- [ ] Reduced motion support

**Technical Details**:
```typescript
// Animation variants
const messageVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

// Keyboard shortcuts
useHotkeys('mod+enter', () => {
  if (inputValue.trim()) {
    sendMessage(inputValue);
  }
});

// Reduced motion
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;
```

**Files to Modify**:
- `frontend/src/components/unified-chat/MessageList.tsx` - Animations
- `frontend/src/components/unified-chat/ChatInput.tsx` - Keyboard shortcuts
- `frontend/src/components/unified-chat/WorkflowSidePanel.tsx` - Transition
- Various components - Accessibility improvements

**Accessibility Checklist**:
- ARIA labels on interactive elements
- Focus visible on all focusable elements
- Color contrast meets WCAG AA
- Screen reader announcements for state changes
- Keyboard navigation for all features

---

### S65-5: CustomUIRenderer Integration (4 pts) 🆕

**Description**: Integrate Phase 15's CustomUIRenderer component to support dynamic Tool-based Generative UI (AG-UI Feature 5) in the unified chat interface.

**Acceptance Criteria**:
- [ ] Import and integrate `CustomUIRenderer` from AG-UI components
- [ ] Handle `CUSTOM` events with UI component payloads
- [ ] Support rendering DynamicForm, DynamicChart, DynamicTable
- [ ] Pass form submissions back to backend via AG-UI protocol
- [ ] Handle loading and error states for dynamic UI

**Technical Details**:
```typescript
// Message with custom UI component
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  customUI?: CustomUIComponent;  // 🆕 Dynamic UI from AG-UI
  toolCall?: ToolCallInfo;
}

// CustomUI types from Phase 15
type CustomUIComponent =
  | { type: 'form'; schema: FormSchema; onSubmit: string }
  | { type: 'chart'; data: ChartData; config: ChartConfig }
  | { type: 'table'; columns: Column[]; data: Row[] }
  | { type: 'card'; title: string; content: string; actions?: Action[] };

// Render message content with dynamic UI support
const renderMessageContent = (message: ChatMessage) => {
  // Check for custom UI component
  if (message.customUI) {
    return (
      <CustomUIRenderer
        component={message.customUI}
        onFormSubmit={(data) => handleFormSubmit(message.id, data)}
        onAction={(action) => handleUIAction(message.id, action)}
      />
    );
  }

  // Standard message bubble
  return <MessageBubble message={message} />;
};

// Handle CUSTOM event with UI payload
const handleCustomEvent = (event: CustomAGUIEvent) => {
  if (event.payload.type === 'RENDER_UI') {
    const { messageId, component } = event.payload;
    updateMessage(messageId, { customUI: component });
  }
};
```

**Files to Modify**:
- `frontend/src/components/unified-chat/MessageList.tsx` - Integrate CustomUIRenderer
- `frontend/src/hooks/useUnifiedChat.ts` - Handle CUSTOM events with UI payloads

**Component Integration**:
```typescript
// Import from Phase 15 AG-UI components
import { CustomUIRenderer } from '@/components/ag-ui/advanced/CustomUIRenderer';
import { DynamicForm } from '@/components/ag-ui/advanced/DynamicForm';
import { DynamicChart } from '@/components/ag-ui/advanced/DynamicChart';
import { DynamicTable } from '@/components/ag-ui/advanced/DynamicTable';
```

---

## Technical Notes

### Token Tracking from AG-UI Events

```typescript
// Listen for token updates in CUSTOM events
const handleCustomEvent = (event: CustomAGUIEvent) => {
  if (event.payload.type === 'TOKEN_UPDATE') {
    updateTokens({
      used: event.payload.tokensUsed,
      limit: event.payload.tokensLimit,
    });
  }
};
```

### Execution Timer

```typescript
// Timer with cleanup
const useExecutionTimer = () => {
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;

    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 100);

    return () => clearInterval(interval);
  }, [startTime]);

  return {
    elapsed,
    isRunning: startTime !== null,
    start: () => setStartTime(Date.now()),
    stop: () => setStartTime(null),
    reset: () => { setStartTime(null); setElapsed(0); },
  };
};
```

### Checkpoint Restore Flow

```
1. User clicks "Restore" on checkpoint
2. Show confirmation dialog
3. Call restore API
4. Backend restores state
5. AG-UI sends STATE_SNAPSHOT event
6. Frontend updates all state
7. Clear messages after checkpoint
8. Show success notification
```

### Animation Configuration

```typescript
// Framer Motion configuration
const motionConfig = {
  transition: { duration: prefersReducedMotion ? 0 : 0.3 },
  initial: prefersReducedMotion ? {} : { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: prefersReducedMotion ? {} : { opacity: 0, y: -20 },
};
```

---

## Dependencies

### From Previous Sprints
- Sprint 62-64: All components and hooks

### External
- Checkpoint API endpoints
- Token usage from AG-UI events
- Framer Motion (optional, for animations)

---

## Definition of Done

- [ ] All 5 stories completed and tested
- [ ] Metrics display correctly in StatusBar
- [ ] Checkpoint restore works end-to-end
- [ ] Reconnection handles network issues
- [ ] Animations smooth and optional
- [ ] Keyboard navigation complete
- [ ] Accessibility audit passed
- [ ] **🆕 CustomUIRenderer** displays forms, charts, tables correctly

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Animation performance | Low | Use CSS transitions, lazy load Framer Motion |
| Checkpoint restore issues | Medium | Clear confirmation, rollback capability |
| Accessibility gaps | Medium | Use automated testing tools |

---

## Phase 16 Completion Criteria

After Sprint 65, Phase 16 should achieve:

1. **Functional**
   - [ ] Chat and Workflow modes seamless
   - [ ] Real-time streaming responses
   - [ ] HITL approval workflow complete
   - [ ] Checkpoint save/restore working

2. **Performance**
   - [ ] First message response < 500ms
   - [ ] Mode switch < 200ms
   - [ ] Smooth 60fps animations

3. **Quality**
   - [ ] WCAG AA accessibility
   - [ ] No critical bugs
   - [ ] TypeScript strict compliance
   - [ ] Comprehensive error handling

---

## Sprint Velocity Reference

Final sprint with polish work and CustomUIRenderer integration.
Expected completion: 2-3 days for 24 pts (enhanced with Tool-based Generative UI integration)
