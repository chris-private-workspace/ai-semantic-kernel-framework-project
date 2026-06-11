# Sprint 163 Checklist: Agent Expert CRUD API + DB Persistence

## DB Model
- [x] `infrastructure/database/models/agent_expert.py` — AgentExpert model
- [x] `infrastructure/database/models/__init__.py` — add import

## Repository
- [x] `infrastructure/database/repositories/agent_expert.py` — CRUD + queries

## Seeder
- [x] `integrations/orchestration/experts/seeder.py` — YAML → DB seeder
- [x] `main.py` — call seeder on startup

## API Upgrade
- [x] `api/v1/experts/schemas.py` — ExpertCreateRequest, ExpertUpdateRequest, ExpertDetailResponse
- [x] `api/v1/experts/routes.py` — POST create endpoint
- [x] `api/v1/experts/routes.py` — PUT update endpoint
- [x] `api/v1/experts/routes.py` — DELETE endpoint (403 for built-in)
- [x] `api/v1/experts/routes.py` — upgrade GET endpoints to use DB

## Registry Hybrid
- [x] `experts/registry.py` — load_from_db() method

## Migration
- [x] Alembic migration for agent_experts table

## Tests
- [x] CRUD endpoint tests (create/update/delete)
- [x] Seeder idempotency test

## Verification
- [x] POST /experts/ creates new expert → 201
- [x] PUT /experts/{name} updates → version bumps
- [x] DELETE built-in → 403
- [x] DELETE custom → 200
- [x] Seeder plants 6 built-in experts
