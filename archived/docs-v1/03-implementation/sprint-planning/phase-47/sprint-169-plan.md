# Sprint 169 Plan — Orchestration Execution Log Persistence

**Phase**: 47 — Orchestrator Chat Improvements  
**Sprint**: 169  
**Branch**: `feature/orchestration-execution-log-persistence`  
**Worktree**: `ai-semantic-kernel-execution-log`  
**Date**: 2026-04-15  

---

## User Stories

### US-1: Pipeline Execution Audit Trail
- **As** an IPA Platform admin
- **I want** every pipeline execution persisted to PostgreSQL
- **So that** I can audit and review processing decisions after the fact

### US-2: Historical Execution Viewing
- **As** an IPA Platform user
- **I want** to see past pipeline processing records in the right panel
- **So that** switching between conversations preserves the processing context

---

## Technical Specifications

### Backend
1. **ORM Model** — `OrchestrationExecutionLog` with JSONB columns for routing_decision, risk_assessment, pipeline_steps, agent_events, dispatch_result
2. **Repository** — extends BaseRepository with `get_by_session`, `get_by_request_id`, `get_latest_for_session`
3. **Persistence Service** — non-blocking write via `asyncio.create_task()`, dedup by request_id, defensive serialization
4. **API Routes** — GET list, GET by id, GET latest by session
5. **Wiring** — `_persist_execution()` helper called at pipeline complete, HITL pause, dialog pause, and error

### Frontend
6. **API Types** — ExecutionLogSummary, ExecutionLogDetail, response wrappers
7. **History Hook** — `useOrchestratorHistory(sessionId)` with fetch/refetch

---

## File Changes

| File | Action |
|------|--------|
| `backend/.../models/orchestration_execution_log.py` | Create |
| `backend/.../repositories/orchestration_execution_log.py` | Create |
| `backend/.../pipeline/persistence.py` | Create |
| `backend/.../orchestration/execution_log_schemas.py` | Create |
| `backend/.../orchestration/execution_log_routes.py` | Create |
| `backend/.../models/__init__.py` | Modify |
| `backend/.../api/v1/__init__.py` | Modify |
| `backend/.../orchestration/chat_routes.py` | Modify |
| `frontend/.../endpoints/orchestration.ts` | Modify |
| `frontend/.../hooks/useOrchestratorHistory.ts` | Create |

---

## Acceptance Criteria

- [ ] Pipeline completion writes log to PostgreSQL
- [ ] Pipeline failure writes log with error field
- [ ] HITL/dialog pause writes log with paused status
- [ ] Dedup prevents double-writes (request_id unique index)
- [ ] GET /orchestration/executions returns paginated list
- [ ] GET /orchestration/executions/{id} returns detail
- [ ] GET /orchestration/executions/by-session/{sid}/latest returns most recent
- [ ] useOrchestratorHistory hook loads historical data
- [ ] SSE stream performance unaffected (non-blocking write)
