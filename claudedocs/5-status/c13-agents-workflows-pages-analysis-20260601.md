# C-13 深度分析:缺核心頁 agents / workflows —— 概念已被 orchestrator/subagents 取代,workflows 真的不存在

**Purpose**: 釐清「缺核心頁 agents / workflows」的真實狀態。**結論:`agents` 概念其實已由 `/orchestrator` + `/subagents` 兩頁實現(取了不同名);`/workflows` 則完全不存在(無頁、無路由、無 mockup、無後端)。** UAT checklist 提到的 `/agents`、`/workflows` 是 V1 遺物。本檔為 research 分析(非 sprint plan)。
**Category**: Frontend pages + backend API gap
**Scope**: C 區研究分析 / C-13
**Created**: 2026-06-01
**Status**: Active(analysis)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — C-13 agents/workflows pages(Workflow 蒐證 + 主 session 親驗 pages 目錄不存在 + mockup 清單無 workflows)

**Related**:
- `integration-progress-20260531.md` §13(C-13 來源)
- `frontend-real-data-wiring-analysis-20260531.md`(orchestrator/subagents BACKEND-MISSING)
- `reference/design-mockups/page-agents.jsx`(orchestrator + subagents 設計)
- `next-phase-candidates.md`(無 agents/workflows 候選)

---

## 0. 一句話結論

> **「agents」不是缺,是改名了** —— mockup `page-agents.jsx` 的內容被拆成 `/orchestrator`(L1-340)+ `/subagents`(L300-440)兩個**已實作**頁(verbatim CSS,Sprint 57.19/57.34/57.38)。**「workflows」才是真的不存在** —— 無 `pages/workflows/`、無 `/workflows` 路由、**無 `page-workflows.jsx` mockup**、無後端。`agents.md` / `workflows.md` UAT checklist 是 V1 遺物(2025-12-09)。

---

## 1. agents:已實現(改名為 orchestrator + subagents,親驗)

| mockup 區段 | 對應頁 | 狀態 | 證據 |
|------------|--------|------|------|
| `page-agents.jsx` L1-340(Orchestrator)| `/orchestrator` | ✅ 實作(active,非 PROP)| `routes.config.ts:148-155` + `OrchestratorPage.tsx`(6 tab,verbatim CSS Sprint 57.34)|
| `page-agents.jsx` L300-440(Subagent Registry)| `/subagents` | ✅ 實作(active)| `routes.config.ts:156-163` + `SubagentsPage.tsx`(Sprint 57.38)|

- 親驗:`git ls-files frontend/src/pages/agents/**` → **空**(無 `/agents` 目錄)。routes.config.ts 無 `/agents` 路由。
- 即:過去 V1 叫 `/agents` 的東西,V2 拆成 orchestrator(單 agent 設定)+ subagents(子 agent registry)。**概念覆蓋,只是名稱不同**。

### ⚠️ 但 agents 兩頁是「fixture-only」(C-13 真正的洞)
| 頁 | 後端狀態 | 證據 |
|----|---------|------|
| orchestrator | **無 orchestrator-config CRUD 端點** | `frontend-real-data-wiring-analysis:53`;無 orchestrator router |
| subagents | **`subagents.py` 是 shape-stub**(回 `[]` + `not_implemented_reason`,無 ORM)| `api/v1/subagents.py:14-27,112-121`;carryover `AD-Subagent-RealList-Phase58` |

→ agents 頁的「缺」不是缺頁,是**缺後端持久化**(同 A-6 的 fixture interim debt 模式)。

---

## 2. workflows:完全不存在(親驗)

| 層 | 狀態 | 證據 |
|----|------|------|
| 前端頁 | ❌ 無 | `git ls-files frontend/src/pages/workflows/**` → 空(親驗)|
| 路由 | ❌ 無 | `routes.config.ts:127-425` 31 entries 無 `/workflows` |
| **Mockup** | ❌ **無** | `reference/design-mockups/` 無 `page-workflows.jsx`(親驗 mockup 清單僅 12 個 page-*.jsx)|
| 後端 | ❌ 無 | 無 `api/v1/workflows.py`;`main.py:59-71` router 清單無 workflows |
| Sprint 排程 | ❌ 無 | `next-phase-candidates.md` 無 workflows-page 候選 |

> **關鍵**:workflows **連 mockup 都沒有** → 依 Mockup-Fidelity 鐵律,**沒有 source of truth 可 build**。要做 workflows 必須**先有設計**(mockup 或 design spec),這是它與 agents(已有 mockup)的根本差別。

---

## 3. UAT checklist 是 V1 遺物(別被誤導)

- `claudedocs/uat/checklists/agents.md` + `workflows.md` 引用 `localhost:3005/agents`、`/api/v1/agents` CRUD、`/workflows` 拖拉編輯器 —— 這些 URL/API **在 V2 完全不存在**。
- 兩檔 last updated **2025-12-09**(V1 時代);port 3005 也是 V1(V2 是 3007)。
- → 這些是 V1 的 agent/workflow CRUD + React Flow 編輯器遺跡,**不代表 V2 規劃**。引用時須標 V1 遺物。

> 註:`routes.config.ts:82` import 的 lucide `Workflow` icon 是給 `/loop-debug` 用,**不是** `/workflows` 路由的證據。

---

## 4. 後端能力 vs 頁面(agents 的真實 backend)

V2 **有**真的 agent 執行引擎,只是沒 CRUD 端點:
- orchestrator loop(TAO/ReAct while-true):`agent_harness/orchestrator_loop/loop.py`
- subagent 4 模式 dispatch(fork/as_tool/teammate/handoff):`agent_harness/subagent/modes/`(註:此即 A-3 分析的 subagent executor)

→ 即「agent 會跑」(runtime 有),但「管理 agent 的 CRUD 頁」(config 持久化 + REST)缺。這跟 A-3(subagent 注入 loop)是不同層面:A-3 是 runtime 接線,C-13 是 management UI + CRUD 後端。

---

## 5. 給決策的最短建議

| 問題 | 答案 |
|------|------|
| agents 頁缺嗎? | ❌ 已實現(orchestrator + subagents,改名);但 fixture-only,缺後端 CRUD/持久化 |
| workflows 頁缺嗎? | ✅ **真的全缺**(頁/路由/mockup/後端 4 層皆無)|
| workflows 能直接做嗎? | ❌ **連 mockup 都沒有** → 必須先設計(mockup / design spec),否則違反 Mockup-Fidelity 鐵律 |
| agents 的下一步? | 補 orchestrator-config CRUD + subagents ORM(`AD-Subagent-RealList-Phase58`)→ 把 fixture 換真資料(同 A-6 模式)|
| workflows 的下一步? | 先**決策要不要做** workflows(V1 有、V2 至今未排程);若要 → 先 design phase 產 mockup,再走 sprint |
| UAT checklist 可信嗎? | ❌ agents.md/workflows.md 是 V1 遺物(2025-12-09),不代表 V2 |
| 急嗎? | 低;agents fixture 可用、workflows 未被任何 sprint 列為候選 = 非當前優先 |

> 不需 code。建議:agents 補後端(orchestrator CRUD + subagents ORM)可排;workflows 需先**產品決策 + 設計**,不是工程接線問題。
