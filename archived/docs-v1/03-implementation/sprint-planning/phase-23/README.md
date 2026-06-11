# Phase 23: 多 Agent 協調與主動巡檢

## Overview

Phase 23 專注於強化 Claude 在多 Agent 協作中的角色，實現 Agent to Agent (A2A) 通信協議，並建立主動巡檢模式以實現主動式 AI 能力。

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | 計劃中 |
| **Duration** | 2 sprints |
| **Total Story Points** | 42 pts |
| **Priority** | 🟡 P1 中優先 |
| **Target Start** | Phase 22 完成後 |

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 81** | Claude 主導的多 Agent 協調 | 26 pts | 計劃中 | [Plan](sprint-81-plan.md) / [Checklist](sprint-81-checklist.md) |
| **Sprint 82** | 主動巡檢與智能關聯 | 16 pts | 計劃中 | [Plan](sprint-82-plan.md) / [Checklist](sprint-82-checklist.md) |
| **Total** | | **42 pts** | | |

---

## 問題背景

### 現狀

1. **A2A 通信不完整**
   - 基礎 Agent 間通信已實現
   - 缺少 Agent 發現和能力宣告機制
   - 協議不標準化

2. **被動響應模式**
   - 系統只能被動響應事件
   - 無法主動發現和預防問題
   - 缺少定時巡檢能力

3. **關聯分析能力不足**
   - 單一事件處理為主
   - 缺少跨事件關聯推理
   - 根因分析能力有限

### 目標

- Claude 能協調多個 Agent 完成複雜任務
- A2A 通信協議完整且標準化
- 系統能主動巡檢並發現潛在問題
- 具備智能關聯和根因分析能力

---

## Features

### Sprint 81: Claude 主導的多 Agent 協調 (26 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S81-1 | Claude 主導的多 Agent 協調 | 10 pts | P1 |
| S81-2 | A2A 通信協議完善 | 8 pts | P1 |
| S81-3 | Claude + MAF 深度融合 | 8 pts | P1 |

### Sprint 82: 主動巡檢與智能關聯 (16 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S82-1 | 主動巡檢模式 | 8 pts | P1 |
| S82-2 | 智能關聯與根因分析 | 8 pts | P1 |

---

## Technical Details

### A2A 消息協議

```python
class A2AMessage(BaseModel):
    message_id: str
    from_agent: str
    to_agent: str
    type: MessageType  # TASK_REQUEST, TASK_RESPONSE, etc.
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]]
    timestamp: datetime
```

### API Endpoints

```
# A2A 通信
POST   /api/v1/a2a/message             # 發送 A2A 消息
GET    /api/v1/a2a/agents              # 獲取所有 Agent
POST   /api/v1/a2a/agents/register     # 註冊 Agent
POST   /api/v1/a2a/agents/discover     # 發現合適 Agent

# 主動巡檢
POST   /api/v1/patrol/trigger          # 手動觸發巡檢
GET    /api/v1/patrol/reports          # 獲取巡檢報告
GET    /api/v1/patrol/schedule         # 獲取巡檢計劃

# 智能關聯
POST   /api/v1/correlation/analyze     # 分析事件關聯
POST   /api/v1/rootcause/analyze       # 根因分析
```

---

## Dependencies

### Prerequisites
- Phase 22 completed (Claude 自主規劃 + mem0)
- MAF Adapters (Phase 3-6)

### New Dependencies
```bash
pip install schedule>=1.2.0
pip install networkx>=3.0
pip install apscheduler>=3.10.0
```

---

## Verification

### Sprint 81 驗證
- [ ] Claude 能協調 3+ Agent 完成任務
- [ ] A2A 消息正確路由
- [ ] Agent 發現和能力查詢正常

### Sprint 82 驗證
- [ ] 巡檢計劃按時執行
- [ ] 異常能被正確識別
- [ ] 根因分析準確率 > 70%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 多 Agent 協調成功率 | > 90% |
| A2A 消息傳遞延遲 | < 500ms |
| 主動巡檢問題發現率 | > 80% |
| 根因分析準確率 | > 70% |

---

**Created**: 2026-01-12
**Total Story Points**: 42 pts
