# Sprint 66 Progress: Tool Integration Bug Fix

> **Phase 16**: Unified Agentic Chat Interface
> **Sprint 目標**: 修復工具參數傳遞問題，啟用完整 Agentic 功能

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 66 |
| 計劃點數 | 10 Story Points |
| 開始日期 | 2026-01-07 |
| 完成日期 | 2026-01-07 |
| 類型 | Bug Fix Sprint |
| 前置條件 | Sprint 62-65 完成、Claude SDK 整合 |

---

## Sprint 背景

Phase 16 Unified Chat Interface 已完成核心 UI，但工具調用功能因關鍵參數傳遞問題而無法運作：

### 根本原因

**檔案**: `backend/src/api/v1/ag_ui/dependencies.py`
**問題**: `tools` 參數接收後未傳遞給 `client.query()`

```python
# 修復前
result = await client.query(
    prompt=prompt,
    max_tokens=max_tokens or 4096,
)
# 缺少: tools=tools 參數

# 修復後
result = await client.query(
    prompt=prompt,
    tools=tool_names,  # ← 新增
    max_tokens=max_tokens or 4096,
)
```

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S66-1 | Fix Claude Executor Tool Passing | 3 | ✅ 完成 | 100% |
| S66-2 | Add AG-UI Tool Events | 3 | ✅ 完成 | 100% |
| S66-3 | Configure Default Tools | 2 | ✅ 完成 | 100% |
| S66-4 | Add HITL Risk Assessment | 2 | ✅ 完成 | 100% |

**整體進度**: 10/10 pts (100%) ✅

---

## 詳細進度記錄

### S66-1: Fix Claude Executor Tool Passing (3 pts)

**狀態**: ✅ 完成

**變更內容**:
- 修改 `_create_claude_executor()` 以接收和傳遞 tools 參數
- 從 Dict 格式提取工具名稱: `[t.get("name") for t in tools]`
- 傳遞至 `client.query(tools=tool_names)`

**檔案修改**:
- `backend/src/api/v1/ag_ui/dependencies.py`

**驗收**:
- ✅ 後端正常啟動
- ✅ 工具參數正確傳遞至 Claude SDK

---

### S66-2: Add AG-UI Tool Events (3 pts)

**狀態**: ✅ 完成

**變更內容**:
- 在 bridge.py 新增工具事件生成邏輯
- 實現 `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` 事件
- 處理 HybridResultV2 中的 tool_calls

**檔案修改**:
- `backend/src/integrations/ag_ui/bridge.py`

**驗收**:
- ✅ 工具事件出現在 SSE 串流中
- ✅ 前端正確接收工具調用資料

---

### S66-3: Configure Default Tools (2 pts)

**狀態**: ✅ 完成

**變更內容**:
- 在 UnifiedChat.tsx 定義預設工具配置
- 低風險工具: Read, Glob, Grep, WebSearch, WebFetch
- 高風險工具: Write, Edit, MultiEdit, Bash, Task

**檔案修改**:
- `frontend/src/pages/UnifiedChat.tsx`

**驗收**:
- ✅ 工具定義在 API 請求中傳送
- ✅ 後端接收工具定義

---

### S66-4: Add HITL Risk Assessment (2 pts)

**狀態**: ✅ 完成

**變更內容**:
- 定義 `HIGH_RISK_TOOLS` 常數
- 在 `TOOL_CALL_START` 事件中添加 `requires_approval` 標記
- 添加 `risk_level` 屬性 (high/low)

**檔案修改**:
- `backend/src/integrations/ag_ui/bridge.py`

**驗收**:
- ✅ 高風險工具有 `requires_approval: true`
- ✅ 低風險工具有 `requires_approval: false`

---

## 修改的檔案總覽

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| `backend/src/api/v1/ag_ui/dependencies.py` | 修改 | 修復工具參數傳遞 |
| `backend/src/integrations/ag_ui/bridge.py` | 修改 | 工具事件 + HITL 風險標記 |
| `frontend/src/pages/UnifiedChat.tsx` | 修改 | 預設工具配置 |

---

## 測試結果

### 手動測試

| 測試案例 | 預期結果 | 狀態 |
|----------|----------|------|
| "請搜尋 AI 新聞" | WebSearch 自動執行 | ✅ 通過 |
| "請讀取 README.md" | Read 工具執行 | ✅ 通過 |
| "請寫入 test.txt" | HITL 審批對話框 | ✅ 通過 |
| 工具 UI 顯示 | 事件可見 | ✅ 通過 |

---

## 技術備註

### 工具參數轉換

```python
# 從 Dict 格式轉換為工具名稱列表
tool_names = []
if tools:
    tool_names = [t.get("name") for t in tools if t.get("name")]
```

### 風險評估邏輯

```python
HIGH_RISK_TOOLS = ["Write", "Edit", "MultiEdit", "Bash", "Task"]

yield AGUIEvent(
    type=AGUIEventType.TOOL_CALL_START,
    data={
        "tool_call_id": tc.id,
        "tool_name": tc.name,
        "requires_approval": tc.name in HIGH_RISK_TOOLS,
        "risk_level": "high" if tc.name in HIGH_RISK_TOOLS else "low",
    },
)
```

---

## Sprint 回顧

### 成功因素
- 問題根源定位準確
- 最小化變更範圍
- 保持現有功能穩定

### 學習要點
- Claude SDK 工具傳遞需要名稱列表而非完整定義
- HITL 風險評估應在事件層級處理

---

**更新日期**: 2026-01-07
**Sprint 狀態**: ✅ 完成
