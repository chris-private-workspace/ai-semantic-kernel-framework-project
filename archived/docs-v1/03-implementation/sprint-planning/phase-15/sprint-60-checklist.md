# Sprint 60 Checklist: AG-UI Advanced Features (5-7) + Integration

## Pre-Sprint Setup

- [x] 確認 Sprint 59 已完成
- [x] 確認 AgenticChatHandler 可用
- [x] 確認 ToolRenderingHandler 可用
- [x] 確認 HITLHandler 可用
- [x] 確認 GenerativeUIHandler 可用
- [x] 建立 `backend/src/integrations/ag_ui/features/advanced/` 目錄結構
- [x] 建立 `frontend/src/components/ag-ui/advanced/` 目錄結構

---

## S60-1: Tool-based Generative UI (8 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/advanced/__init__.py`
- [x] `backend/src/integrations/ag_ui/features/advanced/tool_ui.py`
  - [x] `UIComponentType` 枚舉 (form, chart, card, table, custom)
  - [x] `UIComponentDefinition` dataclass
  - [x] `ToolBasedUIHandler` 類別
  - [x] `emit_ui_component()` 方法
  - [x] `validate_component_schema()` 方法
  - [x] `_build_component_event()` 方法
  - [x] 整合 `CustomEvent`

### 檔案建立 (前端)
- [x] `frontend/src/components/ag-ui/advanced/CustomUIRenderer.tsx`
  - [x] 組件類型路由
  - [x] Schema 驗證
  - [x] 錯誤邊界處理
- [x] `frontend/src/components/ag-ui/advanced/DynamicForm.tsx`
  - [x] 動態表單生成
  - [x] 表單驗證
  - [x] 提交處理
- [x] `frontend/src/components/ag-ui/advanced/DynamicChart.tsx`
  - [x] 圖表類型選擇
  - [x] 數據格式化
  - [x] 響應式設計
- [x] `frontend/src/components/ag-ui/advanced/DynamicCard.tsx`
  - [x] 卡片佈局
  - [x] 圖標渲染
  - [x] 操作按鈕
- [x] `frontend/src/components/ag-ui/advanced/DynamicTable.tsx`
  - [x] 分頁功能
  - [x] 排序功能
  - [x] 篩選功能
- [x] `frontend/src/components/ag-ui/advanced/index.ts`

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/advanced/test_tool_ui.py`
- [x] `frontend/tests/components/ag-ui/advanced/CustomUIRenderer.test.tsx`
- [x] `frontend/tests/components/ag-ui/advanced/DynamicForm.test.tsx`
- [x] 組件渲染測試
- [x] Schema 驗證測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] UI 組件正確渲染
- [x] Schema 驗證正確執行
- [x] 錯誤狀態正確顯示
- [x] 各組件類型正確路由

---

## S60-2: Shared State (8 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/advanced/shared_state.py`
  - [x] `SharedStateHandler` 類別
  - [x] `emit_state_snapshot()` 方法
  - [x] `emit_state_delta()` 方法
  - [x] `StateSyncManager` 類別
  - [x] `_diff_state()` 方法
  - [x] `_merge_state()` 方法
  - [x] 整合 `StateSnapshotEvent`
  - [x] 整合 `StateDeltaEvent`

### API 端點
- [x] 修改 `backend/src/api/v1/ag_ui/routes.py`
  - [x] `GET /api/v1/ag-ui/threads/{thread_id}/state`
  - [x] `PATCH /api/v1/ag-ui/threads/{thread_id}/state`

### 檔案建立 (前端)
- [x] `frontend/src/hooks/useSharedState.ts`
  - [x] `state` 狀態
  - [x] `updateState()` 方法
  - [x] `subscribeToUpdates()` 方法
  - [x] 自動同步邏輯
