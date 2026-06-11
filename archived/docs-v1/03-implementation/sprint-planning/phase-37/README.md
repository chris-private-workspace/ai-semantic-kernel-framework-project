# Phase 37: E2E Assembly B — 任務執行組裝

## 概述

Phase 37 專注於實現 **任務執行組裝（E2E Assembly B）**，讓 Orchestrator 能夠派發任務給子 Agent，子 Agent 能使用 MCP 工具執行操作，結果能回傳並整合為最終回應。

本 Phase 是 IPA Platform 端到端流程的核心組裝階段，將 Phase 36 (A1) 建立的基礎連接擴展為完整的任務分派、執行、回傳、恢復流程。

## 目標

1. **任務分派系統** - Orchestrator 透過 dispatch tools 將任務派發給 MAF Workflow / Claude Worker / Swarm
2. **Worker 結果整合** - 統一 TaskResult protocol，Orchestrator 用 LLM 綜合多個 Worker 結果
3. **三層 Checkpoint 機制** - Conversation / Task / Agent Execution 三層狀態持久化與 Session Resume
4. **Swarm 整合到主流程** - 從 Demo API 移到 Orchestrator dispatch 路徑，啟用 feature flag
5. **端到端可觀測性** - Circuit Breaker、Background Response、G3/G4/G5 STUB 接通

## 前置條件

- ✅ Phase 36 (E2E Assembly A1) 完成
- ✅ Orchestrator 基礎 Router + Intent Classifier 就緒
- ✅ MAF RC4 Workflow Engine 就緒
- ✅ Claude SDK Worker Pool (ClaudeCoordinator) 就緒
- ✅ AG-UI SSE 事件基礎設施就緒
- ✅ Swarm Demo API 已驗證可用

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 113](./sprint-113-plan.md) | 任務分派 Tools + Task Registry | ~12 點 | ✅ 完成 |
| [Sprint 114](./sprint-114-plan.md) | MAF Workflow + Claude Worker 接通 | ~12 點 | ✅ 完成 |
| [Sprint 115](./sprint-115-plan.md) | 三層 Checkpoint + Session Resume | ~12 點 | ✅ 完成 |
| [Sprint 116](./sprint-116-plan.md) | Swarm 整合 + 可觀測性接通 | ~12 點 | ✅ 完成 |

**總計**: ~48 Story Points (4 Sprints)

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                Phase 37: E2E Assembly B — 任務執行組裝架構                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                           Frontend (React 18)                                │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                       任務列表頁面 (Task List)                        │  │    │
│  │   │   • Task CRUD 管理介面                                                │  │    │
│  │   │   • 即時進度顯示 (AG-UI SSE)                                         │  │    │
│  │   │   • Session Resume 入口                                               │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                       Unified Chat 整合                               │  │    │
│  │   │   • 用戶請求 → 任務進度 → 結果回傳                                    │  │    │
│  │   │   • Session 恢復提示                                                  │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │ HTTP / SSE                                │
│                                          ↓                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                           Backend (FastAPI)                                  │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                      Orchestrator (核心)                              │  │    │
│  │   │                                                                      │  │    │
│  │   │   Dispatch Tools:                                                    │  │    │
│  │   │   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐   │  │    │
│  │   │   │dispatch_workflow()│ │dispatch_to_claude│ │dispatch_swarm()  │   │  │    │
│  │   │   │  (Async, MAF)    │ │  (Sync, Claude)  │ │  (Async, Swarm)  │   │  │    │
│  │   │   └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘   │  │    │
│  │   │            │                    │                    │              │  │    │
│  │   │   ┌────────▼────────────────────▼────────────────────▼──────────┐   │  │    │
│  │   │   │              Task Registry (PostgreSQL)                     │   │  │    │
│  │   │   │  task_id | type | status | progress | assigned_agent       │   │  │    │
│  │   │   │  input_params | partial_results | checkpoint_data          │   │  │    │
│  │   │   └────────────────────────────────────────────────────────────┘   │  │    │
│  │   │                                                                      │  │    │
│  │   │   結果整合:                                                          │  │    │
│  │   │   ┌────────────────────────────────────────────────────────────┐   │  │    │
│  │   │   │  LLM 結果綜合 (多 Worker 結果 → 統一回應)                   │   │  │    │
│  │   │   │  TaskResult Protocol (統一回傳格式)                         │   │  │    │
│  │   │   └────────────────────────────────────────────────────────────┘   │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐   │    │
│  │   │ MAF Workflow    │  │ ClaudeCoordinator│  │ Swarm Engine             │   │    │
│  │   │ Engine          │  │ (Worker Pool)  │  │ (SwarmModeHandler)       │   │    │
│  │   │ • Sequential    │  │ • Claude Worker│  │ • Multi-Agent 協作       │   │    │
│  │   │ • Concurrent    │  │ • MCP Tools    │  │ • dispatch_swarm 路徑    │   │    │
│  │   └────────────────┘  └────────────────┘  └────────────────────────────┘   │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                   三層 Checkpoint 系統                                │  │    │
│  │   │                                                                      │  │    │
│  │   │   L1: Conversation State (Redis, TTL 24h)                           │  │    │
│  │   │       session messages, routing decision, approval status           │  │    │
│  │   │                                                                      │  │    │
│  │   │   L2: Task State (PostgreSQL)                                       │  │    │
│  │   │       Task Registry 持久化                                           │  │    │
│  │   │                                                                      │  │    │
│  │   │   L3: Agent Execution State (PostgreSQL)                            │  │    │
│  │   │       agent context, tool call history, intermediate results        │  │    │
│  │   │                                                                      │  │    │
│  │   │   Session Resume:                                                    │  │    │
│  │   │   GET /sessions → POST /sessions/{id}/resume → SessionRecoveryMgr  │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                   可觀測性 + 韌性層                                   │  │    │
│  │   │   • Circuit Breaker (LLM API 宕機降級)                               │  │    │
│  │   │   • Background Response (MAF RC4 continuation_token)                │  │    │
│  │   │   • ARQ 任務排程 (長時間任務不佔用 HTTP 連接)                         │  │    │
│  │   │   • G3/G4/G5 STUB 接通 (Patrol / Correlation / RootCause)          │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                      Task API Endpoints (新增)                              │    │
│  │                                                                              │    │
│  │   POST   /api/v1/tasks                          # 建立任務                  │    │
│  │   GET    /api/v1/tasks                          # 列出任務                  │    │
│  │   GET    /api/v1/tasks/{task_id}                # 取得任務詳情              │    │
│  │   PUT    /api/v1/tasks/{task_id}                # 更新任務                  │    │
│  │   DELETE /api/v1/tasks/{task_id}                # 刪除任務                  │    │
│  │   GET    /api/v1/sessions                       # 列出可恢復 Sessions      │    │
│  │   POST   /api/v1/sessions/{id}/resume           # 恢復 Session             │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Sprint 詳細內容

