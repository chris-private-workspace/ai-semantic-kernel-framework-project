# 重生策略（Rebirth Strategy）

**建立日期**：2026-04-23
**版本**：V2.0

---

## 戰略原則

V2 不是「修補 V1」，是**重新出發**。但不是「全部砍掉」，是**有意識地選擇保留與重建**。

---

## 3 區分治（最終版本）

基於「項目從未上線、無業務數據壓力」的事實：

### 區 1：Greenfield（全新建立）— 約 85%

**範圍**：
```
backend/src/
├── agent_harness/        ⭐ 全新（11 範疇）
├── platform_layer/             ⭐ 全新（governance / multi-tenancy / identity / observability）
├── adapters/             ⭐ 全新（azure_openai / anthropic / maf / mcp）
├── api/v1/               ⭐ 全新（V1 API 已封存）
├── business_domain/      ⭐ 重新設計（保留業務邏輯概念，重寫實作）
├── core/                 ⭐ 全新（純粹工具）
└── middleware/           ⭐ 全新

frontend/src/
├── pages/                ⭐ 全部重新開發（chat / agents / workflows / dashboard / devui）
├── features/             ⭐ 全新（按 11 範疇組織）
├── stores/               ⭐ 全新（合併 store + stores）
└── services/             ⭐ 全新

DB:
└── 全新 schema 設計（Alembic 從零）
```

**理由**：
- 設計哲學從 Pipeline 改為 Loop，無法疊加
- 11 範疇組織邏輯與 V1 散落結構不相容
- 廢碼比例 28%，重構成本接近重寫

### 區 2：評估後選擇性保留 / 重新定義 — 約 10%

**範圍**：`backend/src/infrastructure/`

**逐元件評估**：

| 元件 | V1 設計 | V2 處理 | 工作量 |
|------|---------|---------|-------|
| **DB connection pool** | SQLAlchemy + asyncpg | ✅ 設計保留 | 0.5 天 |
| **ORM async 化** | 同步 + async 混用 | 🔄 全 async 重寫 | 2 天 |
| **Redis client wrapper** | 通用 wrapper | ✅ 保留 | 0.5 天 |
| **RabbitMQ producer/consumer** | 已有 | ⚠️ 評估換 Temporal | TBD |
| **File / Blob storage** | 簡單抽象 | ✅ 保留 | 0.5 天 |
| **Distributed lock** | Redis-based | ✅ 保留 | 0.5 天 |
| **MAF Checkpoint 抽象** | 為 MAF 設計 | ❌ 砍掉，併入 agent_harness/07_state_mgmt | 0 |
| **新增：Vector DB 整合** | 簡陋 mem0 | ⭐ 重新設計 tenant-aware | 3-5 天 |
| **新增：Snapshot Store** | 無 | ⭐ 全新（範疇 7 用） | 2-3 天 |
| **新增：Audit Append-Only Store** | 無 | ⭐ 全新（範疇 9 用） | 2-3 天 |
| **新增：Worker Queue** | 無 | ⭐ 全新（Celery / Temporal） | 3-5 天 |
| **新增：OpenTelemetry** | 部分 | ⭐ 完整整合 | 2-3 天 |

**理由**：基礎設施是「水管」，部分設計可重用，但需配合新架構補強。

### 區 3：Knowledge Archive（知識資產保留）— 約 5%

**範圍**：
```
✅ 完整保留（不動）：
├── docs/07-analysis/V9/                    # V9 codebase 分析（極寶貴）
├── docs/07-analysis/claude-code-study/     # CC 30 wave 研究
├── docs/08-development-log/                # 5 年開發日誌
├── archived/docs-v1/01-planning/, 02-architecture/...  # 設計文件
├── claudedocs/                             # AI 協作紀錄
├── reference/                              # MAF + CC 源碼
├── graphify-out/                           # 知識圖譜

⭐ 新增封存目錄：
└── archived/v1-phase1-48/                  # 整個 V1 完整封存
    ├── backend/
    ├── frontend/
    └── README.md（封存說明 + 如何 git checkout 回來）
```

**理由**：5 年累積的設計知識是項目最大資產，必須保留。

---

## 過渡步驟

### Step 1：宣告與封存（1 天）

```bash
# 1. 在 V1 git 樹打 tag
git tag v1-final-phase48
git push origin v1-final-phase48

# 2. 建立封存目錄
mkdir -p archived/v1-phase1-48
git mv backend archived/v1-phase1-48/backend
git mv frontend archived/v1-phase1-48/frontend

# 3. 建立封存 README
echo "..." > archived/v1-phase1-48/README.md

# 4. 提交
git commit -m "chore: archive V1 (Phase 1-48) — V2 rebirth begins"
```

