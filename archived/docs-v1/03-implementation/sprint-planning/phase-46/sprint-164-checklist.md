# Sprint 164 Checklist: Agent Expert Management Page

## API Client
- [x] `frontend/src/api/endpoints/experts.ts` — API client functions
- [x] `frontend/src/hooks/useExperts.ts` — React Query hooks

## Pages
- [x] `frontend/src/pages/agent-experts/AgentExpertsPage.tsx` — list page
- [x] `frontend/src/pages/agent-experts/CreateAgentExpertPage.tsx` — 5-step form
- [x] `frontend/src/pages/agent-experts/EditAgentExpertPage.tsx` — edit form
- [x] `frontend/src/pages/agent-experts/AgentExpertDetailPage.tsx` — detail view

## Routing & Navigation
- [x] `frontend/src/App.tsx` — add 4 routes
- [x] `frontend/src/components/layout/Sidebar.tsx` — add nav entry (Users icon)

## Verification
- [x] TypeScript compiles without new errors
- [x] /agent-experts page renders expert list
- [x] Create form saves new expert
- [x] Edit form updates existing expert
- [x] Detail page shows full configuration
- [x] Built-in experts: delete disabled, edit shows warning
