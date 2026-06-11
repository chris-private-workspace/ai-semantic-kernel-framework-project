# Sprint 83: WorkflowViz 與 Dashboard

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 83 |
| **Phase** | 24 - 前端完善與生態整合 |
| **Duration** | 5-7 days |
| **Story Points** | 18 pts |
| **Status** | 計劃中 |
| **Priority** | 🟢 P2 低優先 |

---

## Sprint Goal

實現 WorkflowViz 實時更新和 Claude 思考過程可視化，完善 Dashboard 自定義功能。

---

## Prerequisites

- Phase 23 完成（多 Agent 協調）✅
- 前端基礎（Phase 16-19）✅

---

## User Stories

### S83-1: WorkflowViz 實時更新 + Claude 思考過程可視化 (10 pts)

**Description**: 實現工作流可視化的實時更新，包括 Claude 思考過程展示。

**Acceptance Criteria**:
- [ ] 節點狀態實時更新（< 500ms 延遲）
- [ ] 執行路徑追蹤和高亮
- [ ] Claude 思考過程可視化（Extended Thinking）
- [ ] 支援節點詳情面板
- [ ] 支援縮放和平移

**Files to Create/Modify**:
- `frontend/src/components/workflow/WorkflowViz.tsx` (~300 行)
- `frontend/src/components/workflow/ThinkingPanel.tsx` (~150 行)
- `frontend/src/components/workflow/NodeDetailPanel.tsx` (~150 行)
- `frontend/src/hooks/useWorkflowUpdates.ts` (~100 行)

**Technical Design**:
```typescript
// WorkflowViz 組件
interface WorkflowVizProps {
  workflowId: string;
  onNodeClick?: (nodeId: string) => void;
}

const WorkflowViz: React.FC<WorkflowVizProps> = ({ workflowId, onNodeClick }) => {
  const { nodes, edges, updateState } = useWorkflowUpdates(workflowId);

  // 使用 @antv/g6 進行圖形渲染
  const graphRef = useRef<Graph>(null);

  useEffect(() => {
    // 監聽 WebSocket 更新
    const ws = new WebSocket(`/api/v1/workflow/${workflowId}/viz/stream`);
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      updateState(update);
    };
    return () => ws.close();
  }, [workflowId]);

  return (
    <div className="workflow-viz-container">
      <GraphCanvas ref={graphRef} nodes={nodes} edges={edges} />
      <ThinkingPanel />
      <NodeDetailPanel />
    </div>
  );
};
```

**API Endpoints**:
```
GET    /api/v1/workflow/{id}/viz        # 獲取可視化數據
WS     /api/v1/workflow/{id}/viz/stream # 實時更新 WebSocket
```

**Dependencies**:
```bash
npm install @antv/g6@5.x    # 圖形可視化
```

---

### S83-2: Dashboard 自定義 + 學習效果儀表板 (8 pts)

**Description**: 實現 Dashboard 自定義功能和學習效果儀表板。

**Acceptance Criteria**:
- [ ] 支援卡片拖放排序
- [ ] 支援卡片添加/移除
- [ ] 學習效果統計圖表
- [ ] mem0 記憶使用統計
- [ ] 布局持久化

**Files to Create/Modify**:
- `frontend/src/pages/dashboard/CustomizableDashboard.tsx` (~250 行)
- `frontend/src/components/dashboard/LearningMetrics.tsx` (~150 行)
- `frontend/src/components/dashboard/MemoryUsage.tsx` (~100 行)
- `frontend/src/components/dashboard/DraggableCard.tsx` (~100 行)

**Technical Design**:
```typescript
// CustomizableDashboard 組件
interface DashboardWidget {
  id: string;
  type: 'learning-metrics' | 'memory-usage' | 'execution-stats' | 'custom';
  position: { x: number; y: number };
  size: { width: number; height: number };
}

const CustomizableDashboard: React.FC = () => {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const { saveLayout, loadLayout } = useDashboardPersistence();

  // 拖放處理
  const handleDragEnd = (result: DropResult) => {
    const newWidgets = reorderWidgets(widgets, result);
    setWidgets(newWidgets);
    saveLayout(newWidgets);
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="dashboard">
        {(provided) => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            {widgets.map((widget, index) => (
              <DraggableCard key={widget.id} widget={widget} index={index} />
            ))}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
};
```

**Dependencies**:
```bash
npm install echarts@5.x           # 統計圖表
npm install react-beautiful-dnd   # 拖放功能
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] WorkflowViz 實時更新正常
- [ ] Dashboard 可自定義
- [ ] 響應式設計驗證通過
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| WorkflowViz 更新延遲 | < 500ms |
| Dashboard 加載時間 | < 2s |
| 用戶滿意度 | > 4/5 |

---

**Created**: 2026-01-12
**Story Points**: 18 pts
