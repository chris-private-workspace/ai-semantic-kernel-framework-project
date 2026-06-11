# Sprint 162 Checklist: Management API + Hot Reload

## Pydantic Schemas
- [x] `api/v1/experts/schemas.py` — ExpertResponse model
- [x] `api/v1/experts/schemas.py` — ExpertListResponse model
- [x] `api/v1/experts/schemas.py` — ReloadResponse model

## API Routes
- [x] `api/v1/experts/routes.py` — GET /experts/ list all
- [x] `api/v1/experts/routes.py` — GET /experts/?domain= filter
- [x] `api/v1/experts/routes.py` — GET /experts/{name} detail
- [x] `api/v1/experts/routes.py` — POST /experts/reload hot-reload
- [x] `api/v1/experts/__init__.py` — export router

## Router Registration
- [x] `api/v1/__init__.py` — register experts router

## Unit Tests
- [x] `test_routes.py` — test_list_experts
- [x] `test_routes.py` — test_list_experts_by_domain
- [x] `test_routes.py` — test_get_expert_by_name
- [x] `test_routes.py` — test_get_expert_not_found
- [x] `test_routes.py` — test_reload_experts

## Verification
- [x] All existing tests still pass
- [x] New API tests pass
- [x] curl /api/v1/experts/ returns JSON
