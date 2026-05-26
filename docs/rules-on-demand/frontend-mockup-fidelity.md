# 前端 Mockup-Fidelity 規則（4-layer 同步協定）

**Purpose**: 強制「逐字複製 mockup CSS」方法，杜絕 Sprint 57.18-57.27 重複 10 次的 CSS 翻譯 drift。本檔是前端 mockup-fidelity 方法的**單一權威來源**；其他文件指向本檔。

**Category**: Frontend / Development Process / Standards
**Created**: 2026-05-22
**Last Modified**: 2026-05-22
**Status**: Active

**Modification History**:
- 2026-05-22: Initial creation — from the 2026-05-22 mockup-fidelity investigation + `/overview-poc` PoC (`claudedocs/5-status/v2-investigation-20260522/`)

---

## 為什麼需要此規則

Sprint 57.18-57.27（10 個 sprint）前端始終無法與 mockup 一致：`/overview` 重做 3 次、`/cost-dashboard` 4 次，方法論換了 4 種。2026-05-22 調查發現**根因不是執行不力，是方法錯**——production 把 mockup 的 CSS「翻譯」進 Tailwind/shadcn，而翻譯步驟必然注入 drift。**而且專案的指引文件本身（STYLE.md / CLAUDE.md / AGENTS.md）就在規定這個錯方法。** PoC（`/overview-poc`）已驗證正確方法可達 byte-identical。

完整根因 + PoC 證據：`claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md`。

---

## 核心：mockup 是兩層，可複製性相反

「mockup」不是一個不可分割的整體。它是兩層：

| mockup 的層 | 檔案 | 能否無損複製到生產 | 處理方式 |
|------------|------|-------------------|---------|
| **視覺層 / CSS** | `reference/design-mockups/styles.css`（1123 行 / 251 class / oklch）| ✅ 可以 —— 純文字 CSS 宣告 | **逐字複製，永不翻譯** |
| **組件邏輯層** | `reference/design-mockups/page-*.jsx`（UMD React + `window` 全域 + babel-standalone）| ❌ 不可以 —— 無法被 Vite/TS import | 重寫成 typed `.tsx` |

→ 「**重寫**」這個指令**只**套用在組件邏輯層。CSS 層是「**複製**」，不是「重寫」。混淆這兩層 = 過去 10 個 sprint 的錯誤根源。

---

## 4-layer 同步協定

| Layer | 檔案 | 做法 |
|-------|------|------|
| **1** | `reference/design-mockups/styles.css` | canonical，oklch；設計師**只改這裡** |
| **2** | `frontend/src/styles-mockup.css` | **Layer 1 的逐字複製**（byte-identical）；在 `main.tsx` 於 `index.css` 之後 import |
| **3** | `frontend/src/index.css` | `@import "tailwindcss"` + 精簡 bridge；**不**養 mockup 系眼湊 HSL token、**不**用 `html{font-size:13px}` 補償 hack |
| **4** | `frontend/tailwind.config.ts` | 仍透過 Tailwind utility 消費的 token，bridge 用 `var(--X)`（變數已含完整 `oklch()`），**不**用 `hsl(var(--X))` |

---

## 鐵律（7 條）

1. `styles-mockup.css` 必須與 `styles.css` **byte-identical**（`diff` 輸出為空）。
2. 頁面組件**直接消費 mockup class 名**（`className="card"` / `"grid-stats"` / `"badge"` …）—— 不重新拼成 Tailwind utility。
3. 色彩**全程 oklch** —— 禁止 oklch→HSL 近似（兩者非等價色彩空間，每次轉換都偏色）。
4. Tailwind utility **只**用於：mockup 沒有對應 class 的 layout 一次性微調、a11y wrapper —— **不**用於重新表述 mockup 已有的樣式。
5. shadcn primitive **只**用於 interaction 邏輯（`<Dialog>` / `<Tabs>` 的行為）—— **不**作樣式替代層；其視覺仍由 mockup class 決定。
6. 「重寫」scope = **組件邏輯層**（`window` 全域 → typed hooks、`.jsx` → strict `.tsx`、i18n 接線、接 API）。
7. 圖表（recharts / inline SVG）：配色 / 軸標 / 資料形狀逐字對齊 mockup，不用 lib 預設。

