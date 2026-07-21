# V2 誠實全現狀審計 v2 — 引擎 vs 落地（重掃 + 過度開發量化 + go/no-go 裁決）

**Purpose**: 承接 [`v2-reality-audit-engine-vs-grounding-20260626.md`](v2-reality-audit-engine-vs-grounding-20260626.md)（6-26 baseline，快照於 Sprint 57.144）的**更新版重掃**。目的**不是**再產出一份更漂亮的現狀描述——而是回答使用者在 2026-07-15 提出的兩個決策問題：(1) 本項目有沒有重蹈 V1 覆轍的**過度開發**（有紀律地精修一台已會動、但沒開上路的引擎）？(2) 距上一份 audit 已開發 20 個 sprint（57.145–165），最新落地指標是什麼、下一步該做引擎債還是落地？本文的交付物是一個**明確的 go/no-go 裁決 + 停損機制**（§9），層級數字是達成裁決的手段，不是目的。
**Category / Scope**: Status / Reality audit v2（決策錨點 · 引擎 + 願景 + Potemkin + 前端 + carryover 拉力閘）
**Created**: 2026-07-15
**Last Modified**: 2026-07-15
**Status**: Active（snapshot；基於 git HEAD Sprint 57.165，main `88e01514`）
**Method**: 5 個平行 audit agent（切面 A 核心引擎 11+1 / B 願景四支柱 / C Potemkin 掃描 / D 前端頁面 / **E 新增：carryover 真實拉力閘 + engine-debt program 健康度**）+ 主 session 綜合 + 切面間交叉佐證。切面 D 因 agent ECONNRESET 斷線由主 session 用 Glob/Grep 補做。**行號為探查所得近似錨點，會隨 repo 演進——使用時須重新 grep 驗證。**

> **上游文件鏈**：[`agent-harness-cc-parity-20260607.md`](agent-harness-cc-parity-20260607.md) → [`harness-deepening-proposal-20260610.md`](../1-planning/harness-deepening-proposal-20260610.md) → [`v2-reality-audit-engine-vs-grounding-20260626.md`](v2-reality-audit-engine-vs-grounding-20260626.md)（6-26 baseline）→ **本文（重掃 + 過度開發量化）**。
>
> **與 6-26 的關係**：6-26 建立「引擎 vs 落地」框架與 baseline 數字（引擎 ~80% / 落地 ~17%）。本文重跑同一框架取得 delta，並新增 6-26 沒有的「carryover 拉力閘」把「有沒有過度開發」從感覺變成數字。**6-26 的核心預言「最近 9 個引擎 sprint 正讓落地空洞擴大」被本次重掃證明只對了一半——見 §8。**

---

## 0. 一句話結論

> **引擎比 6-26 更紮實了（不是空轉，A 證實 9/12 L3），落地也真的上升了（~17.5% → ~28%）——但上升 100% 集中在「記憶」一格；真正的北極星（接外部系統廣度、跑通真實業務流程）一個 sprint 都沒動，6-26 點名的 2 個核心 Potemkin 零緩解。使用者擔憂的「精修不動的引擎」是真實風險，但它有一個關鍵反證（memory arc），而那個反證正好指出下一步該往哪走。**

兩極分化的**根本形態**沒變（引擎紮實、落地偏科），只是 memory 這一格從 5% 補到 40%。中間那條「把引擎接到真實世界」的主動脈——**接第一個真實外部系統的廣度 + 跑通一條真實業務流程**——依然幾乎是空的。

---

## 1. 驗證層級 Rubric（沿用 6-26）

| 層級 | 定義 | 證明了什麼 |
|------|------|-----------|
| **L3 Drive-Through** | 真 UI + 真後端 + 真 LLM 走通（progress/retro 明確「drive-through PASS / session `<id>` / real Azure gpt-5.2」） | 整台車能開、人能用 |
| **L2 Curl/Probe** | API/harness 會回應，但無真 UI 驅動 | 零件對 + API 會回 |
| **L1 Gate-only** | 有實作 + mypy/pytest 綠，但找不到「人能用」證據 | 只證零件對 |
| **L-Mock** | 用 fixture/mock 驅動（關鍵：是否被誤導成「真」） | 視覺/結構對，資料假 |
| **L0 Paper/Potemkin** | 只有 interface/設計，主流量根本不呼叫 | 紙上有 |

---

## 2. 五切面 Delta 速覽（6-26 → 7-15）

