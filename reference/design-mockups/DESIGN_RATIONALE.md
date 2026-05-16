# Design Rationale — Operator Portal V2

> **目的**：解釋目前 sidebar 上 **每一個** menu 項為什麼存在，以及它對應 V2 文件 / spec 的哪個部分。未來 AI 助手或新加入的工程師要修改任一頁面前，請先讀本檔，避免重複討論「為什麼有這個頁面」。

> **權威來源**：
> - V2 ship target → `frontend/src/routes.config.ts`（13 個頁面）
> - V2 後端範疇 → `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md`（範疇 1-12）
> - V2 vision → `docs/03-implementation/agent-harness-planning/00-v2-vision.md`
> - V2 哲學 → `docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`
> - V2 anti-pattern → `docs/03-implementation/agent-harness-planning/04-anti-patterns.md`

---

## 設計哲學

V2 後端定義了 **12 範疇（11+1）的 agent harness**，但 V2 第一階段（routes.config.ts）只 ship 13 個前端頁面。這意味著：

> **後端能力 ≠ 前端視角**

對 operator / 維運 / SRE / compliance 來說，要管理一套 production agent system，必須能看到「LLM 在做什麼、為什麼這樣做、出問題時怎麼介入」。本 portal 的設計取向是 **把 12 範疇的每個 ABC 都實體化成一個 operator 視角頁面**，即使這些頁面當前不在 V2 ship 計劃內。

因此 menu 上會看到 3 類項目：

| 類別 | 標識 | 意涵 |
|---|---|---|
| **V2 Ship** | 無徽章 / 預設 active | 在 `routes.config.ts` 內，是 V2 第一階段的官方頁面 |
| **PROP**（藍） | `proposed: true` | V2 後端範疇 spec 有定義對應 ABC，但 frontend 還沒列入 routes；本 portal 先畫出來給 stakeholder 確認方向 |
| **DRAFT**（黃） | `designed: true, active: false` | V2 routes 有列、但 `active: false`（未 ship），本 portal 先設計出來 |

---

## 完整 Menu 對應表

### 📂 Operations — 日常 operator workflow

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `overview` | `/overview` | PROP | 跨範疇彙整視圖（非 routes.config.ts 條目，純設計擴充） | operator 進入系統的第一頁；橫切 12 範疇給「一眼看懂目前狀態」的儀表板。對映 V1 「Dashboard」+ V2 12 範疇的 cross-cut 視角 |
| `chat-v2` | `/chat-v2` | ✅ V2 Ship | `routes.config.ts` operations | V2 主要 operator 入口（與 LLM agent 對話） |
| `orchestrator` | `/orchestrator` | PROP | 範疇 1 Orchestrator Loop（TAO/ReAct）| 後端有 `AgentLoop` ABC，operator 需要視覺化「目前每個 session 跑到第幾 turn / 哪個 stop_reason」 |
| `subagents` | `/subagents` | PROP | 範疇 11 Subagent Orchestration | 4 種模式（Fork/Teammate/Handoff/AsTool）需 registry UI 管理 |
| `loop-debug` | `/loop-debug` | ✅ V2 Ship | `routes.config.ts` admin | 範疇 1 LoopEvent 流的 debug view，V2 第一階段必 ship |
| `memory` | `/memory` | ✅ V2 Ship | `routes.config.ts` admin | 範疇 3 雙軸記憶矩陣（5 scope × 3 time scale）的管理面 |
| `state-inspector` | `/state-inspector` | PROP | 範疇 7 State Management | 後端有 `LoopState = TransientState + DurableState` 與 time-travel checkpointer；operator 需查狀態與回放版本 |
| `compaction` | `/compaction` | PROP | 範疇 4 Context Management | Compaction 觸發於 75% window；需 UI 看哪些 session 被壓縮、壓縮率、token saving |
| `jit-retrieval` | `/jit-retrieval` | PROP | 範疇 4 JIT Retrieval | 對應 CC `grep/glob/head/tail`；operator 看哪些檔案 / KB chunk 被按需載入 |
| `subagent-tree` | `/subagent-tree` | PROP | 範疇 11 + 範疇 12 trace tree | Subagent 與父 loop 透過 `parent_span_id` 連接；operator 需樹狀視覺化跨 agent trace |

