# Sprint 103 Checklist: WorkerDetailDrawer 詳情面板

## 開發任務

### Story 103-1: useWorkerDetail Hook
- [ ] 創建 `hooks/useWorkerDetail.ts`
- [ ] 實現 API 調用邏輯
- [ ] 實現輪詢更新
- [ ] 實現錯誤處理
- [ ] 添加 TypeScript 類型

### Story 103-2: WorkerHeader 組件
- [ ] 創建 `WorkerHeader.tsx`
- [ ] 實現返回按鈕
- [ ] 實現 Worker 名稱顯示
- [ ] 實現狀態和進度顯示
- [ ] 實現類型和角色標籤

### Story 103-3: CurrentTask 組件
- [ ] 創建 `CurrentTask.tsx`
- [ ] 實現任務描述顯示
- [ ] 實現文本截斷/展開
- [ ] 添加樣式

### Story 103-4: ToolCallItem 組件
- [ ] 創建 `ToolCallItem.tsx`
- [ ] 實現工具圖標 (MCP vs 普通)
- [ ] 實現狀態圖標和顏色
- [ ] 實現展開/收起功能
- [ ] 實現 Input JSON 格式化
- [ ] 實現 Output JSON 格式化
- [ ] 實現錯誤顯示
- [ ] 實現時間顯示

### Story 103-5: ToolCallsPanel 組件
- [ ] 創建 `ToolCallsPanel.tsx`
- [ ] 實現標題和計數
- [ ] 實現列表渲染
- [ ] 實現空狀態

### Story 103-6: MessageHistory 組件
- [ ] 創建 `MessageHistory.tsx`
- [ ] 實現消息列表渲染
- [ ] 實現角色標識
- [ ] 實現時間戳顯示
- [ ] 實現展開/收起
- [ ] 實現長文本截斷

### Story 103-7: CheckpointPanel 組件
- [ ] 創建 `CheckpointPanel.tsx`
- [ ] 實現 Checkpoint ID 顯示
- [ ] 實現 Backend 類型顯示
- [ ] 實現恢復按鈕

### Story 103-8: WorkerDetailDrawer 主組件
- [ ] 創建 `WorkerDetailDrawer.tsx`
- [ ] 整合 useWorkerDetail Hook
- [ ] 整合 WorkerHeader
- [ ] 整合 CurrentTask
- [ ] 整合 ToolCallsPanel
- [ ] 整合 MessageHistory
- [ ] 整合 CheckpointPanel
- [ ] 實現加載狀態
- [ ] 實現錯誤狀態
- [ ] 實現滾動區域
- [ ] 更新 index.ts 導出

### Story 103-9: 單元測試與整合測試
- [ ] 創建 `__tests__/useWorkerDetail.test.ts`
- [ ] 創建 `__tests__/WorkerHeader.test.tsx`
- [ ] 創建 `__tests__/CurrentTask.test.tsx`
- [ ] 創建 `__tests__/ToolCallItem.test.tsx`
- [ ] 創建 `__tests__/ToolCallsPanel.test.tsx`
- [ ] 創建 `__tests__/MessageHistory.test.tsx`
- [ ] 創建 `__tests__/CheckpointPanel.test.tsx`
- [ ] 創建 `__tests__/WorkerDetailDrawer.test.tsx`

## 品質檢查

### 代碼品質
- [ ] ESLint 檢查通過
- [ ] Prettier 格式化通過
- [ ] TypeScript 編譯通過
- [ ] 無 any 類型

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] Mock API 正確

### 設計
- [ ] Drawer 動畫流暢
- [ ] 響應式設計正確
- [ ] 深色模式支援

## 驗收標準

- [ ] Drawer 正確打開/關閉
- [ ] 所有子組件正確渲染
- [ ] 工具調用詳情展示正確
- [ ] 對話歷史展示正確
- [ ] 輪詢更新正常
- [ ] 測試覆蓋率 > 85%

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 32
**開始日期**: 2026-02-20
