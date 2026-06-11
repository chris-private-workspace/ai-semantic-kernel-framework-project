# IPA Platform V2 — Agent Harness 重生計畫

**建立日期**：2026-04-23
**版本**：V2.2（2026-04-28：兩輪 review 整合修訂）
**狀態**：規劃完成（**production-quality**） → 啟動 Sprint 49.1

> **2026-04-28 Review 整合修訂（兩輪）**：經 8 份 expert review（11 範疇 / PM / 契約 / 測試 / 安全 / SaaS / 前端 / DevOps）後完成兩輪整合：
> - **第一輪 (P0+P1)**：11 範疇升為 **11 + 範疇 12 (Observability)**、路線圖 **16 → 22 sprint**、跨範疇接口附錄、業務工具獨立 spec、§HITL 中央化
> - **第二輪 (20 項 P0)**：Streaming contract / trace_context 簽名 / LoopState 拆分 / 非確定性測試 / Merkle audit / OWASP 矩陣 / BYOK / RLS bypass / DR 修正 / SSE production-grade / Docker 瘦身 / SLO / Forward-fix
>
> 詳見 [`v2-review-integration-report-20260428.md`](./v2-review-integration-report-20260428.md)。

---

## 文件導覽

本目錄是 IPA Platform V2「重新出發」的**規劃根目錄**。所有後續 Phase / Sprint 文件都從這裡延伸。

| 文件 | 用途 |
|------|------|
| [README.md](./README.md) | 本文件，整體導覽 |
| [00-v2-vision.md](./00-v2-vision.md) | V2 願景、核心理念、目標（**含 V2 ≠ SaaS-ready 聲明**） |
| [01-eleven-categories-spec.md](./01-eleven-categories-spec.md) | **11 範疇 + 範疇 12 完整定義 + §HITL 中央化** |
| [02-architecture-design.md](./02-architecture-design.md) | V2 架構設計（5 層 + 範疇 12 cross-cutting） |
| [03-rebirth-strategy.md](./03-rebirth-strategy.md) | 重生策略（3 區分治、archive 處理） |
| [04-anti-patterns.md](./04-anti-patterns.md) | V1 教訓（避免重複的反模式） |
| [05-reference-strategy.md](./05-reference-strategy.md) | 參考資料策略（CC / V1 / MAF / 業界） |
| [06-phase-roadmap.md](./06-phase-roadmap.md) | Phase 49-55 路線圖（**22 sprint，5.5 個月**）|
| [07-tech-stack-decisions.md](./07-tech-stack-decisions.md) | 關鍵技術選型 |
| [08-glossary.md](./08-glossary.md) | 術語表 |
| [08b-business-tools-spec.md](./08b-business-tools-spec.md) | ⭐ **業務領域工具獨立 spec**（5 domain × 24 工具，2026-04-28 新增）|
| [09-db-schema-design.md](./09-db-schema-design.md) | DB Schema 設計（Phase 49.2 用）|
| [10-server-side-philosophy.md](./10-server-side-philosophy.md) | ⭐ **3 大最高指導原則**（必讀） |
| [11-test-strategy.md](./11-test-strategy.md) | 測試與驗收策略（11 範疇 × 4 種測試）|
| [12-category-contracts.md](./12-category-contracts.md) | 範疇間整合契約（含 Reducer / Observability / HITL contracts）|
| [13-deployment-and-devops.md](./13-deployment-and-devops.md) | 部署 + CI/CD + Docker + DR |
| [14-security-deep-dive.md](./14-security-deep-dive.md) | 安全合規深度（STRIDE / OWASP / GDPR） |
| [15-saas-readiness.md](./15-saas-readiness.md) | SaaS Readiness（Tenant / SLA / Billing） |
| [16-frontend-design.md](./16-frontend-design.md) | Frontend 完整設計（**12 頁 sprint 對應表**）|
| [17-cross-category-interfaces.md](./17-cross-category-interfaces.md) | ⭐ **跨範疇接口附錄**（single-source registry，2026-04-28 新增） |
| `phase-49-foundation/` | Phase 49 詳細 Sprint 規劃（**4 sprint**） |
| `phase-50-orchestrator-loop/` | Phase 50（2 sprint） |
| `phase-51-tools-memory/` | Phase 51（**3 sprint**，新增 51.0） |
| `phase-52-context-prompt/` | Phase 52（2 sprint） |
| `phase-53-state-error-guardrails/` | Phase 53（**4 sprint**，新增 53.4） |
| `phase-54-verification-subagent/` | Phase 54（2 sprint） |
| `phase-55-production/` | Phase 55（**5 sprint**，從 2 拆 5） |