> ⚠️ 注意：在 V2 `routes.config.ts` 中，`loop-debug` 與 `memory` 屬於 **admin** category，這裡放在 operations 是設計層的重新分類（基於「operator daily workflow」更直覺）。

---

### 📂 Business — IPA 5 大業務領域（V1 商業資產）

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `incidents` | `/incidents` | PROP | `08b-business-tools-spec.md`（V2 業務工具 spec，已從通用 harness 拆離） | V1 IPA 5 個 business domains（patrol / correlation / RCA / audit / incident）的 operator console；V2 把業務工具與通用 harness 拆分，但 operator 仍需操作面 |

> 📝 注意：根據 V2 vision，「business tools」**不在通用 11 範疇 spec 內**（見 spec §範疇 2 review 修訂），但業務 operator 仍需這層 UI。`domain-patrol` / `domain-correlation` / `domain-rca` / `domain-audit` / `domain-incident` 等 5 個子頁透過 `/incidents/<domain>` 進入（見 `shell.jsx` `DOMAIN_PATHS`）。

---

### 📂 Governance — HITL + 審計 + 驗證

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `governance` | `/governance` | ✅ V2 Ship | `routes.config.ts` admin（Sprint 57.9） | §HITL 中央化 主控台：reviewer 審批佇列 |
| `audit-log` | `/audit-log` | DRAFT | `routes.config.ts` admin（active=false） | 範疇 9 WORM + hash-chain audit；V2 已列但未 ship，先設計 |
| `verification` | `/verification` | ✅ V2 Ship | `routes.config.ts` admin（Sprint 57.11） | 範疇 10 Verification Loops 結果檢視（rules / LLM-judge） |
| `redaction` | `/redaction` | PROP | 範疇 9 Guardrails（PII / jailbreak detection） | 範疇 9 防護規則有 PII redaction，需 UI 管理白名單 / 規則 |
| `error-policy` | `/error-policy` | PROP | 範疇 8 Error Handling | `RetryPolicy` per-tool 矩陣 + `CircuitBreaker` per-provider + `ErrorBudget` per-tenant 三者皆需設定面 |

> ⚠️ 注意：V2 `routes.config.ts` 把 governance / audit-log / verification 都歸 **admin**；本 portal 為了表達「治理 vs 系統管理」的職責分離，把它們拆為獨立的 governance category。這是設計層選擇，不影響後端對應。

---

### 📂 Observability — 範疇 12 dashboard

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `sla-dashboard` | `/sla-dashboard` | ✅ V2 Ship | `routes.config.ts` operations | 範疇 12 三軸 metrics（latency 軸） |
| `cost-dashboard` | `/cost-dashboard` | ✅ V2 Ship | `routes.config.ts` operations | 範疇 12 三軸 metrics（cost 軸，per-tenant 計費） |
| `cache-manager` | `/cache-manager` | PROP | 範疇 4 Prompt Caching（`PromptCacheManager`） | Anthropic / Azure / OpenAI 都有 prompt cache；operator 需看 hit rate、手動 invalidate |
| `sse` | `/sse` | PROP | 範疇 1 `AsyncIterator[LoopEvent]` SSE 推送 | streaming-first 設計，需 dev inspector debug 事件流 |
| `devui` | `/devui` | PROP | 整合 debug：span tree + state version + replay | LangSmith / Langfuse 等價的 in-house debug 介面 |

> 📝 注意：`sla-dashboard` / `cost-dashboard` 在 routes.config.ts 是 **operations** category；這裡為了把所有 metrics-driven 頁面集中，重新歸到 observability。

---

### 📂 Resources — 工具與 flag

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `models` | `/models` | PROP | 範疇 5/6 + `adapters/llm/` | LLM-provider-neutral；operator 需切換 / 比較 / 退役 model |
| `tools` | `/tools` | PROP | 範疇 2 Tool Layer `ToolRegistry` | 6 大類工具註冊表的管理面 |
| `feature-flags` | `/feature-flags` | DRAFT | `routes.config.ts` admin（active=false） | V2 已列但未 ship，先設計 |

---

