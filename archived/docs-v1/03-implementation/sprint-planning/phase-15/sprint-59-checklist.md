# Sprint 59 Checklist: AG-UI Basic Features (1-4)

## Pre-Sprint Setup

- [x] 確認 Sprint 58 已完成
- [x] 確認 HybridEventBridge 可用
- [x] 確認 Thread Manager 可用
- [x] 確認 AG-UI Event Types 可用
- [x] 建立 `backend/src/integrations/ag_ui/features/` 目錄結構
- [x] 建立 `frontend/src/components/ag-ui/` 目錄結構

---

## S59-1: Agentic Chat (7 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/__init__.py`
- [x] `backend/src/integrations/ag_ui/features/agentic_chat.py`
  - [x] `AgenticChatHandler` 類別
  - [x] `handle_chat()` async generator 方法
  - [x] 整合 `HybridOrchestratorV2`
  - [x] 整合 `HybridEventBridge`

### 檔案建立 (前端)
- [x] `frontend/src/components/ag-ui/AgentChat.tsx`
  - [x] 訊息列表渲染
  - [x] 載入狀態顯示
  - [x] 整合 `useAGUI` Hook
- [x] `frontend/src/components/ag-ui/Message.tsx`
  - [x] 用戶訊息樣式
  - [x] 助理訊息樣式
  - [x] 工具調用內嵌顯示
- [x] `frontend/src/components/ag-ui/ChatInput.tsx`
  - [x] 輸入框組件
  - [x] 發送按鈕
  - [x] disabled 狀態
- [x] `frontend/src/components/ag-ui/index.ts`
- [x] `frontend/src/hooks/useAGUI.ts`
  - [x] `messages` 狀態
  - [x] `sendMessage()` 方法
  - [x] `isLoading` 狀態
  - [x] SSE 連接管理
- [x] `frontend/src/providers/AGUIProvider.tsx`

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/test_agentic_chat.py`
- [x] `frontend/tests/components/ag-ui/AgentChat.test.tsx`
- [x] SSE 串流測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 訊息正確串流顯示
- [x] 工具調用正確內嵌
- [x] 載入狀態正確切換

---

## S59-2: Backend Tool Rendering (7 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/tool_rendering.py`
  - [x] `ToolRenderingHandler` 類別
  - [x] `execute_and_format()` 方法
  - [x] `_detect_result_type()` 方法
  - [x] `_format_result()` 方法
  - [x] 整合 `UnifiedToolExecutor`

### 檔案建立 (前端)
- [x] `frontend/src/components/ag-ui/ToolResultRenderer.tsx`
  - [x] text 類型渲染
  - [x] json 類型渲染
  - [x] table 類型渲染
  - [x] image 類型渲染
- [x] `frontend/src/components/ag-ui/ToolExecutingIndicator.tsx`
- [x] `frontend/src/components/ag-ui/ToolErrorDisplay.tsx`

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/test_tool_rendering.py`
- [x] `frontend/tests/components/ag-ui/ToolResultRenderer.test.tsx`
- [x] 各種結果類型測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 結果類型正確檢測
- [x] 各類型正確渲染
- [x] 錯誤狀態正確顯示

---

## S59-3: Human-in-the-Loop (8 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/human_in_loop.py`
  - [x] `HITLHandler` 類別
  - [x] `check_approval_needed()` 方法
  - [x] `create_approval_event()` 方法
  - [x] `handle_approval_response()` 方法
  - [x] `ApprovalStorage` 類別
  - [x] 整合 `RiskAssessmentEngine`

### API 端點
- [x] 修改 `backend/src/api/v1/ag_ui/routes.py`
  - [x] `POST /api/v1/ag-ui/approvals/{id}/approve`
  - [x] `POST /api/v1/ag-ui/approvals/{id}/reject`
  - [x] `GET /api/v1/ag-ui/approvals/pending`

### 檔案建立 (前端)
- [x] `frontend/src/components/ag-ui/ApprovalDialog.tsx`
  - [x] 風險等級 Badge 顯示
  - [x] 工具名稱顯示
  - [x] 參數 JSON 顯示
  - [x] 風險評估原因顯示
  - [x] 批准按鈕
  - [x] 拒絕按鈕
  - [x] 處理中狀態

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/test_human_in_loop.py`
- [x] `backend/tests/unit/api/v1/ag_ui/test_approval_routes.py`
- [x] `frontend/tests/components/ag-ui/ApprovalDialog.test.tsx`
- [x] 審批流程 E2E 測試
- [x] 超時處理測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 高風險操作觸發審批
- [x] 審批/拒絕正確處理
- [x] 超時正確觸發
- [x] 風險等級正確顯示

---

## S59-4: Agentic Generative UI (6 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/generative_ui.py`
  - [x] `GenerativeUIHandler` 類別
  - [x] `emit_progress_event()` 方法
  - [x] `emit_mode_switch_event()` 方法
  - [x] 整合 `ModeSwitcher`

### 檔案建立 (前端)
- [x] `frontend/src/components/ag-ui/ProgressIndicator.tsx`
  - [x] 進度條組件
  - [x] 步驟狀態圖標
  - [x] 步驟名稱顯示
  - [x] 進度百分比
- [x] `frontend/src/components/ag-ui/ModeSwitchNotification.tsx`
  - [x] 模式切換通知
  - [x] 切換原因顯示

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/test_generative_ui.py`
- [x] `frontend/tests/components/ag-ui/ProgressIndicator.test.tsx`
- [x] 進度更新測試
- [x] 模式切換測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 進度事件正確發送
- [x] 進度條正確更新
- [x] 模式切換通知正確顯示
- [x] 步驟狀態正確切換

---

## Quality Gates

### 代碼品質 (後端)
- [x] `black .` 格式化通過
- [x] `isort .` 導入排序通過
- [x] `flake8 .` 無錯誤
- [x] `mypy .` 類型檢查通過

### 代碼品質 (前端)
- [x] `npm run lint` 通過
- [x] `npm run build` 成功
- [x] TypeScript 類型檢查通過

### 測試品質
- [x] 後端單元測試全部通過
- [x] 前端組件測試全部通過
- [x] 覆蓋率 > 85%

### 整合測試
- [x] 完整對話流程 E2E 測試
- [x] 工具執行渲染 E2E 測試
- [x] 審批流程 E2E 測試
- [x] 進度更新 E2E 測試

---

## Notes

```
Sprint 59 開始日期: 2026-01-05
Sprint 59 結束日期: 2026-01-05
實際完成點數: 28 / 28 pts ✅
```
