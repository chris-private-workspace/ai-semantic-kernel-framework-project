# Phase 15 AG-UI UAT 測試腳本

## 概覽

本目錄包含 Phase 15 AG-UI Protocol 的 UAT 測試腳本，用於驗證 7 個 AG-UI 功能的 API 行為。

## 目錄結構

```
phase_15_ag_ui/
├── __init__.py                  # 套件初始化
├── README.md                    # 本文件
├── phase_15_ag_ui_test.py       # 主測試執行器
├── scenario_agentic_chat.py     # Feature 1: Agentic Chat
├── scenario_tool_rendering.py   # Feature 2: Tool Rendering
├── scenario_hitl.py             # Feature 3: Human-in-the-Loop
├── scenario_generative_ui.py    # Feature 4: Generative UI
├── scenario_tool_ui.py          # Feature 5: Tool-based UI
├── scenario_shared_state.py     # Feature 6: Shared State
├── scenario_predictive.py       # Feature 7: Predictive State
└── test_results/                # 測試結果 JSON
```

## 前置條件

1. 後端服務運行中 (`http://localhost:8000`)
2. Python 3.10+
3. 安裝依賴:

```bash
pip install httpx aiohttp pytest pytest-asyncio
```

## 執行測試

### 執行所有測試

```bash
cd scripts/uat/phase_tests/phase_15_ag_ui
python phase_15_ag_ui_test.py
```

### 執行單個場景

```bash
python -c "from scenario_agentic_chat import test_agentic_chat; import asyncio; asyncio.run(test_agentic_chat())"
```

### 使用 pytest

```bash
pytest phase_15_ag_ui_test.py -v
```

## 測試場景

### Feature 1: Agentic Chat
- 基本對話發送
- SSE 串流接收
- 工具調用追蹤

### Feature 2: Tool Rendering
- 結果類型檢測
- 格式化輸出驗證

### Feature 3: Human-in-the-Loop
- 審批請求創建
- 批准/拒絕流程
- 超時處理

### Feature 4: Generative UI
- 進度事件
- 模式切換事件

### Feature 5: Tool-based UI
- 動態組件定義
- 事件回調

### Feature 6: Shared State
- 狀態同步
- 增量更新
- 衝突處理

### Feature 7: Predictive State
- 樂觀更新
- 確認/回滾

## 測試結果

測試結果保存在 `test_results/` 目錄，格式為 JSON:

```json
{
  "timestamp": "2026-01-05T12:00:00",
  "total_tests": 32,
  "passed": 30,
  "failed": 2,
  "skipped": 0,
  "duration_seconds": 45.2,
  "features": {
    "agentic_chat": { "passed": 5, "failed": 0 },
    ...
  }
}
```

## 相關文檔

- [UAT 測試規格](../../../../claudedocs/5-status/phase-15-agui/uat-test-spec.md)
- [詳細測試場景](../../../../claudedocs/5-status/phase-15-agui/uat-test-scenarios.md)
- [AG-UI API 參考](../../../../archived/docs-v1/api/ag-ui-api-reference.md)
