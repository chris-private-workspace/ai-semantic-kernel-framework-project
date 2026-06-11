# Sprint 157 Plan - U5: Error Recovery (Retry + Task Reassignment)

## Phase 46: Agent Team V4 - P2 Upgrades

### Sprint Goal
Add retry with exponential backoff for transient LLM errors and task reassignment when an agent fails.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/integrations/poc/agent_work_loop.py` | MODIFY | _execute_agent_turn_with_retry + task reassignment |
| `backend/src/integrations/poc/shared_task_list.py` | MODIFY | reassign_task() + retry_count tracking |

## Acceptance Criteria

- [ ] Transient errors (timeout, 429, 503) → retry up to 2 times with backoff
- [ ] Fatal errors (401, 403) → fail immediately, no retry
- [ ] Failed task → reset to PENDING for other agents to claim
- [ ] Max 2 retries per task across all agents
- [ ] SSE events: agent_retry, task_reassigned