### Step 2：建立 V2 骨架（Phase 49 Sprint 1，1 週）

```bash
# 建立全新 backend 骨架
mkdir -p backend/src/agent_harness/{01_orchestrator_loop,02_tools,...}
mkdir -p backend/src/platform_layer/{governance,multi_tenancy,...}
mkdir -p backend/src/adapters/{_base,azure_openai,...}
mkdir -p backend/src/api/v1/{chat,tools,...}
# ... 完整目錄樹

# 建立全新 frontend 骨架
mkdir -p frontend/src/pages/{chat,agents,workflows,...}
mkdir -p frontend/src/features/{agent_loop,tool_invocation,...}

# 建立 docker-compose.dev.yml
# 建立 pyproject.toml / requirements.txt（V2 版本）
# 建立 package.json（V2 版本）
```

### Step 3：建立每個範疇的 README + ABC（Phase 49 Sprint 1-2）

每個範疇目錄下建立：
- `README.md` — 該範疇的目標、Level 標籤、API 概覽
- `__init__.py` — 公開接口
- 主要 ABC 定義（範疇 1: AgentLoop ABC, 範疇 2: ToolSpec, ...）

### Step 4：DB Schema 從零設計（Phase 49 Sprint 2）

```python
# backend/src/infrastructure/database/migrations/versions/0001_initial.py

# 不引用任何 V1 schema
# 全新設計，配合 11 範疇需求：
# - sessions (session_memory)
# - messages (對話歷史)
# - tool_calls (tool 執行紀錄)
# - tool_results
# - state_snapshots (範疇 7)
# - audit_log (append-only, 範疇 9)
# - approvals (HITL)
# - memories (各層記憶)
# - tenants
# - users
# - roles
# - tools_registry
```

### Step 5：建立 Adapters 與 Worker（Phase 49 Sprint 3）

```python
# adapters/_base/chat_client.py — ABC 定義
# adapters/azure_openai/adapter.py — 主供應商實作
# platform_layer/workers/agent_loop_worker.py — Worker 框架
# infrastructure/messaging/queue.py — 任務佇列抽象
```

### Step 6：開始 Phase 50（範疇 1 + 6 實作）

V2 真正的「開花結果」階段。

---

## 與 V1 並行策略

**項目從未上線**，所以**不需要並行運行 V1 與 V2**。

**但 V1 代碼仍可作為「活參考」**：

```bash
# 想看 V1 某個邏輯？
git checkout v1-final-phase48 -- archived/v1-phase1-48/backend/src/integrations/orchestration/risk_assessor/

# 抽取後再 checkout 回 V2
git checkout HEAD
```

---

## 處理 V1 寶貴邏輯（避免完全浪費）

V1 雖然 27% 對齊，但**部分設計邏輯有價值**，可作為 V2 的設計輸入：

### V1 → V2 的「邏輯遷移」清單

| V1 模組 | 邏輯價值 | V2 接收位置 | 遷移方式 |
|--------|---------|-----------|---------|
| `risk_assessor/assessor.py` (639 LOC) | 風險評估規則表設計 | `platform_layer/governance/risk/policies/` | 提取規則 YAML，重寫引擎 |
| `hitl/controller.py` (788 LOC) | Teams 通知整合 | `platform_layer/governance/hitl/teams_notifier.py` | 重寫，借鑒 Teams API 整合代碼 |
| `audit/logger.py` | Audit log 格式設計 | `platform_layer/governance/audit/` | 借鑒欄位設計 |
| `intent_router/llm_classifier/` | LLM 分類器 prompts | `agent_harness/05_prompt_builder/templates/` | 移植 prompt 模板 |
| `pipeline/steps/step1_memory.py` | 記憶讀取邏輯 | 範疇 3 重寫但借鑒接入點 | 重寫 |
| `dispatch/executors/team_agent_adapter.py` | MAF GroupChat 整合 | `adapters/maf/group_chat.py` | 直接遷移 |
| MCP servers (`mcp/servers/*`) | 企業 MCP 整合代碼 | `adapters/mcp/` | 直接遷移（MCP 是標準） |

### 不遷移的 V1 模組

| V1 模組 | 不遷移原因 |
|--------|-----------|
| `claude_sdk/autonomous/` | 不在主流量，PoC 性質 |
| `claude_sdk/orchestrator/` | 與 Phase 48 自建 orchestrator 重複 |
| `hybrid/` 整個目錄 | Phase 48 已決定淘汰 |
| `swarm/` | PoC，未驗證價值 |
| 整個 `pipeline/` | Pipeline 思維本身要拋棄 |
| `poc/` | 整個 PoC 目錄 |

