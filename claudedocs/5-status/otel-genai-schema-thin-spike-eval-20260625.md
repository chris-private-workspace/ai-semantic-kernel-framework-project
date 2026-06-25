# Thin-Spike 評估：Cat 12 標準化在 OTel GenAI semantic conventions（研究機會 #5）

**Purpose**: 評估「把 V2 Cat 12 的 span/attribute schema 對齊 CNCF OpenTelemetry GenAI semantic conventions」的可行性、最小可行形狀、`不觸 loop.py` 的設計路徑、量測（conformance）機制、冗餘風險與成本。**這是評估，不是實作 sprint**；產出供決策，不預寫 sprint plan（rolling discipline）。
**Category / Scope**: 範疇 12 (Observability)；schema-conformance translation layer（非 full vertical slice；非 A/B benchmark）
**Created**: 2026-06-25
**Last Modified**: 2026-06-25
**Status**: Active（評估快照；非 sprint）
**Grounding**: 1 個 read-only Explore agent 對 `backend/src/agent_harness/observability` + `loop.py` + `requirements.txt` + `tests` 的 file:line 勘查（2026-06-25）+ 3 處親自 spot-check（`tracer.py:122-240` / `requirements.txt:46-52` / `loop.py:2430-2484`）；研究來源 `ai-agent-harness-consolidated-analysis-20260622.md` §2.7 / §5 #5 / §3 Cat 12

> **Modification History**
> - 2026-06-25: Initial — thin-spike 評估（研究機會 #5 = canonical 排序下一個；#6/#3/#8/#4/#1/#2 已 CLOSED）

---

## 0. 缺口背景（一句話 + 關鍵反轉）

研究機會 #5 的原始框架是：「Cat 12 用**自有 wrapper、非標準 schema**，標準化在 OTel GenAI conventions」（`consolidated-analysis` §5 表 #5：「自有 wrapper,非標準」）。

**但 evidence-first 勘查發現這個前提半錯——這是本評估最重要的發現**：

| 研究假設 | 程式碼實況（file:line） | 結論 |
|---------|------------------------|------|
| 「自有 wrapper」（暗示無真 OTel）| `requirements.txt:46-52` 已 pin **真 OTel SDK**：`opentelemetry-api/sdk/exporter-otlp==1.22.0` + Prometheus reader + FastAPI/SQLAlchemy/Redis instrumentation | OTel SDK、OTLP exporter（Jaeger :4317）、Prometheus、span tree **全部已線上且真實** |
| 「非標準 schema」 | span 名（`agent_loop.llm_call`...）+ attribute key（`span_type`/`model`/`prompt_tokens`...）是 **bespoke**，非 `gen_ai.*` | ✅ 這部分**正確** —— **真正的 gap 只是 schema 命名** |

**所以 #5 不是「採用 OTel」，而是「把已在飛的 OTel span 的 key/name 從 bespoke 翻譯成 CNCF `gen_ai.*` 慣例」**——一個 **schema-conformance 翻譯層**，範圍遠小於 AD 字面。這與 57.125→126、57.134 的 Day-0「foundation 比 AD 假設更完整」同類發現。

研究背書：OTel GenAI semantic conventions（CNCF SIG since 2024-04，`consolidated-analysis` §6 列為 🟢 landmark/已 spot-check）天然對齊**約束 3（provider-neutrality）** + **multi-tenant PII/GDPR**（`captureContent` 預設 off）。

---

## 1. 現況（code-grounded，file:line）

### 1.1 Tracer 抽象（已是乾淨 ABC + 真 SDK wrapper）

- **`Tracer` ABC**：`observability/_abc.py:32-54` — `start_span(*, name, category, trace_context, attributes)` / `record_metric(event)` / `get_current_context()`
- **`OTelTracer`（production）**：`tracer.py:122-240` — lazy-import 真 `opentelemetry.trace` / `.metrics`；`_span_cm`（`:151-197`）是 bespoke→OTel 的**單一邊界**：`:162-173` 組 attrs dict → `:178` `otel_tracer.start_as_current_span(name, attributes=attrs)`
- **`NoOpTracer`（test/dev 預設）**：`tracer.py:57-115`
- **`TraceContext`**：`_contracts/observability.py:59-75`（trace_id/span_id/parent/tenant/user/session/baggage）
- **`SpanCategory` enum**：`_contracts/observability.py:41-56`（13 值 = 11 範疇 + OBSERVABILITY + HITL）
- **`category_span` helper**：`observability/helpers.py:42-80`（None-tracer no-op；verification/business 用它免重複 boilerplate）
- **真 exporter**：`observability/exporter.py:47-91`（OTLP/gRPC → Jaeger + Prometheus reader）

