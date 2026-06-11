# Sprint 158 Plan - U6: Dynamic Agent Count + LLMCallPool

## Phase 47: Agent Team V4 - P3 Upgrades

### Sprint Goal
Make agent count dynamic (2-8 based on task complexity), expand role library, and integrate LLMCallPool for rate-limited concurrent LLM access.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/integrations/poc/agent_work_loop.py` | MODIFY | LLMCallPool integration, configurable ThreadPoolExecutor |
| `backend/src/api/v1/poc/agent_team_poc.py` | MODIFY | 5-8 agent roles, max_agents config |
| `backend/src/integrations/poc/team_tools.py` | MODIFY | Dynamic agent count in TEAM_LEAD_PROMPT |

## Acceptance Criteria

- [ ] TeamLead creates 2-8 sub-tasks based on complexity
- [ ] Agent role library has 5+ roles
- [ ] LLMCallPool controls concurrent LLM access
- [ ] ThreadPoolExecutor sized to agent count
- [ ] Environment variable TEAM_MAX_AGENTS configurable
