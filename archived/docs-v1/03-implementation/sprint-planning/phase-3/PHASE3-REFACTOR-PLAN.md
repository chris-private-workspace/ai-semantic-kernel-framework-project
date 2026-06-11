# Phase 3 重構計劃 (修正版)

**創建日期**: 2025-12-06
**完成日期**: 2025-12-06
**目標**: 修正 Sprint 13-18 的實現，確保正確使用 Microsoft Agent Framework 官方 API

---

## ✅ 執行狀態: 已完成

| Sprint | 點數 | 狀態 | 完成日期 |
|--------|------|------|----------|
| Sprint 19 - 官方 API 修正 | 20/20 | ✅ 完成 | 2025-12-06 |

**驗證結果**: 5/5 checks passed

---

## 問題回顧

### 現有問題
所有 Sprint 13-18 的適配器都沒有使用官方 API：
- `concurrent.py` - 缺少 `from agent_framework import ConcurrentBuilder`
- `groupchat.py` - 缺少 `from agent_framework import GroupChatBuilder`
- `handoff.py` - 缺少 `from agent_framework import HandoffBuilder`
- `magentic.py` - 缺少 `from agent_framework import MagenticBuilder`
- `workflow_executor.py` - 缺少 `from agent_framework import WorkflowExecutor`

### 根本原因
1. `agent-framework` 套件未安裝
2. AI 開發過程中上下文丟失
3. 缺乏驗證機制

---

## 重構策略決定

### 問題: 更新現有文件 vs 創建新的 Sprint？

**建議: 創建新的「修正 Sprint」(Sprint 19)**

**理由**:
1. **保留歷史記錄**: Sprint 13-18 的文檔記錄了錯誤的實現過程，這是有價值的學習記錄
2. **清晰的職責分離**: 新的 Sprint 專注於「修正」而非「新功能」
3. **符合 BMAD 方法論**: 每個 Sprint 都有明確的目標和範圍
4. **便於追蹤**: 可以清楚地知道哪些代碼是修正後的版本

### 文件結構

```
docs/03-implementation/sprint-planning/phase-3/
├── sprint-13-plan.md          # 保留 (歷史記錄)
├── sprint-14-plan.md          # 保留 (歷史記錄)
├── sprint-15-plan.md          # 保留 (歷史記錄)
├── sprint-16-plan.md          # 保留 (歷史記錄)
├── sprint-17-plan.md          # 保留 (歷史記錄)
├── sprint-18-plan.md          # 保留 (歷史記錄)
├── sprint-19-plan.md          # 新增: 修正 Sprint
├── sprint-19-checklist.md     # 新增: 修正檢查清單
└── SPRINT-WORKFLOW-CHECKLIST.md  # 新增: 工作流程檢查點

docs/03-implementation/sprint-execution/
├── sprint-13/ ... sprint-18/  # 保留 (歷史記錄)
└── sprint-19/                 # 新增: 修正執行
    ├── progress.md
    └── decisions.md
```

---

## Sprint 19: Phase 3 官方 API 修正

### 目標
修正 5 個適配器文件，使其正確使用 Microsoft Agent Framework 官方 API

### Story Points: 20 點

### User Stories

#### S19-1: ConcurrentBuilder 修正 (4 點)
**修改範圍**: `builders/concurrent.py`

**修改內容**:
```python
# 添加 import
from agent_framework import ConcurrentBuilder, Executor, Workflow

# 修改 __init__
def __init__(self, ...):
    self._builder = ConcurrentBuilder()  # 添加官方 Builder
    # 保留現有業務邏輯

# 修改 build()
def build(self) -> Workflow:
    for executor in self._executors:
        self._builder.participants(executor)
    return self._builder.with_aggregator(self._aggregator).build()
```

#### S19-2: GroupChatBuilder 修正 (4 點)
**修改範圍**: `builders/groupchat.py`

