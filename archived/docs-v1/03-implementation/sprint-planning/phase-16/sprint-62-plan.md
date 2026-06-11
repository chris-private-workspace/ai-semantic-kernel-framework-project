# Sprint 62: Core Architecture & Adaptive Layout

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 62 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Duration** | 3-4 days |
| **Total Points** | 30 |
| **Focus** | Core architecture and adaptive layout system |

## Sprint Goals

1. Establish the foundational architecture for the unified chat interface
2. Implement adaptive layout that switches between Chat and Workflow modes
3. Build core reusable components for the conversation area
4. Set up the side panel infrastructure for Workflow mode

## Stories

### S62-1: UnifiedChatWindow Base Architecture (8 pts)

**Description**: Create the foundational structure for the unified chat window, including page component, routing, and basic layout containers.

**Acceptance Criteria**:
- [ ] Create `UnifiedChat.tsx` page component
- [ ] Add route `/chat` or `/assistant` in router
- [ ] Implement base layout structure (header, main, input, status bar)
- [ ] Set up component directory structure under `components/unified-chat/`
- [ ] Create type definitions in `types/unified-chat.ts`

**Technical Details**:
```typescript
// Page structure
<UnifiedChatPage>
  <ChatHeader />
  <MainContent>
    <ChatArea />
    {mode === 'workflow' && <WorkflowSidePanel />}
  </MainContent>
  <ChatInput />
  <StatusBar />
</UnifiedChatPage>
```

**Files to Create**:
- `frontend/src/pages/UnifiedChat.tsx`
- `frontend/src/components/unified-chat/index.ts`
- `frontend/src/types/unified-chat.ts`

---

### S62-2: Adaptive Layout Logic (7 pts)

**Description**: Implement the `useHybridMode` hook that manages automatic mode detection and manual override for layout adaptation.

**Acceptance Criteria**:
- [ ] Create `useHybridMode` hook with auto-detection logic
- [ ] Implement manual override capability
- [ ] Add visual indicator for current mode
- [ ] Support smooth transition between modes
- [ ] Persist manual override preference in session

**Technical Details**:
```typescript
interface UseHybridModeReturn {
  currentMode: 'chat' | 'workflow';
  autoMode: 'chat' | 'workflow';
  manualOverride: 'chat' | 'workflow' | null;
  isManuallyOverridden: boolean;
  setManualOverride: (mode: 'chat' | 'workflow' | null) => void;
}

// Usage
const { currentMode, setManualOverride, isManuallyOverridden } = useHybridMode();
```

**Files to Create**:
- `frontend/src/hooks/useHybridMode.ts`

**Integration Points**:
- Connect to AG-UI event stream for mode detection
- Subscribe to IntentRouter results from backend

---

### S62-3: ChatArea Component (8 pts)

**Description**: Build the main conversation area component that displays messages, tool calls, and inline approvals.

**Acceptance Criteria**:
- [ ] Create `ChatArea.tsx` container component
- [ ] Create `MessageList.tsx` for message rendering
- [ ] Reuse/adapt `MessageBubble.tsx` from AG-UI Demo
- [ ] Reuse/adapt `ToolCallCard.tsx` from AG-UI Demo
- [ ] Create `InlineApproval.tsx` for low-risk approvals
- [ ] Support auto-scroll to latest message
- [ ] Handle streaming message updates

**Technical Details**:
```typescript
interface ChatAreaProps {
  messages: Message[];
  isStreaming: boolean;
  onApprove: (toolCallId: string) => void;
  onReject: (toolCallId: string, reason?: string) => void;
}
```

**Component Hierarchy**:
```
ChatArea/
├── MessageList
│   ├── MessageBubble (user)
│   ├── MessageBubble (assistant)
│   │   ├── ToolCallCard
│   │   │   └── InlineApproval (low/medium risk)
│   │   └── StreamingIndicator
```

**Files to Create/Modify**:
- `frontend/src/components/unified-chat/ChatArea.tsx`
- `frontend/src/components/unified-chat/MessageList.tsx`
- `frontend/src/components/unified-chat/InlineApproval.tsx`
- Adapt existing AG-UI components

---

### S62-4: WorkflowSidePanel Component (7 pts)

**Description**: Create the side panel component that displays workflow progress, tool tracking, and checkpoint management when in Workflow mode.

**Acceptance Criteria**:
- [ ] Create `WorkflowSidePanel.tsx` container
- [ ] Create `StepProgress.tsx` for workflow step visualization
- [ ] Create `ToolCallTracker.tsx` for tool execution timeline
- [ ] Create `CheckpointList.tsx` for checkpoint display
- [ ] Implement collapsible panel behavior
- [ ] Support panel width adjustment (optional)

**Technical Details**:
```typescript
interface WorkflowSidePanelProps {
  steps: WorkflowStep[];
  currentStep: number;
  toolCalls: ToolCallStatus[];
  checkpoints: Checkpoint[];
  onRestoreCheckpoint: (checkpointId: string) => void;
}
```

**Panel Sections**:
1. **Step Progress** (top)
   - Current step / total steps
   - Progress bar visualization
   - Step names with status icons

2. **Tool Call Tracker** (middle)
   - Timeline of tool executions
   - Status: pending → running → completed/failed
   - Execution time for each tool

3. **Checkpoint List** (bottom)
   - Available checkpoints with timestamps
   - Restore button for each checkpoint
   - Current checkpoint indicator

**Files to Create**:
- `frontend/src/components/unified-chat/WorkflowSidePanel.tsx`
- `frontend/src/components/unified-chat/StepProgress.tsx`
- `frontend/src/components/unified-chat/ToolCallTracker.tsx`
- `frontend/src/components/unified-chat/CheckpointList.tsx`

---

## Dependencies

### External Dependencies
- Shadcn UI components (already installed)
- Tailwind CSS (already configured)
- Zustand (already installed)
- AG-UI hooks from Phase 15

### Internal Dependencies
- AG-UI Demo components for reference/reuse
- Hybrid orchestrator API endpoints
- AG-UI SSE event stream

## Technical Notes

### Layout CSS Structure
```css
/* Main container */
.unified-chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Adaptive main content */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  /* Workflow mode: flex: 2/3 */
}

.workflow-panel {
  width: 320px; /* or 1/3 of container */
  border-left: 1px solid var(--border);
}
```

### State Management Strategy
```typescript
// Zustand store for unified chat
interface UnifiedChatState {
  mode: 'chat' | 'workflow';
  manualOverride: 'chat' | 'workflow' | null;
  messages: Message[];
  workflowState: WorkflowState | null;
  pendingApprovals: PendingApproval[];
  // ... actions
}
```

## Definition of Done

- [ ] All stories completed and tested
- [ ] Component storybook entries (optional)
- [ ] Unit tests for hooks (useHybridMode)
- [ ] Integration with existing AG-UI backend
- [ ] Responsive layout on desktop (1024px+)
- [ ] Code review completed
- [ ] Documentation updated

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| AG-UI Demo component reuse issues | Medium | Create adapter components if needed |
| Mode detection latency | Low | Use optimistic UI updates |
| Layout responsiveness | Low | Focus on desktop first |

## Sprint Velocity Reference

Based on previous sprints:
- Sprint 58 (AG-UI Core): 30 pts - 3 days
- Sprint 59 (AG-UI Features): 28 pts - 3 days
- Sprint 60 (AG-UI Advanced): 27 pts - 3 days

Expected completion: 3-4 days for 30 pts
