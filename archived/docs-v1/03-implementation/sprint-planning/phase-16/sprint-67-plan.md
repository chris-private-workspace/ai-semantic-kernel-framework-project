# Sprint 67 Plan: UnifiedChat UI Component Integration

## Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 67 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Type** | Bug Fix / Integration Sprint |
| **Story Points** | 8 pts |
| **Duration** | 1 day |
| **Dependencies** | Sprint 66 (Tool Integration) |

---

## Objective

Integrate existing UI components (`ChatArea`, `WorkflowSidePanel`) into the `UnifiedChat.tsx` page to enable:
- Tool call visualization in the chat area
- Workflow side panel with progress tracking
- Inline approval UI for HITL workflow

---

## Problem Statement

Current `/chat` page does not match Phase 16 design specifications:

1. **Missing Side Panel**: Workflow mode shows placeholder instead of `WorkflowSidePanel`
2. **No Tool Calls Display**: Messages only show text content, no tool call cards
3. **Unused Components**: Existing components (`ChatArea`, `MessageList`, `ToolCallTracker`) are implemented but not integrated

### Root Cause

`UnifiedChat.tsx` manually renders messages with `<div>` and `<p>` tags instead of using:
- `ChatArea` component (which includes `MessageList` with tool call support)
- `WorkflowSidePanel` component (which includes tool tracking and checkpoints)

---

## User Stories

### S67-1: Integrate ChatArea Component (3 pts)

**Objective**: Replace manual message rendering with `ChatArea` component

**Acceptance Criteria**:
- [ ] Messages display using `MessageBubble` component
- [ ] Tool calls show as `ToolCallCard` within messages
- [ ] Streaming indicator displays during AI response
- [ ] Auto-scroll to latest message works

**Technical Details**:
- Import `ChatArea` from `@/components/unified-chat/ChatArea`
- Replace lines 335-395 (manual rendering) with `<ChatArea>` component
- Pass required props: `messages`, `isStreaming`, `pendingApprovals`, `onApprove`, `onReject`

---

### S67-2: Integrate WorkflowSidePanel (3 pts)

**Objective**: Replace placeholder with full `WorkflowSidePanel` component

**Acceptance Criteria**:
- [ ] Side panel shows in Workflow mode only
- [ ] Step Progress displays workflow steps
- [ ] Tool Call Tracker shows tool execution timeline
- [ ] Checkpoint List displays available checkpoints
- [ ] Panel can be collapsed/expanded

**Technical Details**:
- Import `WorkflowSidePanel` from `@/components/unified-chat/WorkflowSidePanel`
- Replace lines 399-412 (placeholder) with `<WorkflowSidePanel>` component
- Pass required props: `workflowState`, `toolCalls`, `checkpoints`, `onRestoreCheckpoint`

---

### S67-3: Connect Approval Handlers (2 pts)

**Objective**: Wire up approval/reject handlers to API and UI

**Acceptance Criteria**:
- [ ] `handleApprove` calls `approveToolCall` from hook
- [ ] `handleReject` calls `rejectToolCall` from hook
- [ ] Inline approval UI triggers handlers correctly

**Technical Details**:
- Use `approveToolCall` and `rejectToolCall` from `useUnifiedChat` hook
- Create wrapper handlers that log and call API

---

## Technical Design

### Component Integration Map

```
Before (Current):
UnifiedChat.tsx
  └─ Manual <div> rendering → Only text, no tools

After (Target):
UnifiedChat.tsx
  ├─ ChatArea
  │   ├─ MessageList
  │   │   ├─ MessageBubble (with ToolCallCard)
  │   │   └─ InlineApproval
  │   └─ StreamingIndicator
  │
  └─ WorkflowSidePanel (workflow mode only)
      ├─ StepProgress
      ├─ ToolCallTracker
      └─ CheckpointList
```

### Props Flow

```
useUnifiedChat Hook Returns:
  ├─ messages ─────────────────→ ChatArea.messages
  ├─ isStreaming ─────────────→ ChatArea.isStreaming
  ├─ pendingApprovals ─────────→ ChatArea.pendingApprovals
  ├─ approveToolCall ──────────→ handleApprove
  ├─ rejectToolCall ───────────→ handleReject
  ├─ workflowState ────────────→ WorkflowSidePanel.workflowState
  ├─ toolCalls ────────────────→ WorkflowSidePanel.toolCalls
  └─ checkpoints ──────────────→ WorkflowSidePanel.checkpoints
```

---

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/pages/UnifiedChat.tsx` | Modify | Integrate ChatArea and WorkflowSidePanel |

## Files Referenced (No Changes)

| File | Purpose |
|------|---------|
| `frontend/src/components/unified-chat/ChatArea.tsx` | Chat container with MessageList |
| `frontend/src/components/unified-chat/WorkflowSidePanel.tsx` | Side panel component |
| `frontend/src/components/unified-chat/MessageList.tsx` | Message rendering with tools |
| `frontend/src/hooks/useUnifiedChat.ts` | Hook providing all required state |

---

## Testing Plan

### Manual Testing

| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Tool call display | Send "Search for AI news" | Tool call card appears in chat |
| Side panel | Switch to Workflow mode | Side panel shows with sections |
| Panel collapse | Click collapse button | Panel collapses to icons |
| Inline approval | Trigger low-risk tool | Inline approval buttons appear |

### Visual Verification

1. Chat Mode:
   - Messages have proper styling
   - Tool calls show as cards
   - Streaming indicator works

2. Workflow Mode:
   - Side panel visible
   - Progress bar shows steps
   - Tool tracker shows calls
   - Checkpoints listed

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Component type mismatch | Medium | Check ChatAreaProps compatibility |
| Missing handler props | Low | Hook already provides all handlers |
| Style conflicts | Low | Components already styled |

---

## Success Criteria

- [ ] `/chat` page shows tool calls in messages
- [ ] Workflow mode displays functional side panel
- [ ] Approval handlers work correctly
- [ ] No TypeScript errors
- [ ] No visual regressions

---

## Related Documentation

- [Phase 16 README](README.md)
- [Sprint 66 Plan](sprint-66-plan.md) - Tool Integration Bug Fix
- [Sprint 62 Plan](sprint-62-plan.md) - Core Architecture

---

**Created**: 2026-01-08
**Author**: Claude Code
