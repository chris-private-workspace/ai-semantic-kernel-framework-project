# Thin-Spike 評估：pass^k 可靠性實測 eval harness（研究機會 #2）

**Purpose**: 評估「為 V2 agent loop 建一個 `pass^k` 可靠性實測 harness」的可行性、最小可行形狀、量測軸選擇、冗餘風險與成本。**這是評估，不是實作 sprint**；產出供決策，不預寫 sprint plan（rolling discipline）。
**Category / Scope**: 範疇 12 (Observability / Evaluation)；measurement harness（與 #136-139 同類，非 full vertical slice）
**Created**: 2026-06-24
**Last Modified**: 2026-06-24
**Status**: Active（評估快照；非 sprint）
**Grounding**: 1 個 read-only Explore agent 對 `backend/src` + `backend/scripts` + `backend/tests` 的 file:line 勘查（2026-06-24）；研究來源 `ai-agent-harness-consolidated-analysis-20260622.md` §2.7 / §5 #2 / §6（證據強度）

> **Modification History**
> - 2026-06-24: Initial — thin-spike 評估（研究機會 #2 = canonical 排序下一個；#1/#136-139 已 CLOSED）

---

## 0. 缺口背景（一句話）

平台目前以 **drive-through（跑一次能用）** 與 5 個 **A/B benchmark（兩臂比較）** 驗證品質，但**沒有任何「同一輸入重複 k 次量測一致性」的機制**。研究核心發現：**reliability ≠ capability，且隨任務長度系統性發散**——`pass^k`（k 次重複全通過的比率）才是長程可靠性的真實指標，而 `pass@1` / drive-through-once 對此**完全不可見**（τ-bench：GPT-4o retail pass@1 ~61% 但 **pass^8 <25%**）。研究並明指：**V2 的 trace persistence 是少數能廉價產生 enterprise multi-tenant pass^k 數據的位置**（`consolidated-analysis` §6 研究盲點）= 機會 #2 的價值核心。

來源：`ai-agent-harness-consolidated-analysis-20260622.md` §2.7（pass^k 為主要指標）+ §5 #2 + §4 主題 6（empirical eval 必須超越 pass@1）。

---

## 1. 現況（code-grounded，file:line）

### 1.1 既有 benchmark harness 先例（5 個，**全是 A/B 兩臂，無一是 k-run 重複**）

| 腳本 | Sprint | 形狀 | 與 pass^k 的關係 |
|------|--------|------|------------------|
| `benchmark_judge.py` | 57.111 | cheap vs strong 兩臂 + trace_delta | **PRIME 範本**（結構直接可借）|
| `benchmark_correction_hygiene.py` | 57.136 | keep vs summarize 兩臂 | A/B |
| `benchmark_key_condition.py` | 57.138 | generic vs key_condition 兩臂 | A/B |
| `benchmark_sandbox_escape.py` | 57.137 | regex vs Docker 兩臂（非 LLM）| A/B |
| `benchmark_layered_compaction.py` | 57.139 | per-layer yield | 量測非 A/B，但仍單次 |

**共用 harness pattern**（`benchmark_judge.py`）：
- `load_cases(YAML) → list[BenchCase]`（schema 驗證 + 唯一 ID + category enum）`backend/scripts/benchmark_judge.py:109-151`
- `run_*(...)`（async executor，連真 Azure）`:171-187`
- `build_report(...)`（純函式算 metrics）`:202-248`
- 雙輸出 Markdown（人讀）`:251-275` + JSON（tooling）`:300-317`
- `main()` argparse（`--fixture` / `--out`）`:322-349`
- 真 Azure：late import `build_azure_model_profile()` → `profile.cheap`/`.action` `:281-289`（temp 0.0 確定性）
- corpus：YAML under `backend/tests/fixtures/verification/*.yaml`
- CI-safe 測試：`tests/unit/scripts/test_benchmark_*.py` importlib idiom（檔路徑載入 + spy mock，**不連 Azure**）`test_benchmark_judge.py:19-45,103-120`
- 真 Azure gate：`@pytest.mark.benchmark` + env guard

