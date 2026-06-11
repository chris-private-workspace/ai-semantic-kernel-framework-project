# Phase 24: 前端完善與生態整合

## Overview

Phase 24 專注於完善前端介面功能，包括 WorkflowViz 實時更新、Dashboard 自定義，以及 n8n 觸發整合和多級審批流程。

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | 計劃中 |
| **Duration** | 2 sprints |
| **Total Story Points** | 38 pts |
| **Priority** | 🟢 P2 低優先 |
| **Target Start** | Phase 23 完成後 |

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 83** | WorkflowViz 與 Dashboard | 18 pts | 計劃中 | [Plan](sprint-83-plan.md) / [Checklist](sprint-83-checklist.md) |
| **Sprint 84** | 生態整合與審批流程 | 20 pts | 計劃中 | [Plan](sprint-84-plan.md) / [Checklist](sprint-84-checklist.md) |
| **Total** | | **38 pts** | | |

---

## Features

### Sprint 83: WorkflowViz 與 Dashboard (18 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S83-1 | WorkflowViz 實時更新 + Claude 思考過程可視化 | 10 pts | P2 |
| S83-2 | Dashboard 自定義 + 學習效果儀表板 | 8 pts | P2 |

### Sprint 84: 生態整合與審批流程 (20 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S84-1 | n8n 觸發整合 | 8 pts | P2 |
| S84-2 | 多級審批流程 | 5 pts | P2 |
| S84-3 | 效能監控 + Claude 使用統計 | 5 pts | P2 |
| S84-4 | 短信/郵件通知整合 | 2 pts | P2 |

---

## Technical Details

### WorkflowViz 增強

- Claude 思考過程可視化
- 節點狀態實時更新
- 執行路徑追蹤

### n8n 整合

- Webhook 配置管理
- 雙向整合 (觸發 + 回饋)
- 工作流模板

### API Endpoints

```
# WorkflowViz
GET    /api/v1/workflow/{id}/viz        # 獲取可視化數據
WS     /api/v1/workflow/{id}/viz/stream # 實時更新

# Dashboard
GET    /api/v1/dashboard/stats          # 獲取統計數據
GET    /api/v1/dashboard/widgets        # 獲取自定義組件
PUT    /api/v1/dashboard/layout         # 更新佈局

# n8n 整合
POST   /api/v1/n8n/webhook              # n8n Webhook 端點
GET    /api/v1/n8n/workflows            # 獲取 n8n 工作流
POST   /api/v1/n8n/trigger              # 觸發 n8n 工作流
```

---

## Dependencies

### Prerequisites
- Phase 23 completed (多 Agent 協調)
- 前端基礎 (Phase 16-19)

### New Dependencies (Frontend)
```bash
npm install @antv/g6@5.x    # 圖形可視化
npm install echarts@5.x      # 統計圖表
```

---

## Verification

### Sprint 83 驗證
- [ ] WorkflowViz 實時更新延遲 < 500ms
- [ ] Claude 思考過程正確顯示
- [ ] Dashboard 自定義保存成功

### Sprint 84 驗證
- [ ] n8n 觸發成功率 > 99%
- [ ] 多級審批流程覆蓋所有場景
- [ ] 通知正確發送

---

## Success Metrics

| Metric | Target |
|--------|--------|
| WorkflowViz 更新延遲 | < 500ms |
| Dashboard 加載時間 | < 2s |
| n8n 觸發成功率 | > 99% |

---

**Created**: 2026-01-12
**Total Story Points**: 38 pts
