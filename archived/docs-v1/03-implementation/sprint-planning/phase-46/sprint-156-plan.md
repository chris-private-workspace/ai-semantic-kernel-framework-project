# Sprint 156 Plan - U4: Graceful Shutdown Protocol

## Phase 46: Agent Team V4 - P2 Upgrades

### Sprint Goal
Replace hard shutdown (shutdown_event.set()) with CC-like graceful shutdown protocol: SHUTDOWN_REQUEST → agent ACK → cleanup.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/integrations/poc/agent_work_loop.py` | MODIFY | Shutdown request/ACK protocol + cleanup |
| `frontend/src/hooks/useOrchestratorSSE.ts` | MODIFY | Handle shutdown events |
| `frontend/src/pages/AgentTeamTestPage.tsx` | MODIFY | Agent card shutdown status |

## Acceptance Criteria

- [ ] Agents receive SHUTDOWN_REQUEST via inbox
- [ ] Agents complete current LLM call before ACK
- [ ] 10s timeout → force kill unresponsive agents
- [ ] SSE shows shutdown_request/shutdown_ack events
- [ ] Agent cards show "Shutting down..." state
