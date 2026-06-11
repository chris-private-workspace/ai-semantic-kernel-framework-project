# Sprint 88 決策記錄

## 決策列表

| 編號 | 日期 | 決策 | 原因 | 影響 |
|------|------|------|------|------|
| D88-1 | 2026-01-13 | 使用垂直時間線布局 | 更適合顯示長執行流程，易於滾動查看 | Timeline 組件 |
| D88-2 | 2026-01-13 | 事件配對使用視覺連接線 | 清楚顯示 request/response 關係 | TimelineNode 組件 |
| D88-3 | 2026-01-13 | 樹形結構使用遞歸渲染 | 支持任意層級的嵌套事件 | EventTree 組件 |
| D88-4 | 2026-01-13 | 事件面板使用工廠模式 | 根據事件類型動態選擇面板組件 | EventPanel 組件 |

---

## 詳細說明

### D88-1: 垂直時間線布局

**背景**: 需要直觀展示執行事件的時間順序

**選項分析**:
1. 垂直時間線 - 適合長流程，自然滾動體驗
2. 水平時間線 - 空間有限，不適合多事件
3. 甘特圖 - 複雜度高，學習成本大

**決策**: 選擇垂直時間線布局

**原因**:
- 適合展示大量事件
- 滾動方向自然（向下）
- 可以顯示更多事件詳情
- 與 Chrome DevTools 風格一致

---

### D88-2: 事件配對視覺化

**背景**: LLM_REQUEST/RESPONSE、TOOL_CALL/RESULT 等事件需要配對顯示

**決策**: 使用視覺連接線和背景色區分配對事件

**實現方式**:
- 配對事件使用相同的淡背景色
- 垂直連接線連接配對事件
- 持續時間條顯示在配對區間內

**原因**:
- 一眼識別相關事件
- 清晰展示 I/O 關係
- 便於追蹤執行流程

---

### D88-3: 遞歸樹形結構

**背景**: 事件可能有多層嵌套（Workflow → Executor → LLM → Tool）

**決策**: 使用遞歸組件渲染樹形結構

**數據結構**:
```typescript
interface TreeNode {
  event: TraceEvent;
  children: TreeNode[];
  depth: number;
  isExpanded: boolean;
}
```

**原因**:
- 支持任意層級嵌套
- 組件邏輯清晰
- 便於維護和擴展

---

### D88-4: 事件面板工廠模式

**背景**: 不同類型事件需要顯示不同的詳情內容

**決策**: 使用工廠模式根據事件類型選擇面板

**實現方式**:
```typescript
function EventPanel({ event }: { event: TraceEvent }) {
  switch (event.event_type) {
    case 'LLM_REQUEST':
    case 'LLM_RESPONSE':
      return <LLMEventPanel event={event} />;
    case 'TOOL_CALL':
    case 'TOOL_RESULT':
      return <ToolEventPanel event={event} />;
    default:
      return <DefaultEventPanel event={event} />;
  }
}
```

**原因**:
- 每種事件類型有專門的展示邏輯
- 易於添加新事件類型支持
- 關注點分離，代碼清晰

---

**創建日期**: 2026-01-13
**更新日期**: 2026-01-13
