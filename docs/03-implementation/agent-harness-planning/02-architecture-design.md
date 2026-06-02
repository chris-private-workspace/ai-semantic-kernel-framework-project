# V2 架構設計

**建立日期**：2026-04-23
**版本**：V2.0

---

## 整體架構（5 層 + 跨切面）

> **設計校正（2026-04-23）**：原 4 層設計缺 `business_domain/` 歸屬、`platform_layer/` 過於肥大。修訂為 5 層 + 跨切面。

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (React 18)                       │
│  pages/chat-v2 + pages/agents + pages/workflows + pages/devui    │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓ HTTP / SSE
┌──────────────────────────────────────────────────────────────────┐
│  Layer 1: API Gateway (FastAPI)                                  │
│              backend/src/api/v1/  (V2 全新 API)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│  Layer 2: Business Domain（IT-ops 業務領域）                      │
│  backend/src/business_domain/                                    │
│  patrol / correlation / rootcause / business_audit / incident   │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓ 業務呼叫 harness
┌──────────────────────────────────────────────────────────────────┐
│  Layer 3: Agent Harness Core（11 範疇 + 範疇 12 cross-cutting）   │
│  backend/src/agent_harness/                                      │
│  orchestrator_loop / tools / memory / context_mgmt / ...         │
│  + observability/ (範疇 12 ABC，實作在 cross-cutting 層)          │
└──────┬─────────────────────────────────────────────┬─────────────┘
       ↓                                              ↓
┌─────────────────────┐                ┌──────────────────────────┐
│  Layer 4a: Adapters │                │  Cross-Cutting:          │
│  backend/src/adapters│                │  governance / identity / │
│  (主鏈，被 harness 用)│                │  observability           │
│  azure_openai / maf /│                │  ⭐ 範疇 12 實作位置        │
│  anthropic / mcp /...│                │  backend/src/governance/ │
└──────────┬──────────┘                │  backend/src/identity/   │
           ↓                            │  backend/src/observability│
                                        └──────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│  Layer 4b: Runtime（執行平面，反向依賴例外）                      │
