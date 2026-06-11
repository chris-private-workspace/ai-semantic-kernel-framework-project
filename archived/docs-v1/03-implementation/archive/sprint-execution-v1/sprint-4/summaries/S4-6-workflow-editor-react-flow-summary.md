# S4-6: Workflow Editor UI (React Flow) - 實現摘要

**Story ID**: S4-6
**標題**: Workflow Editor UI (React Flow)
**Story Points**: 13
**狀態**: ✅ 已完成
**完成日期**: 2025-11-26

---

## 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 可視化工作流編輯器 | ✅ | React Flow canvas 含 MiniMap、Controls、Background |
| 拖拽添加步驟 | ✅ | 左側 NodePalette 支援拖拽添加 8 種節點類型 |
| 連接步驟 | ✅ | 動畫連線、條件節點雙輸出（Yes/No） |
| 配置每個步驟參數 | ✅ | 右側 NodeConfigPanel 顯示類型特定配置 |
| 保存和發布工作流 | ✅ | Save Draft + Publish 功能，含驗證 |

---

## 技術實現

### 架構

```
frontend/src/features/workflows/
├── WorkflowEditorPage.tsx     # 主編輯頁面
└── editor/
    ├── index.ts               # 模組導出
    ├── nodeTypes.ts           # 節點類型定義
    ├── CustomNode.tsx         # 自定義節點組件
    ├── NodePalette.tsx        # 節點面板（拖拽源）
    ├── NodeConfigPanel.tsx    # 節點配置面板
    └── WorkflowCanvas.tsx     # React Flow 畫布
```

### 節點類型

| 類型 | 圖標 | 顏色 | 輸入 | 輸出 | 說明 |
|-----|------|------|------|------|------|
| trigger | ▶️ | #22c55e | 0 | 1 | 觸發器（Manual/Schedule/Webhook/Event） |
| action | ⚡ | #3b82f6 | 1 | 1 | 動作（HTTP/Email/Database/Transform） |
| condition | 🔀 | #f59e0b | 1 | 2 | 條件判斷（Yes/No 雙輸出） |
| loop | 🔁 | #8b5cf6 | 1 | 2 | 迴圈處理 |
| agent | 🤖 | #ec4899 | 1 | 1 | AI Agent（GPT-4o/4o-mini/3.5-turbo） |
| webhook | 🌐 | #06b6d4 | 1 | 1 | 外部 Webhook 調用 |
| delay | ⏱️ | #64748b | 1 | 1 | 延遲等待 |
| end | 🏁 | #ef4444 | 1 | 0 | 流程結束 |

### 關鍵組件

#### WorkflowCanvas.tsx
```typescript
// 主要功能
- ReactFlow 整合（useNodesState, useEdgesState）
- 拖放處理（onDragStart, onDragOver, onDrop）
- 節點連接（onConnect）
- 節點選取和配置
- readOnly 模式支持
- MiniMap 帶顏色編碼
- 網格吸附（15px）
```

#### CustomNode.tsx
```typescript
export interface CustomNodeData {
  label: string
  type: NodeType
  config?: Record<string, unknown>
  [key: string]: unknown  // React Flow 類型兼容
}

// 功能
- 顯示圖標和標籤
- 輸入/輸出 Handle
- 條件節點雙輸出（綠色 Yes / 紅色 No）
- 選取狀態高亮
```

#### NodeConfigPanel.tsx
```typescript
// 類型特定配置
- trigger: triggerType (manual/schedule/webhook/event)
- action: actionType (http/email/database/transform), params (JSON)
- condition: field, operator, value
- agent: model (GPT variants), systemPrompt
- webhook: url, method (GET/POST/PUT/PATCH/DELETE)
- delay: duration, unit (seconds/minutes/hours)
- loop: itemsPath, loopVariable
```