### 1.2 現有 span（loop 是唯一 trace-tree owner；executor/parser/verifier tracer 在 production 為 NoOp）

| span 名（bespoke）| 來源 | attributes（bespoke key）|
|------------------|------|--------------------------|
| `agent_loop.run` | `loop.py:2007` | `span_type=LOOP` |
| `agent_loop.turn` | `loop.py:2277` | `span_type=TURN`, `turn` |
| `agent_loop.llm_call` | `loop.py:2434` | `span_type=LLM_CALL`, `model`, +post-response `prompt_tokens`/`completion_tokens`/`cached_input_tokens`/`total_tokens` |
| `agent_loop.prompt_build` | `loop.py:2335` | `span_type=PROMPT_BUILD` |
| `agent_loop.compaction` | `loop.py:2222` | `span_type=COMPACTION` |
| `agent_loop.tool.{name}` | `loop.py:2930` | `span_type=TOOL_EXEC`, `tool` |
| （tracer 自動加）| `tracer.py:162-171` | `category`, `trace_id_neutral`, `tenant_id`, `user_id`, `session_id` |

### 1.3 兩個關鍵 code 事實（決定設計）

**(A) 翻譯點乾淨 = `不觸 loop.py` 可行**
所有 span 都經 `OTelTracer._span_cm`（`tracer.py:162-178`）這個**單一邊界**進真 OTel SDK。在此（或一個被它呼叫的 `_genai_semconv.py` 映射模組）做 bespoke→`gen_ai.*` 映射，可標準化 loop 發出的**所有** span 的 key + name，**零 loop.py 編輯**。`record_metric` labels（`tracer.py:216`）同理。

**(B) 發現一個 latent bug：post-response token attrs 在真 OTel 匯出時遺失**
`loop.py:2430` 建 `llm_attrs` dict 傳給 `start_span`，`tracer.py:173` **複製**成自己的 `attrs` 再 `:178` 在 span 起點 snapshot 進 OTel span。但 `loop.py:2470-2476` 在 span 開始**之後**才 mutate `llm_attrs`（post-response token）。結果：
- loop.py 改的是 `llm_attrs`，tracer snapshot 的是 `attrs`（不同 dict）；
- 即使同 dict，OTel `start_as_current_span(attributes=...)` 在起點即定值，後續 mutate 不傳播。
- **→ 真 `OTelTracer` 匯出的 span 永遠拿不到 token 數**；只有 by-reference 的測試 `RecordingTracer` 看得到（所以 `test_observability_coverage.py` 綠，但 production Jaeger trace 缺 token）。

這給了**順手修法**：tracer 持有 caller 的 `attributes` 原始 reference，在 span **關閉時**（`_span_cm` 的 `finally`）對 OTel span 做 `set_attributes(translate(attributes_current))` —— 因 loop.py 在 span 關閉前已 mutate 完 `llm_attrs`，close-time 讀取即拿到 token，**仍零 loop.py 編輯**，且順手把上述 bug 修掉。

### 1.4 finish_reason / stop_reason 連結（研究高亮點，目前不在 span）

- `StopReason` enum：`_contracts/chat.py:41-49`（END_TURN / TOOL_USE / MAX_TOKENS / STOP_SEQUENCE / SAFETY_REFUSAL / PROVIDER_ERROR）
- 目前 stop_reason **只在 `LLMResponded`/`LoopCompleted` event，不在 span attribute**。研究指 `gen_ai.response.finish_reasons` 的 `tool_calls` vs `stop` 與 while-true loop stop_reason **1:1**（`consolidated-analysis` §2.7）—— 這是高價值映射，但 stop_reason 是 post-response，需 loop.py 在 `llm_attrs` 寫一行才進得了 close-time 翻譯（見 §4 決策 B）。

### 1.5 content capture / PII

- **目前完全不擷取** prompt/response 內容進 span（grep 無 `content=`/`prompt=` 於 tracer）——safe by omission。
- 研究要 `captureContent` opt-in **預設 off**（PII/GDPR）。V2 現況已是「預設 off（根本沒有）」→ 這是**純追加/可選**項，非「移除不安全擷取」。

### 1.6 17.md 契約

`17-cross-category-interfaces.md:150` 已 pin `Tracer` ABC（`start_span`/`record_metric`）為 single-source。schema 是 ABC 的**值**，非 ABC 的**形狀** → 翻譯層不改 ABC 簽章 → **不需動 17.md 契約**。

---

## 2. CNCF OTel GenAI conventions 目標 schema（映射表）

