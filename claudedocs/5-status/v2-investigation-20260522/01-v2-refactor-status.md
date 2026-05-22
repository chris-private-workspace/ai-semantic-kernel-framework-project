# V2 重構狀況與進度調查報告（Task 1）

**調查日期**: 2026-05-22
**調查者**: AI 助手（Claude Opus 4.7）
**範圍**: V2 重構整體 — Phase 49-58（後端 11+1 範疇 + SaaS Stage 1）
**方法**: 2 個 sub-agent 並行掃描 21 份規劃文件 + 37 份 Phase 49-56 retrospective + git/CI/test 驗證
**狀態**: ✅ 完成

> 本報告是 3 份調查報告的第 1 份。第 2 份 = 前端架構/設計系統狀況；第 3 份 = mockup 一致性根因。

---

## 1. 執行摘要（先看這段）

V2 重構**結構上已完成且紀律良好**，但有一個你必須知道的關鍵落差：

- **後端 11+1 範疇**：22/22 sprint 於 Sprint 55.2（2026-05-04）宣告 100% 完成，全範疇達 Level 4+，Cat 9 達 Level 5。SaaS Stage 1 亦 3/3 完成（Sprint 56.3）。
- **但「完成」是 code-level 完成**：Sprint 57.5 自己做的「Reality Check」用 dual-scoring 揭露 — **code-level ~85% / runtime-level ~40%**。意思是「每個 sprint 的隔離測試會過」，但「整個系統端到端跑起來」並未被驗證。
- **企業 SaaS 對標**：V2 整體只達業界企業 SaaS baseline 的 **~30-40%** — 核心強、周邊（合規 / SRE / 生產基礎設施 / 公開 API）幾乎未動。

**對你 3 項任務的意義**：V2 後端核心（agent harness）是真材實料且領先；卡住的前端問題（Task 3）與後端無關 —— 前端從 Phase 57 才開始，是另一條獨立軌道。這點很重要：**前端的 mockup 一致性問題不是 V2 後端架構造成的**。

---

## 2. V2 路線圖總覽（Phase 49-58）

V2 於 2026-04 啟動，因 V1 真實對齊度僅 27%（11 範疇 8 個處於 Level 0-2）而決定重新出發。路線圖 2026-04-28 經 review 從 16→**22 sprint** 擴充（~5.5 個月）。

| Phase | Sprints | 範圍 | 狀態 |
|-------|---------|------|------|
| 49 Foundation | 49.1-49.4 | V1 封存、V2 骨架、CI、DB+RLS、Adapters、OTel、lint | ✅ 2026-04-29 |
| 50 Loop Core | 50.1-50.2 | Cat 1+6、POST /chat SSE、chat-v2 前端 | ✅ |
| 51 Tools+Memory | 51.0-51.2 | Mock tools、Cat 2、Cat 3 | ✅ |
| 52 Context+Prompt | 52.1-52.2 | Cat 4、Cat 5 | ✅ |
| 53 State+Error+Guardrails | 53.1-53.7 | Cat 7/8/9 + governance/HITL + audit cycles | ✅ |
| 54 Verification+Subagent | 54.1-54.2 | Cat 10、Cat 11 | ✅ |
| 55 Production | 55.1-55.6 | 業務領域、audit cycles、**V2 22/22 closure** | ✅ |
| 56 SaaS Stage 1 | 56.1-56.3 | 租戶生命週期、quota/admin auth、SLA+cost ledger | ✅ 3/3 |
| **57 Frontend+SaaS** | 57.1-57.27+ | **前端頁面開發（持續進行中）** | 🔄 進行中 |

> Phase 57 是前端軌道，與後端 11+1 範疇是兩條獨立的工作線。Phase 57 = Task 2 的範圍。

---

## 3. 11+1 範疇成熟度表（後端，Phase 49-56）

成熟度量表：L0(0%) → L3(45-65% 整合+測試) → L4(70-85% 主流量+測試) → L5(90-100%)。目標：全範疇 ≥ L4。