│  backend/src/runtime/                                            │
│  workers/ ← 反向呼叫 agent_harness 跑 loop                       │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│  Layer 5: Infrastructure（DB / Cache / MQ / Storage / Vector）   │
│  backend/src/infrastructure/                                    │
└──────────────────────────────────────────────────────────────────┘
```

### 為什麼是這個分層

| 層 | 角色 | 依賴方向 |
|---|------|---------|
| **API** | HTTP 入口 | 呼叫 business_domain 或 agent_harness |
| **business_domain** | IT-ops 業務（patrol 等） | 呼叫 agent_harness |
| **agent_harness** | 11 範疇核心 + 範疇 12 ABC（橫切，實作在 observability/） | 呼叫 adapters，使用 cross-cutting |
| **adapters** | 供應商適配（LLM / MAF / MCP） | 呼叫 infrastructure |
| **runtime** | Worker 執行平面 | **反向**呼叫 agent_harness（執行 loop）|
| **cross-cutting** | governance / identity / observability | 被任意層使用 |
| **infrastructure** | DB / Cache / MQ / Storage | 不依賴上層 |

### 原 platform_layer/ 拆解說明（重要校正）

> **校正**：原 `platform_layer/` 集合 5 個性質完全不同的子系統會變「上帝層」。已拆為獨立目錄：

```
backend/src/
├── governance/                   # 治理（HITL / Risk / Audit / Compliance）
├── identity/                     # 認證授權（Auth / RBAC / Multi-tenancy）
├── observability/                # 可觀測性（Tracing / Metrics / Logging / Cost）
└── runtime/                      # 執行平面（Workers / Task Queue / Scheduler）
```

### Cross-Cutting Concerns 處理

`governance` / `identity` / `observability` 是**橫切關注點**：
- 可被任意層 import（單向）
- 自身不依賴 agent_harness / business_domain
- 透過 middleware / decorator / context manager 注入

---

## Backend 完整目錄結構

```
backend/src/
│
├── api/                           # ─── API 層 ───
│   └── v1/
│       ├── chat/                  # Chat 對話 API（觸發 agent loop）
│       ├── tools/                 # Tool 註冊與測試 API
│       ├── memory/                # Memory CRUD API
│       ├── sessions/              # Session 管理
│       ├── audit/                 # Audit log 查詢
│       ├── governance/            # HITL approval API
│       ├── agents/                # Agent 管理（CRUD）
│       ├── workflows/             # Workflow 編輯器 API
│       ├── verification/          # Verification 結果查詢
│       └── _internal/             # 內部 API（worker callback 等）
│
├── agent_harness/                 # ─── Layer 1: 11 範疇核心 ───
│   ├── orchestrator_loop/      # 範疇 1
│   │   ├── loop.py                #   核心 TAO loop
│   │   ├── events.py              #   Loop events（SSE）
│   │   ├── termination.py         #   終止條件
│   │   └── tests/
│   │
│   ├── tools/                  # 範疇 2
│   │   ├── registry.py            #   ToolRegistry 統一註冊
│   │   ├── spec.py                #   ToolSpec 定義
│   │   ├── executor.py            #   Tool execution engine
│   │   ├── permissions.py         #   權限檢查
│   │   ├── sandbox.py             #   Sandbox 抽象
│   │   ├── builtin/               #   內建工具
│   │   │   ├── memory_tools.py    #     memory_search / memory_write
│   │   │   ├── search_tools.py    #     web_search / kb_search
│   │   │   ├── exec_tools.py      #     sql_query / python_sandbox
│   │   │   ├── hitl_tools.py      #     request_approval
│   │   │   └── subagent_tools.py  #     task_spawn / handoff
│   │   ├── enterprise/            #   企業工具（接 platform_layer/business）
│   │   │   ├── d365_tools.py
│   │   │   ├── erp_tools.py
│   │   │   ├── servicenow_tools.py
│   │   │   └── ...
│   │   └── tests/
│   │
│   ├── memory/                 # 範疇 3
│   │   ├── layers/                #   5 層記憶
│   │   │   ├── system_memory.py
│   │   │   ├── tenant_memory.py
│   │   │   ├── role_memory.py
│   │   │   ├── user_memory.py
│   │   │   └── session_memory.py
│   │   ├── retrieval.py           #   多層檢索引擎
│   │   ├── extraction.py          #   背景記憶提取
│   │   ├── consolidation.py       #   記憶合併
│   │   └── tests/
│   │
│   ├── context_mgmt/           # 範疇 4
│   │   ├── compactor.py           #   Compaction
│   │   ├── observation_masker.py  #   Observation masking
│   │   ├── jit_retrieval.py       #   Just-in-time retrieval
│   │   ├── token_counter.py       #   Token 計算
│   │   └── tests/
│   │
│   ├── prompt_builder/         # 範疇 5
│   │   ├── builder.py             #   PromptBuilder 主類
│   │   ├── strategies.py          #   位置策略（lost-in-middle）
│   │   ├── templates.py           #   System prompt 模板
│   │   └── tests/
│   │
│   ├── output_parser/          # 範疇 6
│   │   ├── parser.py              #   Native tool_calls 解析
│   │   ├── classifier.py          #   Output 分類（tool / handoff / final）
│   │   └── tests/
│   │
│   ├── state_mgmt/             # 範疇 7
│   │   ├── state.py               #   LoopState typed dataclass
│   │   ├── checkpointer.py        #   Checkpoint 機制
│   │   ├── time_travel.py         #   Time-travel debug
│   │   └── tests/
│   │
│   ├── error_handling/         # 範疇 8
│   │   ├── categories.py          #   4 類錯誤定義
│   │   ├── retry.py               #   Retry policy
│   │   ├── recovery.py            #   LLM-recoverable 處理
│   │   └── tests/
│   │
│   ├── guardrails/             # 範疇 9
│   │   ├── engine.py              #   GuardrailEngine 主類
│   │   ├── input_guardrail.py     #   Input 檢查（PII / jailbreak）
│   │   ├── output_guardrail.py    #   Output 檢查（毒性 / 敏感）
│   │   ├── tool_guardrail.py      #   Tool 檢查（權限 / 風險）
│   │   ├── tripwire.py            #   Tripwire 機制
│   │   └── tests/
│   │
│   ├── verification/           # 範疇 10
│   │   ├── verifier_base.py       #   Verifier ABC
│   │   ├── rules_verifier.py      #   Rules-based
│   │   ├── llm_judge.py           #   LLM-as-judge
│   │   ├── visual_verifier.py     #   Visual（保留接口）
│   │   ├── correction_loop.py     #   Self-correction
│   │   └── tests/
│   │
│   ├── subagent/               # 範疇 11
│   ├── observability/           # 範疇 12（cross-cutting ABC）
│   │   ├── _abc.py              #   Tracer ABC
│   │   └── README.md            #   實作在 backend/src/observability/
│   ├── _contracts/              # ⭐ 跨範疇 single-source 型別 (見 17.md)
│   │   ├── chat.py              #   ChatRequest/Response/Message/StopReason
│   │   ├── tools.py             #   ToolSpec/ToolCall/ToolResult/Annotations
│   │   ├── state.py             #   LoopState/TransientState/DurableState
│   │   ├── events.py            #   LoopEvent + 子類
│   │   ├── memory.py            #   MemoryHint
│   │   ├── prompt.py            #   PromptArtifact/CacheBreakpoint
│   │   ├── verification.py      #   VerificationResult
│   │   ├── subagent.py          #   SubagentBudget/Result
│   │   ├── observability.py     #   TraceContext/MetricEvent
│   │   └── hitl.py              #   ApprovalRequest/Decision/HITLPolicy
│   └── hitl/                    # §HITL 中央化
│       ├── _abc.py              #   HITLManager ABC
│       └── README.md
│       ├── dispatcher.py          #   SubagentDispatcher
│       ├── modes/                 #   4 種模式
│       │   ├── fork.py
│       │   ├── teammate.py
│       │   ├── handoff.py
│       │   └── as_tool.py
│       ├── mailbox.py             #   Teammate 通信
│       └── tests/
│
├── platform_layer/                      # ─── Layer 2: 平台服務 ───
│   ├── governance/                # 治理層（與 9 號範疇配合）
│   │   ├── hitl/                  #   Human-in-the-loop
│   │   │   ├── controller.py
│   │   │   ├── teams_notifier.py  #   Microsoft Teams 整合
│   │   │   └── approval_store.py
│   │   ├── risk/                  #   Risk assessment
│   │   │   ├── assessor.py
│   │   │   └── policies/          #     YAML-based policies
│   │   ├── audit/                 #   Audit log（不可篡改）
│   │   │   ├── logger.py
│   │   │   └── append_only_store.py
│   │   └── compliance/            #   合規檢查
│   │
│   ├── multi_tenancy/             # 多租戶
│   │   ├── tenant_context.py
│   │   ├── isolation.py
│   │   └── policy_loader.py
│   │
│   ├── identity/                  # 認證授權
│   │   ├── auth.py                #   Entra ID / LDAP
│   │   ├── rbac.py                #   Role-based access control
│   │   └── permissions.py
│   │
│   ├── observability/             # 可觀測性
│   │   ├── tracing.py             #   OpenTelemetry tracing
│   │   ├── metrics.py             #   Prometheus metrics
│   │   ├── logging.py             #   Structured logging
│   │   └── cost_tracking.py       #   LLM 成本追蹤
│   │
│   └── workers/                   # Agent worker
│       ├── agent_loop_worker.py   #   執行 agent loop 的 worker
│       ├── task_queue.py          #   任務佇列抽象
│       └── result_store.py        #   結果儲存
│
├── adapters/                      # ─── Layer 3: 適配層 ───
│   ├── _base/                     # Base ABCs
│   │   ├── chat_client.py         #   ChatClient ABC
│   │   ├── tool_format.py         #   工具格式適配
│   │   └── message_format.py      #   訊息格式適配
│   │
│   ├── azure_openai/              # 主供應商
│   │   ├── client.py              #   GPT-5.4 / mini / nano
│   │   ├── adapter.py             #   ChatClient 實作
│   │   └── code_interpreter.py    #   Azure Code Interpreter（如使用）
│   │
│   ├── anthropic/                 # Claude（公司開放後）
│   │   ├── client.py
│   │   └── adapter.py
│   │
│   ├── openai/                    # 直接 OpenAI（備援）
│   │   └── ...
│   │
│   ├── maf/                       # Microsoft Agent Framework Builder
│   │   ├── group_chat.py
│   │   ├── concurrent.py
│   │   ├── handoff.py
│   │   ├── magentic.py
│   │   └── nested_workflow.py
│   │
│   └── mcp/                       # MCP Servers
│       ├── client.py
│       ├── filesystem.py
│       ├── shell.py
│       ├── ldap.py
│       └── ...
│
├── business_domain/               # ─── 業務領域（IT-ops） ───
│   ├── patrol/                    # 巡檢業務（重新設計）
│   ├── correlation/               # 關聯分析
│   ├── rootcause/                 # 根因分析
│   ├── audit/                     # 業務稽核（不同於 platform.governance.audit）
│   └── incident/                  # 事件管理
│
├── infrastructure/                # ─── Layer 4: 基礎設施 ───
│   ├── database/                  # PostgreSQL
│   │   ├── orm.py                 #   SQLAlchemy async
│   │   ├── connection.py
│   │   ├── models/                #   ORM models（重新設計）
│   │   └── migrations/            #   Alembic migrations（從零）
│   │
│   ├── cache/                     # Redis
│   │   └── redis_client.py
│   │
│   ├── messaging/                 # 訊息佇列
│   │   ├── queue.py               #   抽象介面
│   │   └── backend/               #   實作（Celery / RQ / Temporal）
│   │
│   ├── storage/                   # Object storage
│   │   ├── blob_store.py
│   │   └── snapshot_store.py      #   範疇 7 用
│   │
│   ├── distributed_lock/          # Redis-based lock
│   │
│   └── vector_db/                 # Qdrant 整合
│       ├── client.py
│       └── tenant_namespace.py
│
├── core/                          # ─── 核心工具（純函式） ───
│   ├── types/                     # Pydantic 類型定義
│   ├── exceptions/                # 全局異常
│   ├── config/                    # 配置管理
│   ├── crypto/                    # 加密工具
│   └── utils/                     # 雜項
│
└── middleware/                    # FastAPI 中介層
    ├── auth.py
    ├── tenant_context.py
    ├── tracing.py
    └── error_handler.py
