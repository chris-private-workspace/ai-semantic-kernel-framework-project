# Phase 13-23 Sprint Planning Summary

Structured summary of all planned features for Phases 13 through 23 of the IPA Platform project, extracted from each phase's `README.md`.

---

## Phase 13: Hybrid Core Architecture (混合核心架構)
- **Sprints**: Sprint 52, Sprint 53, Sprint 54
- **Goal**: Establish the hybrid core architecture merging MAF (Microsoft Agent Framework) and Claude Agent SDK into a true framework fusion rather than independent execution. The phase builds an Intent Router for intelligent mode detection, a Context Bridge for cross-framework state synchronization, and a Unified Execution Layer where Claude handles all tool execution regardless of originating framework.
- **Planned Features**:
  1. **Intent Router & Mode Detection** (Sprint 52) — Intelligent intent classification that determines whether to use Workflow Mode (MAF-led), Chat Mode (Claude-led), or Hybrid Mode (dynamic switching). Includes `ExecutionMode` enum, `IntentAnalysis` model with confidence scoring, complexity analysis, and multi-agent/persistence requirement detection. — `backend/src/integrations/hybrid/` (IntentRouter class)
  2. **Context Bridge & Sync** (Sprint 53) — Cross-framework context synchronization bridging MAF Checkpoint state (workflow state, agent state, checkpoints) with Claude Context (session history, tool calls). Supports bi-directional sync and context merging. — `backend/src/integrations/hybrid/` (ContextBridge class, MAFContext, ClaudeContext dataclasses)
  3. **HybridOrchestrator Refactor / Unified Execution Layer** (Sprint 54) — Refactor HybridOrchestrator into V2 integrating Intent Router and Context Bridge. All tool execution routed through Claude via UnifiedToolExecutor with hook-based pre/post processing (approval, audit). MAF workflow tool calls are proxied through Claude. — `backend/src/integrations/hybrid/` (UnifiedToolExecutor, HybridOrchestratorV2)
- **Planned Story Points**: 105 (35 + 35 + 35)
- **Key Architecture Decisions**:
  - Three execution modes: WORKFLOW_MODE, CHAT_MODE, HYBRID_MODE
  - All tool execution unified through Claude regardless of source framework
  - FrameworkSelector retained as auxiliary to Intent Router
  - SessionAgentBridge connected to Context Bridge for Session-Workflow state sync
  - CheckpointStorage extended to support ClaudeContext storage
  - Fallback to native executor if unified layer fails
- **Hotfix Record**: 2026-01-07 LLM connection fix — API route layer `core_routes.py` was not injecting `claude_executor` into `HybridOrchestratorV2`, causing Chat Mode to return simulated responses. Fixed by adding `backend/src/api/v1/hybrid/dependencies.py` with Claude dependency injection.

---

## Phase 14: Advanced Hybrid Features (進階混合功能)
- **Sprints**: Sprint 55, Sprint 56, Sprint 57
- **Goal**: Build the Risk Assessment Engine for intelligent risk-based approval decisions, a dynamic Mode Switcher for Workflow-Chat transitions, and a Unified Checkpoint system supporting cross-framework state recovery. These advanced features complete the hybrid architecture's operational capabilities.
- **Planned Features**:
  1. **Risk Assessment Engine** (Sprint 55) — Multi-dimensional risk scoring engine (0.0-1.0 scale) with four risk levels: LOW (auto-execute), MEDIUM (audit log), HIGH (require approval), CRITICAL (multi-approval). Evaluates operation type, target scope, parameters, user trust level, environment context, and historical anomaly patterns. — `backend/src/integrations/hybrid/` (RiskAssessmentEngine, RiskLevel enum, RiskAssessment model)
  2. **Mode Switcher & HITL** (Sprint 56) — Dynamic mode switching between Workflow and Chat modes triggered by complexity changes, user requests, failure recovery, or resource constraints. Includes state preservation via checkpoint snapshots before switching, context migration, and rollback capability on failed switches. — `backend/src/integrations/hybrid/` (ModeSwitcher, SwitchTrigger)
  3. **Unified Checkpoint & Polish** (Sprint 57) — Unified HybridCheckpoint structure (version 2) containing MAF state, Claude state, execution mode, mode transition history, risk profile, and sync metadata. Supports cross-framework restoration (full, partial, or post-mode-switch). Storage backends: Redis, PostgreSQL, Filesystem. — `backend/src/integrations/hybrid/` (HybridCheckpoint, UnifiedCheckpointStorage)
