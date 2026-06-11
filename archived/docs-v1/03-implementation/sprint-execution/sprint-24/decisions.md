# Sprint 24 Decisions: Planning & Multi-turn 整合

## Decision Log

### 2025-12-06

#### Decision 1: Planning 模組架構

**問題**: 如何整合 Phase 2 的規劃功能與官方 Agent Framework？

**選項**:
1. 完全使用官方 MagenticBuilder，放棄擴展功能
2. 創建 PlanningAdapter 包裝官方 API，保留擴展功能
3. 維持現狀，不遷移

**決策**: 選項 2 - 創建 PlanningAdapter

**理由**:
- 官方 `MagenticBuilder` 是規劃核心
- Phase 2 的 TaskDecomposer 和 DecisionEngine 沒有官方對應
- 這些擴展功能對企業用戶有價值

---

#### Decision 2: Multi-turn 狀態管理

**問題**: 如何管理多輪對話狀態？

**選項**:
1. 繼續使用自行實現的 SessionManager
2. 使用官方 Checkpoint API
3. 混合方案

**決策**: 選項 3 - 混合方案

**理由**:
- 使用官方 `CheckpointStorage` 接口進行狀態持久化
- 保留 SessionManager 的業務邏輯
- 實現 `RedisCheckpointStorage` 支持 Redis 存儲

---

## Architecture Decisions

### PlanningAdapter 架構

```
PlanningAdapter
├── _magentic_builder: MagenticBuilder  # 官方 API
├── _task_decomposer: TaskDecomposer    # Phase 2 擴展
├── _decision_engine: DecisionEngine    # Phase 2 擴展
└── Methods:
    ├── with_task_decomposition()
    ├── with_decision_engine()
    ├── build() → Workflow
    └── run() → Result
```

### MultiTurnAdapter 架構

```
MultiTurnAdapter
├── _checkpoint_storage: CheckpointStorage  # 官方接口
├── _session_manager: SessionManager        # Phase 2 業務邏輯
└── Methods:
    ├── add_turn()
    ├── get_history()
    └── clear_session()
```

---

## Open Questions

1. TaskDecomposer 的分解策略是否需要與官方 API 整合？
2. DecisionEngine 的規則系統是否需要持久化？
3. 是否需要支持多種 CheckpointStorage 實現？

---

**Last Updated**: 2025-12-06
