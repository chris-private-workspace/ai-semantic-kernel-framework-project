# Sprint 69 Checklist: Claude Code UI + Dashboard Integration

## Sprint Information

| Field | Value |
|-------|-------|
| **Sprint** | 69 |
| **Phase** | 17 - Agentic Chat Enhancement |
| **Focus** | Hierarchical Step Progress UI + Dashboard Integration + Guest User ID |
| **Points** | 21 pts |
| **Status** | ✅ Completed |

---

## Pre-Sprint Checklist

- [x] Sprint 68 completed
- [x] AG-UI CUSTOM events working
- [x] StepProgress component exists
- [x] Workflow mode functional

---

## Story Completion Tracking

### S69-1: step_progress Backend Event (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Define `SubStepStatus` enum | ✅ | pending/running/completed/failed/skipped |
| Define `SubStep` dataclass | ✅ | |
| Define `StepProgressPayload` dataclass | ✅ | |
| Implement `emit_step_progress()` | ✅ | |
| Integrate with HybridEventBridge | ✅ | |
| Emit at workflow step start | ✅ | |
| Emit on substep status change | ✅ | |
| Emit at workflow step completion | ✅ | |
| Add throttling (max 2/sec) | ✅ | |

**Files Created**:
- [x] `backend/src/integrations/ag_ui/events/progress.py`

**Files Modified**:
- [x] `backend/src/integrations/ag_ui/bridge.py`
- [x] `backend/src/integrations/hybrid/orchestrator_v2.py`

**Event Schema**:
```json
{
  "event_name": "step_progress",
  "payload": {
    "step_id": "step-001",
    "step_name": "Process documents",
    "current": 2,
    "total": 5,
    "progress": 45,
    "status": "running",
    "substeps": [
      {"id": "load", "name": "Load files", "status": "completed"},
      {"id": "parse", "name": "Parse content", "status": "running", "progress": 67},
      {"id": "analyze", "name": "Analyze", "status": "pending"}
    ]
  }
}
```

---

### S69-2: StepProgress Sub-step Component (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Create `StepProgressEnhanced.tsx` | ✅ | |
| Create `SubStepItem.tsx` | ✅ | Integrated in StepProgressEnhanced |
| Implement `StatusIcon` component | ✅ | ✓, ◉, ○, ✗ icons |
| Add main step header with progress | ✅ | |
| Add collapsible substep list | ✅ | |
| Show progress percentage | ✅ | |
| Add expand/collapse animation | ✅ | |
| Add progress bar animation | ✅ | |
| Respect reduced motion | ✅ | |
| Integrate into WorkflowSidePanel | ✅ | |

**Files Created**:
- [x] `frontend/src/components/unified-chat/StepProgressEnhanced.tsx`

**Files Modified**:
- [x] `frontend/src/components/unified-chat/index.ts`

**Visual Design**:
```
Step 2/5: Process documents (45%)  [████░░░░░░]
  ├─ ✓ Load files
  ├─ ◉ Parse content (67%)
  ├─ ○ Analyze structure
  └─ ○ Generate summary
```

**Status Icons**:
| Status | Icon | Color |
|--------|------|-------|
| completed | ✓ (Check) | green-500 |
| running | ◉ (Loader2 spinning) | blue-500 |
| pending | ○ (Circle) | gray-400 |
| failed | ✗ (AlertCircle) | red-500 |
| skipped | ⊘ (Slash) | gray-400 |

---

### S69-3: Progress Event Integration (3 pts)

| Task | Status | Notes |
|------|--------|-------|
| Add `StepProgressState` interface | ✅ | |
| Handle `step_progress` in useAGUI | ✅ | |
| Store step progress in state | ✅ | |
| Update on each progress event | ✅ | |
| Provide `currentStepProgress` getter | ✅ | |
| Clear progress on run completion | ✅ | |
| Add types to unified-chat.ts | ✅ | |
| Expose in useUnifiedChat | ✅ | |

**Files Modified**:
- [x] `frontend/src/hooks/useAGUI.ts`
- [x] `frontend/src/hooks/useUnifiedChat.ts`
- [x] `frontend/src/types/unified-chat.ts`

