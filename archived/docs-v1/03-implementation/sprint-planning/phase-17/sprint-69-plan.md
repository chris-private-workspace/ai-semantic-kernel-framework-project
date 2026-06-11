# Sprint 69: Claude Code UI + Dashboard Integration

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 69 |
| **Phase** | 17 - Agentic Chat Enhancement |
| **Duration** | 3-4 days |
| **Total Points** | 21 |
| **Focus** | Hierarchical step progress display, Dashboard integration, and Guest User ID |

## Sprint Goals

1. Implement `step_progress` custom event in backend
2. Create sub-step progress component with visual hierarchy
3. Add progress percentage and parallel operation tracking
4. Integrate with existing StepProgress component
5. **Integrate UnifiedChat into Dashboard layout**
6. **Implement Guest User ID for per-user sandbox**

## Prerequisites

- Sprint 68 completed
- AG-UI CUSTOM events working
- StepProgress component exists from Phase 16

---

## Stories

### S69-1: step_progress Backend Event (5 pts)

**Description**: Implement the `step_progress` custom event that provides hierarchical step information including sub-steps, progress percentage, and status.

**Acceptance Criteria**:
- [ ] Define `step_progress` event schema
- [ ] Emit events during workflow execution
- [ ] Include step hierarchy (parent/child)
- [ ] Include progress percentage (0-100)
- [ ] Support sub-step status (pending/running/completed/failed)
- [ ] Emit updates at meaningful intervals

**Technical Details**:
```python
# backend/src/integrations/ag_ui/events/progress.py
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum

class SubStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SubStep:
    """Sub-step within a main step."""
    id: str
    name: str
    status: SubStepStatus
    progress: Optional[int] = None  # 0-100, optional
    message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class StepProgressPayload:
    """Payload for step_progress custom event."""
    step_id: str
    step_name: str
    current: int          # Current step number (1-based)
    total: int            # Total steps
    progress: int         # Overall progress 0-100
    status: SubStepStatus
    substeps: List[SubStep] = field(default_factory=list)
    metadata: Optional[dict] = None

def emit_step_progress(
    bridge: HybridEventBridge,
    payload: StepProgressPayload,
) -> None:
    """Emit step_progress custom event."""
    event = CustomEvent(
        event_name="step_progress",
        payload={
            "step_id": payload.step_id,
            "step_name": payload.step_name,
            "current": payload.current,
            "total": payload.total,
            "progress": payload.progress,
            "status": payload.status.value,
            "substeps": [
                {
                    "id": ss.id,
                    "name": ss.name,
                    "status": ss.status.value,
                    "progress": ss.progress,
                    "message": ss.message,
                    "started_at": ss.started_at,
                    "completed_at": ss.completed_at,
                }
                for ss in payload.substeps
            ],
            "metadata": payload.metadata,
        },
    )
    bridge.emit_event(event)
```

**Integration with Workflow Execution**:
```python
# Example usage in HybridOrchestrator
async def execute_workflow_step(self, step: WorkflowStep):
    # Emit step start
    emit_step_progress(self.bridge, StepProgressPayload(
        step_id=step.id,
        step_name=step.name,
        current=step.index,
        total=self.total_steps,
        progress=0,
        status=SubStepStatus.RUNNING,
        substeps=[
            SubStep(id="load", name="Load data", status=SubStepStatus.PENDING),
            SubStep(id="process", name="Process", status=SubStepStatus.PENDING),
            SubStep(id="save", name="Save results", status=SubStepStatus.PENDING),
        ],
    ))

    # Execute sub-steps with progress updates
    for i, substep in enumerate(step.substeps):
        # Update substep to running
        emit_step_progress(...)

        # Execute
        await self.execute_substep(substep)

        # Update substep to completed
        emit_step_progress(...)
```

**Files to Create**:
- `backend/src/integrations/ag_ui/events/progress.py`

**Files to Modify**:
- `backend/src/integrations/ag_ui/bridge.py` - Add emit helper
- `backend/src/integrations/hybrid/orchestrator_v2.py` - Emit progress events

---

### S69-2: StepProgress Sub-step Component (5 pts)

**Description**: Enhance the StepProgress component to display hierarchical sub-steps with Claude Code-style visual feedback.

**Acceptance Criteria**:
- [ ] Display main step with progress bar
- [ ] Show collapsible sub-step list
- [ ] Status icons: ✓ completed, ◉ running, ○ pending, ✗ failed
- [ ] Progress percentage on running sub-steps
- [ ] Elapsed time display
- [ ] Smooth animations for status changes
- [ ] Support reduced motion preference