> **關鍵差異**：5 個全是「**兩個不同 arm 各跑一次**」；pass^k 是「**同一 arm 跑 k 次**」。pattern 上 net-new（k-loop orchestration + 跨 run 一致性 metric 是新的），但**腳手架 100% 可借**。

### 1.2 Trace persistence「廉價數據源」（研究點名）

| 面 | file:line | 可供 pass^k 之處 |
|----|-----------|-----------------|
| `message_events` 表 | `infrastructure/db/models/sessions.py:224-268` | JSONB `event_data` + `sequence_num` + tenant-scoped + 月分區；存每個 SSE frame |
| 主流量 persist observer | `api/v1/chat/router.py:571-604`（`_persist_main_event`）| run 中每 frame 寫入（SAVEPOINT best-effort）|
| `messages` ledger（57.127）| `sessions.py:164-218` + `state_mgmt/message_store.py` | role/content/model/tokens，可離線查 |
| `LoopCompleted` 事件 | 帶 `input/output_tokens`/`provider`/`model` | 每 run 成本/模型 |
| `trace_id`（每事件）| `event_wire_schema.py:66`（BASE_FIELDS）| 跨 run 關聯 |

→ **離線一致性可算**：persisted events 含 tool calls / final answer / stop_reason / tokens。但 **prod 目前沒有「自然重複的 run」**——harness 必須**自己產生** k 次 run（online），可選擇再示範從 persistence 讀回（證「廉價數據源」論點）。

### 1.3 驅動一次 run 的入口（harness 跑 k 次的接點）

- `build_real_llm_handler(...) → AgentLoopImpl` `api/v1/chat/handler.py:280-296`（env 驗證 `AZURE_OPENAI_*` `:325-332`；`chat_client=profile.action` `:348`）
- `loop.run(*, session_id, user_input, trace_context) → AsyncIterator[LoopEvent]` `orchestrator_loop/loop.py:1942-1948`（yield LoopStarted…LoopCompleted）
- 成本：`LoopCompleted` 已 sum per-run tokens（`test_chat_cost_ledger.py:63-79`）

### 1.4 確認不存在（AP-6 冗餘檢查 — 全 grep 為零）

`pass^k`/`pass_k`/`passk` / `reliability`(除 docstring) / `fault.?inject` / `repeated.?run` / `behavioral.?consistency` / `MAST` / failure-mode taxonomy = **backend/src 全部零出現**。唯一相鄰：`FlakyTransientError` + `flaky_tool`（**test-only** retry fixture，`test_loop_retry_integration.py:93-195`，非 pass^k；但可作未來 λ fault-injection 的借用點）；`factual_consistency` judge template（單次 verifier，非 k-run）。→ **net-new，無既有實作衝突**。

---

## 2. 核心洞察：價值與最大風險

**價值更高（而非邊際）**：本平台的 DoD 鐵律是 drive-through（跑一次能用）——但這正是 **pass@1 式單次**。研究的硬數字（τ-bench pass^8 <25%）說明：一個 drive-through PASS 的功能，重複跑 8 次可能 <25% 全過。平台**目前對「跨重複 run 的可靠性」完全盲**。pass^k harness 補的是「drive-through 證一次能用、pass^k 證跨重複 run 可靠」這條 **reliability science** 的缺軸（§4 主題 6）。且研究指出 V2 的 trace persistence 是**業界少數能廉價產生這類數據的位置**——這是 V2 的結構性優勢，不做就浪費。