---

## 禁止項（過去 10 sprint 的 drift 來源 —— 逐條對應）

- ❌ **翻譯 CSS** —— 讀 mockup 樣式再手工拼成 Tailwind utility（drift 注入點 #2）
- ❌ **oklch → HSL「approximation」** —— 用眼睛湊 HSL 值（drift 注入點 #1）
- ❌ 用 shadcn `Card` / `Badge` / `Button` **預設值**替代 mockup 的 padding / radius / shadow / color（drift 注入點 #3）
- ❌ 養兩套並行 token tree（shadcn 系 + mockup 系）+ `font-size` hack（drift 注入點 #4 補償債）
- ❌ 把 mockup 當成不可分割的整體（它是兩層，可複製性相反）
- ❌ 用「production 簡化版」名義裁剪 mockup widget / 改 layout
- ❌ 自創 i18n copy 不對照 mockup `reference/design-mockups/i18n.jsx`

---

## DoD（每個 frontend 頁面 task）

1. **CSS diff**：`diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → 必須為空（line-ending 除外）。
2. **Playwright 截圖**：mockup（`cd reference/design-mockups && python -m http.server`）vs production dev server，1440×900 viewport。
3. **computed-style 量測**：代表元素（`.card` / `.badge` / `.stat` / `.page-head` …）的 background / border / radius / font / padding **逐項**對比 mockup；版面尺寸（卡片寬、grid）逐項對比。drift 偵測在**代碼/量測層**做，用眼只做最後信任閘。
4. **drift 分類 + verdict**：殘留 drift 分 token / 結構 / 組件 / 引擎 4 類，parity verdict 記入 progress.md / DRIFT-REPORT.md。
5. **grep guard**：組件檔案內無寫死的 hex / oklch 色值（`grep -rn '#[0-9a-fA-F]\{6\}\|oklch(' frontend/src/features frontend/src/pages` 應只剩 mockup 內聯 style 的合法引用）。

---

## fundamental drift 處理（先換方法，再重建）

若頁面出現結構性 drift：**先判定「方法對不對」，方法錯就先換方法，再重建** —— **不要**用同一套會 drift 的方法 patch 或 redo。前車之鑑：`/overview` 用翻譯法做了 3 次、`/cost-dashboard` 4 次，每次 redo 都重新注入 drift。

---

## 參考

- **EKP 姊妹專案**：相同 mockup 架構（React UMD + babel CDN + 手寫 oklch `styles.css`）達 90-95% 保真度，靠的就是逐字複製 CSS（見 memory `reference_ekp_mockup_method`）。
- **完整根因 + PoC 證據**：`claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md`。
- **mockup 兩層說明**：`reference/design-mockups/AGENTS.md` §整合到 production。
- **CLAUDE.md** §Frontend Mockup-Fidelity Hard Constraint（always-loaded 核心摘要，指向本檔）。

---

## Phase-2 re-point systematic anti-patterns（2026-05-24 user-reported issues 後加入）

Sprint 57.18-57.27 epic 解決了「CSS 翻譯 → HSL approximation」這條主軸 drift。但 Phase-2 per-page re-point（57.29+）開展後又揭示**另外 3 條獨立的系統性 drift class**，需在每個 re-point sprint 的 Day 0 + Day 2.5 對齊驗證納入。

### Anti-pattern AP-Phase2-A：Production-only 外層 padding wrapper（翻譯遺產）

**症狀**：Production page 的 root JSX 元素包了一層 `<div style={{ padding: <N>, ... }}>` 或類似 wrapper，外層 padding 跟 `.content` 預設 `padding: 24px 28px 60px` 疊加 → 視覺左右 inset 比 mockup 明顯多 10-20+ px。

**前車**：`/state-inspector` `STATE_PAGE_WRAPPER_STYLE = { padding: 18, ... }`（Sprint 57.19 vintage；Sprint 57.37 verbatim re-point 誤以為「保留 backend wiring」而保留）→ FIX-011 fixed 2026-05-24。

**Day 0 Prong 1 額外 grep**：
```bash
grep -n "padding:.*[0-9]\|style={{ padding" frontend/src/pages/<target>/<page>.tsx
# mockup page-*.jsx return 通常以 <> fragment 或 <div className="page-head"> 起；無 padding wrapper
```

**判定規則**：
- Mockup 頁面 return 第一層是否有 `<div style={{ padding: ... }}>` 或 `<div className="some-page-wrapper" style={{...}}>`？→ 若 mockup 無 → production 該層必須刪
- 例外：若 mockup 有 fullbleed 設計（`loop-canvas` / `chat-shell`），production 用 `AppShellV2 fullBleed` prop 而**不是**自己加 padding wrapper

**Re-point sprint Day 1 task**：刪除所有 production-only padding/margin wrapper；如需內部間距，用 mockup `.grid-X` / `.col` / `.row` class（這些 class 本身含 gap 邏輯）。

---

### Anti-pattern AP-Phase2-B：Inline 混 font-family span 缺 baseline 對齊提示

**症狀**：mockup 設計中混排 `<span class="mono">` + `<span class="subtle">` + 普通 `<span>` 在同一 inline row。Mono 字體（Geist Mono）跟 sans 字體（Noto Sans TC）baseline 距離大；production 渲染時 mono 字 baseline 看起來「下沉」明顯，跟 mockup 看起來不一致。

**前車**：`/state-inspector` detail card title `[v18 by orchestrator_loop]` —`by` 字 baseline 明顯低於 `v18` + `orchestrator_loop` 兩個 mono token。Mockup 設計用 `<span class="row" style={{ gap: 6 }}>` 包，但**未強制 baseline 對齊**；mockup 本身在系統 mono `Menlo` 渲染時差距小，production 用 `Geist Mono` 差距大。

**Day 0 Prong 2 grep**：
```bash
grep -n 'className="mono"\|className=".*\bmono\b\|className="subtle"' reference/design-mockups/<target-page>.jsx
# 看是否同 inline row 有 mono + subtle / 普通 sans 混排
```

**Re-point sprint Day 1 task（推薦）**：
- 若 mockup 該 row 設計用 `<span class="row">` 包多個不同 font-family 的 span，production 應**主動補加** baseline 對齊：要嘛 outer span 加 `display: inline-flex; align-items: baseline`，要嘛內 span 加 `vertical-align: baseline`
- 不算違反「verbatim CSS swap」原則 —— mockup 自身沒設這個 prop 是因為 mockup 渲染環境 font 差距小

**驗證**：Day 2.5 後 baseline sweep，截圖該 row vs mockup `localhost:8080/#<route>` 1:1 對比。

