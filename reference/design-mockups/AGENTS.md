# AGENTS.md — 給未來 AI 助手的開發守則

> **本檔目的**：你（接手的 AI 助手）打開這個資料夾要做事之前，必讀。可以省下 30 分鐘的探索 + 避免常見的「不知道為什麼這樣設計」的誤改。

---

## 1. 你正在看的是什麼

這是 **IPA Platform V2 operator portal** 的 hi-fi 互動原型，不是 production frontend。

- **不是** `frontend/src/` 下的 React + Vite production code
- **是** 設計階段的 prototype，給 stakeholder 看「V2 的 operator portal 長什麼樣」
- 對應 GitHub repo：`laitim2001/ai-semantic-kernel-framework-project`
- production frontend 在該 repo 的 `frontend/` 目錄

兩者關係：本 portal 設計 → stakeholder 通過 → 才會挑頁面實作到 production `frontend/`。

---

## 2. 開始任何任務前必讀順序

1. **本檔（AGENTS.md）**
2. **DESIGN_RATIONALE.md** ← 每個 menu 項為什麼存在
3. **README.md** ← 檔案結構
4. **shell.jsx 的 ROUTES 陣列** ← 看現在所有 menu 項
5.（若涉及對齊 V2 規格）repo 的 `frontend/src/routes.config.ts` 與 `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md`

---

## 3. 技術棧鐵律（不要違反）

| 規則 | 為什麼 |
|---|---|
| **無 build step**：純 HTML + Babel Standalone + React UMD | 設計原型應該 1 秒打開、0 dependency。**不要**引入 npm / Vite / Webpack |
| **`.jsx` 用 `<script type="text/babel">` 載入** | 見 index.html |
| 每個 `.jsx` 結尾必須 `Object.assign(window, { ComponentName })` | Babel script 不共享 scope；元件必須掛 window 才能跨檔使用 |
| 全域 styles 物件**必須命名**，禁止 `const styles = {...}` | 多個 script 都用 `styles` 會撞名 → 用 `chatStyles` / `governanceStyles` 等 |
| 單檔不超過 1000 行 | 超過就拆 `page-platform.jsx` / `page-platform2.jsx` |
| React 版本鎖死 18.3.1 + Babel 7.29.0 + integrity hash | 見 index.html，**禁止** 改 unpinned |

---

## 4. 新增 / 修改頁面 SOP

### 4.1 新增一個 menu 項

1. **先驗證合理性**：到 repo 的 `routes.config.ts` 或 `01-eleven-categories-spec.md` 找對應條目
   - 如果 V2 routes 內有 → 不加 `proposed`，直接 `active: true`
   - 如果只有後端 spec 有對應 ABC → 加 `proposed: true`
   - 如果都沒有 → 屬於「設計擴充」，**在 DESIGN_RATIONALE.md 寫清楚理由**才能加
2. **在 `shell.jsx` 的 `ROUTES` 陣列加一行**，包含 id / path / nameKey / icon / category / active / proposed?
3. **在 `i18n.jsx` 加翻譯**：`nav.<key>` + `page.<key>.title`（en + zh）
4. **在 `shell.jsx` 的 `ID_TO_KEY` 加 mapping**（用於 breadcrumb）
5. **建立元件**：放在現有 `page-*.jsx` 內，或新增 `page-*.jsx` 後在 `index.html` 加 `<script>` 載入
6. **在 `app.jsx` 元件路由表加 case**
7. **在 DESIGN_RATIONALE.md 對應 category 表內加一行**

### 4.2 修改現有頁面

- 動 menu 標籤前先想：是 V2 routes 來的？還是 PROP？看 DESIGN_RATIONALE.md
- 動 category 分類前先看 DESIGN_RATIONALE.md §「V2 三類 vs 本 portal 六類的重新分類理由」
- 動樣式前先看 `styles.css` 有沒有 token 可用（不要 hardcode 顏色）

