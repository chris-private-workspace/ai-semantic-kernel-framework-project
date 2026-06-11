# Sprint 24: Planning & Multi-turn 模組分析

## S24-1: 評估 Planning 模組 (5 pts)

### 分析日期: 2025-12-06

---

## 1. 模組概覽

### 1.1 Planning 模組 (domain/orchestration/planning/)

| 組件 | 文件 | 行數 | Sprint | 功能 |
|------|------|------|--------|------|
| `DynamicPlanner` | dynamic_planner.py | ~750 | S10-2 | 動態規劃引擎 |
| `TaskDecomposer` | task_decomposer.py | ~792 | S10-1 | 任務分解器 |
| `AutonomousDecisionEngine` | decision_engine.py | ~725 | S10-3 | 自主決策引擎 |
| `TrialAndErrorEngine` | trial_error.py | ~894 | S10-4 | 試錯學習引擎 |
| **總計** | | **~3,161** | | |

### 1.2 Multi-turn 模組 (domain/orchestration/multiturn/)

| 組件 | 文件 | 行數 | Sprint | 功能 |
|------|------|------|--------|------|
| `MultiTurnSessionManager` | session_manager.py | ~824 | S9-3 | 會話管理器 |
| `TurnTracker` | turn_tracker.py | ~457 | S9-3 | 輪次追蹤器 |
| `SessionContextManager` | context_manager.py | ~527 | S9-3 | 上下文管理器 |
| **總計** | | **~1,808** | | |

---

## 2. 組件詳細分析

### 2.1 DynamicPlanner

**功能**:
- 從目標創建執行計劃
- 監控執行進度
- 動態調整計劃
- 異常處理和重新規劃

**官方 API 對應**: `MagenticBuilder`

**決策**: 🔄 **遷移到 PlanningAdapter**

**理由**:
- 官方 `MagenticBuilder` 提供規劃核心功能
- 保留進度監控和重新規劃邏輯作為擴展
- 通過適配器層整合

**整合方案**:
```python
class PlanningAdapter:
    def __init__(self):
        self._magentic_builder = MagenticBuilder()  # 官方 API
        self._task_decomposer = TaskDecomposer()    # 保留擴展
        self._decision_engine = DecisionEngine()    # 保留擴展
```

---

### 2.2 TaskDecomposer

**功能**:
- 4 種分解策略 (hierarchical, sequential, parallel, hybrid)
- 自動依賴檢測
- 執行順序計算
- 信心評分

**官方 API 對應**: 無直接對應

**決策**: ✅ **保留為擴展**

**理由**:
- 這是 Phase 2 的獨特功能
- 官方 API 沒有提供類似的任務分解能力
- 對企業用戶有重要價值

**整合方案**:
- 作為 `PlanningAdapter` 的可選擴展
- 通過 `with_task_decomposition()` 方法啟用

---

### 2.3 AutonomousDecisionEngine

**功能**:
- 多選項評估
- 風險評估
- 決策可解釋性
- 自定義決策規則

**官方 API 對應**: 無直接對應

**決策**: ✅ **保留為擴展**

**理由**:
- 企業場景需要決策追蹤和審計
- 官方 API 不提供決策解釋能力
- 風險評估對關鍵業務流程很重要

**整合方案**:
- 作為 `PlanningAdapter` 的可選擴展
- 通過 `with_decision_engine()` 方法啟用

---

### 2.4 TrialAndErrorEngine

**功能**:
- 自動重試和參數調整
- 錯誤模式識別
- 成功模式學習
- 學習洞察提取

**官方 API 對應**: 無直接對應

**決策**: ✅ **保留為擴展**

**理由**:
- 提供自適應執行能力
- 學習機制對長期運行很有價值
- 可以與官方重試機制互補

**整合方案**:
- 作為獨立的擴展模組
- 可以通過 `PlanningAdapter` 配置使用

---

### 2.5 MultiTurnSessionManager

**功能**:
- 會話生命週期管理 (create, start, pause, resume, close)
- 輪次管理
- 消息追蹤
- 事件處理

**官方 API 對應**: `CheckpointStorage`

**決策**: 🔄 **遷移到 MultiTurnAdapter**

**理由**:
- 官方 `CheckpointStorage` 提供狀態持久化
- 保留會話管理的業務邏輯
- 通過適配器層整合

**整合方案**:
```python
class MultiTurnAdapter:
    def __init__(self):
        self._checkpoint_storage = CheckpointStorage()  # 官方接口
        self._session_manager = SessionManager()        # 保留業務邏輯
```

