# Phase 39: E2E Assembly D — Pipeline Assembly + Wiring

## 概述

Phase 39 是 IPA Platform **E2E Assembly 計劃**的第四階段（D），專注於 **管線組裝與接線（Pipeline Assembly & Wiring）**。

Phase 35-38 已建立所有核心模組（~60 個檔案、~10K+ LOC），但這些模組各自獨立存在，缺少將它們組裝成可運行端到端管線的啟動代碼。Phase 39 的核心使命是：**將散落的積木組裝成一台可運行的機器**。

> **Status**: ✅ 完成 — 4 Sprints (134-137), ~44 SP

## 核心問題（來自 GAP-ANALYSIS-10-REQUIREMENTS）

### 3 個 CRITICAL 差距

1. **組裝缺口（Assembly Gap）** — `OrchestratorMediator` 的 7 個 handler 全部 default None，沒有啟動代碼將它們接線到真實依賴
2. **無後台執行** — 所有執行綁定在 HTTP 請求週期，用戶斷開 = 任務中止
3. **新舊系統並存** — AG-UI bridge 仍連接舊 `HybridOrchestratorV2`，新 `OrchestratorMediator` 無 HTTP 入口

## 目標

1. **OrchestratorBootstrap** — 建立啟動組裝模組，接線所有 7 個 handler + MCP + Memory + ToolSecurity
2. **AG-UI Bridge 遷移** — 將 AG-UI SSE 串流從 HybridOrchestratorV2 遷移到 OrchestratorMediator
3. **後台任務執行** — 整合 ARQ 非同步任務佇列，dispatch 改為提交到 background worker
4. **安全加固 + 最終整合** — ToolSecurityGateway 接入、HITL 持久化、Risk Engine 統一、E2E 整合煙霧測試

## 前置條件

- ✅ Phase 35 (A0) — 核心假設驗證（AgentHandler, Chat API）
- ✅ Phase 36 (A1) — 基礎組裝（Security, Storage, HITL, Tools）
- ✅ Phase 37 (B) — 任務執行（Task Registry, Checkpoint, Circuit Breaker）
- ✅ Phase 38 (C) — 記憶+知識（Memory Manager, RAG Pipeline, Agent Skills）
- ✅ Checkpoint tag: `checkpoint/pre-assembly-phase39`

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 134](./sprint-134-plan.md) | OrchestratorBootstrap 全管線組裝 | ~12 點 | ✅ 完成 |
| [Sprint 135](./sprint-135-plan.md) | AG-UI Bridge 遷移 + 即時串流 | ~12 點 | ✅ 完成 |
| [Sprint 136](./sprint-136-plan.md) | 後台任務執行 + ARQ 整合 | ~10 點 | ✅ 完成 |
| [Sprint 137](./sprint-137-plan.md) | 安全加固 + E2E 整合測試 | ~10 點 | ✅ 完成 |

**總計**: ~44 Story Points (4 Sprints)

## 架構概覽

### 組裝前（Phase 35-38 現狀）

```
┌──────────────────────────────────────────────────────────────────┐
│                   散落的積木（未組裝）                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Auth API  ←─(斷開)─→  Session CRUD  ←─(斷開)─→  SessionFactory │
│                                                                   │
│  InputGateway ←─(斷開)─→ RoutingHandler(None)                    │
│                                                                   │
│  RiskAssessor ←─(斷開)─→ ApprovalHandler(None)                   │
│                                                                   │
│  AgentHandler ←─(接線)─→ LLM + ToolRegistry                     │
│                                                                   │
│  ExecutionHandler(claude=None, maf=None, swarm=None)             │
│                                                                   │
│  MCP Layer ←─(完全斷開)─→ Orchestrator                           │
│                                                                   │
│  MemoryManager ←─(斷開)─→ ContextHandler                        │
│                                                                   │
│  AG-UI Bridge ──→ HybridOrchestratorV2 (舊系統)                  │
│  OrchestratorMediator (新系統) ──→ 無 HTTP 入口                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 組裝後（Phase 39 目標）

```
┌──────────────────────────────────────────────────────────────────┐
│                   完整組裝的端到端管線                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Auth JWT ──→ Session CRUD ──→ SessionFactory ──→ Mediator       │
│                                                                   │
│  InputGateway ──→ RoutingHandler ──→ FrameworkSelector            │
│       │                                    │                      │
│       ↓                                    ↓                      │
│  RiskAssessor ──→ ApprovalHandler ──→ HITL (PostgreSQL)          │
│                                    │                              │
│                                    ↓                              │
│  AgentHandler ──→ LLM + ToolRegistry + MCP Tools                 │
│       │              │                                            │
│       ↓              ↓                                            │
│  MemoryManager  ToolSecurityGateway                              │
│       │                                                           │
│       ↓                                                           │
│  ExecutionHandler ──→ MAF / Claude / Swarm (via ARQ)             │
│       │                                                           │
│       ↓                                                           │
│  ResultSynthesiser ──→ AG-UI SSE ──→ 前端即時更新                 │
│       │                                                           │
│       ↓                                                           │
│  ObservabilityHandler + Checkpoint (L1/L2/L3)                    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Sprint 詳細內容

