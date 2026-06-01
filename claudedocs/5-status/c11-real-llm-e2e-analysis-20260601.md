# C-11 深度分析:real-LLM e2e —— gate 已建好,缺 secrets + 取消註解

**Purpose**: 評估 real-LLM 端到端驗證(C-11)的真實狀態與啟用所需。**重大校正:e2e gate 早已完整建好**(`e2e-real-llm-smoke.yml`,Sprint 57.6),不是「缺 marker / 缺 test」——缺的是 ① GitHub Secrets `AZURE_OPENAI_*` ② 取消 schedule 註解。這是 A 區 + B-7 + B-8 的共同前提。本檔為 research 分析(非 sprint plan)。
**Category**: CI / E2E real-LLM verification(cross-cutting)
**Scope**: C 區研究分析 / C-11
**Created**: 2026-06-01
**Status**: Active(analysis;對應 `AD-Cat4-7-8-10-RealLLM-E2E` deferred)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — C-11 real-LLM e2e(Workflow 並行蒐證 + 主 session 親驗 e2e-real-llm-smoke.yml 全檔)

**Related**:
- `integration-progress-20260531.md` §11(C-11 來源)
- `cat8-errorbudget-redis-wiring-analysis-20260531.md`(B-7,共同前提)
- `cat10-verification-default-enable-analysis-20260601.md`(B-8,共同前提)
- `area-a-integration-sequencing-capstone-20260531.md`(A 區,共同前提)
- `.github/workflows/e2e-real-llm-smoke.yml`(關鍵 gate)
- Sprint 57.63 retrospective §AD-Cat4-7-8-10-RealLLM-E2E

---

## 0. 一句話結論

> **real-LLM e2e gate 早已完整建好**(`e2e-real-llm-smoke.yml`,Sprint 57.6 建,spin up Postgres+Redis+backend → POST `real_llm` chat → 驗 `loop_completed` + cost_ledger Δ≥2 + audit_log Δ≥1)。啟用只需 **2 件事**:① 在 repo Secrets 設 `AZURE_OPENAI_ENDPOINT/API_KEY/DEPLOYMENT_NAME` ② 取消 `schedule` 註解(或手動 `workflow_dispatch`)。**這是 A 區接線 + B-7 budget + B-8 verification 全部的共同前提** —— 一旦能真跑,這三項的「未實證」狀態才能轉「已驗證」。

---

## 1. 校正兩個 agent 的盲點(均經主 session 親驗)

Workflow 兩個 agent 各漏一半,我親驗後拼出完整圖:
- **C-11 agent** 只查 pytest marker(`grep real_llm → pyproject.toml 無 marker`),結論「無 live test、缺 key」——**漏了 CI workflow**。
- **C-15 agent** 列出 `e2e-real-llm-smoke.yml` 是 active workflow,但沒讀內容、沒連到 C-11。
- **我親驗**:`ls .github/workflows/` 確認該檔存在 + 親讀全檔 → 它就是「缺的 real-LLM e2e」,且**已經是完整可運作的 gate**。

→ 教訓同 B-9:agent 分頭看會各有盲點,主 session 交叉驗證才看出全貌。

---

## 2. e2e gate 真實內容(親讀 `e2e-real-llm-smoke.yml` 全 194 行)

| 面向 | 事實 | 證據 |
|------|------|------|
| 用途 | 關 Sprint 57.5 reality check「CI 從不跑 chat router→real LLM→DB persist」的洞(AD-Reality-5)| `e2e-real-llm-smoke.yml:8-16` |
| 流程 | spin up postgres:16 + redis:7 → migrate → seed tenant+user → 起 uvicorn → POST `/api/v1/chat/` mode=real_llm | `:61-173` |
| 驗收 | ① SSE 含 `event: loop_completed` ② cost_ledger Δ≥2(input+output split)③ audit_log Δ≥1 | `:172-185` |
| 成本護欄 | `max_tokens=100` + 單一請求/run;估 <$0.005/run、<$0.15/月 | `:27-29` |
| Trigger | `workflow_dispatch`(隨時可手動)+ `schedule` daily 04:00 **註解掉** | `:42-54` |
| Gate 強度 | **informational only**,非 branch protection 5 required checks,失敗**不**擋 PR | `:23-25` |
| 啟用條件 | AD-CI-6:等 Phase 58 production launch 配 `AZURE_OPENAI_API_KEY` secret | `:20-21,50-52` |

