# Phase 16: Unified Agentic Chat Interface - UAT Tests

Phase 16 統一聊天介面的 UAT (User Acceptance Testing) 測試框架。

## 概述

本測試框架驗證 Phase 16 的核心功能：
- SSE 連接管理
- 消息流式傳輸
- 模式切換 (Chat/Workflow)
- HITL 審批流程
- 檢查點恢復
- 執行指標追蹤

## 目錄結構

```
phase_16_unified_chat/
├── __init__.py                      # 模組初始化
├── README.md                        # 本文件
├── phase_16_unified_chat_test.py    # 主測試執行器
├── unified_chat_client.py           # HTTP/SSE 測試客戶端
├── mock_generator.py                # 模擬數據生成器
├── scenario_sse_connection.py       # 場景 1: SSE 連接管理
├── scenario_message_streaming.py    # 場景 2: 消息流式傳輸
├── scenario_mode_switching.py       # 場景 3: 模式切換
├── scenario_approval_flow.py        # 場景 4: 審批流程
├── scenario_checkpoint_restore.py   # 場景 5: 檢查點恢復
├── scenario_execution_metrics.py    # 場景 6: 執行指標
└── test_results/                    # 測試結果輸出目錄
```

## 測試場景

| ID | 場景名稱 | 描述 | 步驟數 |
|----|----------|------|--------|
| PHASE16-001 | SSE Connection Management | 驗證 SSE 連接的建立、斷線重連和事件接收 | 6 |
| PHASE16-002 | Message Streaming | 驗證完整的消息發送和接收流程 | 7 |
| PHASE16-003 | Mode Switching | 驗證 Chat/Workflow 模式的自動檢測和手動切換 | 6 |
| PHASE16-004 | Approval Flow | 驗證工具呼叫的 HITL 審批機制 | 8 |
| PHASE16-005 | Checkpoint Restore | 驗證檢查點的創建和恢復功能 | 8 |
| PHASE16-006 | Execution Metrics | 驗證 Token 使用、執行時間和工具統計的追蹤 | 7 |

## 使用方式

### 基本執行

```bash
# 切換到測試目錄
cd scripts/uat/phase_tests/phase_16_unified_chat

# 使用模擬模式運行所有測試（默認）
python phase_16_unified_chat_test.py

# 使用真實 API 運行
python phase_16_unified_chat_test.py --use-real-api

# 運行單個場景
python phase_16_unified_chat_test.py --scenario PHASE16-001

# 詳細輸出
python phase_16_unified_chat_test.py --verbose

# 列出所有場景
python phase_16_unified_chat_test.py --list

# 不保存結果文件
python phase_16_unified_chat_test.py --no-save
```

### 執行模式

#### 模擬模式（默認）

- 不需要後端服務運行
- 使用 `MockSSEGenerator` 生成模擬事件
- 適合 CI/CD 和快速驗證

```bash
python phase_16_unified_chat_test.py
```

#### 真實 API 模式

- 需要後端服務在 `http://localhost:8000` 運行
- 測試真實的 API 端點

```bash
# 首先啟動後端
cd backend && uvicorn main:app --reload

# 然後運行測試
python phase_16_unified_chat_test.py --use-real-api
```

## API 端點依賴

