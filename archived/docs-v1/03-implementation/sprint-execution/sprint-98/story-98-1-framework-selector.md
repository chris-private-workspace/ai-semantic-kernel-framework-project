# Story 98-1: 重命名 IntentRouter → FrameworkSelector

## 概述

| 屬性 | 值 |
|------|-----|
| **Story 編號** | S98-1 |
| **名稱** | 重命名 IntentRouter → FrameworkSelector |
| **點數** | 2 |
| **優先級** | P0 |
| **狀態** | ✅ 完成 |

## 目標

重命名現有 IntentRouter 以避免與 Phase 28 的 BusinessIntentRouter 混淆。

## 變更清單

### 1. router.py (`backend/src/integrations/hybrid/intent/router.py`)

- [x] 類名: `IntentRouter` → `FrameworkSelector`
- [x] 方法: `analyze_intent()` → `select_framework()`
- [x] 保留向後兼容別名 `IntentRouter = FrameworkSelector`
- [x] 保留向後兼容方法 `analyze_intent()`

### 2. models.py (`backend/src/integrations/hybrid/intent/models.py`)

- [x] 添加別名: `FrameworkAnalysis = IntentAnalysis`
- [x] 更新模組頭部註釋

### 3. `__init__.py` 文件

- [x] `backend/src/integrations/hybrid/intent/__init__.py` - 導出新名稱
- [x] `backend/src/integrations/hybrid/__init__.py` - 導出新名稱

### 4. orchestrator_v2.py (`backend/src/integrations/hybrid/orchestrator_v2.py`)

- [x] 更新初始化參數: `intent_router` → `framework_selector`
- [x] 更新內部屬性: `_intent_router` → `_framework_selector`
- [x] 添加向後兼容參數支援
- [x] 添加向後兼容屬性

## 向後兼容性

所有舊名稱保持可用：

```python
# 新用法 (推薦)
from src.integrations.hybrid.intent import FrameworkSelector, FrameworkAnalysis

selector = FrameworkSelector()
analysis = await selector.select_framework("user input")

# 舊用法 (向後兼容)
from src.integrations.hybrid.intent import IntentRouter, IntentAnalysis

router = IntentRouter()  # Same as FrameworkSelector
analysis = await router.analyze_intent("user input")
```

## 測試驗證

- [x] 現有測試繼續使用舊名稱，確保向後兼容
- [x] 無破壞性變更

## 技術細節

### 類別對應

| 舊名稱 | 新名稱 | 說明 |
|--------|--------|------|
| `IntentRouter` | `FrameworkSelector` | 框架選擇器 |
| `IntentAnalysis` | `FrameworkAnalysis` | 框架分析結果 |
| `analyze_intent()` | `select_framework()` | 框架選擇方法 |

### 別名定義

```python
# router.py
IntentRouter = FrameworkSelector

# models.py
FrameworkAnalysis = IntentAnalysis
```

---

**完成日期**: 2026-01-16
