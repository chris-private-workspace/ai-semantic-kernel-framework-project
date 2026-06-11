# Phase 15 AG-UI Protocol UAT 測試

## 概覽

Phase 15 實現了 AG-UI Protocol 整合，提供 7 個核心功能用於 AI Agent 與前端的即時通訊。

**總 Story Points**: 85 pts
**狀態**: 已完成 (Sprint 58-60)

## 目錄結構

```
phase-15-agui/
├── README.md               # 本文件
├── uat-test-spec.md        # UAT 測試規格
├── uat-test-scenarios.md   # 詳細測試場景
├── uat-checklist.md        # 測試驗收清單
└── uat-report-template.md  # 測試報告模板
```

## 7 個 AG-UI 功能

| # | 功能 | 說明 | Sprint |
|---|------|------|--------|
| 1 | **Agentic Chat** | 即時對話 + 工具內嵌 | S59-1 |
| 2 | **Tool Rendering** | 工具結果自動檢測與渲染 | S59-2 |
| 3 | **Human-in-the-Loop** | 高風險操作審批 | S59-3 |
| 4 | **Generative UI** | 長時間操作進度顯示 | S59-4 |
| 5 | **Tool-based UI** | 動態組件 (Form/Chart/Card/Table) | S60-1 |
| 6 | **Shared State** | 雙向狀態同步 | S60-2 |
| 7 | **Predictive State** | 樂觀更新 + 自動回滾 | S60-3 |

## 相關代碼位置

### Backend
- `backend/src/api/v1/ag_ui/` - API 端點
- `backend/src/integrations/ag_ui/` - 核心組件
  - `bridge.py` - HybridEventBridge
  - `events/` - 15 種事件類型
  - `features/` - 7 個功能處理器
  - `thread/` - ThreadManager

### Frontend
- `frontend/src/types/ag-ui.ts` - 類型定義
- `frontend/src/hooks/useSharedState.ts` - 狀態同步 Hook
- `frontend/src/hooks/useOptimisticState.ts` - 樂觀更新 Hook
- `frontend/src/components/ag-ui/advanced/` - 動態 UI 組件

## 快速開始

```bash
# 啟動後端
cd backend && uvicorn main:app --reload --port 8000

# 啟動前端
cd frontend && npm run dev

# 運行 UAT 測試
cd scripts/uat/phase_tests/phase_15_ag_ui
python phase_15_ag_ui_test.py
```

## 文檔連結

- [AG-UI API 參考](../../docs/api/ag-ui-api-reference.md)
- [AG-UI 整合指南](../../docs/guides/ag-ui-integration-guide.md)
- [Phase 15 Sprint 規劃](../../docs/03-implementation/sprint-planning/phase-15/)
