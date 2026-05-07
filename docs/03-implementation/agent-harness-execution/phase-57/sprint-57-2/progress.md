# Sprint 57.2 Progress

> [Sprint 57.2 Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-2-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-2-checklist.md)
> **Branch**: `feature/sprint-57-2-audit-cycle-carryover` (from main `96716a1a`)

---

## Day 0 — 2026-05-07：探勘 + 三-prong plan-vs-repo verify

### 0.1 Branch + Baselines ✅

| Check | Result |
|-------|--------|
| Branch create | ✅ `feature/sprint-57-2-audit-cycle-carryover` from `96716a1a` |
| pytest collected | ✅ 1561 (= 1557 pass + 4 skip) — matches baseline |
| mypy --strict | ✅ 0 errors / 293 source files |
| 8 V2 lints | ✅ 8/8 green (1.98s) |
| LLM SDK leak | ✅ 0 in agent_harness/ + business_domain/ (2 in adapters/azure_openai/ — allowed) |

### 0.2 三-prong plan-vs-repo verify — 11 D-findings catalogued

#### Prong 1 — Path Verify

| ID | Plan claim | Reality | Severity |
|----|-----------|---------|----------|
| **D1** | `backend/src/business_domain/cost_ledger/service.py` exists (56.3 introduced) | ❌ **不存在**;真實位置 `backend/src/platform_layer/billing/cost_ledger.py` + `infrastructure/db/models/cost_ledger.py` | 🟠 Yellow — path drift, scope unchanged |
| **D2** | `backend/src/business_domain/cost_ledger/pricing_loader.py` exists | ❌ **不存在**;真實 `backend/src/platform_layer/billing/pricing.py` | 🟠 Yellow — path drift |
| **D3a** | 4 detectors flat in `agent_harness/guardrails/` | ❌ 真實位置:`guardrails/input/` (pii + jailbreak)、`guardrails/output/` (sensitive_info + toxicity)、`guardrails/tool/` (tool_guardrail) — **3 subfolders** plan 沒提 | 🟠 Yellow — path drift + extra `tool/` folder |
| **D3b** | Detector naming: `secrets_leak_detector` + `role_confusion_detector` | ❌ 真實命名:`sensitive_info_detector` + `toxicity_detector` (output 類)+ `tool_guardrail` (tool 類) | 🟠 Yellow — naming drift |
| **D4** | `backend/src/platform_layer/observability/sla_metric_recorder.py` | ❌ 真實 `sla_monitor.py`;class 名應該也是 SLAMonitor 非 SLAMetricRecorder | 🟠 Yellow — naming drift |
| ✓ | `backend/src/api/v1/chat/router.py` exists | ✅ confirmed L361-365 |
| ✓ | `backend/src/agent_harness/_contracts/events.py` exists | ✅ confirmed |
| ✓ | `backend/src/agent_harness/orchestrator_loop/loop.py` exists | ✅ confirmed |
| ✓ | `agent_harness/orchestrator_loop/_metrics.py` NOT exist (NEW) | ✅ confirmed 0 results |
| ✓ | `.github/workflows/deploy-production.yml` exists | ✅ confirmed |

#### Prong 2 — Content Verify

