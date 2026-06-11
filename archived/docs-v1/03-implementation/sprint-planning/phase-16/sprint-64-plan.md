# Sprint 64: Approval Flow & Risk Indicators

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 64 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Duration** | 3-4 days |
| **Total Points** | 29 |
| **Focus** | HITL approval workflows and risk visualization |

## Sprint Goals

1. Implement complete Human-in-the-Loop (HITL) approval workflow
2. Build approval dialog for high-risk operations
3. Create comprehensive risk indicator system
4. Integrate with backend approval API

## Prerequisites

- Sprint 62 completed (Core Architecture)
- Sprint 63 completed (SSE Integration)
- Backend approval endpoints operational
- Risk assessment service ready

---

## Stories

### S64-1: useApprovalFlow Hook (10 pts) ⬆️ Enhanced

**Description**: Create a dedicated hook for managing approval state, handling approval requests, coordinating with the backend, and handling mode switch confirmations.

**Acceptance Criteria**:
- [ ] Create `useApprovalFlow` hook
- [ ] Track pending approvals list
- [ ] Manage dialog approval state (for high-risk)
- [ ] Implement `approve()` function
- [ ] Implement `reject()` function with reason
- [ ] Handle approval timeouts
- [ ] Integrate with AG-UI events
- [ ] **🆕 Mode switch confirmation**: Confirm automatic mode switches
- [ ] **🆕 Mode switch dialog**: Show ModeSwitchConfirmDialog for complex switches

**Technical Details**:
```typescript
interface UseApprovalFlowReturn {
  // State
  pendingApprovals: PendingApproval[];
  dialogApproval: PendingApproval | null;
  isProcessing: boolean;

  // Actions
  approve: (toolCallId: string) => Promise<void>;
  reject: (toolCallId: string, reason?: string) => Promise<void>;
  dismissDialog: () => void;

  // Derived
  hasPendingApprovals: boolean;
  highRiskCount: number;
}

interface PendingApproval {
  toolCallId: string;
  toolName: string;
  arguments: Record<string, unknown>;
  riskLevel: RiskLevel;
  riskScore: number;
  riskFactors: string[];
  requestedAt: string;
  timeoutAt?: string;
}
```

**Files to Create**:
- `frontend/src/hooks/useApprovalFlow.ts`
- `frontend/src/components/unified-chat/ModeSwitchConfirmDialog.tsx` - 🆕

**Dependencies**:
- AG-UI `TOOL_CALL_START` events with approval requirement
- Backend approval API endpoints

**🆕 Mode Switch Confirmation**:
```typescript
// ModeSwitchConfirmDialog for complex mode switches
interface ModeSwitchConfirmProps {
  from: ExecutionMode;
  to: ExecutionMode;
  reason: string;
  confidence: number;
  onConfirm: () => void;
  onCancel: () => void;
  open: boolean;
}

// Trigger confirmation for significant mode switches
const handleModeSwitch = (event: ModeDetectionPayload) => {
  // Auto-accept high-confidence simple switches
  if (event.confidence >= 0.9 && !event.isComplexSwitch) {
    acceptModeSwitch(event.mode);
    return;
  }

  // Require confirmation for complex or lower-confidence switches
  setModeSwitchPending({
    from: currentMode,
    to: event.mode,
    reason: event.reason,
    confidence: event.confidence,
  });
};
```

---

### S64-2: ApprovalDialog Component (7 pts)

**Description**: Build a modal dialog for high-risk and critical approval requests with detailed risk information.

**Acceptance Criteria**:
- [ ] Create `ApprovalDialog.tsx` component
- [ ] Display tool name and arguments
- [ ] Show risk level with color coding
- [ ] List risk factors and explanations
- [ ] Provide approve/reject buttons
- [ ] Support rejection reason input
- [ ] Show countdown timer for timeout
- [ ] Accessible keyboard navigation

**Technical Details**:
```typescript
interface ApprovalDialogProps {
  approval: PendingApproval;
  onApprove: () => void;
  onReject: (reason?: string) => void;
  onDismiss: () => void;
  isProcessing: boolean;
}
```

