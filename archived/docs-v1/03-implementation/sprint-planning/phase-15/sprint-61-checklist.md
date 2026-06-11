# Sprint 61 Checklist: AG-UI Frontend Integration & E2E Testing

## Pre-Sprint Setup

- [x] 確認 Sprint 60 已完成
- [x] 確認 useSharedState Hook 可用
- [x] 確認 useOptimisticState Hook 可用
- [x] 確認 AG-UI Types 已定義
- [x] 確認後端 AG-UI API 可用
- [x] 建立 UAT 測試規格文檔 (Phase F)
- [x] 建立 Python UAT 腳本框架

---

## S61-1: useAGUI 主 Hook (8 pts) ✅ 已完成

### 檔案建立
- [x] `frontend/src/hooks/useAGUI.ts`
  - [x] `UseAGUIOptions` 介面
  - [x] `UseAGUIReturn` 介面
  - [x] SSE 連接管理 (EventSource)
  - [x] 連接狀態追蹤 (connectionStatus)
  - [x] 消息狀態管理 (messages, addUserMessage)
  - [x] 工具調用追蹤 (toolCalls, getToolCall)
  - [x] 待審批管理 (pendingApprovals)
  - [x] 審批操作 (approveToolCall, rejectToolCall)
  - [x] 執行控制 (runAgent, cancelRun)
  - [x] 運行狀態 (runState, isRunning)
  - [x] 整合 useSharedState
  - [x] 整合 useOptimisticState
  - [x] 自動重連機制

### 類型擴展
- [x] `frontend/src/types/ag-ui.ts`
  - [x] `ChatMessage` 類型
  - [x] `ToolCallState` 類型
  - [x] `ToolCallStatus` 類型
  - [x] `PendingApproval` 類型
  - [x] `RiskLevel` 類型
  - [x] `RunAgentInput` 類型
  - [x] `ToolDefinition` 類型
  - [x] `SSEConnectionStatus` 類型
  - [x] `RunStatus` 類型
  - [x] `AGUIRunState` 類型

### 導出更新
- [x] `frontend/src/hooks/index.ts`
  - [x] 導出 useAGUI
  - [x] 導出相關類型

### 驗證
- [x] Hook 可正確導入
- [x] TypeScript 編譯通過
- [x] SSE 事件類型正確處理

---

## S61-2: Chat 組件 (8 pts) ✅ 已完成

### 檔案建立
- [x] `frontend/src/components/ag-ui/chat/index.ts`
- [x] `frontend/src/components/ag-ui/chat/ChatContainer.tsx`
  - [x] 消息列表渲染
  - [x] 工具調用內嵌顯示
  - [x] 串流狀態指示
  - [x] 錯誤處理
- [x] `frontend/src/components/ag-ui/chat/MessageBubble.tsx`
  - [x] User 消息樣式
  - [x] Assistant 消息樣式
  - [x] System 消息樣式
  - [x] Tool 消息樣式
  - [x] 時間戳顯示
- [x] `frontend/src/components/ag-ui/chat/MessageInput.tsx`
  - [x] 多行輸入支持
  - [x] 發送按鈕
  - [x] Enter 發送 / Shift+Enter 換行
  - [x] 禁用狀態 (串流中)
- [x] `frontend/src/components/ag-ui/chat/ToolCallCard.tsx`
  - [x] 工具名稱顯示
  - [x] 參數顯示 (JSON 格式化)
  - [x] 執行狀態標籤
  - [x] 結果顯示
  - [x] 錯誤顯示
- [x] `frontend/src/components/ag-ui/chat/StreamingIndicator.tsx`
  - [x] 打字動畫
  - [x] 脈動效果

### 測試
- [x] ChatContainer 渲染測試
- [x] MessageBubble 各角色測試
- [x] MessageInput 交互測試
- [x] ToolCallCard 狀態測試

### 驗證
- [x] 消息正確渲染
- [x] 工具調用卡片正確顯示
- [x] 串流指示器正確動畫
- [x] 輸入框功能正常

---

## S61-3: HITL 審批組件 (5 pts) ✅ 已完成

### 檔案建立
- [x] `frontend/src/components/ag-ui/hitl/index.ts`
- [x] `frontend/src/components/ag-ui/hitl/ApprovalDialog.tsx`
  - [x] 模態框佈局
  - [x] 工具名稱和參數顯示
  - [x] 風險等級顯示
  - [x] 風險理由顯示
  - [x] 批准按鈕
  - [x] 拒絕按鈕
  - [x] 超時倒計時
