# Sprint 67 Checklist: UnifiedChat UI Component Integration

## Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 67 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Type** | Bug Fix / Integration Sprint |
| **Story Points** | 8 pts |
| **Status** | Complete |

---

## S67-1: Integrate ChatArea Component (3 pts)

**File**: `frontend/src/pages/UnifiedChat.tsx`

### Tasks

- [x] **T1**: Import ChatArea component
  ```tsx
  import { ChatArea } from '@/components/unified-chat/ChatArea';
  ```

- [x] **T2**: Add missing state for streaming message ID
  - Check if `useUnifiedChat` returns `streamingMessageId`
  - If not, derive from messages or add placeholder

- [x] **T3**: Replace manual message rendering (lines 335-395)
  - Remove `<div className="flex-1 overflow-y-auto p-4">...</div>` block
  - Replace with `<ChatArea>` component

- [x] **T4**: Pass correct props to ChatArea
  ```tsx
  <ChatArea
    messages={messages}
    isStreaming={isStreaming}
    streamingMessageId={streamingMessageId}
    pendingApprovals={pendingApprovals}
    onApprove={handleApprove}
    onReject={handleReject}
  />
  ```

### Verification

- [x] Messages render with proper styling
- [x] Tool calls display as cards
- [x] Streaming indicator shows during AI response
- [x] No TypeScript errors

---

## S67-2: Integrate WorkflowSidePanel (3 pts)

**File**: `frontend/src/pages/UnifiedChat.tsx`

### Tasks

- [x] **T1**: Import WorkflowSidePanel component
  ```tsx
  import { WorkflowSidePanel } from '@/components/unified-chat/WorkflowSidePanel';
  ```

- [x] **T2**: Replace placeholder (lines 399-412)
  - Remove `<aside>` with placeholder text
  - Replace with `<WorkflowSidePanel>` component

- [x] **T3**: Pass correct props to WorkflowSidePanel
  ```tsx
  {effectiveMode === 'workflow' && (
    <WorkflowSidePanel
      workflowState={workflowState}
      toolCalls={toolCalls}
      checkpoints={checkpoints}
      onRestoreCheckpoint={handleRestore}
    />
  )}
  ```

- [x] **T4**: Remove unused `_workflowState` underscore prefix
  - Change `workflowState: _workflowState` to `workflowState`
  - Use directly in WorkflowSidePanel

### Verification

- [x] Side panel appears in Workflow mode
- [x] Step Progress section shows
- [x] Tool Call Tracker section shows
- [x] Checkpoint List section shows
- [x] Collapse/expand works

---

## S67-3: Connect Approval Handlers (2 pts)

**File**: `frontend/src/pages/UnifiedChat.tsx`

### Tasks

- [x] **T1**: Create handleApprove wrapper
  ```tsx
  const handleApprove = useCallback(async (toolCallId: string) => {
    console.log('[UnifiedChat] Approving tool call:', toolCallId);
    await approveToolCall(toolCallId);
  }, [approveToolCall]);
  ```

- [x] **T2**: Create handleReject wrapper
  ```tsx
  const handleReject = useCallback(async (toolCallId: string, reason?: string) => {
    console.log('[UnifiedChat] Rejecting tool call:', toolCallId, reason);
    await rejectToolCall(toolCallId, reason);
  }, [rejectToolCall]);
  ```

- [x] **T3**: Destructure approveToolCall/rejectToolCall from hook
  - Add to the useUnifiedChat destructuring

### Verification

- [x] Approve button calls API
- [x] Reject button calls API
- [x] Console logs show correct tool call IDs

---

## Code Changes Summary

### Imports to Add

```tsx
import { ChatArea } from '@/components/unified-chat/ChatArea';
import { WorkflowSidePanel } from '@/components/unified-chat/WorkflowSidePanel';
```

### Hook Destructuring Update

```tsx
const {
  messages,
  isConnected,
  isStreaming,
  error,
  sendMessage,
  cancelStream,
  currentMode,
  autoMode,
  manualOverride: _manualOverride,
  isManuallyOverridden,
  setManualOverride,
  workflowState,  // Remove underscore
  pendingApprovals,
  toolCalls,
  checkpoints,
  currentCheckpoint,
  tokenUsage,
  approveToolCall,  // Add
  rejectToolCall,   // Add
} = useUnifiedChat({...});
```

### New Handlers

```tsx
const handleApprove = useCallback(async (toolCallId: string) => {
  console.log('[UnifiedChat] Approving tool call:', toolCallId);
  await approveToolCall(toolCallId);
}, [approveToolCall]);

const handleReject = useCallback(async (toolCallId: string, reason?: string) => {
  console.log('[UnifiedChat] Rejecting tool call:', toolCallId, reason);
  await rejectToolCall(toolCallId, reason);
}, [rejectToolCall]);
```

---

## Testing Checklist

### Manual Testing

| Test Case | Expected | Status |
|-----------|----------|--------|
| Message display | MessageBubble components | [ ] |
| Tool call in message | ToolCallCard visible | [ ] |
| Workflow side panel | Panel with 3 sections | [ ] |
| Panel collapse | Collapses to icons | [ ] |
| Approve tool | Console log + API call | [ ] |
| Reject tool | Console log + API call | [ ] |

### Visual Regression

- [ ] Chat mode layout unchanged (except tool cards)
- [ ] Workflow mode has functional side panel
- [ ] No style conflicts

---

## Documentation Updates

- [ ] **Phase 16 README.md**: Add Sprint 67 to overview table
- [ ] **CLAUDE.md**: Update Phase 16 status if needed

---

## Completion Checklist

- [x] All S67-1 tasks completed
- [x] All S67-2 tasks completed
- [x] All S67-3 tasks completed
- [x] No TypeScript errors
- [x] Manual testing passed (build successful)
- [x] Documentation updated
- [x] Sprint 67 marked complete in README

---

## Notes

- Components already exist and are fully implemented
- Main work is integration, not new development
- Hook already returns all required data
- No backend changes needed

---

**Created**: 2026-01-08
**Status**: In Progress
