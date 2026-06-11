# Sprint 62 Checklist: Core Architecture & Adaptive Layout

## Pre-Sprint Verification

- [ ] Phase 15 AG-UI components available for reuse
- [ ] AG-UI SSE endpoint operational (`/api/v1/ag-ui`)
- [ ] Hybrid orchestrator API endpoints ready
- [ ] Development environment configured

---

## S62-1: UnifiedChatWindow Base Architecture (8 pts)

### Files Created
- [ ] `frontend/src/pages/UnifiedChat.tsx`
- [ ] `frontend/src/components/unified-chat/index.ts`
- [ ] `frontend/src/types/unified-chat.ts`
- [ ] `frontend/src/components/unified-chat/ChatHeader.tsx`
- [ ] `frontend/src/components/unified-chat/ChatInput.tsx`
- [ ] `frontend/src/components/unified-chat/StatusBar.tsx`

### Implementation Checklist
- [ ] Page component renders without errors
- [ ] Route `/chat` configured in router
- [ ] Header shows mode toggle buttons
- [ ] Input area has text field and send button
- [ ] Status bar displays placeholder values
- [ ] Layout uses full viewport height

### Verification Commands
```bash
# Run frontend dev server
cd frontend && npm run dev

# Navigate to /chat route
# Verify basic layout renders
```

---

## S62-2: Adaptive Layout Logic (7 pts)

### Files Created
- [ ] `frontend/src/hooks/useHybridMode.ts`
- [ ] `frontend/src/stores/unifiedChatStore.ts` (if using Zustand)

### Implementation Checklist
- [ ] `useHybridMode` hook implemented
- [ ] Auto-detection subscribes to AG-UI events
- [ ] Manual override works via header buttons
- [ ] `currentMode` reflects correct state
- [ ] `isManuallyOverridden` flag accurate
- [ ] Mode persists during session

### Hook API Verification
```typescript
// Test hook returns expected interface
const {
  currentMode,      // 'chat' | 'workflow'
  autoMode,         // 'chat' | 'workflow'
  manualOverride,   // 'chat' | 'workflow' | null
  isManuallyOverridden, // boolean
  setManualOverride,    // function
} = useHybridMode();
```

### Verification Steps
- [ ] Default mode is 'chat'
- [ ] Clicking Workflow button changes mode
- [ ] Clicking Chat button reverts mode
- [ ] Manual override indicator shows when active
- [ ] Auto mode updates from backend events

---

## S62-3: ChatArea Component (8 pts)

### Files Created
- [ ] `frontend/src/components/unified-chat/ChatArea.tsx`
- [ ] `frontend/src/components/unified-chat/MessageList.tsx`
- [ ] `frontend/src/components/unified-chat/InlineApproval.tsx`

### Reused/Adapted Files
- [ ] `MessageBubble.tsx` from AG-UI Demo
- [ ] `ToolCallCard.tsx` from AG-UI Demo
- [ ] `StreamingIndicator.tsx` from AG-UI Demo

### Implementation Checklist
- [ ] ChatArea renders message list
- [ ] User messages display correctly
- [ ] Assistant messages display correctly
- [ ] Tool calls render within messages
- [ ] Inline approval buttons show for low/medium risk
- [ ] Streaming indicator shows during response
- [ ] Auto-scroll to latest message works
- [ ] Empty state handled gracefully

### Verification Steps
```typescript
// Test with mock data
const mockMessages = [
  { role: 'user', content: 'Hello' },
  { role: 'assistant', content: 'Hi there!', toolCalls: [...] }
];
```
- [ ] Messages render in correct order
- [ ] Tool calls expandable/collapsible
- [ ] Approve/Reject buttons functional
- [ ] Scroll behavior smooth

---

## S62-4: WorkflowSidePanel Component (7 pts)

### Files Created
- [ ] `frontend/src/components/unified-chat/WorkflowSidePanel.tsx`
- [ ] `frontend/src/components/unified-chat/StepProgress.tsx`
- [ ] `frontend/src/components/unified-chat/ToolCallTracker.tsx`
- [ ] `frontend/src/components/unified-chat/CheckpointList.tsx`

### Implementation Checklist
- [ ] Panel renders when mode is 'workflow'
- [ ] Panel hidden when mode is 'chat'
- [ ] StepProgress shows current/total steps
- [ ] Progress bar visualizes completion
- [ ] ToolCallTracker shows tool timeline
- [ ] Tool status icons (pending, running, done, failed)
- [ ] Execution time displayed per tool
- [ ] CheckpointList shows available checkpoints
- [ ] Restore button functional
- [ ] Panel collapsible (optional)

### Verification Steps
```typescript
// Test with mock workflow data
const mockWorkflow = {
  steps: [
    { name: 'Analyze', status: 'completed' },
    { name: 'Execute', status: 'running' },
    { name: 'Verify', status: 'pending' }
  ],
  currentStep: 2,
  toolCalls: [
    { name: 'search', status: 'completed', duration: 1200 },
    { name: 'analyze', status: 'running', duration: null }
  ],
  checkpoints: [
    { id: 'cp-001', timestamp: '...', canRestore: true }
  ]
};
```
- [ ] Steps display with correct status
- [ ] Progress bar at 40% (2/5)
- [ ] Tools show in timeline order
- [ ] Checkpoint restore triggers callback

---

## Integration Tests

### Layout Adaptation
- [ ] Chat mode: full-width chat area
- [ ] Workflow mode: chat area + side panel
- [ ] Transition animation smooth
- [ ] No layout shift during mode change

### Component Communication
- [ ] Header mode buttons update `useHybridMode`
- [ ] ChatArea receives messages from parent
- [ ] WorkflowSidePanel receives workflow state
- [ ] StatusBar reflects current metrics

### Responsive Behavior (Desktop)
- [ ] Works at 1024px width
- [ ] Works at 1280px width
- [ ] Works at 1920px width
- [ ] Side panel doesn't overflow

---

## Code Quality

### TypeScript
- [ ] All components have proper type definitions
- [ ] No `any` types used
- [ ] Props interfaces documented
- [ ] Hooks have return type annotations

### Styling
- [ ] Consistent Tailwind class usage
- [ ] Uses Shadcn UI components where applicable
- [ ] Dark mode compatible (if applicable)
- [ ] No inline styles

### Performance
- [ ] No unnecessary re-renders
- [ ] Memoization where appropriate
- [ ] Virtual list for long message histories (optional)

---

## Definition of Done

- [ ] All 4 stories completed
- [ ] Manual testing passed
- [ ] TypeScript compilation succeeds
- [ ] ESLint passes
- [ ] Code reviewed
- [ ] Documentation updated

---

## Sprint Completion Sign-off

| Item | Status | Date | Notes |
|------|--------|------|-------|
| S62-1 Complete | ⬜ | | |
| S62-2 Complete | ⬜ | | |
| S62-3 Complete | ⬜ | | |
| S62-4 Complete | ⬜ | | |
| Integration Tested | ⬜ | | |
| Sprint Complete | ⬜ | | |

**Total Points**: 30 pts
**Completion Date**: TBD
