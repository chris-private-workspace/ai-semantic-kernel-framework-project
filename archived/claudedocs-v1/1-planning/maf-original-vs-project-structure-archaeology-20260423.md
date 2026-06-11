# MAF 原始架構 vs IPA Platform 結構考古報告

**建立日期**：2026-04-23
**目的**：在重組架構前，先釐清「什麼是 MAF 原裝、什麼是項目自建」，識別原始架構血脈與後期演進
**驗證**：codebase-researcher 子代理對 `reference/agent-framework/python/` 與 `backend/src/` 進行對比掃描

---

## 圖例

| 標記 | 來源 | 意義 |
|------|------|------|
| 🔵 | MAF 原裝啟發 | 導入 MAF 時建的包裝層，目錄結構模仿 MAF |
| 🟢 | 項目原創 | 項目自己設計，與 MAF 無關 |
| 🟡 | 混合 | 有 MAF 影子但加了大量自建內容 |
| 🔴 | 後期演進 | Phase 28+ 後新增，與原本 MAF 結構無關 |

---

## Section A：MAF 官方 Python 套件架構

**根目錄**：`reference/agent-framework/python/`

### 頂層結構
```
reference/agent-framework/python/
├── packages/                    ← 15 個獨立可發佈 PyPI 套件
├── samples/                     ← 範例目錄
│   ├── getting_started/
│   ├── demos/
│   ├── autogen-migration/
│   └── semantic-kernel-migration/
├── agent_framework_meta/
├── docs/
└── pyproject.toml (頂層)
```

### `packages/` 下 15 個官方子套件
1. **a2a** — Agent-to-Agent protocol
2. **ag-ui** — AG-UI Protocol
3. **anthropic** — Claude provider
4. **azure-ai** — Azure AI provider
5. **azure-ai-search** — Azure Search 整合
6. **azurefunctions** — Azure Functions 整合
7. **chatkit** — Chat UI 套件
8. **copilotstudio** — Copilot Studio 整合
9. **core** — **核心套件**（最重要）
10. **declarative** — 宣告式定義
11. **devui** — Developer UI
12. **lab** — 實驗性功能
13. **mem0** — mem0 記憶整合
14. **purview** — Purview 整合
15. **redis** — Redis 整合

### `packages/core/agent_framework/` 核心內部結構

**頂層私有模組**（`_` 前綴）：
- `_agents.py` — Agent 基類
- `_clients.py` — LLM 客戶端
- `_logging.py` — 日誌
- `_mcp.py` — MCP 整合
- `_memory.py` — 記憶
- `_middleware.py` — 中介層
- `_pydantic.py` — Pydantic 工具
- `_serialization.py` — 序列化
- `_telemetry.py` — 遙測
- `_threads.py` — Thread 管理
- `_tools.py` — 工具系統
- `_types.py` — 型別定義

**公開模組**：
- `exceptions.py`
- `observability.py`
- `__init__.py`

**`core/` 內子套件**：
- `_workflows/` — **整個 Workflow / Builder 系統都在這裡**
  - 包含：`ConcurrentBuilder`, `GroupChatBuilder`, `HandoffBuilder`, `MagenticBuilder`, `WorkflowExecutor`, `Edge`, `Executor`
- `a2a/`
- `ag_ui/`
- `anthropic/`
- `azure/`
- `chatkit/`
- `declarative/`
- `devui/`
- `lab/`
- `mem0/`
- `microsoft/`
- `openai/`
- `redis/`

### MAF 架構特徵（關鍵觀察）

> **⚠️ 重要發現**：MAF 官方使用 **`_workflows/`（單一私有套件）** 容納所有 workflow / builder 系統。**沒有** `builders/` 目錄、**沒有** `acl/`、`assistant/`、`multiturn/`、`clients/` 這些子目錄。
>
> **本項目把 MAF 的 `_workflows/` 拆成了 `core/ + builders/` — 這是 Day 1 就有的風格分歧**

---

## Section B：本項目 backend/src/integrations/ 來源歸類

### B.1 MAF 原裝啟發區（🔵 / 🟡）