### Sprint 134 (~12 SP): OrchestratorBootstrap 全管線組裝

**目標**: 建立啟動組裝模組，一次性接線所有組件

| Story | 描述 | SP |
|-------|------|-----|
| S134-1 | OrchestratorBootstrap 類 — 組裝 7 個 handler 的工廠方法 | 3 |
| S134-2 | InputGateway + RoutingHandler 接線（含 FrameworkSelector） | 2 |
| S134-3 | RiskAssessor + ApprovalHandler 接線 | 2 |
| S134-4 | ExecutionHandler 接線（MAF executor + Claude executor + SwarmHandler） | 3 |
| S134-5 | MCP 工具動態註冊到 OrchestratorToolRegistry | 2 |

### Sprint 135 (~12 SP): AG-UI Bridge 遷移 + 即時串流

**目標**: 將 AG-UI SSE 從舊系統遷移到新 Mediator

| Story | 描述 | SP |
|-------|------|-----|
| S135-1 | MediatorEventBridge — 適配 OrchestratorMediator 到 AG-UI 事件格式 | 3 |
| S135-2 | AG-UI `/run` endpoint 改用 MediatorEventBridge | 2 |
| S135-3 | 中間事件串流（thinking tokens、tool-call progress） | 3 |
| S135-4 | Session-aware SSE 通道（用戶斷開重連不丟事件） | 2 |
| S135-5 | MemoryManager 接入 ContextHandler（自動記憶注入） | 2 |

### Sprint 136 (~10 SP): 後台任務執行 + ARQ 整合

**目標**: 長時間任務不佔用 HTTP 連接

| Story | 描述 | SP |
|-------|------|-----|
| S136-1 | ARQ worker 設置（Redis-backed 任務佇列） | 2 |
| S136-2 | dispatch_workflow/swarm 改為 ARQ 提交 | 3 |
| S136-3 | 任務狀態輪詢 API + SSE 完成推送 | 2 |
| S136-4 | Session Resume 接通 — 恢復後台執行中的任務 | 3 |

### Sprint 137 (~10 SP): 安全加固 + E2E 整合測試

**目標**: 安全層接入 + 端到端煙霧測試

| Story | 描述 | SP |
|-------|------|-----|
| S137-1 | ToolSecurityGateway 接入 OrchestratorToolRegistry.execute() | 2 |
| S137-2 | HITL 審批持久化到 PostgreSQL（取代 in-memory） | 2 |
| S137-3 | 統一 RiskAssessor 和 RiskAssessmentEngine | 2 |
| S137-4 | E2E 整合煙霧測試（完整 10 步流程） | 2 |
| S137-5 | Extended Thinking 執行模式 | 2 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 組裝過程破壞現有功能 | 系統不可用 | `checkpoint/pre-assembly-phase39` tag 可隨時回退 |
| HybridOrchestratorV2 移除影響 | AG-UI 中斷 | 新舊 Bridge 並存，Feature flag 切換 |
| ARQ 整合複雜度高 | 延期 | 可先用 FastAPI BackgroundTasks 過渡 |
| MCP 動態註冊影響效能 | 啟動慢 | Lazy loading + 快取 |
| 多 Worker 進程狀態不同步 | Session 混亂 | 先限制單 Worker，後續加 Redis session store |

## 成功標準

- [ ] OrchestratorBootstrap 能一次性建立完整可運行的 Mediator pipeline
- [ ] 用戶請求從 Auth → Session → Mediator → Worker → Response 端到端可跑通
- [ ] AG-UI SSE 串流使用新 MediatorEventBridge
- [ ] 長時間任務透過 ARQ 在後台執行
- [ ] ToolSecurityGateway 攔截所有工具調用
- [ ] HITL 審批持久化到 PostgreSQL
- [ ] Session 關閉後可恢復並重連後台任務
- [ ] MCP 工具可被 Orchestrator Agent 動態發現和調用
- [ ] E2E 10 步煙霧測試通過

## 回退計劃

如果組裝過程造成不可挽回的問題：
```bash
git reset --hard checkpoint/pre-assembly-phase39
```

---

**Phase 39 前置**: Phase 35-38 (E2E Assembly A0-C) 完成
**Checkpoint**: `checkpoint/pre-assembly-phase39`
**總 Story Points**: ~44 pts
**Sprint 範圍**: Sprint 134-137
