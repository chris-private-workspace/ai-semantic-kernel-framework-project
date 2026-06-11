# Sprint 83 Checklist: WorkflowViz 與 Dashboard

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 2 |
| **Total Points** | 18 pts |
| **Completed** | 0 |
| **In Progress** | 0 |
| **Status** | 計劃中 |

---

## Stories

### S83-1: WorkflowViz 實時更新 (10 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 安裝 @antv/g6 可視化庫
- [ ] 創建 WorkflowViz 組件
  - [ ] 圖形初始化
  - [ ] 節點渲染
  - [ ] 邊渲染
- [ ] 實現 WebSocket 實時更新
  - [ ] 連接管理
  - [ ] 狀態同步
  - [ ] 重連機制
- [ ] 實現節點狀態渲染
  - [ ] 待執行狀態
  - [ ] 執行中狀態
  - [ ] 完成狀態
  - [ ] 失敗狀態
- [ ] 創建 ThinkingPanel 組件
  - [ ] Extended Thinking 展示
  - [ ] 思考過程動畫
- [ ] 創建 NodeDetailPanel 組件
  - [ ] 節點信息展示
  - [ ] 執行日誌
- [ ] 實現縮放和平移
- [ ] 測試延遲 < 500ms

**Acceptance Criteria**:
- [ ] 節點狀態實時更新
- [ ] 執行路徑追蹤
- [ ] Claude 思考可視化
- [ ] 節點詳情面板
- [ ] 縮放和平移

---

### S83-2: Dashboard 自定義 (8 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 安裝 echarts 和 react-beautiful-dnd
- [ ] 創建 CustomizableDashboard 組件
  - [ ] 布局管理
  - [ ] Widget 渲染
- [ ] 實現拖放排序
  - [ ] DragDropContext 配置
  - [ ] 拖放處理邏輯
- [ ] 實現卡片增刪
  - [ ] 添加 Widget 對話框
  - [ ] 刪除確認
- [ ] 創建 LearningMetrics 組件
  - [ ] Few-shot 學習效果圖表
  - [ ] 決策品質趨勢
- [ ] 創建 MemoryUsage 組件
  - [ ] mem0 使用統計
  - [ ] 記憶數量趨勢
- [ ] 實現布局持久化
  - [ ] 保存到 localStorage
  - [ ] 保存到後端 API

**Acceptance Criteria**:
- [ ] 卡片可拖放
- [ ] 卡片可增刪
- [ ] 學習效果圖表
- [ ] 記憶使用統計
- [ ] 布局保存

---

## Verification Checklist

### Functional Tests
- [ ] WorkflowViz 渲染正確
- [ ] 實時更新正常
- [ ] Dashboard 拖放正常
- [ ] 布局持久化正常

### Performance Tests
- [ ] 更新延遲 < 500ms
- [ ] 頁面加載 < 2s

### Responsive Tests
- [ ] 桌面端顯示正常
- [ ] 平板端顯示正常

---

**Last Updated**: 2026-01-12
