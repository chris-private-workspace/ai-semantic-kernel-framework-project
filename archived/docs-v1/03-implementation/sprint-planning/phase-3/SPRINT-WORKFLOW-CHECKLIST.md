# Phase 3 Sprint 工作流程檢查點

**目的**: 確保每個 Sprint 開發過程中正確使用 Microsoft Agent Framework 官方 API

---

## Sprint 開始前檢查 (BEFORE SPRINT)

### 環境驗證
- [ ] 運行 `pip install agent-framework` 確認套件已安裝
- [ ] 運行 `python -c "from agent_framework import ConcurrentBuilder"` 確認可以 import
- [ ] 運行 `python scripts/verify_official_api_usage.py` 查看當前狀態

### 規劃文件審閱
- [ ] 已閱讀對應 Sprint 的 `sprint-XX-plan.md`
- [ ] 已確認規劃文件中的代碼範例 (例如 import 語句)
- [ ] 已理解「適配器」的正確含義：**包裝官方 API**，而非重新實現

### 官方 API 確認
- [ ] 確認要使用的官方類名稱 (如 `ConcurrentBuilder`, `GroupChatBuilder`)
- [ ] 確認官方類的方法 (如 `.participants()`, `.build()`)
- [ ] 參考 `reference/agent-framework/` 中的官方源碼

---

## 每個 Story 開始時檢查 (BEFORE STORY)

### 代碼準備
- [ ] 在文件頂部添加官方 API 的 import：
```python
from agent_framework import (
    ConcurrentBuilder,  # 或其他需要的官方類
    Executor,
    Workflow,
)
```

### 適配器結構確認
- [ ] 適配器類包含官方 Builder 的實例變數：
```python
class XxxBuilderAdapter:
    def __init__(self, ...):
        self._builder = OfficialBuilder()  # 使用官方類
```

- [ ] `build()` 方法調用官方 Builder：
```python
def build(self) -> Workflow:
    return self._builder.participants(...).build()
```

---

## 每個 Story 完成時檢查 (AFTER STORY)

### 代碼驗證
- [ ] 運行 `python scripts/verify_official_api_usage.py` 確認通過
- [ ] 在文件中搜索 `from agent_framework` 確認有正確的 import
- [ ] 確認代碼中有 `self._builder = OfficialBuilder()` 模式

### 功能驗證
- [ ] 單元測試通過
- [ ] 適配器可以正確構建工作流

### 文檔更新
- [ ] 更新 `progress.md` 標記完成
- [ ] 更新 `sprint-XX-checklist.md` 勾選項目

---

## Sprint 結束時檢查 (AFTER SPRINT)

### 完整驗證
- [ ] 運行 `python scripts/verify_official_api_usage.py` 所有檢查通過
- [ ] 所有單元測試通過
- [ ] 整合測試通過

### 對照規劃
- [ ] 對照 `sprint-XX-plan.md` 中的代碼範例，確認實現一致
- [ ] 確認所有官方 API 都有被正確使用

### 代碼審查
- [ ] 審查每個適配器文件的 import 語句
- [ ] 審查每個適配器類的 `__init__` 方法
- [ ] 審查每個 `build()` 方法

---

## 驗證腳本使用說明

### 基本使用
```bash
cd backend
python scripts/verify_official_api_usage.py
```

### 預期輸出 (修復後)
```
============================================================
Agent Framework Official API Usage Verification
============================================================

[PASS] concurrent.py
[PASS] groupchat.py
[PASS] handoff.py
[PASS] magentic.py
[PASS] workflow_executor.py

============================================================
Summary: 5/5 passed, 0 skipped
============================================================
[SUCCESS] All checks passed!
```

---

## 正確 vs 錯誤範例

### ❌ 錯誤: 自行實現功能
```python
# 沒有從 agent_framework import 官方類
class ConcurrentBuilderAdapter:
    def __init__(self, ...):
        self._tasks = []  # 自行管理任務

    def build(self):
        return MyCustomWorkflow(...)  # 自行實現
```

### ✅ 正確: 使用官方 API
```python
from agent_framework import ConcurrentBuilder, Workflow

class ConcurrentBuilderAdapter:
    def __init__(self, ...):
        self._builder = ConcurrentBuilder()  # 使用官方類

    def build(self) -> Workflow:
        return self._builder.participants(...).with_aggregator(...).build()
```

---

## 緊急聯繫

如果在開發過程中遇到以下問題，應立即停止並確認：

1. **無法 import 官方類** → 檢查 `pip install agent-framework`
2. **不確定官方 API 用法** → 查看 `reference/agent-framework/` 源碼
3. **規劃文件與官方 API 不符** → 以官方 API 為準，更新規劃文件
