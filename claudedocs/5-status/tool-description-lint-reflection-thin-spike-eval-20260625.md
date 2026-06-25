# Thin-Spike 評估：Cat 2 tool-description lint + structured-error reflection（研究機會 #7）

**Purpose**: 評估「為 Cat 2 工具層加 (A) tool-description 品質 lint + (B) 工具失敗的 structured-error reflection」的可行性、最小可行形狀、`不觸 loop.py` 的設計路徑、量測機制、冗餘風險與成本。**這是評估，不是實作 sprint**；產出供決策，不預寫 sprint plan（rolling discipline）。
**Category / Scope**: 範疇 2 (Tool Layer)；Half A = 靜態 lint detector + 可選離線量測；Half B = 執行器層 error 分類 + 離線 A/B harness（非 full vertical slice；非觸 loop.py 主路徑）
**Created**: 2026-06-25
**Last Modified**: 2026-06-25
**Status**: Active（評估快照；非 sprint）
**Grounding**: 1 個 read-only Explore agent 對 `backend/src/agent_harness/{tools,skills,subagent,error_handling}` + `loop.py` + `scripts/lint` + `scripts/benchmark_*` 的 file:line 勘查（2026-06-25）+ 3 處親自 spot-check（`executor.py:200-243` / `loop.py:2940-3058` / `_contracts/tools.py:77-149`）；研究來源 `ai-agent-harness-consolidated-analysis-20260622.md` §2.3 / §2.4 / §5 #7 / §3 Cat 2

> **Modification History**
> - 2026-06-25: Initial — thin-spike 評估（研究機會 #7 = canonical 排序**最後一個**；#6/#3/#8/#4/#1/#2/#5 已全 CLOSED）

---

## 0. 缺口背景（一句話 + 兩半的不對稱）

研究機會 #7 在 `consolidated-analysis` §5 表是單一條目「**tool-description lint + structured-error reflection**」（Cat 2），但實際是**兩個正交的半**，形狀、證據強度、風險都不同 —— 本評估最重要的框架是「**不要把兩半當一件事**」：

| 半 | 研究來源 | 證據強度 | 新穎度（vs 現況）| loop.py 依賴 |
|----|---------|---------|-----------------|-------------|
| **A — tool-description lint** | §2.3「用模型改寫 flawed tool description → 後續任務完成時間 ~40% 下降」 | 🟡 **單一 Anthropic 數據點，量級當 anecdotal** | **100% 新**（無任何 description 檢查）| **完全無**（CI lint over spec 檔）|
| **B — structured-error reflection** | §2.4「對 tool error 的 structured reflection（taxonomy: invocation/parameter/wrong-tool/failed-API）BFCL v3:Qwen3-4B 16.25%→20.75%；Repair@5 6.8%→26.4%」 | 🟢 但**部分增益來自 RL training、scope 限 trained-reflection regime** | **~30% 部分存在**（Cat 8 ErrorClass 正交）| **dominant 路徑無；rare 路徑殘留**（見 §1.3）|

**關鍵反轉（與 §2.4 self-correction 警語的關係）**：研究 §2.4 同時說「**intrinsic self-correction（無 external signal）一致失敗、常退化準確率**」（ICLR 2024）。但 Half B **不是** intrinsic self-reflection —— 它餵回的是**工具執行的真實錯誤**（external verifiable signal），正落在「self-correction provably helps 的 regime」（§2.4 的 key-condition 分界線同理）。所以 Half B 方向與 self-correction 警語**不衝突**；唯一該 hedge 的是 BFCL 數字含 RL-training confound，不能假設 prompt-only 拿到同幅度增益 → **這正是要 evidence-first 量測再決定 default 的理由**（與 57.136/137/138/139 同 pattern）。

---

## 1. 現況（code-grounded，file:line）

### 1.1 ToolSpec + 註冊（description 今天零驗證）

- **`ToolSpec`**：`_contracts/tools.py:87-99` — `name / description: str / input_schema / annotations / concurrency_policy / hitl_policy / risk_level / version / tags`。`description` 是裸 `str`，**無任何約束**。
- **`ToolRegistryImpl.register()`**：`tools/registry.py:51-74` — register 時用 `Draft202012Validator.check_schema()`（`:61`）驗 `input_schema` 語法 + 查 name 重複（`:57-64`），但**對 `description` 文字零檢查**（無 non-empty / 無 min-length / 無 param-desc 必填）。
- 結論：Half A 是**乾淨的新增點** —— 在 register 加驗證 **或** 加一個 CI lint 掃 spec 檔，兩者皆無既有衝突。