| 切面 | 6-26 | 7-15 | 方向 | 一句話 |
|------|------|------|------|--------|
| **A 引擎 11+1** | 7 L3 · 3 L2 · 1 L1 · 1 遺漏 | **9 L3 · 2 部分 · 1 L1 · 0 遺漏** | ⬆️ 更紮實（+2 L3） | memory + compaction 升 L2→L3；引擎 ~80%→~85-90% |
| **B 願景四支柱** | ~17.5% | **~28%** | ⬆️ 但偏科 | 全部升幅來自 memory（+35pp）；其餘三柱原地 |
| **C Potemkin** | 2 核心確認 | **2 核心原封不動** + 死控件實數 2→6 | ➡️ 沒修 | business mock-as-real + Filter 死鈕整輪週期沒人碰 |
| **D 前端** | 9/39 L3（23%） | **~9–10/40 L3（~23–25%）** | ➡️ 廣度持平 | 新 drive-through 全塞進 chat-v2 單頁深度，無新 L3 頁 |
| **E carryover 拉力閘** | （本次新增） | **過度開發指數 78%** | 🔴 | 105 open AD 中 82 個「不做也無害」的完備性工作 |

---

## 3. 切面 A：核心引擎 11+1 驗證層級

| # | 範疇 | 今天 | 6-26 | Delta | 關鍵證據（近似錨點） |
|---|------|------|------|-------|---------------------|
| 1 | Orchestrator Loop | **L3** | L3 | 加深 | `loop.py` 真 while+4 terminator；57.157 dt STRONG（cross-burst 突破 max_turns=8）|
| 2 | Tool + Docker sandbox | **L3** | L3 | 加深 | 57.164 dt（真 404→taxonomy chip；並修好 wired-but-unreachable）|
| 3 | Memory（5-scope 雙軸） | **L3** ⬆️ | **L2** | **升 L2→L3** ⭐ | 57.148 dt（identity+跨 session recall）+ 57.155 dt（真 embedding+Qdrant 語意 recall+per-user 隔離）|
| 4 | Context Mgmt（compaction） | **L3** ⬆️（caveat） | **L2** | **升 L2→L3** | 57.161 dt（chat-v2 UI marker 顯示真縮減 22,925→10,584）；**caveat：需 env lever + 重 corpus 才觸發，常態聊天不觸發** |
| 5 | Prompt Construction | **L3** | L3 | 持平 | `builder.py` 每輪 build()；memory inject 騎此 seam |
| 6 | Output Parsing | **L3** | L3 | 持平 | classify→3-way branch 真驅動 |
| 7 | State Mgmt | **L3** | L3 | 加深 | rehydration + 57.157 continuation 持久化 + DAG todo state |
| 8 | Error Handling / retry | **L1** | L1 | 局部進展 | 57.164 讓「分類→terminate」首次有真 error dt；**但 retry-on-transient 核心仍 gate-only** → 保守維持 L1 |
| 9 | Guardrails（4 閘+HITL） | **L3（部分）** | L3（部分） | 持平 | input/between/output/tool-HITL 皆 dt；**第4閘 tripwire 無 dt** |
| 10 | Verification Loops | **L3** | L3 | 加深 | 57.153 dt（memory-aware judge；fabrication-catch 0→100%）|
| 11 | Subagent（4 模式） | **L3（部分）** | L3（部分） | 持平 | FORK/TEAMMATE/HANDOFF 皆 L3；**as_tool 子模式無獨立 dt** |
| 12 | Observability | **L3** | L3 | 持平 | OTel span tree 3/3 conformant（57.142）|

**分布**：L3 **9**（6-26 為 7）· 部分 2（Cat 9 tripwire · Cat 11 as_tool）· L1 1（Cat 8 retry）· 遺漏 0。

**判斷**：6-26 結論「引擎是真的，V1 病已治好」今天**更成立**。兩個 L2→L3 升級（memory、compaction）都補的是 6-26 明確點名的缺口。**無新增 Potemkin**；57.164 的 drive-through 紀律反而主動揪出並修好一個 wired-but-unreachable gap = V2 免疫系統仍在運作。引擎那「80%」今天更接近 **85–90%**。

> **本切面範圍界定**：只證「引擎內部驗到哪層」，不答「引擎是否接到真實世界」——後者是 B/C/E。

---

## 4. 切面 B：願景四支柱落地%

四支柱定義 = 一個能訪問公司資源、跑通真實流程的個人代理：1 連接外部系統 · 2 跨代理協作 · 3 長壽個人代理 · 4 真實業務流程。

