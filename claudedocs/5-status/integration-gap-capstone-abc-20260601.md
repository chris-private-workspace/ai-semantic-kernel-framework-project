# 整合盤點 A+B+C 總 Capstone —— 15 項缺口的收斂、工作束、優先序

**Purpose**: 把整合盤點(`integration-progress-20260531.md`)的 A 區(6 接線缺口)+ B 區(4 優化)+ C 區(5 研究)共 15 項逐點分析收斂成單一決策導航:兩條跨區「工作束」、一張優先序表、盤點需校正的兩處過時措辭。本檔是 **analysis 層 capstone**(非 sprint plan,守 rolling 紀律 —— 只排序,不承諾具體未來 sprint task)。
**Category**: Cross-cutting integration analysis(收斂 11+1 範疇 + 前端 + DevOps + 合規)
**Scope**: 整合盤點 A+B+C 收尾
**Created**: 2026-06-01
**Status**: Active(decision aid)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — 收斂 A(6)+B(4)+C(5)= 15 項為工作束 + 優先序 + 盤點校正清單

**Related(本檔為下列之總 capstone)**:
- `integration-progress-20260531.md` — 原始總盤點(本檔校正其 §B-9 + §132 兩處過時措辭)
- `area-a-integration-sequencing-capstone-20260531.md` — A 區子 capstone(loop 接線)
- A 區:`cat3/cat5/cat11/cat12/cat-events-to-sse/frontend-real-data-*`(6 份)
- B 區:`cat8-errorbudget-redis` / `cat10-verification-default-enable` / `b9-mockup-repoint` + REFACTOR-006(B-10 已落地)
- C 區:`c11-real-llm-e2e` / `c12-iam-block-bc` / `c13-agents-workflows-pages` / `c14-compliance-axis` / `c15-devops-data-platform`

---

## 0. 一句話總結

> **15 項缺口收斂成兩條「鑰匙鏈」**:① **real-LLM 上線束**(C-11 gate 是鑰匙 → 解鎖 A 區接線驗收 + B-7 budget + B-8 verification)② **billing 正確性束**(B-7 + B-8 + C-15 cost_ledger,real-LLM 上線即真金白銀)。其餘為獨立項(前端接線 / 合規地基 / workflows 設計)。**很多「缺口」其實是「已建好沒接通」或「有意 interim debt」,真正要從零做的少。**

---

## 1. 15 項全景(性質分類)

| 區 | 項 | 一句話 | 性質 |
|----|----|--------|------|
| A-1 | Cat 3 Memory 注入 | store 完整,3 處沒接 loop | 接線 |
| A-2 | Cat 5 PromptBuilder | 建好但 handler 不傳 → fallback 恆走(**拱心石**)| 接線 |
| A-3 | Cat 11 Subagent/HANDOFF | 3 模式 executor 在、HANDOFF 空殼;全未注入 | 接線 + 設計 |
| A-4 | Cat 12 loop tracer | 只 root span + no-op tracer 注入 | 純加法 |
| A-5 | events→SSE | 部分事件靜默丟(不 crash)| 補洞 + infra |
| A-6 | 前端真資料 | 多數 fixture interim debt;admin-tenants/memory 真接線弄丟 | 前端 |
| B-7 | RedisBudgetStore | **已建好未接線**(AP-2)+ per-request 重建使 budget 失效 | 接線 |
| B-8 | Verification 預設開啟 | 不該翻;3 launch-blocker | 研究 → 決策 deferred |
| B-9 | Mockup re-point | **前提過時**:22/22 PARITY 已達,剩 14 PROP + 4 二階債 | 已完成 + 二階債 |
| B-10 | verifier_factory | **已刪除落地**(REFACTOR-006) | ✅ DONE |
| C-11 | real-LLM e2e | **gate 早已建好**,缺 3 secrets + 取消註解(**鑰匙**)| ops |
| C-12 | IAM Block B/C | 前端 ship + 後端有意缺(3 AD)| 有意 gap |
| C-13 | agents/workflows | agents 已改名實現(fixture-only);workflows 全缺+無 mockup | 混合 |
| C-14 | 合規軸 | 程式 0%、地基齊;法規細節須外部查證 | 0% + 地基 |
| C-15 | DevOps/Data | 有 Bicep IaC;真缺 DR/Outbox(billing 雙扣)/analytics | 混合 |

**性質統計**:已完成 1(B-10)/ 已完成+二階債 1(B-9)/ 接線(已建好沒接通)5(A-1,A-2,A-3,A-6,B-7)/ 純加法或補洞 2(A-4,A-5)/ ops 1(C-11)/ 有意 gap 1(C-12)/ 研究決策 1(B-8)/ 混合 2(C-13,C-15)/ 0%+地基 1(C-14)。
→ **真正「從零做」的極少**;多數是接線、啟用、或還 interim debt。

---

## 2. 🔑 工作束 1:real-LLM 上線(C-11 是鑰匙)

```
        ┌─────────────────────────────────────────┐
        │  C-11  啟用 e2e-real-llm-smoke.yml        │
        │  (設 3 GitHub Secrets + 取消 schedule註解) │
        │  零 code,<$0.15/月,gate 已建好           │
        └───────────────────┬─────────────────────┘
                            │ 解鎖「主流量真實驗證」
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  A 區接線驗收        B-7 budget 驗證      B-8 verification 量測
  (Cat4/7/8/10       (budget 只在        (假陽性率/延遲/
   真串流路徑證)       real-LLM 流量跑)     judge token 漏記)
```
- **為何 C-11 先**:A 區接線(Sprint 57.63 已注入)只用 mock 驗;B-7 budget、B-8 verification 都只在 real-LLM 流量才真執行。C-11 是這三者唯一的主流量驗證點,且**零 code、成本可忽略、gate 已建好**。
- **動作**:用戶提供 Azure key → 設 `AZURE_OPENAI_{ENDPOINT,API_KEY,DEPLOYMENT_NAME}` 3 個 repo Secret → Actions 手動 Run "E2E Real-LLM Smoke" → 綠即 close `AD-Cat4-7-8-10-RealLLM-E2E`。

