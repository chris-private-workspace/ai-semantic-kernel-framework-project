# Sprint 166 Checklist — SubagentExecutor Dynamic Agent Count

**Sprint Plan**: [sprint-166-plan.md](sprint-166-plan.md)

---

## Implementation

- [x] Change 1: TaskDecomposer `complexity_hint` param + prompt update + MAX_SUBTASKS cap
- [x] Change 2: DispatchRequest `metadata` field (already existed with risk_level + intent_summary)
- [x] Change 3: chat_routes.py fill metadata from pipeline context (already populated)
- [x] Change 4: SubagentExecutor `_infer_complexity()` + pass hint
- [x] Change 5: step6_llm_route.py subagent description update
- [x] Change 6: worker_executor.py Expert Registry bridge import (already done in Sprint 159)

## Testing

- [x] Unit test: `complexity_hint` parameter variations (3 tests)
- [x] Unit test: MAX_SUBTASKS cap enforcement (2 tests)
- [x] Unit test: `_infer_complexity()` logic (8 tests)
- [x] Regression: existing TaskDecomposer tests pass (22/22)
- [x] Regression: existing SubagentExecutor tests pass (no pre-existing failures)

## Verification

- [ ] Simple query → 1-2 agents
- [ ] Complex incident → 4-8 agents
- [ ] TeamExecutor unchanged
- [ ] Pipeline 8-step progress normal
- [ ] Route Decision badge correct
