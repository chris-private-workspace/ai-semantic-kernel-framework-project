# Phase 16: Unified Agentic Chat Interface

## Overview

Phase 16 focuses on building a **production-ready unified conversation window** that integrates all features from the MAF + Claude SDK hybrid architecture (Phase 13-14) and AG-UI Protocol (Phase 15) into a cohesive user experience.

**Target**: Enterprise-grade agentic chat interface with intelligent mode switching, risk-based approvals, and real-time state synchronization.

## Relationship with AG-UI Demo

| Component | Purpose | Status |
|-----------|---------|--------|
| **AG-UI Demo** (`/ag-ui-demo`) | Feature testing and development showcase | Preserved |
| **Unified Chat** (`/chat` or `/assistant`) | Production-ready unified interface | **New in Phase 16** |

The AG-UI Demo page serves as a testing ground and feature showcase, while the Unified Chat Interface provides a polished, user-friendly experience for production use.

## Key Features

### 1. Adaptive Layout
- **Chat Mode**: Full-width conversation area (similar to Claude AI Web)
- **Workflow Mode**: Side panel with step progress and tool tracking
- **Automatic Transition**: Layout adapts based on execution mode

### 2. Intelligent Mode Switching
- **Auto-detection**: IntentRouter determines optimal mode
- **Manual Override**: Users can force mode switching
- **Visual Indicator**: Clear mode status in header and status bar

### 3. Layered Approval System
- **Low/Medium Risk**: Inline approval within message flow
- **High/Critical Risk**: Modal dialog with detailed risk information
- **Risk Badge**: Color-coded risk level indicator

### 4. Advanced Information Display
- Token usage tracking (used/limit)
- Checkpoint status with restore capability
- Risk assessment details
- Execution time statistics

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─ Header ────────────────────────────────────────────────────────┐ │
│ │ IPA Assistant    [💬 Chat] [📋 Workflow]    🟢 Connected   [⚙️] │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Main Content ──────────────────────────────────────────────────┐ │
│ │  ┌─ Chat Area ───────────────┐  ┌─ Side Panel (Workflow) ────┐ │ │
│ │  │                           │  │ (Adaptive: Workflow only)   │ │ │
│ │  │  👤 User message          │  │                            │ │ │
│ │  │                           │  │ 📊 Step Progress           │ │ │
│ │  │  🤖 Assistant (streaming) │  │ Step 2/5 ████░░ 40%       │ │ │
│ │  │    └─ [Tool] ✅ 3.2s     │  │                            │ │ │
│ │  │    └─ [Tool] ⚠️ Pending  │  │ 🔧 Tool Call Tracker       │ │ │
│ │  │        [Approve][Reject]  │  │ ├─ search ✅ 1.2s          │ │ │
│ │  │                           │  │ ├─ analyze ✅ 2.1s         │ │ │
│ │  │                           │  │ └─ edit ⏳ Pending         │ │ │
│ │  └───────────────────────────┘  │                            │ │ │
│ │                                 │ 📍 Checkpoints             │ │ │
│ │                                 │ └─ cp-001 [Restore]        │ │ │
│ │                                 └────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Input Area ────────────────────────────────────────────────────┐ │
│ │ [📎] Type your message...                          [🎤] [Send] │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Status Bar ────────────────────────────────────────────────────┐ │
│ │ Mode: Chat │ Risk: Low 🟢 │ Tokens: 1.2K/4K │ Time: 3.5s │ ✓   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Structure