### 1.2 既有工具 description 品質（混雜，有真實 lint 目標）

11 個 built-in spec（file:line + 品質判讀）：

| 工具 | file:line | description 品質 | param desc? |
|------|-----------|-----------------|-------------|
| `python_sandbox` | `tools/exec_tools.py:32-78` | ✅ 詳盡（含 print() 陷阱 + numpy 說明）| ✅ |
| `write_todos` | `tools/todo_tools.py:62-100` | ✅ 詳盡（plan-first 用法）| ✅ |
| `memory_search` / `memory_write` | `tools/memory_tools.py:122-158` / `160-196` | ✅ 良好 | ✅ |
| `web_search` | `tools/search_tools.py:45-80` | ✅ 良好 | ✅ |
| `request_approval` | `tools/hitl_tools.py:54-89` | ✅ 良好 | ✅ |
| `read_skill` / `run_skill_script` | `skills/tool.py:63-90` / `114-144` | ✅ 良好 | ✅ |
| `task_spawn` | `subagent/tools.py:82-108` | ✅ 良好 | ✅ |
| `echo_tool` | `tools/echo_tool.py:29-52` | ⚠️ 極簡「Test-only built-in」| ✅ |
| `note_tool` | `tools/note_tool.py:44-67` | ⚠️ 極簡「Test-only built-in」| ✅ |

→ 現況**已大致良好**（這降低 Half A 的 ~40% 增益期望；多數 spec 不是 flawed）。但有真實 lint 價值：**強制非空 + min-length + param-level desc 必填**，防止未來新工具退化成 `echo_tool` 那種一句話 stub。Half A 的價值是**護欄（防退化）**而非「修好現有爛 description」—— 誠實框架。

### 1.3 工具失敗路徑（Half B + 「獨立於 loop.py」的決定性勘查）

**(A) Dominant 路徑 = handler 拋例外 → 執行器（Cat 2）已捕捉並結構化**
`ToolExecutorImpl` 在 `executor.py:224-243` `except Exception` → 回 `ToolResult(success=False, error=str(exc), error_class="{module}.{ClassName}")`（`:242` 已保留 FQ 例外類名，Sprint 53.3 US-9）。**這是工具失敗的主路徑，全在 Cat 2。**

**(B) Loop 對 soft-failure 只是「分類 + append」，不重建 content**
`loop.py:3044-3055`：`if not result.success` → 用 `result.error_class` 走 `classify_by_string()`（Cat 8 分類 + terminator），然後**沿用執行器回傳的 `result`** append 成 tool message（53.1 baseline）。LLM 看到的是**執行器建的 `result.content`/`result.error`** → **在執行器層 enrich content + 加 taxonomy 欄位，零 loop.py 編輯即覆蓋主路徑。**

**(C) Rare 路徑 = 執行器自己拋（非 handler）→ loop 自建 content（殘留）**
`loop.py:2968-3030`：只有當 `_tool_executor.execute()` **本身**拋例外（罕見：rate-limit gate / schema 驗證等路徑 raise 而非 return）才進此 branch，在 `:3023-3030` 自建 `content=f"Error: {exc!r}. Please adjust your approach."`（**且未設 error_class**）。這條繞過執行器 enrichment。

**決定性結論（settle「#7 獨立於 loop.py」）**：
- **Half A**：100% 獨立（CI lint 掃 spec 檔，根本不碰 runtime）。
- **Half B dominant 路徑**：✅ 純 Cat 2 可做（執行器 `executor.py:236-243` enrich `content` + 加 `error_taxonomy` 欄位），**零 loop.py 編輯**。
- **Half B rare 路徑**（執行器自身拋）：殘留 —— `loop.py:3023-3030` 自建 content 繞過。**全覆蓋**需 loop.py 那段改成呼叫一個 Cat 2 diagnostic 函式（refactor 非 edit），或**接受 rare 路徑暫不 enrich + 登 Phase 58 follow-on**（建議，見 §4 決策 B）。

### 1.4 既有 error taxonomy（Cat 8，與 Half B 正交，非冗餘）

