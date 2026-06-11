# IPA Platform - Sprint Planning Overview

**版本**: 10.0 (Phase 31-34: Platform Improvement Roadmap)
**創建日期**: 2025-11-29
**最後更新**: 2026-02-21
**總開發週期**: 123 Sprints (34 Phases)

---

## 快速導航 - Phase 總覽

| Phase | 名稱 | Sprints | Story Points | 狀態 | 文件 |
|-------|------|---------|--------------|------|------|
| Phase 1 | 基礎建設 | 1-6 | ~90 pts | ✅ 完成 | [README](./phase-1/README.md) |
| Phase 2 | 並行執行引擎 | 7-12 | ~90 pts | ✅ 完成 | [README](./phase-2/README.md) |
| Phase 3 | Official API Migration | 13-18 | ~105 pts | ✅ 完成 | [README](./phase-3/README.md) |
| Phase 4 | Advanced Adapters | 19-24 | ~105 pts | ✅ 完成 | [README](./phase-4/README.md) |
| Phase 5 | Connector Ecosystem | 25-27 | ~75 pts | ✅ 完成 | [README](./phase-5/README.md) |
| Phase 6 | Enterprise Integration | 28-30 | ~75 pts | ✅ 完成 | [README](./phase-6/README.md) |
| Phase 7 | Multi-turn & Memory | 31-33 | ~90 pts | ✅ 完成 | [README](./phase-7/README.md) |
| Phase 8 | Code Interpreter | 34-36 | ~90 pts | ✅ 完成 | [README](./phase-8/README.md) |
| Phase 9 | MCP Integration | 37-39 | ~90 pts | ✅ 完成 | [README](./phase-9/README.md) |
| Phase 10 | MCP Expansion | 40-44 | ~105 pts | ✅ 完成 | [README](./phase-10/README.md) |
| Phase 11 | Agent-Session Integration | 45-47 | ~90 pts | ✅ 完成 | [README](./phase-11/README.md) |
| Phase 12 | Claude Agent SDK | 48-51 | 165 pts | ✅ 完成 | [README](./phase-12/README.md) |
| Phase 13 | Hybrid Core Architecture | 52-54 | 105 pts | ✅ 完成 | [README](./phase-13/README.md) |
| Phase 14 | Advanced Hybrid Features | 55-57 | 95 pts | ✅ 完成 | [README](./phase-14/README.md) |
| Phase 15 | AG-UI Protocol Integration | 58-60 | 85 pts | ✅ 完成 | [README](./phase-15/README.md) |
| Phase 16 | Unified Agentic Chat Interface | 61-65 | 100 pts | ✅ 完成 | [README](./phase-16/README.md) |
| Phase 17 | DevTools Backend API | 66-68 | 72 pts | ✅ 完成 | [README](./phase-17/README.md) |
| Phase 18 | Session Management | 69-70 | 46 pts | ✅ 完成 | [README](./phase-18/README.md) |
| Phase 19 | Autonomous Agent | 71-72 | 48 pts | ✅ 完成 | [README](./phase-19/README.md) |
| Phase 20 | File Attachment Support | 73-76 | 60 pts | ✅ 完成 | [README](./phase-20/README.md) |
| Phase 21 | Sandbox Security | 77-78 | 48 pts | ✅ 完成 | [README](./phase-21/README.md) |
| Phase 22 | mem0 Core Implementation | 79-80 | 54 pts | ✅ 完成 | [README](./phase-22/README.md) |
| Phase 23 | Performance Optimization | 81-82 | 48 pts | ✅ 完成 | [README](./phase-23/README.md) |
| Phase 24 | Production Deployment | 83-84 | 48 pts | ✅ 完成 | [README](./phase-24/README.md) |
| Phase 25 | Production Expansion | 85-86 | 45 pts | ✅ 完成 | [README](./phase-25/README.md) |
| Phase 26 | DevUI Frontend | 87-89 | 42 pts | ✅ 完成 | [README](./phase-26/README.md) |
| Phase 27 | mem0 整合完善 | 90 | 13 pts | ✅ 完成 | [README](./phase-27/README.md) |
| Phase 28 | 三層意圖路由 | 91-99 | 235 pts | ✅ 完成 | [README](./phase-28/README.md) |
| Phase 29 | Agent Swarm 可視化 | 100-106 | 190 pts | ✅ 完成 | [README](./phase-29/README.md) |
| Phase 30 | Azure AI Search (延後) | 107-110 | 75 pts | ⏸️ 延後 | [README](./phase-30/README.md) |
| Phase 31 | Security Hardening + Quick Wins | 111-113 | ~125 pts | ⏸️ 被 Phase 35-38 取代 | [README](./phase-31/README.md) |
| Phase 32 | Core Business Scenario + Architecture | 114-118 | ~205 pts | ⏸️ 被 Phase 35-38 取代 | [README](./phase-32/README.md) |
| Phase 33 | Production Readiness + Quality | 119-123 | ~205 pts | ⏸️ 被 Phase 35-38 取代 | [README](./phase-33/README.md) |
| Phase 34 | Feature Expansion | TBD | TBD | ⏸️ 被 Phase 35-38 取代 | [README](./phase-34/README.md) |
| **Phase 35** | **E2E Assembly A0 — 核心假設驗證** | **107-108** | **~15 pts** | **📋 計劃中** | [README](./phase-35/README.md) |
| **Phase 36** | **E2E Assembly A1 — 基礎組裝** | **109-112** | **~48 pts** | **📋 計劃中** | [README](./phase-36/README.md) |
| **Phase 37** | **E2E Assembly B — 任務執行組裝** | **113-116** | **~48 pts** | **📋 計劃中** | [README](./phase-37/README.md) |
| **Phase 38** | **E2E Assembly C — 記憶與知識組裝** | **117-120** | **~38 pts** | **📋 計劃中** | [README](./phase-38/README.md) |