**最大風險 = 量測本身是否誠實有意義（而非 AP-4 Potemkin 報告）**：
1. **oracle 可信度**：pass/fail 判定靠什麼？若用 LLMJudge 當 oracle，judge 本身也有一致性問題（R-Judge：8 LLM「遠非完美」）→ judge 的 noise 會污染 pass^k 訊號。
2. **k 值與成本**：k 次 × N case × 真 Azure = 成本線性放大；k 太小（k=2）訊號弱，k 太大貴。
3. **「測不出發散」也是合法結果**：若 V2 在 corpus 上 pass^k ≈ pass@1（沒發散），那是**真實的好消息 + 誠實的 verdict**，不是失敗——但 corpus 必須含足夠難/多步的 case 才能讓發散有機會顯現（否則是「用太簡單的題證明很可靠」的假象）。

---

## 3. 設計選項矩陣

### 3.1 量測哪些軸（measure axes）

| 軸 | 定義 | 證據強度 | thin-spike 取捨 |
|----|------|---------|----------------|
| **pass^k**（核心）| 同輸入跑 k 次，每次經 oracle 判 pass/fail；pass^k = k 次全 pass 的 case 比率；對照 pass@1 = 平均單次 pass 率 | 🟢 τ-bench landmark | ✅ **必做**（headline）|
| **behavioral consistency** | 即使都 pass，k 次的 trace/答案是否一致（答案 diff / tool-序列 diff）| 🟡 獨立可量測軸 | ✅ **建議納入**（廉價，讀 persisted events 即得）|
| **fault injection (λ)** | 注入 infra fault（tool error / transient LLM error）量退化；可借 `FlakyTransientError` | 🔴 citation mis-attributed（ReliabilityBench 數字存疑）| ⏭️ **後置**（證據最弱 + Cat 8 已有 fixture，留作擴展）|
| **perturbation (ε)** | paraphrase 輸入量穩定性 | 🔴 同上 conflate | ⏭️ **後置** |

→ **推薦最小軸 = pass^k + behavioral consistency**（兩者皆 🟢/🟡 + 廉價）；λ/ε 後置（證據最弱，且各自是獨立擴展）。

### 3.2 online 產生 vs offline 消費

| 選項 | 機制 | 評估 |
|------|------|------|
| **A. online 產生（推薦）** | harness 自己呼 `loop.run()` k 次（鏡像 benchmark_judge 呼 judge）| ✅ 自足、corpus 確定、最像既有 5 腳本 |
| **B. offline 消費 persisted traces** | 查 `message_events` 既有重複 run | ❌ prod 無自然重複 run，spike 無數據可消費 |
| **A+ 證 persistence** | online 產生 + 額外示範從 `message_events` 讀回算一致性 | 🟡 可作次要 leg，證「廉價數據源」論點 |

→ **推薦 A**（online 產生）；persistence read-back 作 optional 次要證明（呼應研究「trace persistence 是數據源」）。

### 3.3 oracle（pass/fail 怎麼判）+ corpus

| oracle | 適用 | 評估 |
|--------|------|------|
| **rules-based**（exact / contains expected answer）| 封閉題（算術 / 結構化抽取）| ✅ 確定性、零 judge noise、便宜 → **優先** |
| **LLMJudge**（output_quality / key_condition）| 開放題 | 🟡 已建好可借，但引入 judge noise → 標註其一致性為已知 caveat |
| **混合（推薦）** | rules 優先、開放題才 judge | ✅ |

- **corpus**：小型（~8-15 case），**必須含 easy → multi-step 梯度**（研究：reliability 隨複雜度 super-linear 退化 → 多步題才能讓 pass^k < pass@1 顯現）。每 case：`{id, input, oracle_type, expected, category(easy/multistep/tool-use)}`。
- corpus 位置：`backend/tests/fixtures/observability/pass_k_cases.yaml`（或沿 verification/ 慣例）。

### 3.4 surface（要不要 UI / wire）

| 選項 | 評估 |
|------|------|
| **純 offline 腳本（推薦）** | 同 5 個既有 benchmark：NO frontend / NO wire event / NO migration → 乾淨 Cat 12 measurement spike |
| 加 wire/UI dashboard | ❌ 過度（YAGNI）；pass^k 是 CI/離線指標，非 chat-v2 即時面 |