執行紀錄在隔壁目錄：`docs/03-implementation/agent-harness-execution/`

---

## 重要前提（必讀）

### 1. 這不是「修補 V1」
V1 經審計確認**真實對齊度只 27%**，11 範疇中 8 個處於 Level 0-2（不可用 / 半成品）。決策**重新出發**而非繼續修補。

### 2. 這不是「全部砍掉」
V1 有寶貴資產應保留：
- 5 年累積的設計知識（V9 分析、CC 30-wave 研究、V1 教訓）
- 部分 infrastructure 設計（DB pool / Redis wrapper / Storage）
- 業務領域邏輯**設計概念**（patrol / correlation / rootcause 等的需求理解）

### 3. 這是「11 + 1 範疇導向」
V2 從 Day 1 按 **agent harness 11 範疇 + 範疇 12 cross-cutting**組織代碼，避免 V1 跨目錄散落（Guardrails 散在 6 處、Orchestrator 散在 5 處）的問題。

### 4. 這是「企業 governance + CC 級閉環」混合架構
不是模仿 CC，是建立**業界第一個完整閉環的企業 agent 平台** — 這是 V1 一直在追求但未達成的願景。

### 5. **V2 完成 ≠ SaaS-ready**（2026-04-28 新增）
V2（Phase 55）達到「核心能力 + 業務領域 + canary 試用」；SaaS Stage 1（內部 SaaS / billing / SLA / DR）在 Phase 56-58。

---

## 11 + 1 範疇核心

V2 嚴格按以下 11 範疇 + 範疇 12 (Observability cross-cutting) 組織：

| # | 範疇 | 中文 | V1 對齊度 | V2 目標 | Phase |
|---|------|------|----------|---------|-------|
| 1 | Orchestrator Layer (TAO/ReAct) | 編排層 | 18% | 80%+ | 50.1 |
| 2 | Tool Layer | 工具層 | 32% | 75%+ | 51.1 |
| 3 | Memory（**雙軸**：5 scope × 3 time scale） | 記憶 | 15% | 70%+ | 51.2 |
| 4 | Context Mgmt（**含 Prompt Caching**） | 上下文管理 | 5% | 75%+ | 52.1 |
| 5 | Prompt Construction | 提示組裝 | 20% | 75%+ | 52.2 |
| 6 | Output Parsing | 輸出解析 | 75% | 90%+ | 50.1 |
| 7 | State Mgmt（**含 Reducer + transient/durable**） | 狀態管理 | 30% | 70%+ | 53.1 |
| 8 | Error Handling | 錯誤處理 | 20% | 75%+ | 53.2 |
| 9 | Guardrails & Safety | 護欄與安全 | 30% | 85%+ | 53.3 + 53.4 |
| 10 | Verification Loops | 驗證迴圈 | 15% | 70%+ | 54.1 |
| 11 | Subagent Orchestration（**4 模式，無 worktree**） | 子代理編排 | 35% | 75%+ | 54.2 |
| **12** | **Observability / Tracing**（cross-cutting，2026-04-28 新增） | 觀測層 | 0% | 75%+ | 49.4 滲透所有 |
| **平均** | | | **~27%** | **~75%** | |

完整定義見 `01-eleven-categories-spec.md`。

---

## 路線圖總覽（**22 sprint 修訂版**）

| Phase | 名稱 | 原 sprint | **新 sprint** | 範疇 |
|-------|------|----------|---------------|------|
| **49** | Foundation | 3 | **4** | 骨架 + CI + DB + RLS + Adapters + OTel + Lint |
| **50** | Loop Core | 2 | 2 | 範疇 1 + 6 |
| **51** | Tools + Memory | 2 | **3** | 51.0 mock + 範疇 2 + 範疇 3 |
| **52** | Context + Prompt | 2 | 2 | 範疇 4 + 5（含 caching）|
| **53** | State + Error + Guardrails | 3 | **4** | 範疇 7 + 8 + 9 + Governance Frontend |
| **54** | Verification + Subagent | 2 | 2 | 範疇 10 + 11 |
| **55** | Production | 2 | **5** | 業務 backend / frontend / 缺漏 6 頁 / E2E / Canary |
| **合計** | | 16 | **22 sprint** | **約 5.5 個月** |

