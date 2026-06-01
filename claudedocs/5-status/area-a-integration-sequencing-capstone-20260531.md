# Area-A 整合排序 Capstone — Loop 接線 6 缺口的依賴圖與 Sprint 選擇依據

**Purpose**: 把 Area A 六份逐點分析(A-1~A-6)的結論收斂成一張依賴圖 + 一張排序表,作為未來 sprint「先做哪個」的決策依據。本檔是 **analysis 層 capstone**,不是 sprint plan(不含具體未來 sprint task 承諾,遵守 rolling planning 紀律)。
**Category**: Cross-cutting integration analysis(對齊 11+1 範疇 3 / 5 / 11 / 12 + 前端 + SSE)
**Scope**: Phase 57+ 整合盤點後續 / Area A 深度分析收尾
**Created**: 2026-05-31
**Status**: Active(decision aid)

**Modification History (newest-first)**:
- 2026-06-01: Sprint 57.64 closeout — 候選 Sprint A ✅ SHIPPED (Cat 5/3/11 keystone wiring); D3 修正 runtime-confirmed; AP-2 假綠 CLOSED; real_llm leg 改述為卡 A-5
- 2026-05-31: Initial creation — 收斂 A-1~A-6 六份分析為依賴圖 + 排序表 + sprint bundle 建議

**Related(本檔為下列 6 份之 capstone,精確 file:line 證據以子檔為準)**:
- `integration-progress-20260531.md` — 整合總盤點(L1~L4 達成度)
- `cat3-memory-loop-injection-analysis-20260531.md` — A-1
- `cat5-promptbuilder-loop-injection-analysis-20260531.md` — A-2
- `cat11-handoff-loop-injection-analysis-20260531.md` — A-3
- `cat12-loop-tracer-analysis-20260531.md` — A-4
- `cat-events-to-sse-analysis-20260531.md` — A-5
- `frontend-real-data-wiring-analysis-20260531.md` — A-6

---

## 0. 一句話總結

> **Area A 的瓶頸不是「沒蓋好」,而是「蓋好了沒接上 loop」。** 6 個缺口裡,5 個是純注入/加法(不動 `loop.py` 主體),只有 HANDOFF(A-3b)是真正要設計的新東西。**拱心石是 A-2 Tier 1(PromptBuilder 注入)** —— 它一通,A-1 Tier 2、Cat 4 快取的一半、A-5c 診斷可見性跟著解鎖。

---

## 1. 六缺口速覽(現況 → 缺什麼 → 性質)

| 代號 | 範疇 | 元件成熟度 | 缺口本質 | 改 `loop.py`? |
|------|------|-----------|---------|:---:|
| **A-1** | Cat 3 Memory | store 完整(Level 3) | 3 處斷:① `make_default_executor` 不註冊 builtin 工具 ② 無 auto-inject ③ 無 verify_before_use | Tier1 ❌ / Tier2 ❌(流經 Cat 5) |
| **A-2** | Cat 5 PromptBuilder | `PromptBuilder`+`DefaultPromptBuilder` 全建好 | handler 不傳 `prompt_builder=` → `loop.py` true-branch 永走不到,fallback 恆走;`check_promptbuilder` lint **假綠** | Tier1 ❌ / Tier2 ✅(快取) |
| **A-3** | Cat 11 Subagent | FORK/TEAMMATE/AS_TOOL executor 在;HANDOFF 空殼 | `AgentLoopImpl` 無 `subagent_dispatcher` param;4 模式全未注入 | A-3a ❌(3 模式)/ A-3b ✅(HANDOFF) |
| **A-4** | Cat 12 Tracer | tracer ABC + span 型別在 | 三重缺:只有 root span、注入 no-op tracer、exporter env-gated;另有 `ctx.child()` nesting bug | ➕ 純加法 |
| **A-5** | Events→SSE | 14 型事件 + SSE router 在 | `sse.py` 對部分型別 `raise NotImplementedError`,但 router `try/except: debug+continue` 接住 → **不 crash 但靜默丟事件** | ❌ |
| **A-6** | 前端真資料 | ~5 頁 full real | rebuild 弄丟 2 處接線 + ~7 頁 fixture(預期債)+ ~7 頁缺後端 | ❌(前端) |

---

## 2. 依賴圖(誰解鎖誰)