**Technical Details**:
```typescript
// frontend/src/components/unified-chat/StepProgressEnhanced.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Circle, AlertCircle, Loader2 } from 'lucide-react';

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
}

interface StepProgressEnhancedProps {
  step: StepProgressEvent;
  isExpanded?: boolean;
  onToggle?: () => void;
}

const StatusIcon = ({ status }: { status: SubStep['status'] }) => {
  switch (status) {
    case 'completed':
      return <Check className="w-4 h-4 text-green-500" />;
    case 'running':
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    case 'pending':
    default:
      return <Circle className="w-4 h-4 text-gray-400" />;
  }
};

export function StepProgressEnhanced({
  step,
  isExpanded = true,
  onToggle,
}: StepProgressEnhancedProps) {
  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  return (
    <div className="space-y-2">
      {/* Main step header */}
      <div
        className="flex items-center justify-between p-2 bg-secondary/50 rounded-lg cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <StatusIcon status={step.status} />
          <span className="font-medium">
            Step {step.current}/{step.total}: {step.stepName}
          </span>
          {step.status === 'running' && (
            <span className="text-sm text-muted-foreground">
              ({step.progress}%)
            </span>
          )}
        </div>

        {/* Progress bar */}
        <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${step.progress}%` }}
            transition={{ duration: prefersReducedMotion ? 0 : 0.3 }}
          />
        </div>
      </div>

      {/* Sub-steps */}
      <AnimatePresence>
        {isExpanded && step.substeps.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
            className="ml-6 space-y-1"
          >
            {step.substeps.map((substep) => (
              <SubStepItem key={substep.id} substep={substep} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SubStepItem({ substep }: { substep: SubStep }) {
  return (
    <div className="flex items-center gap-2 py-1 text-sm">
      <StatusIcon status={substep.status} />
      <span className={substep.status === 'completed' ? 'text-muted-foreground' : ''}>
        {substep.name}
      </span>
      {substep.status === 'running' && substep.progress !== undefined && (
        <span className="text-xs text-blue-500">({substep.progress}%)</span>
      )}
      {substep.message && (
        <span className="text-xs text-muted-foreground ml-auto">
          {substep.message}
        </span>
      )}
    </div>
  );
}
```

**Claude Code-style Display Example**:
```
Step 2/5: Process documents (45%)
  ├─ ✓ Load files
  ├─ ◉ Parse content (67%)
  ├─ ○ Analyze structure
  └─ ○ Generate summary
```

**Files to Create**:
- `frontend/src/components/unified-chat/StepProgressEnhanced.tsx`
- `frontend/src/components/unified-chat/SubStepItem.tsx`

**Files to Modify**:
- `frontend/src/components/unified-chat/WorkflowSidePanel.tsx` - Use enhanced component

---

### S69-3: Progress Event Integration (3 pts)

**Description**: Integrate the step_progress event handling in the frontend hooks and connect to the enhanced UI components.

**Acceptance Criteria**:
- [ ] Handle `step_progress` CUSTOM event in useAGUI
- [ ] Store step progress state
- [ ] Update state on each progress event
- [ ] Provide getter for current step progress
- [ ] Clear progress on run completion

**Technical Details**:
```typescript
// frontend/src/hooks/useAGUI.ts - Add to existing

interface StepProgressState {
  steps: Map<string, StepProgressEvent>;
  currentStep: string | null;
}

const useAGUI = () => {
  const [stepProgress, setStepProgress] = useState<StepProgressState>({
    steps: new Map(),
    currentStep: null,
  });

  const handleCustomEvent = (event: CustomAGUIEvent) => {
    if (event.payload.event_name === 'step_progress') {
      const progress = event.payload as StepProgressEvent;

      setStepProgress((prev) => {
        const newSteps = new Map(prev.steps);
        newSteps.set(progress.stepId, progress);

        return {
          steps: newSteps,
          currentStep: progress.status === 'running' ? progress.stepId : prev.currentStep,
        };
      });
    }

    // Handle other custom events...
  };

  // Reset on run completion
  useEffect(() => {
    if (runStatus === 'completed' || runStatus === 'error') {
      setStepProgress({ steps: new Map(), currentStep: null });
    }
  }, [runStatus]);

  return {
    // ... existing returns
    stepProgress,
    currentStepProgress: stepProgress.currentStep
      ? stepProgress.steps.get(stepProgress.currentStep)
      : null,
  };
};
```

**Files to Modify**:
- `frontend/src/hooks/useAGUI.ts` - Handle step_progress event
- `frontend/src/hooks/useUnifiedChat.ts` - Expose step progress
- `frontend/src/types/unified-chat.ts` - Add StepProgressEvent types

---

### S69-4: Dashboard Layout Integration (5 pts)

**Description**: Integrate UnifiedChat page into Dashboard layout (AppLayout), adding Sidebar and Header.

**Acceptance Criteria**:
- [ ] Change `/chat` route to AppLayout child route
- [ ] Add "Chat" or "Assistant" navigation item in Sidebar
- [ ] Adjust UnifiedChat layout to fit AppLayout container
- [ ] Keep ChatHeader as page-level header
- [ ] Remove standalone page title (handled by AppLayout Header)

**Technical Details**:
```tsx
// App.tsx - Route changes
// Before:
<Route path="/chat" element={<UnifiedChat />} />  // Standalone

// After:
<Route path="/" element={<AppLayout />}>
  <Route path="dashboard" element={<DashboardPage />} />
  <Route path="chat" element={<UnifiedChat />} />  // Integrated
  ...
</Route>
```

```tsx
// Sidebar.tsx - Add navigation item
const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Chat', href: '/chat', icon: MessageSquare },  // New
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  ...
];
```

```tsx
// UnifiedChat.tsx - Layout adjustment
// Before: h-screen (full screen)
// After: h-full (fill AppLayout container)

return (
  <div className="flex flex-col h-full">  {/* Changed from h-screen */}
    <ChatHeader ... />
    <div className="flex-1 overflow-hidden">
      ...
    </div>
  </div>
);
```

**Files to Modify**:
- `frontend/src/App.tsx` - Route integration
- `frontend/src/components/layout/Sidebar.tsx` - Add navigation
- `frontend/src/pages/UnifiedChat.tsx` - Layout adaptation

---

### S69-5: Guest User ID Implementation (3 pts)

**Description**: Implement Guest User ID mechanism to provide user identification for per-user sandbox.

**Acceptance Criteria**:
- [ ] Create `getGuestUserId()` utility function
- [ ] localStorage persistence for Guest UUID
- [ ] Pass user_id in API requests
- [ ] Backend receives and uses user_id for sandbox directories
- [ ] Prepare Phase 18 migration interface

**Technical Details**:
```typescript
// frontend/src/utils/guestUser.ts
const GUEST_USER_KEY = 'ipa_guest_user_id';

export function getGuestUserId(): string {
  let userId = localStorage.getItem(GUEST_USER_KEY);
  if (!userId) {
    userId = `guest-${crypto.randomUUID()}`;
    localStorage.setItem(GUEST_USER_KEY, userId);
  }
  return userId;
}

// For Phase 18 use
export function setAuthenticatedUserId(userId: string): void {
  const guestId = localStorage.getItem(GUEST_USER_KEY);
  if (guestId) {
    // Call backend migration API
    migrateGuestData(guestId, userId);
  }
  localStorage.removeItem(GUEST_USER_KEY);
}
```

```python
# backend/src/api/v1/ag_ui/dependencies.py
def get_user_id(
    x_user_id: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None),
) -> str:
    """Get user ID from headers (auth or guest)."""
    if x_user_id:  # Authenticated user (Phase 18)
        return x_user_id
    if x_guest_id:  # Guest user (Phase 17)
        return x_guest_id
    raise HTTPException(status_code=401, detail="User ID required")
```

**Files to Create**:
- `frontend/src/utils/guestUser.ts`

**Files to Modify**:
- `backend/src/api/v1/ag_ui/dependencies.py` - Add get_user_id
- `backend/src/integrations/claude_sdk/hooks/sandbox.py` - Use user_id
- `frontend/src/api/client.ts` - Add X-Guest-Id header

---

## Technical Notes

### Event Flow

```
Backend Workflow Execution
         │
         ▼
   emit_step_progress()
         │
         ▼
   CustomEvent(step_progress)
         │
         ▼
   SSE Stream
         │
         ▼
   Frontend useAGUI
         │
         ▼
   handleCustomEvent()
         │
         ▼
   setStepProgress()
         │
         ▼
   StepProgressEnhanced component
```

### Progress Calculation

```python
# Calculate overall progress from substeps
def calculate_step_progress(substeps: List[SubStep]) -> int:
    if not substeps:
        return 0

    completed = sum(1 for s in substeps if s.status == "completed")
    running_progress = sum(
        (s.progress or 0) / 100
        for s in substeps
        if s.status == "running"
    )

    total_progress = completed + running_progress
    return int((total_progress / len(substeps)) * 100)
```

### Animation Configuration

```typescript
// Respect reduced motion preference
const animationConfig = {
  duration: prefersReducedMotion ? 0 : 0.3,
  ease: 'easeOut',
};

// Progress bar animation
const progressVariants = {
  initial: { width: 0 },
  animate: (progress: number) => ({
    width: `${progress}%`,
    transition: animationConfig,
  }),
};
```

---

## Dependencies

### From Previous Sprints
- Sprint 68: Sandbox + History
- Phase 16: StepProgress base component
- AG-UI CUSTOM event infrastructure

### External
- Framer Motion (optional, for animations)
- Lucide React icons

---

## Definition of Done

- [ ] All 5 stories completed and tested
- [ ] step_progress events emit during workflow
- [ ] Sub-steps display with correct status icons
- [ ] Progress percentage updates in real-time
- [ ] Animations respect reduced motion
- [ ] Chat page integrated into Dashboard layout
- [ ] Guest User ID works with per-user sandbox
- [ ] Integration tests pass

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Event overhead | Low | Throttle updates to max 2/sec |
| Animation jank | Low | Use CSS transitions, lazy load Framer |
| State size growth | Low | Clear on run completion |
| Layout overflow | Medium | Test with various content sizes |
| Guest ID persistence | Low | localStorage with fallback |

---

## Sprint Velocity Reference

UI enhancement work with Dashboard integration and Guest User ID.
Expected completion: 3-4 days for 21 pts
