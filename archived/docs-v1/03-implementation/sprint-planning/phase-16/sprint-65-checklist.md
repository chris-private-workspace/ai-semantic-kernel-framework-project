# Sprint 65 Checklist: Metrics, Checkpoints & Polish

## Pre-Sprint Verification

- [ ] Sprint 62-64 components completed
- [ ] Checkpoint API endpoints operational
- [ ] Token usage events available
- [ ] All previous functionality working

---

## S65-1: useExecutionMetrics Hook (6 pts)

### Files Created
- [ ] `frontend/src/hooks/useExecutionMetrics.ts`

### Files Modified
- [ ] `frontend/src/components/unified-chat/StatusBar.tsx`

### Implementation Checklist
- [ ] Hook tracks token usage (used, limit, percentage)
- [ ] Hook tracks execution time with timer
- [ ] Hook tracks tool call counts by status
- [ ] Hook tracks message counts by role
- [ ] Formatted display values provided
- [ ] Metrics update from AG-UI events
- [ ] `resetMetrics()` function implemented
- [ ] Timer start/stop functions implemented

### Hook API Verification
```typescript
const {
  tokens,         // { used, limit, percentage, formatted }
  time,           // { total, isRunning, formatted }
  tools,          // { total, completed, failed, pending }
  messages,       // { total, user, assistant }
  resetMetrics,   // () => void
  startTimer,     // () => void
  stopTimer,      // () => void
} = useExecutionMetrics();
```

### Verification Steps
- [ ] Token count updates on new messages
- [ ] Timer starts on run begin
- [ ] Timer stops on run end
- [ ] Tool counts accurate
- [ ] Formatted values display correctly
- [ ] Reset clears all metrics

---

## S65-2: Checkpoint Integration (6 pts)

### Files Created
- [ ] `frontend/src/hooks/useCheckpoints.ts`

### Files Modified
- [ ] `frontend/src/components/unified-chat/CheckpointList.tsx`
- [ ] `frontend/src/api/endpoints/ag-ui.ts`

### Implementation Checklist
- [ ] Hook loads checkpoints from AG-UI events
- [ ] Hook tracks current checkpoint
- [ ] `restoreCheckpoint(id)` calls API
- [ ] Confirmation dialog before restore
- [ ] Success notification after restore
- [ ] Error handling for failed restore
- [ ] Restore disabled during active execution
- [ ] UI updates after restore

### Hook API Verification
```typescript
const {
  checkpoints,         // Checkpoint[]
  currentCheckpoint,   // string | null
  isRestoring,         // boolean
  canRestore,          // boolean
  restoreCheckpoint,   // (id: string) => Promise<void>
  loadCheckpoints,     // () => Promise<void>
} = useCheckpoints();
```

### Verification Steps
- [ ] Checkpoints load from backend
- [ ] Current checkpoint highlighted
- [ ] Restore button shows loading state
- [ ] Confirmation dialog appears
- [ ] Restore API call succeeds
- [ ] State resets to checkpoint
- [ ] Messages cleared after checkpoint
- [ ] Error shows if restore fails

---

## S65-3: Error Handling & Recovery (4 pts)

### Files Created
- [ ] `frontend/src/components/unified-chat/ErrorBoundary.tsx`
- [ ] `frontend/src/components/unified-chat/ConnectionStatus.tsx`

### Files Modified
- [ ] `frontend/src/hooks/useUnifiedChat.ts`
- [ ] `frontend/src/components/unified-chat/ChatHeader.tsx`

### Implementation Checklist
- [ ] SSE reconnection with exponential backoff
- [ ] Max retry limit (e.g., 5 attempts)
- [ ] Manual reconnect button
- [ ] Network error detection
- [ ] API error handling
- [ ] Error boundary catches crashes
- [ ] User-friendly error messages
- [ ] Graceful degradation

### Error Types Handled
- [ ] CONNECTION_ERROR - SSE connection failed
- [ ] API_ERROR - Backend API error
- [ ] PARSE_ERROR - Invalid JSON response
- [ ] TIMEOUT_ERROR - Request timeout
- [ ] UNKNOWN_ERROR - Catch-all

### Verification Steps
- [ ] Disconnect network → reconnection attempts
- [ ] After max retries → manual reconnect option
- [ ] API 500 error → error message displayed
- [ ] Component crash → error boundary catches
- [ ] Recovery works after fixing issues

---

## S65-4: UI Polish & Accessibility (4 pts)

### Files Modified
- [ ] `frontend/src/components/unified-chat/MessageList.tsx`
- [ ] `frontend/src/components/unified-chat/ChatInput.tsx`
- [ ] `frontend/src/components/unified-chat/WorkflowSidePanel.tsx`
- [ ] Various unified-chat components

### Animation Checklist
- [ ] Message appear animation (fade + slide)
- [ ] Mode transition animation (smooth resize)
- [ ] Side panel slide in/out
- [ ] Loading skeleton states
- [ ] Reduced motion support (@media query)

### Keyboard Shortcuts
- [ ] Cmd/Ctrl + Enter - Send message
- [ ] Escape - Close dialog/cancel
- [ ] Tab - Navigate focusable elements
- [ ] Arrow keys - Navigate messages (optional)

### Accessibility Checklist
- [ ] All buttons have accessible names
- [ ] Dialog focus trapping works
- [ ] Screen reader announces new messages
- [ ] Color contrast meets WCAG AA
- [ ] Focus visible on all elements
- [ ] Role and aria attributes correct
- [ ] Skip links (if applicable)

### Verification Steps
- [ ] Animations play smoothly (60fps)
- [ ] Animations respect prefers-reduced-motion
- [ ] Keyboard-only navigation works
- [ ] Screen reader can use interface
- [ ] Lighthouse accessibility score > 90

