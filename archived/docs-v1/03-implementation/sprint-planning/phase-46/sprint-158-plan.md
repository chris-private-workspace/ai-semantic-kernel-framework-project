# Sprint 158: Expert Definition Format + Registry Core

## Phase 46: Agent Expert Registry
**Sprint**: 158
**Story Points**: 13
**Dependencies**: None (standalone, additive only)

---

## User Stories

### U1: YAML Expert Definition
**作為**開發者，**我希望**能用 YAML 文件定義 Agent 專家，**以便**版本控制和快速修改。

**Acceptance Criteria**:
- YAML schema 包含: name, display_name, display_name_zh, description, domain, capabilities, model, max_iterations, system_prompt, tools, enabled, metadata
- 6 個內建專家定義（network, database, application, security, cloud, general）
- 專家定義從 `worker_roles.py` 遷移，保留完整 system prompt

### U2: AgentExpertRegistry
**作為**平台，**我希望** AgentExpertRegistry 自動載入 definitions/ 目錄，**以便**新增專家不需改程式碼。

**Acceptance Criteria**:
- `load()` 載入所有 `.yaml` 檔案
- `get(name)` 返回專家定義或 None
- `get_or_fallback(name)` 三層 fallback: YAML → worker_roles → general
- `list_names()`, `list_all()`, `list_by_domain()` 查詢方法
- `reload()` hot-reload 能力
- `get_registry()` singleton factory

### U3: Schema Validation
**作為**測試人員，**我希望** Registry 驗證 YAML schema，**以便**防止格式錯誤的定義被載入。

**Acceptance Criteria**:
- 缺少必填欄位時拋出 `ExpertSchemaValidationError`
- `enabled: false` 的專家不被載入
- 無效 domain 值被拒絕

---

## Technical Specification

### Files to Create

| File | Purpose |
|------|---------|
| `backend/src/integrations/orchestration/experts/__init__.py` | Package init |
| `backend/src/integrations/orchestration/experts/registry.py` | Core registry |
| `backend/src/integrations/orchestration/experts/exceptions.py` | Exceptions |
| `backend/src/integrations/orchestration/experts/definitions/*.yaml` | 6 experts |
| `backend/tests/unit/integrations/orchestration/experts/__init__.py` | Test package |
| `backend/tests/unit/integrations/orchestration/experts/test_registry.py` | Tests |

### Files to Modify
None — Sprint 158 is purely additive.

### Data Model

```python
@dataclass
class AgentExpertDefinition:
    name: str
    display_name: str
    display_name_zh: str
    description: str
    domain: str                # network|database|application|security|cloud|general|custom
    capabilities: list[str]
    model: str | None          # None = inherit default
    max_iterations: int        # default 5
    system_prompt: str
    tools: list[str]           # ["*"] = all tools
    enabled: bool
    metadata: dict[str, Any]
```

### Valid Domains
`network`, `database`, `application`, `security`, `cloud`, `general`, `custom`

---

## Test Plan

| Test | Description |
|------|-------------|
| `test_load_builtin_definitions` | All 6 YAMLs load without error |
| `test_get_returns_correct_expert` | Name lookup works |
| `test_get_unknown_falls_back_to_worker_role` | Fallback to worker_roles |
| `test_get_completely_unknown_falls_back_to_general` | Double fallback |
| `test_reload_hot_reloads` | reload() refreshes definitions |
| `test_validate_rejects_missing_fields` | Schema validation |
| `test_list_by_domain` | Domain filtering |
| `test_disabled_expert_not_loaded` | enabled: false skipped |

---

## Verification

```bash
cd backend && python -c "
from src.integrations.orchestration.experts.registry import get_registry
r = get_registry()
print(f'Loaded {len(r.list_names())} experts: {r.list_names()}')
e = r.get('network_expert')
print(f'Network: domain={e.domain}, model={e.model}')
print(f'Fallback: {r.get_or_fallback(\"unknown\").name}')
"
```
