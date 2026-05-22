# mockup 一致性問題：根因診斷 + 解法 + PoC 驗證（Task 3）

**調查日期**: 2026-05-22
**調查者**: AI 助手（Claude Opus 4.7）
**範圍**: 為何「頁面效果與 mockup 不一致」10 個 sprint 處理不了 — 根因、解法、PoC 實證
**方法**: 直接讀檔診斷 + EKP 參考專案經驗交叉驗證 + Playwright 雙服務截圖 + computed-style 量測 + `/overview-poc` PoC 頁面
**狀態**: ✅ 完成（PoC 驗證通過）

> 本報告是 3 份調查報告的第 3 份，也是核心。第 1 份 = V2 整體狀況；第 2 份 = 前端現況。
> PoC 程式碼在分支 `investigation/mockup-fidelity-poc`；截圖在本資料夾 `screenshots/`。

---

## 1. 執行摘要

**問題不是執行不力，是方法錯了。** 10 個 sprint、4 種方法論換來換去、`/overview` 重做 3 次、`/cost-dashboard` 重做 4 次 —— 因為每一種方法都包含同一個有損步驟：**翻譯 CSS**。

**根因一句話**：mockup 是兩層 ——「視覺層 CSS（`styles.css`）」與「組件邏輯層（`.jsx`）」。CSS 層**可以、也應該**逐字複製；只有組件邏輯層需要重寫。團隊把「重寫」套用到了兩層，於是 CSS 也被翻譯，而翻譯必然 drift。

**這個結論已被 PoC 實證**：把 mockup `styles.css` 逐字複製進生產、頁面組件直接消費 mockup 的 class 名 —— `/overview-poc` 與 mockup 的 `.card` / `.badge` / `.page-title` computed style **逐項 byte-identical**，色彩全程 `oklch` 零翻譯。

**這個結論也被 EKP 專案佐證**：EKP 用**完全相同**的 mockup 架構（React UMD + babel-standalone CDN + `window` 全域 + 手寫 oklch `styles.css`，零 build），達到 90-95% 保真度 —— 唯一差別就是 **EKP 不翻譯 CSS，它逐字複製**。

---

## 2. 根因診斷

### 2.1 「誤會」的本質：mockup 被當成不可分割的整體

10 個 sprint 來，「可不可以複製 mockup 文件」這個問題一直在錯的顆粒度上被回答。「mockup」不是一個整體，是**兩層，可複製性相反**：

| mockup 的層 | 檔案 | 技術形態 | 能否無損複製到生產 | 正確處理 |
|------------|------|---------|-------------------|---------|
| **視覺層 / CSS** | `styles.css`（1123 行 / 251 class / oklch）| 純文字 CSS 宣告 | ✅ **可以** —— Tailwind 之後再 load 一個 `.css` 完全合法 | **逐字複製，永不翻譯** |
| **組件邏輯層** | `page-*.jsx`（UMD React + `window` 全域 + babel-standalone）| 瀏覽器即時編譯、無模組系統 | ❌ **不可以** —— 無法被 Vite/TS `import` | 重寫成 typed TSX |

- **你的訴求（「複製文件直接用」）對了一半** —— CSS 那一半本來就應該複製。
- **mockup `AGENTS.md`（「用 Tailwind/shadcn 重寫，不整合」）規則對、scope 錯** —— 「重寫」只該套組件邏輯層。
- **團隊實際做的，錯在連 CSS 一起翻譯了。**

### 2.2 那條不該存在的「CSS 翻譯管線」

生產端沒有用 mockup 的 `styles.css`，而是把它重新表述了一遍，4 道有損加工：

| # | drift 注入點 | 證據 |
|---|------------|------|
| 1 | **oklch → 用眼睛湊的 HSL** | `frontend/src/index.css:125` 註解親口寫：`oklch→HSL approximation`。mockup `--bg: oklch(0.135 0.005 260)` 被湊成 `--bg: 225 5% 13%`。oklch 與 HSL 不是等價色彩空間，每個顏色都偏。 |
| 2 | **251 個 mockup class → 每頁手工拼成 Tailwind utility** | `STYLE.md` 強制 utility-first；epic 每個 sprint 一頁手工 port，無像素一致保證 |
| 3 | **shadcn primitive 替代** | shadcn `Card/Badge/Button` 預設 padding/radius ≠ mockup |
| 4 | **補償債** | 生產 `index.css` 同時養 shadcn 系（`--background`）+ mockup 系（`--bg`）兩套並行 token tree；外加 `html{font-size:13px}` hack（為了讓 Tailwind rem 縮放到 mockup 13px）|

