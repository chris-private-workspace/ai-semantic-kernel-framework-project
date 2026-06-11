# Sprint 165 Checklist: Expert Selection in Orchestrator Chat

## Backend SSE
- [x] `dispatch/executors/team.py` — emit EXPERT_ROSTER_PREVIEW after decomposition
- [x] `dispatch/executors/pipeline_emitter_bridge.py` — forward EXPERT_ROSTER_PREVIEW

## Frontend Store
- [x] `frontend/src/stores/expertSelectionStore.ts` — Zustand store

## Frontend Component
- [x] `frontend/src/components/unified-chat/agent-team/AgentRosterPanel.tsx` — roster preview UI

## Integration
- [x] `frontend/src/hooks/useOrchestratorPipeline.ts` — handle EXPERT_ROSTER_PREVIEW event
- [x] `frontend/src/pages/OrchestratorChat.tsx` — render AgentRosterPanel

## Verification
- [x] Team mode triggers EXPERT_ROSTER_PREVIEW SSE event
- [x] AgentRosterPanel shows expert list with DomainBadge
- [x] Toggle switches visual state
- [x] Panel collapses after execution starts