#### WorkflowEditorPage.tsx
```typescript
// 主要功能
- 工作流加載/創建（useQuery, useMutation）
- 定義轉換（definitionToFlow, flowToDefinition）
- 保存草稿（handleSave）
- 發布工作流（handlePublish）
- 發布驗證（canPublish）
  - 需要至少一個 Trigger 節點
  - 需要至少一個 End 節點
  - 需要工作流名稱
```

### 數據轉換

```typescript
// React Flow → Workflow Definition
function flowToDefinition(nodes: Node[], edges: Edge[]): Workflow['definition'] {
  return {
    nodes: nodes.map(node => ({
      id: node.id,
      type: (node.data as CustomNodeData).type,
      position: node.position,
      data: {
        label: (node.data as CustomNodeData).label,
        nodeType: (node.data as CustomNodeData).type,
        config: (node.data as CustomNodeData).config || {},
      },
    })),
    edges: edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
    })),
  }
}
```

---

## 依賴項

```json
{
  "@xyflow/react": "^12.x"
}
```

---

## TypeScript 類型兼容性

### 問題
- `@xyflow/react` 要求節點數據實現 `Record<string, unknown>`
- TanStack Query v5 移除了 `onSuccess` callback

### 解決方案
```typescript
// CustomNodeData 添加 index signature
export interface CustomNodeData {
  label: string
  type: NodeType
  config?: Record<string, unknown>
  [key: string]: unknown  // 兼容 @xyflow/react 類型約束
}

// 使用 useEffect 替代 onSuccess
useEffect(() => {
  if (workflowData) {
    setName(workflowData.name)
    // ...
  }
}, [workflowData])
```

---

## UI 特性

- **拖放操作**: 從左側面板拖拽節點到畫布
- **連線動畫**: 動態連線效果
- **MiniMap**: 右下角顯示工作流縮略圖
- **控制面板**: 縮放、居中、全屏控制
- **網格背景**: 點狀網格，15px 間距
- **網格吸附**: 節點對齊網格
- **鍵盤刪除**: Delete/Backspace 刪除選中節點
- **未保存提示**: "Unsaved" 標籤顯示

---

## 驗證邏輯

發布工作流需滿足以下條件：
1. ✅ 工作流名稱不為空
2. ✅ 至少包含一個 Trigger 節點
3. ✅ 至少包含一個 End 節點

不滿足時顯示詳細錯誤提示。

---

## 代碼位置

```
frontend/src/
├── api/
│   └── workflows.ts               # Workflow API 服務
└── features/
    └── workflows/
        ├── WorkflowEditorPage.tsx # 編輯頁面
        └── editor/
            ├── index.ts           # 導出
            ├── nodeTypes.ts       # 節點類型定義
            ├── CustomNode.tsx     # 自定義節點
            ├── NodePalette.tsx    # 節點面板
            ├── NodeConfigPanel.tsx# 配置面板
            └── WorkflowCanvas.tsx # React Flow 畫布
```

---

## 測試覆蓋

| 測試文件 | 測試數量 | 狀態 |
|---------|---------|------|
| 單元測試 | 待 S4-10 | ⏳ |
| E2E 測試 | 待 S4-10 | ⏳ |

### 構建驗證
- ✅ `npm run build` 成功
- ✅ TypeScript 編譯無錯誤
- ✅ 產出文件大小：
  - CSS: 42.83 kB (gzip: 8.13 kB)
  - JS: 653.21 kB (gzip: 209.96 kB)
- ⚠️ Chunk 大小警告（>500KB）- 可考慮動態導入優化

---

## 性能考量

- React Flow 使用 memo 優化渲染
- CustomNode 使用 `memo` HOC
- 大型工作流建議使用虛擬化
- 未來可考慮代碼分割 (`@xyflow/react` 懶加載)

---

## 相關文檔

- [Sprint 規劃](../../sprint-planning/sprint-4-ui-frontend.md)
- [S4-5 Workflow List 摘要](./S4-5-workflow-list-summary.md)
- [React Flow 文檔](https://reactflow.dev/)

---

**生成日期**: 2025-11-26