| 支柱 | 今天% | 6-26% | Delta | 最高層級 | 一句判斷 |
|------|-------|-------|-------|---------|---------|
| **1 連接外部系統** | ~20% | ~15% | **+5pp** | L3 | 深化了「同一個本機連接器」（keyword→embedding→per-tenant），**沒跨過「公司既有外部系統」門檻**；`adapters/` 仍零外部連接器、零 MCP，connector 只讀本機檔 |
| **2 跨代理協作** | ~50% | ~50% | **0** | L3 | 原地不動；50% 是「機制齊全」寬鬆給分，非「真實協同完成任務」；57.145–165 零 subagent 工作 |
| **3 長壽個人代理（記憶）** | ~40% | ~5% | **+35pp** ⭐ | L3 | **唯一真正推落地的一段**；修好 6-26「memory 接了沒人用」Potemkin；但「長期為你工作」半邊仍 max_turns=8 bounded-burst |
| **4 真實業務流程** | ~2% | ~0% | **0** | L-Mock/L0 | `business_domain_mode` 預設仍 `"mock"`；零 business sprint；**最危險空洞完全沒動** |

**合計 ~28%**（6-26 ~17.5%）→ 空洞**縮小**，NOT 擴大——**但縮小 100% 來自 pillar 3 一根支柱**。

**20 sprint 拆帳**：57.145–147 knowledge（pillar 1 +5pp，真深化但停 Slice 3a）· 57.148–155 memory（pillar 3 +35pp，**唯一推落地**）· **57.156–165（10 sprint）對四支柱淨貢獻 ≈ 0**（純引擎內部；6-26 警告的「重心偏回引擎」在 memory 插曲後已重新發生）。

---

## 5. 切面 C：Potemkin 掃描

| # | Potemkin | 類型 | 近似錨點 | 6-26 狀態 | 嚴重度 |
|---|----------|------|---------|-----------|--------|
| 1 | `business_domain_mode` 預設 `"mock"` → 18 工具全打 mock_services（seed.json 假資料）| mock-as-real | `core/config/__init__.py:114` | **6-26 就有，未修** | 🔴 高 |
| 2 | SessionList「Filter」鈕無 onClick | 死控件 | `chat_v2/components/SessionList.tsx:156` | **6-26 就有，未修** | 🟡 中 |
| 3 | ChatHeader「Audit」鈕無 onClick | 死控件 | `chat_v2/components/ChatHeader.tsx:177` | 6-26 漏掉 | 🟡 中 |
| 4 | ChatHeader「Loop」鈕→無 hashchange 消費者 | 死控件 | `ChatHeader.tsx:166` | 6-26 漏掉 | 🟢 低-中 |
| 5–6 | InspectorTurn「Open audit entry」+「Open in Loop Debug」無 onClick | 死控件 | `inspector/InspectorTurn.tsx:238,242` | 6-26 漏掉 | 🟡 中 |
| 7 | SLA TimeRangeTabs 改高亮但不 refetch | 死控件（borderline） | `sla-dashboard/.../TimeRangeTabs.tsx:49` | 未列 | 🟢 低 |

**#1 關鍵**：mock_services 是 `docker-compose.dev.yml` 預設服務，dev env 實機在跑 → agent 呼工具真的拿到 seed.json 假資料並在答案中當真呈現，**答案文字無任何 MOCK 標示**（唯一標示 = 工具名 `mock_` 前綴，只在 Inspector 可見）。6-26 建議的「啟動明示 MOCK 警告 / 預設 raise」**一項都沒做**。

**#3–6 全在 chat-v2 主流量**、周圍無 banner——6-26 §7 曾誤寫 chat-v2「零死控件」與事實不符。

**淨判斷**：6-26 tracked 的 2 個核心 Potemkin **0 修 2 留**；死控件實數 2→6。**正向抵銷**：6-26 記的「memory/skills 接了沒人用」已被 57.148–155 + skills epic 接進主流量、57.164 chip 可達性已修——真進步，但**不觸及** #1/#2 兩個核心。前端整體「標示紀律」守得好（BackendGapBanner 45 檔覆蓋）。

---

## 6. 切面 D：前端頁面真實層級

**總頁數 ~40**（32 主 route + 8 auth 頁；6-26 為 39）。

- **L3 ~9–10 頁（~23–25%）**：以 **chat-v2 為核心**（工具/subagent/verification/HITL/memory/knowledge/compaction marker/taxonomy chip 全在此頁多輪 dt）+ overview/admin-tenants/memory 部分（drive-through-20260606 稽核過）。
- **L-Mock（fixture+banner，誠實非 L3）**：cost/sla/overview 三大 dashboard + governance 子頁 + verification + orchestrator（~15–20 頁）。
- **auth 8 頁**：register/invite/mfa 前端 shipped 但後端 501 → demo。
- **dev/debug ~10 頁**（loop-debug/state-inspector/compaction/jit-retrieval/subagent-tree/sse/devui/cache-manager/models/tools）：開發用途，L1–L2。