| ID | Plan claim | Reality | Severity |
|----|-----------|---------|----------|
| **D5** | guardrails/ Stage 0 advisory only | ❌ **不正確** — `tool/tool_guardrail.py` since Sprint 53.3 已實作 **3-stage approval (Stages 1+2 wired)**;Stage 2.3 max calls 自 55.4 close AD-Cat9-5;ToolGuardrail.check() 已有 RBAC + tenant scope + session counter active blocking | 🔴 Red — 實作模型完全不同於 plan 假設 |
| **D6** | record_llm_call() uses default `azure_openai/gpt-5.4` constants | ❌ 不正確 — `record_llm_call()` signature L97-L104 已 require `provider: str` + `model: str` 為 required parameter (非 default constant) | 🟠 Yellow — provider/model API correct, default 在呼叫端 |
| **D7** | chat router observer should pass real ChatResponse provider/model | ✅ 確認 router.py L363-364 hardcoded `provider="azure_openai"` + `model="gpt-5.4"` — AD-Cost-Ledger-Provider-Attribution 真有效 scope | 🟢 Green — confirms US-1 valid scope |
| **D8** | SLAMonitor.classify_loop_complexity() 用 last-event proxy | ✅ 確認 `sla_monitor.py` L92-L94 explicit comment 「per-loop tool_calls and subagent counts not visible in LoopCompleted today...counter accumulator event deferred to Phase 56.x」— AD-Cat10-Cat11-LoopMetricsAccumulator 真有效 scope | 🟢 Green — confirms US-2 valid scope |
| **D9** | US-3 scope = "Stage 0 advisory → Stage 1 active gate" | ❌ **不正確** — `loop.py` L207 + L421-422 + L478-479 + L698-699 already wires `guardrail_engine.check_input/check_output/check_tool_call`;Stage 1 active gate engine + loop side **already done**(53.3+55.4 期間) | 🔴 Red — US-3 plan 對於 Stage 0 → 1 描述完全錯誤;真實缺口在 chat router 不 instantiate engine |
| **D10** | chat router does NOT instantiate GuardrailEngine / register detectors | ✅ 確認 router.py 0 references to GuardrailEngine — AD-Cat9-1-WireDetectors 真實 scope = **factory + DI wiring**(不是 Stage 0 → 1 升級) | 🟢 Green — confirms US-3 真實 scope |

#### Prong 3 — Schema Verify (AD-Plan-4-Schema-Grep — folded Sprint 57.1)

| ID | Plan claim | Reality | Severity |
|----|-----------|---------|----------|
| **D11** | cost_ledger ORM has `total_tokens` column;新增 input_tokens / output_tokens 欄位需 Migration 0017 | ❌ **不正確** — cost_ledger ORM 是 **generic ledger** schema:`cost_type / sub_type / quantity / unit / unit_cost_usd / total_cost_usd / session_id / recorded_at`(NO 任何 token-named column);provider/model/granularity 編碼於 `sub_type: String(128)` (e.g. `"azure_openai_gpt-5.4_total"`) → AD-Cost-Ledger-Token-Split 真實 fix = 改寫 sub_type 編碼 (`_input` / `_output` 兩 entry),**NO migration needed** | 🔴 Red — US-1 schema 假設完全錯誤;Migration 0017 NOT NEEDED |
| ✓ | Migration head 0016 latest | ✅ confirmed `0016_sla_and_cost_ledger.py` is latest;0017 not yet occupied (但 D11 不需要 0017) |
| ✓ | RLS policy on cost_ledger | ✅ TenantScopedMixin (per ORM L71) + RLS policy (per 0016 migration) — backwards-compat retained |

---

### 0.3 Drift Impact Assessment + Decision

#### Per-US scope re-shape

| US | Original plan scope | Real scope (post-Day-0 探勘) | Effort delta |
|----|---------------------|------------------------------|--------------|
| **US-1 Cost Ledger 精度** | Migration 0017 + service.py signature change + chat router fix(~6 hr) | **NO migration**;sub_type encoding split + chat router real ChatResponse read(~3 hr) | **~50% reduction** |
| **US-2 LoopMetricsAccumulator** | 新增 _metrics.py + AgentLoop integration + LoopCompleted payload(~6 hr) | confirmed scope unchanged + class name correction `SLAMetricRecorder` → `SLAMonitor`(~6 hr) | unchanged |
| **US-3 Cat 9 Stage 1 wiring** | 改 Stage 0 → Stage 1 + 加 GuardrailTriggered SSE event(~6 hr) | engine + loop already 完成;chat router 加 `build_default_guardrail_engine()` factory + DI wiring + 4 detector registration(~3-4 hr) | **~40% reduction** |
| **US-4 deploy-production.yml** | trigger 改 + 5-point criteria verify(~3 hr) | confirmed scope unchanged | unchanged |
| **US-5 alignment audit + closeout** | light-touch grep + closeout(~3 hr) | confirmed scope unchanged | unchanged |
| **Total** | ~24 hr bottom-up | **~18-20 hr bottom-up** | **~17-25% reduction** |