- `ErrorClass` enum：`error_handling/_abc.py:30-36`（TRANSIENT / LLM_RECOVERABLE / HITL_RECOVERABLE / FATAL）—— 這是**重試決策**用的 4 類。
- retry matrix：`error_handling/retry.py:71-82`（TRANSIENT max3 / LLM_RECOVERABLE max2 / 其餘 max0）。
- Half B 提的 taxonomy（**invocation / parameter / wrong-tool / failed-API** —— 錯誤**來源**分類，給 LLM 看怎麼修）與 Cat 8 的「該不該重試」**正交**：一個 schema-mismatch（parameter 類）在 Cat 8 是 FATAL（不重試），但 Half B 要告訴 LLM「你少了 required field X」讓它**下一輪自己修對**。兩者可共存，**無 AP-6 冗餘**。

### 1.5 既有 lint detector + benchmark harness pattern（兩半的施工模板）

- **Lint detectors**：`scripts/lint/check_*.py`（10 個：AP-1 / promptbuilder / cross-category-import / duplicate-dataclass / **llm_sdk_leak** / sync-callback / sole-mutator / rls-policies / ap4-frontend-placeholder / event-schema-sync）；pattern = `find_violations(root)` walk `rglob("*.py")` → NamedTuple violations → `main(argv)` exit 0/1；pytest 鏡像在 `backend/tests/unit/scripts/lint/test_*.py`（importlib 動態載入測 `find_violations`）。`run_all.py` 列各 detector + `--root` arg。**無任何 description detector** → Half A 直接 mirror `check_llm_sdk_leak.py`。
  - ⚠️ 註：`scripts/lint/run_all.py` 已知 stale（部分 v2 lints 遷 pytest）—— spike 須先核對當前 wiring（CLAUDE.md 已知問題）。
- **Benchmark harness**：`backend/scripts/benchmark_{judge,sandbox_escape,pass_k,otel_conformance,key_condition,correction_hygiene,layered_compaction}.py`；共同形狀 = YAML corpus（`tests/fixtures/`）+ `load_cases` + runner + `build_report`（純函式 metrics）+ `main(--real)` Azure/Docker flag + `@pytest.mark.benchmark` + env-gated 真跑。→ Half B 的 A/B 量測直接 mirror（最近例：`benchmark_correction_hygiene.py` 57.136 量 self-conditioning，與 Half B 同家族）。

---

## 2. 目標形狀（pending 決策）

### Half A — tool-description lint
一個 `check_tool_descriptions.py` detector，掃 `agent_harness/{tools,skills,subagent}` 的 `ToolSpec(...)` literal，斷言：
1. `description` 非空 + ≥ N 字元（防 `echo_tool` 式 stub；test-only 工具可 allow-list 豁免）
2. `input_schema` 每個 property 有 `description`（param-level 必填）
3. （可選）description 不含 placeholder（`TODO` / `FIXME` / `...`）

### Half B — structured-error reflection（Cat 2 執行器層）
1. 一個純函式 `classify_tool_error(error_class, error_msg, schema_path?) -> ErrorTaxonomy`（invocation / parameter / wrong-tool / failed-API / unknown）。
2. 執行器在 `executor.py:236-243`（+ schema-mismatch 路徑 `:342-352`）把 taxonomy 寫進 `ToolResult`（新欄位 `error_taxonomy` 或 enrich `content` 成診斷觀察，如「parameter error: missing required field 'query'. Provide it and retry.」）。
3. **lever**：env-gated（`CHAT_TOOL_ERROR_REFLECTION`，預設 off/on 待 §4 決策 C + A/B 證據）。
4. **A/B harness** `benchmark_tool_error_reflection.py`：corpus = 故意觸發各類 tool 錯誤的案例，量 reflection-on vs -off 的 next-turn 修復成功率 / 修復所需 turn 數（mirror `benchmark_correction_hygiene.py`）。

---

## 3. 量測機制（= 本 spike 的「drive-through」）

| 半 | 「drive-through」形狀 | CATCH |
|----|---------------------|-------|
| **A** | detector 對真 spec 檔跑出實際違規清單（如 `echo_tool`/`note_tool` 命中或被豁免）+ pytest 鏡像 | lint detector 本身（pure-infra，無 UI；與 57.137/138 同「harness 即 drive-through」）|
| **B** | `benchmark_tool_error_reflection.py` real-Azure A/B：N 案例 × reflection on/off，回報修復率 delta + token delta；verdict 決定 default（gain ≥ 門檻才 default-on，否則 env 可選）| A/B harness（real-Azure，非 gate-only）|