**總計**: ~2528 Story Points across 120 Sprints (38 Phases, 其中 Phase 30-34 已暫停/取代)

> **當前執行順序**: Phase 35 (A0 驗證) → Phase 36 (A1 基礎) → Phase 37 (B 任務執行) → Phase 38 (C 記憶+知識)
> Phase 31-34 的安全/持久化/品質工作已整合到 Phase 35-38 的 E2E Assembly 計劃中。
> Phase 35 (A0) 是 Go/No-Go 門檻：如果核心假設驗證失敗，需重新評估後續計劃。
> 基於三份專家分析報告：Architecture Review、Codebase Verification、Business Panel Analysis。

---

## Phase 13-15: Hybrid Architecture & AG-UI (NEW)

### 背景

Phase 12 完成 Claude Agent SDK 整合後，需要進一步整合 **Microsoft Agent Framework (MAF)** 和 **Claude Agent SDK** 兩個框架，實現真正的混合編排架構。

### Phase 13: Hybrid Core Architecture (105 pts)

**目標**: 建立 MAF + Claude SDK 的核心整合架構

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 52 | Intent Router & Mode Detection | 35 pts | 智能意圖路由、模式檢測 |
| Sprint 53 | Context Bridge & Sync | 35 pts | 跨框架上下文同步 |
| Sprint 54 | HybridOrchestrator Refactor | 35 pts | 統一 Tool 執行、V2 編排器 |

**核心組件**:
- **Intent Router**: 判斷 Workflow Mode vs Chat Mode
- **Context Bridge**: MAF ↔ Claude 狀態同步
- **Unified Tool Executor**: 所有 Tool 通過 Claude 執行

### Phase 14: Advanced Hybrid Features (95 pts)

**目標**: 實現進階混合功能和優化

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 55 | Risk Assessment Engine | 30 pts | 風險評估驅動的審批決策 |
| Sprint 56 | Mode Switcher & HITL | 35 pts | 動態模式切換、增強 HITL |
| Sprint 57 | Unified Checkpoint & Polish | 30 pts | 統一 Checkpoint、整合測試 |

