# Sprint 102 Checklist: AgentSwarmPanel + WorkerCard

## 開發任務

### Story 102-1: TypeScript 類型定義
- [ ] 創建 `frontend/src/components/unified-chat/agent-swarm/` 目錄
- [ ] 創建 `types/index.ts`
- [ ] 定義 `WorkerType` 類型
- [ ] 定義 `WorkerStatus` 類型
- [ ] 定義 `SwarmMode` 類型
- [ ] 定義 `SwarmStatus` 類型
- [ ] 定義 `ToolCallInfo` 接口
- [ ] 定義 `ThinkingContent` 接口
- [ ] 定義 `WorkerMessage` 接口
- [ ] 定義 `WorkerSummary` 接口
- [ ] 定義 `WorkerDetail` 接口
- [ ] 定義 `AgentSwarmStatus` 接口
- [ ] 定義所有組件 Props 接口

### Story 102-2: SwarmHeader 組件
- [ ] 創建 `SwarmHeader.tsx`
- [ ] 實現模式標籤顯示
- [ ] 實現狀態圖標和顏色
- [ ] 實現 Worker 數量顯示
- [ ] 實現開始時間顯示
- [ ] 響應式設計

### Story 102-3: OverallProgress 組件
- [ ] 創建 `OverallProgress.tsx`
- [ ] 實現進度條顯示
- [ ] 實現百分比顯示
- [ ] 實現狀態顏色
- [ ] 實現動畫效果

### Story 102-4: WorkerCard 組件
- [ ] 創建 `WorkerCard.tsx`
- [ ] 實現角色圖標映射
- [ ] 實現狀態配置
- [ ] 實現類型標籤
- [ ] 實現標題行
- [ ] 實現當前操作顯示
- [ ] 實現進度條
- [ ] 實現工具調用計數
- [ ] 實現查看按鈕
- [ ] 實現選中狀態
- [ ] 實現 hover 效果

### Story 102-5: WorkerCardList 組件
- [ ] 創建 `WorkerCardList.tsx`
- [ ] 實現列表渲染
- [ ] 實現滾動區域
- [ ] 實現空狀態
- [ ] 實現選中狀態傳遞

### Story 102-6: AgentSwarmPanel 主面板
- [ ] 創建 `AgentSwarmPanel.tsx`
- [ ] 整合 SwarmHeader
- [ ] 整合 OverallProgress
- [ ] 整合 WorkerCardList
- [ ] 實現加載狀態
- [ ] 實現空狀態
- [ ] 創建 `index.ts` 導出文件

### Story 102-7: SwarmStatusBadges 組件
- [ ] 創建 `SwarmStatusBadges.tsx`
- [ ] 實現徽章渲染
- [ ] 實現狀態圖標
- [ ] 實現 Tooltip
- [ ] 實現點擊事件

### Story 102-8: 單元測試
- [ ] 創建 `__tests__/` 目錄
- [ ] 創建 `SwarmHeader.test.tsx`
- [ ] 創建 `OverallProgress.test.tsx`
- [ ] 創建 `WorkerCard.test.tsx`
- [ ] 創建 `WorkerCardList.test.tsx`
- [ ] 創建 `AgentSwarmPanel.test.tsx`
- [ ] 創建 `SwarmStatusBadges.test.tsx`

## 品質檢查

### 代碼品質
- [ ] ESLint 檢查通過
- [ ] Prettier 格式化通過
- [ ] TypeScript 編譯通過
- [ ] 無 any 類型

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] 快照測試正確

### 設計
- [ ] 響應式設計正確
- [ ] 深色模式支援
- [ ] Accessibility 檢查通過

## 驗收標準

- [ ] AgentSwarmPanel 正確顯示 Swarm 狀態
- [ ] WorkerCard 正確顯示 Worker 信息
- [ ] 狀態變化時 UI 正確更新
- [ ] 點擊事件正常工作
- [ ] 測試覆蓋率 > 85%

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 30
**開始日期**: 2026-02-13