---

### Anti-pattern AP-Phase2-C：Tailwind utility `border-border` → shadcn token 殘留（Phase-2 未 re-point 的 page）

**症狀**：production 內 31+ files 還在用 Tailwind `border border-border` / `border-b-2 border-border` 等 utility class。這些 utility 透過 `tailwind.config` 解析到 `hsl(var(--sc-border))` —— shadcn-system **`--sc-border`**，**不是** mockup `--border`。視覺差距：
- Mockup dark `--border: oklch(0.26 0.008 260)` (L=26%) — 中深灰
- Shadcn dark `--sc-border: hsl(217.2 32.6% 17.5%)` (L=17.5%) — 更深，視覺接近黑

**這不是「CSS translation drift」class（不像 Sprint 57.18-57.27 翻譯方法錯）**——這是 **Phase-2 epic incomplete migration** class：剩 6 個 🟡 routes 還沒 re-point，這些 page 的所有 Tailwind utility border 都還在用 shadcn token。

**Day 0 Prong 2 grep（用於 audit pages）**：
```bash
grep -rln "border-border\|\bborder\s+border-" frontend/src/pages/<route>/ frontend/src/features/<feature>/
# 若 > 0 sites，re-point sprint 必須包含 Tailwind utility → mockup verbatim CSS class 替換
```

**Re-point sprint Day 1 task**：
- 把 Tailwind utility class（`border-border`, `bg-card`, `text-muted-foreground`, `bg-muted/30` 等）→ mockup verbatim class（`.card`, `.subtle`, `.mono`, etc.）
- 移除 `text-card-foreground` / `bg-card` 等 shadcn-system token usage —— 用 mockup CSS classes 取代

