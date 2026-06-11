# Phase 2 Output: Sprint Planning 功能基準清單

> **用途**: 作為 Phase 3 源代碼全文閱讀的對照基準
> **來源**: 3 個 Agent 全文讀取 34 個 Phase 的 README.md + 關鍵計劃文件
> **詳細資料**:
>   - Phase 1-12: `archived/docs-v1/03-implementation/sprint-planning/PHASE-1-TO-12-PLANNING-SUMMARY.md`
>   - Phase 13-23: `claudedocs/phase-13-to-23-planning-summary.md`
>   - Phase 24-34: `archived/docs-v1/03-implementation/sprint-planning/PHASE-24-34-PLANNING-SUMMARY.md`

---

## 34 Phase 總覽

| Phase | 名稱 | Sprints | Story Points | 核心目標 | 目標代碼模組 |
|-------|------|---------|-------------|---------|-------------|
| 1 | Foundation & MVP | 0-6 | ~285 | 完整 MVP：Agent Framework 核心、CRUD、HITL、Connectors、Frontend | api/, domain/, frontend/ |
| 2 | Advanced Orchestration | 7-12 | ~222 | Concurrent、Handoff、GroupChat、Dynamic Planning、Nested Workflow | domain/orchestration/ |
| 3 | Official API Migration (Part 1) | 13-18 | ~160 | Phase 2 功能遷移到官方 MAF API（Adapter Pattern） | integrations/agent_framework/ |
| 4 | Official API Migration (Part 2) | 19-24 | ~165 | 完成 Adapter Pattern + Phase 1 核心遷移 | integrations/agent_framework/ |
| 5 | MVP Core Migration | 25-27 | ~100 | Phase 1 MVP 核心遷移（0% → 95%+ 官方 API 合規） | integrations/agent_framework/ |
| 6 | Migration Audit | 28-30 | ~75 | 遷移審計 + 最終合規驗證 | integrations/agent_framework/ |
| 7 | LLM Service Layer | 34-36 | ~58 | 發現 Phase 2 組件從未連接 LLM；建立 LLMService 抽象層 | integrations/llm/ |
| 8 | Code Interpreter | 37-38 | ~35 | Azure OpenAI Code Interpreter（Assistants API） | integrations/agent_framework/builders/ |
| 9 | MCP Architecture | 39-41 | ~110 | MCP 架構 + 3 層安全模型 + 5 個 MCP Server | integrations/mcp/ |
| 10 | Session Mode | 42-43 | ~95 | 即時對話的 Session Mode（雙模式架構） | domain/sessions/, api/v1/sessions/ |
| 11 | Agent-Session Integration | 45-47 | ~95 | AgentExecutor 統一執行介面 + Session-Agent 整合 | domain/sessions/, integrations/ |
| 12 | Claude Agent SDK | 48-50 | ~105 | Claude SDK 整合：HybridOrchestrator、Hooks、統一 API | integrations/claude_sdk/ |
| 13 | Hybrid Core Architecture | 52-54 | 105 | Intent Router + Context Bridge + HybridOrchestratorV2 | integrations/hybrid/ |
| 14 | Advanced Hybrid Features | 55-57 | 95 | Risk Assessment + Mode Switcher + Unified Checkpoint | integrations/hybrid/ |
| 15 | AG-UI Protocol | 58-61 | 123 | AG-UI SSE 協議 + 7 個核心功能 | integrations/ag_ui/, frontend/ag-ui/ |
| 16 | Unified Agentic Chat | 62-65 | ~100 | UnifiedChat 頁面 + 完整聊天 UI | frontend/pages/UnifiedChat, components/unified-chat/ |
| 17 | DevTools Backend API | 66-68 | ~72 | DevUI 後端 API + 執行追蹤 | api/v1/devtools/, domain/devtools/ |
| 18 | Authentication | 69-70 | ~46 | JWT Auth + Login/Signup + Guest UUID → Real User | api/v1/auth/, domain/auth/ |
| 19 | UI Polish | 71-72 | ~48 | 前端 UI 打磨 + 回應式設計 | frontend/ |
| 20 | File Attachment | 73-76 | ~60 | 檔案上傳/下載 + AG-UI 檔案附件 | api/v1/files/, integrations/ag_ui/ |
| 21 | Sandbox Security | 77-78 | ~48 | 進程級沙箱隔離 | core/sandbox/ |
| 22 | Claude Autonomous + Memory | 79-80 | ~54 | Claude 自主規劃 + mem0 記憶系統 | api/v1/autonomous/, integrations/memory/ |
| 23 | Multi-Agent Coordination | 81-82 | ~48 | A2A Protocol + Patrol 巡檢 + Correlation + RootCause | integrations/a2a,patrol,correlation,rootcause/ |
| 24 | Frontend Enhancement | 83-84 | ~38 | WorkflowViz + Dashboard + n8n 整合 | frontend/, api/v1/n8n/ |
| 25 | Production Scaling | 85-86 | ~40 | K8s 部署 + Prometheus/Grafana + 災備 | infrastructure/ (P3, 低優先) |
| 26 | DevUI Frontend | 87-89 | ~42 | DevUI 前端頁面（Tracing、Monitor、Settings） | frontend/pages/DevUI/ |
| 27 | mem0 Integration Polish | 90 | ~13 | mem0 完善 + 記憶搜索 UI | integrations/memory/ |
| 28 | Three-tier Intent Routing | 91-99 | 235 | 三層意圖路由（Pattern→Semantic→LLM）+ InputGateway + HITL + Dialog | integrations/orchestration/ |
| 29 | Agent Swarm | 100-106 | ~190 | 多 Agent Swarm 可視化 + SSE 追蹤 | integrations/swarm/, frontend/agent-swarm/ |
| 30 | Azure AI Search | 107-108 | ~30 | SemanticRouter Azure AI Search（已延後→Phase 32 吸收） | integrations/orchestration/ |
| 31 | Security Gate | 111-113 | ~78 | 安全加固（Auth 7%→100%、Mock 清理、Rate Limiting） | api/, core/auth, core/security/ |
| 32 | First Business Scenario | 114-118 | ~135 | AD 帳號管理場景 + ServiceNow Webhook + 真實 LLM | api/v1/orchestration/, integrations/ |
| 33 | Advanced Orchestration V2 | 119-123 | ~135 | 進階 Dialog Engine + Metrics + Memory + 測試 | integrations/orchestration/, integrations/memory/ |
| 34 | N8N + Mediator + ReactFlow | 124-133 | ~280 | n8n 整合 + HybridOrchestratorV2 Mediator + ReactFlow DAG + 測試 | integrations/n8n/, integrations/hybrid/, frontend/workflow-editor/ |