**Delta vs 6-26（9/39=23%）→ 廣度持平**。關鍵：57.145–165 的新 drive-through **全部透過既有的 chat-v2 單頁完成**，沒有把任何新頁面推上 L3。chat-v2 這一頁的 L3 **深度**大增，但前端 L3 的**廣度**沒擴張——與 E 的「44 頁 carryover 仍低層級」一致。

---

## 7. 切面 E：Carryover 拉力閘 + 過度開發量化（新增維度）

**Open AD 總數 = 105**（以 pending-backlog dashboard `TRACKS[]` 為權威清單）：engine-debt follow-on 39 · grounding 6 · Frontend/SaaS #1–46（扣 #32/#41）44 · misc 16。

**拉力閘判準**（嚴格）：只有「某個真實流程**現在**被它擋住 / 現在是假的」才 YES；「將來可能有用 / 引擎應該更完整 / per-tenant 覆寫 / inspector surface / A/B robustness / -Phase58 精修」一律 NO。

| 判定 | 數量 | 佔比 |
|------|------|------|
| **YES（真實拉力，該做）** | 8 | 8% |
| **NO（工程完備性，deferred-indefinitely）** | 82 | **78%（過度開發指數）** |
| **BORDERLINE** | 15 | 14% |

**8 個 YES**：grounding 4（External-Sources / DocTypes / Ingest-Scale + 1）· auth-hard-stub 3（Register/Invite/MFA backend 501）· `AD-Subagent-RealList`（`/subagents` 餵假列表）· `AD-Loop-CancelEvent-Poll`（Stop 後 in-flight LLM 續跑計費）。
> ⚠️ 誠實註記：這 8 個嚴格說是「**願景流程**被擋」非「**當前生產使用者**被擋」——本專案 pre-production、無真實租戶。連 YES 都帶條件（見 §9）。

**engine-debt 7-range 健康度**：39 個 open 中僅 **1 個**有真實 user-facing 拉力（Loop CancelEvent-Poll，且尚未動工），**~87% 是完備性驅動**。

| range | open | YES | 判斷 | | range | open | YES | 判斷 |
|-------|:---:|:---:|------|-|-------|:---:|:---:|------|
| ① Tool | 6 | 0 | 完備性 | | ⑤ Verification | 5 | 0 | 完備性 |
| ② Task | 5 | 0 | 完備性 | | ⑥ Loop/Interrupt | 4 | **1** | 唯一有拉力（未動工）|
| ③ Compaction | 3 | 0 | 完備性 | | ⑦ Observability | 3 | 0 | 完備性 |
| ④ Memory | 13 | 0 | 完備性 | | **合計** | **39** | **1** | **~87% 完備性** |

**冒煙槍**：engine-debt kickoff memo（2026-07-06）**自己白紙黑字**承認這 7 range「mostly engine-internal → 落地%大多不會動」。當前主線（剛燒掉 57.155–165 共 11 個 sprint）**依其自身定義就是 landing-neutral**。

---

## 8. 綜合判斷（回答使用者兩個問題）

### Q1：有沒有過度開發？→ 有，但要講精確

**不是 V1 式的假車。** 切面 A 硬證實引擎 9/12 真 L3（有 real Azure gpt-5.2 drive-through）。V1 那種「造了不會動的東西」的病，V2 沒得。

**是「持續精修一台會動、但沒開上路的引擎」。** 三個獨立切面從三個角度指向同一結論（交叉一致性 > 單一數字）：
- **時間投入面（B）**：57.156–165 這 **10 個 sprint 對願景四支柱淨貢獻 ≈ 0**。
- **Backlog 面（E）**：105 open AD **82 個（78%）** 是「不做也無害」的完備性；engine-debt 內部 **87%**。
- **該修沒修面（C）**：6-26 點名的 2 個核心 Potemkin **整輪 sprint 週期沒人碰**——精力都投在引擎新能力，沒回頭補真正影響「能不能信任這台車」的洞。

### Q2：最新狀況 + 一個改變判斷的實證

6-26 說「最近 9 個引擎 sprint 正讓落地空洞**擴大**」。重掃證明**只對了一半**：
- 57.148–155 memory arc（8 sprint）把 pillar 3 **5%→40%**，真 drive-through 落地 → **空洞不是擴大，是被 memory 補了一次**。
- 但 memory arc 之後 57.156–165 重心**又偏回引擎**，落地再次停住。