**核心組件**:
- **Risk Assessment Engine**: 基於風險等級的 HITL
- **Mode Switcher**: Workflow ↔ Chat 動態切換
- **Unified Checkpoint**: 跨框架狀態保存與恢復

---

## Phase 15: AG-UI Protocol Integration (NEW)

### 背景

Phase 13-14 完成混合架構後，需要標準化 Agent-UI 通訊協議。**AG-UI (Agent-User Interface Protocol)** 是由 CopilotKit 提出的開放、輕量級、事件驅動協議，讓 AI Agents 能以標準化方式與前端 UI 互動。

### Phase 15: AG-UI Protocol Integration (85 pts)

**目標**: 實現完整的 AG-UI 協議支持，標準化前後端通訊

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 58 | AG-UI Core Infrastructure | 30 pts | SSE Endpoint, HybridEventBridge, Thread Manager |
| Sprint 59 | AG-UI Basic Features (1-4) | 28 pts | Agentic Chat, Tool Rendering, HITL, Generative UI |
| Sprint 60 | AG-UI Advanced Features (5-7) | 27 pts | Tool-based UI, Shared State, Predictive Updates |

### AG-UI 7 大功能

| # | 功能 | 說明 | 對應 Sprint |
|---|------|------|-------------|
| 1 | **Agentic Chat** | 即時對話與工具調用展示 | S59-1 |
| 2 | **Backend Tool Rendering** | 後端決定 Tool 結果 UI | S59-2 |
| 3 | **Human-in-the-Loop** | 使用者審批整合 | S59-3 |
| 4 | **Agentic Generative UI** | Agent 動態生成 UI 元件 | S59-4 |
| 5 | **Tool-based Generative UI** | Tool 驅動的動態 UI | S60-1 |
| 6 | **Shared State** | 前後端共享狀態 | S60-2 |
| 7 | **Predictive State Updates** | 樂觀/預測性狀態更新 | S60-3 |

### 核心組件

```
Backend:
├── AG-UI SSE Endpoint (/api/v1/ag-ui)
├── HybridEventBridge (Hybrid → AG-UI 事件轉換)
├── Thread Manager (對話線程管理)
└── State Synchronizer (前後端狀態同步)

Frontend:
├── AGUIProvider (React Context)
├── useAGUI Hook (SSE 連線管理)
├── AgentChat Component (對話 UI)
├── ApprovalDialog Component (HITL UI)
└── SharedStateManager (狀態同步)
```

### 與現有架構整合

| Phase 13-14 組件 | AG-UI 整合方式 |
|-----------------|---------------|
| HybridOrchestrator | → HybridEventBridge → AG-UI Events |
| Risk Assessment | → 驅動 HITL (Feature 3) |
| Mode Switcher | → STATE_DELTA 事件通知前端 |
| Unified Checkpoint | → STATE_SNAPSHOT 事件 |

---

## 產品概述

### 產品定位
**IPA Platform** (Intelligent Process Automation) - 企業級 AI Agent 編排管理平台

### 核心差異化
| 傳統 RPA | IPA Platform |
|---------|--------------|
| 規則基礎，固定流程 | **LLM 智能決策**，自適應場景 |
| 被動執行，問題發生後處理 | **主動巡檢預防**，從救火到預防 |
| 單系統操作，信息孤島 | **跨系統關聯分析**，統一視圖 |
| 無學習能力，準確率固定 | **人機協作學習**，越用越智能 |

### 目標用戶
1. **IT 運維團隊** (主要) - 500-2000 人企業，50-500 人 IT 部門
2. **客戶服務團隊** (次要) - 100-1000 人 CS 部門

### 商業價值
- IT 處理時間：6 小時/天 → 1 小時/天 (節省 40%+)
- CS 處理時間：30-80 分鐘/工單 → 縮短 50%+
- 12 個月 ROI > 200%

