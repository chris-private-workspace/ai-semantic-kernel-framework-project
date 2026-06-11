# Sprint 160 Checklist: Domain-Specific Tool Schemas

## Domain Tools
- [x] `experts/domain_tools.py` — DOMAIN_TOOLS mapping (6 domains)
- [x] `experts/domain_tools.py` — TEAM_TOOLS shared list
- [x] `experts/domain_tools.py` — ALL_KNOWN_TOOLS aggregated set
- [x] `experts/domain_tools.py` — resolve_tools() with *, @domain, explicit
- [x] `experts/domain_tools.py` — get_domain_tools() accessor

## Tool Validator
- [x] `experts/tool_validator.py` — validate_expert_tools() function
- [x] `experts/tool_validator.py` — warns on unknown tools (no blocking)

## Registry Integration
- [x] `experts/registry.py` — call resolve_tools() in _load_one()
- [x] `experts/registry.py` — call validate_expert_tools() in load()
- [x] `experts/__init__.py` — export new functions

## Unit Tests
- [x] `test_domain_tools.py` — test_resolve_tools_explicit
- [x] `test_domain_tools.py` — test_resolve_tools_wildcard
- [x] `test_domain_tools.py` — test_resolve_tools_domain_ref
- [x] `test_domain_tools.py` — test_resolve_tools_mixed
- [x] `test_domain_tools.py` — test_validate_tools_valid
- [x] `test_domain_tools.py` — test_validate_tools_warns_unknown
- [x] `test_domain_tools.py` — test_domain_tools_all_domains_defined

## Verification
- [x] All existing tests still pass
- [x] New tests pass
- [x] YAML expert tools resolve correctly