---

## 功能類別匯總（對標 V7 的 64+ 功能）

### A. Agent 編排能力 (Phase 1-6, 8)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| A1 | Agent CRUD + Framework Core | S1 | domain/agents/, api/v1/agents/ |
| A2 | Workflow Definition + Execution | S1-2 | domain/workflows/, api/v1/workflows/ |
| A3 | Tool Integration (ToolRegistry) | S1 | domain/agents/tools/ |
| A4 | Execution State Machine | S1 | domain/executions/ |
| A5 | Concurrent Execution (Fork-Join) | S7 | api/v1/concurrent/ |
| A6 | Agent Handoff | S8 | api/v1/handoff/ |
| A7 | GroupChat Multi-agent | S9 | api/v1/groupchat/ |
| A8 | Dynamic Planning | S10 | api/v1/planning/ |
| A9 | Nested Workflow | S11 | api/v1/nested/ |
| A10 | Code Interpreter | S37-38 | api/v1/code_interpreter/ |
| A11-A16 | MAF Builder Adapters (遷移) | S13-33 | integrations/agent_framework/builders/ |

### B. 人機協作能力 (Phase 1, 14, 28)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| B1 | Checkpoint Mechanism | S2 | domain/checkpoints/, api/v1/checkpoints/ |
| B2 | HITL Approval Flow | S2 | domain/workflows/executors/approval |
| B3 | Risk Assessment Engine | S55 | integrations/hybrid/risk/ |
| B4 | Mode Switcher | S56 | integrations/hybrid/switching/ |
| B5 | Unified Checkpoint | S57 | integrations/hybrid/checkpoint/ |
| B6 | HITL Controller (Phase 28) | S98 | integrations/orchestration/hitl/ |
| B7 | Approval Routes (Phase 28) | S98 | api/v1/orchestration/approval_routes |

### C. 狀態與記憶能力 (Phase 10-11, 22, 27)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| C1 | Session Mode | S42-43 | domain/sessions/ |
| C2 | AgentExecutor Unified Interface | S45-47 | domain/sessions/executor |
| C3 | Redis LLM Cache | S2 | infrastructure/cache/ |
| C4 | mem0 Memory System | S79-80 | integrations/memory/ |
| C5 | mem0 Polish | S90 | integrations/memory/ |