### 📂 Admin — 租戶 / 身分 / 計費

| ID | 路由 | 狀態 | 對應 V2 來源 | 為什麼有 |
|---|---|---|---|---|
| `admin-tenants` | `/admin-tenants` | ✅ V2 Ship | `routes.config.ts` admin | tenant 列表與 lifecycle 管理 |
| `tenant-onboarding` | `/admin/tenant-onboarding` | PROP | 對應 tenant 建立流程（非 spec 內，UX 補強） | 從 admin-tenants 列表進來的「新增 tenant」wizard |
| `tenant-settings` | `/tenant-settings` | ✅ V2 Ship | `routes.config.ts` admin | 單一 tenant 的設定 |
| `pricing` | `/admin/pricing` | PROP | 對應範疇 12 `agent.cost.usd` metric 的計費規則設定 | 後端 emit cost metric，前端需有「定價方案」設定面（platform admin 才能看） |
| `rbac` | `/rbac` | PROP | 範疇 9 權限分層（與推理分離原則）+ 範疇 2 `PermissionSpec` | tenant_admin / operator / compliance / auditor 等 role 的權限矩陣 |
| `profile` | `/profile` | DRAFT | `routes.config.ts` settings（active=false） | V2 已列但未 ship |
| `mfa` | `/mfa` | DRAFT | `routes.config.ts` settings（active=false） | V2 已列但未 ship |

---

## V2 三類 vs 本 portal 六類的 category 重新分類理由

V2 `routes.config.ts` 只有 3 個 category：

| V2 category | V2 頁面 |
|---|---|
| operations | chat-v2, cost-dashboard, sla-dashboard |
| admin | admin-tenants, tenant-settings, audit-log, feature-flags, governance, verification, loop-debug, memory |
| settings | profile, mfa |

本 portal 重新分為 6 類，理由：

1. **operations** 拆出 **observability**：dashboard 類（cost / sla / cache / sse / devui）與「跟 agent 對話 / debug agent」（chat / orchestrator / memory / state-inspector）職責不同
2. **admin** 拆出 **governance**：reviewer 不一定是 platform admin（compliance 角色），路由分離有助於 RBAC 視覺化
3. **admin** 拆出 **resources**：models / tools / feature-flags 是「平台資源管理」，與「租戶管理」職責不同
4. **operations** 新增 **business** category：放 IPA 5 大業務 domain console，與通用 agent operations 區隔（呼應 V2 `08b-business-tools-spec.md` 把業務工具拆出通用 harness 的設計決定）

> **如果未來嚴格貼回 V2 routes.config.ts 3-category**：把 6 category 折疊回 3 category 即可，每個頁面的「業務責任」不變。

---

## V2 spec 中**有但本 portal 沒有**的內容

範疇 5（Prompt Construction）目前沒對應頁面，因為 prompt builder 是內部組件，operator 不直接管。未來若加入「prompt template library」管理面，建議加在 resources category。

範疇 6（Output Parsing）同理，operator 不直接管。

---

## V2 spec 中**沒有但本 portal 有**的內容

- `incidents` 與 5 個 `domain-*`：來自 V1 IPA 業務面；V2 spec 把業務工具拆到 `08b-business-tools-spec.md`，業務 console 仍是合法需求
- `tenant-onboarding`、`pricing`：純 UX 補強；後端能力存在（tenant lifecycle API、cost metric），但 routes 沒列
- 6 category 重新分類：見上節
- **`overview` dashboard**：跨範疇彙整視圖；V2 routes.config.ts 無此條目，但任何 production operator portal 都需要這層 landing page。本 portal 提供它，等同於主動補完 V2 plan 缺漏的「進入頁」
- **`auth-register` / `auth-invite` / `auth-mfa` / `auth-expired`**：見下節「Auth 流程完整圖」

這些不違反 V2 設計，只是「在 V2 路線圖之外、additional 的設計提案」。要不要實作由 product owner 決定。

---

## Auth 流程完整圖

V2 後端 spec 提到「WorkOS OIDC + MFA + dev-login」，但 `routes.config.ts` **不收錄 auth 路由**（auth routes 用獨立 `AuthShell`，由 `App.tsx` 直接 wire）。本 portal 把所有 auth 場景都設計出來：

