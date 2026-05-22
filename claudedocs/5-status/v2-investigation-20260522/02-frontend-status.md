# 前端架構/頁面/設計系統重構狀況調查報告（Task 2）

**調查日期**: 2026-05-22
**調查者**: AI 助手（Claude Opus 4.7）
**範圍**: 前端架構、頁面清單與狀態、設計系統三源、mockup-fidelity epic 57.18-57.27
**方法**: 2 個 sub-agent 並行分析設計系統三源 + epic 軌跡 + 7 份 DRIFT-REPORT + routes.config 驗證
**狀態**: ✅ 完成

> 本報告是 3 份調查報告的第 2 份。第 1 份 = V2 重構整體狀況；第 3 份 = mockup 一致性根因（含 PoC）。

---

## 1. 執行摘要（先看這段）

前端從 Phase 57 才正式開展，目前狀況可以一句話總結：**頁面開發本身在推進，但「跟 mockup 一致」這件事走了 10 個 sprint 仍只完成約 1/3，而且方法論換了 4 次才找到能用的。**

關鍵數字：
- **31 條路由**：13 條 active（真頁面）、14 條 PROP stub（只顯示 ComingSoonPlaceholder）、4 條 DRAFT（連 route 都沒生成）
- **真正達到 mockup「parity」的頁面 ≈ 10 個**（7 條 auth + cost-dashboard + sla-dashboard + overview），全部靠 Sprint 57.23+ 的「strict 逐行重建」方法
- **Sprint 57.22 audit**：41 條路由全面審計，當時只有 3 個 ship 頁 ≥70%；epic 總估 **~297 小時 / 10 個 sprint**，目前才走約 4 個
- **多次重做**：`/overview` 被做了 3 次、`/cost-dashboard` 約 4 次、`/chat-v2` 3 次

**最重要的發現（為 Task 3 鋪路）**：mockup 是一個**刻意設計成「零 build」的瀏覽器直跑原型**，而 mockup 自己的 `AGENTS.md` 文件明確寫著「**不直接整合，要重寫**」。但你一直要求的是「複製文件再在其上開發」。這兩者之間有一個**根本矛盾** —— 這就是你擔心的「誤會」，Task 3 會完整拆解。

---

## 2. 前端架構總覽

`frontend/src/` 結構：

| 目錄 | 內容 |
|------|------|
| `pages/` | 28 個頁面目錄（對應 routes.config 的 active + PROP 頁）|
| `features/` | 18 個 feature 模組（資料 hooks / services / types / 組件）|
| `components/` | 共用組件：`AppShellV2.tsx`（外殼）、`Sidebar.tsx`、`AuthShell.tsx`、`ThemeProvider.tsx`、`topbar/`、`ui/`（shadcn primitives）、`charts/`、`shared/` |
| `routes.config.ts` | **單一路由註冊表**（31 條，6 分類）— App.tsx 與 Sidebar.tsx 都消費它 |
| `i18n/` | en + zh-TW 雙語 |
| `store/` + `stores/` | Zustand（注意：有兩個 store 目錄）|

技術棧：React 18 + TypeScript（strict）+ Vite + **Tailwind CSS v4** + shadcn/ui primitives + TanStack Query + Zustand。

**⚠️ 偵察發現的目錄重複（建議後續清理，非本次重點）**：`features/` 內出現疑似重複命名 —— `state` vs `state-mgmt`、`subagent` vs `subagents`、`orchestrator-loop` vs `loops`；`src/` 下 `store/` 與 `stores/` 並存。這觸及反模式 AP-3（跨目錄散落）/ AP-11（命名遺留），值得未來一個小 sprint 收斂，但與 mockup 一致性問題無直接關係。

---

## 3. 頁面清單與狀態（routes.config.ts 31 條）

| 分類 | 數量 | active（真頁面）| PROP stub | DRAFT |
|------|------|----------------|-----------|-------|
| operations | 10 | overview, chat-v2, orchestrator, subagents, loop-debug, memory, state-inspector | compaction, jit-retrieval, subagent-tree | — |
| business | 1 | — | incidents | — |
| governance | 5 | governance, verification | redaction, error-policy | audit-log |
| observability | 5 | cost-dashboard, sla-dashboard | cache-manager, sse, devui | — |
| resources | 3 | — | models, tools | feature-flags |
| admin | 7 | admin-tenants, tenant-settings | tenant-onboarding, pricing, rbac | profile, mfa |
| **合計** | **31** | **13 active** | **14 PROP** | **4 DRAFT** |