#### Net scope shift

- 5 path drifts (D1/D2/D3a/D3b/D4): file/class 命名差 — 影響 plan §File Change List 文字,不影響 scope
- 3 content drifts (D5/D9/D10): US-3 mental model 完全錯誤 — Stage 1 active gate 已存在;真實缺口是 chat router DI
- 1 schema drift (D11): US-1 mental model 錯誤 — generic ledger 不需 migration;encoding 改 sub_type 即可
- Net: **~20-25% scope reduction**(都是減少,不是增加)
- Calibration multiplier 0.55 重新算:**18-20 hr × 0.55 = ~10-11 hr commit**(原 plan 14-17 hr → 修正 ~10-11 hr)

#### Per AD-Plan-1 sprint-workflow.md 决策規則

> Findings shift scope by 20-50% → revise plan §Acceptance Criteria + §Workload + **re-confirm with user**

**This is 20-25% scope reduction → 觸發 user re-confirm。**

#### 三-prong ROI evidence (本 Day 0 第 4 次 AD-Plan-3 application)

- **Prong 1 alone(path verify)** 只 catch D1/D2/D3a/D3b/D4 = 5 path drifts — 都是 cosmetic naming/path,scope 影響低
- **Prong 2(content verify, AD-Plan-3 promoted Sprint 55.6)** catch D5/D6/D7/D8/D9/D10 = 6 critical content drifts — D5+D9+D10 直接挑戰 US-3 整個 mental model;若 Prong 2 沒做,Day 1 寫 ~3 hr 才會發現 Stage 1 已存在,whole-day rework
- **Prong 3(schema verify, AD-Plan-4 folded Sprint 57.1)** catch D11 = 1 schema drift — 直接挑戰 US-1 整個 mental model;若 Prong 3 沒做,Day 1 寫 Migration 0017 才會 Alembic generate 後發現 schema 不需要 migration,~2 hr rework
- **本次 ROI 估算**: Day 0 ~3 hr cost 防 Day 1+ ~5-7 hr rework = **~2-2.5× ROI** (本次數字較低因為 drift 多為 reduction;但避免「做了才發現不需要」的盲走才是核心價值)

---

## Decision: PAUSE for user re-confirm 🟡

**Day 0 完成 — 11 D-findings catalogued。Net 20-25% scope reduction。**

### 建議 plan §Workload 修正

- Bottom-up est ~18-20 hr (原 ~25-30 hr)
- Calibrated commit `large multi-domain` 0.55 → **~10-11 hr** (原 ~14-17 hr)

### 建議 plan §US 修正

1. **US-1**:刪 Migration 0017 task;改 `record_llm_call()` 寫 2 entries (input + output sub_type) 取代 1 entry total;chat router 讀真實 event.provider/model
2. **US-2**:class 名修正 `SLAMetricRecorder` → `SLAMonitor`(其餘 scope 不變)
3. **US-3**:scope 改寫 — 新增 `build_default_guardrail_engine()` factory + chat router DI wire (取代「Stage 0 → 1 升級」mental model);engine + loop 已有的 check_input/check_output/check_tool_call 不動
4. US-4 / US-5:不變

### 建議 sprint plan §Acceptance Criteria 修正