**Component Structure**:
```
ApprovalDialog/
├── DialogHeader (title, close button)
├── RiskBadge (level indicator)
├── ToolInfo (name, arguments)
├── RiskFactors (list of concerns)
├── TimeoutCountdown (if applicable)
├── RejectReasonInput (optional)
└── ActionButtons (Approve, Reject)
```

**Files to Create**:
- `frontend/src/components/unified-chat/ApprovalDialog.tsx`

**Shadcn UI Components**:
- Dialog, DialogContent, DialogHeader, DialogFooter
- Button, Badge, Input, Textarea
- AlertTriangle icon for risk

---

### S64-3: Risk Indicator System (7 pts) ⬆️ Enhanced

**Description**: Implement comprehensive risk visualization across the interface with detailed risk factor information.

**Acceptance Criteria**:
- [ ] Create `RiskIndicator` component for StatusBar
- [ ] Color-coded risk levels (green/yellow/orange/red)
- [ ] Show risk score (0-100)
- [ ] Tooltip with risk details
- [ ] Animate on risk level change
- [ ] Support different sizes (sm, md, lg)
- [ ] **🆕 Display risk factors**: List of specific risk factors from RiskAssessmentEngine
- [ ] **🆕 Display reasoning**: Explanation of why this risk level was assigned

**Technical Details**:
```typescript
type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

interface RiskIndicatorProps {
  level: RiskLevel;
  score: number;
  factors?: string[];
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
  showTooltip?: boolean;
}

// Color mapping
const riskColors: Record<RiskLevel, string> = {
  low: 'bg-green-500',
  medium: 'bg-yellow-500',
  high: 'bg-orange-500',
  critical: 'bg-red-500',
};
```

**Files to Create/Modify**:
- `frontend/src/components/unified-chat/RiskIndicator.tsx` - New
- `frontend/src/components/unified-chat/StatusBar.tsx` - Integrate RiskIndicator

**Visual Design**:
- Low: Green dot, "Low" text
- Medium: Yellow dot, "Medium" text
- High: Orange dot with pulse animation, "High" text
- Critical: Red dot with strong pulse, "Critical!" text

**🆕 Enhanced RiskIndicator with Detailed Tooltip**:
```typescript
interface RiskIndicatorProps {
  level: RiskLevel;
  score: number;
  factors?: string[];       // 🆕 Risk factors from backend
  reasoning?: string;       // 🆕 Risk assessment reasoning
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
  showTooltip?: boolean;
}

// RiskIndicator with detailed tooltip
const RiskIndicator: FC<RiskIndicatorProps> = ({
  level,
  score,
  factors = [],
  reasoning,
  size = 'md',
  showTooltip = true,
}) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <div className={cn("flex items-center gap-1", sizeClasses[size])}>
        <span className={cn("rounded-full", riskColors[level], pulseClasses[level])} />
        <span className="capitalize">{level}</span>
        {showScore && <span className="text-muted-foreground">({score})</span>}
      </div>
    </TooltipTrigger>
    {showTooltip && (
      <TooltipContent className="max-w-xs">
        <div className="space-y-2">
          <div className="font-medium">Risk Assessment: {level.toUpperCase()}</div>
          <div className="text-sm">Score: {score}/100</div>

          {/* 🆕 Risk Factors */}
          {factors.length > 0 && (
            <div>
              <p className="text-sm font-medium">Risk Factors:</p>
              <ul className="text-sm text-muted-foreground list-disc list-inside">
                {factors.map((factor, i) => (
                  <li key={i}>{factor}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 🆕 Reasoning */}
          {reasoning && (
            <div>
              <p className="text-sm font-medium">Assessment Reasoning:</p>
              <p className="text-sm text-muted-foreground">{reasoning}</p>
            </div>
          )}
        </div>
      </TooltipContent>
    )}
  </Tooltip>
);
```

---

### S64-4: Approval API Integration (5 pts)

**Description**: Connect frontend approval actions to backend API endpoints.