### 4.3 刪除頁面（**慎重**）

⚠️ **預設不刪**。本 portal 的設計理念就是「呈現 12 範疇的完整 operator 視角」。

要刪只有 3 種情況：
1. 該 menu 項既不在 V2 routes、也不在 11+1 範疇 spec、且 DESIGN_RATIONALE.md 沒寫保留理由 → 真正的 V1 殘留
2. Product owner 明確要求拿掉
3. 兩個頁面職責重複合併

刪除時要做：
- `shell.jsx` ROUTES 移除條目
- `app.jsx` 元件路由 case 移除
- 對應 `page-*.jsx` 元件移除（並從 `index.html` 拿掉 `<script>` 如果整檔不再用）
- `i18n.jsx` 翻譯移除
- `shell.jsx` `ID_TO_KEY` 移除
- DESIGN_RATIONALE.md 對應表移除
- 變更歷史寫一筆

---

## 5. 三種狀態旗標的正確用法

```js
// 1. V2 ship target，已完工
{ id: "chat-v2", ..., active: true }

// 2. V2 範疇 spec 有對應，frontend 還沒 ship；設計先行
{ id: "orchestrator", ..., active: true, proposed: true }

// 3. V2 routes.config.ts 標 active=false，本 portal 先設計
{ id: "feature-flags", ..., active: false, designed: true }

// 4. 純佔位，不可點
{ id: "future-thing", ..., active: false }  // 會渲染 SOON badge + disabled
```

`proposed` 與 `designed` **意義不同**：
- `proposed` = 「我們建議加進 V2 routes」（從範疇 spec 推導）
- `designed` = 「V2 已列在 routes.config.ts 但 active=false」（先把 UI 畫好）

---

## 6. i18n 守則

- **所有可見文字** 都過 `t()` 函式
- key 命名：`nav.<id>` / `page.<key>.title` / `page.<key>.<section>`
- 兩語言要同步加（en + zh）；漏掉會 fallback 到 key 本身露出

---

## 7. 樣式守則

- `styles.css` 內 design tokens 在 `:root` 與 `[data-theme="dark"]` 區塊
- 顏色一律 `var(--xxx)` 或 `oklch(from var(--xxx) ...)` 
- spacing 用 `var(--space-N)` 或固定 4 / 8 / 12 / 14
- 圓角用 `var(--radius)`；prop 徽章 / draft 徽章請複用 `shell.jsx` 內現有寫法
- **禁止**：emoji（除非用戶明確要）、漸層背景、emoji icon、hand-drawn SVG

---

## 8. 對齊 V2 規格的對應索引

要查某個範疇對應哪個頁面，看 DESIGN_RATIONALE.md。要查某個頁面對應哪個範疇 spec section，反向也看那檔。

**主要對應**：

| V2 範疇 | 對應 menu 項 |
|---|---|
| 跨範疇 landing | overview （跨切 12 範疇的閤讀式 dashboard）|
| 範疇 1 Orchestrator Loop | orchestrator, loop-debug, sse |
| 範疇 2 Tool Layer | tools |
| 範疇 3 Memory | memory |
| 範疇 4 Context Management | compaction, jit-retrieval, cache-manager |
| 範疇 5 Prompt Construction | （未對應，內部組件） |
| 範疇 6 Output Parsing | （未對應，內部組件） |
| 範疇 7 State Management | state-inspector |
| 範疇 8 Error Handling | error-policy |
| 範疇 9 Guardrails & Safety | redaction, rbac |
| 範疇 10 Verification Loops | verification |
| 範疇 11 Subagent Orchestration | subagents, subagent-tree |
| 範疇 12 Observability | sla-dashboard, cost-dashboard, devui |
| §HITL 中央化 | governance |
| §Business Tools（08b spec） | incidents + 5 domain-* |
| Tenant / Identity / Audit | admin-tenants, tenant-settings, tenant-onboarding, audit-log, profile, mfa, pricing |
| Auth flows | auth-login, auth-callback, auth-dev, auth-register, auth-invite, auth-mfa, auth-expired （獨立 AuthShell，不進 Sidebar）|
| Topbar overlays | CommandPalette ⋘K, NotificationsPanel, UserMenu （mount 在 App 根，不是 menu 項）|
| Feature flags | feature-flags |
| LLM Adapter | models |