→ **推薦純 offline**：`scripts/benchmark_pass_k.py` + corpus YAML + CI-safe 測試。**零 migration / 零 wire（維持 26）/ 零 frontend**。

---

## 4. 推薦的最小垂直切片（thin-spike 形狀）

> 一個 measurement harness（非 vertical slice）；目的是**在 V2 自己的 loop 上實測 pass^k 是否真的偏離 pass@1**（evidence-first payoff），並建立一個永久可重跑的可靠性實測工具。

| 元件 | 範疇 | 估計檔數 | precedent |
|------|------|---------|-----------|
| `scripts/benchmark_pass_k.py`（load_cases / run_pass_k(k) / build_report / MD+JSON）| 12 | +1 新 | `benchmark_judge.py`(57.111) |
| `tests/fixtures/observability/pass_k_cases.yaml`（~8-15 case，含 multi-step 梯度）| 12 | +1 新 | `judge_benchmark.yaml` |
| oracle helper（rules-based exact/contains + 可選 LLMJudge 包裝）| 10/12 | +1 新或內嵌 | `RulesBasedVerifier` / `LLMJudgeVerifier` |
| CI-safe `tests/unit/scripts/test_benchmark_pass_k.py`（importlib + spy loop，不連 Azure）| Tests | +1 新 | `test_benchmark_judge.py` |
| （可選）persistence read-back leg | 12 | +小段 | `message_events` 查詢 |
| **Verdict + drive-through gate**（見 §6）| — | — | 本評估關鍵 |

- **report 指標**：per-case pass@1 / pass^k / behavioral_consistency（答案 + tool-序列 agreement）/ per-category（easy vs multistep）breakdown / 每 run token 成本 + k×N 總成本。
- **k 預設**：k=5（可配置；研究 LLM eval 常 k=3-10）。
- 規模對標 `verification-trace-and-benchmark-spike`(57.111，greenfield 量測腳本 + golden fixture + benchmark marker，calib class 0.60)。

---

## 5. 冗餘 / Anti-Pattern 評估

- **AP-6（冗餘抽象）**：grep 證實零既有 pass^k/consistency/fault scaffolding（§1.4）→ net-new。與 5 個 A/B benchmark 正交（它們比 arm，這個測 repeatability）。**低風險**。
- **AP-4（Potemkin / 假報告）**：最大風險 = oracle 不可信或 corpus 太簡單 → 報告數字無意義。緩解：rules-based oracle 優先（零 noise）+ corpus 含 multi-step 梯度 + judge noise 標為 caveat（§2）。
- **AP-2（side-track）**：純 offline 腳本，但屬「永久 CI/離線可重跑工具」（同 5 個既有 benchmark），非死碼；`@pytest.mark.benchmark` 接 real-Azure 路徑。
- **LLM neutrality**：harness 經 `build_azure_model_profile` → `ChatClient` ABC，不直接 import openai/anthropic（同既有 benchmark）。

---

## 6. Drive-Through / 成敗判準（這個 spike 的 verdict gate）

thin-spike **不以「腳本存在 + 跑得動」算成功**。成功 = 真 Azure 跑完 k×N，產出**誠實 verdict**：

1. harness 對 corpus 每 case 跑 k 次真 Azure，算出 pass@1 vs pass^k vs behavioral_consistency；
2. **核心命題實測**：在 multi-step case 上，pass^k 是否 < pass@1（研究預測會發散）？**任一方向都是合法 verdict**——發散 = 證實平台有可靠性盲點（高價值，指向後續工作）；不發散 = V2 在此 corpus 上穩定（誠實好消息，但須註明 corpus 難度）；
3. 報告 MD+JSON 落地 `benchmark_reports/`，CI-safe 單元測試綠（不連 Azure）。

> **drive-through 性質**：pass^k 是 **offline/backend measurement harness（無 UI）**，故 drive-through = **真 Azure harness run 產出真報告**（同 #135 background-job「runtime verification, no UI」與 #137/#138「CATCH = 量測 harness 本身」的 pattern），非 chat-v2 UI 驅動。