詳見 `06-phase-roadmap.md`。

---

## 預計成果（Phase 55 完成時）

- ✅ 11 範疇 + 範疇 12 全部 Level 4+ 對齊
- ✅ 真實對齊度從 27% → 75%+
- ✅ 主流量：UnifiedChat → Agent Loop → Tools → Verification 完整閉環
- ✅ 多供應商（Azure OpenAI 主、Anthropic / OpenAI 可選）+ Multi-Provider Routing
- ✅ 完整治理層（Input/Output/Tool guardrails、Tripwire ABC plugin、Audit WORM + hash chain）
- ✅ 企業級 HITL（中央化 HITLManager、Teams 整合、多級審批、cross-session resume）
- ✅ 業務領域功能接入新 harness（patrol / correlation / rootcause / audit / incident）
- ✅ Cross-cutting Observability（OTel + Jaeger / 三軸 metric / 12 個 SpanCategory）
- ✅ 9 個前端頁面 + DevUI 12 範疇成熟度 dashboard
- ✅ Canary 試用（內部 1-2 用戶）

> **不達成（推遲到 Phase 56-58）**：SaaS Stage 1 / Cost Tracking 第 13 範疇 / 多 provider 並行生產化 / 公網開放。

---

## 與 V1 的關係

| 項目 | V1 處理 | V2 對應 |
|------|--------|---------|
| `backend/src/` | 整體封存到 `archived/v1-phase1-48/` | 全新 backend |
| `frontend/src/pages/` | 封存 chat / agent-swarm | 全新 chat-v2 + 重新開發其他 pages |
| `frontend/src/shared/` | 保留作參考 | V2 從中抽取可重用的 UI 模式 |
| `infrastructure/` | 設計參考 | V2 重新評估每個元件 |
| `docs/07-analysis/V9/` | 完整保留 | V2 baseline 知識 |
| `docs/07-analysis/claude-code-study/` | 完整保留 | V2 設計藍本 |
| `claudedocs/` | 完整保留 | V2 持續使用 |
| `archived/docs-v1/03-implementation/sprint-planning/` | 完整保留（凍結） | V2 改用 `agent-harness-planning/` |

---

## Anti-Patterns（必讀）

V1 累積的 10 個反模式，V2 必須避免：

1. **Pipeline ≠ Loop 混淆**（範疇 1）
2. **Claude SDK 側翼陷阱**（範疇 1）
3. **Guardrails 跨 6 目錄散落**（範疇 9）
4. **Potemkin Features（結構槽位但無內容）**（範疇 3, 10）
5. **PoC 不合併 / 不淘汰**（全範疇）
6. **Hybrid 橋接層債務**（範疇 1）
7. **Context Rot 完全忽略**（範疇 4）
8. **無 PromptBuilder**（範疇 5）
9. **無 Verification Loop**（範疇 10）
10. **Mock vs Real 主流量分歧**（全範疇）
11. **Sync callback 在 async loop**（範疇 1，2026-04-28 新增）

詳見 `04-anti-patterns.md`。

---

## Single-Source 介面權威表（17.md）

> ⭐ 任何跨範疇 dataclass / ABC / tool / event **只能在 17.md 列出的 owner 文件定義一次**。其他文件只能引用，不能重新定義。

24 個核心 dataclass + 19 個核心 ABC + 22 個 LoopEvent + 9 個跨範疇工具的權威表見 [`17-cross-category-interfaces.md`](./17-cross-category-interfaces.md)。

---

## 下一步

1. ✅ 17 份規劃文件 + 1 跨範疇附錄 + 1 業務工具 spec 完成（共 19 份文件）
2. ✅ Review 整合修訂完成（22 sprint / 範疇 12 / HITL 中央化）
3. ✅ Sprint 49.1 plan + checklist 對齊新規劃
4. ▶️ **啟動 Phase 49 Sprint 49.1**：V1 封存 + 骨架 + CI Pipeline
