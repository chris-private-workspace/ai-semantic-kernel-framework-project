# Sprint 58 Checklist: AG-UI Core Infrastructure

## Pre-Sprint Setup

- [x] 確認 Phase 14 已完成
- [x] 確認 HybridOrchestratorV2 可用
- [x] 建立 `backend/src/api/v1/ag_ui/` 目錄結構
- [x] 建立 `backend/src/integrations/ag_ui/` 目錄結構

---

## S58-1: AG-UI SSE Endpoint (10 pts)

### 檔案建立
- [x] `backend/src/api/v1/ag_ui/__init__.py`
- [x] `backend/src/api/v1/ag_ui/routes.py`
  - [x] `POST /api/v1/ag-ui` 主端點
  - [x] SSE StreamingResponse 實現
  - [x] CORS headers 設定
- [x] `backend/src/api/v1/ag_ui/schemas.py`
  - [x] `RunAgentInput` Pydantic 模型
  - [x] `AGUIMessage` 模型
  - [x] `AGUITool` 模型
- [x] `backend/src/api/v1/ag_ui/dependencies.py`
  - [x] `get_event_bridge()` 依賴
  - [x] `get_thread_manager()` 依賴

### API 註冊
- [x] 修改 `backend/src/api/v1/__init__.py` 註冊 ag_ui router

### 測試
- [x] `backend/tests/unit/api/v1/ag_ui/test_routes.py`
- [x] SSE 格式測試
- [x] 請求驗證測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 端點返回 `text/event-stream` content-type
- [x] SSE 格式正確 (`data: {...}\n\n`)
- [x] CORS headers 正確設定

---

## S58-2: HybridEventBridge (10 pts)

### 檔案建立
- [x] `backend/src/integrations/ag_ui/__init__.py`
- [x] `backend/src/integrations/ag_ui/bridge.py`
  - [x] `HybridEventBridge` 類別
  - [x] `stream_events()` async generator
  - [x] `_format_sse()` 方法
- [x] `backend/src/integrations/ag_ui/converters.py`
  - [x] `EventConverters` 類別
  - [x] `convert()` 方法
  - [x] `to_run_started()` 方法
  - [x] `to_run_finished()` 方法
  - [x] `to_text_message_start()` 方法
  - [x] `to_text_message_content()` 方法
  - [x] `to_text_message_end()` 方法
  - [x] `to_tool_call_start()` 方法
  - [x] `to_tool_call_args()` 方法
  - [x] `to_tool_call_end()` 方法

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/test_bridge.py`
- [x] `backend/tests/unit/integrations/ag_ui/test_converters.py`
- [x] 事件轉換測試
- [x] 串流測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] Hybrid 事件正確轉換為 AG-UI 事件
- [x] 事件順序正確 (RUN_STARTED → ... → RUN_FINISHED)
- [x] 錯誤處理正確

---

## S58-3: Thread Manager (5 pts)

### 檔案建立
- [x] `backend/src/integrations/ag_ui/thread/__init__.py`
- [x] `backend/src/integrations/ag_ui/thread/models.py`
  - [x] `AGUIThread` dataclass
  - [x] `AGUIMessage` dataclass
  - [x] `ThreadStatus` 枚舉
- [x] `backend/src/integrations/ag_ui/thread/manager.py`
  - [x] `ThreadManager` 類別
  - [x] `get_or_create()` 方法
  - [x] `append_messages()` 方法
  - [x] `update_state()` 方法
  - [x] `delete()` 方法
- [x] `backend/src/integrations/ag_ui/thread/storage.py`
  - [x] `ThreadRepository` 類別
  - [x] `ThreadCache` 類別

### API 端點
- [x] 在 `backend/src/api/v1/ag_ui/routes.py` 添加:
  - [x] `GET /api/v1/ag-ui/threads/{thread_id}`
  - [x] `DELETE /api/v1/ag-ui/threads/{thread_id}`

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/thread/test_manager.py`
- [x] `backend/tests/unit/integrations/ag_ui/thread/test_storage.py`
- [x] Redis 緩存測試
- [x] PostgreSQL 持久化測試

### 驗證
- [x] Thread 正確創建和獲取
- [x] 多 Run 共用同一 Thread
- [x] Write-Through 策略正確

---

## S58-4: AG-UI Event Types (5 pts)

### 檔案建立
- [x] `backend/src/integrations/ag_ui/events/__init__.py`
- [x] `backend/src/integrations/ag_ui/events/base.py`
  - [x] `AGUIEventType` 枚舉
  - [x] `BaseAGUIEvent` 基類
- [x] `backend/src/integrations/ag_ui/events/lifecycle.py`
  - [x] `RunStartedEvent` 模型
  - [x] `RunFinishedEvent` 模型
- [x] `backend/src/integrations/ag_ui/events/message.py`
  - [x] `TextMessageStartEvent` 模型
  - [x] `TextMessageContentEvent` 模型
  - [x] `TextMessageEndEvent` 模型
- [x] `backend/src/integrations/ag_ui/events/tool.py`
  - [x] `ToolCallStartEvent` 模型
  - [x] `ToolCallArgsEvent` 模型
  - [x] `ToolCallEndEvent` 模型
- [x] `backend/src/integrations/ag_ui/events/state.py`
  - [x] `StateSnapshotEvent` 模型
  - [x] `StateDeltaEvent` 模型
  - [x] `CustomEvent` 模型

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/events/test_base.py`
- [x] `backend/tests/unit/integrations/ag_ui/events/test_message.py`
- [x] `backend/tests/unit/integrations/ag_ui/events/test_tool.py`
- [x] JSON 序列化測試
- [x] 類型驗證測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 所有事件可正確序列化為 JSON
- [x] Literal type 正確驗證
- [x] timestamp 自動生成

---

## Quality Gates

### 代碼品質
- [x] `black .` 格式化通過
- [x] `isort .` 導入排序通過
- [x] `flake8 .` 無錯誤
- [x] `mypy .` 類型檢查通過

### 測試品質
- [x] 單元測試全部通過
- [x] 覆蓋率 > 85%

### 整合測試
- [x] SSE 端點完整流程測試
- [x] Thread 持久化測試
- [x] 錯誤處理測試

---

## Notes

```
Sprint 58 開始日期: 2026-01-04
Sprint 58 結束日期: 2026-01-05
實際完成點數: 30 / 30 pts ✅
```