**修改內容**:
```python
from agent_framework import (
    GroupChatBuilder,
    GroupChatDirective,
    ManagerSelectionResponse,
)

def __init__(self, ...):
    self._builder = GroupChatBuilder()

def build(self) -> Workflow:
    return self._builder.participants(...).with_max_rounds(...).build()
```

#### S19-3: HandoffBuilder 修正 (4 點)
**修改範圍**: `builders/handoff.py`

**修改內容**:
```python
from agent_framework import HandoffBuilder, HandoffUserInputRequest

def __init__(self, ...):
    self._builder = HandoffBuilder()

def build(self) -> Workflow:
    return self._builder.participants(...).set_coordinator(...).build()
```

#### S19-4: MagenticBuilder 修正 (4 點)
**修改範圍**: `builders/magentic.py`

**修改內容**:
```python
from agent_framework import (
    MagenticBuilder,
    MagenticManagerBase,
    StandardMagenticManager,
)

def __init__(self, ...):
    self._builder = MagenticBuilder()
```

#### S19-5: WorkflowExecutor 修正 (4 點)
**修改範圍**: `builders/workflow_executor.py`

**修改內容**:
```python
from agent_framework import (
    WorkflowExecutor,
    SubWorkflowRequestMessage,
    SubWorkflowResponseMessage,
)

def __init__(self, ...):
    self._executor = WorkflowExecutor(...)
```

---

## 修正流程

### 每個 Story 的修正步驟

1. **開始前** (5 分鐘)
   - [ ] 閱讀 `SPRINT-WORKFLOW-CHECKLIST.md`
   - [ ] 確認官方 API 可用: `python -c "from agent_framework import XxxBuilder"`

2. **修改代碼** (30-60 分鐘)
   - [ ] 添加官方 API import
   - [ ] 添加 `self._builder = OfficialBuilder()` 在 `__init__`
   - [ ] 修改 `build()` 方法調用官方 Builder
   - [ ] 保留現有業務邏輯

3. **驗證** (10 分鐘)
   - [ ] 運行 `python scripts/verify_official_api_usage.py`
   - [ ] 運行該文件的單元測試
   - [ ] 確認語法正確: `python -m py_compile xxx.py`

4. **更新文檔** (5 分鐘)
   - [ ] 更新 `sprint-19/progress.md`
   - [ ] 標記 checklist 項目

---

## 預估時間

| Story | 預估時間 | 複雜度 |
|-------|---------|--------|
| S19-1 ConcurrentBuilder | 1 小時 | 中 |
| S19-2 GroupChatBuilder | 1 小時 | 中 |
| S19-3 HandoffBuilder | 1 小時 | 中 |
| S19-4 MagenticBuilder | 1.5 小時 | 中高 |
| S19-5 WorkflowExecutor | 1.5 小時 | 中高 |
| **總計** | **6 小時** | |

---

## 驗收標準

### 必須通過
1. `python scripts/verify_official_api_usage.py` 輸出 `5/5 passed`
2. 所有單元測試通過
3. 語法檢查通過

### 代碼審查
1. 每個適配器文件都有 `from agent_framework import ...`
2. 每個適配器類都有 `self._builder = OfficialBuilder()`
3. 每個 `build()` 方法都調用 `self._builder.build()`

---

## 風險和注意事項

### 風險
1. **API 不兼容**: 官方 API 可能與現有業務邏輯不完全匹配
   - 緩解: 查看官方源碼，必要時調整業務邏輯

2. **遷移層影響**: 修改可能影響 `*_migration.py` 文件
   - 緩解: 遷移層不需要使用官方 API，保持原樣

### 注意事項
1. **保留業務邏輯**: 只修改 API 調用，不改變功能行為
2. **向後兼容**: 保持現有介面不變
3. **驗證優先**: 每次修改後立即驗證

---

## 相關文件

- [工作流程檢查點](./SPRINT-WORKFLOW-CHECKLIST.md)
- [根因分析報告](../sprint-execution/phase-3-root-cause-analysis.md)
- [架構審查報告](../sprint-execution/phase-3-architecture-audit.md)
- [驗證腳本](../../../../backend/scripts/verify_official_api_usage.py)
