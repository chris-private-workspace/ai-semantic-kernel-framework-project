# Sprint 21 Decisions: Handoff 完整遷移

## Decision Log

### 2025-12-06

#### DEC-21-001: Policy Mapping Strategy

**Context**: 需要將 Phase 2 的 HandoffPolicy 映射到官方 API

**Decision**: 使用適配器模式，創建 `HandoffPolicyAdapter` 靜態方法

**Rationale**:
- 官方 API 使用 `interaction_mode` 和 `termination_condition`
- Phase 2 使用 `HandoffPolicy` 枚舉 (IMMEDIATE, GRACEFUL, CONDITIONAL)
- 適配器可以無縫轉換，保持向後兼容

**Mapping**:
| Phase 2 Policy | Official API |
|----------------|--------------|
| IMMEDIATE | `interaction_mode="autonomous"` |
| GRACEFUL | `interaction_mode="human_in_loop"` |
| CONDITIONAL | `termination_condition=fn` |

---

## Architecture Decisions

### 保留 Phase 2 功能清單

1. **HandoffPolicy** - 3 種交接策略
2. **CapabilityMatcher** - 4 種匹配策略
3. **ContextTransfer** - 4 種傳遞策略
4. **HandoffTrigger** - 6 種觸發類型

### 遷移原則

1. API 層只使用適配器
2. 適配器內部調用官方 Builder
3. Phase 2 邏輯封裝為選擇器/配置函數
4. 保持 API 響應格式不變

---

**Last Updated**: 2025-12-06