Half B 若要更強的 drive-through，可在 chat-v2 主流量觸發一個真實 tool 失敗（如 `python_sandbox` 丟例外）→ 看 LLM 下一輪是否依結構化診斷修對 —— 但這依賴 real-LLM 非確定性（57.130 deterministic-tool-trigger 教訓），A/B harness 是更可靠的主證據。

---

## 4. 待決策（將以 AskUserQuestion 確認）

### 決策 A — scope（兩半關係）
- **A1（建議）**：**Half A + Half B 同一 spike**，但 Half A 是「確定交付」（lint detector，價值確定、零風險）、Half B 是「evidence-first measure-then-default」（執行器 enrich + A/B harness + default 由證據定）。一個 thin spike 涵蓋，符合 §2.4 家族（57.136-139）的「ship 一個 lever + 量測 verdict」pattern。
- **A2**：只做 Half A（lint）—— 最小、最確定；Half B 另立 spike。
- **A3**：只做 Half B（reflection）—— 但 Half A 幾乎零成本，分開不划算。

### 決策 B — Half B 的「獨立於 loop.py」嚴格度
- **B1（建議）純 Cat 2**：只 enrich 執行器 dominant 路徑（`executor.py`），`loop.py:3023-3030` rare 路徑（執行器自身拋）**暫不 enrich** → 登 `AD-Tool-Error-Reflection-Loop-RarePath-Phase58`。零 loop.py 編輯。
- **B2 全覆蓋**：B1 + 把 `loop.py:3023-3030` 改成呼叫 Cat 2 的 `classify_tool_error` 建 content（~3-5 行 surgical refactor）→ rare 路徑也結構化。破「零 loop.py」但覆蓋完整。

### 決策 C — Half B default（含 RL-training confound）
- **C1（建議）env-gated，default 由 A/B 證據定**：先 default-off lever，A/B harness verdict 若 gain 顯著（next-turn 修復率提升且 token 不爆）→ 翻 default-on；否則保 opt-in（同 57.136 keep-default / 57.138 opt-in 的證據驅動決策）。
- **C2 直接 default-on**：假設 external-signal reflection 必有益（方向研究背書）→ 但跳過量測違反 evidence-first，不建議。

### 決策 D — Half A 施工位置
- **D1（建議）CI lint detector**（`check_tool_descriptions.py`）：與既有 10 個 detector 一致、可 allow-list test 工具、不影響 runtime。
- **D2 register-time 驗證**（`registry.py:register`）：runtime 強制，但會讓 test-only 工具註冊變麻煩 + 與既有「lint 管品質、register 管語法」分工不一致。

---

## 5. 冗餘 / 反模式風險

| 風險 | 評估 |
|------|------|
| **AP-6 為未來預留** | Half A 有當前真實案例（防 description 退化 + param-desc 必填）；Half B taxonomy 有當前案例（LLM 修錯需結構化診斷）。**但** Half B 的新 `error_taxonomy` 欄位若無 consumer = AP-6 → 必須同 spike 接上 enrich content（有 consumer = LLM observation）|
| **AP-4 Potemkin** | Half A detector 對真 spec 跑出實際違規 + Half B A/B harness real-Azure 量測 = 有實質，非空殼 |
| **AP-3 散落** | Half A 集中 `scripts/lint/`；Half B taxonomy 集中執行器 + 一個純函式模組 → 不散落 |
| **AP-2 side-track** | Half B 必須接主流量（執行器 → loop append → LLM 看到），非旁支 |
| **與 Cat 8 ErrorClass 重複** | §1.4 已論證正交（重試決策 vs 修錯診斷）—— 共存非冗餘；design note 須明記兩 taxonomy 分工 |
| **~40% 數字當真** | 誠實框架：§2.3 是單一 anecdotal 點 + 現況 description 已大致良好 → Half A 價值定位「護欄」非「~40% 提速」；不在 PR/design note 引用 40% 當預期 |

---

## 6. 最小可行形狀（pending 決策；以 A1+B1+C1+D1 估）

