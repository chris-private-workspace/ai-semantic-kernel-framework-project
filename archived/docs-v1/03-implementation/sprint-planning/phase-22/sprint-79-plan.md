# Sprint 79: Claude 自主規劃引擎 + mem0 整合

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 79 |
| **Phase** | 22 - Claude 自主能力與學習系統 |
| **Duration** | 5-7 days |
| **Story Points** | 23 pts |
| **Status** | 計劃中 |
| **Priority** | 🔴 P0 高優先 |

---

## Sprint Goal

實現 Claude 自主規劃引擎和 mem0 長期記憶整合，讓 Claude 從「Tool 執行者」升級為「自主規劃者」。

---

## Prerequisites

- Phase 21 完成（沙箱安全架構）✅
- Claude SDK 基礎整合（Phase 12）✅
- Redis + PostgreSQL 基礎設施 ✅

---

## User Stories

### S79-1: Claude 自主規劃引擎 (13 pts)

**Description**: 實現 Claude 自主規劃引擎，讓 Claude 能夠自主分析、規劃、執行和驗證複雜任務。

**Background**:
目前 Claude 僅作為「Tool 執行者」，被動接收指令並執行。需要升級為能夠自主規劃的角色。

**Acceptance Criteria**:
- [ ] 實現「分析 → 規劃 → 執行 → 驗證」閉環流程
- [ ] Claude 能主動分析 IT 事件並生成處理規劃
- [ ] Extended Thinking 深度整合（動態 budget_tokens 調整）
- [ ] 規劃步驟可追溯和可解釋
- [ ] 支援複雜度評估和資源預估

**Technical Design**:

```python
# 動態 budget_tokens 調整策略
async def calculate_budget_tokens(event_complexity: str) -> int:
    complexity_map = {
        "simple": 4096,      # 簡單事件
        "moderate": 8192,    # 中等複雜
        "complex": 16000,    # 複雜事件
        "critical": 32000,   # 關鍵事件
    }
    return complexity_map.get(event_complexity, 8192)
```

**Files to Create**:
- `backend/src/integrations/claude_sdk/autonomous/__init__.py`
- `backend/src/integrations/claude_sdk/autonomous/planner.py` (~250 行)
- `backend/src/integrations/claude_sdk/autonomous/analyzer.py` (~150 行)
- `backend/src/integrations/claude_sdk/autonomous/executor.py` (~200 行)
- `backend/src/integrations/claude_sdk/autonomous/verifier.py` (~100 行)
- `backend/src/api/v1/claude_sdk/autonomous.py` (~100 行)

**API Endpoints**:
```
POST   /api/v1/claude/autonomous/plan     # 生成自主規劃
GET    /api/v1/claude/autonomous/{id}     # 獲取規劃狀態
POST   /api/v1/claude/autonomous/{id}/execute  # 執行規劃
```

---

### S79-2: mem0 長期記憶整合 (10 pts)

**Description**: 整合 mem0 SDK 實現 AI 助手的長期記憶能力，讓系統能夠從歷史事件學習。

**Background**:
目前系統每次會話都是「全新開始」，無法記住用戶偏好和系統知識。需要建立三層記憶架構。

**Acceptance Criteria**:
- [ ] mem0 Python SDK 成功整合
- [ ] Qdrant 向量存儲配置完成（本地部署）
- [ ] 三層記憶架構實現（工作記憶 + 會話記憶 + 長期記憶）
- [ ] 事件處理記憶存儲和檢索
- [ ] 相似事件自動關聯
- [ ] 記憶檢索準確率 > 80%

**Technical Design**:

```python
from mem0 import Memory

# 初始化 mem0 (使用本地 Qdrant)
memory = Memory(
    vector_store={
        "provider": "qdrant",
        "config": {"path": "/data/mem0/qdrant"}
    },
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
)
```

**三層記憶架構**:
```
Layer 1: 工作記憶 (Redis)           ← 已實現 ✅
Layer 2: 會話記憶 (PostgreSQL)      ← 已實現 ✅
Layer 3: 長期記憶 (mem0 + Qdrant)   ← 本 Sprint 實現 🆕
```

**Files to Create**:
- `backend/src/integrations/memory/__init__.py`
- `backend/src/integrations/memory/mem0_client.py` (~200 行)
- `backend/src/integrations/memory/unified_memory.py` (~150 行)
- `backend/src/integrations/memory/embeddings.py` (~100 行)
- `backend/src/api/v1/memory/routes.py` (~100 行)

**API Endpoints**:
```
POST   /api/v1/memory/add                 # 添加記憶
GET    /api/v1/memory/search              # 搜索記憶
GET    /api/v1/memory/user/{user_id}      # 獲取用戶記憶
DELETE /api/v1/memory/{id}                # 刪除記憶
```

**Dependencies**:
```bash
pip install mem0ai>=1.0.1
pip install qdrant-client>=1.7.0
pip install openai>=1.0.0  # 用於嵌入模型
```

---

## Technical Architecture

### Claude 自主規劃引擎架構

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Claude 自主規劃引擎架構                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  輸入層                                                                              │
│  ═══════                                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                             │
│  │ IT 事件     │    │ 用戶請求    │    │ 系統告警    │                             │
│  │ (ServiceNow)│    │ (Chat)      │    │ (Prometheus)│                             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                             │
│         │                  │                  │                                     │
│         └──────────────────┼──────────────────┘                                     │
│                            ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Claude 自主規劃引擎                                    │   │
│  │                                                                             │   │
│  │   Phase 1: 分析 → Extended Thinking (動態 budget_tokens)                    │   │
│  │   Phase 2: 規劃 → 自主決策樹生成                                             │   │
│  │   Phase 3: 執行 → 調用 MAF Workflow / Claude Tools                          │   │
│  │   Phase 4: 驗證 → 結果驗證和學習                                             │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] Claude 能接收 IT 事件並自主生成處理規劃
- [ ] Extended Thinking 輸出包含分析和規劃步驟
- [ ] mem0 SDK 成功初始化和連接
- [ ] 能存儲和檢索記憶
- [ ] 單元測試覆蓋率 > 80%
- [ ] API 文檔更新

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Extended Thinking 品質不穩定 | High | Low | 動態調整 budget_tokens |
| mem0 成本超預算 | High | Medium | 使用本地 Qdrant 替代雲服務 |
| 向量嵌入 API 限制 | Medium | Medium | 批量處理 + 緩存 |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Claude 自主規劃成功率 | > 80% |
| Extended Thinking 品質評分 | > 4/5 |
| mem0 記憶檢索準確率 | > 80% |
| 響應時間（規劃生成） | < 10s |

---

**Created**: 2026-01-12
**Story Points**: 23 pts