---

### 2.6 TurnTracker & SessionContextManager

**功能**:
- 輪次追蹤
- 上下文作用域管理
- 狀態序列化

**官方 API 對應**: `Checkpoint`

**決策**: 🔄 **整合到 MultiTurnAdapter**

**理由**:
- 上下文狀態可以存儲為 Checkpoint
- 保留上下文作用域邏輯
- 簡化 API 設計

---

## 3. 官方 API 對應表

| Phase 2 功能 | 官方 API | 行為 | 說明 |
|-------------|----------|------|------|
| DynamicPlanner | `MagenticBuilder` | 遷移 | 使用官方規劃核心 |
| TaskDecomposer | 無 | 保留 | 獨特的擴展功能 |
| DecisionEngine | 無 | 保留 | 獨特的擴展功能 |
| TrialAndErrorEngine | 無 | 保留 | 獨特的擴展功能 |
| SessionManager | `CheckpointStorage` | 遷移 | 使用官方狀態管理 |
| TurnTracker | `Checkpoint` | 整合 | 狀態存儲到 Checkpoint |
| ContextManager | `Checkpoint` | 整合 | 上下文存儲到 Checkpoint |

---

## 4. 架構設計

### 4.1 PlanningAdapter 架構

```
PlanningAdapter
├── _magentic_builder: MagenticBuilder    # 官方 API - 規劃核心
├── _task_decomposer: TaskDecomposer      # Phase 2 擴展 - 任務分解
├── _decision_engine: DecisionEngine      # Phase 2 擴展 - 決策引擎
├── _trial_error_engine: TrialAndErrorEngine  # Phase 2 擴展 - 試錯學習
│
└── Methods:
    ├── with_task_decomposition()         # 啟用任務分解
    ├── with_decision_engine()            # 啟用決策引擎
    ├── with_trial_error()                # 啟用試錯學習
    ├── build() → Workflow                # 構建工作流
    └── run() → Result                    # 執行規劃
```

### 4.2 MultiTurnAdapter 架構

```
MultiTurnAdapter
├── _checkpoint_storage: CheckpointStorage  # 官方接口 - 狀態持久化
├── _session_manager: SessionManager        # Phase 2 業務邏輯
├── _context_manager: ContextManager        # Phase 2 上下文管理
│
└── Methods:
    ├── add_turn()                          # 添加對話輪次
    ├── get_history()                       # 獲取對話歷史
    ├── clear_session()                     # 清除會話
    ├── save_checkpoint()                   # 保存檢查點
    └── restore_checkpoint()                # 恢復檢查點
```

---

## 5. 遷移策略

### 5.1 Phase 1: 創建適配器

1. **PlanningAdapter** (S24-2)
   - 創建適配器類
   - 整合 MagenticBuilder
   - 添加擴展方法

2. **MultiTurnAdapter** (S24-3)
   - 創建適配器類
   - 整合 CheckpointStorage
   - 添加會話管理方法

### 5.2 Phase 2: 更新 API 路由

3. **API 路由更新** (S24-4)
   - 修改 Planning API
   - 修改 Multi-turn API
   - 保持向後兼容

### 5.3 Phase 3: 測試和文檔

4. **測試和文檔** (S24-5)
   - 單元測試
   - 集成測試
   - 遷移指南

---

## 6. 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 規劃功能不兼容 | 中 | 高 | 保留擴展機制，可以回退 |
| 會話狀態丟失 | 低 | 高 | 完整測試狀態恢復 |
| API 行為變更 | 中 | 中 | 保持接口兼容 |
| 性能下降 | 低 | 中 | 性能測試和優化 |

---

## 7. 結論

### 保留的功能 (Phase 2 擴展)
- TaskDecomposer - 任務分解能力
- AutonomousDecisionEngine - 決策追蹤和審計
- TrialAndErrorEngine - 自適應學習
- SessionManager 業務邏輯 - 會話生命週期

### 遷移到官方 API
- 規劃核心 → MagenticBuilder
- 狀態持久化 → CheckpointStorage
- 檢查點管理 → Checkpoint API

### 下一步
1. S24-2: 實現 PlanningAdapter (10 pts)
2. S24-3: 實現 MultiTurnAdapter (8 pts)
3. S24-4: 更新 API 路由 (4 pts)
4. S24-5: 測試和文檔 (3 pts)

---

**分析完成日期**: 2025-12-06
**分析者**: Claude
**狀態**: ✅ 完成