> 注意：規範仍在演進（2025 有 `gen_ai.system` → `gen_ai.provider.name` rename；`prompt_tokens` → `input_tokens`）。spike 應 **pin 一個版本/日期** 作 conformance 目標並記於 design note。

| V2 bespoke | CNCF `gen_ai.*` 目標 | 註 |
|-----------|---------------------|----|
| span 名 `agent_loop.run` | `invoke_agent {name}`（op=`invoke_agent`）| agent 生命週期 |
| span 名 `agent_loop.llm_call` | `chat {model}`（op=`chat`）| LLM roundtrip |
| span 名 `agent_loop.tool.{name}` | `execute_tool {name}`（op=`execute_tool`）| 工具執行 |
| `span_type` | `gen_ai.operation.name`（`chat`/`invoke_agent`/`execute_tool`）+ keep `span_type` 作內部 | turn/prompt_build/compaction 無對應 op → 保 bespoke 或用 `gen_ai.operation.name` 擴充值 |
| `model` | `gen_ai.request.model` / `gen_ai.response.model` | |
| `prompt_tokens` | `gen_ai.usage.input_tokens` | 需 close-time 翻譯（§1.3 B）|
| `completion_tokens` | `gen_ai.usage.output_tokens` | 同上 |
| `total_tokens` | （規範無單一 key；可保 bespoke 或省）| |
| `cached_input_tokens` | cache token 規範**較不穩定** | 標註 hedge；可暫保 bespoke |
| `tool` | `gen_ai.tool.name`（+ `gen_ai.tool.call.id` 若有）| |
| （新增）| `gen_ai.provider.name`（如 `azure.ai.openai`）| 目前 provider 未進 loop span，需 adapter→tracer 來源 |
| （新增）| `gen_ai.response.finish_reasons`（array）| 見 §4 決策 B；stop_reason 1:1 |
| `tenant_id`/`user_id`/`session_id` | 保 bespoke（非 GenAI 範圍，企業治理需要）| 不動 |

---

## 3. Conformance 量測機制（= 本 spike 的「drive-through」）

OTel 標準化**沒有 A/B「哪個數字好」**，而是 **conformance（合規）**：「V2 匯出的 GenAI span 是否符合 CNCF schema」。誠實的 drive-through = **用真 OTel SDK 匯出 span 再檢查 key**：

- OTel SDK 提供 `InMemorySpanExporter`（`opentelemetry.sdk.trace.export.in_memory_span_exporter`）—— 真 SDK、捕獲 span、斷言 `gen_ai.*` key + span 名 + finish_reasons。
- 形狀：`scripts/benchmark_otel_conformance.py`（鏡像 5 個既有 `benchmark_*.py` pattern；但**非 A/B**，是 conformance checklist：N 個必備 `gen_ai.*` key 中通過 M 個 = conformance ratio）。
- 與 #135/#137/#138 同「**CATCH = harness 本身 / 真 SDK 即 drive-through**」pattern（pure-infra item，無 UI）。
- verdict 範例：「6/6 span 名對齊 op-prefix；input/output_tokens 在真匯出 span 出現（修掉 §1.3 B bug）；finish_reasons 出現（若採決策 B）」。

CI 測試另以既有 `test_observability_coverage.py` 的 `RecordingTracer` pattern + 新 `assert_genai_conformant(span)` 檢查器斷言映射正確（offline，無 Azure）。

---

## 4. 待決策（將以 AskUserQuestion 確認）

### 決策 A — 翻譯位置（基本由「不觸 loop.py」+ evidence 鎖定）
- **(建議) translation-at-tracer**：`_genai_semconv.py` 映射 + 在 `OTelTracer._span_cm` start+close 套用。loop.py 續發 bespoke key（內部/測試視圖不變），**匯出**視圖為 `gen_ai.*`。零 loop.py 編輯 + 順手修 §1.3 B token bug。
- (否決) emit-gen_ai-at-source：在 loop.py 直接改 key 名 → 違反「不觸 loop.py」+ 散落多點。

### 決策 B — `不觸 loop.py` 的嚴格度（**真正的 open 決策**）
高價值的 `gen_ai.usage.*`（token）與 `gen_ai.response.finish_reasons` 都是 **post-response**：
- **B1 嚴格零 loop.py**：tracer close-time 翻譯，自動帶出 token（loop.py 已寫 `llm_attrs` token）→ `gen_ai.usage.input/output_tokens` 匯出。**finish_reasons 延後**（需 loop.py 寫一行 stop_reason 進 `llm_attrs`，本選項不做）。
- **B2 容許 1 行 loop.py**：B1 + 在 `loop.py:2476` 後加 `llm_attrs["finish_reason"]=response.stop_reason.value` → close-time 翻譯成 `gen_ai.response.finish_reasons`。研究高亮的 1:1 stop_reason 映射 = 高價值；代價 = 破「零 loop.py」但僅 1 行 surgical。

