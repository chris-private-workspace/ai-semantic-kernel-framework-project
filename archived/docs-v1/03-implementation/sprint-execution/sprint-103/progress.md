# Sprint 103: WorkerDetailDrawer 詳情面板

## 概述

Sprint 103 專注於實現 Worker 詳情的 Drawer 滑出面板，這是查看單個 Worker 完整執行詳情的核心介面。

## 目標

1. 實現 WorkerDetailDrawer 主組件
2. 實現 WorkerHeader 標題欄
3. 實現 CurrentTask 任務描述組件
4. 實現 ToolCallsPanel 工具調用面板
5. 實現 ToolCallItem 單個工具調用組件
6. 實現 MessageHistory 對話歷史組件
7. 實現 CheckpointPanel 檢查點面板

## Story Points: 32 點

---

## Story 進度

### Story 103-1: useWorkerDetail Hook (4h, P0)

**狀態**: ⏳ 進行中

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/hooks/useWorkerDetail.ts`

**完成項目**:
- [ ] 實現 fetch 邏輯
- [ ] 支援輪詢更新
- [ ] 錯誤處理
- [ ] TypeScript 類型完整

---

### Story 103-2: WorkerHeader 組件 (3h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerHeader.tsx`

**完成項目**:
- [ ] 顯示 Worker 名稱和角色圖標
- [ ] 顯示狀態和進度
- [ ] 顯示類型標籤
- [ ] 返回按鈕正常工作

---

### Story 103-3: CurrentTask 組件 (2h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/CurrentTask.tsx`

**完成項目**:
- [ ] 正確顯示任務描述
- [ ] 支援長文本展開/收起
- [ ] 樣式符合設計規範

---

### Story 103-4: ToolCallItem 組件 (4h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/ToolCallItem.tsx`

**完成項目**:
- [ ] 正確顯示工具調用信息
- [ ] 支援展開/收起
- [ ] 輸入/輸出格式化正確
- [ ] 錯誤狀態正確顯示

---

### Story 103-5: ToolCallsPanel 組件 (3h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/ToolCallsPanel.tsx`

**完成項目**:
- [ ] 正確顯示工具調用數量
- [ ] 列表滾動正常
- [ ] 空狀態處理

---

### Story 103-6: MessageHistory 組件 (4h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/MessageHistory.tsx`

**完成項目**:
- [ ] 正確顯示各角色消息
- [ ] 支援展開/收起
- [ ] 消息時間戳顯示
- [ ] 長文本截斷

---

### Story 103-7: CheckpointPanel 組件 (2h, P1)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/CheckpointPanel.tsx`

**完成項目**:
- [ ] 顯示 Checkpoint ID
- [ ] 顯示 Backend 類型
- [ ] 恢復按鈕正常

---

### Story 103-8: WorkerDetailDrawer 主組件 (6h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerDetailDrawer.tsx`

**完成項目**:
- [ ] Drawer 正確打開/關閉
- [ ] 所有子組件正確渲染
- [ ] 加載狀態正確
- [ ] 錯誤處理正確
- [ ] 滾動正常
- [ ] 動畫流暢

---

### Story 103-9: 單元測試 (4h, P0)

**狀態**: ⏳ 待開始

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/__tests__/WorkerDetailDrawer.test.tsx`
- 其他組件測試文件

**完成項目**:
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] Mock API 正確

---

## 前置任務: UI 組件

### Sheet 組件

**狀態**: ⏳ 待創建

**交付物**:
- `frontend/src/components/ui/Sheet.tsx`

---

### Separator 組件

**狀態**: ⏳ 待創建

**交付物**:
- `frontend/src/components/ui/Separator.tsx`

---

## 品質檢查

### 代碼品質
- [ ] TypeScript 類型完整
- [ ] 遵循專案代碼風格
- [ ] 組件正確導出

### 測試
- [ ] 單元測試創建
- [ ] 測試覆蓋率 > 85%

---

## 文件結構

```
frontend/src/components/unified-chat/agent-swarm/
├── index.ts                     # 更新導出
├── hooks/
│   ├── index.ts                 # 更新導出
│   ├── useSwarmEvents.ts        # (Sprint 101)
│   └── useWorkerDetail.ts       # 新增
├── WorkerHeader.tsx             # 新增
├── CurrentTask.tsx              # 新增
├── ToolCallItem.tsx             # 新增
├── ToolCallsPanel.tsx           # 新增
├── MessageHistory.tsx           # 新增
├── CheckpointPanel.tsx          # 新增
├── WorkerDetailDrawer.tsx       # 新增
└── __tests__/                   # 更新
    ├── useWorkerDetail.test.ts
    ├── WorkerHeader.test.tsx
    ├── CurrentTask.test.tsx
    ├── ToolCallItem.test.tsx
    ├── ToolCallsPanel.test.tsx
    ├── MessageHistory.test.tsx
    ├── CheckpointPanel.test.tsx
    └── WorkerDetailDrawer.test.tsx

frontend/src/components/ui/
├── Sheet.tsx                    # 新增
└── Separator.tsx                # 新增
```

---

## 完成標準

- [ ] 所有 Story 完成
- [ ] 測試覆蓋率 > 85%
- [ ] 動畫流暢
- [ ] 代碼審查通過

---

## 開發日期

- **開始日期**: 2026-01-29
- **完成日期**: -
- **Story Points**: 0 / 32 完成 (0%)