```

---

## Frontend 目錄結構

```
frontend/src/
│
├── pages/                         # 頁面（**全部重新開發**）
│   ├── chat/                      # ⭐ V2 Chat 主介面
│   │   ├── ChatPage.tsx
│   │   ├── components/
│   │   │   ├── MessageList/
│   │   │   ├── ToolCallCard/
│   │   │   ├── ThinkingBlock/
│   │   │   ├── HITLApprovalCard/
│   │   │   ├── VerificationStatus/
│   │   │   └── LoopProgressIndicator/
│   │   └── hooks/
│   │
│   ├── agents/                    # Agent 管理（重新設計）
│   ├── workflows/                 # Workflow 編輯器（重新設計）
│   ├── dashboard/                 # 主儀表板
│   ├── devui/                     # 開發者工具（範疇可視化）
│   │   ├── LoopVisualizer.tsx     #   Loop 流程可視化
│   │   ├── CategoryStatus.tsx     #   11 範疇成熟度
│   │   ├── StateTimeTravel.tsx    #   時間旅行除錯
│   │   └── ...
│   │
│   ├── audit/                     # Audit log 瀏覽
│   ├── memory/                    # Memory 管理
│   └── governance/                # 治理面板（HITL 審批）
│
├── features/                      # ⭐ 按 11 範疇組織的功能組件
│   ├── agent_loop/                # 範疇 1 視覺化
│   ├── tool_invocation/           # 範疇 2 顯示
│   ├── memory_layers/             # 範疇 3 顯示
│   ├── context_health/            # 範疇 4 健康度
│   ├── prompt_inspector/          # 範疇 5 檢視
│   ├── tool_call_renderer/        # 範疇 6 渲染
│   ├── state_timeline/            # 範疇 7 時間軸
│   ├── error_panel/               # 範疇 8 錯誤面板
│   ├── guardrail_status/          # 範疇 9 護欄狀態
│   ├── verification_panel/        # 範疇 10 驗證
│   ├── subagent_tree/             # 範疇 11 子代理樹
│   └── trace_viewer/              # 範疇 12 (Observability) — Jaeger UI 嵌入
│
├── shared/                        # 共用基礎
│   ├── ui/                        # shadcn UI（從 V1 抽取保留）
│   ├── hooks/                     # 通用 hooks
│   ├── api/                       # API client（Fetch）
│   ├── lib/                       # 工具函式
│   └── types/                     # TypeScript 類型
│
├── stores/                        # Zustand（合併原 store + stores）
│   ├── chat_store.ts
│   ├── session_store.ts
│   ├── auth_store.ts
│   └── ...
│
├── services/                      # API 服務層
│   ├── chat_service.ts            #   調用 chat API
│   ├── tool_service.ts
│   ├── memory_service.ts
│   └── ...
│
└── archived/                      # V1 頁面封存（參考用）
    ├── unified-chat/
    ├── agent-swarm/
    └── README.md