---

## S65-5: CustomUIRenderer Integration (4 pts) 🆕

### Files Modified
- [ ] `frontend/src/components/unified-chat/MessageList.tsx` - Integrate renderer
- [ ] `frontend/src/hooks/useUnifiedChat.ts` - Handle UI events

### Implementation Checklist
- [ ] Import `CustomUIRenderer` from AG-UI components
- [ ] Add `customUI` field to ChatMessage type
- [ ] Handle `CUSTOM` events with `RENDER_UI` payload
- [ ] Conditionally render CustomUIRenderer or MessageBubble
- [ ] Implement `handleFormSubmit()` callback
- [ ] Implement `handleUIAction()` callback
- [ ] Loading state for dynamic UI
- [ ] Error handling for failed UI render

### Supported UI Components
- [ ] DynamicForm - Form rendering and submission
- [ ] DynamicChart - Data visualization (line, bar, pie)
- [ ] DynamicTable - Tabular data display
- [ ] Card - Simple content card with actions

### Verification Steps
```typescript
// Test CUSTOM event with UI payload
const uiEvent = {
  type: 'CUSTOM',
  payload: {
    type: 'RENDER_UI',
    messageId: 'msg-1',
    component: {
      type: 'form',
      schema: { /* form schema */ },
      onSubmit: 'submit_action_id',
    },
  },
};
```
- [ ] Form renders correctly within message
- [ ] Form submission triggers callback
- [ ] Chart renders with provided data
- [ ] Table displays columns and rows
- [ ] Error boundary catches render failures
- [ ] Loading spinner shows during component load

---

## S65-BF-1: CustomEvent Field Name Fix (Bug Fix)

### Files Modified
- [x] `backend/src/integrations/ag_ui/converters.py`

### Implementation Checklist
- [x] Line 432: 修正 `name`/`value` → `event_name`/`payload`
- [x] Lines 601-609: 修正 `custom_event_type`/`data` → `event_name`/`payload`

### Verification Steps
- [ ] Backend 啟動無 Pydantic 驗證錯誤
- [ ] Workflow Mode 工具調用正常
- [ ] HITL approval 事件正確發送

---

## Integration Tests

### Metrics Display
- [ ] Token counter shows in StatusBar
- [ ] Time counter updates during execution
- [ ] Tool counts accurate
- [ ] All metrics reset on clear

### Checkpoint Flow
- [ ] Checkpoints appear in side panel
- [ ] Restore confirmation shows
- [ ] Restore succeeds and updates UI
- [ ] Cannot restore during execution

### Error Recovery
- [ ] Network loss triggers reconnection
- [ ] Reconnection succeeds when network returns
- [ ] Manual reconnect button works
- [ ] Errors don't crash the app

### Polish
- [ ] Animations feel smooth
- [ ] No janky transitions
- [ ] Keyboard shortcuts work
- [ ] Accessible to screen readers

---

## Code Quality

### TypeScript
- [ ] All new types properly defined
- [ ] No `any` types
- [ ] Strict mode compliance
- [ ] Proper error types

### Performance
- [ ] Animations use CSS where possible
- [ ] No layout thrashing
- [ ] Memoization where needed
- [ ] Lazy loading for heavy components

### Testing
- [ ] Unit tests for hooks
- [ ] Integration tests for flows
- [ ] Accessibility tests

---

## Phase 16 Final Checklist

### Functional Requirements
- [ ] Chat mode works correctly
- [ ] Workflow mode works correctly
- [ ] Mode switching seamless
- [ ] Streaming responses work
- [ ] Tool calls display correctly
- [ ] Approvals (inline and dialog) work
- [ ] Checkpoints save and restore
- [ ] Metrics display accurately

### Non-Functional Requirements
- [ ] Performance meets targets
- [ ] Accessibility WCAG AA compliant
- [ ] Error handling comprehensive
- [ ] TypeScript strict compliance
- [ ] No critical bugs

---

## Definition of Done

- [ ] All 5 stories completed
- [ ] Manual testing passed
- [ ] TypeScript compilation succeeds
- [ ] ESLint passes
- [ ] Accessibility audit passed
- [ ] Performance targets met

---

## Sprint Completion Sign-off

| Item | Status | Date | Notes |
|------|--------|------|-------|
| S65-1 Complete | ⬜ | | |
| S65-2 Complete | ⬜ | | |
| S65-3 Complete | ⬜ | | |
| S65-4 Complete | ⬜ | | |
| S65-5 Complete | ⬜ | | 🆕 CustomUIRenderer |
| S65-BF-1 Complete | ⬜ | | CustomEvent Fix |
| Integration Tested | ⬜ | | |
| Sprint Complete | ⬜ | | |

**Total Points**: 24 pts (Enhanced with Tool-based Generative UI integration)
**Completion Date**: TBD

---

## Phase 16 Completion Sign-off

| Sprint | Points | Status | Date |
|--------|--------|--------|------|
| Sprint 62 | 30 pts | ✅ Complete | 2026-01-07 |
| Sprint 63 | 30 pts | ⬜ | |
| Sprint 64 | 29 pts | ⬜ | |
| Sprint 65 | 24 pts | ⬜ | |
| **Phase 16 Total** | **113 pts** | ⬜ | |

**Phase 16 Complete**: ⬜
**Phase Completion Date**: TBD

---

**Enhancement Summary (AG-UI Integration)**:
- Sprint 63: +5 pts (STATE_SNAPSHOT/DELTA, Optimistic Updates, Mode Switch Reason)
- Sprint 64: +4 pts (RiskIndicator Tooltip, Mode Switch Confirm Dialog)
- Sprint 65: +4 pts (CustomUIRenderer Integration)