**Acceptance Criteria**:
- [ ] Implement API client for approval endpoints
- [ ] `POST /api/v1/ag-ui/approve` integration
- [ ] `POST /api/v1/ag-ui/reject` integration
- [ ] Handle API errors gracefully
- [ ] Optimistic updates with rollback
- [ ] Loading states during API calls

**Technical Details**:
```typescript
// API endpoints
const approvalApi = {
  approve: (toolCallId: string) =>
    apiClient.post(`/api/v1/ag-ui/tool-calls/${toolCallId}/approve`),

  reject: (toolCallId: string, reason?: string) =>
    apiClient.post(`/api/v1/ag-ui/tool-calls/${toolCallId}/reject`, { reason }),
};

// In useApprovalFlow
const approve = async (toolCallId: string) => {
  setIsProcessing(true);

  // Optimistic update
  removeFromPending(toolCallId);

  try {
    await approvalApi.approve(toolCallId);
  } catch (error) {
    // Rollback
    addToPending(originalApproval);
    showError('Approval failed');
  } finally {
    setIsProcessing(false);
  }
};
```

**Files to Modify**:
- `frontend/src/api/endpoints/ag-ui.ts` - Add approval endpoints
- `frontend/src/hooks/useApprovalFlow.ts` - API integration

---

## Technical Notes

### Approval Flow Sequence

```
1. Backend detects high-risk tool call
2. AG-UI sends TOOL_CALL_START with requiresApproval: true
3. Frontend adds to pendingApprovals
4. If high/critical risk → show ApprovalDialog
5. User approves/rejects
6. Frontend calls approval API
7. Backend executes or cancels tool
8. AG-UI sends TOOL_CALL_END with result
```

### Risk Level Decision Tree

```typescript
const handleToolCallStart = (event: ToolCallStartEvent) => {
  if (!event.requiresApproval) return;

  const approval: PendingApproval = {
    toolCallId: event.toolCallId,
    toolName: event.toolName,
    arguments: event.arguments,
    riskLevel: event.riskLevel,
    riskScore: event.riskScore,
    riskFactors: event.riskFactors || [],
    requestedAt: new Date().toISOString(),
    timeoutAt: event.timeout ? addSeconds(new Date(), event.timeout) : undefined,
  };

  addPendingApproval(approval);

  // High-risk operations get modal dialog
  if (approval.riskLevel === 'high' || approval.riskLevel === 'critical') {
    setDialogApproval(approval);
  }
};
```

### Timeout Handling

```typescript
// Countdown timer for approval timeout
const ApprovalTimeout: FC<{ timeoutAt: string }> = ({ timeoutAt }) => {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      const diff = new Date(timeoutAt).getTime() - Date.now();
      setRemaining(Math.max(0, Math.floor(diff / 1000)));
    }, 1000);

    return () => clearInterval(interval);
  }, [timeoutAt]);

  if (remaining <= 0) return <span className="text-red-500">Expired</span>;
  return <span className="text-yellow-500">{remaining}s remaining</span>;
};
```

---

## Dependencies

### From Previous Sprints
- Sprint 62: InlineApproval component, StatusBar
- Sprint 63: AG-UI event handling, useUnifiedChat

### External
- Backend approval API endpoints
- Risk assessment from HybridOrchestrator
- AG-UI TOOL_CALL events with approval metadata

---

## Definition of Done

- [ ] All 4 stories completed and tested
- [ ] Low/medium risk shows inline approval
- [ ] High/critical risk shows dialog
- [ ] Approval API calls succeed
- [ ] Risk indicator updates in real-time
- [ ] Timeout handling works correctly
- [ ] Accessible to keyboard users

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API latency affecting UX | Medium | Optimistic updates, loading states |
| Missed approval timeout | High | Clear visual countdown, auto-reject option |
| Dialog blocking other actions | Low | Non-modal for lower risks |

---

## Sprint Velocity Reference

Based on previous sprints: ~8-10 pts/day
Expected completion: 3-4 days for 29 pts (enhanced with Risk Detail and Mode Switch Confirmation)
