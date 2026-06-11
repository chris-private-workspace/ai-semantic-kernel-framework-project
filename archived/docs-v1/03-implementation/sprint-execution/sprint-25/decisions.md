# Sprint 25 Decisions

## Decision Log

### 2025-12-06

#### D25-1: 刪除策略

**問題**: 如何安全地刪除已遷移到適配器的代碼?

**決策**:
1. 先確認無其他代碼引用 (grep 搜索)
2. 運行所有測試確保無影響
3. 執行刪除
4. 重新運行測試驗證

**理由**: 確保刪除操作不會破壞現有功能

---

#### D25-2: 保留擴展功能

**問題**: 哪些自行實現的功能應該保留?

**決策**: 保留以下擴展功能:
- `task_decomposer.py` - 任務分解 (PlanningAdapter 引用)
- `decision_engine.py` - 決策引擎 (PlanningAdapter 引用)
- `context_propagation.py` - 上下文傳播 (NestedWorkflowAdapter 引用)
- `recursive_handler.py` - 遞歸處理 (NestedWorkflowAdapter 引用)
- `session_manager.py` - 會話管理 (MultiTurnAdapter 引用)

**理由**: 這些是官方 API 沒有提供但對業務有價值的擴展

---

## Pending Decisions

無

---

**Last Updated**: 2025-12-06