---

## 技術架構摘要

### 核心技術棧

| 層級 | 技術 | 版本 | 說明 |
|------|------|------|------|
| **Agent 框架** | Microsoft Agent Framework | Preview | 核心編排引擎 |
| **Claude SDK** | Claude Agent SDK | Latest | 智能對話能力 |
| **後端** | Python FastAPI | 0.100+ | REST API 服務 |
| **前端** | React + TypeScript | 18+ | 現代化 UI |
| **數據庫** | PostgreSQL | 16+ | 主數據存儲 |
| **緩存** | Redis | 7+ | LLM 響應緩存 |
| **消息隊列** | Azure Service Bus / RabbitMQ | - | 異步任務處理 |
| **LLM** | Azure OpenAI + Claude | GPT-4o / Claude 3.5 | 企業級推理 |

### 系統架構圖 (Phase 15)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    React 18 前端 (Shadcn UI)                              │
│   Dashboard | Workflows | Agents | Sessions | AgentChat | ApprovalDialog  │
│                                                                           │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  AG-UI Frontend: AGUIProvider + useAGUI + SharedStateManager      │  │
│   └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ SSE (text/event-stream)
                                 │ POST /api/v1/ag-ui
┌────────────────────────────────┴─────────────────────────────────────────┐
│                         FastAPI Backend                                   │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  AG-UI Layer: SSE Endpoint + HybridEventBridge + Thread Manager    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│  ┌─────────────┐    ┌──────────────▼──┐    ┌───────────────┐             │
│  │Intent Router│───→│HybridOrchestrator│───→│ Risk Assessor │             │
│  └─────────────┘    └─────────────────┘    └───────────────┘             │
│         │                  │                    │                         │
│         ▼                  ▼                    ▼                         │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐                │
│  │Mode Switcher│    │Context Bridge│    │Unified Chkpt  │                │
│  └─────────────┘    └──────────────┘    └───────────────┘                │
│         │                  │                                              │
│         ▼                  ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                   Unified Tool Executor                             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│         │                                │                                │
│         ▼                                ▼                                │
│  ┌─────────────────┐            ┌───────────────────┐                    │
│  │MAF Adapters     │            │Claude SDK         │                    │
│  │ - GroupChat     │            │ - ClaudeSDKClient │                    │
│  │ - Handoff       │            │ - ToolRegistry    │                    │
│  │ - Concurrent    │            │ - HookManager     │                    │
│  │ - Nested        │            │ - MCP Integration │                    │
│  └─────────────────┘            └───────────────────┘                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌─────▼─────┐
   │Service  │      │Redis    │      │PostgreSQL │
   │Bus      │      │Cache    │      │Database   │
   └─────────┘      └─────────┘      └───────────┘