- Cost Ledger entries 顯示 `sub_type` 含 `_input` / `_output` (取代 `_total`) + provider 真實值
- Loop pre-input + pre-tool + post-output 各有對應 detector check (透過 chat router 預設 register 4 個 detector)
- pytest baseline 1557 → **≥ 1564**(+7 minimum;原 +10 → 修正 +7 因為 US-1 + US-3 各少 1-2 個 test)

### Options for user

**Option A**: Approve revised plan(20-25% scope reduction);Day 1 啟動執行 ~10-11 hr commit
**Option B**: Continue with original plan but mentally adjust(higher risk — actual code 會 deviate from plan §File Change List)
**Option C**: Abort + redraft plan with reality-aligned text(~30 min rework cost;cleaner audit trail)

**建議 Option A** — drift 都是 reduction、scope 簡化、不影響整體 acceptance criteria 達成、calibration ratio 估算用修正版 ~10-11 hr commit。

⏸ **等待 user decision 才啟動 Day 1**。

---

## Day 0 後續 — Option A approved → Day 1 啟動前 deeper discovery（D12+D13）

User 2026-05-07 approve Option A 後,啟動 Day 1 前 read events.py 確認 record_llm_call() 改動範圍,catch 2 個額外 critical findings:

| ID | Finding | Implication |
|----|---------|-------------|
| **D12** | LoopCompleted 只有 `total_tokens` (combined) — NO `input_tokens` / `output_tokens` / `provider` / `model` 欄位 | US-1 無法只改 chat router observer + cost_ledger service;**必須先 add 4 fields to LoopCompleted event** + 由 AgentLoop emit 真實值 |
| **D13** | LLMResponded event(L87)只有 `content / tool_calls / thinking` — NO token usage / provider / model;LLMRequested(L75)有 `model + tokens_in` 但只 pre-call estimate | per-call ChatResponse usage 沒有寫入 event;**必須**(a)由 Adapter 層 azure_openai/adapter.py 在 LLMResponded 加 provider/model/input_tokens/output_tokens 欄位 + populate 真實值,或(b)在 ChatClient ABC ChatResponse 既有 metadata 由 AgentLoop 直接累加到 accumulator(不經 event) |

### US-1 + US-2 真實 coupling discovered

原 plan 將 US-1(Cost Ledger 精度)+ US-2(LoopMetricsAccumulator)當作獨立 USs。Day 1 探勘揭露:

- US-1 record_llm_call() 要拿 input/output 真實 split + provider/model **必須**從 LoopCompleted event 來
- LoopCompleted 目前 emit at AgentLoop run() 結尾;欄位由 AgentLoop 直接 set
- 加新欄位需要 AgentLoop 累加 per-call 數據 → **這就是 US-2 LoopMetricsAccumulator scope**!

**真實 scope structure**(Day 1 啟動 strategy):
1. **Day 1 上午**:add `input_tokens / output_tokens / provider / model` fields to LoopCompleted event(events.py)+ LoopMetricsAccumulator class(_metrics.py)
2. **Day 1 下午 — Day 2 上午**:AgentLoop 注入 accumulator + 每個 LLM call 由 ChatResponse 抽 usage + provider + model 累加;LoopCompleted emit 時 populate 4 個新欄位
3. **Day 2 下午**:cost_ledger.record_llm_call() signature 改 `total_tokens` → `input_tokens + output_tokens`;寫 2 entries(input + output sub_type);chat router observer 讀新欄位
4. **Day 3**:US-3 chat router GuardrailEngine factory + DI(per Day 0 D9+D10 — engine + loop already done,只缺 router instantiate)
5. **Day 4**:US-4 deploy-production.yml + US-5 alignment audit + closeout

### Revised scope estimate

| US | 修正 bottom-up | 修正 calibrated(× 0.55) |
|----|----------------|--------------------------|
| US-1 + US-2 bundled(events + accumulator + cost_ledger fix + adapter)| ~12 hr | ~6.6 hr |
| US-3(chat router DI)| ~3 hr | ~1.7 hr |
| US-4 + US-5 | ~6 hr | ~3.3 hr |
| Day 0 已執行 | ~3 hr | ~1.7 hr |
| **Total** | **~24 hr** | **~13.3 hr** |