> auth 路由（`/auth/login`、`/auth/callback` 等）不在此註冊表，用 `AuthShell` 直接在 App.tsx 接線。

**三態約定**（routes.config 檔頭 + design/operator-portal/AGENTS.md §5）：
- `active=true`：完整實作已 ship
- `active=true + proposed=true`（**PROP**）：後端 ABC 存在，前端 stub 只渲染 `ComingSoonPlaceholder`，等後續 sprint 真正 port
- `active=false + designed=true`（**DRAFT**）：未來條目，sidebar 顯示 DRAFT badge，不生成 route

**現實**：14 個 PROP 頁基本是佔位（Sprint 57.22 audit 證實「~13 條路由評分 0%」）。真正有內容的是 13 條 active —— 但 13 條裡只有約 4 條（overview / cost-dashboard / sla-dashboard / chat-v2）經過 57.23+ 重建達 parity，其餘 9 條（orchestrator / subagents / loop-debug / memory / state-inspector / governance / verification / admin-tenants / tenant-settings）是 mockup 進專案前或 57.19 期間開發的，**仍處於 drift 狀態**。

---

## 4. 設計系統三源

| 來源 | 角色 | 技術形態 |
|------|------|---------|
| **`reference/design-mockups/`** | ⭐ canonical 視覺真相來源（24 檔）| **零 build 瀏覽器直跑原型** |
| `design/operator-portal/` | Sprint 57.18 的 `cp` 快照（byte-identical）+ 多 1 份 `INTEGRATION-LOG.md` | 同上；CLAUDE.md 標其「權威性低於 reference/」|
| `frontend/` 生產設計系統 | 實際 ship 的 token | Tailwind v4 + `tailwind.config.ts` + `index.css` + `STYLE.md` |

### 4.1 mockup 的技術形態（關鍵）

`reference/design-mockups/` 是一個**刻意設計成無建置步驟的原型**：
- `index.html` 從 CDN 載入 React 18 UMD + ReactDOM + `@babel/standalone@7.29.0`，再用 `<script type="text/babel">` 載入 17 個 `.jsx`，**瀏覽器即時編譯 JSX**
- 跨檔案連結靠 `window` 全域變數（每個 `.jsx` 結尾 `Object.assign(window, {Component})`）
- CSS = 單一手寫 `styles.css`（~40KB），用 **`oklch()` 色彩 + CSS custom properties**；`:root` 定義 `--primary: oklch(0.62 0.16 250)`、7 個語義 token、4 個 risk level、density 變數；3 個 dark variant 透過 `[data-theme][data-variant]` 切換
- **完全沒有 Tailwind、沒有 npm、沒有 bundler**

### 4.2 mockup 自己的文件說「不要整合，要重寫」⚠️

這是 Task 3 的核心線索。mockup 的 3 份說明文件**明確指示重寫**：

- **`AGENTS.md §10 Q4`**：「本 portal **不直接整合**。它是設計參考。production frontend 工程師看本 portal 的視覺，自己用 Vite + TS + Tailwind / shadcn 在 repo `frontend/src/pages/` **重寫**。」
- **`README.md`「選項 A — 純設計參考（推薦）」**：「AI 助手實作 V2 frontend 頁面時可以直接打開 `index.html` 在瀏覽器看設計，再對照 `routes.config.ts` 補實作。」
- **`AGENTS.md §3`** 技術鐵律：「無 build step…**不要**引入 npm / Vite / Webpack」—— mockup 刻意與生產工具鏈不相容。

→ 換句話說：**mockup 從設計上就被定位為「視覺規格」，不是「可複製的代碼基底」。** 這與「複製文件再開發」的訴求直接衝突。

### 4.3 生產 token 系統

`frontend/` 用 Tailwind CSS v4。`tailwind.config.ts` 把顏色定義成 `hsl(var(--X))` 橋接；實際值在 `index.css` 的 `:root`/`.dark` 以 **HSL 三元組**寫死。Sprint 57.18 加入 7 語義 + 4 risk token；57.20 加 mockup layout token tree + density。`STYLE.md` 規定 utility-first、禁 inline style（lint 強制）、除 `index.css` 外不寫自訂 CSS。

