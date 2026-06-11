# Sprint 131: 測試覆蓋率 → 80%

## 概述

Sprint 131 專注於將測試覆蓋率從 Phase 33 的 ~60% 提升到 Phase 34 的 80% 目標。根據 Sprint 123 的 gap analysis，優先補強 HITL、Metrics、MCP Core、Dialog Engine 等關鍵模組的測試覆蓋。

## 目標

1. HITL 模組覆蓋率 32% → 80%
2. Metrics 模組覆蓋率 25% → 70%
3. MCP Core（client/protocol/transport）覆蓋率 21% → 60%
4. Dialog Engine 覆蓋率 37% → 70%
5. 整體覆蓋率達到 80%

## Story Points: 25 點

## 前置條件

- ⬜ Sprint 128-130 完成
- ⬜ Sprint 123 gap analysis 已讀

## 任務分解

### Story 131-1: HITL 模組測試補強 (2 天, P2)

**目標**: 覆蓋率 32% → 80%

**缺失覆蓋**:
- `hitl/controller.py` (32%) — 審批工作流各狀態路徑
- `hitl/approval_handler.py` (22%) — 審批處理與超時
- `hitl/notification.py` (27%) — 通知分發

**新增測試**:

| 測試檔案 | 預估測試數 | 範圍 |
|----------|-----------|------|
| `test_hitl_controller_deep.py` | ~25 | 完整審批工作流 |
| `test_approval_handler.py` | ~15 | 審批/拒絕/超時 |
| `test_hitl_notification.py` | ~10 | 通知分發 |

### Story 131-2: Metrics + MCP Core 測試 (2 天, P2)

**Metrics 目標**: 25% → 70%
- `metrics.py` (25%) — OpenTelemetry 指標記錄

**MCP Core 目標**: 21% → 60%
- `core/client.py` (21%) — MCP 客戶端通訊
- `core/protocol.py` (22%) — MCP 協議處理
- `core/transport.py` (24%) — MCP 傳輸層

**新增測試**:

| 測試檔案 | 預估測試數 | 範圍 |
|----------|-----------|------|
| `test_orchestration_metrics.py` | ~20 | 指標記錄與聚合 |
| `test_mcp_client.py` | ~15 | 客戶端連線與通訊 |
| `test_mcp_protocol.py` | ~10 | 協議消息處理 |
| `test_mcp_transport.py` | ~10 | 傳輸層 |

### Story 131-3: Dialog Engine + Input Gateway (2 天, P2)

**Dialog Engine 目標**: 37% → 70%
- `guided_dialog/engine.py` (37%) — 對話引擎主流程

**Input Gateway 目標**: 17% → 50%
- `input_gateway/gateway.py` (17%) — 多源輸入處理

**新增測試**:

| 測試檔案 | 預估測試數 | 範圍 |
|----------|-----------|------|
| `test_dialog_engine_deep.py` | ~20 | 對話引擎完整流程 |
| `test_input_gateway.py` | ~15 | 多源輸入處理 |
| `test_schema_validator.py` | ~10 | Schema 驗證 |

### Story 131-4: 覆蓋率報告與驗證 (1 天, P2)

- 全面覆蓋率報告
- 差距分析更新
- 80% 目標達成確認

## 依賴

- 改善提案 Phase D P2: 測試覆蓋率 → 80%
- Sprint 123 gap analysis