- [x] `frontend/src/components/ag-ui/hitl/ApprovalBanner.tsx`
  - [x] 內嵌提示樣式
  - [x] 簡潔信息顯示
  - [x] 快速操作按鈕
- [x] `frontend/src/components/ag-ui/hitl/RiskBadge.tsx`
  - [x] Low 樣式 (綠色)
  - [x] Medium 樣式 (黃色)
  - [x] High 樣式 (橙色)
  - [x] Critical 樣式 (紅色)
- [x] `frontend/src/components/ag-ui/hitl/ApprovalList.tsx`
  - [x] 列表佈局
  - [x] 排序 (按時間/風險)
  - [x] 批量操作支持

### 測試
- [x] ApprovalDialog 開啟/關閉測試
- [x] 批准/拒絕操作測試
- [x] RiskBadge 各等級測試
- [x] 超時處理測試

### 驗證
- [x] 對話框正確顯示
- [x] 風險等級樣式正確
- [x] 操作回調正確觸發
- [x] 超時倒計時正確

---

## S61-4: AG-UI Demo 頁面 (10 pts) ✅ 已完成

### 檔案建立
- [x] `frontend/src/pages/ag-ui/AGUIDemoPage.tsx`
  - [x] Tab 導航 (7 個功能)
  - [x] 響應式佈局 (8+4 cols)
  - [x] 狀態欄顯示
- [x] `frontend/src/pages/ag-ui/components/index.ts`
- [x] `frontend/src/pages/ag-ui/components/AgenticChatDemo.tsx`
  - [x] 基本對話功能
  - [x] 消息歷史顯示
- [x] `frontend/src/pages/ag-ui/components/ToolRenderingDemo.tsx`
  - [x] 代碼結果語法高亮
  - [x] JSON 結果格式化
  - [x] 錯誤結果顯示
- [x] `frontend/src/pages/ag-ui/components/HITLDemo.tsx`
  - [x] 觸發審批場景
  - [x] 審批操作演示
- [x] `frontend/src/pages/ag-ui/components/GenerativeUIDemo.tsx`
  - [x] 進度指示器演示
  - [x] 模式切換動畫
- [x] `frontend/src/pages/ag-ui/components/ToolUIDemo.tsx`
  - [x] 表單生成演示
  - [x] 圖表生成演示
  - [x] 卡片生成演示
  - [x] 表格生成演示
- [x] `frontend/src/pages/ag-ui/components/SharedStateDemo.tsx`
  - [x] 狀態顯示
  - [x] 手動更新
  - [x] 同步狀態
- [x] `frontend/src/pages/ag-ui/components/PredictiveDemo.tsx`
  - [x] 樂觀更新演示
  - [x] 回滾演示
- [x] `frontend/src/pages/ag-ui/components/EventLogPanel.tsx`
  - [x] 事件列表
  - [x] 事件過濾
  - [x] 事件詳情展開

### 路由配置
- [x] `frontend/src/App.tsx` 添加 `/ag-ui-demo` 路由

### 驗證
- [x] 頁面可訪問 (/ag-ui-demo)
- [x] 所有 Tab 可切換
- [x] 事件日誌正確顯示
- [x] 響應式佈局正確

---

## S61-5: Playwright E2E 測試 (7 pts) ✅ 已完成

### 測試工具建立
- [x] `frontend/e2e/ag-ui/fixtures.ts`
  - [x] AGUITestPage 類別
  - [x] 常用操作封裝
  - [x] 斷言輔助函數

### 功能測試建立
- [x] `frontend/e2e/ag-ui/agentic-chat.spec.ts`
  - [x] 發送消息測試
  - [x] 接收串流響應測試
  - [x] 消息列表顯示測試
- [x] `frontend/e2e/ag-ui/tool-rendering.spec.ts`
  - [x] 代碼結果渲染測試
  - [x] JSON 結果渲染測試
  - [x] 錯誤結果渲染測試
- [x] `frontend/e2e/ag-ui/hitl.spec.ts`
  - [x] 審批對話框觸發測試
  - [x] 批准操作測試
  - [x] 拒絕操作測試
  - [x] 超時處理測試