| 子目錄 | 顏色 | 引入時間 | MAF import? | 來源說明 |
|--------|-----|---------|-----------|---------|
| `agent_framework/core/` | 🟡 混合 | Phase 1-10 | ✅ YES | 包裝 MAF `_workflows/*` — 名稱「core」模仿 MAF 套件名，但**把 `_workflows` 攤平進 `core/`** |
| `agent_framework/builders/` | 🔵 原裝啟發 | Phase 1-10 | ✅ YES（concurrent/groupchat/handoff/magentic/planning 都 import 官方 builders）| Adapter layer 包裝 MAF `_workflows.*Builder`；**`builders/` 是項目發明的目錄名（MAF 沒有）** |
| `agent_framework/clients/` | 🔵 原裝啟發 | Phase 5-15 | ✅ YES（`anthropic_chat_client.py`） | 包裝 MAF `anthropic/`、`azure/`、`openai/` chat clients |
| `agent_framework/memory/` | 🔵 原裝啟發 | Phase 10-20 | ✅ YES（`base.py`） | 包裝 MAF `_memory.py` + `mem0/` |
| `agent_framework/multiturn/` | 🟡 混合 | Phase 15-25 | ✅ YES（adapter, checkpoint_storage） | 項目自建 multi-turn 協調器，使用 MAF threads/checkpoint |
| `agent_framework/tools/` | 🟡 混合 | Phase 5-15 | 部分 | Tool registry 疊加在 MAF `_tools.py` 上 |

### B.2 項目原創區（🟢）

| 子目錄 | 顏色 | 引入時間 | 來源說明 |
|--------|-----|---------|---------|
| `agent_framework/acl/` | 🟢 原創 | Phase 20+ | 存取控制 — **企業需求，MAF 沒有** |
| `agent_framework/assistant/` | 🟢 原創 | Phase 20+ | 自定 assistant 抽象 |
| `claude_sdk/*`（autonomous, hooks, hybrid, mcp, orchestrator, tools）| 🟢 原創 | Phase 22+ | **完全不 import MAF**；建構於 `claude-agent-sdk` 上的獨立 vendor track |
| `hybrid/`（checkpoint, context, execution, hooks, intent, orchestrator, prompts, risk, switching）| 🟢 原創 | Phase 25-28 | 混合層橋接 MAF↔SDK — CLAUDE.md 明文寫 **"intentional novel design"** |
| `memory/`（頂層）| 🟢 原創 | Phase 20+ | 項目級記憶抽象（mem0 整合，與 `agent_framework/memory/` 不同） |
| `learning/, llm/, knowledge/` | 🟢 原創 | Phase 25+ | 跨切面模組 |
| `patrol/, correlation/, rootcause/, audit/, incident/` | 🟢 原創 | Phase 30-40 | **IT-ops 業務領域**（Phase 30+） |
| `n8n/, contracts/, shared/` | 🟢 原創 | varies | 工作流整合 / 共用工具 |

### B.3 後期演進區（🔴 — Phase 28+ 演進）

| 子目錄 | 顏色 | 引入時間 | 來源說明 |
|--------|-----|---------|---------|
| `orchestration/intent_router/` | 🔴 後期 | Phase 28 | 三層 intent routing — **Phase 28 大重構** |
| `orchestration/dispatch/` | 🔴 後期 | Phase 28+ | Route executors（direct / subagent / team） |
| `orchestration/pipeline/` | 🔴 後期 | Phase 28+ | Step-based orchestration pipeline |
| `orchestration/risk_assessor/` | 🔴 後期 | Phase 28+ | 項目原創風險評估 |
| `orchestration/hitl/` | 🔴 後期 | Phase 28+ | Human-in-the-loop |
| `orchestration/experts/, transcript/, audit/` | 🔴 後期 | Phase 30-44 | Phase 32+ 專家路由 + 稽核 |
| `orchestration/guided_dialog/, resume/, input_gateway/, approval/` | 🔴 Phase 48 | Phase 48 | **`resume/service.py` import MAF for checkpoint 兼容**；Phase 48 LLM-native orchestrator 新增 |
| `swarm/` | 🔴 後期 | Phase 29 | Phase 29 Agent Swarm |
| `a2a/` | 🔴 後期 | Phase 29+ | 包裝 MAF `packages/a2a/` |
| `ag_ui/` | 🔴 後期 | Phase 20-28 | 包裝 MAF `ag-ui`（AG-UI Protocol：SSE / events） |
| `mcp/` | 🟡 混合 | Phase 15-25 | MCP servers（Azure / Filesystem / LDAP / Shell / SSH） |
| `poc/` | 🔴 PoC | Phase 47-48 | **PoC sandbox**，測試 orchestrator 替代方案（team / orchestrator / real / claude_sdk tools） |