```

---

## 開發狀態總覽

### 已完成 Phase (1-27)

| Phase | 主要成就 |
|-------|---------|
| Phase 1-2 | 基礎架構、並行執行引擎 |
| Phase 3-4 | Official API Migration、Advanced Adapters |
| Phase 5-6 | Connector Ecosystem、Enterprise Integration |
| Phase 7-8 | Multi-turn & Memory、Code Interpreter |
| Phase 9-10 | MCP Core、MCP Expansion (22 servers) |
| Phase 11 | Agent-Session Integration (90 pts) |
| Phase 12 | Claude Agent SDK Integration (165 pts) |
| Phase 13 | Hybrid Core Architecture - Intent Router, Context Bridge (105 pts) |
| Phase 14 | Advanced Hybrid Features - Risk Assessment, Mode Switcher (95 pts) |
| Phase 15 | AG-UI Protocol Integration - 7 Features Complete (85 pts) |
| Phase 16 | Unified Agentic Chat Interface (100 pts) |
| Phase 17 | DevTools Backend API (72 pts) |
| Phase 18 | Session Management (46 pts) |
| Phase 19 | Autonomous Agent (48 pts) |
| Phase 20 | File Attachment Support (60 pts) |
| Phase 21 | Sandbox Security (48 pts) |
| Phase 22 | mem0 Core Implementation (54 pts) |
| Phase 23 | Performance Optimization (48 pts) |
| Phase 24 | Production Deployment (48 pts) |
| Phase 25 | Production Expansion (45 pts) |
| Phase 26 | DevUI Frontend - Timeline, Statistics, SSE (42 pts) |
| Phase 27 | mem0 整合完善 - 測試和文檔 (13 pts) |

**已完成總計**: 2189 Story Points across 99 Sprints

### 最新完成 (Phase 27-28)

| Phase | Sprint | 完成日期 | 主要交付物 |
|-------|--------|----------|-----------|
| Phase 27 | Sprint 90 | 2026-01-14 | mem0 依賴、環境變數、59 個測試、文檔 |
| Phase 28 | Sprint 91-93 | 2026-01-15 | Pattern Matcher、Semantic Router、BusinessIntentRouter |
| Phase 28 | Sprint 94-96 | 2026-01-15 | GuidedDialogEngine、InputGateway、RiskAssessor |
| Phase 28 | Sprint 97-98 | 2026-01-15 | HITLController、HybridOrchestratorV2 整合 |
| Phase 28 | Sprint 99 | 2026-01-16 | E2E 測試、性能測試、監控指標、文檔 |

---

## 非功能性需求 (NFR)

### 性能要求
| 指標 | 目標值 |
|------|--------|
| Agent 執行延遲 (P95) | < 5 秒 |
| LLM 調用延遲 (P95) | < 3 秒 |
| API 響應時間 (P95) | < 500ms |
| Dashboard 加載時間 | < 2 秒 |
| 併發執行數 | 50+ 同時 |
| Redis 緩存命中率 | ≥ 60% |
| Checkpoint 恢復成功率 | > 99.9% |
| 模式切換成功率 | > 99% |

### 可用性要求
| 指標 | MVP 目標 | Phase 14 目標 |
|------|----------|-------------|
| 系統正常運行 | 99.0% | 99.5% |
| 數據持久性 | 99.99% | 99.99% |
| 檢查點恢復 | 100% | 100% |

### 安全要求
| 要求 | 實現方式 |
|------|---------|
| 認證 | JWT + 24h 會話 |
| 授權 | 角色基礎 (admin/user/viewer) |
| 傳輸加密 | TLS 1.3 |
| 存儲加密 | AES-256 |
| 機密管理 | Azure Key Vault |
| 風險評估 | Risk Assessment Engine (Phase 14) |

---

## 開發環境設置

### 前置要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Azure CLI (已登入)
- Git

### 快速開始

```bash
# 1. Clone 專案
git clone https://github.com/your-org/ipa-platform.git
cd ipa-platform

# 2. 啟動開發環境
docker-compose up -d

# 3. 安裝 Python 依賴
cd backend
pip install -r requirements.txt
pip install agent-framework --pre

# 4. 啟動後端
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. 安裝前端依賴 (另一終端)
cd frontend
npm install
npm run dev
```

### 環境變量

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/ipa_platform
REDIS_URL=redis://localhost:6379
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
ANTHROPIC_API_KEY=xxx
```

---

## 風險與緩解

| 風險 | 等級 | 緩解措施 |
|------|------|---------|
| Agent Framework API 變更 | 中 | 鎖定版本，監控 Release Notes |
| Claude SDK API 變更 | 中 | 版本鎖定，抽象層隔離 |
| LLM Token 成本超預算 | 中 | 成本監控 + 閾值告警 + 緩存 |
| 框架整合複雜度 | 高 | Context Bridge + Unified Checkpoint |
| 模式切換狀態丟失 | 中 | Checkpoint 機制 + 回滾支持 |

---

## 參考文檔