```

---

## 架構約束（必須遵守）

### 約束 1：依賴方向

```
api/        ──→ agent_harness/  ──→ adapters/  ──→ infrastructure/
                       ↓                              ↑
                  platform_layer/   ──────────────────────┘

  (向下依賴，不可反向)
```

**規則**：
- ✅ `agent_harness` 可 import `adapters` / `platform`
- ✅ `platform` 可 import `infrastructure`
- ❌ `agent_harness` **禁止** import `infrastructure` 直接（必須透過 platform）
- ❌ `agent_harness` **禁止** import 任何 LLM SDK（必須透過 adapters）
- ❌ `infrastructure` **禁止** import `agent_harness` / `platform`

### 約束 2：範疇間依賴

```
範疇 1 (Loop)  ←  其他範疇被 Loop 使用
範疇 6 (Output Parsing)  ←  Loop 用
範疇 5 (Prompt)  ←  Loop 用
範疇 2 (Tools)  ←  Loop 用
範疇 3 (Memory)  ←  Loop / Tools 用
範疇 4 (Context Mgmt)  ←  Loop 用
範疇 7 (State)  ←  Loop 用
範疇 8 (Error)  ←  全範疇用
範疇 9 (Guardrails)  ←  Loop / Tools 用（攔截器）
範疇 10 (Verification)  ←  Loop 後置
範疇 11 (Subagent)  ←  Tools 觸發 / Loop 嵌套
```

**規則**：
- ✅ 範疇可 import 同層或更低層範疇
- ❌ 範疇間**循環依賴**禁止
- ✅ 跨切面（範疇 8/9/10）可被任何範疇 import

### 約束 3：Adapter 層強制（**LLM Provider 中性**）⭐⭐⭐

> 對應 `10-server-side-philosophy.md` 原則 2

**`agent_harness/**` 任何代碼禁止 import LLM 供應商 SDK**：

```python
# ❌ 嚴禁（CI 強制 fail）
from openai import AzureOpenAI
from anthropic import Anthropic
import openai
import anthropic

# ❌ 禁止使用 OpenAI / Anthropic 原生 schema
tools = [{"type": "function", "function": {...}}]      # OpenAI 原生
tools = [{"name": "...", "input_schema": {...}}]       # Anthropic 原生

# ✅ 正確：透過 ABC + 中性格式
from src.adapters._base.chat_client import ChatClient
from src.agent_harness.tools.spec import ToolSpec

client: ChatClient = get_chat_client_from_config()
tools: list[ToolSpec] = [...]
response = await client.chat_with_tools(messages, tools)
```

**強制規則**：
- ❌ `agent_harness/**/*.py` 不得 `import openai` / `import anthropic`
- ❌ `Message`、`ToolSpec`、`ChatResponse` 必須是 V2 中性格式
- ✅ Adapter 層負責所有供應商特定轉換
- ✅ CI lint 強制檢查（Phase 49.3 建立）

**驗收**：「30 分鐘換 provider」測試通過 — 主流量切換 LLM 供應商只改 config 不改代碼。

### 約束 4：所有 Tool 透過 Registry

```python
# ❌ 禁止
result = await some_function(args)