- **Planned Story Points**: 95 (30 + 35 + 30)
- **Key Architecture Decisions**:
  - Risk-based approval integrated with existing ApprovalHook
  - CheckpointStorage extended to UnifiedCheckpointStorage
  - Mode switching includes rollback mechanism
  - Checkpoint compression and expiration cleanup planned for storage management

---

## Phase 15: AG-UI Protocol Integration (AG-UI 協議整合)
- **Sprints**: Sprint 58, Sprint 59, Sprint 60, Sprint 61
- **Goal**: Integrate the AG-UI (Agent-User Interface) open protocol by CopilotKit for real-time SSE-based communication between AI agents and the frontend. Implement all 7 core AG-UI features: Agentic Chat, Backend Tool Rendering, Human-in-the-Loop, Agentic Generative UI, Tool-based Generative UI, Shared State, and Predictive State Updates.
- **Planned Features**:
  1. **AG-UI Core Infrastructure** (Sprint 58) — SSE endpoint (`POST /api/v1/ag-ui`), HybridEventBridge converting Phase 13-14 internal events to AG-UI standard events (RunStarted, TextMessage, ToolCall, StateSnapshot, StateDelta, Custom events). Thread management and state synchronization. — `backend/src/api/v1/ag_ui/` (AG-UI endpoint), `backend/src/integrations/ag_ui/` (HybridEventBridge, AGUIEventType, AGUIEvent)
  2. **AG-UI Basic Features (1-4)** (Sprint 59) — Agentic Chat (streaming conversation + tool calls), Backend Tool Rendering (backend executes tools, frontend renders results), Human-in-the-Loop (function approval requests via RiskAssessment), Agentic Generative UI (long-operation progress updates). Frontend: AGUIProvider React Context, AgentChat, ToolResultRenderer, ApprovalDialog, ProgressIndicator components. — `frontend/src/providers/AGUIProvider.tsx`, `frontend/src/components/ag-ui/`
  3. **AG-UI Advanced Features (5-7) & Integration** (Sprint 60) — Tool-based Generative UI (custom UI components from ToolRegistry), Shared State (bi-directional state sync via ContextBridge + UnifiedCheckpoint using StateSnapshot/StateDelta events), Predictive State Updates (optimistic updates via ContextBridge + Redis). Frontend: CustomUIRenderer, StateSyncManager, OptimisticStateHook. — `frontend/src/components/ag-ui/`
  4. **AG-UI Frontend Integration & E2E Testing** (Sprint 61) — Full frontend integration of all AG-UI components with end-to-end testing. — `frontend/src/`
- **Planned Story Points**: 123 (30 + 28 + 27 + 38)
- **Key Architecture Decisions**:
  - SSE (Server-Sent Events) chosen over WebSocket for AG-UI protocol compliance
  - Event bridge pattern: internal Hybrid events mapped to standard AG-UI event types
  - Existing Phase 13-14 components extended (stream_execute on orchestrator, state events on ContextBridge)
  - Fallback to WebSocket or Long Polling for browser compatibility

---