→ 修正後 commit ~13 hr — **基本回到原 plan 14-17 hr commit 區間**。Day 0 早期估算 10-11 hr 沒考慮 events.py + adapter coupling;真實 scope ≈ 原 plan。

**Day 1 啟動 — 不再 PAUSE**(user 已 Option A approve;coupling 是 implementation detail not scope shift)。

---

## Day 1 — 2026-05-07：US-1 + US-2 bundled execution — events + accumulator foundation ✅

### Completed

| Task | Status |
|------|--------|
| events.py LLMResponded 加 4 fields(provider/model/input_tokens/output_tokens)| ✅ |
| events.py LoopCompleted 加 4 fields(input_tokens/output_tokens/provider/model)| ✅ |
| `_metrics.py` LoopMetricsAccumulator class created | ✅ |
| LoopMetricsAccumulator.on_event() handles LLMResponded / VerificationPassed/Failed / SubagentSpawned | ✅ |
| LoopMetricsAccumulator.to_loop_completed_payload() returns 6-field dict | ✅ |
| mypy --strict events.py + _metrics.py | ✅ 0 errors |
| pytest collect 1561(unchanged baseline)| ✅ no regression |

### D-finding catalogued Day 1

| ID | Finding | Action taken |
|----|---------|--------------|
| **D14** | event naming drift:plan asserted `VerificationCompleted` + `SubagentDispatched` but真實 names `VerificationPassed` + `VerificationFailed` + `SubagentSpawned` | _metrics.py imports + on_event() updated to real names;both Pass/Fail count as iterations |

### Day 1 Calibration

- Plan committed Day 1: ~3.3 hr(US-1 portion)
- Actual Day 1: ~2.5 hr(events + accumulator + 1 mypy fix dict[str, int|str])
- Day 1 ratio:**0.76**(slightly under;rest of US-1 + US-2 pulled into Day 2-3)

### Day 2 plan(明日)

1. AgentLoop integration — 14 LoopCompleted emit points populate from accumulator(可能 refactor 為 single emit helper)
2. Adapter layer — `adapters/azure_openai/adapter.py` populate LLMResponded fields with ChatResponse.usage + provider + model
3. mypy + pytest checkpoint

### Day 3 plan

1. cost_ledger.record_llm_call() signature change(`total_tokens` → `input_tokens` + `output_tokens`)+ 寫 2 entries(input/output sub_type)
2. chat router observer L361-365 改讀新欄位
3. 5 unit + 1 integration test for US-1+US-2 bundle

### Files changed Day 1

- `backend/src/agent_harness/_contracts/events.py`(MODIFY:+8 fields total LLMResponded + LoopCompleted)
- `backend/src/agent_harness/orchestrator_loop/_metrics.py`(NEW:103 lines)

⏸ **Day 1 closeout — commit Day 1 work to feature branch**。Day 2 next session 啟動。

---

## Day 2 — 2026-05-07：AgentLoop integration + adapter check ✅

### Completed

| Task | Status |
|------|--------|
| `loop.py` 加 `from ._metrics import LoopMetricsAccumulator` import | ✅ |
| `loop.py` `run()` L772 注入 `metrics_acc = LoopMetricsAccumulator()`(per-run local var) | ✅ |
| `loop.py` LLMResponded yield(L956)加 4 fields(provider/model/input_tokens/output_tokens)+ accumulator update | ✅ |
| `loop.py` END_TURN LoopCompleted 2 emit sites(L996+L1008)populate from accumulator | ✅ |
| Adapter check — AzureOpenAIAdapter L440-442 already populates `prompt_tokens` + `completion_tokens` | ✅ **D15: no change needed** |
| mypy --strict on loop.py + _metrics.py + events.py | ✅ 0 errors / 3 source files |
| pytest agent_harness unit suite | ✅ 862 passed / 1 skipped(no regression)|
| pytest collect baseline | ✅ 1561(unchanged)|