**全局 fix candidate（高 ROI 替代路徑）**：
- Option **A** — 對齊 `--sc-border` 值到 mockup `--border`（1-line `index.css` 改：dark `--sc-border` → `oklch(0.26 0.008 260)` / light → `oklch(0.91 0.006 260)`）。**Pros**：未 re-point page 立刻視覺對齊 mockup；**Cons**：違反 Sprint 57.28 4-layer 設計意圖（shadcn token 故意 dual-track）
- Option **B** — 加速 Phase-2 re-point 剩 6 🟡 routes；不再追加 shadcn-system tokens；等 epic close 該 utility 自然消失（completeness path）

**推薦**：B（completeness），但 A 是 acceptable 過渡 fix 若用戶覺得視覺差距難忍。

### Code review checklist（新增 3 條）

每個 Phase-2 re-point sprint PR 必須能對下列 3 條回答 ✅ / N/A：

- [ ] **AP-Phase2-A**: production root JSX 第一層有 `<div style={{ padding: X }}>` 或 wrapper？若有，已對照 mockup 確認該層**應該存在**（fullBleed 例外）；否則已刪除
- [ ] **AP-Phase2-B**: 若 mockup row 中混排 mono + subtle / 不同 font-family span，已主動補 `align-items: baseline` 或 `vertical-align: baseline`
- [ ] **AP-Phase2-C**: 該 page / feature 內 Tailwind utility `border-border` / `bg-card` / `text-muted-foreground` 等 shadcn-system token 用法已全部替換為 mockup verbatim class

---

## 🛡️ Mockup File is Canonical (AuditDocSync Rule)

> **加入版本**：Sprint 57.46（2026-05-26）；closes `AD-MockupFidelity-AuditDocSync-Rule`（source: Sprint 57.45 NEW carryover）。

當 audit-derived 文件（`audit-report.md` / drift-audit / NEAR-PARITY / CATASTROPHIC verdict 等）聲明 component X 有 property Y，但 mockup 來源檔顯示 property Z：

**Mockup file wins. Audit doc 更新對齊 mockup，**不是**反向。**

### Why this rule exists

Audit doc 是**衍生資料**（從 mockup screenshot + 頁面 read-through 由人手抄錄）。一旦 Sprint N 的 audit doc 寫成「tab order 是 A/B/C/D」，Sprint N+1, N+2, ... 都引用該 audit doc 而不再回去看 mockup 來源。**Transcription errors（手抄誤）會 propagate forward 跨多個 sprint 不被挑戰**。

**Sprint 57.45 evidence**：audit row 9 聲明 /chat-v2 Inspector tabs 應為「Run / Tools / Memory / Verify」，但 mockup `reference/design-mockups/page-chat.jsx:378-381` 實際是「Turn / Trace / Memory / Tree」。Audit doc 從 Sprint 57.22 起 transcription error 持續 propagate **23 個 sprint 不被挑戰**，直到 Path B audit overrule 才被 grep 驗證出。

### Day 0 Prong 2 enforcement

每個 drift-audit / Phase-2 re-point 的 Day 0 Prong 2 grep **必須**包含：

1. **直接讀 mockup 來源檔**（例：`reference/design-mockups/page-*.jsx`）
2. **將 audit doc 聲明用 grep 對照來源檔**
3. **若有 discrepancy → audit doc 是錯的；更新 audit doc 對齊 mockup；調查 transcription error 何時被引入**

**Grep query template**：
```bash
# 例：audit doc 聲明 /chat-v2 tabs = "Run/Tools/Memory/Verify"
grep -n "Tab\|tab" reference/design-mockups/page-chat.jsx
# 若實際 mockup 顯示的是 "Turn/Trace/Memory/Tree" → audit doc transcription error
# 立即修正 audit doc + 添加 inline note + log carryover AD
```

### Audit doc update protocol

當發現 audit doc transcription error：

- **加 inline note**：`<!-- Sprint XX.Y Day 0 Prong 2: row N claim was transcription error; mockup shows X -->`
- **更新 verdict**：若 mockup 與 production 實際一致，將 NEAR-PARITY / CATASTROPHIC → PARITY
- **Cross-reference**：將完整 root cause 寫入 Sprint XX.Y retrospective
- **Log carryover AD**：若 pattern 表示更廣的 audit-corpus integrity 問題，新增 carryover AD