| # | 範疇 | 實作 Sprint | 宣稱 Level | 實際交付 |
|---|------|------------|-----------|---------|
| 1 | Orchestrator Loop | 50.1-50.2 | L3 | 真 `while`-loop TAO、StopReason enum、工具結果回注、SSE 事件 |
| 2 | Tool Layer | 51.1 | L3 | Registry/executor/sandbox/permissions、6 builtin + 18 業務工具 |
| 3 | Memory | 51.2 | L3 | 5 層 memory、retrieval/extraction、衝突解析、memory_tools |
| 4 | Context Mgmt | 52.1 | L3 | Compactor、observation masker、JIT retrieval、token counter |
| 5 | Prompt Construction | 52.2 | **L4** | DefaultPromptBuilder、3 種 position strategy、100% 主流量 |
| 6 | Output Parsing | 50.1→50.2 | **L4** | 完全 native tool_calls + 前端顯示 |
| 7 | State Mgmt | 53.1 | L3 | Typed LoopState、checkpointer、time-travel、HITL pause/resume |
| 8 | Error Handling | 53.2 | **L4** | 4 error class、retry cap=2、recovery、fault injection |
| 9 | Guardrails | 53.3+53.4/53.5 | **L4→L5** | Engine、3 層 guardrails、tripwire、WORM hash-chain audit |
| 10 | Verification | 54.1 | **L4** | Verifier ABC、rules/LLM-judge、correction loop (max 2) |
| 11 | Subagent | 54.2 | **L4** | 4 模式（Fork/Teammate/Handoff/AsTool）、mailbox、無 worktree |
| 12 | Observability | 49.4（cross-cutting）| L4 | OTel tracing/metrics、trace_context 傳遞 |

**後端代碼結構驗證**：`backend/src/agent_harness/` 14 個子目錄齊全（11 範疇 + observability + hitl + _contracts），與規劃一致。

**測試數成長**：150(49.4) → 259(50.2) → 596(53.1) → 1351(54.2) → **1696 collected（2026-05-22 驗證）**。

---

## 4. 關鍵落差：dual-scoring（code-level vs runtime-level）⚠️

這是 Task 1 最重要的發現。Sprint 57.5「V2 Reality Check」引入 dual-scoring framework：

| 軸線 | 衡量什麼 | 分數 | 證據 |
|------|---------|------|------|
| **Code-level** ★★★★ | paper 對齊的結構、測試、lint 通過 | **~85%** | pytest 1598、mypy 0/295、8 條 V2 lint、0 LLM-SDK leak、16 migrations |
| **Runtime-level** ★★ | 真的能 boot、persist DB、端到端跑 | **~40%** | 7 條 RED gap 0/7 closed、default boot 載入 stub、chat session → DB 0 變化 |

**核心模式**：V2 被優化成「每個 sprint 的隔離測試會過」，而不是「整個系統端到端跑起來」。21 份規劃文件分層：9 份強對齊 / 8 份輕微 drift / 4 份顯著落差（docs 10、14、15、**16-frontend-design**）。

> 注意 doc 16 = 前端設計規劃，是「顯著落差」分類之一 —— 這直接呼應你遇到的前端問題，Task 2 會深入。

### Sprint 57.5 → 57.6 的 5 條 RED 修復狀況

| ID | RED 發現 | 57.6 狀態 |
|----|---------|----------|
| R1 | `dev.py` 指向 stub `src/main.py` 而非真 `api/main.py`；vite proxy port drift | ✅ 已修 |
| R2 | `.env` 未自動載入 → real-LLM 模式 503 | ✅ 已修 |
| R3 | Chat session → DB 0 變化（sessions/audit_log/cost_ledger/tool_calls）| 🟡 部分 — 只 audit_log 接上；sessions+tool_calls 延後（卡在缺 JWT user_id 抽取基礎設施）|
| R4 | doc 16 宣稱 12 個前端頁；實際只 4 個真正 ship、3 placeholder、5 未開發 | 🟡 部分 — 只補文件，頁面未重建 |
| R5 | AP-4 Potemkin 未強制；placeholder 文字繞過 CI | ✅ 已修 — 第 9 條 lint + nightly E2E smoke workflow |