- [x] `frontend/src/components/ag-ui/advanced/StateDebugger.tsx`
  - [x] 狀態顯示
  - [x] 變更歷史
  - [x] 即時更新

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/advanced/test_shared_state.py`
- [x] `backend/tests/unit/api/v1/ag_ui/test_state_routes.py`
- [x] `frontend/tests/hooks/useSharedState.test.ts`
- [x] Delta 計算測試
- [x] 狀態合併測試
- [x] 同步一致性測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] State Snapshot 正確發送
- [x] State Delta 正確計算
- [x] 前後端狀態同步
- [x] 同步延遲 < 50ms

---

## S60-3: Predictive State Updates (6 pts)

### 檔案建立 (後端)
- [x] `backend/src/integrations/ag_ui/features/advanced/predictive.py`
  - [x] `PredictiveStateHandler` 類別
  - [x] `predict_next_state()` 方法
  - [x] `confirm_prediction()` 方法
  - [x] `rollback_prediction()` 方法
  - [x] `_calculate_confidence()` 方法
  - [x] 整合 `StateDeltaEvent`

### 檔案建立 (前端)
- [x] `frontend/src/hooks/useOptimisticState.ts`
  - [x] `optimisticState` 狀態
  - [x] `applyOptimistic()` 方法
  - [x] `confirmOptimistic()` 方法
  - [x] `rollbackOptimistic()` 方法
  - [x] 版本追蹤
- [x] `frontend/src/components/ag-ui/advanced/OptimisticIndicator.tsx`
  - [x] 預測狀態顯示
  - [x] 確認/回滾 UI

### 測試
- [x] `backend/tests/unit/integrations/ag_ui/features/advanced/test_predictive.py`
- [x] `frontend/tests/hooks/useOptimisticState.test.ts`
- [x] 預測準確性測試
- [x] 回滾機制測試
- [x] 版本衝突處理測試
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 預測狀態正確應用
- [x] 確認後正確合併
- [x] 回滾後正確還原
- [x] 回滾延遲 < 100ms

---

## S60-4: Integration & E2E Testing (5 pts)

### E2E 測試建立
- [x] `backend/tests/e2e/ag_ui/test_full_flow.py`
  - [x] 完整對話流程測試
  - [x] 工具執行渲染測試
  - [x] 審批流程測試
  - [x] 進度更新測試
  - [x] 動態 UI 渲染測試
  - [x] 狀態同步測試
  - [x] 預測更新測試
- [x] `frontend/tests/e2e/ag-ui/full-flow.spec.ts`
  - [x] Playwright E2E 測試

### 效能測試
- [x] `backend/tests/performance/ag_ui/test_performance.py`
  - [x] SSE 串流吞吐量測試
  - [x] 狀態同步延遲測試
  - [x] 並發連接測試

### 效能指標驗證
- [x] 狀態同步延遲 < 50ms
- [x] 預測回滾延遲 < 100ms
- [x] UI 渲染延遲 < 200ms
- [x] SSE 吞吐量 > 1000 events/sec

### 文檔更新
- [x] `docs/api/ag-ui-api-reference.md`
  - [x] SSE 端點文檔
  - [x] Thread API 文檔
  - [x] State API 文檔
  - [x] Approvals API 文檔
- [x] `docs/guides/ag-ui-integration-guide.md`
  - [x] 整合指南
  - [x] 前端組件使用說明
  - [x] 最佳實踐

### 驗證
- [x] 所有 E2E 測試通過
- [x] 效能指標達標
- [x] API 文檔完整
- [x] 整合指南可用

---

## Quality Gates

### 代碼品質 (後端)
- [x] `black .` 格式化通過
- [x] `isort .` 導入排序通過
- [x] `flake8 .` 無錯誤
- [x] `mypy .` 類型檢查通過

### 代碼品質 (前端)
- [x] `npm run lint` 通過
- [x] `npm run build` 成功
- [x] TypeScript 類型檢查通過

### 測試品質
- [x] 後端單元測試全部通過
- [x] 前端組件測試全部通過
- [x] E2E 測試全部通過
- [x] 效能測試達標
- [x] 覆蓋率 > 85%

### Phase 15 完成驗證
- [x] 所有 7 個 AG-UI 功能已實現
- [x] API 文檔完整
- [x] 整合指南完成
- [x] 效能指標達標

---

## Notes

```
Sprint 60 開始日期: 2026-01-05
Sprint 60 結束日期: 2026-01-05
實際完成點數: 27 / 27 pts ✅

Phase 15 總計: 85 / 85 pts ✅
```

---

## 補充: UI 組件擴展 (2026-01-06)

### 新增 Shadcn UI 組件

為支援 Sprint 60 advanced 組件 (DynamicForm, DynamicChart, DynamicCard, DynamicTable)，
需要安裝和創建以下 Radix UI 基礎組件：

**安裝的依賴**:
```bash
npm install @radix-ui/react-checkbox @radix-ui/react-radio-group @radix-ui/react-collapsible
```

**新增的 UI 組件**:
| 檔案 | 用途 | Radix 依賴 |
|------|------|------------|
| `frontend/src/components/ui/Checkbox.tsx` | 表單複選框 | @radix-ui/react-checkbox |
| `frontend/src/components/ui/RadioGroup.tsx` | 單選按鈕組 | @radix-ui/react-radio-group |
| `frontend/src/components/ui/Table.tsx` | 表格組件 | 純 HTML |
| `frontend/src/components/ui/Tooltip.tsx` | 提示工具 | @radix-ui/react-tooltip |
| `frontend/src/components/ui/Collapsible.tsx` | 可折疊區塊 | @radix-ui/react-collapsible |
| `frontend/src/components/ui/Select.tsx` | 下拉選單 (Radix + 向後兼容) | @radix-ui/react-select |

**Select 組件向後兼容**:
- 新增 `Select`, `SelectTrigger`, `SelectContent`, `SelectItem` (Radix UI API)
- 保留 `SimpleSelect` 用於舊頁面向後兼容

**修改的檔案**:
- `src/pages/agents/CreateAgentPage.tsx` - 改用 SimpleSelect
- `src/pages/agents/EditAgentPage.tsx` - 改用 SimpleSelect
- `src/pages/workflows/CreateWorkflowPage.tsx` - 改用 SimpleSelect
- `src/pages/workflows/EditWorkflowPage.tsx` - 改用 SimpleSelect

**類型定義**:
- `frontend/src/vite-env.d.ts` - Vite ImportMeta 類型定義