```
frontend/src/
├── pages/
│   └── UnifiedChat.tsx              # Main page component
│
├── components/unified-chat/
│   ├── ChatHeader.tsx               # Header with mode toggle
│   ├── ChatArea.tsx                 # Main conversation area
│   │   ├── MessageList.tsx          # Message container
│   │   ├── MessageBubble.tsx        # Individual message (reuse AG-UI)
│   │   ├── ToolCallCard.tsx         # Tool display (reuse AG-UI)
│   │   └── InlineApproval.tsx       # Low-risk inline approval
│   ├── WorkflowSidePanel.tsx        # Workflow mode side panel
│   │   ├── StepProgress.tsx         # Step progress indicator
│   │   ├── ToolCallTracker.tsx      # Tool execution timeline
│   │   └── CheckpointList.tsx       # Checkpoint management
│   ├── ChatInput.tsx                # Message input area
│   ├── StatusBar.tsx                # Bottom status bar
│   │   ├── ModeIndicator.tsx        # Current mode display
│   │   ├── RiskIndicator.tsx        # Risk level badge
│   │   ├── TokenUsage.tsx           # Token consumption
│   │   └── ExecutionTime.tsx        # Time tracking
│   └── ApprovalDialog.tsx           # High-risk approval modal
│
├── hooks/
│   ├── useUnifiedChat.ts            # Main chat orchestration
│   ├── useHybridMode.ts             # Mode detection/switching
│   ├── useApprovalFlow.ts           # Approval workflow logic
│   └── useExecutionMetrics.ts       # Metrics collection
│
└── types/
    └── unified-chat.ts              # Type definitions
```

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 62** | Core Architecture & Adaptive Layout | 30 pts | ✅ Complete | [Plan](sprint-62-plan.md) / [Checklist](sprint-62-checklist.md) |
| **Sprint 63** | Mode Switching & State Management | 30 pts | ✅ Complete | [Plan](sprint-63-plan.md) / [Checklist](sprint-63-checklist.md) |
| **Sprint 64** | Approval Flow & Risk Indicators | 29 pts | ✅ Complete | [Plan](sprint-64-plan.md) / [Checklist](sprint-64-checklist.md) |
| **Sprint 65** | Metrics, Checkpoints & Polish | 24 pts | ✅ Complete | [Plan](sprint-65-plan.md) / [Checklist](sprint-65-checklist.md) |
| **Sprint 66** | Tool Integration Bug Fix | 10 pts | ✅ Complete | [Plan](sprint-66-plan.md) / [Checklist](sprint-66-checklist.md) |
| **Sprint 67** | UI Component Integration | 8 pts | ✅ Complete | [Plan](sprint-67-plan.md) / [Checklist](sprint-67-checklist.md) |
| **Total** | | **131 pts** | ✅ **100%** | |

### Enhancement Summary (AG-UI Full Integration)

Phase 16 規劃已增強以完整整合 AG-UI 7 大功能和 Phase 13-14 組件：

| 增強項目 | 點數 | 說明 |
|----------|------|------|
| Sprint 63 增強 | +5 pts | STATE_SNAPSHOT/DELTA 處理、樂觀更新、模式切換原因顯示 |
| Sprint 64 增強 | +4 pts | RiskIndicator 詳情 Tooltip、ModeSwitchConfirmDialog |
| Sprint 65 增強 | +4 pts | CustomUIRenderer 整合 (Tool-based Generative UI) |
| **總增量** | **+13 pts** | AG-UI 功能覆蓋率: 71% → 100% |

## Technology Stack

- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS + Shadcn UI
- **State Management**: Zustand
- **Server State**: React Query
- **Real-time**: SSE (Server-Sent Events) via AG-UI Protocol
- **Icons**: Lucide React

## Dependencies

### Prerequisites (from previous phases)
- Phase 13-14: Hybrid MAF + Claude SDK Architecture
- Phase 15: AG-UI Protocol Integration

### Reusable Components
- `MessageBubble` from AG-UI Demo
- `ToolCallCard` from AG-UI Demo
- `RiskBadge` from AG-UI HITL
- SSE hooks from AG-UI integration

## Success Criteria

1. **Functional Requirements**
   - [x] Chat and Workflow modes work seamlessly
   - [x] Automatic mode detection with manual override
   - [x] Inline and modal approvals function correctly
   - [x] Real-time streaming responses

2. **Performance Requirements**
   - [x] First message response < 500ms
   - [x] Mode switch transition < 200ms
   - [x] Smooth streaming without jank

3. **User Experience**
   - [x] Intuitive mode indicators
   - [x] Clear risk level visualization
   - [x] Responsive on desktop (1024px+)

## Related Documentation

- [Phase 13: Hybrid Core Architecture](../phase-13/README.md)
- [Phase 14: Advanced Hybrid Features](../phase-14/README.md)
- [Phase 15: AG-UI Protocol Integration](../phase-15/README.md)
- [AG-UI API Reference](../../../api/ag-ui-api-reference.md)
- [AG-UI Integration Guide](../../../guides/ag-ui-integration-guide.md)

---

**Phase Status**: 🔄 In Progress (Sprint 66 Bug Fix)
**Start Date**: 2026-01-07
**Last Update**: 2026-01-07
**Duration**: 5 sprints
**Total Story Points**: 113/123 pts (92%)