### D. 前端介面能力 (Phase 1, 15-16, 18-20, 26, 29, 34)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| D1 | Dashboard | S5 | frontend/pages/dashboard/ |
| D2 | Workflow Management Pages | S5 | frontend/pages/workflows/ |
| D3 | Agent Management Pages | S5 | frontend/pages/agents/ |
| D4 | Approval Workbench | S5 | frontend/pages/approvals/ |
| D5 | AG-UI Components | S58-61 | frontend/components/ag-ui/ |
| D6 | UnifiedChat | S62-65 | frontend/pages/UnifiedChat |
| D7 | Login/Signup | S70 | frontend/pages/auth/ |
| D8 | DevUI Pages | S87-89 | frontend/pages/DevUI/ |
| D9 | Agent Swarm Visualization | S100-106 | frontend/components/unified-chat/agent-swarm/ |
| D10 | ReactFlow Workflow DAG | S133 | frontend/components/workflow-editor/ |
| D11 | Agent Templates | S4 | frontend/pages/templates/ |

### E. 連接與整合能力 (Phase 1, 9, 12-13, 23, 34)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| E1 | ServiceNow Connector | S2 | domain/connectors/ |
| E2 | MCP Architecture (5 Servers) | S39-41 | integrations/mcp/ |
| E3 | Claude Agent SDK | S48-50 | integrations/claude_sdk/ |
| E4 | Hybrid MAF+Claude | S52-54 | integrations/hybrid/ |
| E5 | AG-UI Protocol (SSE) | S58 | integrations/ag_ui/ |
| E6 | A2A Protocol | S81 | integrations/a2a/ |
| E7 | n8n Integration | S124+ | integrations/n8n/, api/v1/n8n/ |
| E8 | InputGateway (Multi-source) | S93 | integrations/orchestration/input_gateway/ |

### F. 智能決策能力 (Phase 7, 13, 28)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| F1 | LLM Service Layer | S34-36 | integrations/llm/ |
| F2 | Intent Router (Hybrid) | S52 | integrations/hybrid/intent/ |
| F3 | Three-tier Routing (Pattern→Semantic→LLM) | S91-97 | integrations/orchestration/intent_router/ |
| F4 | Guided Dialog Engine | S98 | integrations/orchestration/guided_dialog/ |
| F5 | Business Intent Router | S96 | integrations/orchestration/intent_router/router |
| F6 | LLM Classifier | S97 | integrations/orchestration/intent_router/llm |
| F7 | Claude Autonomous Planning | S79 | api/v1/autonomous/ |

### G. 可觀測性能力 (Phase 1, 4, 23)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| G1 | Audit Logging | S3 | domain/audit/, api/v1/audit/ |
| G2 | DevUI Tracing | S4, S66-68 | domain/devtools/, api/v1/devtools/ |
| G3 | Patrol Monitoring | S82 | integrations/patrol/ |
| G4 | Event Correlation | S82 | integrations/correlation/ |
| G5 | Root Cause Analysis | S82 | integrations/rootcause/ |

### H. Agent Swarm 能力 (Phase 29)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| H1 | Swarm Manager + Workers | S100-102 | integrations/swarm/ |
| H2 | Swarm SSE Events | S103 | api/v1/swarm/ |
| H3 | Swarm Frontend Panel | S104-105 | frontend/components/unified-chat/agent-swarm/ |
| H4 | Swarm Tests | S106 | tests/ |

### I. 安全能力 (Phase 18, 21, 31)
| # | 功能 | 來源 Sprint | 目標模組 |
|---|------|------------|---------|
| I1 | JWT Authentication | S70 | core/auth, core/security/ |
| I2 | Global Auth Middleware | S111 | api/v1/__init__.py (protected_router) |
| I3 | Sandbox Isolation | S77-78 | core/sandbox/ |
| I4 | MCP Permission System | S39 | integrations/mcp/security/ |

---

## Phase 3 分析的對照要求

每個 Phase 3 Agent 在閱讀源代碼時，應對照本文件的功能清單，回答：

1. **功能 X 是否已實現？** — 對應的代碼檔案是否存在？業務邏輯是否完整？
2. **與計劃是否一致？** — 實際實現是否偏離了 Sprint Plan？
3. **有哪些計劃外的實現？** — 代碼中有哪些功能不在上述清單中？
4. **有哪些計劃但未實現的？** — 上述清單中哪些功能的代碼是空的或 mock？

---

**生成日期**: 2026-03-15
**功能總數**: 70+ 個（跨 8+1 個能力類別）
**Phase 數量**: 34 (Sprint 0-133)