> 它連 cost_ledger Δ≥2 都驗——**正好能抓 B-8 指出的 judge-token 漏記**(若 verification enabled,judge call 不入 ledger,Δ 會不符)。e2e gate 與 B-7/B-8 是互補的。

---

## 3. 程式碼側已就緒(親驗 + 與 C-11 agent 一致)

- `build_real_llm_handler`(`handler.py:178-185`)缺 `AZURE_OPENAI_ENDPOINT/API_KEY/DEPLOYMENT_NAME` 任一 → `raise RuntimeError` → router 轉 HTTP 503(`router.py:216-223`)。
- Cat 4/7/8/10 注入點齊全(`handler.py:207-248`,Sprint 57.63)。
- `AzureOpenAIConfig` BaseSettings auto-load `AZURE_OPENAI_*`(`adapters/azure_openai/config.py:34-67`)。
- `.env.example:62-65` 已記錄 4 個 key 的 placeholder。
- 無 `real_llm` pytest marker(`pyproject.toml:60-68` 7 個 marker 無此項)—— 但這**不重要**,因為 e2e 驗證走的是 **CI workflow(curl 真 backend)**,不是 pytest marker。Test 註解提到的 `-m real_llm` 是另一條尚未建的路徑。

---

## 4. 啟用 real-LLM e2e 的精確步驟(不需寫 code)

1. **取得 Azure OpenAI 資源**:endpoint + api_key + 一個 deployment(如 gpt-4o)。
2. **設 GitHub repo Secrets**:`AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_DEPLOYMENT_NAME`(workflow `:114-116` 已 wire `${{ secrets.* }}`)。
3. **手動觸發**:Actions → "E2E Real-LLM Smoke" → Run workflow(`workflow_dispatch` 隨時可用,無需改任何檔)。
4. **(可選)轉常態**:取消 `:53-54` schedule 註解 → daily 04:00 自動跑。
5. **(可選)升 required check**:納入 branch protection(`:23-25` 註明 Phase 58+ 才考慮)。

> 本機驗證替代路徑:`.env` 填真 key → `python -m uvicorn api.main:app` → POST real_llm chat,人工觀察 SSE。

---

## 5. 為何 C-11 是「拱心前提」

| 下游項 | 為何卡 C-11 |
|--------|------------|
| **A 區接線**(Cat 4/7/8/10 注入)| Sprint 57.63 已注入但只用 mock 驗;真 LLM 串流路徑上 `StateCheckpointed`/`ContextCompacted`/`VerificationPassed` 是否真發生,要 e2e 才證 |
| **B-7 RedisBudgetStore** | budget 只在 real-LLM 流量才被執行;e2e 是它唯一的主流量驗證點 |
| **B-8 Verification 開啟** | 假陽性率 / 延遲 / judge-token 漏記,全要 real-LLM e2e 量 |

→ ∴ C-11 應**最先做**(在任何 A/B 實作 sprint 的驗收環節)。成本極低(<$0.15/月),阻塞解除收益最大。

---

## 6. 唯一真實 uncertainty

- **是否本機已有 `.env` 含真 key**:`.env` 在 `.gitignore`,repo 無法確認;retro 明述「MISSING this env」。→ 這是唯一未知;若用戶手上有 Azure key,C-11 幾乎是「填 secret + 按鈕」的距離。

---

## 7. 給決策的最短建議

| 問題 | 答案 |
|------|------|
| e2e gate 要建嗎? | ❌ 已建好(`e2e-real-llm-smoke.yml`,Sprint 57.6,完整可運作)|
| 缺什麼? | Azure Secrets(3 個)+ 取消 schedule 註解(或手動觸發)|
| 要寫 code 嗎? | ❌ 零 code;純 ops(設 secret + 按鈕)|
| 急嗎? | ⭐ 最高優先 —— 它是 A 區 + B-7 + B-8 的共同驗證前提,成本 <$0.15/月 |
| 風險? | 低;有成本護欄(max_tokens=100)、informational gate 不擋 PR |
| 對應 AD? | `AD-Cat4-7-8-10-RealLLM-E2E`(deferred);啟用即可 close |

> 不需 code。建議:用戶提供 Azure key → 設 3 個 GitHub Secrets → 手動 Run "E2E Real-LLM Smoke" → 綠了即 close AD + 解鎖 A/B 驗收。