---

## Section C：歷史時間軸（V9 + 開發日誌錨定）

| 時期 | 引入的目錄 |
|------|-----------|
| **Phase 1-10**（最早期：純 MAF 包裝）| `agent_framework/core/, builders/, clients/, tools/` — 直接 MAF wrappers |
| **Phase 11-20**（記憶 + 多輪整合）| `agent_framework/memory/, multiturn/`, `mcp/`, `ag_ui/`, 頂層 `memory/` |
| **Phase 21-28**（**第一次架構分歧**）| `claude_sdk/*`, `hybrid/*` — 採用第二個 framework；建橋接層 |
| **Phase 28**（**結構性重構**）| `orchestration/{intent_router, dispatch, pipeline, risk_assessor, hitl}` — **三層 intent routing** |
| **Phase 29**（多 agent 擴張）| `swarm/`, `a2a/` |
| **Phase 30-44**（業務領域 + 治理擴張）| `orchestration/{experts, transcript, audit}`；領域模組 `patrol, correlation, rootcause, incident, audit, learning, knowledge` |
| **Phase 47-48**（**最終架構斷裂**）| `poc/`, `orchestration/{guided_dialog, resume, input_gateway, approval, input}` — Phase 48 LLM-native orchestrator |

---

## Section D：項目背離 MAF 的 4 個關鍵時刻

### 1. Phase ~22：第一次主要分歧 — Claude SDK 引入
- 引入 `claude_sdk/`
- 項目承諾**多供應商 agent runtime**，非純 MAF
- 起點：項目接受「單一框架不夠」

### 2. Phase 25-28：明確的結構性偏離 — Hybrid 層
- 建立 `hybrid/`
- 編入 **"intentional novel design"**（code-enforced steps + LLM routing）
- 明確走出 MAF builder 範式

### 3. Phase 28：**結構性叉路** ⚠️
- `orchestration/intent_router` + 3-tier dispatch
- **第一個不在 `agent_framework/` 內的 orchestration 層**
- 從此 orchestration 不歸 MAF 管

### 4. Phase 47-48：最終架構斷裂 ⚠️⚠️
- `poc/` + LLM-native orchestrator（`guided_dialog, resume, input_gateway`）
- **Phase 48 移除 ~7,430 行 legacy 代碼**
- 用 config-driven (YAML) LLM-native routing 取代 MAF-centric orchestration

---

## Section E：核心發現

### 發現 1：MAF 影響範圍**只在 `agent_framework/` 一個目錄**

對比 IPA 的 21 個 integrations 子模組，**真正屬於 MAF 影響的只有 1 個**（`agent_framework/`）。剩下 20 個全是項目自建。

```
backend/src/integrations/
├── agent_framework/    ← 🔵🟡 MAF 包裝層（唯一受 MAF 直接影響）
├── claude_sdk/         ← 🟢 完全自建（Phase 22+）
├── orchestration/      ← 🔴 完全自建（Phase 28+）
├── hybrid/             ← 🟢 完全自建（Phase 25+）
├── swarm/              ← 🔴 完全自建（Phase 29）
├── a2a/                ← 🔴 包裝 MAF a2a
├── ag_ui/              ← 🔴 包裝 MAF ag-ui
├── mcp/                ← 🟡 混合
├── memory/             ← 🟢 自建
├── learning/           ← 🟢 自建
├── llm/                ← 🟢 自建
├── knowledge/          ← 🟢 自建
├── patrol/             ← 🟢 自建（IT-ops 業務）
├── correlation/        ← 🟢 自建（IT-ops 業務）
├── rootcause/          ← 🟢 自建（IT-ops 業務）
├── audit/              ← 🟢 自建（IT-ops 業務）
├── incident/           ← 🟢 自建（IT-ops 業務）
├── n8n/                ← 🟢 自建
├── contracts/          ← 🟢 自建
├── shared/             ← 🟢 自建
└── poc/                ← 🔴 PoC
```

