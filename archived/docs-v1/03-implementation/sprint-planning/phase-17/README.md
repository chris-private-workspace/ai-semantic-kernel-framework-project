# Phase 17: Agentic Chat Enhancement

## Overview

Phase 17 focuses on enhancing the Agentic Chat interface with **security, persistence, user experience, and platform integration**:

1. **Sandbox Isolation** - Per-User sandbox, Agent operates only on user's uploaded files and sandbox directories
2. **Chat History** - Complete conversation persistence and recovery
3. **Claude Code-style UI** - Hierarchical progress display with detailed execution feedback
4. **Dashboard Integration** - Integrate UnifiedChat into main platform layout

**Target**: Production-grade agentic conversation interface with enterprise security standards

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | ✅ Completed |
| **Duration** | 2 sprints |
| **Total Story Points** | 42 pts |
| **Completion Date** | 2026-01-08 |

## Architecture Decisions

| Decision | Choice | Description |
|----------|--------|-------------|
| **Sandbox Scope** | Per-User | `data/{type}/{user_id}/`, using Guest UUID before auth |
| **Authentication** | Phase 18 | Phase 17 uses Guest User ID (localStorage) |
| **Page Layout** | Dashboard Integration | UnifiedChat joins Sidebar + Header |

### Guest User ID Design

Phase 17 uses temporary Guest User ID (transition solution):

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
```

Phase 18 implements: Guest UUID → Real User ID automatic migration

## Key Features

### 1. Sandbox Security Architecture

```
data/
├── uploads/{user_id}/      # User uploaded files
├── sandbox/{user_id}/      # Code execution sandbox
├── outputs/{user_id}/      # Agent generated outputs
└── temp/                   # Temporary files (no user isolation)
```

**Security Controls**:
- Allowlist-based path validation
- Blocked patterns for source code (`backend/`, `frontend/`, `*.py`, `*.tsx`)
- User-scoped directory isolation
- File upload API with type validation

### 2. Chat History Persistence

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | PostgreSQL | Source of truth |
| **Backend** | Redis | 5-min TTL cache |
| **Frontend** | localStorage | Quick access cache |

**Data Flow**:
```
User → Frontend → API → ThreadManager → PostgreSQL/Redis
      ↑                                      ↓
      └── loadHistory() ← GET /threads/{id}/history
```

### 3. Claude Code-style Progress UI

```
Step 1/5: Process documents (20%)
  ✓ Load files
  ◉ Parse content (45%)
  ○ Analyze
```

**Features**:
- Hierarchical step progress
- Sub-step tracking with status icons
- Real-time progress percentage
- Parallel operation visualization

### 4. Dashboard Integration

UnifiedChat integrated into the main Dashboard layout:
- Added to AppLayout with Sidebar + Header
- "AI 助手" navigation item in Sidebar
- Responsive layout within container
- Preserves ChatHeader as page-level header

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Dashboard Layout (AppLayout)                     │
├───────────┬─────────────────────────────────────────────────────────┤
│           │                   Unified Chat UI                        │
│  Sidebar  ├─────────────────────────────────────────────────────────┤
│           │  ┌─ Chat History ──────────────────────────────────────┐│
│  - Dash   │  │ loadHistory() → GET /threads/{id}/history           ││
│  - Chat ← │  │ Backend (PostgreSQL) = Source of Truth               ││
│  - Work   │  └─────────────────────────────────────────────────────┘│
│  - Agent  │                                                          │
│  - ...    │  ┌─ Step Progress (Claude Code-style) ─────────────────┐│
│           │  │ CUSTOM event: step_progress                          ││
│           │  │ ├── step_id, step_name, current, total, progress    ││
│           │  │ └── substeps: [{name, status, progress}]            ││
│           │  └─────────────────────────────────────────────────────┘│
│           │                                                          │
│           │  ┌─ Sandbox Isolation (Per-User) ──────────────────────┐│
│           │  │ SandboxHook → allowed_paths → data/{type}/{user_id}/││
│           │  │            → blocked_patterns → backend/, frontend/ ││
│           │  └─────────────────────────────────────────────────────┘│
└───────────┴─────────────────────────────────────────────────────────┘
```

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 68** | Sandbox Isolation + Chat History | 21 pts | ✅ Completed | [Plan](sprint-68-plan.md) / [Checklist](sprint-68-checklist.md) |
| **Sprint 69** | Claude Code UI + Dashboard Integration | 21 pts | ✅ Completed | [Plan](sprint-69-plan.md) / [Checklist](sprint-69-checklist.md) |
| **Total** | | **42 pts** | ✅ | |

