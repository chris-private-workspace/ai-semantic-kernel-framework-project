# Agent Framework 功能索引

UAT 測試涵蓋的 50 個 Agent Framework 功能清單。

---

## 功能清單

| # | 功能名稱 | 分類 |
|---|----------|------|
| 1 | 順序式 Agent 編排 | 核心編排 |
| 2 | 人機協作檢查點 | HITL |
| 3 | 跨系統連接器 | 整合 |
| 4 | 跨場景協作 (CS↔IT) | 整合 |
| 5 | Few-shot 學習 | AI 能力 |
| 6 | Agent 模板市場 | 資源管理 |
| 7 | DevUI 整合 | UI |
| 8 | n8n 觸發 | 整合 |
| 9 | Prompt 管理 | 資源管理 |
| 10 | 審計追蹤 | 監控 |
| 11 | Teams 通知 | 通知 |
| 12 | 監控儀表板 | 監控 |
| 13 | 現代 Web UI | UI |
| 14 | Redis 緩存 | 效能 |
| 15 | Concurrent 並行執行 | 核心編排 |
| 16 | Enhanced Gateway | 核心編排 |
| 17 | Collaboration Protocol | 協作 |
| 18 | GroupChat 群組聊天 | 協作 |
| 19 | Agent Handoff 交接 | 協作 |
| 20 | Multi-turn 多輪對話 | 對話 |
| 21 | Conversation Memory | 對話 |
| 22 | Dynamic Planning 動態規劃 | 規劃 |
| 23 | Autonomous Decision | 規劃 |
| 24 | Trial-and-Error 試錯 | 規劃 |
| 25 | Nested Workflows 嵌套工作流 | 核心編排 |
| 26 | Sub-workflow Execution | 核心編排 |
| 27 | Recursive Patterns | 核心編排 |
| 28 | GroupChat 投票系統 | 協作 |
| 29 | HITL Manage | HITL |
| 30 | Capability Matcher | 智能路由 |
| 31 | Context Transfer | 協作 |
| 32 | Handoff Service | 協作 |
| 33 | GroupChat Orchestrator | 協作 |
| 34 | Planning Adapter | 規劃 |
| 35 | Redis/Postgres Checkpoint | 效能 |
| 36 | 跨系統智能關聯 | 整合 |
| 37 | 主動巡檢模式 | 監控 |
| 38 | WorkflowViz | UI |
| 39 | Agent to Agent (A2A) | 協作 |
| 40 | mem0 (外部記憶系統) | 記憶 |
| 41 | devui (開發者 UI) | UI |
| 42 | 通知系統 | 通知 |
| 43 | 智能路由 | 智能路由 |
| 44 | Dashboard 統計卡片 | UI |
| 45 | 待審批管理頁面 | UI |
| 46 | 效能監控頁面 | UI |
| 47 | Agent 能力匹配器 | 智能路由 |
| 48 | 投票系統 | 協作 |
| 49 | HITL 功能擴展 | HITL |
| 50 | Termination 條件 | 核心編排 |

---

## 分類索引

### 核心編排 (7)
#1, #15, #16, #25, #26, #27, #50

### 協作 (10)
#17, #18, #19, #28, #31, #32, #33, #39, #48

### HITL (3)
#2, #29, #49

### 規劃 (4)
#22, #23, #24, #34

### 對話 (2)
#20, #21

### 記憶 (1)
#40

### 整合 (4)
#3, #4, #8, #36

### 智能路由 (3)
#30, #43, #47

### 效能 (2)
#14, #35

### UI (7)
#7, #13, #38, #41, #44, #45, #46

### 監控 (3)
#10, #12, #37

### 通知 (2)
#11, #42

### 資源管理 (2)
#6, #9

### AI 能力 (1)
#5

---

## 相關 API 模組

| 功能分類 | API 路徑 |
|----------|----------|
| 核心編排 | `backend/src/api/v1/workflows/`, `concurrent/`, `nested/` |
| 協作 | `backend/src/api/v1/groupchat/`, `handoff/` |
| HITL | `backend/src/api/v1/hitl/`, `checkpoints/` |
| 規劃 | `backend/src/api/v1/planning/` |
| 對話 | `backend/src/api/v1/multiturn/` |
| 整合 | `backend/src/api/v1/connectors/`, `scenarios/` |
| 智能路由 | `backend/src/api/v1/capability/`, `routing/` |
| LLM 服務 | `backend/src/integrations/llm/` |

---

## Phase 7 AI 自主決策能力更新

**狀態**: ✅ 完成 (2025-12-21)

Phase 7 為以下功能添加了 LLM 驅動的 AI 能力：

| 功能 | Phase 7 更新 | 狀態 |
|------|-------------|------|
| #22 Dynamic Planning | LLM 服務整合 | ✅ |
| #23 Autonomous Decision | AI 決策引擎 | ✅ |
| #24 Trial-and-Error | AI 錯誤學習 | ✅ |
| #34 Planning Adapter | LLM 注入支援 | ✅ |

### 新增 LLM 服務組件

| 組件 | 用途 | 位置 |
|------|------|------|
| LLMServiceProtocol | 統一接口 | `integrations/llm/protocol.py` |
| AzureOpenAILLMService | 生產環境 | `integrations/llm/azure_openai.py` |
| MockLLMService | 測試用 | `integrations/llm/mock.py` |
| CachedLLMService | 效能優化 | `integrations/llm/cached.py` |
| LLMServiceFactory | 工廠模式 | `integrations/llm/factory.py` |

### Phase 7 測試覆蓋

- **E2E 測試**: `tests/e2e/test_ai_autonomous_decision.py` (40 tests)
- **LLM 整合測試**: `tests/e2e/test_llm_integration.py` (20 tests)
- **效能測試**: `tests/performance/test_llm_performance.py` (21 tests)

### 詳細文檔

- [LLM 服務 README](../../backend/src/integrations/llm/README.md)
- [Phase 7 總結報告](../../docs/03-implementation/sprint-execution/phase-7-summary.md)
- [技術架構 §6](../../docs/02-architecture/technical-architecture.md)
