# C-11 深度分析:real-LLM e2e —— gate 已建好,缺 secrets + 取消註解

**Purpose**: 評估 real-LLM 端到端驗證(C-11)的真實狀態與啟用所需。**重大校正:e2e gate 早已完整建好**(`e2e-real-llm-smoke.yml`,Sprint 57.6),不是「缺 marker / 缺 test」——缺的是 ① GitHub Secrets `AZURE_OPENAI_*` ② 取消 schedule 註解。這是 A 區 + B-7 + B-8 的共同前提。本檔為 research 分析(非 sprint plan)。
**Category**: CI / E2E real-LLM verification(cross-cutting)
**Scope**: C 區研究分析 / C-11
**Created**: 2026-06-01
**Status**: Active(analysis;對應 `AD-Cat4-7-8-10-RealLLM-E2E` deferred)

**Modification History (newest-first)**:
- 2026-06-03: §8 added — 本機 real-LLM smoke 實跑（real-LLM 閉環 LIVE + 已驗證；cost_ledger Δ=0 待釐清）+ root-cause 深查推翻初判 streaming bug + 2 確認 billing 缺口（model/pricing-key 不匹配 $0 成本 + max_tokens 不相容 gpt-5.2）+ 3 衍生 AD。零 code、未重啟。
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

---

## 8. 執行結果（2026-06-03 本機 real-LLM smoke + root-cause 深查）

> **方法校正**：用戶 policy「secret 不進 GitHub」→ 不走 CI gate（§4 路徑 A），改走**本機路徑**（§4 末行）。本機 `.env` 4 個 `AZURE_OPENAI_*` 全已 set（確認）→ 直接在本機重現 workflow 的 smoke：reuse 既有 running backend（PID 28832，起於 2026-06-01 16:30）→ `POST /auth/dev-login` 取 v2_jwt → `POST /api/v1/chat/` `{mode:real_llm}` → 驗 SSE + DB delta。**全程零 GitHub secret、零 code change**。

### 8.1 Smoke 結果（5 條驗收，3.5 過 / 1 未過）

| 驗收 | 結果 | 證據 |
|------|------|------|
| HTTP 200（非 503）| ✅ | real_llm handler 通；Azure 憑證有效 |
| `event: loop_end` | ✅ | SSE 含 loop_end frame |
| 真實 LLM 回覆（非 mock）| ✅ | gpt-4o（label）回 `"Hello there, nice to meet you."` |
| `audit_log` Δ≥1 | ✅ | Δ=1（1166→1167）|
| **`cost_ledger` Δ≥2** | ❌ | **Δ=0**（2→2，完全沒寫行）|

### 8.2 Root-cause 深查 —— 推翻初判「明確 streaming code bug」

初判（adapter 串流缺 `stream_options.include_usage`）經逐項實證**全部推翻**：

| 假設 | 結果 | 證據（file:line / 實測）|
|------|------|------|
| 串流缺 include_usage | ❌ 不成立 | loop 用**非串流** `chat()`（`loop.py:1032`），不是 `stream()` |
| `response.usage` 沒帶回（tokens=0）| ❌ 不成立 | 直接實測 `AzureOpenAIAdapter.chat()` → `TokenUsage(prompt=12, completion=9, total=21)`（usage 捕捉正常）|
| `record_llm_call` 因缺 pricing 跳過 | ❌ 不成立 | pricing=None 時走 **zero-cost 分支仍寫 2 行**（`cost_ledger.py:138-184`）|
| pricing yaml 壞掉觸發 fail-soft | ❌ 不成立 | `PricingLoader().load_from_yaml('config/llm_pricing.yml')` 實測**載入 OK** |
| pricing loader 沒 wire | ❌ code 已修 | FIX-022 在 lifespan `main.py:167` 呼叫 `_wire_pricing_loader()`；進程起於 06-01（FIX-022 2026-05-31 已在 disk）|