### D-finding catalogued Day 2

| ID | Finding | Action |
|----|---------|--------|
| **D15** | `adapters/azure_openai/adapter.py` L440-442 已 populates `TokenUsage(prompt_tokens=..., completion_tokens=...)` from `usage_obj` | NO adapter change needed;Day 2 scope reduced ~1 hr |

### Day 2 Calibration

- Plan committed Day 2: ~3.3 hr(US-2 portion)
- Actual Day 2: ~2 hr(loop.py 4 edits + adapter verification — D15 saves rework)
- Day 2 ratio:**0.61**(under;adapter already correct + LoopCompleted refactor minimal — only END_TURN emits populate, early-termination paths use defaults per docstring)

### Day 2 design decisions

1. **Per-run accumulator**(local var,not `self._accumulator`)— concurrent run() calls 不 share state,符合 Cat 1 isolated-loop principle
2. **End-of-loop populate only**(non-error/cancel/guardrail paths)— 14 LoopCompleted emit points 中只有 2 個(END_TURN)讀取 accumulator;其他 12 個 early-termination paths 保持 defaults(已 documented 於 events.py LoopCompleted docstring)
3. **provider source via `self._chat_client.model_info().provider`** — 不依賴 ChatResponse(它無 provider 欄位);藉 ChatClient ABC 的 model_info() 取得 adapter constant
4. **model source via `response.model`** — per-call 真實值(由 adapter 填寫)

### Day 3 plan(明日)

1. cost_ledger.record_llm_call() signature change:
   - `total_tokens` → `input_tokens: int + output_tokens: int`
   - 寫 2 entries(`{provider}_{model}_input` + `{provider}_{model}_output`)
   - Pricing: `input_tokens × pricing.input_per_million` + `output_tokens × pricing.output_per_million`(取代當前 avg)
   - Cached portion 仍 honor `cached_input_tokens`
2. Chat router L361-365 改:
   - `provider=event.provider`(從 LoopCompleted 真實值)取代 hardcoded `"azure_openai"`
   - `model=event.model` 取代 hardcoded `"gpt-5.4"`
   - `input_tokens=event.input_tokens` + `output_tokens=event.output_tokens` 取代 `total_tokens=event.total_tokens`
3. 5 unit tests + 1 integration test for US-1+US-2 bundle

### Files changed Day 2

- `backend/src/agent_harness/orchestrator_loop/loop.py`(MODIFY:+22 lines / -3 lines = imports + accumulator init + LLMResponded fields + 2 END_TURN emit population)

### 累積 calibration tracking

| Day | Bottom-up | Calibrated | Actual | Ratio |
|-----|-----------|------------|--------|-------|
| 0 | ~3 hr | ~1.7 hr | ~2 hr | 1.18 |
| 1 | ~6 hr | ~3.3 hr | ~2.5 hr | 0.76 |
| 2 | ~6 hr | ~3.3 hr | ~2 hr | 0.61 |
| 3-4 (remaining) | ~11 hr | ~6.1 hr | TBD | — |
| **Sprint Total est** | **~26 hr** | **~14.3 hr** | TBD | TBD |

⏸ **Day 2 closeout — commit Day 2 work**。Day 3 next session 啟動 cost_ledger fix + tests。




---

## References

- [sprint-57-2-plan.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-2-plan.md)
- [sprint-57-2-checklist.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-2-checklist.md)
- [sprint-workflow.md](../../../../.claude/rules/sprint-workflow.md) §Step 2.5(三-prong verify with Prong 3 Schema Verify folded Sprint 57.1)
- AD-Plan-1 / AD-Plan-2 / AD-Plan-3 / AD-Plan-4-Schema-Grep — process AD chain validating Day 0 ROI