```
                    ┌──────────────────────────────────────────┐
                    │  A-2 Tier1  PromptBuilder 注入(拱心石)    │
                    │  handler 傳 prompt_builder= + memory_provider │
                    └───────────────┬──────────────────────────┘
                                    │ 解鎖
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ A-1 Tier2        │  │ Cat 4 快取的一半  │  │ A-5c 診斷可見性   │
   │ memory auto-inject│  │ (prompt caching) │  │ (PromptBuilt 事件)│
   └──────────────────┘  └──────────────────┘  └──────────────────┘

   ── 共用同一缺口(make_default_executor 不註冊 builtin 工具)──
   ┌──────────────────┐        ┌────────────────────────────┐
   │ A-1 Tier1         │ ◀───同─▶│ A-3a FORK/TEAMMATE/AS_TOOL  │
   │ memory 工具(on-demand)│ 一缺口 │ (註冊 subagent 工具)        │
   └──────────────────┘        └────────────────────────────┘

   ── 獨立、可任意排程(無上游依賴)──
   • A-4   loop tracer Tier0+1(純加法)
   • A-5a  Tripwire 等事件 serialize(便宜)
   • A-5b  事件 schema codegen + CI parity(高槓桿,防未來漂移)
   • A-6a  admin-tenants 重掛(Area A 最便宜的贏面)
   • A-6b  memory 前端 3 個 hook(語意上配 A-1)

   ── 下游 / 昂貴 / 配對 sprint(後排)──
   • A-5c  診斷事件可見性  ← 下游於 A-1 / A-2 / A-4(要先有事件才值得顯示)
   • A-2 Tier2  prompt caching  ← 動 loop.py,排 A-2 Tier1 之後
   • A-3b  HANDOFF 真實落地  ← design spike,需 design note(8-point gate)
   • A-6c/d  缺後端的頁  ← 本質是後端 feature sprint,前後端同 sprint 配對出
```

**讀圖要點**:
1. **A-2 Tier1 是唯一的「拱心石」** —— 它的下游有 3 條(A-1 Tier2 / Cat4 快取 / A-5c)。先做它,後面三件變便宜。
2. **A-1 Tier1 與 A-3a 是「同一個缺口的兩個受益者」** —— 都卡在 `make_default_executor` 沒呼叫 `register_builtin_tools`。一次改動同時喂 memory 工具 + subagent 工具,合做 ROI 最高。
3. **A-4 / A-5a / A-5b / A-6a / A-6b 彼此獨立** —— 可插在任何 sprint 之間填空,不互相阻塞。
4. **A-3b(HANDOFF)是孤兒** —— 唯一需要「設計尚不存在的東西」,別跟便宜項混在同一 sprint。

---

## 3. Master 排序表(依「解鎖價值 / 成本」)

| 序 | 項目 | 動 loop.py | 估算成本 | 解鎖價值 | 上游依賴 | 性質 |
|:--:|------|:---:|:---:|:---:|------|------|
| ⭐1 | **A-2 Tier1** PromptBuilder 注入 | ❌ | 中 | 🔺🔺🔺(拱心石) | 無 | 注入 |
| ⭐1 | **A-1 Tier1** memory 工具 | ❌ | 低 | 🔺🔺 | 無(共用缺口) | 注入 |
| ⭐1 | **A-3a** subagent 3 模式工具 | ❌ | 低 | 🔺🔺 | 無(共用缺口) | 注入 |
| 2 | **A-1 Tier2** memory auto-inject | ❌ | 中 | 🔺🔺 | **A-2 Tier1** | 注入 |
| 2 | **A-2 Tier2** prompt caching | ✅ | 中 | 🔺 | A-2 Tier1 | 改 loop |
| 3 | **A-4** loop tracer Tier0+1 | ➕ | 中 | 🔺🔺(可觀測性) | 無 | 純加法 |
| 3 | **A-5b** 事件 schema codegen+CI | ❌ | 中 | 🔺🔺🔺(防漂移) | 無 | infra |
| 3 | **A-5a** Tripwire serialize | ❌ | 低 | 🔺 | 無 | 補洞 |
| 4 | **A-6a** admin-tenants 重掛 | ❌ | 極低(~½天) | 🔺 | 無 | 前端 |
| 4 | **A-6b** memory 前端 3 hook | ❌ | 低(~3-5h) | 🔺 | 語意配 A-1 | 前端 |
| 5 | **A-5c** 診斷事件可見性 | ❌ | 中 | 🔺 | A-1/A-2/A-4 | 下游 |
| 6 | **A-3b** HANDOFF 落地 | ✅ | 高(spike) | 🔺 | design note | 新設計 |
| 6 | **A-6c/d** 缺後端的頁 | ❌ | 高(後端) | 視功能 | 後端 sprint | 配對 |

---

## 4. 建議的 Sprint 切分(每個 = 未來一個 sprint 候選,**尚未開 plan**)