### Why this rule is hard-loaded as rule corpus (not Sprint 57.45 case study only)

**因為 audit-derivative 文件數量持續增長**（每個 drift audit / Phase-2 sweep 都產生新 audit doc），手抄錯誤累積機率每 sprint 增加。Sprint 57.22 → 57.45 之間累積了 23 sprint 的 propagation，光是檢查 production 跟 audit doc 對齊**並不足夠**——必須把 mockup 來源檔作為 canonical source 來打通。

### 跨參考

- `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 — content verify methodology（grep 對照 source claim）
- Sprint 57.45 retrospective — Path B audit overrule 案例完整 narrative
- Sprint 57.22 retrospective — transcription error 引入點（原始 Sprint /chat-v2 audit）

---

**維護責任**：每個 frontend sprint kickoff 必讀本檔；Code reviewer 以 DoD 5 條 + 鐵律 7 條 + Phase-2 anti-patterns 3 條 + AuditDocSync 1 條為 PR 強制檢查項。

---

## 📸 Mockup Capture Method

> **加入版本**：Sprint 57.46（2026-05-26）；closes `AD-MockupCapture-Method-Resolution`（source: Sprint 57.43+ AD-MockupCapture-03+04 carryover）；formalizes existing convention.

要 capture mockup 的真實畫面（為了與 production 1:1 比對 / 為 audit-report.md 提供 evidence），**統一方法 = Option B static file serve**。

### 為什麼是 Option B

- Mockup 本身就是 standalone React UMD + babel-standalone CDN，**可以**用 `python -m http.server` 直接 serve
- 比 file:// 可靠（file:// 下 babel-standalone fails on CORS / SRI for unpkg CDN scripts → blank black PNG）
- 比 byte-proxy / JSX transpile 簡單（不需額外 build step）
- 比 real-browser screenshot service 快（local，無 network）

### 標準命令

```bash
# Terminal 1: serve mockup（在 reference/design-mockups/ 內或上層皆可）
cd reference/design-mockups
python -m http.server 8080

# Terminal 2: 跑 Playwright sweep（從 frontend/）
cd frontend
node scripts/mockup-sweep.mjs

# 輸出：claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/*.png
# 24 個 PNG（auth 7 + ops 7 + governance 4 + observability 2 + admin 2 + PROP 1 + 1 alt）
# 每個 1440×900 viewport
```

### Script 細節

- **檔案**：`frontend/scripts/mockup-sweep.mjs`
- **method**：透過 `window.location.hash` SPA 切換而**非**每 route 重新 `goto`（mockup 是 SPA，hash routing；first goto + 8s babel-compile wait → subsequent hash nav 各 900ms）
- **bypass file://**：硬編 `BASE_URL = "http://localhost:8080/index.html"` 對應 Option B serve
- **output dir**：`claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/`（與同期 `production/` sweep 並列方便對比）

### 何時跑

- 任何 drift audit / Phase-2 re-point sprint 的 Day 0 Prong 2 或 Day 2.5（pre-merge）證據捕捉
- Mockup 來源更新後（e.g. 設計師調整 page-*.jsx）→ 重跑取得新 baseline

### 不建議的 alternatives

- ❌ **file:// + Playwright** — babel-standalone CDN fail，PNG 是黑色 blank
- ❌ **JSX transpile to HTML** — 增加 build step，不需要（mockup 已能用 babel-standalone 直接跑）
- ❌ **headless Chrome real browser screenshot service** — overkill，慢，需 network

### 跨參考

- `frontend/scripts/mockup-sweep.mjs` — 完整 source（22 routes + hash SPA nav）
- `frontend/scripts/route-sweep.mjs` — sibling production-side sweep（與 mockup-sweep 共用 slug naming）
- CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint — 提到 `python -m http.server` 為 canonical method

---

**Modification History**:
- 2026-05-26: Sprint 57.46 — add §AuditDocSync Rule + §Mockup Capture Method (closes 2 carryover ADs)
