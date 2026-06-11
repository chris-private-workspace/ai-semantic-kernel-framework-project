# Sprint 166 Plan — SubagentExecutor Dynamic Agent Count

**Phase**: 46 — Agent Expert Registry
**Sprint**: 166
**Story Points**: 5
**Branch**: `feature/phase-46-agent-expert-registry`

---

## User Stories

### US-166-1: Dynamic Agent Count Based on Task Complexity
**As** an IPA platform user,
**I want** the subagent mode to create a dynamic number of agents based on task complexity,
**So that** simple queries use fewer agents (lower cost) and complex incidents use more agents (better coverage).

### US-166-2: Complexity-Aware TaskDecomposer
**As** the orchestration pipeline,
**I want** TaskDecomposer to receive complexity hints from pipeline context,
**So that** decomposition produces an appropriate number of subtasks matching actual task requirements.

### US-166-3: Expert Registry Integration with SwarmWorkerExecutor
**As** a SwarmWorkerExecutor,
**I want** to use Expert Registry definitions when available,
**So that** agents have richer system prompts and capabilities from YAML expert definitions.

---

## Technical Specification

### Background
CC source study reveals subagent count is LLM-driven and dynamic (1-10+). Our TaskDecomposer uses a fixed "2-5" prompt guideline with no enforcement, producing similar agent counts regardless of task complexity.

### Changes

| # | File | Change |
|---|------|--------|
| 1 | `backend/src/integrations/swarm/task_decomposer.py` | Add `complexity_hint` param, update prompt, add MAX_SUBTASKS=10 cap |
| 2 | `backend/src/integrations/orchestration/dispatch/executors/subagent.py` | Add `_infer_complexity()`, pass hint to decomposer |
| 3 | `backend/src/integrations/orchestration/dispatch/models.py` | Add `metadata` field to DispatchRequest |
| 4 | `backend/src/api/v1/orchestration/chat_routes.py` | Fill DispatchRequest.metadata from pipeline context |
| 5 | `backend/src/integrations/orchestration/pipeline/steps/step6_llm_route.py` | Update subagent description in prompt |
| 6 | `backend/src/integrations/swarm/worker_executor.py` | Import from Expert Registry bridge with fallback |

### Acceptance Criteria
- [ ] Simple query ("Check DNS for example.com") → subagent creates 1-2 agents
- [ ] Complex incident ("Multiple services down across network, DB, app") → subagent creates 4-8 agents
- [ ] TaskDecomposer respects MAX_SUBTASKS=10 hard cap
- [ ] TeamExecutor unchanged (backward compatible, uses default "auto" hint)
- [ ] SwarmWorkerExecutor uses Expert Registry definitions when available
- [ ] All existing tests pass