每一次「重建」都重跑這條管線 → 每次重新注入 drift → 宣稱完成 → 後來審計發現不對 → 重做。**第 4 次和第 1 次一樣 drift，因為 drift 在方法的翻譯步驟裡，不在執行的細心程度裡。**

### 2.3 為什麼自動化 gate 沒擋住

Sprint 57.17 揭露：Tailwind v4 自 Sprint 57.7 起靜默 no-op，9 個 sprint 渲染成無樣式 HTML，而 e2e / a11y / visual-regression 全過 —— 因為它們檢查 ARIA/DOM/文字，不檢查 computed CSS。drift 偵測一直靠「用眼睛看」，subtle 的 typography/spacing 必漏。

---

## 3. 解法：4-layer 同步協定（適配本專案 Vite + Tailwind v4）

源自 EKP 的 4-layer sync protocol，適配本專案技術棧（EKP 用 Next.js；本專案用 Vite）：

| Layer | 檔案 | 做法 | drift 注入點 |
|-------|------|------|-------------|
| **1** | `reference/design-mockups/styles.css` | canonical，oklch，**設計師只改這裡** | — |
| **2** | `frontend/src/styles-mockup.css` | **Layer 1 的逐字複製**（byte-identical）；在 `main.tsx` 於 `index.css` 之後 import | **0**（一次檔案複製 = 0 注入點）|
| **3** | `frontend/src/index.css` | 瘦身：`@import "tailwindcss"` + 精簡 bridge；**退役雙 token tree + `html{font-size:13px}` hack** | — |
| **4** | `tailwind.config.ts` | 仍透過 Tailwind utility 消費的 token，bridge 由 `hsl(var(--X))` 改為 `var(--X)`（變數已含完整 `oklch()`）| — |

**組件層**：頁面 `.tsx` 直接消費 mockup class 名（`className="card"`），不重新拼成 Tailwind utility。「重寫」只套組件邏輯層（`window` 全域 → typed hooks、UMD/babel → ESM TSX、`.jsx` → strict `.tsx`）。

**5 條配套原則**（EKP 的「收得住 drift」機制）：
1. **設計保真度升為 Hard Constraint** —— 與「不可改架構」同級，違反即 STOP（本專案 CLAUDE.md 已有 Mockup-Fidelity 章節，但未升為硬停）
2. **fundamental drift → 先換方法、再重建** —— 不要用同一套會 drift 的方法 redo 第 4 次
3. **驗證在代碼層** —— `.jsx` 與 `.tsx` 並排逐行；用眼只做最後信任閘
4. **drift 偵測 = 一行 `diff`** —— `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` 預期 0 差異；CI lint + grep guard 抓組件內寫死的 hex/oklch
5. **DESIGN_SYSTEM.md + drift incident log** —— 設計系統解析一次寫下來；每次 drift 修復記一行

### 技術可行性（已驗證）
- Tailwind v4 原生支援 `oklch()`；色彩可全程 oklch，**oklch→HSL 翻譯根本不需要發生**（unforced error）
- mockup `styles.css` 的 `:root` 預設即 dark-linear 變體 → 逐字複製後 dark mode 開箱即用
- styles-mockup.css 於 `index.css` 後載入 → 同 specificity 下 cascade order 勝出 → mockup class 生效
- 唯一需調的 theme toggle：mockup CSS 用 `[data-theme]`，生產 `ThemeProvider` 用 `.dark` class —— full migration 時對齊（PoC dark-only 不受影響）

---

## 4. PoC 實證（`/overview-poc`）

### 4.1 做了什麼

在分支 `investigation/mockup-fidelity-poc`：
1. `cp reference/design-mockups/styles.css frontend/src/styles-mockup.css` —— `diff` 確認 **byte-identical 逐字複製**
2. `main.tsx` 於 `index.css` 後加 `import "./styles-mockup.css"`
3. 新建 `frontend/src/pages/overview-poc/`（index.tsx + components.tsx）—— 1:1 機械 port mockup `page-overview.jsx`，**逐字用 mockup class 名**（`card`/`badge`/`stat`/`page-head`/`grid-stats`...），fixture data 內聯為 typed const，`ui.jsx` primitives port 成本地 TSX 組件
4. routes.config 加 `/overview-poc` 路由；頁面自包 `<RequireAuth><AppShellV2>`（用預設 main = mockup `.content` 的忠實複製）
5. `tsc --noEmit` 乾淨

