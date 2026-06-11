# Sprint 158 Checklist: Expert Definition Format + Registry Core

## Expert Definitions (6 YAML files)
- [x] `definitions/network_expert.yaml` — migrated from worker_roles
- [x] `definitions/database_expert.yaml` — migrated from worker_roles
- [x] `definitions/application_expert.yaml` — migrated from worker_roles
- [x] `definitions/security_expert.yaml` — migrated from worker_roles
- [x] `definitions/cloud_expert.yaml` — NEW domain
- [x] `definitions/general.yaml` — fallback expert

## Registry Implementation
- [x] `experts/exceptions.py` — ExpertDefinitionError, ExpertNotFoundError, ExpertSchemaValidationError
- [x] `experts/registry.py` — AgentExpertDefinition dataclass
- [x] `experts/registry.py` — AgentExpertRegistry.load()
- [x] `experts/registry.py` — AgentExpertRegistry.reload()
- [x] `experts/registry.py` — AgentExpertRegistry.get() + get_or_fallback()
- [x] `experts/registry.py` — AgentExpertRegistry.list_names() + list_all() + list_by_domain()
- [x] `experts/registry.py` — _validate() schema validation
- [x] `experts/registry.py` — _load_worker_role_fallback() backward compat
- [x] `experts/registry.py` — get_registry() singleton factory
- [x] `experts/__init__.py` — public exports

## Unit Tests
- [x] `test_registry.py` — test_load_builtin_definitions
- [x] `test_registry.py` — test_get_returns_correct_expert
- [x] `test_registry.py` — test_get_unknown_falls_back_to_worker_role
- [x] `test_registry.py` — test_get_completely_unknown_falls_back_to_general
- [x] `test_registry.py` — test_reload_hot_reloads
- [x] `test_registry.py` — test_validate_rejects_missing_fields
- [x] `test_registry.py` — test_list_by_domain
- [x] `test_registry.py` — test_disabled_expert_not_loaded

## Verification
- [x] All 6 YAMLs load with zero errors
- [x] get("network_expert") returns correct definition
- [x] get("nonexistent") falls back gracefully
- [x] No modifications to worker_roles.py or any executor
- [x] Tests pass: `pytest tests/unit/integrations/orchestration/experts/`