### 決策 C — content capture opt-in flag（PII）
- **C1（建議）延後**：YAGNI；V2 已「預設 off（根本沒有）」；登 follow-on `AD-Observability-Content-Capture-OptIn-Phase58`。
- C2 納入：設計 `OTEL_*_CAPTURE_MESSAGE_CONTENT`-style 預設 off flag + 截斷/雜湊（不存全文）。增 scope。

### 決策 D — 規範版本錨定
spike 必 pin 一個 CNCF GenAI semconv 版本/快照日期作 conformance 目標（規範演進中）→ 記 design note；用 stable 子集（op name + request/response.model + usage.input/output_tokens + finish_reasons + tool.name）避開未穩定 key（cache token）。

---

## 5. 冗餘 / 反模式風險

| 風險 | 評估 |
|------|------|
| **AP-6 為未來預留抽象** | 翻譯層有**當前真實使用案例**（外部 OTel/APM 互通 + CNCF 互操作）→ 非投機。但 content-capture flag（決策 C2）若無當前消費者 = AP-6 風險 → 傾向延後（C1）|
| **AP-4 Potemkin** | conformance harness + 真 SDK InMemoryExporter 斷言 = 有實質量測，非空殼 |
| **AP-3 散落** | 映射集中 `_genai_semconv.py` + 套於單一 tracer 邊界 → 不散落 |
| **約束 3 中性** | `gen_ai.*` 本身就是 provider-neutral schema；映射不引入 native import → 強化中性 |
| **雙視圖（內部 bespoke / 匯出 gen_ai）混淆** | 需 design note 明記「loop.py + 測試用 bespoke、匯出用 gen_ai」雙視圖契約，避免後人困惑 |

---

## 6. 最小可行形狀（pending 決策）

```
backend/src/agent_harness/observability/_genai_semconv.py   # NEW — bespoke→gen_ai 映射表 + span-name remap + 純函式
backend/src/agent_harness/observability/tracer.py           # EDIT — OTelTracer._span_cm start+close 套映射（決策 A/B1）
backend/scripts/benchmark_otel_conformance.py               # NEW — 真 InMemorySpanExporter conformance harness
backend/tests/fixtures/observability/otel_conformance_cases.yaml  # NEW — 必備 gen_ai.* key checklist
backend/tests/unit/.../test_genai_semconv.py               # NEW — 映射純函式 + assert_genai_conformant 斷言
（決策 B2 才動）backend/src/agent_harness/orchestrator_loop/loop.py  # EDIT — 1 行 finish_reason 寫入
```

- 範疇：Cat 12（純）。NO migration / NO wire event / NO frontend / NO 17.md 契約變更。
- 預估形狀：~4-6 NEW/EDIT 檔；計算量輕（映射 + conformance 斷言）；無 DB；real-SDK drive-through 不需 backend server（standalone script，如其他 benchmark_*.py）。

---

## 7. 與其他機會的關係

- **獨立於 loop.py**（§4.4 proposal）—— 可與 #2/#7 互換順序；canonical 排序 #5 在 #2 後、#7 前。
- **與 #2 pass^k 互補**：#2 量「跨重複 run 可靠性」；#5 標準化「單次 run 的 telemetry schema」→ 兩者皆 Cat 12 但正交。
- **finish_reasons 1:1 stop_reason** 是研究跨 #5/#11(subagent handoff) 的共用洞見。

---

## 8. References

- `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.7 Cat 12 / §5 #5 / §3 / §6（OTel GenAI 🟢）+ §295 OTel blog link
- `backend/src/agent_harness/observability/{_abc.py,tracer.py,exporter.py,helpers.py}` + `_contracts/observability.py`
- `backend/src/agent_harness/orchestrator_loop/loop.py:2007,2222,2277,2335,2430-2484,2930`
- `backend/requirements.txt:46-52`（真 OTel SDK pin）
- `backend/tests/integration/orchestrator_loop/test_observability_coverage.py`（RecordingTracer pattern）
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md:150`（Tracer 契約）
- `docs/rules-on-demand/observability-instrumentation.md`（Cat 12 埋點規則 + version-pin AD）
- 前例 benchmark harness：`benchmark_judge.py`（57.111）/ `benchmark_sandbox_escape.py`（57.137）