### Sprint 113 (~12 SP): 任務分派 Tools + Task Registry

**目標**: 建立 Orchestrator 的任務分派能力與任務追蹤基礎設施

| 項目 | 內容 |
|------|------|
| **Orchestrator Dispatch Tools** | `dispatch_workflow()`, `dispatch_to_claude()`, `dispatch_swarm()` |
| **Async Dispatch** | `dispatch_workflow` 和 `dispatch_swarm` 為非同步工具（返回 `task_id`，後台執行） |
| **Task Registry** | PostgreSQL 任務表：`task_id`, `type`, `status`, `progress`, `assigned_agent`, `input_params`, `partial_results`, `checkpoint_data` |
| **Task CRUD API** | 完整 REST API + 前端任務列表頁面 |
| **update_task_status() Tool** | Orchestrator 可透過工具更新任務狀態 |

**交付物**:
- [ ] 三個 dispatch tools 實作完成
- [ ] Task Registry 資料庫 migration
- [ ] Task CRUD API endpoints
- [ ] 前端任務列表頁面
- [ ] update_task_status() tool

### Sprint 114 (~12 SP): MAF Workflow + Claude Worker 接通

**目標**: 讓 Orchestrator 能實際驅動 MAF Workflow 和 Claude Worker，並統一結果回傳

| 項目 | 內容 |
|------|------|
| **MAF Workflow 啟動** | Orchestrator 能啟動 Sequential / Concurrent MAF workflow |
| **Claude Worker 派任** | Orchestrator 能派任務給 Claude worker pool (ClaudeCoordinator) |
| **TaskResult Protocol** | 統一 Worker 結果回傳格式 |
| **LLM 結果整合** | Orchestrator 用 LLM 綜合多個 Worker 結果為最終回應 |
| **AG-UI SSE 進度推送** | 即時推送任務執行進度到前端 |

**交付物**:
- [ ] MAF Workflow dispatch 端到端可執行
- [ ] Claude Worker dispatch 端到端可執行
- [ ] TaskResult protocol 定義與實作
- [ ] LLM 結果綜合邏輯
- [ ] SSE 進度推送驗證

### Sprint 115 (~12 SP): 三層 Checkpoint + Session Resume

**目標**: 實現完整的狀態持久化與 Session 恢復機制

| 層級 | 存儲 | 內容 | TTL |
|------|------|------|-----|
| **L1 Conversation State** | Redis | session messages, routing decision, approval status | 24h |
| **L2 Task State** | PostgreSQL | Task Registry 的持久化 | 永久 |
| **L3 Agent Execution State** | PostgreSQL | agent context, tool call history, intermediate results | 永久 |

