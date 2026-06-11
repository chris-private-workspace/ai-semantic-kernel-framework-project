# Sprint 133 Checklist: ReactFlow 工作流視覺化 + Phase 34 驗收

## 開發任務

### Story 133-1: ReactFlow 安裝與基礎設定
- [ ] 安裝 `@xyflow/react` 套件
- [ ] 安裝 `dagre`（自動佈局）
- [ ] 建立 `frontend/src/components/workflow-editor/` 目錄
- [ ] 實現 `WorkflowCanvas.tsx` 主畫布
  - [ ] ReactFlow Provider 設定
  - [ ] 控制面板（縮放、全螢幕）
  - [ ] 小地圖
- [ ] 設定前端路由 `/workflows/{id}/editor`

### Story 133-2: 工作流 DAG 視覺化
- [ ] 實現自訂節點
  - [ ] `nodes/AgentNode.tsx` — Agent 執行節點
  - [ ] `nodes/ConditionNode.tsx` — 條件分支節點
  - [ ] `nodes/ActionNode.tsx` — 系統行動節點
  - [ ] `nodes/StartEndNode.tsx` — 開始/結束節點
- [ ] 實現自訂邊
  - [ ] `edges/DefaultEdge.tsx` — 預設連線
  - [ ] `edges/ConditionalEdge.tsx` — 條件連線
- [ ] 實現 hooks
  - [ ] `hooks/useWorkflowData.ts` — 工作流資料轉換
  - [ ] `hooks/useNodeDrag.ts` — 節點拖拽
- [ ] 實現自動佈局
  - [ ] `utils/layoutEngine.ts` — dagre 佈局引擎
  - [ ] 水平/垂直佈局切換
- [ ] 互動功能
  - [ ] 節點拖拽移動
  - [ ] 節點點擊顯示詳情
  - [ ] 邊點擊顯示條件
  - [ ] 縮放與平移
  - [ ] 匯出為 JSON

### Story 133-3: 後端 API 整合
- [ ] 實現 DAG API 端點
  - [ ] GET `/api/v1/workflows/{id}/graph`
  - [ ] PUT `/api/v1/workflows/{id}/graph`
  - [ ] POST `/api/v1/workflows/{id}/graph/layout`
- [ ] 工作流定義 → DAG 資料轉換
- [ ] DAG 佈局持久化

### Story 133-4: Phase 34 驗收
- [ ] 功能驗收
  - [ ] n8n 三種模式 E2E
  - [ ] ADF Pipeline 觸發/監控
  - [ ] IT 事件處理全流程
  - [ ] LLMClassifier 真實調用
  - [ ] D365 MCP CRUD
  - [ ] Correlation/RootCause 真實資料
  - [ ] MAF ACL 隔離
  - [ ] HybridOrchestratorV2 Mediator
  - [ ] ReactFlow DAG 視覺化
- [ ] 品質驗收
  - [ ] 測試覆蓋率 ≥ 80%
  - [ ] 無 CRITICAL 已知問題
  - [ ] 3+ 業務場景可用
- [ ] 效能驗收
  - [ ] API 回應時間基準
  - [ ] 並發處理能力
- [ ] 文件
  - [ ] Phase 34 驗收報告
  - [ ] 效能基準報告
  - [ ] 覆蓋率報告
  - [ ] 剩餘 issues 清單

## 驗證標準

- [ ] ReactFlow DAG 視覺化完整可用
- [ ] Phase 34 所有 P1/P2/P3 功能驗收通過
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 月節省 > $10,000（預估）
- [ ] 無 CRITICAL 已知問題
- [ ] Phase 34 驗收報告完成