---

## 風險管理

### 風險 1：4 個月時程超期

**緩解**：
- 每個 Phase 結束強制 retro
- 範疇優先級清晰（核心 6 個範疇 vs 進階 5 個）
- 砍 scope 而非延期

### 風險 2：開發過程中又發現新範疇

**緩解**：
- `01-eleven-categories-spec.md` 是 living document，可加範疇
- 但只有「跨多個範疇出現的需求」才升級為新範疇

### 風險 3：Azure OpenAI GPT-5.4 能力不足

**緩解**：
- Adapter 層支援多供應商
- Phase 49 早期測試 GPT-5.4 的 native function calling 與 parallel tool calls
- 必要時公司爭取開放 Claude

### 風險 4：Worker Queue 選型錯誤

**緩解**：
- Phase 49 Sprint 3 做 PoC（Celery vs Temporal）
- 透過 `infrastructure/messaging/queue.py` 抽象，可切換

### 風險 5：V1 的散落代碼有遺漏的有用邏輯

**緩解**：
- V1 完整封存於 `archived/`
- 任何時候可 checkout 參考
- 開發過程中遇到「V1 是怎麼做的」隨時翻

---

## V1 → V2 對應表（快速參考）

| V1 路徑 | V2 對應 |
|---------|---------|
| `integrations/orchestration/pipeline/` | ❌ 整個淘汰（Pipeline 思維拋棄） |
| `integrations/orchestration/dispatch/executors/` | → `agent_harness/01_orchestrator_loop/` + `11_subagent/` |
| `integrations/orchestration/intent_router/` | → 淘汰（LLM 自主路由） |
| `integrations/orchestration/risk_assessor/` | → `platform_layer/governance/risk/` |
| `integrations/orchestration/hitl/` | → `platform_layer/governance/hitl/` |
| `integrations/orchestration/audit/` | → `platform_layer/governance/audit/` |
| `integrations/orchestration/transcript/` | → `agent_harness/07_state_mgmt/` |
| `integrations/orchestration/resume/` | → `agent_harness/07_state_mgmt/` |
| `integrations/agent_framework/builders/` | → `adapters/maf/` |
| `integrations/agent_framework/clients/` | → `adapters/_base/` + `adapters/anthropic/` |
| `integrations/agent_framework/memory/` | → `agent_harness/03_memory/` |
| `integrations/agent_framework/multiturn/` | → `agent_harness/04_context_mgmt/` |
| `integrations/claude_sdk/*` | → 大部分淘汰，僅 hooks 設計借鑒至 `09_guardrails/` |
| `integrations/hybrid/` | ❌ 整個淘汰 |
| `integrations/swarm/` | ❌ 淘汰，11_subagent 重新設計 |
| `integrations/a2a/` | → `adapters/maf/` 或淘汰 |
| `integrations/ag_ui/` | ❌ 淘汰，自建 SSE 事件規範 |
| `integrations/mcp/` | → `adapters/mcp/` |
| `integrations/memory/` | → `agent_harness/03_memory/` |
| `integrations/learning/` | → 淘汰或併入範疇 10 |
| `integrations/llm/` | → `adapters/_base/` |
| `integrations/knowledge/` | → 暫保留設計 idea，併入範疇 3 |
| `integrations/patrol/correlation/rootcause/audit/incident/` | → `business_domain/`（重新設計） |
| `integrations/poc/` | ❌ 整個淘汰 |
| `domain/` | → 部分歸入 `business_domain/`，部分歸入 `agent_harness` |
| `infrastructure/` | ⚠️ 部分保留，部分重寫（見區 2） |
| `core/` | ⭐ 重新設計（V1 太雜） |

---

## 預期成果

Phase 49-55 結束時：

1. ✅ V1 完全封存於 `archived/`
2. ✅ V2 backend 4 層架構建立
3. ✅ 11 範疇全部達 Level 4+
4. ✅ Frontend 重新開發完成
5. ✅ 業務領域功能接入新 harness
6. ✅ Docker 化開發環境
7. ✅ 真實對齊度從 27% → 75%+

---

## 下一步

確認重生策略後：
- `04-anti-patterns.md`：V1 反模式清單（避免重蹈覆轍）
- `05-reference-strategy.md`：參考資料策略
- `06-phase-roadmap.md`：詳細 Sprint 規劃