| 項目 | 內容 |
|------|------|
| **Session Resume 流程** | `GET /sessions` → `POST /sessions/{id}/resume` → `SessionRecoveryManager` |
| **Claude Thread 持久化** | Phase A 採用「重建 thread」方案 |
| **ARQ 任務排程** | 長時間 Swarm / Workflow 任務不佔用 HTTP 連接 |

**交付物**:
- [ ] L1 Redis Conversation State 實作
- [ ] L2 PostgreSQL Task State 持久化
- [ ] L3 PostgreSQL Agent Execution State 持久化
- [ ] Session Resume API + SessionRecoveryManager
- [ ] Claude thread 重建邏輯
- [ ] ARQ 任務排程整合

### Sprint 116 (~12 SP): Swarm 整合 + 可觀測性接通

**目標**: 將 Swarm 整合到主流程，完成端到端可觀測性

| 項目 | 內容 |
|------|------|
| **Swarm 整合** | 從 Demo API 移到 Orchestrator 的 `dispatch_swarm()` 路徑 |
| **Feature Flag** | `SwarmModeHandler` feature flag 改為 `enabled=True` |
| **G3/G4/G5 STUB 接通** | Patrol / Correlation / RootCause STUB API 接通 |
| **Circuit Breaker** | LLM API 宕機降級模式 |
| **Background Response** | 利用 MAF RC4 `continuation_token` 實現長時間任務 |
| **端到端可觀測性驗證** | 完整鏈路追蹤驗證 |

**交付物**:
- [ ] Swarm 透過 dispatch_swarm() 執行
- [ ] SwarmModeHandler enabled=True 驗證通過
- [ ] G3/G4/G5 STUB API 端到端接通
- [ ] Circuit Breaker 降級測試通過
- [ ] continuation_token Background Response 驗證
- [ ] 端到端可觀測性報告

## 端到端流程

```
用戶請求
    │
    ↓
Orchestrator (Intent Classification + Routing)
    │
    ├── dispatch_to_claude() ──→ Claude Worker ──→ MCP 工具操作
    │                                                    │
    ├── dispatch_workflow() ───→ MAF Workflow ───→ 多步驟執行
    │        (Async, task_id)                            │
    │                                                    │
    ├── dispatch_swarm() ─────→ Swarm Engine ───→ 多 Agent 協作
    │        (Async, task_id)                            │
    │                                                    │
    ↓                                                    ↓
Task Registry (追蹤所有任務狀態)              結果回傳 (TaskResult)
    │                                                    │
    ↓                                                    ↓
AG-UI SSE (即時進度推送)                    LLM 結果綜合
    │                                                    │
    ↓                                                    ↓
前端即時更新                                  用戶收到統一回應
```

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| React | 18.2+ | 前端框架 |
| TypeScript | 5.0+ | 類型安全 |
| Zustand | 4.0+ | 狀態管理 |
| Shadcn UI | latest | UI 組件庫 |
| FastAPI | 0.100+ | 後端框架 |
| Pydantic | 2.0+ | 數據驗證 |
| PostgreSQL | 16 | 任務 / 狀態持久化 |
| Redis | 7 | Conversation State 快取 |
| ARQ | latest | 非同步任務排程 |
| MAF RC4 | latest | Agent Framework |
| Claude SDK | latest | Claude Agent 整合 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Async dispatch 任務遺失 | 任務無回應 | Task Registry 持久化 + ARQ 重試機制 |
| LLM 結果綜合品質不穩 | 回應品質差 | 設計 prompt template + fallback 策略 |
| Session Resume 狀態不完整 | 恢復失敗 | 三層 Checkpoint 互相驗證 + 降級方案 |
| Swarm 整合到主流程出問題 | 功能退化 | Feature flag 漸進啟用 + 回退機制 |
| Circuit Breaker 觸發頻率 | 服務降級過度 | 可調閾值 + 半開狀態自動恢復 |
| 長時間任務超時 | HTTP 連接斷開 | ARQ 背景執行 + continuation_token |

## 成功標準

- [ ] Orchestrator 能透過 dispatch tools 派發任務給三種 Worker
- [ ] Worker 結果統一回傳並由 LLM 綜合為最終回應
- [ ] Task Registry 完整追蹤所有任務狀態
- [ ] 三層 Checkpoint 正常運作
- [ ] Session 關閉後重開能恢復進度
- [ ] Swarm 透過 Orchestrator dispatch_swarm() 正常執行
- [ ] Circuit Breaker 降級正常觸發與恢復
- [ ] G3/G4/G5 STUB API 端到端可呼叫
- [ ] AG-UI SSE 即時推送任務進度
- [ ] 端到端延遲 < 500ms (P95, 不含 LLM 推理時間)

---

**Phase 37 前置**: Phase 36 (E2E Assembly A1) 完成
**總 Story Points**: ~48 pts (4 Sprints)
**Sprint 範圍**: Sprint 113 - Sprint 116