---

## 7. 誠實判斷 + 成本 + 邊界

**判斷**：**值得做一個 thin spike**。理由：(a) 補的是 reliability science 的核心缺軸（drive-through 是 pass@1，pass^k 盲）；(b) net-new 無冗餘；(c) 腳手架 100% 可借 5 個 benchmark 先例；(d) V2 trace persistence 是研究點名的稀缺數據位置——結構性優勢；(e) evidence-first：spike 直接在 V2 自己的 loop 上**實測**研究的 pass^k≠pass@1 命題，而非照抄論文數字。

**成本（粗估，spike 級）**：對標 `verification-trace-and-benchmark-spike`(0.60 class)，約 1 個 measurement-harness sprint。**真 Azure 成本** = k × N case × (主 loop + oracle judge) tokens；k=5 × ~12 case 量級可控（可先用 cheap tier 跑 oracle）。**本文件只是評估，是否開 spike 由你決定**。

**Scope 邊界（即使做，也 NOT 做）**：
- ❌ fault injection (λ) / perturbation (ε)——證據最弱（🔴 mis-attributed），各自獨立擴展，後置；
- ❌ MAST 14-mode failure 自動分類器——無既有 taxonomy，獨立大件，後置（研究列為 negative-test catalog 擴展）；
- ❌ wire event / chat-v2 dashboard——YAGNI；
- ❌ 不改 oracle 既有 verifier 行為——只**包裝**呼叫，不改 `llm_judge.py`/`rules_based.py`。

---

## 8. 與其它研究機會的關係（不要混淆）

canonical 排序 #2 → #5 → #7（皆不觸 `loop.py`、可互穿插）：
1. **#2 pass^k（本評估）**——repeatability 量測。**最直接補 reliability science 缺軸**。
2. **#5 OTel GenAI schema**——把 Cat 12 wrapper 標準化到 CNCF conventions。與 #2 相鄰（同 Cat 12 observability），但 #5 是 telemetry **格式標準化**，#2 是 **eval 指標**；可先 #2 證指標、再 #5 標準化 trace 格式。
3. **#7 tool-desc lint + structured-error reflection**——Cat 2 工具層品質。正交。

**後置擴展（從本 spike 自然長出）**：λ fault-injection（借 `FlakyTransientError`）/ ε perturbation / MAST classifier（可接 57.111 judge benchmark harness）/ persistence-driven 跨租戶 pass^k 數據產線（研究點名的 V2 結構優勢）。

---

## 9. 參考

- `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.7 / §4 主題 6 / §5 #2 / §6（證據強度：pass^k 🟢 / λ-ε 🔴）
- `claudedocs/1-planning/next-phase-candidates.md` §Research-Derived Candidates（#2 = canonical 排序下一個）
- `claudedocs/1-planning/harness-deepening-proposal-20260610.md`（本評估屬其精神延伸）
- grounding（1 Explore agent，2026-06-24）：
  - benchmark 範本：`backend/scripts/benchmark_judge.py:109-349` / `tests/unit/scripts/test_benchmark_judge.py:19-120`
  - trace persistence：`infrastructure/db/models/sessions.py:164-307` / `api/v1/chat/router.py:571-626` / `event_wire_schema.py:66`（wire 26）
  - 驅動：`api/v1/chat/handler.py:280-348` / `orchestrator_loop/loop.py:1942-2026`
  - AP-6 零冗餘：grep `pass^k`/`consistency`/`fault`/`MAST` = backend/src 零；`FlakyTransientError` test-only `test_loop_retry_integration.py:191`
- `04-anti-patterns.md` —— AP-4 / AP-6 / AP-2
- **本評估不預寫 sprint plan**；若決定開 spike，依 `.claude/rules/sprint-workflow.md` 標準流程（plan → checklist → Day-0 三-prong → code → drive-through）。