**兩輪施作（誠實紀錄）**：第一輪 agent 一次性 port → 內容區僅約 **80%**：CSS class 樣式精確，但 ① 19 處 copy 字串用「猜」的（如卡片標題「Active loops」應為「Active agent loops」）② 外層誤用 `fullBleed` 移除了 padding，KPI 卡片寬 284 vs mockup 268。第二輪「逐字轉錄」修正：copy 全部對齊 mockup `i18n.jsx`、移除 `fullBleed` 改用 `AppShellV2` 預設 main（其 `pt-24/px-28/pb-60` 正是 mockup `.content` 的忠實複製）→ 內容區達 **~95-98%**。**這一輪修正本身印證報告核心論點：CSS 層複製即零 drift，但「組件層」port 仍需仔細施作 + 程式化驗證迭代。**

### 4.2 驗證結果（Playwright 雙服務，第二輪修正後）

**量化 A — CSS class computed style 逐項 byte-identical**（mockup :8080 vs PoC :3007/overview-poc）：

| 屬性 | Mockup | PoC | |
|------|--------|-----|---|
| `.card` background / border / radius | `oklch(0.165…)` / `oklch(0.26…)` / `12px` | 完全相同 | ✅ |
| `.badge` background / color / font / padding | `oklch(0.72 0.16 155 / 0.12)` / … / `10.5px` / `1px 6px` | 完全相同 | ✅ |
| `.stat` / `.card-head` / `.card-title` / `.page-sub` / `.route-pill` font·padding·radius·gap | （8 種元素逐項）| 完全相同 | ✅ |
| `--bg` root var | `oklch(0.135 0.005 260)` | `oklch(0.135 0.005 260)` | ✅ |

**量化 B — 版面尺寸逐項 byte-identical**（第二輪 layout 修正後）：

| 量測 | Mockup | PoC | |
|------|--------|-----|---|
| 內容區 width / padding | `1208` / `24px 28px 60px` | `1208` / `24px 28px 60px` | ✅ |
| `.stat` KPI 卡片寬 ×4 | `268, 268, 268, 268` | `268, 268, 268, 268` | ✅ |
| 第一張 `.card` 寬 | `638` | `638` | ✅ |
| `.page-head` 寬 | `1107` | `1107` | ✅ |

→ PoC 的 `--bg` 是 mockup 精確 oklch 原值，**不是**舊方法眼湊的 `225 5% 13%` HSL。色彩全程 oklch。
→ CSS class 樣式 byte-identical 是**演繹必然**（styles-mockup.css 與 styles.css byte-identical → 同 class = 同渲染）；版面尺寸 byte-identical 來自第二輪移除 `fullBleed` 的修正。

**視覺 — 截圖比對**（見 `screenshots/final-*.png`）：
`final-mockup-content.png` vs `final-poc-content.png` —— 文案 / KPI / 卡片 / 圖表 / 版面寬度視覺上不可區分；僅存差異 = 即時時鐘（`new Date()`，預期）+ sub-pixel 文字渲染。內容區判定 **~95-98%**。

### 4.3 PoC 證明了什麼（與沒證明什麼）

**✅ 證實**：

| 命題 | 結果 |
|------|------|
| 逐字複製 mockup CSS 在 Vite + Tailwind v4 技術可行 | ✅ |
| 生產組件可直接消費 mockup 251 個 class | ✅ |
| 色彩全程 oklch、不需翻譯成 HSL | ✅ |
| CSS class 樣式 = byte-identical（非「接近」）| ✅ |
| 版面尺寸可達 byte-identical | ✅（第二輪修正後）|
| 頁面內容區整體可達 ~95-98% | ✅ |

**⚠️ 範圍界線（PoC 沒有涵蓋的，必須誠實標明）**：

| 項 | 狀態 |
|----|------|
| 外殼層（sidebar + topbar）| PoC 用生產 `AppShellV2`，**未**與 mockup `shell.jsx` 逐項比對 —— 獨立工作項 |
| 組件層 port 不會「自動」到位 | 第一輪即有 copy + layout drift；需仔細逐字轉錄 + 程式化量測迭代（如本 PoC 第二輪所示）|
| 真實 data / i18n 接線 | PoC 用 fixture data + 內聯英文字串；正式頁仍需接 API + i18n |

---

## 5. 遷移計劃（把 PoC 變成全專案方法）

PoC 是分支實驗，不直接 merge。正式採用建議按以下順序，走標準 sprint 流程：

### Phase 1 — Foundation 切換（1 個 sprint）
- Layer 2：`styles-mockup.css` 逐字複製 + `main.tsx` 接線
- Layer 3：`index.css` 瘦身 —— 退役 mockup 系眼湊 HSL token、退役 `html{font-size:13px}` hack
- Layer 4：`tailwind.config.ts` bridge `hsl(var(--X))` → `var(--X)`；解決 `--primary` 等 token 碰撞
- theme toggle 對齊（`ThemeProvider` 改 toggle `[data-theme]` 或保留 `.dark` 並調 mockup selector）
- CI：加 `diff` guard + grep guard（抓組件內寫死色值）
- ⚠️ 此 sprint 會短暫影響現有 13 個 active 頁（token 碰撞）—— 需同 sprint 內逐頁 re-point 或接受過渡期