### Sprint 68 Stories (Completed)

| Story | Feature | Points | Status |
|-------|---------|--------|--------|
| S68-1 | Sandbox Directory Structure | 3 pts | ✅ |
| S68-2 | SandboxHook Path Validation | 5 pts | ✅ |
| S68-3 | File Upload API | 5 pts | ✅ |
| S68-4 | History API Implementation | 5 pts | ✅ |
| S68-5 | Frontend History Integration | 3 pts | ✅ |
| **Total** | | **21 pts** | ✅ |

### Sprint 69 Stories (Completed)

| Story | Feature | Points | Status |
|-------|---------|--------|--------|
| S69-1 | step_progress Backend Event | 5 pts | ✅ |
| S69-2 | StepProgress Sub-step Component | 5 pts | ✅ |
| S69-3 | Progress Event Frontend Integration | 3 pts | ✅ |
| S69-4 | Dashboard Layout Integration | 5 pts | ✅ |
| S69-5 | Guest User ID Implementation | 3 pts | ✅ |
| **Total** | | **21 pts** | ✅ |

## Component Structure

```
backend/src/
├── core/
│   └── sandbox_config.py           # ✅ Sandbox directory config
│
├── integrations/
│   ├── claude_sdk/
│   │   └── hooks/
│   │       └── sandbox.py          # ✅ Sandbox path validation
│   └── ag_ui/
│       ├── routes.py               # ✅ History API implementation
│       └── events/
│           └── progress.py         # ✅ step_progress event
│
├── api/v1/ag_ui/
│   ├── upload.py                   # ✅ File upload API
│   └── dependencies.py             # ✅ get_user_id dependency

frontend/src/
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx             # ✅ Add Chat navigation
│   └── unified-chat/
│       └── StepProgressEnhanced.tsx # ✅ Sub-step component
│
├── pages/
│   └── UnifiedChat.tsx             # ✅ Layout adaptation
│
├── hooks/
│   └── useUnifiedChat.ts           # ✅ loadHistory() + history API
│
├── utils/
│   └── guestUser.ts                # ✅ Guest User ID
│
├── App.tsx                         # ✅ Route integration
│
└── types/
    └── unified-chat.ts             # ✅ StepProgress types
```

## Technology Stack

- **Backend**: FastAPI + SQLAlchemy + Redis
- **Frontend**: React 18 + TypeScript + Zustand
- **Protocol**: AG-UI SSE + CUSTOM events
- **Storage**: PostgreSQL (persistent) + Redis (cache)
- **Layout**: AppLayout (Sidebar + Header)

## Dependencies

### Prerequisites (from previous phases)
- Phase 15: AG-UI Protocol Integration (ThreadManager, SSE events)
- Phase 16: Unified Agentic Chat Interface (base components)

### New Dependencies
- File upload handling (python-multipart)
- Path validation utilities

## Success Criteria

1. **Security Requirements** ✅
   - [x] Agent cannot access `backend/` or `frontend/` directories
   - [x] Agent can only read/write within user's sandbox directories
   - [x] File uploads are validated and user-scoped
   - [x] Different Guest Users have isolated sandboxes

2. **Persistence Requirements** ✅
   - [x] Chat history survives page refresh
   - [x] History loads from backend API on page load
   - [x] Same Guest User can recover conversations

3. **User Experience** ✅
   - [x] Step progress shows hierarchical sub-steps
   - [x] Real-time progress percentage updates
   - [x] Visual feedback matches Claude Code style

4. **Dashboard Integration** ✅
   - [x] Chat page has Sidebar + Header
   - [x] Navigation visible in Sidebar
   - [x] Layout has no overflow or scrolling issues

## Related Documentation

- [Phase 15: AG-UI Protocol Integration](../phase-15/README.md)
- [Phase 16: Unified Agentic Chat Interface](../phase-16/README.md)
- [Phase 18: Authentication System](../phase-18/README.md)
- [AG-UI API Reference](../../../api/ag-ui-api-reference.md)

---

**Phase Status**: ✅ Completed
**Created**: 2026-01-08
**Completed**: 2026-01-08
**Duration**: 2 sprints
**Total Story Points**: 42 pts