> rolling 紀律:以下只是**候選排序**,不是 sprint plan。實際開 sprint 時才寫 plan+checklist,且一次只寫當前 sprint。

- **候選 Sprint A ✅ SHIPPED(Sprint 57.64,2026-06-01)** —「**Agent 會用記憶 + 結構化 prompt + 會用 subagent 工具**」= A-2 Tier1 + A-1 Tier1 + A-3a。三者於 api/factory 層接線(`make_default_executor` opt-in deps + 3 個 `make_chat_*` factory + `build_real_llm_handler` 注入),**未動 loop.py**。整合測試證實三者同時在 chat SSE flow 發火;**closes AP-8 + AP-2 假綠 lint**;real_llm live leg 延後(confirmatory,卡在 A-5 OOS + Azure cost)。
  - **D3 修正 runtime-confirmed**:capstone 原premise「A-1/A-3a 共用同一 `register_builtin_tools` 呼叫」**經 Day-0 + 實作證實為部分錯誤** —— `register_builtin_tools` 只註冊 memory,**不註冊 subagent 工具**;A-3a 需要 `make_task_spawn_tool` **獨立註冊**(+ Cat11→Cat2 `_adapt_subagent_handler` bridge)。bundle 仍 coherent(同批檔案、無 loop.py),但是「一個改動面、兩次註冊呼叫」。詳見 `CHANGE-032` + sprint-57-64 retrospective。

- **候選 Sprint B**:A-1 Tier2(auto-inject)+ A-2 Tier2(prompt caching)。承 A,動 loop.py,把「被動帶記憶 + 省 token」一起做。

- **候選 Sprint C(獨立 infra)**:A-5b(schema codegen + CI parity)+ A-5a(Tripwire serialize)。把「未來事件靜默漂移」變成 CI 失敗 —— 最高槓桿的防呆,愈早做愈省。

- **候選 Sprint D(獨立 infra)**:A-4(loop tracer Tier0+1)。純加法,用 RecordingTracer 可測,任何時間可插。

- **候選 Sprint E(前端,最便宜贏面)**:A-6a(admin-tenants 重掛)+ A-6b(memory 3 hook)。E 排在 A/B 之後做,memory 頁顯示的真資料才有內容可看。

- **後排 / 需設計**:A-5c(等 A/B/D 產出事件後再顯示)、A-3b(HANDOFF,需先寫 design note 過 8-point gate)、A-6c/d(本質後端 feature,前後端同 sprint 配對)。

---

## 5. 紀律與風險備忘

- **AP-2 假綠陷阱 ✅ CLOSED(Sprint 57.64)**:`check_promptbuilder_usage` 已加 path-targeted AST 正向檢查,偵測 chat call-site 真的傳 `prompt_builder=`(移掉 kwarg 會 regress)—— 假綠翻真綠。
- **AP-4 Potemkin**:`HandoffExecutor` 空殼 + `make_default_executor` 不註冊工具,都是「結構在、內容無」。接線 sprint 的 DoD 必須含「關掉會壞什麼」的負面測試。
- **Mockup-Fidelity**:A-6 的 ~7 頁 fixture 是**設計好的 interim debt**(fixture + BackendGapBanner),不是 regression;只有 admin-tenants / memory 兩處是 rebuild 真正弄丟的接線。
- **real_llm e2e leg 待補(非阻塞)**:Sprint 57.63(Cat 4/7/8/10)+ 57.64(Cat 5/3/11 keystone)皆已注入 production `real_llm` 路徑,mock 整合測試為主 gate。HTTP 層的 `PromptBuilt`-in-stream 斷言**卡在 A-5(events→SSE)未做** —— PromptBuilt 是 in-process LoopEvent,尚非 client SSE 事件。建議候選 Sprint B 或 A-5 sprint 順手讓 keystone 在 real 路徑外部可觀測(C-11 已證 real_llm 路徑本身可達 END_TURN)。
- **17.md single-source**:任何接線若新增/改 contract(如 `subagent_dispatcher` param),必須回登 `17-cross-category-interfaces.md`,不在本檔或子檔平行定義。

---

## 6. 給 next session 的最短交接

1. 本檔 + 6 份子分析皆在 `claudedocs/5-status/`,**全 untracked、未 commit**(在 main)。要保存須先開 feature branch + 授權。
2. 想動工 → 從**候選 Sprint A**(A-2 Tier1 + A-1 Tier1 + A-3a)開 plan+checklist。
3. 想先看最便宜成果 → **候選 Sprint E** 的 A-6a(admin-tenants 重掛 ~½ 天)。