## Phase 16: Unified Agentic Chat Interface
- **Sprints**: Sprint 62, Sprint 63, Sprint 64, Sprint 65, Sprint 66, Sprint 67
- **Goal**: Build a production-ready unified conversation window integrating all MAF + Claude SDK hybrid features (Phase 13-14) and AG-UI Protocol (Phase 15) into a cohesive user experience. Enterprise-grade agentic chat with intelligent mode switching, risk-based approvals, and real-time state synchronization. The AG-UI Demo page is preserved separately as a testing ground.
- **Planned Features**:
  1. **Core Architecture & Adaptive Layout** (Sprint 62) — Chat Mode (full-width like Claude AI Web) vs Workflow Mode (side panel with step progress/tool tracking). Automatic layout transition based on execution mode. Main page component `UnifiedChat.tsx`. — `frontend/src/pages/UnifiedChat.tsx`, `frontend/src/components/unified-chat/`
  2. **Mode Switching & State Management** (Sprint 63) — IntentRouter auto-detection of optimal mode, manual override, visual mode indicator in header/status bar. STATE_SNAPSHOT/DELTA handling, optimistic updates, mode switch reason display. Enhanced +5 pts for AG-UI integration. — `frontend/src/hooks/useHybridMode.ts`, `frontend/src/components/unified-chat/ChatHeader.tsx`
  3. **Approval Flow & Risk Indicators** (Sprint 64) — Layered approval: inline for Low/Medium risk, modal dialog for High/Critical risk. Color-coded risk badges. RiskIndicator detail tooltip, ModeSwitchConfirmDialog. Enhanced +4 pts. — `frontend/src/components/unified-chat/ApprovalDialog.tsx`, `InlineApproval.tsx`, `frontend/src/hooks/useApprovalFlow.ts`
  4. **Metrics, Checkpoints & Polish** (Sprint 65) — Token usage tracking (used/limit), checkpoint status with restore capability, risk assessment details, execution time statistics. CustomUIRenderer integration for Tool-based Generative UI. Enhanced +4 pts. — `frontend/src/components/unified-chat/StatusBar.tsx` (ModeIndicator, RiskIndicator, TokenUsage, ExecutionTime), `frontend/src/hooks/useExecutionMetrics.ts`
  5. **Tool Integration Bug Fix** (Sprint 66) — Fix tool integration issues. 10 pts. — Various unified-chat components
  6. **UI Component Integration** (Sprint 67) — Final UI component integration polish. 8 pts. — Various unified-chat components
- **Planned Story Points**: 131 (30 + 30 + 29 + 24 + 10 + 8)
- **Key Architecture Decisions**:
  - Separate production interface (`/chat` or `/assistant`) from AG-UI Demo (`/ag-ui-demo`)
  - Reuse AG-UI Demo components (MessageBubble, ToolCallCard, RiskBadge, SSE hooks)
  - React 18 + TypeScript + Tailwind CSS + Shadcn UI + Zustand + React Query
  - Component structure: ChatHeader, ChatArea (MessageList, MessageBubble, ToolCallCard, InlineApproval), WorkflowSidePanel (StepProgress, ToolCallTracker, CheckpointList), ChatInput, StatusBar, ApprovalDialog

---

