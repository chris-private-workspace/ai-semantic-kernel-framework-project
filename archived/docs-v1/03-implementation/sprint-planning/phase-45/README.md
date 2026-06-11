# Phase 45: Orchestration Core

## 目標

合併 V8 Orchestration Layer 和 PoC Pipeline 為一條生產級 8 步 pipeline，
加入真正的分派執行層（subagent / team），並改版 Unified Chat 前端。

## 背景

- **V8 Orchestration Layer**（~15,500 LOC, 39 檔案）— 三層意圖路由、完整度檢查、引導對話、7 維風險評估、完整 HITL
- **PoC Pipeline**（~500 LOC, agent_team_poc.py）— 記憶、知識庫、LLM 選路、checkpoint、transcript
- 兩者各自只解決了一半問題，Phase 45 將它們合併為完整的 orchestration 系統

## 8 步 Pipeline 架構

```
[Step 1] 記憶讀取           ← PoC: UnifiedMemoryManager + ContextBudgetManager
[Step 2] 知識庫搜索         ← PoC: Qdrant 向量搜索
[Step 3] 意圖分析 + 完整度  ← V8: BusinessIntentRouter (三層) + CompletenessChecker
[Step 4] 風險評估           ← V8: RiskAssessor (7維 + 40 ITIL 政策)
[Step 5] HITL 審批閘        ← V8+PoC: HITLController
[Step 6] LLM 選路決策       ← PoC: OrchestratorAgent + select_route()
[Step 7] 分派執行           ← 全新: DispatchService
[Step 8] 後處理             ← PoC: checkpoint + 記憶抽取 + transcript
```

## Sprint 規劃

| Sprint | 重點 | 點數 |
|--------|------|------|
| 153 | Pipeline 基礎 + Steps 1-2（記憶+知識） | 20 |
| 154 | Steps 3-5（意圖+風險+HITL） | 21 |
| 155 | Step 6 LLM 選路 + 分派層 | 23 |
| 156 | 生產 API + 後處理 | 22 |
| 157 | 前端改版 | 20 |
| 158 | 測試 + 收尾 | 15 |
| **合計** | | **121** |

## 分支

- Branch: `feature/phase-45-orchestration-core`
- Worktree: `C:/Users/Chris/Downloads/ai-semantic-kernel-orchestration/`

## 新建模組

```
backend/src/integrations/orchestration/
├── pipeline/          ← 統一 pipeline 服務
│   ├── service.py     ← OrchestrationPipelineService
│   ├── context.py     ← PipelineContext
│   ├── exceptions.py  ← 暫停異常
│   └── steps/         ← 8 個步驟
│
├── dispatch/          ← 執行分派層
│   ├── service.py     ← DispatchService
│   └── executors/     ← 5 個執行器
```

## 關鍵原則

1. **不動 V8 原有模組** — 只用 pipeline/steps/ 包裝
2. **不動 PoC 端點** — Phase 46 再 deprecate
3. **復用現有模組** — TranscriptService、ResumeService、IPACheckpointStorage 等
4. **swarm/workflow executor 先做 stub** — Phase 45 聚焦 direct/subagent/team

---

**Started**: 2026-04-11
**Status**: In Progress
