# Sprint 162: Management API + Hot Reload

## Phase 46: Agent Expert Registry
**Sprint**: 162
**Story Points**: 13
**Dependencies**: Sprint 161 (Frontend) ✅

---

## User Stories

### U1: Expert List API
**作為**前端，**我希望**有 REST API 能列出所有專家定義，**以便**在 UI 中顯示專家清單。

**Acceptance Criteria**:
- `GET /api/v1/experts/` 返回所有啟用的專家
- 支援 `?domain=network` 過濾
- 返回 name, display_name, domain, capabilities, tools, model, enabled

### U2: Expert Detail API
**作為**前端，**我希望**能查詢單一專家的完整定義，**以便**在 detail drawer 顯示。

**Acceptance Criteria**:
- `GET /api/v1/experts/{name}` 返回完整專家定義
- 不存在的專家返回 404

### U3: Hot Reload API
**作為**管理員，**我希望**能觸發 registry 重新載入，**以便**不重啟服務就能套用 YAML 變更。

**Acceptance Criteria**:
- `POST /api/v1/experts/reload` 觸發 hot-reload
- 返回重新載入後的專家數量
- 不影響正在執行的 agent

---

## Technical Specification

### Files to Create

| File | Purpose |
|------|---------|
| `backend/src/api/v1/experts/__init__.py` | Router export |
| `backend/src/api/v1/experts/routes.py` | API endpoints |
| `backend/src/api/v1/experts/schemas.py` | Pydantic response models |
| `backend/tests/unit/api/v1/experts/__init__.py` | Test package |
| `backend/tests/unit/api/v1/experts/test_routes.py` | Route tests |

### Files to Modify

| File | Change |
|------|--------|
| `backend/src/api/v1/__init__.py` | Register experts router |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/experts/` | List all experts (optional `?domain=` filter) |
| GET | `/api/v1/experts/{name}` | Get expert by name |
| POST | `/api/v1/experts/reload` | Hot-reload all definitions |

### Pydantic Schemas

```python
class ExpertResponse(BaseModel):
    name: str
    display_name: str
    display_name_zh: str
    description: str
    domain: str
    capabilities: list[str]
    model: str | None
    max_iterations: int
    tools: list[str]
    enabled: bool
    metadata: dict[str, Any]

class ExpertListResponse(BaseModel):
    experts: list[ExpertResponse]
    total: int

class ReloadResponse(BaseModel):
    status: str
    experts_loaded: int
    expert_names: list[str]
```

---

## Test Plan

| Test | Description |
|------|-------------|
| `test_list_experts` | GET /experts/ returns all experts |
| `test_list_experts_by_domain` | GET /experts/?domain=network filters correctly |
| `test_get_expert_by_name` | GET /experts/network_expert returns correct data |
| `test_get_expert_not_found` | GET /experts/nonexistent returns 404 |
| `test_reload_experts` | POST /experts/reload returns updated count |