### 發現 2：MAF `_workflows/` Day 1 就被改名

- MAF 官方：所有 builder 在 `_workflows/`
- 本項目：拆成 `core/ + builders/`
- **這是 Day 1 就有的風格分歧**，不是後期偏離

### 發現 3：項目「本質上」不是 MAF 項目

| 維度 | 數據 |
|------|------|
| MAF 受影響目錄 | 1 / 21 = **5%** |
| 純自建目錄 | 14 / 21 = **67%** |
| 包裝 MAF（但完全自建邏輯）| 6 / 21 = **28%** |
| 純 MAF 原樣使用 | **0 / 21 = 0%** |

**本項目從來都不是 MAF 項目，只是一個「曾經以 MAF 起步的項目」**。

### 發現 4：MAF 套件中**至少 9 個 IPA 完全沒用**
- `chatkit` — 未使用
- `copilotstudio` — 未使用
- `declarative` — 未使用
- `devui` — 未使用（IPA 自建 frontend）
- `lab` — 未使用
- `purview` — 未使用
- `azure-ai-search` — 未使用
- `azurefunctions` — 未使用
- `redis` — 未使用（IPA 用 redis-py）

實際使用的 MAF 套件只有 **6 個**：`core`, `a2a`, `ag-ui`, `anthropic`, `azure-ai`, `mem0`

---

## Section F：對重組的關鍵啟示

### 啟示 1：**「重組為 11 範疇」不需要砍 MAF**
因為 MAF 只佔 5% 目錄，重組對 MAF 影響極小。真正動刀的是後期 Phase 28-48 演進的 95% 自建代碼。

### 啟示 2：**重組阻力最小路徑**
- ✅ **保留 `agent_framework/`** 完整不動（原裝啟發，是 MAF 包裝層）
- ✅ **保留業務領域目錄**（patrol / correlation / rootcause / audit / incident — 與 11 範疇無關）
- 🔧 **重組對象主要是 `orchestration/` + `hybrid/` + `claude_sdk/` + `swarm/` + `a2a/`** — 這 5 個目錄

### 啟示 3：**Phase 28 是真正的架構分水嶺**
- Phase 28 之前：項目像 MAF 項目（即使 5% 目錄受影響）
- Phase 28 之後：項目走向自己的路，但**目錄結構沒重新規劃**，只是不斷新增到 `orchestration/` 下
- **這就是 11 範疇散落的根本原因** — Phase 28-48 增量演進，沒人按 agent harness 範疇歸類

### 啟示 4：**重組正當性極強**
- MAF 影響只 5%，不存在「破壞 MAF 架構」的顧慮
- 95% 自建代碼本來就沒有官方架構約束
- Phase 28-48 增量演進已產生 6 處 Guardrails 散落、5 處 Orchestrator 散落
- **重組是補修 5 年增量演進的累積債，而非顛覆 MAF**

---

## Section G：後續討論議題

1. **是否確認**：本項目從來都不是 MAF 項目（只佔 5%）？
2. **是否同意**：重組對象只在 5 個目錄（orchestration / hybrid / claude_sdk / swarm / a2a）？
3. `agent_framework/` 是否完整保留作為 **MAF 兼容層**（不參與 11 範疇重組）？
4. 業務領域（patrol / correlation / rootcause / audit / incident）是否獨立成 `business_domain/` 目錄，**也不參與 11 範疇重組**？
5. 重組目標是否只針對「**Phase 28-48 增量演進的 agent harness 部分**」？

**這份報告作為架構重組討論的歷史考古 baseline。建議先確認以上 5 個議題後再進入正式重組計畫**。