# ✅ 正確
from src.agent_harness.tools.registry import ToolRegistry
result = await ToolRegistry.execute("tool_name", args, context=ctx)
```

### 約束 5：Loop 必須使用 PromptBuilder

```python
# ❌ 禁止
messages = [{"role": "system", ...}, {"role": "user", ...}]

# ✅ 正確
from src.agent_harness.prompt_builder.builder import PromptBuilder
messages = PromptBuilder.build(system_role=..., tools=..., ...)
```

---

## 部署架構

### 開發環境（Phase 49）
```
docker-compose.dev.yml:
├── backend-api          # FastAPI（API + worker 暫合一）
├── postgres
├── redis
├── rabbitmq             # Or 後續換 Temporal
├── qdrant               # Vector DB
└── frontend (Vite)
```

### 階段 1：分離 API 與 Worker（Phase 50+）
```
docker-compose.yml:
├── backend-api          # FastAPI（純 API）
├── agent-worker         # 獨立 worker 跑 agent loop
├── postgres
├── redis
├── rabbitmq / temporal
├── qdrant
└── frontend (Vite build → static)
```

### 階段 2：K8s（後續，非本次規劃）
保留設計空間，本次不規劃。

---

## 死 Port 問題的解決

V1 經常遇到的 Windows 死 port 問題，V2 透過：

1. **Docker 化開發環境**：每次重啟容器強制釋放 port
2. **WSL2 推薦**：避免 Windows TCP socket 殘留
3. **PID 管理腳本**：保留 V1 經驗（`feedback_windows_process_management.md`）

**不需要架構級解決**，這是執行環境問題。

---

## API v1 主要 endpoints（V2 全新）

```
POST   /api/v1/chat                 # 觸發 agent loop（SSE 回應）
GET    /api/v1/chat/sessions/{id}   # 查詢 session 狀態
POST   /api/v1/chat/sessions/{id}/resume  # HITL 後恢復