```
scripts/lint/check_tool_descriptions.py                          # NEW — Half A detector（mirror check_llm_sdk_leak）
backend/tests/unit/scripts/lint/test_tool_descriptions.py        # NEW — Half A pytest 鏡像
backend/src/agent_harness/tools/_error_taxonomy.py               # NEW — Half B 純函式 classify_tool_error
backend/src/agent_harness/tools/executor.py                      # EDIT — :236-243 + schema 路徑 enrich content/taxonomy
backend/src/agent_harness/_contracts/tools.py                    # EDIT — ToolResult += error_taxonomy（可選欄位）
backend/scripts/benchmark_tool_error_reflection.py               # NEW — Half B A/B harness（mirror benchmark_correction_hygiene）
backend/tests/fixtures/tools/tool_error_reflection_cases.yaml    # NEW — A/B corpus
backend/tests/unit/.../test_error_taxonomy.py                    # NEW — 純函式 + enrich 斷言
（決策 D2 才動）.../tools/registry.py                              # register-time 驗證
（決策 B2 才動）.../orchestrator_loop/loop.py                      # rare 路徑 refactor（~3-5 行）
```

- 範疇：Cat 2（純）+ scripts/lint。**NO migration / NO wire event / NO frontend / NO 17.md 契約變更**（`ToolResult` 加可選欄位不改 ABC 簽章；但 design note 須記）。
- 預估形狀：~6-8 NEW/EDIT 檔；計算量輕（lint walk + 純函式分類 + A/B 斷言）；無 DB；A/B drive-through 用 standalone script（如其他 benchmark_*.py，不需 backend server）。
- 估算 class 候選：類同 `guardrail-restrict-spike` 0.60（57.137）/ `verification-context-hygiene-spike` 0.60（57.136）—— Cat 2 結構性護欄 spike + 量測 harness + env-gated lever + drive-through；real-code core（detector + 純函式 + enrich + ~150 行 harness）足以撐 0.60 spike multiplier（57.137 lesson）。

---

## 7. 與其他機會的關係

- **canonical 排序最後一個**：#6/#3/#8/#4/#1/#2/#5 全 CLOSED → #7 是最後一個 canonical research item。之後進 Phase 58 carryover pool（DAG / scheduler / provider-attr / content-capture / metrics-labels / `AD-Loop-CancelEvent-Poll` 等）。
- **獨立於 loop.py**（Half A 完全、Half B dominant 路徑）→ 不與任何 in-flight 衝突。
- **與 #3 cross-burst scheduler 互換**：使用者可改選 #3（其 task-primitive 前置已於 57.140 shipped）；但 #7 更小、更獨立、收束 canonical 清單。
- **與 #8 key-condition verifier 共用洞見**：兩者都是「external verifiable signal 讓 correction 可靠」的 §2.4 分界線 —— #8 在 verifier（答案層），#7 Half B 在 tool error（工具層）。

---

## 8. References

- `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.3（tool-desc ~40% 🟡）/ §2.4（structured reflection BFCL v3 🟢 + RL confound + self-correction 分界）/ §5 #7 / §3 Cat 2 / §6（landmark 2509.18847 Structured Reflection）
- `backend/src/agent_harness/_contracts/tools.py:77-149`（ToolSpec / ToolAnnotations / ToolResult + error_class）
- `backend/src/agent_harness/tools/{registry.py:51-74, executor.py:200-243, exec_tools.py, todo_tools.py, memory_tools.py, search_tools.py, hitl_tools.py, echo_tool.py, note_tool.py}` + `skills/tool.py` + `subagent/tools.py`
- `backend/src/agent_harness/error_handling/{_abc.py:30-36, retry.py:56-82}`（Cat 8 ErrorClass — 正交）
- `backend/src/agent_harness/orchestrator_loop/loop.py:508-569, 2940-3058`（_handle_tool_error + dominant/rare 失敗路徑）
- `scripts/lint/{run_all.py, check_llm_sdk_leak.py}` + `backend/tests/unit/scripts/lint/`（Half A detector 模板）
- 前例 benchmark harness：`backend/scripts/benchmark_correction_hygiene.py`（57.136）/ `benchmark_sandbox_escape.py`（57.137）/ `benchmark_key_condition.py`（57.138）
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`（ToolSpec / ToolResult / ToolExecutor 契約 — 不改簽章）