---

## 5. mockup → 生產 的「翻譯鏈」與 drift 注入點

```
mockup styles.css (oklch)
  → 手動 HSL 近似  ← drift 點 1
  → index.css :root/.dark (HSL 三元組)
  → tailwind.config.ts hsl(var(--X)) 橋接
  → STYLE.md token 表
  → 手寫 .tsx Tailwind classes  ← drift 點 2、3
```

**4 個 drift 注入點**：
1. **oklch → HSL 近似**：兩者不是等價色彩空間；index.css 註解自己寫「approximation」。`oklch(0.62 0.16 250)` → `hsl(...)` 是**用眼睛湊的，不是計算的**。
2. **逐頁手工重寫**：每頁在 TSX 手動重建，spacing / radius / shadow 重新打成 Tailwind class，**沒有任何機制保證像素一致**。
3. **shadcn primitive 替代**：`STYLE.md §1` 偏好 shadcn `Button/Card/Tabs`，其預設值與 mockup 的 padding/radius 不同。
4. **token 表 staleness**：`STYLE.md §4` 還列 `Inter`/`JetBrains Mono`，但 config 已 ship `Geist`；risk 配色有兩套互相矛盾的版本。

**直接複用 mockup 樣式可行嗎？目前判定不可行**，技術阻礙：
- CSS 取向不相容（手寫 CSS + oklch vs Tailwind v4 JIT；`styles.css` 從不被 import）
- 模組系統不相容（`window` 全域 + babel-standalone vs Vite ESM；`.jsx` 無法被 `import`）
- 無建置產物（mockup 刻意無 package.json）
- 型別（untyped JSX vs strict TS）

**但有部分機械化的勝算**（Task 3 會展開）：oklch→HSL **可以用 culori 精確計算**而非用眼睛湊，消除 drift 點 1；`styles.css :root` 的 token 值可作為 codegen 單一來源餵進 `index.css`。

---

## 6. mockup-fidelity epic 57.18-57.27 軌跡

10 個 sprint 換了 **4 種方法論**，每種前一種失敗才換：

| Sprint | 目標 | 方法論 | 觸及頁 | parity 判定 | ratio |
|--------|------|--------|--------|------------|-------|
| 57.18 | epic 起步：cp mockup→`design/operator-portal/`、加 token、6 分類路由、18 PROP stub | **基礎建設**（cp 作參考，非 ship）| 0 | N/A | 1.10 |
| 57.19 | Round 1：port Operations 4 頁 + topbar | **mockup-port（fixture 翻譯）** + code-level drift 審計 | 7 | 僅 code-level；視覺延後 | 0.56 |
| 57.20 | Tier-1 retrofit 5 頁 | **Day 0 計劃中止** → 改 shell rewrite + token migration | 2（overview/chat-v2）| 部分 | ~0.50 |
| 57.21 | chat-v2 Full-Fidelity Phase-1 | **結構重寫**（Turn data model + 9 組件）| 1 | 結構 parity；cosmetic 延後 | 1.20 |
| 57.22 | 41 路由全面審計 | **純審計** | 0 | N/A — 產出 10-sprint roadmap | 0.51 |
| 57.23 | Auth Round 2 — 6 P0 路由 | **strict 逐行重建**（`mockup-ref Lxx-yy` 註解）| 7+AuthShell | PARITY（code-level）| 0.59 |
| 57.24 v2 | cost-dashboard 重建 | **v1 計劃 Day 1 中止** → strict 重建 + 抽 7 primitives | 1 | PARITY（code-level）| 1.19 |
| 57.25 | sla-dashboard 重建 | strict 重建，複用 7 primitives | 1 | PARITY（code-level）| 0.88 |
| 57.26 | foundation token 校正（13px 字、sidebar、bg、radius）| **全域 CSS 修正** 22 路由 | 22（僅 foundation）| 0 regression | 0.91 |
| 57.27 | overview 重建 — 9 widgets | strict 重建，複用 primitives | 1 | PARITY（**Playwright 驗證**）| ~0.95 |

### 方法論演進（4 階段，每階段因前者失敗而轉換）

