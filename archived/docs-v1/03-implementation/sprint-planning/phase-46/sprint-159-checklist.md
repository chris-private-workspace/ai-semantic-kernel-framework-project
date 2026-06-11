# Sprint 159 Checklist: TaskDecomposer + Executor Integration

## Bridge Adapter
- [x] `experts/bridge.py` — get_expert_role() dict adapter
- [x] `experts/bridge.py` — get_expert_role_names() merged list
- [x] `experts/bridge.py` — get_expert_descriptions() formatted prompt text
- [x] `experts/__init__.py` — export bridge functions

## TaskDecomposer Integration
- [x] `task_decomposer.py` — import from bridge instead of worker_roles
- [x] `task_decomposer.py` — use get_expert_role_names() for role validation
- [x] `task_decomposer.py` — inject expert descriptions into LLM prompt

## WorkerExecutor Integration
- [x] `worker_executor.py` — import from bridge instead of worker_roles
- [x] `worker_executor.py` — use get_expert_role() for role lookup
- [x] `worker_executor.py` — support per-expert model selection (model key in role dict)

## Unit Tests
- [x] `test_bridge.py` — test_bridge_get_expert_role_returns_dict
- [x] `test_bridge.py` — test_bridge_get_expert_role_fallback
- [x] `test_bridge.py` — test_bridge_get_expert_role_names_includes_all
- [x] `test_bridge.py` — test_bridge_get_expert_descriptions_format
- [x] `test_bridge.py` — test_decomposer_uses_registry_roles (integration)
- [x] `test_bridge.py` — test_executor_uses_registry_role (integration)

## Verification
- [x] worker_roles.py NOT modified
- [x] swarm_integration.py NOT modified
- [x] Bridge functions return correct format
- [x] Existing pytest tests still pass (29/29)
- [x] New tests pass: `pytest tests/unit/integrations/orchestration/experts/`