測試依賴以下 API 端點：

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/v1/ag-ui` | POST | SSE 主端點 |
| `/api/v1/ag-ui/tool-calls/{id}/approve` | POST | 批准工具呼叫 |
| `/api/v1/ag-ui/tool-calls/{id}/reject` | POST | 拒絕工具呼叫 |
| `/api/v1/ag-ui/sessions/{id}/pending-approvals` | GET | 獲取待審批列表 |
| `/api/v1/ag-ui/checkpoints` | GET | 獲取檢查點列表 |
| `/api/v1/ag-ui/checkpoints/{id}/restore` | POST | 恢復檢查點 |
| `/api/v1/hybrid/analyze` | POST | 意圖分析 (模式檢測) |
| `/api/v1/ag-ui/state/{id}/sync` | GET | 狀態同步 |

## 測試場景詳情

### PHASE16-001: SSE Connection Management

驗證 SSE 連接的生命週期管理：

1. **建立 SSE 連接** - 驗證連接在 5 秒內建立
2. **驗證連接狀態** - 確認連接狀態正確
3. **接收 SSE 事件** - 驗證可接收各種事件類型
4. **模擬斷線** - 測試斷線處理
5. **驗證自動重連** - 驗證指數退避重連
6. **關閉連接** - 驗證資源清理

### PHASE16-002: Message Streaming

驗證完整的消息流程：

1. **發送用戶消息** - 發送測試消息
2. **接收 RUN_STARTED** - 驗證運行開始事件
3. **接收 TEXT_MESSAGE_START** - 驗證消息開始
4. **接收流式內容** - 驗證多個內容片段
5. **接收 TEXT_MESSAGE_END** - 驗證消息結束
6. **接收 RUN_FINISHED** - 驗證運行完成
7. **驗證消息完整性** - 確認內容正確拼接

### PHASE16-003: Mode Switching

驗證模式檢測和切換：

1. **發送 Chat 類型輸入** - 驗證 CHAT_MODE 檢測
2. **發送 Workflow 類型輸入** - 驗證 WORKFLOW_MODE 檢測
3. **驗證信心分數** - 確認分數在有效範圍
4. **測試邊界情況** - 處理模糊輸入
5. **驗證切換原因** - 確認原因記錄
6. **測試多次切換** - 驗證連續切換

### PHASE16-004: Approval Flow

驗證 HITL 審批機制：

1. **觸發審批請求** - 創建需要審批的工具呼叫
2. **驗證待審批列表** - 確認列表更新
3. **測試批准操作** - 驗證批准功能
4. **驗證工具執行** - 確認批准後執行
5. **測試拒絕操作** - 驗證拒絕功能
6. **驗證風險等級** - 確認風險分類
7. **測試批量審批** - 驗證批量操作
8. **驗證審批歷史** - 確認歷史記錄

### PHASE16-005: Checkpoint Restore

驗證檢查點功能：

1. **執行工作流** - 執行到 Step 2
2. **創建檢查點** - 在當前步驟創建
3. **繼續執行** - 執行到 Step 4
4. **獲取檢查點列表** - 確認檢查點存在
5. **恢復檢查點** - 恢復到 Step 2
6. **驗證狀態回滾** - 確認狀態正確
7. **驗證執行中禁用** - 確認執行中不可恢復
8. **測試多個檢查點** - 驗證多檢查點管理

### PHASE16-006: Execution Metrics

驗證指標追蹤：

1. **啟動計時器** - 開始計時
2. **追蹤 Token 使用** - 發送消息追蹤
3. **執行工具呼叫** - 執行多個工具
4. **驗證工具統計** - 確認 completed/failed/pending
5. **停止計時器** - 計算執行時間
6. **驗證格式化顯示** - 確認指標格式
7. **測試重置功能** - 驗證重置操作

## 測試輸出

測試結果保存在 `test_results/` 目錄，格式為 JSON：

```json
{
  "phase": "Phase 16: Unified Agentic Chat Interface",
  "timestamp": "2025-01-07T10:00:00.000000",
  "configuration": {
    "simulation_mode": true,
    "base_url": "http://localhost:8000/api/v1"
  },
  "summary": {
    "total_scenarios": 6,
    "passed": 6,
    "failed": 0,
    "errors": 0,
    "total_duration_ms": 1234.56
  },
  "scenarios": [...]
}
```

## 驗收標準

| 標準 | 要求 |
|------|------|
| SSE 連接建立 | < 5 秒 |
| 斷線重連 | < 30 秒內完成 |
| 消息回應開始 | < 500ms |
| 模式檢測準確率 | > 80% |
| 審批請求顯示 | < 1 秒 |

## 依賴

- Python 3.9+
- httpx
- asyncio

## 相關文檔

- [Phase 16 規劃文檔](../../../../archived/docs-v1/03-implementation/sprint-planning/phase-16/README.md)
- [AG-UI API 參考](../../../../archived/docs-v1/api/ag-ui-api-reference.md)
- [AG-UI 整合指南](../../../../archived/docs-v1/guides/ag-ui-integration-guide.md)

---

**版本**: 1.0.0
**更新日期**: 2026-01-07
**狀態**: Phase 16 Complete (113 pts)
