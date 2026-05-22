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

**維護責任**：每個 frontend sprint kickoff 必讀本檔；Code reviewer 以 DoD 5 條 + 鐵律 7 條為 PR 強制檢查項。
