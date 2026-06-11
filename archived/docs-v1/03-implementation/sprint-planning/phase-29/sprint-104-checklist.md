# Sprint 104 Checklist: ExtendedThinking + 工具調用展示優化

## 開發任務

### Story 104-1: 後端 Extended Thinking 支援
- [x] 修改 `ClaudeSDKClient` 支援 thinking 捕獲
- [x] 添加 `thinking_callback` 參數
- [x] 實現 thinking 事件處理
- [x] 確認 `SwarmTracker.add_worker_thinking()` (已存在)
- [x] 確認 `SwarmIntegration.on_thinking()` (已存在)
- [x] 確保向後兼容
- [x] 編寫單元測試

### Story 104-2: ExtendedThinkingPanel 主面板
- [x] 創建 `ExtendedThinkingPanel.tsx`
- [x] 實現展開/收起功能
- [x] 實現 ThinkingBlock 子組件
- [x] 實現自動滾動
- [x] 實現 Token 統計
- [x] 實現時間戳顯示
- [x] 添加動畫效果

### Story 104-3: 實時思考更新
- [x] 確認 `useSwarmEvents.ts` 處理 thinking 事件 (已存在)
- [x] 整合 ExtendedThinkingPanel 到 WorkerDetailDrawer
- [x] 優化重渲染性能

### Story 104-4: WorkerActionList 組件
- [x] 創建 `WorkerActionList.tsx`
- [x] 定義 ActionType 類型
- [x] 實現操作圖標映射
- [x] 實現操作顏色映射
- [x] 實現列表渲染
- [x] 實現點擊事件
- [x] 實現 metadata 顯示
- [x] 實現 inferActionType 工具函數

### Story 104-5: 增強工具調用展示
- [x] 添加狀態轉換動畫
- [x] 實現實時計時器 (useLiveTimer hook)
- [x] 實現流式輸出支援
- [x] 優化展開/收起動畫
- [x] 狀態感知的視覺樣式

### Story 104-6: 單元測試
- [x] 創建 `__tests__/ExtendedThinkingPanel.test.tsx`
- [x] 創建 `__tests__/WorkerActionList.test.tsx`
- [x] 創建 `backend/tests/unit/swarm/test_thinking_events.py`
- [x] 測試增量更新邏輯
- [x] 測試實時事件處理

## 品質檢查

### 代碼品質
- [ ] ESLint 檢查通過
- [ ] Prettier 格式化通過
- [ ] TypeScript 編譯通過
- [ ] Black 格式化通過 (後端)
- [ ] mypy 類型檢查通過 (後端)

### 測試
- [ ] 前端測試覆蓋率 > 85%
- [ ] 後端測試覆蓋率 > 90%
- [ ] 所有測試通過

### 性能
- [ ] 實時更新延遲 < 100ms
- [ ] 無明顯閃爍
- [ ] 滾動流暢

## 驗收標準

- [x] Extended Thinking 正確顯示
- [x] 實時更新正常工作
- [x] Token 統計正確
- [x] 操作列表正確渲染
- [x] 動畫效果流暢
- [ ] 測試覆蓋率達標

---

**Sprint 狀態**: ✅ 開發完成
**Story Points**: 28
**開始日期**: 2026-01-29
**完成日期**: 2026-01-29