## Phase 17: Agentic Chat Enhancement
- **Sprints**: Sprint 68, Sprint 69
- **Goal**: Enhance the agentic chat interface with security (per-user sandbox isolation), persistence (complete chat history), Claude Code-style UI (hierarchical progress display), and dashboard integration. Production-grade conversation interface with enterprise security standards.
- **Planned Features**:
  1. **Sandbox Directory Structure** (Sprint 68, S68-1, 3 pts) — Create `data/uploads/{user_id}/`, `data/sandbox/{user_id}/`, `data/outputs/{user_id}/`, `data/temp/` directory structure. — `backend/src/core/sandbox_config.py`
  2. **SandboxHook Path Validation** (Sprint 68, S68-2, 5 pts) — Allowlist-based path validation, blocked patterns for source code (`backend/`, `frontend/`, `*.py`, `*.tsx`), user-scoped directory isolation. — `backend/src/integrations/claude_sdk/hooks/sandbox.py`
  3. **File Upload API** (Sprint 68, S68-3, 5 pts) — File upload endpoint with type validation, user-scoped storage. — `backend/src/api/v1/ag_ui/upload.py`, `backend/src/api/v1/ag_ui/dependencies.py`
  4. **History API Implementation** (Sprint 68, S68-4, 5 pts) — Backend chat history with PostgreSQL (source of truth) + Redis (5-min TTL cache). `GET /threads/{id}/history`. — `backend/src/integrations/ag_ui/routes.py`
  5. **Frontend History Integration** (Sprint 68, S68-5, 3 pts) — `loadHistory()` in frontend, localStorage quick access cache. — `frontend/src/hooks/useUnifiedChat.ts`
  6. **step_progress Backend Event** (Sprint 69, S69-1, 5 pts) — CUSTOM SSE event for step progress with step_id, step_name, current, total, progress, substeps. — `backend/src/integrations/ag_ui/events/progress.py`
  7. **StepProgress Sub-step Component** (Sprint 69, S69-2, 5 pts) — Hierarchical step progress display (Claude Code-style) with sub-step tracking and status icons. — `frontend/src/components/unified-chat/StepProgressEnhanced.tsx`
  8. **Progress Event Frontend Integration** (Sprint 69, S69-3, 3 pts) — Wire up step_progress events to frontend components. — `frontend/src/pages/UnifiedChat.tsx`
  9. **Dashboard Layout Integration** (Sprint 69, S69-4, 5 pts) — Integrate UnifiedChat into AppLayout with Sidebar + Header, add "AI 助手" navigation. — `frontend/src/pages/UnifiedChat.tsx`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/App.tsx`
  10. **Guest User ID Implementation** (Sprint 69, S69-5, 3 pts) — Temporary Guest User ID via localStorage (`guest-{UUID}`), transition solution until Phase 18 auth. — `frontend/src/utils/guestUser.ts`
- **Planned Story Points**: 42 (21 + 21)
- **Key Architecture Decisions**:
  - Per-User sandbox scope using `data/{type}/{user_id}/`
  - Authentication deferred to Phase 18; Phase 17 uses Guest UUID
  - UnifiedChat integrated into dashboard (Sidebar + Header) rather than standalone page
  - Three-tier history storage: PostgreSQL (persistent) + Redis (cache) + localStorage (quick access)

---

## Phase 18: Authentication System
- **Sprints**: Sprint 70, Sprint 71, Sprint 72
- **Goal**: Implement a complete authentication system upgrading Guest Users to real user management. Includes JWT authentication (login/logout/token refresh), user management (registration, password hashing), access control (roles, route protection), and Guest UUID to Real User ID data migration.
- **Planned Features**:
  1. **JWT Utilities** (Sprint 70, S70-1, 3 pts) — `create_access_token()`, `decode_token()` using python-jose. — `backend/src/core/security/jwt.py`
  2. **UserRepository + AuthService** (Sprint 70, S70-2, 5 pts) — UserRepository extending BaseRepository, AuthService for registration and authentication logic. — `backend/src/infrastructure/database/repositories/user.py`, `backend/src/domain/auth/service.py`, `backend/src/domain/auth/schemas.py`
  3. **Auth API Routes** (Sprint 70, S70-3, 3 pts) — `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`. — `backend/src/api/v1/auth/routes.py`
  4. **Auth Dependency Injection** (Sprint 70, S70-4, 2 pts) — `get_current_user()` dependency using OAuth2PasswordBearer + token validation. — `backend/src/api/v1/dependencies.py`
  5. **Auth Store (Zustand)** (Sprint 71, S71-1, 3 pts) — Frontend authentication state management. — `frontend/src/store/authStore.ts`
  6. **Login/Signup Pages** (Sprint 71, S71-2, 5 pts) — Login and signup form pages. — `frontend/src/pages/auth/LoginPage.tsx`, `frontend/src/pages/auth/SignupPage.tsx`
  7. **ProtectedRoute Component** (Sprint 71, S71-3, 3 pts) — Route protection redirecting unauthenticated users to /login. — `frontend/src/components/auth/ProtectedRoute.tsx`
  8. **API Client Token Interceptor** (Sprint 71, S71-4, 2 pts) — Automatic Bearer token injection, 401 response handling (logout + redirect). — `frontend/src/api/client.ts`
  9. **Session User Association** (Sprint 72, S72-1, 3 pts) — Link sessions to authenticated users, add `user_id` and `guest_user_id` to session model. — `backend/src/infrastructure/database/models/session.py`, `backend/src/infrastructure/database/models/user.py`
  10. **Guest Data Migration API** (Sprint 72, S72-2, 3 pts) — `POST /auth/migrate-guest` endpoint migrating sessions, uploads, sandbox data from guest to authenticated user. — `backend/src/api/v1/auth/migration.py`
  11. **Frontend Migration Flow** (Sprint 72, S72-3, 2 pts) — Automatic guest data migration on first login, clear Guest UUID after migration. — `frontend/src/utils/guestUser.ts` (migrateGuestData)
- **Planned Story Points**: 34 (13 + 13 + 8)
- **Key Architecture Decisions**:
  - Leverages existing User Model, API Client token support, Role field, and Repository pattern
  - JWT via python-jose, bcrypt via passlib for password hashing
  - Guest UUID -> Real User ID automatic migration on first login
  - No new frontend dependencies (uses existing React Router, Zustand)

---

## Phase 19: UI Enhancement - Sidebar + Chat History + Metrics
- **Sprints**: Sprint 73, Sprint 74
- **Goal**: Fix three UI issues: (1) make the sidebar collapsible for more screen space, (2) add a ChatGPT-style chat history panel for conversation management, and (3) fix token/time metrics display that was not updating during streaming.
- **Planned Features**:
  1. **Token/Time Metrics Fix** (Sprint 73, S73-1, 3 pts) — Fix time being hardcoded to 0 and token display depending on a `TOKEN_UPDATE` SSE event the backend never sends. Integrate `useExecutionMetrics` hook for real-time timer. — `frontend/src/pages/UnifiedChat.tsx`, `frontend/src/hooks/useExecutionMetrics.ts`
  2. **Sidebar Collapse** (Sprint 73, S73-2, 5 pts) — Add `isCollapsed` prop and toggle button to Sidebar, animated transition (300ms) between 256px and 64px widths, icons-only in collapsed state. — `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/AppLayout.tsx`
  3. **ChatHistoryPanel Component** (Sprint 74, S74-1, 5 pts) — Conversation history list panel (like ChatGPT) with "New Chat" button, thread selection, title generation from first message. — `frontend/src/components/unified-chat/ChatHistoryPanel.tsx`
  4. **useChatThreads Hook** (Sprint 74, S74-2, 3 pts) — Thread management hook for creating, listing, switching, and persisting chat threads. — `frontend/src/hooks/useChatThreads.ts`
  5. **UnifiedChat Layout Integration** (Sprint 74, S74-3, 5 pts) — Integrate ChatHistoryPanel into UnifiedChat page layout alongside ChatArea. History panel collapsible/expandable. — `frontend/src/pages/UnifiedChat.tsx`
- **Planned Story Points**: 21 (8 + 13)
- **Key Architecture Decisions**:
  - No new dependencies; uses existing React, Zustand, Tailwind
  - Thread persistence via localStorage (MVP approach)
  - Existing `useExecutionMetrics` hook reused for timer functionality

---

## Phase 20: File Attachment Support
- **Sprints**: Sprint 75, Sprint 76
- **Goal**: Add file attachment support to the AI assistant interface, enabling Claude AI/ChatGPT-style file upload for analysis and file download for Claude-generated outputs.
- **Planned Features**:
  1. **Backend File Upload API** (Sprint 75, S75-1, 5 pts) — `POST /api/v1/files/upload` endpoint with user-scoped storage in `data/uploads/{user_id}/`. Supports text (.txt, .md, .json, .csv up to 10MB), code (.py, .js, .ts, .java up to 10MB), PDF (up to 25MB), images (.png, .jpg, .gif, .webp up to 20MB). — `backend/src/api/v1/files/`
  2. **Frontend FileUpload Component** (Sprint 75, S75-2, 5 pts) — Click-to-select and drag-and-drop file upload with progress indicator. — `frontend/src/components/unified-chat/`
  3. **Attachment Preview Component** (Sprint 75, S75-3, 3 pts) — Preview thumbnails for images, file type icons for other files, remove attachment capability. — `frontend/src/components/unified-chat/`
  4. **ChatInput Integration** (Sprint 75, S75-4, 3 pts) — Integrate file upload into the chat input area with attachment button. — `frontend/src/components/unified-chat/ChatInput.tsx`
  5. **Claude SDK File Analysis Connection** (Sprint 75, S75-5, 2 pts) — Connect uploaded files to Claude SDK for analysis. — `backend/src/integrations/claude_sdk/`
  6. **Backend File Download API** (Sprint 76, S76-1, 4 pts) — `GET /api/v1/files/{id}/download`, `GET /api/v1/files/{id}` (metadata), `DELETE /api/v1/files/{id}`, `GET /api/v1/files` (list). Files stored in `data/outputs/{session_id}/`. — `backend/src/api/v1/files/`
  7. **FileMessage Component** (Sprint 76, S76-2, 5 pts) — Display Claude-generated files in conversation with icon, name, and download button. — `frontend/src/components/unified-chat/`
  8. **File Type Renderer** (Sprint 76, S76-3, 4 pts) — Image preview, code syntax highlighting preview for generated files. — `frontend/src/components/unified-chat/`
  9. **ChatArea Integration** (Sprint 76, S76-4, 3 pts) — Integrate file messages into the chat conversation area. — `frontend/src/components/unified-chat/ChatArea.tsx`
- **Planned Story Points**: 34 (18 + 16)
- **Key Architecture Decisions**:
  - Storage structure: `data/uploads/{user_id}/` for uploads, `data/outputs/{session_id}/` for generated files
  - No new frontend dependencies (native File API)
  - Backend uses already-installed `python-multipart`
  - Download types include .txt, .md, .json, .csv, .py, .js, .png, .svg, .xlsx

---

## Phase 21: Sandbox Security Architecture
- **Sprints**: Sprint 77, Sprint 78
- **Goal**: Establish process-isolated secure execution environment ensuring agents cannot access the main process's sensitive resources (environment variables, database connections, configuration). This is a P0 security infrastructure priority that must be completed before further feature development. Addresses the discovery (2026-01-12) that Claude Agent runs in the main process with shared memory space.
- **Planned Features**:
  1. **SandboxOrchestrator** (Sprint 77, S77-1, 13 pts) — Process scheduler and lifecycle manager. Creates/manages sandbox child processes per user. Delegates execution from API Bridge to isolated sandbox processes. — `backend/src/core/sandbox/orchestrator.py` (~200 lines)
  2. **SandboxWorker** (Sprint 77, S77-2, 8 pts) — Runs Claude Agent in isolated child process with restricted environment variables (only SANDBOX_USER_ID, SANDBOX_DIR, ANTHROPIC_API_KEY; no DB_*, REDIS_*, or sensitive config). Sandbox directory: `data/sandbox/{user_id}/` with uploads/, outputs/, workspace/ subdirectories. — `backend/src/core/sandbox/worker.py` (~250 lines), `backend/src/core/sandbox/worker_main.py` (~100 lines)
  3. **IPC Communication & Event Forwarding** (Sprint 78, S78-1, 7 pts) — stdin/stdout JSON-RPC 2.0 protocol for main process <-> sandbox process communication. Supports request/response and streaming events (SSE forwarding). — `backend/src/core/sandbox/ipc.py` (~150 lines)
  4. **Existing Code Adaptation** (Sprint 78, S78-2, 5 pts) — Adapt `api/v1/sessions/chat.py`, `api/v1/claude_sdk/routes.py`, `domain/sessions/bridge.py`, `domain/sessions/executor.py` to use SandboxOrchestrator instead of direct execution. — Various backend files (~150-200 lines of changes)
  5. **Security Testing & Verification** (Sprint 78, S78-3, 5 pts) — Path traversal attack testing, environment variable leak testing, process crash isolation testing, performance overhead verification (<200ms first startup). — Test files
- **Planned Story Points**: 38 (21 + 17)
- **Key Architecture Decisions**:
  - Process isolation via Python subprocess (standard library, no new dependencies)
  - JSON-RPC 2.0 over stdin/stdout for IPC
  - Restricted env: only ANTHROPIC_API_KEY passed to sandbox; DB, Redis, and other sensitive config excluded
  - Existing hooks and tools run inside sandbox process unchanged
  - No changes required to database layer, frontend, or workflow definitions
  - Process pool with pre-warming and reuse (>90% target reuse rate)
  - Rationale: Hook-based "logical isolation" is insufficient (can be bypassed via path traversal, symlinks, encoding tricks, race conditions)

---

## Phase 22: Claude Autonomous Capability & Learning System (Claude 自主能力與學習系統)
- **Sprints**: Sprint 79, Sprint 80
- **Goal**: Upgrade Claude from "Tool Executor" to "Autonomous Planner" with a four-phase planning engine (Analyze -> Plan -> Execute -> Verify), integrate mem0 long-term memory system for cross-session learning, and establish explainable decision audit trails. Enable Claude to autonomously plan complex IT incident handling steps.
- **Planned Features**:
  1. **Claude Autonomous Planning Engine** (Sprint 79, S79-1, 13 pts) — Four-phase engine: (1) Analysis via Extended Thinking with dynamic budget_tokens (4096-32000 based on complexity), (2) Autonomous decision tree generation, (3) Execution via MAF Workflow or Claude Tools, (4) Result verification and learning. API: `POST /api/v1/claude/autonomous/plan`, `GET /api/v1/claude/autonomous/{id}`, `POST /api/v1/claude/autonomous/{id}/execute`. — `backend/src/integrations/claude_sdk/` (autonomous planning module)
  2. **mem0 Long-term Memory Integration** (Sprint 79, S79-2, 10 pts) — Three-tier memory architecture: Layer 1 Working Memory (Redis, already exists), Layer 2 Session Memory (PostgreSQL, already exists), Layer 3 Long-term Memory (mem0 with local Qdrant, NEW). Unified memory manager. API: `POST /api/v1/memory/add`, `GET /api/v1/memory/search`, `GET /api/v1/memory/user/{user_id}`, `DELETE /api/v1/memory/{id}`. — `backend/src/integrations/memory/` (Mem0Client, UnifiedMemoryManager)
  3. **Few-shot Learning System** (Sprint 80, S80-1, 8 pts) — Extract examples from historical cases for few-shot prompting. — `backend/src/integrations/learning/`
  4. **Autonomous Decision Audit Trail** (Sprint 80, S80-2, 8 pts) — Complete, queryable audit records of Claude's autonomous decisions. API: `GET /api/v1/audit/decisions`, `GET /api/v1/audit/decisions/{id}`. — `backend/src/integrations/audit/`
  5. **Trial-and-Error Smart Fallback** (Sprint 80, S80-3, 6 pts) — Automatic fallback mechanism when execution fails, with retry and alternative strategy selection. — `backend/src/integrations/claude_sdk/`
  6. **Claude Session State Enhancement** (Sprint 80, S80-4, 5 pts) — Cross-session state persistence for Claude sessions. — `backend/src/integrations/claude_sdk/`
- **Planned Story Points**: 50 (23 + 27)
- **Key Architecture Decisions**:
  - mem0 with local Qdrant (cost control vs cloud service)
  - OpenAI text-embedding-3-small for vector embeddings
  - Dynamic Extended Thinking budget_tokens: simple=4096, moderate=8192, complex=16000, critical=32000
  - New dependencies: `mem0ai>=1.0.1`, `qdrant-client>=1.7.0`, `openai>=1.0.0`

---

## Phase 23: Multi-Agent Coordination & Proactive Patrol (多 Agent 協調與主動巡檢)
- **Sprints**: Sprint 81, Sprint 82
- **Goal**: Strengthen Claude's role in multi-agent collaboration by implementing the Agent-to-Agent (A2A) communication protocol with agent discovery and capability declaration, and establish a proactive patrol mode for preventive AI capabilities including scheduled inspections and intelligent correlation/root cause analysis.
- **Planned Features**:
  1. **Claude-led Multi-Agent Coordination** (Sprint 81, S81-1, 10 pts) — Claude orchestrates 3+ agents to complete complex tasks, coordinating task delegation, result aggregation, and conflict resolution. — `backend/src/integrations/a2a/`
  2. **A2A Communication Protocol Enhancement** (Sprint 81, S81-2, 8 pts) — Standardized A2A message protocol with `A2AMessage` model (message_id, from_agent, to_agent, type, payload, context, timestamp). Agent discovery and capability query. API: `POST /api/v1/a2a/message`, `GET /api/v1/a2a/agents`, `POST /api/v1/a2a/agents/register`, `POST /api/v1/a2a/agents/discover`. — `backend/src/integrations/a2a/`
  3. **Claude + MAF Deep Fusion** (Sprint 81, S81-3, 8 pts) — Deeper integration of Claude autonomous capabilities with MAF workflow patterns. — `backend/src/integrations/hybrid/`
  4. **Proactive Patrol Mode** (Sprint 82, S82-1, 8 pts) — Scheduled patrol/inspection system that proactively discovers and prevents problems. API: `POST /api/v1/patrol/trigger`, `GET /api/v1/patrol/reports`, `GET /api/v1/patrol/schedule`. — `backend/src/integrations/patrol/`
  5. **Intelligent Correlation & Root Cause Analysis** (Sprint 82, S82-2, 8 pts) — Cross-event correlation reasoning and root cause analysis. API: `POST /api/v1/correlation/analyze`, `POST /api/v1/rootcause/analyze`. — `backend/src/integrations/correlation/`, `backend/src/integrations/rootcause/`
- **Planned Story Points**: 42 (26 + 16)
- **Key Architecture Decisions**:
  - New dependencies: `schedule>=1.2.0`, `networkx>=3.0`, `apscheduler>=3.10.0`
  - A2A protocol standardized with typed message model
  - Patrol mode supports both manual triggers and scheduled execution
  - Root cause analysis accuracy target: >70%

---

## Cross-Phase Summary

| Phase | Name | Sprints | Story Points | Status |
|-------|------|---------|--------------|--------|
| 13 | Hybrid Core Architecture | 52-54 | 105 | Completed |
| 14 | Advanced Hybrid Features | 55-57 | 95 | Partially Completed (68%) |
| 15 | AG-UI Protocol Integration | 58-61 | 123 | Backend Complete, Frontend In Progress |
| 16 | Unified Agentic Chat Interface | 62-67 | 131 | Completed |
| 17 | Agentic Chat Enhancement | 68-69 | 42 | Completed |
| 18 | Authentication System | 70-72 | 34 | Completed |
| 19 | UI Enhancement | 73-74 | 21 | Completed |
| 20 | File Attachment Support | 75-76 | 34 | Completed |
| 21 | Sandbox Security Architecture | 77-78 | 38 | Planned |
| 22 | Claude Autonomous & Learning | 79-80 | 50 | Planned |
| 23 | Multi-Agent Coordination & Patrol | 81-82 | 42 | Planned |
| **Total** | | **52-82 (31 sprints)** | **715** | |

### Deferred / Out-of-Scope Items
- **Phase 14, Sprint 57** (Unified Checkpoint & Polish): Marked as "Planned" (not completed), while Sprints 55-56 were completed. Phase total at 68%.
- **Phase 17**: Authentication explicitly deferred to Phase 18; Phase 17 uses Guest User ID as transition solution.
- **Phase 21-23**: All marked as "Planned" status, not yet started at time of documentation.