### Phase 2 — 逐頁 re-point（多 sprint，但每頁成本大幅塌縮）
- 既有 ~10 個「已重建」頁 + ~14 個 PROP stub + 仍 drift 頁，逐一改成消費 mockup class
- 每頁工作量 = 只剩「組件邏輯層」（接 API、i18n、typed props）—— CSS 免費
- Sprint 57.22 audit 估的 ~297 小時，大部分是 CSS 翻譯；CSS 改成複製後此估值大幅下修

### Phase 3 — 制度化
- `AGENTS.md` 寫死「重寫」scope 只含組件邏輯層、CSS 是「複製」
- 建 `DESIGN_SYSTEM.md`（251 class catalogue，dev API reference）
- 建 drift incident log + anti-pattern 目錄
- 設計保真度升為 CLAUDE.md Hard Constraint（違反即 STOP）

---

## 6. 風險與誠實caveat

| 項 | 說明 |
|----|------|
| **全域 CSS 載入影響所有頁** | styles-mockup.css 有全域 reset（`*`/`body`/`button`）+ 251 class。一旦全域載入，所有頁都受影響 —— 這是**預期的**（它成為 foundation），但 Phase 1 切換期間既有頁會有 token 碰撞，需同 sprint 處理 |
| **`--primary` 等 token 碰撞** | mockup `--primary` 是 oklch、生產 index.css 是 HSL；同名碰撞會讓 `hsl(var(--primary))` bridge 失效。Phase 1 必須一併解決 bridge |
| **shell 仍是獨立議題** | PoC 證明的是「頁面內容層」。`AppShellV2` 與 mockup `shell.jsx` 的差異是另一條 drift（Sprint 57.20 已重建過 shell，但未必 1:1）|
| **PoC ≠ 生產就緒** | PoC 用 fixture data、copy 有小差異。正式遷移每頁仍需做「組件邏輯層」重寫（接真 API、正確 i18n）|
| **theme variant / density** | mockup 有 4 個 theme variant + 3 density；生產目前只用 linear 預設。full migration 需決定保留哪些 |

---

## 7. 建議的下一步

1. **採納 4-layer 協定**，開一個「Foundation 切換」sprint（Phase 1），走標準 plan→checklist→code 流程
2. **修正 `AGENTS.md`** 的「重寫」scope 定義 —— 這是杜絕誤會重演的關鍵一行
3. **PoC 分支保留** 作為 Phase 1 的參考實作（`investigation/mockup-fidelity-poc`）
4. 重新評估 Sprint 57.22 audit 的 ~297 小時估值 —— CSS 改複製後大幅下修
5. 既有「已宣稱 PARITY」的頁（overview/cost/sla/auth）也建議在 Phase 2 一併 re-point —— 它們目前是「眼湊 HSL 翻譯」版，computed style 與 mockup 仍有偏差

---

## 附錄：EKP 參考專案交叉驗證

EKP 是另一個用**完全相同 mockup 架構**的 Claude Code 開發專案（React UMD + babel-standalone CDN + `window` 全域 + 手寫 oklch `styles.css`，零 build），達到 **90-95%+ 保真度**。其成功關鍵與本報告解法完全一致：

- styles.css 逐字複製進 `frontend/app/styles-mockup.css`，Tailwind preflight 後 load
- 色彩全程 oklch，從不轉 HSL
- 組件直接消費 mockup class 名
- 4-layer sync protocol（寫在 EKP `DESIGN_SYSTEM.md §7`）
- drift 偵測 = 一行 `diff`
- EKP 中途也出過嚴重 drift（W20 4 頁 fundamental drift 且通過全部自動 gate）—— 它能收住，靠的是「fundamental drift → 先換方法再重建」+ 代碼層驗證 + oklch grep guard + drift incident log

EKP 證明：**差別不在 mockup 本身，在消費方法。** 本專案的 mockup 沒有「比較難處理」—— 它和 EKP 的一模一樣。

---

**調查結論**：3 項任務完成。V2 後端健康（Task 1）；前端 epic 走了 10 sprint 仍只完成約 1/3（Task 2）；根因是 CSS 翻譯管線、解法是逐字複製 + 4-layer 協定、PoC 已實證 byte-identical 保真（Task 3）。