**淨結果**：5 條 RED 中 3 條完全關閉、2 條部分。**R4 正是前端問題的源頭** —— 它在 57.5 被識別但只「補文件」，真正的頁面重建延後到了 Sprint 57.18+ 的 mockup-fidelity epic（Task 2/3 主軸）。

---

## 5. 企業 SaaS 對標落差

`enterprise-saas-gap-analysis-20260508.md`（8 個 sub-agent 並行對標 2026 業界 baseline）：**V2 ≈ 企業 SaaS baseline 的 30-40%**。

**Top 10 critical gaps**（截至 2026-05-10）：1 done + 2 partial + **7 open**。
- 已做：Frontend Foundation 1/N ✅
- 部分：Auth（WorkOS 選定、OIDC login ship；RS256/SAML/SCIM/MFA 延後）、Frontend Auth UX shell
- 未動：Status Page/Incident Response、SOC 2、SBOM/Cosign/Trivy（EU CRA 2026-09 強制）、APAC PDPA、IaC/Terraform、Public API spec、Outbox pattern

**Buy-vs-Build**：9 條決策，只有 IAM=WorkOS 已決；其餘 8 條（Billing/Support/Analytics/Feature Flags/GRC/Status/Email/CMS）未決。建議原則：「自研 11+1 agent harness（差異化），買 SaaS 周邊（非差異化）」。

**各領域覆蓋**：Agent Harness Core code 85%/runtime 40%；Identity ~10%；DevOps ~30%；Observability telemetry 70%/ops 10%；Security controls 50%/cert 0%；Data OLTP 70%/analytics 0%；API internal 90%/public ~15%；Commerce ~17%。

---

## 6. 當前 git / CI 狀態（2026-05-22 驗證）

- **當前 branch**：`feature/sprint-57-27-overview-rebuild`
- **Sprint 57.27**：`/overview` operator dashboard mockup-fidelity 全重建（9 widgets 1:1），已於 2026-05-21 closeout，**PR #160 OPEN**（尚未 merge）
- **main 最新**：`fb27df73`（Sprint 57.26 Foundation-Fidelity Token Correction）
- **後端測試**：1696 collected
- **Branch protection**：enforce_admins=true / review_count=0（solo-dev policy）/ 5 條 required CI checks

---

## 7. 風險與待處理項

- **AD（Audit Debt）紀律成熟**：Phase 53.7、55.3-55.6 是專門的 audit cycle mini-sprint，多數 AD 已關閉。Day-0「plan-vs-repo grep verify」在 55.6 單 sprint 就抓到 11 個 wrong-content drift。
- **仍開放的 reality-gap carryover**：AD-Reality-3a/3b（sessions/tool_calls 持久化，卡在 JWT user_id 基礎設施）。
- **企業 SaaS 周邊未啟動**：合規、SRE ops、生產 infra、公開 API ≈ baseline 的 30-40%，多數未開工。
- **paper-vs-reality 訊號**：L4 成熟度宣稱是「代碼存在」基礎的；Sprint 55.6 AD-Cat8-2 發現一個標記為完成的範疇內含 dead `_retry_policy` attribute —— 證實 L4 宣稱可能掩蓋部分未接線的內部。

---

## 8. 結論（給 Task 2/3 的橋接）

1. **V2 後端核心是健康的** —— 11+1 範疇結構完整、紀律良好、測試 1696 條、agent harness 是這個專案的真正差異化資產。
2. **「完成」要打折看** —— code 85% / runtime 40%；隔離測試過 ≠ 端到端可用。
3. **前端是獨立、較晚、且明確標記為「顯著落差」的軌道** —— doc 16 是 4 份 significant-gap 文件之一；Sprint 57.5 R4 識別了前端頁面落差但只補文件；真正的重建從 Sprint 57.18 才開始。
4. **你遇到的前端 mockup 卡關問題，根源不在 V2 後端架構**，而在 Phase 57 前端軌道自身的方法論 —— 這正是 Task 2（盤點前端現況）與 Task 3（診斷根因）要回答的。

---

**下一步**：Task 2 — 前端架構/頁面/設計系統重構狀況調查。