**結論**：real-LLM 關鍵 code 路徑**看來正確**。`cost_ledger Δ=0`（完全沒行）最可能是**正在跑的 backend 進程（PID 28832）在它自身啟動時 pricing loader 沒裝成**（cost_ledger_service 為 None → `router.py:435` gate `cost_ledger is not None` False → 整段跳過）。屬 **process-state，非 code bug**。**唯一確認法**：重啟 backend（current code）+ 看啟動 log「pricing loader wired/not wired」（`main.py:149/151`）+ 重跑 smoke。**本次依用戶指示未重啟、未改 code** → 列為待驗。

### 8.3 但 C-11 揪出 2 個確認的真實 billing 缺口（與 8.2 無關，重啟也不消失）

1. **Model / pricing-key 三方不匹配** → cost 行（即使有寫）為 **$0 成本**：
   - deployment 實際 = `gpt-5.2`（`AzureOpenAIConfig.deployment_name`）
   - config `model_name` = `gpt-4o`（→ `ChatResponse.model` → `LoopCompleted.model` → `record_llm_call(model="gpt-4o")`）
   - `config/llm_pricing.yml` 只有 `azure_openai/gpt-4o-mini`（**無 gpt-4o、無 gpt-5.2**）
   - → `get_llm_pricing("azure_openai","gpt-4o")` = None → `record_llm_call` zero-cost 分支 → cost 行 `total_cost_usd=0`（`cost_ledger.py:138-144`；程式註解自稱「observable anomaly」）。`router.py:128` 註解本身已點出此 model-vs-pricing-key 落差。

2. **`max_tokens` 與 gpt-5.2-class deployment 不相容**：直接傳 `max_tokens` → Azure 回 **400「'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead」**。loop 主流量未傳 `max_tokens`（`loop.py:1028`）故主路徑不撞；但 **e2e-real-llm-smoke.yml 的成本護欄靠 `MAX_TOKENS_PER_CALL`/`max_tokens`**（`:132`）→ 在此 deployment 會 400。adapter `_stream_impl:282` + `chat()` 都用 `max_tokens` kwarg。

### 8.4 C-11 狀態更新

- **real-LLM 閉環 = LIVE + 已驗證**：HTTP 200 / loop_end / 真實回覆 / audit_log Δ=1。Azure 路徑真實可用（不再「全程 mock」）。
- **cost-ledger leg 未綠**：受 8.2（待重啟驗）+ 8.3（確認缺口）影響。e2e gate 的 `cost_ledger Δ≥2` 在此環境不會過，直到 8.2 釐清 + 8.3 修正。
- **CI gate（`e2e-real-llm-smoke.yml`）維持手動/關閉**（用戶 policy：secret 不進 GitHub）；本機路徑為實際驗收途徑。

### 8.5 衍生 AD（記入 `claudedocs/1-planning/next-phase-candidates.md`）

- `AD-RealLLM-CostLedger-ProcessState-Verify`（待驗）— 重啟 backend + 捕捉啟動 pricing-loader log + 重跑 smoke，判定「沒 cost 行」是進程狀態 vs code bug。
- `AD-Cost-Ledger-Model-Pricing-Key-Mismatch`（確認）— model_name=gpt-4o / deployment=gpt-5.2 / pricing 僅 gpt-4o-mini → cost 行 $0。修法選項：對齊 `model_name` 至真實 deployment 模型 + 補 pricing yaml 真實模型條目（gpt-4o / gpt-5.2）；或讓 `model_name` 反映 deployment。屬 billing 正確性束（B-7/B-8/C-15）。
- `AD-Adapter-MaxTokens-NewModel-Param`（確認）— gpt-5.2-class deployment 需 `max_completion_tokens`；adapter `chat()`/`_stream_impl` 與 e2e workflow 成本護欄需相容處理（依 model / api-version 切換 param 名）。

> **Verified ratio**：8.1-8.3 每條 claim 對應 file:line 或本機實測指令輸出；8.2 為「推翻初判」的反證集；8.4 狀態為實測導出。本次純文件，無 code change、無重啟。