---

## 9. 用戶不要的事情（避雷）

從歷次對話歸納出的明確「不要做」：

- **不要** 把 V2 沒規劃 / 沒對應的頁面強塞（例如 V1 的 visual workflow editor）
- **不要** 把現有 PROP 頁面當垃圾刪—它們是設計擴充，有保留理由（見 DESIGN_RATIONALE.md）
- **不要** 提議引入 npm / build pipeline
- **不要** 自作主張改 category 分類

---

## 10. 你常會被問到的問題與標準答案

**Q：為什麼有些頁面在 V2 routes.config.ts 沒列卻在 menu？**
A：見 DESIGN_RATIONALE.md §設計哲學。本 portal 不只展示 V2 第一階段 ship 範圍，而是把 12 範疇 spec 的 ABC 都實體化為 operator 視角頁面。

**Q：為什麼 category 跟 V2 不一樣？**
A：見 DESIGN_RATIONALE.md §「V2 三類 vs 本 portal 六類」。基於 operator daily workflow + 角色職責分離。

**Q：用戶要新增 X 頁面，怎麼判斷該不該加？**
A：照 §4.1 SOP。先找 V2 對應，找得到照辦；找不到要在 DESIGN_RATIONALE.md 寫保留理由。

**Q：頁面要怎麼跟 production frontend 整合？**
A：本 mockup 是**兩層**，可複製性相反，整合方式也不同：

| mockup 的層 | 檔案 | 整合到 production 的方式 |
|------------|------|------------------------|
| **視覺層 / CSS** | `styles.css`（oklch design tokens + 所有 class） | **逐字複製（verbatim）** 進 production `frontend/src/styles-mockup.css`，**byte-identical，永不翻譯** |
| **組件邏輯層** | `page-*.jsx`（React UMD + `window` 全域 + babel-standalone） | **重寫**成 typed `.tsx`（接 API / typed hooks / i18n） |

→「**重寫**」這個指令**只**套用在**組件邏輯層**；CSS 層是「**複製**」，不是「重寫」。
production 工程師**不可**把 `styles.css` 翻譯成 Tailwind / shadcn —— 那個翻譯步驟必然
注入色彩與尺寸 drift，是 Sprint 57.18-57.27 重複 10 次的錯誤根源。production 頁面直接
消費 mockup class 名（`className="card"` …）、色彩全程 oklch、不做 oklch→HSL 近似。

完整 4-layer 同步協定 + 7 鐵律 + DoD 見 production repo 的
[`docs/rules-on-demand/frontend-mockup-fidelity.md`](../../docs/rules-on-demand/frontend-mockup-fidelity.md)（前端 mockup-fidelity 權威方法）。

---

## 11. 完成任務後

- 如果動了 ROUTES → 更新 DESIGN_RATIONALE.md 對應表
- 如果新增 `page-*.jsx` → 更新 README.md 檔案結構
- 如果改了開發規則 → 更新本檔
- 如果改了與 V2 spec 的對應 → 在 DESIGN_RATIONALE.md 「變更歷史」加一筆

---

## 變更歷史

- 2026-05-16：初版
- 2026-05-16（補）：加入 overview / auth-register / auth-invite / auth-mfa / auth-expired / Topbar 三個 overlay 的對應索引
- 2026-05-22：§10 重寫「跟 production 整合」Q&A —— mockup 是兩層（CSS 逐字複製 / 組件邏輯重寫），「重寫」只套用組件邏輯層；指向 `docs/rules-on-demand/frontend-mockup-fidelity.md`（align to validated mockup-fidelity method）