**這個「一插曲就動、一回引擎就停」的軌跡，本身就是最有力的決策指標**：轉落地會動數字（memory 證明了），回引擎不會動數字（memo 自認 + B 量測 ≈ 0）。這不是主觀判斷，是 20 個 sprint 的資料自然分出的兩段。

**表面矛盾調和**：B 說「落地升到 28%」、E 說「過度開發 78%」——不衝突。B 量**已做的**裡落地佔比（memory 拉高）；E 量**還沒做的 backlog** 裡完備性佔比。合起來：**過去的投入部分轉成了落地（好），未來的 backlog 塞滿了不會轉成落地的完備性工作（該砍）。**

---

## 9. 裁決 + 停損機制（決策錨點 — 本文的交付物）

> **尊重使用者 2026-07-06 拍板「先引擎債押後落地」的決定權——本裁決不是推翻，是把量化攤開供其在下一個 selection 點重選。**

**明確傾向：下一步轉落地，不要再排純引擎 range。** 三條可擇一或並行：

1. **轉落地（首選）** — 起 `AD-Knowledge-Connector-External-Sources` 或 `DocTypes`（接第一個真實外部系統 / 吃 PDF）。knowledge connector **卡在 Slice 3a 門檻前**（只能讀本機 .md），跨過去 = pillar 1 從「深度」變「廣度」，是**唯一會把 §9 落地%往上推的桶**。

2. **零成本高信號修復（半天）** — business mock-as-real 加**啟動 MOCK 警示**（6-26 建議被忽略至今）+ SessionList Filter 死鈕接線。成本極低，直接消掉「假裝真」這個最傷信任的洞。

3. **停損機制（止住 backlog 自我繁殖）**：
   - **落地%地板**：落地停在 ~28% 期間，**禁止連續 >1 個純 engine-debt sprint**；每清 1 個 engine range 至少插 1 個 grounding/de-Potemkin sprint。
   - **翻轉 phasing 選項**：趁引擎新鮮先做 3 個真拉力 grounding pillar（External-Sources → DocTypes → Ingest-Scale）；engine 尾債（78–87% NO）本就能無限期躺著。
   - **backlog 清理**：把 82 個 NO 正式標 `deferred-indefinitely` 移出「下一步候選」視野 → 把「105 項待辦」的心理壓力砍到 **23 項**（8 YES + 15 borderline）。

### §9 Gate（每個新 sprint 起始對照）

沿用 6-26 §9 精神，但升級為**帶停損的觸發器**（不再只是「acknowledged once」的背景音）：

1. 這個 sprint 讓願景四支柱**任何一格**的落地%動了嗎？（連續 N 個 sprint 為 0 = 停損信號）
2. 這個 sprint 碰的 AD，過「真實拉力閘」是 YES 還是 NO？（NO = 該問為什麼現在做）
3. 若這是純 engine-debt sprint，它是不是**連續第 2 個**？（是 = 觸發停損，強制插落地）
4. 每個新產生的 carryover，套拉力閘——NO 的直接標 `deferred-indefinitely`，不進候選視野。

---

## 附：與 6-26 的數字對照總表

| 指標 | 6-26 | 7-15 | Delta |
|------|------|------|-------|
| 引擎 L3 範疇數 | 7/12 | **9/12** | +2 |
| 引擎整體% | ~80% | **~85–90%** | ⬆️ |
| 願景四支柱合計 | ~17.5% | **~28%** | +10.5pp（全來自 memory）|
| pillar 1 連外部 | ~15% | ~20% | +5pp（深度非廣度）|
| pillar 3 記憶 | ~5% | **~40%** | **+35pp** ⭐ |
| pillar 4 真實業務流程 | ~0% | ~2% | ≈0（mock-as-real 未動）|
| 核心 Potemkin | 2 | **2（原封不動）** | 0 修 |
| 前端 L3 頁 | 9/39（23%） | ~9–10/40（~23–25%） | 廣度持平 |
| 過度開發指數（新） | — | **78%** | — |

---

**Related**:
- [`v2-reality-audit-engine-vs-grounding-20260626.md`](v2-reality-audit-engine-vs-grounding-20260626.md) — 6-26 baseline（本文的前身）
- [`v2-pending-backlog-dashboard-20260714.html`](v2-pending-backlog-dashboard-20260714.html) — 105 open AD 的互動式盤點（切面 E 的權威清單）
- [`../1-planning/next-phase-candidates.md`](../1-planning/next-phase-candidates.md) — pending 單一來源
- `memory/project_engine_debt_program_kickoff.md` — 2026-07-06 phasing 決策（本文量化其 landing-neutral 自認）