| 類別 | 文檔位置 |
|------|---------|
| 產品探索 | `docs/00-discovery/` |
| 產品規劃 | `docs/01-planning/prd/` |
| UI/UX 設計 | `docs/01-planning/ui-ux/` |
| 技術架構 | `docs/02-architecture/` |
| Agent Framework | `reference/agent-framework/` |
| Claude Agent SDK | `backend/src/integrations/claude_sdk/` |
| Phase 13 文檔 | `docs/03-implementation/sprint-planning/phase-13/` |
| Phase 14 文檔 | `docs/03-implementation/sprint-planning/phase-14/` |
| Phase 15 文檔 | `docs/03-implementation/sprint-planning/phase-15/` |
| Phase 16 文檔 | `docs/03-implementation/sprint-planning/phase-16/` |

---

**Phase 28 完成成就** (2026-01-16):
- ✅ 三層路由: Pattern Matcher → Semantic Router → LLM Classifier
- ✅ BusinessIntentRouter: 業務意圖分類 + 完整度評估
- ✅ GuidedDialogEngine: 引導式對話 + 增量更新
- ✅ InputGateway: 多來源輸入處理 (ServiceNow, Prometheus, 用戶)
- ✅ RiskAssessor: IT Intent → 風險等級映射
- ✅ HITLController: 人機協作審批流程
- ✅ E2E 整合測試、性能測試、監控指標整合
- ✅ 完整文檔 (ARCHITECTURE.md, API Reference)

**Phase 28 統計**:
- 總 Story Points: 235 pts
- Sprint 數量: 9 (Sprint 91-99)
- 測試覆蓋率: > 87%
- 組件數量: 35 檔案

**Phase 1-29 已完成**:
- 總 Story Points: 2379 pts
- 總 Sprint 數量: 106
- 開發週期: 2025-11 至 2026-02

---

## Phase 29: Agent Swarm 可視化 (NEW)

### 背景

Phase 28 完成三層意圖路由後，需要實現 **Agent Swarm 可視化系統**，讓用戶能夠直觀地看到多代理協作的執行過程、Worker 詳情、擴展思考過程等。

### 設計參考

- **設計文檔**: `docs/07-analysis/Agentic-chat-page/agent-swarm-chat-layout-design.md`
- **參考介面**: Kimi AI Agent Swarm 聊天介面

### Phase 29: Agent Swarm 可視化與執行追蹤 (190 pts)

**目標**: 實現多代理協作的執行過程可視化

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 100 | Swarm 數據模型 + 後端 API | 28 pts | WorkerExecution, SwarmTracker, API 端點 |
| Sprint 101 | Swarm 事件系統 + SSE 整合 | 25 pts | SwarmEventEmitter, HybridEventBridge 整合 |
| Sprint 102 | AgentSwarmPanel + WorkerCard | 30 pts | 前端主面板和 Worker 卡片組件 |
| Sprint 103 | WorkerDetailDrawer 詳情面板 | 32 pts | Worker 詳情 Drawer, 工具調用展示 |
| Sprint 104 | ExtendedThinking + 工具調用優化 | 28 pts | 擴展思考展示, 操作列表組件 |
| Sprint 105 | OrchestrationPanel 整合 + 狀態管理 | 25 pts | Zustand Store, 組件整合 |
| Sprint 106 | E2E 測試 + 性能優化 + 文檔 | 22 pts | 測試套件, 性能報告, 文檔 |

### 核心功能

1. **Agent Swarm Panel** - 多代理任務列表與整體進度
2. **Worker Card** - 單個 Worker 的狀態、進度、當前操作
3. **Worker Detail Drawer** - Worker 執行詳情滑出面板
4. **Extended Thinking Panel** - Claude 思考過程展示
5. **Real-time SSE Events** - 實時狀態推送

### 技術架構

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│   OrchestrationPanel + AgentSwarmPanel + WorkerDetailDrawer │
└────────────────────────────┬────────────────────────────────┘
                             │ SSE Events