1. **57.18「複製作參考」**：的確複製了 mockup 檔案 —— 但放進 `design/operator-portal/` 當唯讀參考，從不是可 ship 的代碼。
2. **57.19-57.20「port / token-migrate」**：把 mockup JSX 翻譯成生產組件，或只換 Tailwind token。57.20 計劃 Day 0 就中止。
3. **57.22「停下來審計」**：ad-hoc port 產出不一致後，凍結所有 coding，做 41 路由全面審計 —— 發現「cosmetic retrofit」結構上不可行，多數頁需重建。
4. **57.23-57.27「strict 逐行重建」**：最終固定下來的方法 —— 每頁從零重建、加 `mockup-ref Lxx-yy` 註解、抽共用 primitive、用 BackendGapBanner 誠實標示。57.24 的 retrofit-式 v1 計劃 Day 1 中止，再次證實 retrofit 已死。

---

## 7. 7 份 DRIFT 報告結論

1. **57.19 DRIFT-REPORT**：9 個既有頁審計 → 11 cosmetic + 7 structural + 1 functional drift；估 ~17.5 hr retrofit
2. **57.20 ROUND-2**：7 個 57.19 產出繼承新 shell OK，但 **16 條頁內 drift 仍在** → 延後 Round-2
3. **57.21 PHASE-1**：chat-v2 結構 parity 達成（9 項）；**12 項 Phase-2 延後**；揭露 3 個 silent paper-vs-runtime 失敗（theme/font/layout 從未真正渲染）
4. **57.23 AUTH-ROUND-2**：12 個頁面狀態全 PARITY 或 COSMETIC、0 structural —— 但判定基於 *code-level 審計*，Playwright 卡住
5. **57.24 RETROFIT-TIER-1**：Sprint **Day 1 中止** —— 5 個「cosmetic retrofit」目標中 3 個其實是 STRUCTURAL；只 cost-dashboard 重建達 PARITY
6. **57.25 SLA DRIFT**：6 個 widget group 全重建 → PARITY（code-level）；連續第 4 個 sprint Playwright 卡住
7. **57.27 OVERVIEW DRIFT**：9 widgets → PARITY（**這次 Playwright 驗證**）；17 條 drift ID 關閉；1 條誠實分歧（ActiveLoopsCard 後端 404）

---

## 8. 現況評估

**已達 parity（~10 頁）**：7 條 Auth 路由 + AuthShell、cost-dashboard、sla-dashboard、overview —— 全靠 strict rebuild。**但只有 overview 經 Playwright 視覺驗證**，其餘是 code-level parity（Playwright MCP 連續 4+ sprint 卡住）。57.26 修好了全 22 路由的共用 foundation。

**仍 drift（~25+ 條 P0 路由）**：chat-v2 Phase-2 widgets、governance、redaction、rbac、tenant-settings 6-tab、models、tools、admin 多頁 —— 10-sprint roadmap 才走約 4 個。

**為何走了 10 個 sprint**：
1. mockup 是 `.jsx` demo，**不是可跑的生產代碼**，不能「直接複製」，必須在 typed TSX 重新實作（含真 data hooks / i18n / 多租戶）
2. 早期用便宜的 port/token-migrate 方法，留下結構性 drift，必須重做
3. 57.22 前沒有前置審計，前 4 個 sprint「盲做」
4. silent paper-vs-runtime 落差（57.21 發現 theme/font/layout 從未真正渲染卻已宣稱 ship）
5. Playwright 驗證壞了 4+ sprint，「parity」只在 code-level 宣稱，drift 得以溜過

---

## 9. 通往 Task 3 的橋接

Task 2 盤點出一個**結構性矛盾**，Task 3 將完整診斷並提解法：

> **你的訴求**：「複製 mockup 文件 → 在其上繼續開發」
> **mockup 自己的 AGENTS.md**：「不直接整合，要用 Tailwind/shadcn 重寫」
> **團隊實際做的**：照 AGENTS.md 重寫 → 翻譯鏈 4 個 drift 點 → 每頁手工、每 sprint 一頁、做了又發現不對再重做

這三者沒有對齊。Task 3 會回答：
- 這個矛盾的本質是什麼？是技術限制、流程問題、還是溝通誤會？
- 「複製文件直接用」在技術上能不能成立？需要付出什麼代價？
- 有沒有第三條路（介於「純手工翻譯」與「直接複製」之間）能大幅消除 drift？
- 用一個 PoC 頁面實證新方法可行。

---

**下一步**：Task 3 — mockup 一致性問題根因診斷 + 解法 + PoC 驗證。