**Type Definitions**:
```typescript
interface SubStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress?: number;
  message?: string;
  startedAt?: string;
  completedAt?: string;
}

interface StepProgressEvent {
  stepId: string;
  stepName: string;
  current: number;
  total: number;
  progress: number;
  status: SubStep['status'];
  substeps: SubStep[];
  metadata?: Record<string, unknown>;
}
```

---

### S69-4: Dashboard Layout Integration (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Move `/chat` route under AppLayout | ✅ | |
| Add "Chat" to Sidebar navigation | ✅ | "AI 助手" |
| Import MessageSquare icon | ✅ | |
| Change UnifiedChat from h-screen to h-full | ✅ | |
| Test layout overflow | ✅ | |
| Verify ChatHeader works in container | ✅ | |
| Test responsive behavior | ✅ | |

**Files Modified**:
- [x] `frontend/src/App.tsx`
- [x] `frontend/src/components/layout/Sidebar.tsx`
- [x] `frontend/src/pages/UnifiedChat.tsx`

**Test Cases**:
- [x] Chat accessible from Dashboard sidebar
- [x] Layout fills container without overflow
- [x] ChatHeader displays correctly
- [x] Sidebar navigation works

---

### S69-5: Guest User ID Implementation (3 pts)

| Task | Status | Notes |
|------|--------|-------|
| Create `guestUser.ts` utility | ✅ | Created in Sprint 68 |
| Implement `getGuestUserId()` | ✅ | |
| Add localStorage persistence | ✅ | |
| Add `X-Guest-Id` header to API client | ✅ | |
| Create `get_user_id` dependency in backend | ✅ | |
| Update SandboxHook to use user_id | ✅ | |
| Add `setAuthenticatedUserId()` placeholder | ✅ | migrateGuestData() |

**Files Created**:
- [x] `frontend/src/utils/guestUser.ts`

**Files Modified**:
- [x] `frontend/src/api/client.ts`
- [x] `backend/src/api/v1/ag_ui/dependencies.py`
- [x] `backend/src/integrations/claude_sdk/hooks/sandbox.py`

**Test Cases**:
- [x] Guest ID generated on first visit
- [x] Guest ID persists across page refresh
- [x] API requests include X-Guest-Id header
- [x] Backend receives and uses user_id
- [x] Different browser sessions get different IDs

---

## Integration Testing

| Scenario | Status | Notes |
|----------|--------|-------|
| Workflow emits step_progress events | ✅ | Backend verified |
| Events received by frontend | ✅ | SSE verified |
| UI updates on progress event | ✅ | Component verified |
| Sub-steps show correct status | ✅ | Visual verified |
| Progress bar animates smoothly | ✅ | Animation verified |
| Reduced motion respected | ✅ | A11y verified |
| State clears on completion | ✅ | Cleanup verified |

---

## Accessibility Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Status icons have aria-label | ✅ | |
| Progress announced to screen reader | ✅ | |
| Color not only indicator | ✅ | Icons + text |
| Reduced motion supported | ✅ | prefers-reduced-motion |
| Focus management | ✅ | Expand/collapse |

---

## Post-Sprint Checklist

- [x] All stories complete (21 pts)
- [x] Visual matches Claude Code style
- [x] Animations smooth (60fps)
- [x] Accessibility audit passed
- [x] Chat integrated into Dashboard
- [x] Guest User ID works with sandbox
- [x] Phase 17 README updated
- [x] Demo recording created (optional)

---

## Phase 17 Completion Summary

After Sprint 69:

| Feature | Status |
|---------|--------|
| Sandbox Isolation (Per-User) | ✅ Sprint 68 |
| Chat History | ✅ Sprint 68 |
| Claude Code UI | ✅ Sprint 69 |
| Dashboard Integration | ✅ Sprint 69 |
| Guest User ID | ✅ Sprint 69 |

**Total Points**: 42 pts (21 + 21)

---

## Notes

### Animation Considerations
- Use CSS transitions for simple animations ✅
- Lazy load Framer Motion if needed ✅
- Always check prefers-reduced-motion ✅
- Target 60fps for smooth updates ✅

### Event Throttling
- Max 2 step_progress events per second ✅
- Batch rapid substep changes ✅
- Debounce UI updates if needed ✅

---

**Checklist Status**: ✅ Completed
**Last Updated**: 2026-01-08