┌────────────────────────────┴────────────────────────────────┐
│                    FastAPI Backend                           │
│   SwarmTracker + SwarmEventEmitter + Swarm API              │
│                         │                                    │
│   ClaudeCoordinator + SwarmIntegration                      │
└─────────────────────────────────────────────────────────────┘
```

---

**Phase 29 完成**: 2026-02-09
**總 Story Points**: 190 pts
**Sprint 數量**: 7 (Sprint 100-106)

---

## Phase 31-34: Platform Improvement Roadmap (NEW)

### 背景

基於 6 位領域專家（Security Architect / Enterprise Architect / SRE-DevOps / Business Analyst / Code Quality Lead / Integration Architect）的統一改善方案建議書，規劃 4 個新 Phase 來系統性改善平台的安全性、業務落地能力和生產就緒度。

> **分析報告**: `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md`

### 執行順序

```
Phase 31 (Security)  →  Phase 32 (Business Scenario + Architecture)
   3 weeks                    5 weeks
                              ↑ 吸收 Phase 30 Azure AI Search 工作
                     →  Phase 33 (Production Readiness)  →  Phase 34 (Expansion)
                            5-6 weeks                        Ongoing
```

### Phase 31: Security Hardening + Quick Wins (125 pts, 3 Sprints)

**目標**: 達到「可安全內部展示」狀態。Auth 7%→100%，安全評分 1/10→6/10。

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 111 | Quick Wins + Auth Foundation | ~40 pts | CORS/Vite/JWT 修復 + 全局 Auth Middleware |
| Sprint 112 | Mock Separation + Redis Storage | ~45 pts | 18 Mock 分離 + InMemory→Redis |
| Sprint 113 | MCP Security + Validation | ~40 pts | MCP Permission 啟用 + Shell/SSH 白名單 |

### Phase 32: Core Business Scenario + Architecture (205 pts, 5 Sprints)

**目標**: AD 帳號管理場景端到端可用，ROI +112%，月節省 $5,740。

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 114 | AD Scenario Foundation | ~40 pts | PatternMatcher AD 規則 + LDAP MCP + ServiceNow Webhook |
| Sprint 115 | SemanticRouter Real (=Phase 30) | ~45 pts | Azure AI Search + AzureSemanticRouter |
| Sprint 116 | Architecture Reinforcement | ~45 pts | Swarm 整合 + Layer 4 拆分 + 循環依賴修復 |
| Sprint 117 | Multi-Worker + ServiceNow MCP | ~40 pts | Gunicorn Multi-Worker + ServiceNow MCP Server |
| Sprint 118 | E2E Testing + Validation | ~35 pts | AD 場景全流程 E2E 測試 |

### Phase 33: Production Readiness + Quality (205 pts, 5 Sprints)

**目標**: 團隊內部可以開始使用。Docker 部署到 Azure，測試覆蓋 60%+。

| Sprint | 名稱 | Points | 主要交付物 |
|--------|------|--------|-----------|
| Sprint 119 | InMemory Storage Migration | ~45 pts | Top 4 InMemory→Redis + ContextSync Redis Lock |
| Sprint 120 | InMemory Completion + Checkpoint | ~40 pts | 剩餘 InMemory 替換 + Checkpoint 統一設計 |
| Sprint 121 | Checkpoint + CI/CD | ~40 pts | Checkpoint 統一 + Dockerfile + CI/CD Pipeline |
| Sprint 122 | Azure Deployment + Observability | ~45 pts | Azure App Service + OTel + 結構化日誌 |
| Sprint 123 | Test Coverage + Quality | ~35 pts | 測試覆蓋→60% + 品質報告 |

### Phase 34: Feature Expansion (大綱，待詳細規劃)

**目標**: 擴展業務場景和整合。詳細 Sprint 規劃待 Phase 33 接近完成時進行。

優先項目: n8n 整合、Azure Data Factory MCP、IT 事件處理場景、D365 MCP、Test→80%
