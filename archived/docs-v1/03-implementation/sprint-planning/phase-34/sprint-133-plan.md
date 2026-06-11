# Sprint 133: ReactFlow 工作流視覺化 + Phase 34 驗收

## 概述

Sprint 133 是 Phase 34 的最後一個 Sprint。實現 ReactFlow 工作流 DAG 視覺化，並進行 Phase 34 全面驗收，確認所有功能目標達成。

## 目標

1. 安裝並整合 ReactFlow (@xyflow/react)
2. 實現工作流 DAG 視覺化（節點 + 邊 + 互動）
3. Phase 34 全面驗收（功能 + 效能 + 覆蓋率）
4. 撰寫 Phase 34 完成報告

## Story Points: 30 點

## 前置條件

- ⬜ Sprint 132 完成
- ⬜ Phase 34 所有 P1/P2 功能已實現
- ⬜ 測試覆蓋率 ≥ 80%

## 任務分解

### Story 133-1: ReactFlow 安裝與基礎設定 (1 天, P3)

**交付物**:
- 安裝 `@xyflow/react` 套件
- 建立 ReactFlow 基礎元件
- 整合到現有前端路由

**安裝**:
```bash
cd frontend && npm install @xyflow/react
```

**檔案結構**:
```
frontend/src/components/workflow-editor/
├── WorkflowCanvas.tsx        # 主畫布元件
├── nodes/
│   ├── AgentNode.tsx         # Agent 節點
│   ├── ConditionNode.tsx     # 條件節點
│   ├── ActionNode.tsx        # 行動節點
│   └── StartEndNode.tsx      # 開始/結束節點
├── edges/
│   ├── DefaultEdge.tsx       # 預設邊
│   └── ConditionalEdge.tsx   # 條件邊
├── hooks/
│   ├── useWorkflowData.ts    # 工作流資料 hook
│   └── useNodeDrag.ts        # 節點拖拽 hook
└── utils/
    └── layoutEngine.ts       # 自動佈局（dagre）
```

### Story 133-2: 工作流 DAG 視覺化 (3 天, P3)

**目標**: 將 Workflow 定義轉換為視覺化 DAG

**節點類型**:

| 節點類型 | 視覺 | 用途 |
|---------|------|------|
| AgentNode | 藍色圓角矩形 | Agent 執行步驟 |
| ConditionNode | 菱形 | 分支條件 |
| ActionNode | 綠色矩形 | 系統行動 |
| StartNode | 圓形 | 工作流起點 |
| EndNode | 雙圓形 | 工作流終點 |

**互動功能**:
- 節點拖拽移動
- 節點點擊顯示詳情面板
- 邊點擊顯示條件配置
- 縮放與平移
- 自動佈局（dagre 演算法）
- 匯出為 JSON

### Story 133-3: 後端 API 整合 (1 天, P3)

**API 端點**:

| 端點 | 用途 |
|------|------|
| GET `/api/v1/workflows/{id}/graph` | 取得工作流 DAG 資料 |
| PUT `/api/v1/workflows/{id}/graph` | 儲存 DAG 佈局 |
| POST `/api/v1/workflows/{id}/graph/layout` | 自動佈局 |

**DAG 資料格式**:
```json
{
  "nodes": [
    {"id": "1", "type": "agent", "position": {"x": 0, "y": 0}, "data": {"label": "分類Agent"}}
  ],
  "edges": [
    {"id": "e1-2", "source": "1", "target": "2", "label": "INCIDENT"}
  ]
}
```

### Story 133-4: Phase 34 驗收 (2 天, P3)

**驗收項目**:

| 項目 | 驗收標準 | 來源 |
|------|---------|------|
| n8n 整合 | 3 種模式全部可用 | 改善提案 Phase D P1 |
| ADF MCP | Pipeline 觸發與監控 | 改善提案 Phase D P1 |
| IT 事件處理 | 端到端自動化流程 | 改善提案 Phase D P1 |
| LLMClassifier | 真實 LLM 調用，準確率 > 85% | 改善提案 Phase D P2 |
| D365 MCP | CRUD 操作正常 | 改善提案 Phase D P2 |
| Correlation/RootCause | 真實資料（非偽造） | 改善提案 Phase D P2 |
| MAF ACL | API 變更隔離 | 改善提案 Phase D P2 |
| 測試覆蓋率 | ≥ 80% | 改善提案 Phase D P2 |
| HybridOrchestratorV2 | Mediator 重構完成 | 改善提案 Phase D P3 |
| ReactFlow | DAG 視覺化可用 | 改善提案 Phase D P3 |
| 3+ 業務場景 | AD + IT 事件 + ETL | 改善提案成功標準 |
| 無 CRITICAL 問題 | Issue tracking | 改善提案成功標準 |

**交付物**:
- Phase 34 驗收報告
- 效能基準報告
- 覆蓋率報告（80%+）
- 剩餘 issues 清單

## 依賴

- 改善提案 Phase D P3: ReactFlow 工作流視覺化
- Phase 34 所有 Sprint 完成