GET    /api/v1/tools                # 列出可用工具
POST   /api/v1/tools/test           # 測試工具

GET    /api/v1/memory               # 查詢記憶
POST   /api/v1/memory/search        # 搜索記憶
POST   /api/v1/memory               # 寫入記憶

GET    /api/v1/audit                # 審計日誌
GET    /api/v1/audit/{session_id}   # 特定 session 審計

POST   /api/v1/governance/approve   # HITL 批准
POST   /api/v1/governance/reject    # HITL 拒絕

GET    /api/v1/state/{session_id}/timeline       # State 時間軸
POST   /api/v1/state/{session_id}/time-travel    # 時間旅行

GET    /api/v1/verification/{session_id}         # 驗證結果

GET    /api/v1/agents               # Agent CRUD
GET    /api/v1/workflows            # Workflow CRUD

GET    /api/v1/_internal/health     # Health check
GET    /api/v1/_internal/metrics    # Prometheus metrics
```

---

## SSE 事件規範（Frontend ↔ Backend）

```typescript
// Loop 事件
type LoopEvent =
  | { type: "loop_start"; data: { request_id, session_id } }
  | { type: "turn_start"; data: { turn_num } }
  | { type: "llm_request"; data: { model, tokens_in } }
  | { type: "llm_response"; data: { content, tool_calls?, thinking? } }
  | { type: "tool_call_request"; data: { tool_name, args } }
  | { type: "tool_call_result"; data: { tool_name, result, is_error } }
  | { type: "guardrail_check"; data: { layer, passed } }
  | { type: "tripwire_fired"; data: { reason } }
  | { type: "compaction_triggered"; data: { tokens_before, tokens_after } }
  | { type: "hitl_required"; data: { approval_id, prompt } }
  | { type: "verification_start"; data: { verifier_type } }
  | { type: "verification_result"; data: { passed, reason? } }
  | { type: "loop_end"; data: { result, total_turns, total_tokens } };
