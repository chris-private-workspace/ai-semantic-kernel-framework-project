# Sprint 159: TaskDecomposer + Executor Integration

## Phase 46: Agent Expert Registry
**Sprint**: 159
**Story Points**: 8
**Dependencies**: Sprint 158 (Registry Core) ✅

---

## User Stories

### U1: Registry-Backed Role Resolution
**作為**平台，**我希望** TaskDecomposer 和 WorkerExecutor 從 AgentExpertRegistry 取得專家定義，**以便**使用更豐富的 system prompt、capabilities 和 model 配置。

**Acceptance Criteria**:
- TaskDecomposer 使用 registry 的專家名稱列表（含 capabilities 描述）
- WorkerExecutor 從 registry 取得專家定義（含 fallback）
- 現有 worker_roles.py 完全不修改（backward compatible）
- 所有現有 swarm 功能不受影響

### U2: Enhanced Role Matching
**作為** TaskDecomposer，**我希望** LLM prompt 包含每個專家的 capabilities 和 description，**以便**更精準地將子任務分派給最適合的專家。

**Acceptance Criteria**:
- Decomposition prompt 包含專家 capabilities 資訊
- LLM 可以根據能力描述選擇最佳專家
- 無效角色仍 fallback 到 general

### U3: Per-Expert Model Selection
**作為** WorkerExecutor，**我希望**能使用專家定義中的 model 欄位，**以便**不同專家可以使用不同的 LLM 模型。

**Acceptance Criteria**:
- 專家有 model 定義時使用該 model
- model 為 null 時使用系統預設 model
- model 切換不影響現有 tool execution 流程

---

## Technical Specification

### Architecture: Adapter Pattern

```
TaskDecomposer ──import──→ experts.bridge.get_expert_role_names()
                           experts.bridge.get_expert_descriptions()
                                    ↓
                           AgentExpertRegistry (YAML definitions)
                                    ↓ fallback
                           worker_roles.py (legacy)

WorkerExecutor ──import──→ experts.bridge.get_expert_role()
                                    ↓
                           AgentExpertRegistry.get_or_fallback()
                                    ↓ returns
                           Dict compatible with existing _role_def usage
```

### Files to Create

| File | Purpose |
|------|---------|
| `backend/src/integrations/orchestration/experts/bridge.py` | Adapter functions compatible with worker_roles API |
| `backend/tests/unit/integrations/orchestration/experts/test_bridge.py` | Bridge adapter tests |

### Files to Modify

| File | Change |
|------|--------|
| `backend/src/integrations/swarm/task_decomposer.py` | Import from bridge instead of worker_roles; enhance prompt with capabilities |
| `backend/src/integrations/swarm/worker_executor.py` | Import from bridge instead of worker_roles; support per-expert model |

### Files NOT Modified

| File | Reason |
|------|--------|
| `worker_roles.py` | Preserved as fallback tier — never modify |
| `swarm_integration.py` | No role logic — orchestrates at higher level |

### Bridge API

```python
# experts/bridge.py

def get_expert_role(name: str) -> dict[str, Any]:
    """Drop-in replacement for worker_roles.get_role().
    Returns dict with: name, display_name, system_prompt, tools, model, capabilities.
    """

def get_expert_role_names() -> list[str]:
    """Drop-in replacement for worker_roles.get_role_names().
    Returns merged list: registry experts + worker_roles names.
    """

def get_expert_descriptions() -> str:
    """Returns formatted expert descriptions for LLM prompt injection.
    Each expert listed with domain, capabilities, and description.
    """
```

### Integration Points

1. **task_decomposer.py line 16**: `from .worker_roles import get_role_names` → `from ..orchestration.experts.bridge import get_expert_role_names, get_expert_descriptions`
2. **task_decomposer.py line 104**: `get_role_names()` → `get_expert_role_names()`
3. **task_decomposer.py prompt**: Inject `get_expert_descriptions()` for better matching
4. **worker_executor.py line 16**: `from .worker_roles import get_role` → `from ..orchestration.experts.bridge import get_expert_role`
5. **worker_executor.py line 73**: `get_role(task.role)` → `get_expert_role(task.role)`

---

## Test Plan

| Test | Description |
|------|-------------|
| `test_bridge_get_expert_role_returns_dict` | Returns dict compatible with executor |
| `test_bridge_get_expert_role_fallback` | Unknown names fallback to general |
| `test_bridge_get_expert_role_names_includes_all` | Returns all registry + worker_roles names |
| `test_bridge_get_expert_descriptions_format` | Returns formatted string with capabilities |
| `test_decomposer_uses_registry_roles` | TaskDecomposer prompt includes registry experts |
| `test_executor_uses_registry_role` | WorkerExecutor loads from registry |
| `test_executor_model_override` | Per-expert model selection works |

---

## Verification

```bash
cd backend && python -c "
from src.integrations.orchestration.experts.bridge import (
    get_expert_role, get_expert_role_names, get_expert_descriptions
)
print('Role names:', get_expert_role_names())
role = get_expert_role('network_expert')
print(f'Network role keys: {list(role.keys())}')
print(f'Has system_prompt: {bool(role.get(\"system_prompt\"))}')
print(f'Has tools: {bool(role.get(\"tools\"))}')
print('Expert descriptions (first 200 chars):')
print(get_expert_descriptions()[:200])
"
```