---

## 3. 🔑 工作束 2:billing 正確性(real-LLM 上線即真金白銀)

| 項 | 缺陷 | 機制 |
|----|------|------|
| B-7 | budget 跨實例不一致 + per-request InMemory 重建 → budget 失效 | InMemoryBudgetStore 每請求 new(`handler.py:218`)|
| B-8 | judge LLM call 不入 cost ledger 也不入 quota | judge 走獨立 `chat()`,不經 LoopCompleted accumulator |
| C-15 | cost_ledger 雙扣/漏扣 | record_llm_call 與 LLM call 不在同交易 + 無 idempotency + Outbox 未實作 |

→ 三者同根:**cost/token 記帳未與 LLM 呼叫原子耦合**。real-LLM 上線(工作束 1)後立即成真實財務風險。建議合為一個「billing 正確性」spike(idempotency key + 交易耦合 + 可選 Outbox 分階段)。

---

## 4. 獨立項(不在兩束內,可並行排程)

| 項 | 槓桿 | 依賴 |
|----|------|------|
| **A-2 Tier1 + A-1 Tier1 + A-3a**(拱心石 bundle)| 高(共用「註冊 builtin 工具/傳 builder」一改動)| 無;但驗收靠 C-11 |
| A-4 loop tracer | 中(可觀測性,RecordingTracer 可測)| 無 |
| A-5b 事件 schema codegen + CI parity | 高(防未來靜默漂移)| 無 |
| B-9 D3 per-page 視覺 CI | 高(把 drift 從人眼 sweep 變 CI 自動抓)| 無 |
| A-6a admin-tenants 重掛 | 低成本贏面(~½天)| 無 |
| C-13 agents 補後端 | 中(orchestrator CRUD + subagents ORM)| 無 |

---

## 5. 需先「決策 / 外部輸入」才動工的項

| 項 | 卡在什麼 |
|----|---------|
| B-8 Verification 預設開啟 | 3 launch-blocker(billing/模板/零測試);維持 deferred |
| C-12 IAM Block B/C | 商業優先序;最小=invites spike(**禁止預寫 Block B 規劃**)|
| C-13 workflows | **連 mockup 都沒有** → 須先產品決策 + 設計 |
| C-14 合規軸 | **法規細節須外部查證**(法務);第一步 GDPR erasure spike(地基最齊)|
| C-15 DR / deploy 啟用 | Azure provision + Secrets(同 C-11 前提)|

---

## 6. 📋 盤點需校正的兩處過時措辭(改 `integration-progress` 需用戶授權)

| 位置 | 原文 | 應為 | 依據 |
|------|------|------|------|
| §B-9(item 9)| 「眼湊 HSL...目前僅 overview 過」| 「22/22 active 頁 PARITY 已達(Sprint 57.40-57.45),CI gate 綠;剩 14 PROP promote + 4 二階債」| `b9-mockup-repoint-status-analysis` + 親跑 CI gate |
| §15 / §132 | 「無 Terraform、~30%」| 「有 Bicep IaC(5 模組,未驗部署),無 Terraform/Helm;deploy pipeline disabled;真缺 DR/Outbox/analytics」| `c15-devops-data-platform-analysis` + 親驗 `infra/` |

> 另:C-11 也校正了「real-LLM 0%」的隱含 —— gate 已建好,缺的是 secrets 而非基礎設施。

---

## 7. 整體優先序建議(rolling:只排序,不預寫 sprint plan)

| 序 | 動作 | 為何 | 成本 |
|:--:|------|------|------|
| ⭐1 | **C-11 啟用 real-LLM e2e** | 鑰匙;解鎖 A 驗收 + B-7 + B-8;零 code | 極低(設 secret + 按鈕)|
| 2 | **拱心石 bundle**(A-2T1 + A-1T1 + A-3a)| 共用一改動,解鎖最多 loop 能力;驗收靠 #1 | 中 |
| 3 | **billing 正確性 spike**(B-7 + B-8 + C-15 cost)| real-LLM 上線即財務風險 | 中 |
| 4 | A-5b schema codegen + B-9 D3 視覺 CI | 防未來漂移,高槓桿 infra | 中 |
| 5 | A-4 tracer / A-6a admin-tenants | 純加法 / 最便宜贏面 | 低 |
| 6 | C-12 invites spike / C-13 agents 後端 | 視商業優先序 | 中 |
| 後排 | C-14 合規(須法務)/ C-13 workflows(須設計)/ C-15 DR(須 Azure)| 外部輸入未到 | — |

---

## 8. 給 next session 的最短交接

1. A+B+C 共 16 份分析 + 2 capstone 在 `claudedocs/5-status/`(A 區 PR #220 merged、B 區 PR #221 merged、C 區待 commit)。
2. **想動工最自然的第一步 = C-11**(用戶給 Azure key → 設 3 secret → Run workflow,零 code)。
3. **第一個實作 sprint** = 拱心石 bundle(A-2T1 + A-1T1 + A-3a),走 V2 sprint workflow(讀最近 closed sprint plan 當模板)。
4. 兩處盤點措辭待校正(§6),改原盤點需授權。