```

> **Sprint 57.66 (A-5a+) — real serializer registration**: the catalog above is the
> original aspirational design; the live `sse.py` serializer (single-source for the actual
> wire) names some events differently and Sprint 57.66 surfaces four more diagnostic events
> that were already yielded on the chat loop but previously dropped at the serializer. The
> **real** wire-types now emitted on the chat SSE stream:
>
> - `prompt_built` — `{ messages_count, estimated_input_tokens, cache_breakpoints_count, memory_layers_used: string[], position_strategy_used, duration_ms }` (Cat 5)
> - `context_compacted` — `{ tokens_before, tokens_after, compaction_strategy, messages_compacted, duration_ms }` (Cat 4; the catalog's aspirational `compaction_triggered`)
> - `state_checkpointed` — `{ version }` (Cat 7)
> - `tripwire_triggered` — `{ violation_type, detail }` (Cat 9; the catalog's aspirational `tripwire_fired`)
>
> Plus two prompt-cache fields carried on existing frames: `llm_response.data.cached_input_tokens`
> and `loop_end.data.{ cached_input_tokens, cache_hit_rate }` (genuine JSON numbers — FIX-025
> stopped `_jsonable` from stringifying floats on the wire). All frames carry the injected `trace_id`.
> Single-source serializer: `backend/src/api/v1/chat/sse.py`; FE contract: `frontend/src/features/chat_v2/types.ts`
> (`KNOWN_LOOP_EVENT_TYPES`, 18 types). 17.md §4.1 emit-ownership unchanged (these `LoopEvent`
> subclasses already existed; this sprint only added their SSE projection).

> **Sprint 57.67 (A-5b) — codegen single-source**: the FE contract above is no longer
> hand-maintained. The 18 wire-types + their payload shapes are now declared once in
> **`backend/src/api/v1/chat/event_wire_schema.py`** (`WIRE_SCHEMA`), from which
> `scripts/codegen/generate_event_schemas.py` GENERATES `frontend/src/features/chat_v2/generated/`
> `events.json` + `loopEvents.generated.ts` (the latter re-exported by `types.ts`). Two gates make
> drift un-mergeable: a pytest parity test (`test_event_wire_schema_parity.py` — every `sse.py`
> serializer branch's wire-type + `data` keys must match the registry) and the `check_event_schema_sync`
> lint (10th V2 lint in `run_all.py` + `lint.yml` `v2-lints`, a required check — regenerates + diffs).
> `sse.py` keeps its hand-written branches (locked by the parity test, not rewritten). To add/change a
> wire-type: edit the registry → re-run the codegen → commit. The aspirational catalog block (top) is
> retained for historical context; the registry is the authoritative wire contract.

---

## §Naming Drift Note (Sprint 57.6+ — closes AD-Reality-6)

**Modification History**:
- 2026-05-08: Sprint 57.6 Day 4 US-4 — fold-in 02.md flat-layer drift per Sprint 57.5 V2 reality check 21-doc audit

### 真實 backend layer structure(per V2 22/22 closure 真實 ship)

V2 規劃 02-architecture-design.md 早期 §Architecture Diagram 描述 **5-layer flat structure**: `agent_harness/`, `platform/`, `adapters/`, `business_domain/`, `infrastructure/`。Sprint 57.5 V2 reality check 21-doc paper audit 確認真實 backend layer 結構為 **nested platform_layer/{...}** form,not flat:

```
backend/src/
├── agent_harness/         # 11+1 範疇 (Cat 1-12)
├── adapters/              # _base/ + azure_openai/ ...
├── api/                   # api/v1/* HTTP endpoints
├── business_domain/       # 5 domains: patrol/correlation/rootcause/audit/incident
├── core/                  # config / logging / settings
├── infrastructure/        # db/ + redis/
├── middleware/            # tenant_context.py
├── mock_services/         # 51.0 mock business
├── platform_layer/        # ⭐ NESTED (NOT flat per paper claim):
│   ├── billing/           # CostLedgerService + PricingLoader (56.3)
│   ├── governance/        # audit/ + hitl/ + risk/ + service_factory (53.4-53.6)
│   ├── identity/          # auth + JWT (52.5)
│   ├── middleware/        # TenantContextMiddleware (49.3)
│   ├── observability/     # OTel + SLA + Tracer (49.4 + 56.3)
│   ├── tenant/            # quota / lifecycle (56.1 + 56.2)
│   └── workers/           # Celery / Temporal selection (49.4)
└── runtime/               # platform_layer-orchestrated runtime utilities
```

### Why drift exists

Phase 49.1 V2 foundation skeleton 起初按 paper flat-layer 結構建立(`platform/governance/`, `platform/identity/` etc.)。Phase 53.4 (§HITL Centralization backend) 起,`platform_layer/` 子目錄逐步 nested(governance / hitl / risk merged under governance/),per natural modularization needs。Phase 56.1-56.3 SaaS Stage 1 nested 進一步深入(billing / tenant / observability split out)。

**Paper claim vs reality**:Paper 仍稱 "flat 5-layer";reality has converged to **nested 7-subdir under platform_layer/** + `agent_harness/` + `adapters/` + `api/` + `business_domain/` + `core/` + `infrastructure/` + `middleware/` + `mock_services/` + `runtime/`。

### Implication for new code

新代碼應對齐 nested form(per `cd backend/src/ && ls` 真實結構),NOT 假設 flat-layer(會導致 import path 錯誤 + Sprint 49.1-era pattern misuse)。`category-boundaries.md` 已對齐 nested form per Sprint 53.4-onwards updates;此 drift note 是 02.md catch-up 補登記 per Sprint 57.5 reality check audit。

### Phase 57.7+ remediation candidates

- (a) Refactor `platform_layer/` 子目錄 to flat per paper claim — large effort,low ROI(reality-direction 已成熟 nested,paper-direction 過時)
- (b) Update 02.md §Architecture Diagram to match reality(this section + future sprint cleanup)— **CHOSEN per AD-Reality-6**
- (c) No-op,leave drift documented — too lazy,reality check already flagged

This Sprint 57.6 closeout adopts (b) by adding this Naming Drift Note。Future sprint cleanup may revise §Architecture Diagram inline to match reality(low priority,not blocking)。

### SpanCategory: by-category enum vs by-span-type granularity (Sprint 57.71 — A-4 loop tracer)

The `Tracer` `SpanCategory` enum (`agent_harness/_contracts/observability.py`) is **by-category** (13 values: ORCHESTRATOR / TOOLS / MEMORY / CONTEXT_MGMT / PROMPT_BUILDER / OUTPUT_PARSER / STATE_MGMT / ERROR_HANDLING / GUARDRAILS / VERIFICATION / SUBAGENT / OBSERVABILITY / HITL), but the Cat 12 spec (`01.md §範疇12`) intended a **by-span-type** set (LOOP / TURN / LLM_CALL / TOOL_EXEC …). Sprint 57.71 (A-4 loop tracer) opened the loop-internal span tree and resolved this drift.

**Decision: KEEP the by-category enum unchanged + express span-type granularity via span name + `attributes["span_type"]`.**
- **Rationale**: the by-category enum is load-bearing (used at ~8 sites + the `observability/metrics.py` name→category map); renaming to by-span-type = high blast radius, no upside. Span name was already the granularity convention (`tool.{name}`, `output_parser.parse`).
- **Implementation**: each loop span carries `attributes["span_type"]` (LOOP / TURN / LLM_CALL / TOOL_EXEC / PROMPT_BUILD / COMPACTION) + the closest existing `SpanCategory` (TURN→ORCHESTRATOR, TOOL_EXEC→TOOLS, PROMPT_BUILD→PROMPT_BUILDER, COMPACTION→CONTEXT_MGMT). `observability/helpers.category_span` extended with optional `attributes` / `span_type` (additive). Enum untouched.
- **Rejected**: by-span-type enum rename (blast radius — `metrics.py` map + 8 sites); hybrid dual-enum (two semantics → confusion).

---

## 下一步

確認架構後：
- `03-rebirth-strategy.md`：重生策略（如何過渡）
- `04-anti-patterns.md`：V1 教訓
- `06-phase-roadmap.md`：詳細 Phase / Sprint 規劃