| route id | URL | 狀態 | 對應 V2 / 業界場景 | 為什麼有 |
|---|---|---|---|---|
| `auth-login` | `/auth/login` | 設計擴充 | repo README §「Auth in local dev」 | SSO 主登入入口（SAML / OIDC / Microsoft / Google） |
| `auth-callback` | `/auth/callback` | 設計擴充 | WorkOS OIDC callback | SSO 回呼處理頁，顯示 tenant 載入進度 |
| `auth-dev` | `/auth/dev-login` | 設計擴充 | repo README §「DEV_LOGIN=true」 | 非生產環境的快速登入，假冒身分用 |
| **`auth-register`** | `/auth/register` | 設計擴充 | 對映 `tenant-onboarding` 的 self-service 版 | 新公司 self-signup wizard（4 step：identity → org → plan → confirm） |
| **`auth-invite`** | `/auth/invite` | 設計擴充 | 對映 RBAC 邀請流程（範疇 9 + admin） | tenant_admin 邀請新成員加入時的接受頁；含角色 / 租戶資訊與 MFA 引導 |
| **`auth-mfa`** | `/auth/mfa` | 設計擴充 | repo README §「MFA required by tenant policy」 | TOTP / WebAuthn 雙因素驗證頁；登入過程中必經 |
| **`auth-expired`** | `/auth/expired` | 設計擴充 | JWT 24h 過期 / 安全策略 | session timeout 提示頁；保留 in-flight 對話 + HITL 狀態的承諾 |

> 注意：repo `routes.config.ts` 明確說「Auth routes are NOT in this registry」，這些 route 由 production code 在 `App.tsx` 直接 wire。本 portal 把它們列在「Tweaks → Auth flows」面板可跳轉，不混入主 Sidebar。

---

## Topbar 互動規格

Topbar 4 個 icon 的點擊行為（之前都是裝飾，現在補完）：

| Icon | 行為 | 元件 | 對映 |
|---|---|---|---|
| 🔍 `⌘K` Search | 開啟全域 Command Palette modal | `CommandPalette` | 業界標配（Linear / Notion / Vercel）：搜尋 actions / pages / tenants / sessions |
| 🔔 Bell | 右上 dropdown popover；含 unread badge | `NotificationsPanel` | 對映範疇 9 tripwire + 範疇 1 events + §HITL ApprovalRequested |
| 🎚 Sliders | 開啟 Tweaks 面板 | `tweaks-panel.jsx`（既有） | 設計原型用，production 不會有 |
| 👤 Avatar | 右上 dropdown popover | `UserMenu` | 含 tenant switcher / profile / MFA / preferences / logout |

設計守則：
- ⌘K 是全域 modal（中央，blur 背景）；其他兩個是 anchor 在 icon 旁的 dropdown popover
- Bell 顯示未讀紅點 badge（從 `notifsSeed` 計算）
- Avatar 開 popover；含 tenant switcher（呼應 sidebar 上的 tenant-switcher，two-way sync）
- 全部 panel 都吃 Escape 關閉、外部點擊關閉

---

## 維護守則

1. **新增頁面前**：先檢查 `routes.config.ts` 與 `01-eleven-categories-spec.md`，確認對應的範疇 ABC 或 V2 routes 條目。如果都沒有 → 屬於「設計擴充」，要在本檔對應段落明確標註理由
2. **刪除頁面前**：本 portal 的目的是「展示 12 範疇的完整 operator 視角」，**不要因為「V2 第一階段沒 ship」就刪**。改為標 `proposed: true` 即可
3. **修改 category 分類前**：理解現有 6 類的拆分理由（見上節），不要為了「對齊 V2 3 category」而硬塞
4. **修改完後**：本檔的對應表也要同步更新

---

## 變更歷史

- 2026-05-16：初版，對照 V2 `routes.config.ts` + 11+1 範疇 spec 完整檢查每個 menu 項
- 2026-05-16（補）：新增 `overview` dashboard、4 個 auth 補完頁（register / invite / mfa / expired）、Topbar 三 icon 互動（CommandPalette / NotificationsPanel / UserMenu）