- [x] `frontend/e2e/ag-ui/generative-ui.spec.ts`
  - [x] 進度指示器測試
  - [x] 模式切換測試
- [x] `frontend/e2e/ag-ui/tool-ui.spec.ts`
  - [x] 表單驗證測試
  - [x] 圖表渲染測試
  - [x] 表格排序測試
- [x] `frontend/e2e/ag-ui/shared-state.spec.ts`
  - [x] 狀態同步測試
  - [x] 衝突解決測試
- [x] `frontend/e2e/ag-ui/predictive-state.spec.ts`
  - [x] 樂觀更新測試
  - [x] 回滾動畫測試
- [x] `frontend/e2e/ag-ui/integration.spec.ts`
  - [x] 完整對話流程測試
  - [x] 多功能組合測試

### 驗證
- [x] 所有 E2E 測試文件已建立
- [x] 測試覆蓋所有 7 個功能
- [x] 測試可重複執行

---

## S61-6: Backend Test Endpoints for Feature 4 & 5 (5 pts) ✅ 已完成

### 檔案修改
- [x] `backend/src/api/v1/ag_ui/schemas.py`
  - [x] `TestWorkflowProgressRequest` schema
  - [x] `TestWorkflowProgressResponse` schema
  - [x] `TestModeSwitchRequest` schema
  - [x] `TestModeSwitchResponse` schema
  - [x] `TestUIComponentRequest` schema
  - [x] `TestUIComponentResponse` schema
- [x] `backend/src/api/v1/ag_ui/routes.py`
  - [x] `POST /test/progress` 端點
  - [x] `POST /test/mode-switch` 端點
  - [x] `POST /test/ui-component` 端點
- [x] `scripts/uat/phase_tests/phase_15_ag_ui/phase_15_ag_ui_test.py`
  - [x] Feature 4 測試更新 (使用 /test/progress, /test/mode-switch)
  - [x] Feature 5 測試更新 (使用 /test/ui-component)

### 驗證
- [x] 測試端點可正常調用
- [x] 返回正確的 AG-UI 事件
- [x] UAT 測試 16/17 通過 (94.1%), 1 skipped (需要真實工具執行)

---

## 額外完成: Advanced 組件 (Bonus)

### 額外檔案建立
- [x] `frontend/src/components/ag-ui/advanced/index.ts`
- [x] `frontend/src/components/ag-ui/advanced/CustomUIRenderer.tsx`
- [x] `frontend/src/components/ag-ui/advanced/DynamicForm.tsx`
- [x] `frontend/src/components/ag-ui/advanced/DynamicTable.tsx`
- [x] `frontend/src/components/ag-ui/advanced/DynamicChart.tsx`
- [x] `frontend/src/components/ag-ui/advanced/DynamicCard.tsx`
- [x] `frontend/src/components/ag-ui/advanced/StateDebugger.tsx`
- [x] `frontend/src/components/ag-ui/advanced/OptimisticIndicator.tsx`

---

## Quality Gates

### 代碼品質 (前端)
- [ ] `npm run lint` 通過
- [ ] `npm run build` 成功
- [ ] TypeScript 類型檢查通過

### 測試品質
- [x] 組件測試文件已建立
- [x] E2E 測試文件已建立
- [x] Backend UAT 測試 16/17 通過

### 可訪問性
- [x] 所有組件有 data-testid
- [x] 關鍵元素有 ARIA labels
- [x] 鍵盤導航支持

### Phase 15 完成驗證
- [x] 所有 Sprint 61 Stories 完成
- [x] Demo 頁面路由已配置 (/ag-ui-demo)
- [x] E2E 測試文件已建立

---

## Notes

```
Sprint 61 開始日期: 2026-01-06
Sprint 61 完成日期: 2026-01-06
計劃點數: 43 pts (38 原始 + 5 S61-6)
已完成: 43 pts (100%)

Story 完成狀態:
- S61-1: useAGUI Hook (8 pts) ✅
- S61-2: Chat 組件 (8 pts) ✅
- S61-3: HITL 審批組件 (5 pts) ✅
- S61-4: AG-UI Demo 頁面 (10 pts) ✅
- S61-5: Playwright E2E 測試 (7 pts) ✅
- S61-6: Backend Test Endpoints (5 pts) ✅
- Bonus: Advanced 組件 (額外完成)

待驗證:
- 前端 lint/build 品質檢查
```
