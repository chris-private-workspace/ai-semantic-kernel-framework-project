---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-15-plan.md
Purpose: Sprint 57.15 plan — AD-Inline-Style-Cleanup-Sweep. Migrate the ~14 remaining `style={{}}` inline-style call sites in `frontend/src/features/**` to Tailwind utility classes (replacing hardcoded hex colours like `#666` that fail WCAG AA contrast), add a `no-inline-style` ESLint guard with documented exceptions for the genuinely-dynamic cases, re-enable the `color-contrast` axe rule in `a11y-scan.spec.ts` (now that the chat-v2 panels are clean), and regenerate the 6 visual-regression baselines (via the 57.14 `visual-baseline` workflow) since the cost-dashboard / governance / admin-tenants snapshots' colours change. Phase 57+ Frontend SaaS — mechanical refactor / a11y-hardening sprint.
Category: Frontend / a11y / DevOps (lint config)
Scope: Phase 57 / Sprint 57.15

Description:
    `frontend/src` carries 80 `style={{}}` occurrences across 14 feature
    components (Sprint 57.13 Foundation introduced the design-system layer
    `components/ui/` but the pre-existing feature pages still hand-roll inline
    styles). Two concrete problems flow from this:

      1. **a11y**: several of these inline styles hardcode low-contrast hex
         colours (`color: "#666"` on a white surface ≈ 3.5:1 — fails WCAG AA
         4.5:1 for normal text). Sprint 57.13 US-B5 added `a11y-scan.spec.ts`
         (axe scan over the gated pages) but had to ship with
         `.disableRules(["color-contrast"])` because the chat-v2 inline panels
         (`ToolCallCard` / `MessageList` / `ApprovalCard` / …) fail it. The TODO
         is named `AD-Inline-Style-Cleanup-Sweep` in 57.13's retrospective Q4
         and 57.14's retrospective Q4 (still open).
      2. **convention drift**: `STYLE.md` (Sprint 57.10) codified "Tailwind
         utility classes; no inline `style` except genuinely-dynamic values" but
         there's no lint guard, so the rule isn't enforced and these 14 files
         pre-date it.

    This is a focused mechanical-refactor sprint, not a feature sprint. Work is
    grouped:

    A. Inline-style → Tailwind migration (US-A1, US-A2) — triage every
       `style={{}}` occurrence in the 14 files into (a) **static** (a literal
       object of fixed CSS — the overwhelming majority: `padding`, `textAlign`,
       `borderBottom`, `color: "#666"`, `fontStyle`, `width: "100%"`, …) → map
       to Tailwind utility classes (compliant colour tokens for the hex ones);
       (b) **dynamic** (a value computed from props/state — `marginLeft: depth*12`
       in `SubagentTree`, `color: riskColor` in `ApprovalCard`, bar widths in
       `SLAMetricsCard`) → either map to a finite set of Tailwind classes
       (riskLevel → `text-red-700`/`text-amber-700`/`text-green-700`), or use a
       CSS custom property (`style={{ "--indent": … }}` + `pl-[var(--indent)]`),
       or — last resort — keep the inline style with an `// eslint-disable-next-line
       react/forbid-dom-props -- <reason>` and a one-line comment. Verify each
       component still renders/behaves identically (vitest unchanged; visual diff
       handled in step C).

    B. Guard + a11y re-enable (US-B1) — add `react/forbid-dom-props` (and
       `react/forbid-component-props` for component-level `style` props) to
       `frontend/eslint.config.js` set to `error` with a helpful message; the
       remaining genuinely-dynamic cases carry inline `eslint-disable` comments;
       re-enable the `color-contrast` rule in `a11y-scan.spec.ts` (drop it from
       `.disableRules([])`); update `STYLE.md` §"Inline styles" with the
       guard + the dynamic-value escape hatch + the CSS-custom-property pattern.

    C. Closeout (US-C1) — full validation sweep (npm lint + build + vitest +
       playwright) + regenerate the 6 visual-regression baselines via the 57.14
       `visual-baseline` workflow_dispatch job (the cost-dashboard /
       MonthPicker / governance / admin-tenants colours change, so the committed
       `*-chromium-linux.png` baselines must be refreshed — this is the first
       real end-to-end exercise of the 57.14 mechanism) + retrospective Q1-Q7 +
       memory snapshot + doc syncs (16-frontend-design.md timeline / sprint-workflow.md
       calibration +1 row / STYLE.md + CONVENTION.md if any / SITUATION + CLAUDE.md
       deferred post-merge) + PR.

    Deferred OUT of this sprint (explicitly): broader design-system adoption
    (replacing the hand-rolled tables/cards with `components/ui/` primitives) is
    NOT this sprint — this is the *minimal* "kill the inline styles, fix the
    contrast, add the guard" pass; if re-enabling `color-contrast` surfaces
    violations *outside* the 14 inline-style files (design-system components,
    untouched pages) those are findings → fix small ones, defer large ones with a
    NEW AD; the `AD-Lighthouse-Visual-Hard-Gate` (turn `visual-regression.spec.ts`
    + `frontend-lighthouse.yml` from advisory to required) stays a separate
    carryover.

Created: 2026-05-11 (Sprint 57.15 drafting; closes the standing carryover AD-Inline-Style-Cleanup-Sweep)
Last Modified: 2026-05-11
Status: Draft (Day 2 done — all 10 files migrated; 5 Round2 files file-level-disabled; `no-restricted-syntax` guard `error`; `color-contrast` re-enabled 8/9 routes; STYLE.md §1 updated. Day 3 = closeout + visual baseline refresh)

Modification History (newest-first):
    - 2026-05-11: Day 2 — §2.1 5 visual/a11y files migrated (ApprovalList was a no-op — already 57.9-migrated) + §2.3 5 Round2 file-level disables + US-B1 (guard / a11y color-contrast 8/9 / STYLE.md); D-DAY2-1 hotfix (ApprovalCard risk colours → `text-[#hex]` to keep approval-card.spec.ts color assertion + match §3 reference)
    - 2026-05-11: Day 1 — D-DAY1-1 scope finding (15 files / 133 `style=` attrs vs plan's 80/14); user chose (B) Tiered (10 files this sprint, 5 → NEW AD-Inline-Style-Cleanup-Sweep-Round2); see §"Day 1 scope revision"
    - 2026-05-11: Day 0 三-prong — 4 D-PRE findings (D-PRE-1 `eslint-plugin-react` not a dep → `no-restricted-syntax` selector instead; D-PRE-2/3/4 de-risk/align); see §"Day 0 三-prong drift findings" + progress.md
    - 2026-05-11: Initial creation (Sprint 57.15 — AD-Inline-Style-Cleanup-Sweep; 4 USs / Day 0-3)

Related:
    - sprint-57-14-plan.md (structural template per sprint-workflow.md §Step 1 — most recent completed sprint)
    - docs/03-implementation/agent-harness-execution/phase-57/sprint-57-14/retrospective.md (Q4 — AD-Inline-Style-Cleanup-Sweep listed still-open) + sprint-57-13/retrospective.md (Q4 — origin)
    - frontend/STYLE.md (Sprint 57.10 — codified the Tailwind-no-inline-style convention this sprint enforces) + frontend/CONVENTION.md (§10-13 design-system / a11y from 57.13)
    - frontend/tests/e2e/a11y/a11y-scan.spec.ts (the `.disableRules(["color-contrast"])` this sprint removes) + frontend/tests/e2e/visual/visual-regression.spec.ts (+ the 57.14 `visual-baseline` workflow that regenerates its 6 baselines)
    - frontend/src/components/ui/* (the design-system layer — already inline-style-clean; the migration targets only feature components)
    - .claude/rules/frontend-react.md / file-header-convention.md / sprint-workflow.md / anti-patterns-checklist.md
---

# Sprint 57.15 — AD-Inline-Style-Cleanup-Sweep（inline-style → Tailwind + a11y color-contrast 重開 + no-inline-style guard）

## Sprint Goal

把 `frontend/src/features/**` 殘留的 14 個 component（80 個 `style={{}}` call site）的 inline style 遷移到 Tailwind utility class（其中 hardcode 的低對比 hex 色——`#666` 之類在白底約 3.5:1，不過 WCAG AA 4.5:1——換成合規的 design token / Tailwind 色階）；對真正 *動態* 的少數 case（`SubagentTree` 的 `marginLeft: depth*12`、`ApprovalCard` 的 `color: riskColor`、`SLAMetricsCard` 的 bar 寬度）用「finite Tailwind class 集合 / CSS custom property / 最後手段 inline `eslint-disable` + reason」處理。加 `react/forbid-dom-props`（+ `react/forbid-component-props`）ESLint guard（`error`，附 helpful message + dynamic 逃生口）防 regression；移除 `a11y-scan.spec.ts` 的 `.disableRules(["color-contrast"])` 重開該 axe rule（chat-v2 panel 已清乾淨）；更新 `STYLE.md` §"Inline styles"。因 cost-dashboard / MonthPicker / governance / admin-tenants 這幾頁的顏色會變，本 sprint 順帶**重產 6 個 `visual-regression.spec.ts` 的 `*-chromium-linux.png` baseline**（透過 57.14 落的 `visual-baseline` workflow_dispatch job + 下載 artifact commit 進 feature branch）——這也是 57.14 機制第一次端到端跑通。

---

## Background

### 為什麼這個 sprint 存在（standing carryover）

`frontend/src` 有 80 個 `style={{}}` 散在 14 個 feature component（grep `style={{` 於 `frontend/src` 2026-05-11；數目 Day 0 三-prong 再 pin）：

| 檔案 | occurrences | 是否在 visual snapshot 內 |
|------|-------------|--------------------------|
| `features/tenant-settings/components/TenantSettingsView.tsx` | 27 | 否 |
| `features/cost-dashboard/components/CostBreakdownTable.tsx` | 14 | ✅ cost-dashboard |
| `features/tenant-settings/components/TenantSettingsEditForm.tsx` | 13 | 否 |
| `features/admin-tenants/components/TenantListTable.tsx` | 5 | ✅ admin-tenants |
| `features/chat_v2/components/ApprovalCard.tsx` | 4 | 否（chat-v2）|
| `features/sla-dashboard/components/SLAMetricsCard.tsx` | 4 | 否 |
| `features/chat_v2/components/ToolCallCard.tsx` | 3 | 否（chat-v2）|
| `features/chat_v2/components/ChatLayout.tsx` | 2 | 否（chat-v2）|
| `features/chat_v2/components/MessageList.tsx` | 2 | 否（chat-v2）|
| `features/cost-dashboard/components/MonthPicker.tsx` | 2 | ✅ cost-dashboard |
| `features/governance/components/ApprovalList.tsx` | 1 | ✅ governance |
| `features/admin-tenants/components/TenantListPagination.tsx` | 1 | ✅ admin-tenants |
| `features/admin-tenants/components/TenantListFilters.tsx` | 1 | ✅ admin-tenants |
| `features/subagent/components/SubagentTree.tsx` | 1 | 否（chat-v2 inline）|
| **合計** | **80 / 14 檔** | 7 檔影響 6 個 visual snapshot 中的 3 個（cost-dashboard / governance / admin-tenants）|

> CLAUDE.md 的 carryover 列表（`SubagentTree`/`TenantSettingsView`/`TenantList{Pagination,Table,Filters}`/`ChatLayout`/`SLAMetricsCard`/`MonthPicker`/`CostBreakdownTable`/`MessageList`/`ApprovalCard`/`ToolCallCard`+admin-tenants index）是近似值；實際 scope = Day 0 三-prong 時 `grep -rn "style={{" frontend/src` 命中的全部檔案（目前 14，含 carryover 沒列的 `TenantSettingsEditForm` + governance `ApprovalList`；不含 `pages/AdminTenantsPage` — grep 沒命中）。`frontend/src/components/ui/`（57.13 設計系統層）已 inline-style-clean，不在 scope。

兩個具體痛點：
1. **a11y**：`a11y-scan.spec.ts`（57.13 US-B5）必須 ship 帶 `.disableRules(["color-contrast"])`（comment 寫明因 chat-v2 inline panel 的 hardcode hex 不過 WCAG AA contrast）。所有結構性 rule（aria / labels / roles / focus）是開的，只 color-contrast 關著——這是 57.13 + 57.14 retrospective Q4 列的 `AD-Inline-Style-Cleanup-Sweep`。
2. **convention drift**：`STYLE.md`（Sprint 57.10）已 codify「Tailwind utility class；除真正動態值外不用 inline `style`」，但沒 lint guard 強制，這 14 檔又 pre-date 該規範。

### 為什麼順帶重產 visual baseline（57.14 機制的第一次端到端）

7 個 migration 目標檔（`CostBreakdownTable` / `MonthPicker` / `ApprovalList` / `TenantListTable` / `TenantListPagination` / `TenantListFilters`）正好 render 在 6 個 `visual-regression.spec.ts` snapshot 的 3 個（cost-dashboard / governance / admin-tenants）裡。把 `#666` 換成合規色階 → **顏色會變** → 那 3 個 `*-chromium-linux.png` baseline 會 mismatch（即使 spacing 用 Tailwind `p-2` = `0.5rem` 完全等價，顏色不等價）。所以本 sprint 必須重產那些 baseline——透過 57.14 落的 `visual-baseline` workflow_dispatch job（`gh workflow run "Playwright E2E" --ref feature/sprint-57-15-inline-style-cleanup` → ubuntu-latest 跑 `RUN_VISUAL=1 playwright test visual --update-snapshots` → 上傳 `visual-baselines` artifact + 開 `chore/visual-baselines-<run_id>` PR against feature branch）。本 dev session 不能在 Windows 產可用 baseline（cross-OS 渲染差異），所以走 workflow + 下載 artifact commit（同 57.14 PR #135 的做法）。這 sprint 因此也驗證了 57.14 機制 end-to-end works（FIX-007/008 後的版本）。

### 17.md / V2 紀律對齊

- `17-cross-category-interfaces.md`：N/A——0 NEW agent-harness contract / ABC / LoopEvent / migration / API endpoint；只動前端 component + ESLint config + e2e spec + design tokens（若需新 token）。
- Multi-tenant 鐵律：N/A（不動 backend / DB / API）。
- LLM Provider Neutrality：N/A（不碰 `agent_harness/`；Tailwind / ESLint / @axe-core 非 LLM SDK）。
- CC Reference 不照搬：N/A（前端樣式重構）。
- 04 anti-patterns：AP-2 no orphan（`react/forbid-dom-props` guard 真的會 lint fail；不是裝了放著）；AP-4 no Potemkin（`color-contrast` rule 重開後真的會 scan；不是空殼）；AP-6 YAGNI（**不**順手做設計系統全面替換 / **不**為「將來」加沒被要求的 token / **不**重構沒壞的 component 邏輯——只 `style={{}}` → `className`）。

---

## User Stories

### Group A — Inline-style → Tailwind migration

#### US-A1: 三-prong 後逐檔 triage 所有 `style={{}}`，分 static / dynamic，建 migration 表

**作為** 開發者，**我希望** 14 個檔的 80 個 inline-style call site 被逐一分類（static literal → Tailwind class / dynamic computed → 逃生口策略）並有一張對照表，**以便** 遷移有依據、不漏不錯。

- Day 0 三-prong 後對每檔 `grep -n "style={{"` + 讀該行上下文，分類：
  - **static**：literal object，CSS 值全是常數（`padding: "0.5rem"`、`textAlign: "right"`、`color: "#666"`、`borderBottom: "1px solid #ddd"`、`fontStyle: "italic"`、`width: "100%"`、`borderCollapse: "collapse"`、`marginTop: "1rem"`、…）→ 直接對應 Tailwind utility（`p-2`、`text-right`、`text-gray-700`、`border-b border-gray-200`、`italic`、`w-full`、`border-collapse`、`mt-4`、…）。對 hex 色：對照 `tailwind.config.*` 的 `theme.colors` / design token；`#666` → 合規色階（`text-gray-600` `#4b5563` ≈ 7:1 ✅，或 `text-gray-500` `#6b7280` ≈ 4.7:1 ✅ — 取夠 contrast 的；`#c62828` error red → `text-red-700` ≈ 5.9:1 ✅；`#333` → `text-gray-800` / `text-gray-900`）。
  - **dynamic**：值含變數 / 表達式（`marginLeft: depth > 0 ? \`${depth * 12}px\` : undefined`、`color: riskColor`、bar `width: \`${pct}%\``）→ 策略（優先序）：(i) 若是有限集合（riskLevel ∈ {high, medium, low} → `text-red-700` / `text-amber-700` / `text-green-700`）→ 條件 `className`；(ii) 連續值（depth indent、bar %）→ CSS custom property：`style={{ "--indent": \`${depth * 12}px\` } as React.CSSProperties}` + `className="pl-[var(--indent)]"`（Tailwind arbitrary value 讀 CSS var — 仍有一個 `style` 但只設 CSS var，guard 用 `eslint-disable` + reason 放行，或 guard 的 message 接受「只設 `--*` 變數」）；(iii) 真的無解 → 保留 inline `style` + `// eslint-disable-next-line react/forbid-dom-props -- <one-line reason>`。
- 在 `progress.md` Day 1 列 migration 表：檔 / 行 / 原 inline style / 分類 / 目標（Tailwind class 或逃生口策略）。
- **不改 component 邏輯 / 結構**（只 `style={{}}` → `className`，必要時加一個 wrapper class）；**不刪 component**；**不順手**做設計系統替換。

**驗收**：`progress.md` Day 1 有完整 80-row（或合併同類後）migration 表；每 row 標 static/dynamic + 目標；dynamic 的逃生口策略明確。

#### US-A2: 執行遷移——14 檔 `style={{}}` → Tailwind class，逐檔驗渲染不變

**作為** 開發者，**我希望** 14 檔的 inline style 都換成 Tailwind utility class（dynamic 的按 US-A1 策略），**以便** 樣式集中可維護、低對比色消失、design-system 一致。

- 按 migration 表逐檔改；每改一檔跑該 feature 的 vitest（`npm run test -- <feature>`）確認不變；改完跑全套 vitest（baseline 236 pass）。
- hex 色 → design token / Tailwind 色階：先看 `tailwind.config.*` 與 `components/ui/` 用的 token（`text-muted-foreground` 之類若已定義且合規優先用，與設計系統一致）；若沒有合適的就用 Tailwind 內建色階（取 ≥ 4.5:1 的）。**不新增** design token 除非真的找不到能用的（YAGNI）。
- chat-v2 4 檔（`ApprovalCard` / `ToolCallCard` / `ChatLayout` / `MessageList`）+ `SubagentTree`——這些是 `color-contrast` 重開的前提；清完它們的 hardcode hex。
- 每改一檔的 file-header MHist 加 1 行（Behavioral：`- 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)`，≤ E501）。
- `git diff` 確認改的都是 `frontend/src/features/**/*.tsx`（+ 可能 `tailwind.config.*` 若加 token）；無 component 邏輯改動。

**Tests**：無新增 unit test（純樣式重構；既有 vitest 涵蓋 render；component 行為不變）。若某檔的 test 斷言了 inline style 的字面值（`expect(el).toHaveStyle({ color: "#666" })`）→ 改該斷言對齊新 class（`expect(el).toHaveClass("text-gray-600")` 或刪該過度具體的斷言）。

**驗收**：`git diff` 只動 `frontend/src/features/**`（+ 可能 `tailwind.config.*`）；`npm run test`（vitest）綠（236 pass，或若有改斷言則對應調整後綠）；`grep -rn "style={{" frontend/src` 剩下的只有帶 `eslint-disable react/forbid-dom-props` 的 dynamic 逃生口（每個有 reason comment）；`npm run lint && npm run build`（main bundle 預期 ~不變或微降——少了 inline style object 字面量）。

### Group B — Guard + a11y re-enable

#### US-B1: `no-inline-style` ESLint guard + `color-contrast` axe rule 重開 + `STYLE.md` §Inline styles

**作為** 維運者，**我希望** inline `style` 有 lint guard 防 regression、`a11y-scan.spec.ts` 的 `color-contrast` rule 重開、`STYLE.md` 寫明規範與逃生口，**以便** 這次 sweep 的成果鎖住、a11y 護欄完整、後人知道怎麼做。

- `frontend/eslint.config.js` — 加 rule：
  ```js
  "react/forbid-dom-props": ["error", { "forbid": [{ "propName": "style",
    "message": "Use Tailwind utility classes (STYLE.md §Inline styles). For genuinely-dynamic values (computed dimensions, progress %), set a CSS custom property and read it via a Tailwind arbitrary value (`pl-[var(--x)]`), or add `// eslint-disable-next-line react/forbid-dom-props -- <reason>`." }] }],
  "react/forbid-component-props": ["error", { "forbid": [{ "propName": "style",
    "message": "Pass className, not style, to components. See STYLE.md §Inline styles." }] }],
  ```
  （`eslint-plugin-react` 已是 dep；確認 Day 0 三-prong。若 `forbid-dom-props` 對 `{ "--x": … }`-only style 也報——它會——則那些 case 用 inline `eslint-disable` + reason；guard 的價值在「預設禁止、例外要標」。）
- `frontend/tests/e2e/a11y/a11y-scan.spec.ts` — `.disableRules(["color-contrast"])` → 移除（或若還有 out-of-scope 的少數違規無法本 sprint 修 → 改成更窄的 disable + comment 指向 NEW AD，但**先試全開**）；更新該段 comment（不再提 chat-v2 inline panel，因為已修）。
- `frontend/STYLE.md` — §"Inline styles"（新增或擴充現有 §）：規則（預設用 Tailwind utility class）+ 動態值 3 策略（finite class set / CSS custom property + arbitrary value / inline `eslint-disable` + reason，附範例）+ 指向 `react/forbid-dom-props` guard。MHist += 57.15 entry。`Last Modified` → 2026-05-11。若 `CONVENTION.md` §10（design-system）也提到 styling，加 cross-ref（不重複內容）。
- 跑 `npm run lint`（含新 guard — 應 0 error，因為 US-A2 已清乾淨 + dynamic 的有 disable comment）；跑 `npm run e2e -- a11y/a11y-scan.spec.ts`（含重開的 color-contrast — 應綠；若紅則是 US-A2 漏了某個低對比色 → 回去修，不是改 spec）。

**驗收**：`eslint.config.js` 有 `react/forbid-dom-props` + `react/forbid-component-props`（`error`）；`npm run lint` 0 error；`a11y-scan.spec.ts` 不再 `.disableRules(["color-contrast"])`（或只 disable 明確標 NEW AD 的窄範圍）；`npm run e2e -- a11y/a11y-scan.spec.ts` 綠；`STYLE.md` §Inline styles 有規則 + 3 逃生口 + 範例 + guard cross-ref。

### Group C — Closeout

#### US-C1: 驗證 sweep + 重產 visual baseline + retrospective + memory + doc syncs + PR

**作為** AI 助手，**我希望** sprint 收尾完整（驗證 / visual baseline 重產 / 文件 / memory / PR），**以便** 下個 session 接得上、CI 全綠。

- Full validation sweep: `cd frontend && npm run lint`（含新 guard，0 error）`&& npm run build`（main bundle ≈ 不變或微降）`&& npm run test`（vitest 236 pass，或調斷言後綠）`&& npx playwright test`（綠——但 `visual-regression.spec.ts` 在本機 Windows 仍 skip，6 visual test 不跑；其餘 40 pass）；backend untouched — `git diff --stat main..HEAD` 確認 0 `backend/` 改動（→ backend baseline 不變：pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / 0 LLM SDK leak；不重跑）。
- **重產 visual baseline**（57.14 機制第一次端到端）：push feature branch 後 → `gh workflow run "Playwright E2E" --ref feature/sprint-57-15-inline-style-cleanup` → 等 `visual-baseline` job 跑完 → 它會（a）開一個 `chore/visual-baselines-<run_id>` PR against feature branch + （b）上傳 `visual-baselines` artifact。做法同 57.14 PR #135：下載 artifact → 把更新的 `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*-chromium-linux.png`（預期 cost-dashboard / governance / admin-tenants 3 個變，app-shell / auth-login / verification-recent 3 個不變）commit 進 feature branch（不 merge 那個 auto-PR；close 它）→ feature branch 的 CI 重跑 `visual-regression.spec.ts` 應綠。**誠實標**：若 workflow 因任何原因跑不了（如 dispatch 權限）→ baseline 重產列 retrospective Q4 carryover（`AD-Visual-Baseline-Refresh-57.15`），feature branch 的 `visual-regression.spec.ts` CI 會紅（intentional — 等 baseline 更新）→ PR 描述註明 + 不 block merge（user 決定）。但**先試 workflow 路徑**。
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-15/progress.md` — Day 0-3 daily entries + D-PRE / D-DAY drift catalog + migration 表（Day 1）。
- 同目錄 `retrospective.md` — Q1-Q7（Q2 ratio；Q4 carryover AD：若 a11y 重開有 out-of-scope 違規未修 / 若 visual baseline 重產有問題 / `AD-Lighthouse-Visual-Hard-Gate` 仍 open）；Q6 calibration class verdict（NEW `frontend-refactor-mechanical` HYBRID 0.50 1st app）。
- memory: `~/.claude/projects/.../memory/project_phase57_15_inline_style_cleanup.md` + `MEMORY.md` index +1 row。
- in-sprint doc syncs: `16-frontend-design.md`（V2 Ship Timeline +1 entry — inline-style sweep + a11y color-contrast re-enabled + no-inline-style guard）/ `.claude/rules/sprint-workflow.md`（calibration matrix +1 row — `frontend-refactor-mechanical` 0.50 1-data-point）/ `STYLE.md` §Inline styles（已在 US-B1）/ checklist [x] + plan/checklist header MHist closeout（Status: Draft → Closed）。
- post-merge doc syncs: `CLAUDE.md`（main HEAD + Latest Sprint row + Next Phase 候選 — 移除 `AD-Inline-Style-Cleanup-Sweep`；a11y color-contrast 現已全開）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分。
- PR: `git push` feature branch → `gh pr create`；solo-dev review_count=0；等 5 active CI checks 綠（含 `Frontend E2E` — 若 visual baseline 已重產 commit 進 branch 則綠；若沒則 `visual-regression.spec.ts` 會紅，PR 描述註明）；merge 由 user 決定（surface PR，不自行 merge per executing-actions-with-care）。

**驗收**：PR 開好；5 active CI checks 狀態如上（visual 視 baseline 重產而定）；retrospective.md 8 條 sprint-workflow self-check 全 ✅；memory snapshot 寫好。

---

## Technical Specifications

### Migration 流程（US-A1 → US-A2）

```
1. Day 0 三-prong: grep -rn "style={{" frontend/src → pin 14 檔 80 occurrences;
   讀 tailwind.config.* 的 theme.colors / design token; 讀 components/ui/ 用的 color util
   class（text-muted-foreground 之類）; 讀 eslint.config.js 現有 rules + 確認 eslint-plugin-react dep;
   讀 STYLE.md 現有 §; 讀 a11y-scan.spec.ts L84-95 的 disableRules block; 讀 1-2 個 vitest
   是否斷言 inline style 字面值
2. Day 1 US-A1: 逐檔 grep -n + 讀上下文 → migration 表（static→Tailwind class / dynamic→策略）
3. Day 1-2 US-A2: 逐檔改; 每改跑 npm run test -- <feature>; 改完跑全套 vitest;
   每檔 file-header MHist +1 行; git diff 確認只動 src/features/** (+可能 tailwind.config.*)
4. Day 2 US-B1: eslint.config.js +react/forbid-dom-props +react/forbid-component-props;
   a11y-scan.spec.ts 移 color-contrast; STYLE.md §Inline styles; npm run lint (0 err) +
   npm run e2e -- a11y/a11y-scan.spec.ts (綠)
5. Day 3 US-C1: full sweep + push + gh workflow run visual-baseline + 下載 artifact commit
   baseline + retro + memory + doc syncs + PR
```

### Static → Tailwind 對照（樣本；完整在 Day 1 migration 表）

| 原 inline style | Tailwind class |
|-----------------|----------------|
| `padding: "0.5rem"` | `p-2` |
| `textAlign: "right"` | `text-right` |
| `textAlign: "left"` | `text-left` |
| `color: "#666"` | `text-gray-600`（`#4b5563` ≈ 7:1 ✅；或 design token `text-muted-foreground` 若合規）|
| `color: "#333"` | `text-gray-800` |
| `color: "#c62828"`（error red）| `text-red-700`（≈ 5.9:1 ✅）|
| `borderBottom: "1px solid #ddd"` | `border-b border-gray-200` |
| `borderBottom: "2px solid #333"` | `border-b-2 border-gray-800` |
| `borderCollapse: "collapse"` | `border-collapse` |
| `width: "100%"` | `w-full` |
| `marginTop: "1rem"` | `mt-4` |
| `marginTop: "0.5rem"` | `mt-2` |
| `fontStyle: "italic"` | `italic` |
| `fontWeight: 700` | `font-bold` |
| `fontSize: "0.85rem"` | `text-sm`（≈ 0.875rem — 視覺等價；若要精確 `text-[0.85rem]`）|

### Dynamic case 處理（樣本；完整在 Day 1 migration 表）

| 檔:行 | 原 dynamic style | 策略 |
|-------|------------------|------|
| `SubagentTree.tsx:77` | `style={{ marginLeft: depth > 0 ? \`${depth * 12}px\` : undefined }}` | CSS custom property：`style={{ "--st-indent": \`${depth * 12}px\` } as React.CSSProperties}` + `className="ml-[var(--st-indent)]"`（或若 depth 有上限 → 有限 `ml-0/ml-3/ml-6/...` class set；視 depth 範圍 Day 1 決定）；`eslint-disable react/forbid-dom-props -- CSS var only, dynamic tree-indent` |
| `ApprovalCard.tsx:135` | `style={{ color: riskColor, fontWeight: 700 }}` | `riskColor` 來自 `riskLevel` ∈ 有限集 → `className={cn("font-bold", riskLevel === "high" && "text-red-700", riskLevel === "medium" && "text-amber-700", riskLevel === "low" && "text-green-700")}`（移除 `riskColor` 變數）|
| `SLAMetricsCard.tsx`（bar 寬）| `style={{ width: \`${pct}%\` }}` | CSS custom property：`style={{ "--bar-w": \`${pct}%\` } as React.CSSProperties}` + `className="w-[var(--bar-w)]"`；`eslint-disable react/forbid-dom-props -- CSS var only, dynamic SLA bar width` |

> CSS-var-only `style` 仍會被 `react/forbid-dom-props` 抓（它不分內容）→ 那些 line 加 `// eslint-disable-next-line react/forbid-dom-props -- <reason>`。Guard 的價值不是「零 inline style」而是「預設禁止、每個例外都有理由可審」。

### `a11y-scan.spec.ts` color-contrast 重開（US-B1）

```typescript
// 現況（57.13 US-B5 / 57.14 hermeticity fix 後）:
//   const results = await new AxeBuilder({ page })
//     .disableRules(["color-contrast"])   // ← 因 chat-v2 inline panel hardcode hex
//     .analyze();
// 改成（chat-v2 已清乾淨 → 全開）:
//   const results = await new AxeBuilder({ page }).analyze();
// 並更新上方 comment（不再提 inline panel）。
// 若重開後出現 *out-of-scope*（非這 14 檔的）color-contrast 違規無法本 sprint 修:
//   .disableRules(["color-contrast"])  ← 保留但 comment 改成「剩 X 處在 <檔/組件>，AD-Color-Contrast-Round2」
//   — 但這是 fallback；先試全開。
```

### `visual-baseline` workflow 重產（US-C1，57.14 機制）

```bash
# feature branch push 後:
gh workflow run "Playwright E2E" --ref feature/sprint-57-15-inline-style-cleanup
# 等 visual-baseline job (ubuntu-latest) 跑完 → 它:
#   1. RUN_VISUAL=1 playwright test visual --update-snapshots → 重產 6 個 *-chromium-linux.png
#   2. 若有變 → push 到 chore/visual-baselines-<run_id> + gh pr create --base feature/sprint-57-15-...
#   3. 永遠上傳 visual-baselines artifact
# 做法（同 57.14 PR #135）:
#   - gh run download <run_id> -n visual-baselines  → 取得 6 個 PNG
#   - 把變了的（預期 cost-dashboard / governance / admin-tenants）commit 進 feature branch
#   - close 那個 chore/visual-baselines-<run_id> auto-PR（不 merge — 已手動 commit）
#   - feature branch CI 重跑 → visual-regression.spec.ts 綠
```

### Calibration class

NEW class `frontend-refactor-mechanical` — HYBRID weighted blend over the 4 USs:
- US-A1+A2 (triage + migrate ~80 inline-style occurrences across 14 files; per-file render verify) ≈ `mechanical-refactor × 0.40-0.45` weight ~0.70 of sprint
- US-B1 (ESLint guard + a11y rule re-enable + STYLE.md §) ≈ `ci-config+a11y × 0.55` weight ~0.15
- US-C1 (closeout + visual-baseline regen via 57.14 workflow) ≈ `closeout × 0.80` weight ~0.15
- Weighted blend ≈ **0.48 ≈ 0.50** mid-band (conservative default for an unvalidated new class; pending 2-3 future refactor sprints to validate — `AD-*-Cleanup-Sweep` is a recurring shape).

---

## File Change List

> 完整精確清單在 Day 0 三-prong 後於 checklist 落實；以下為 plan 層級概覽。

### MODIFIED Frontend — src（migration 目標，14 檔）
- `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx`（27）
- `frontend/src/features/tenant-settings/components/TenantSettingsEditForm.tsx`（13）
- `frontend/src/features/cost-dashboard/components/CostBreakdownTable.tsx`（14）
- `frontend/src/features/cost-dashboard/components/MonthPicker.tsx`（2）
- `frontend/src/features/sla-dashboard/components/SLAMetricsCard.tsx`（4）
- `frontend/src/features/governance/components/ApprovalList.tsx`（1）
- `frontend/src/features/admin-tenants/components/TenantListTable.tsx`（5）
- `frontend/src/features/admin-tenants/components/TenantListPagination.tsx`（1）
- `frontend/src/features/admin-tenants/components/TenantListFilters.tsx`（1）
- `frontend/src/features/chat_v2/components/ApprovalCard.tsx`（4）
- `frontend/src/features/chat_v2/components/ToolCallCard.tsx`（3）
- `frontend/src/features/chat_v2/components/ChatLayout.tsx`（2）
- `frontend/src/features/chat_v2/components/MessageList.tsx`（2）
- `frontend/src/features/subagent/components/SubagentTree.tsx`（1）
- （視需要）`frontend/tailwind.config.*` — 僅在找不到能用的 design token 時加（YAGNI — 預期不需要）

### MODIFIED Frontend — config / spec / docs
- `frontend/eslint.config.js` — `react/forbid-dom-props` + `react/forbid-component-props`（`error`）
- `frontend/tests/e2e/a11y/a11y-scan.spec.ts` — 移除 `.disableRules(["color-contrast"])`（或窄化）+ 更新 comment
- `frontend/STYLE.md` — §"Inline styles"（規則 + 3 逃生口 + 範例 + guard cross-ref）+ MHist + Last Modified
- （視需要）`frontend/CONVENTION.md` — §10 cross-ref（若提到 styling；不重複內容）
- （視 vitest）若有 test 斷言 inline style 字面值 → 對應 spec 改斷言

### NEW Frontend — regenerated（由 57.14 workflow 產，US-C1）
- `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/{cost-dashboard,governance,admin-tenants}-chromium-linux.png` — 重產（顏色變）；app-shell / auth-login / verification-recent 預期不變（不在 migration scope 內）

### Doc syncs
- in-sprint: `16-frontend-design.md`（V2 Ship Timeline +1 — inline-style sweep + a11y color-contrast re-enabled + no-inline-style guard）/ `.claude/rules/sprint-workflow.md`（calibration matrix +1 row — `frontend-refactor-mechanical` 0.50）/ `STYLE.md`（已上）/ checklist [x] + plan/checklist MHist closeout
- post-merge: `CLAUDE.md`（main HEAD / Latest Sprint / Next Phase 候選 — 移除 `AD-Inline-Style-Cleanup-Sweep`）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

---

## Acceptance Criteria

### Functional
- [ ] (A1) Day 0 三-prong 後 `progress.md` Day 1 有完整 migration 表（檔 / 行 / 原 inline style / static|dynamic / 目標 Tailwind class 或逃生口策略）涵蓋全部 14 檔。
- [ ] (A2) 14 檔的 `style={{}}` 全遷移：static → Tailwind utility class（hex 色 → ≥ 4.5:1 的 design token / Tailwind 色階）；dynamic → finite class set / CSS custom property + arbitrary value / inline `eslint-disable` + reason comment。`grep -rn "style={{" frontend/src` 剩下的每個都帶 `eslint-disable react/forbid-dom-props -- <reason>`。`git diff` 只動 `frontend/src/features/**`（+ 可能 `tailwind.config.*`）；無 component 邏輯改動。每改的檔 file-header MHist +1 行（≤ E501）。`npm run test`（vitest）綠（236 pass，或調斷言後綠）。
- [ ] (B1) `eslint.config.js` 有 `react/forbid-dom-props` + `react/forbid-component-props`（`error` + helpful message）；`npm run lint` 0 error。`a11y-scan.spec.ts` 不再 `.disableRules(["color-contrast"])`（或只 disable 明確標 NEW AD 的窄範圍 + comment）；`npm run e2e -- a11y/a11y-scan.spec.ts` 綠。`STYLE.md` §Inline styles 有規則 + 3 逃生口 + 範例 + `react/forbid-dom-props` cross-ref；MHist + Last Modified 更新。
- [ ] (C1) full validation sweep 綠：`npm run lint`（含新 guard，0 error）+ `npm run build`（main bundle ≈ 不變或微降）+ `npm run test`（vitest 236 pass）+ `npx playwright test`（40 pass / visual 在 Windows 仍 skip）；backend untouched（`git diff --stat main..HEAD` = 0 `backend/`）。visual baseline 重產：`gh workflow run "Playwright E2E" --ref feature/...` → 下載 artifact → 變了的 PNG commit 進 feature branch（或誠實標 carryover 若 workflow 跑不了）。

### Non-functional
- pytest baseline 1676 + 4 skip — 不變（不動 backend）；mypy --strict 0/306 — 不變；9 V2 lints 9/9 — 不變；Vite build main bundle 297.89 kB — ≈ 不變或微降（少了 inline style object 字面量；不應顯著增加）；Vitest 236 — 不變（純樣式重構；若調過度具體的 style 斷言則對應數字微調，記 progress.md）；ESLint — 新增 2 rules 後仍 silent（0 error）；LLM SDK leak 0；新增 0 npm runtime dep（`eslint-plugin-react` 已是 dep；不裝新 package）。
- Playwright e2e — 40 pass / 7 skip（本機 Windows）；CI ubuntu — 46 → 仍 46（visual 6 個跑，baseline 重產後綠；color-contrast 重開後 a11y-scan 仍綠）。
- a11y — `a11y-scan.spec.ts` 從「color-contrast disabled」變「全 axe rule 啟用」（或窄化 disable 標 NEW AD）。

### Sprint workflow discipline
- Phase README（無需，沿用 phase-57-frontend-saas）→ plan（本檔）→ checklist → Day 0 三-prong → code（Day 1-2）→ 每 day update checklist + progress.md → retrospective（Day 3）→ PR。
- 三-prong（Day 0）：Prong 1 path verify（14 src 檔 + `eslint.config.js` + `a11y-scan.spec.ts` + `visual-regression.spec.ts` + `STYLE.md` + `CONVENTION.md` + `tailwind.config.*` + `16-frontend-design.md` + `sprint-workflow.md` 存在）+ Prong 2 content verify（`tailwind.config.*` theme.colors / design token / `components/ui/` 用的 color class；`eslint.config.js` 現有 rules + `eslint-plugin-react` 在 deps；`a11y-scan.spec.ts` 現有 `.disableRules` block；`STYLE.md` 現有 §；隨機 2-3 個 vitest 是否斷言 inline style 字面值；14 檔的 `style={{}}` static vs dynamic 比例抽樣）+ Prong 3 schema verify（N/A — 不動 DB / migration / ORM / API）。

### V2 紀律 9 項 self-check（each commit + PR）
1. Server-Side First — N/A（不動 backend）；前端樣式重構
2. LLM Provider Neutrality — N/A（不碰 agent_harness）；Tailwind / ESLint / @axe-core 非 LLM SDK
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. 11+1 範疇 — N/A（純前端 component + ESLint config + e2e spec；無範疇雜湊）
6. 04 anti-patterns — AP-2 no orphan（`react/forbid-dom-props` guard 真的會 lint fail / color-contrast 重開真的會 scan）/ AP-4 no Potemkin（migration 後低對比色真的消失）/ AP-6 YAGNI（不順手做設計系統全面替換 / 不加沒被要求的 token / 不重構沒壞的 component 邏輯）
7. Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. File header convention — plan/checklist/progress/retrospective header + MHist 1-line max；每改的 component 檔更新 MHist（Behavioral — 樣式重構算 Behavioral？嚴格說是 Structural-ish 但只改 className，採 Behavioral entry 即可）
9. Multi-tenant rule — N/A（不動 backend / DB / API）

---

## Deliverables (checklist mapping)

- [ ] US-A1: Day 0 三-prong → `progress.md` Day 1 完整 migration 表（14 檔 / 80 occurrences / static|dynamic / 目標）
- [ ] US-A2: 14 檔 `style={{}}` → Tailwind class（dynamic 按策略）+ 每檔 vitest 驗 + 每檔 MHist +1 + `grep "style={{"` 剩的都有 `eslint-disable` + reason + `npm run test` 綠 + `git diff` 只動 `src/features/**`
- [ ] US-B1: `eslint.config.js` +`react/forbid-dom-props`+`react/forbid-component-props` + `a11y-scan.spec.ts` 移 `.disableRules(["color-contrast"])` + `STYLE.md` §Inline styles + `npm run lint` 0 err + `npm run e2e -- a11y/a11y-scan.spec.ts` 綠
- [ ] US-C1: full validation sweep + visual baseline 重產（`gh workflow run` + 下載 artifact commit）+ retrospective Q1-Q7 + memory snapshot + 3 in-sprint doc syncs + PR (+ 2 deferred post-merge)

---

## Dependencies & Risks

### External dependencies
- `eslint-plugin-react` — 已是 frontend dev dep（提供 `react/forbid-dom-props` + `react/forbid-component-props`）；Day 0 三-prong 確認版本支援這兩 rule（react plugin v7.20+ 都有）。0 NEW npm package。
- 57.14 `visual-baseline` workflow_dispatch job（`.github/workflows/playwright-e2e.yml`）— 本 sprint 依賴它重產 6 個 baseline；FIX-007（`git add` glob）+ FIX-008（open-a-PR 不直推 protected branch）已修；本 sprint 是該機制的第一次「真的有東西要重產」的端到端使用。
- `npx playwright install chromium` — 本機已裝（`chromium-1217` ↔ Playwright 1.59.1）；e2e 跑 a11y-scan 用。

### Risk matrix

| Risk | 機率 | 影響 | 緩解 |
|------|------|------|------|
| `react/forbid-dom-props` 對 CSS-var-only 的 `style={{ "--x": … }}` 也報 → 大量 `eslint-disable` comment 顯得醜 | 高（基本必然）| 低 | 接受：guard 的價值是「預設禁止、例外要標 reason」；CSS-var-only 的 case 加 `// eslint-disable-next-line react/forbid-dom-props -- CSS var only, <what's dynamic>`；STYLE.md 寫明這是 OK 的 pattern。若 CSS-var case 很多（>5）→ 考慮 ESLint custom rule「允許只設 `--*` 的 style」——但 YAGNI，先用 disable comment |
| 把 hex 色換成 Tailwind 色階後**仍**不過 WCAG AA（選錯色階）| 中 | 中（color-contrast 重開會紅）| US-A2 改完先跑 `npm run e2e -- a11y/a11y-scan.spec.ts`（含重開的 color-contrast）；紅 = 哪個色還不夠 → 換更深的色階（`gray-600` `#4b5563` ≈ 7:1 vs `gray-500` `#6b7280` ≈ 4.7:1 — 不確定就取深的）。**修色不改 spec** |
| 重開 `color-contrast` 後出現 *out-of-scope*（非這 14 檔的）違規（design-system 組件 / 別的頁）| 中 | 中 | 視違規數：少（1-2 處）→ 順手修（仍在「a11y hardening」精神內，不算 scope creep）；多 → 保留 `.disableRules(["color-contrast"])` 但 comment 改成「剩 X 處在 <檔>，NEW AD-Color-Contrast-Round2」+ retrospective Q4 列；**不**假裝沒看到 |
| 遷移改變了 visual snapshot 的 pixel（不只顏色，spacing / layout 也飄）→ 6 個 baseline 全變 | 中 | 中 | Tailwind 的 `p-2`=`0.5rem`、`mt-4`=`1rem`、`w-full`=`100%` 與原 inline 值**完全等價** → spacing/layout 不該飄；只顏色變（intentional）。若 layout 真飄 → 是 migration 錯（漏了某個值 / 用錯 class）→ 修 migration 不接受 baseline 飄。重產後人工 eyeball 6 個 PNG diff 確認只有顏色變 |
| `visual-baseline` workflow dispatch 在 feature branch 上跑不起來（權限 / `gh workflow run` 對 non-default branch）| 低 | 低（baseline 重產延後）| `gh workflow run "Playwright E2E" --ref <feature-branch>` 對 `workflow_dispatch` trigger 應 work（workflow 已在 main 上定義）；若不行 → fallback：merge PR 到 main（接受 `visual-regression.spec.ts` CI 紅）→ 在 main 上 `gh workflow run --ref main` → 它開 `chore/visual-baselines-<run_id>` PR → merge → green。retrospective Q4 記 `AD-Visual-Baseline-Refresh-57.15`（若走 fallback）|
| vitest 有 test 斷言 inline style 字面值（`toHaveStyle({color:"#666"})`）→ migration 後紅 | 中 | 低 | Day 0 三-prong 抽樣確認；US-A2 改 component 時同步改該斷言（→ `toHaveClass` 或刪過度具體的）；記 progress.md（這算 spec 對齊 implementation，不算「改 spec 來跑綠」——斷言的對象本來就該是 class 不是字面 hex）|
| 14 檔太多一天改不完（`TenantSettingsView` 27 + `TenantSettingsEditForm` 13 + `CostBreakdownTable` 14 = 54 個 occurrence 集中在 3 檔）| 中 | 中 | Day 1-2 都給 Group A；若仍超 → 先改 chat-v2 5 檔（`color-contrast` 重開的前提）+ visual-snapshot 的 7 檔（cost/governance/admin-tenants），剩 `TenantSettings{View,EditForm}` + `SLAMetricsCard`（不在 snapshot、不影響 a11y-scan 的 gated pages — 確認 a11y-scan 掃哪些 route）標 🚧 + carryover AD `AD-Inline-Style-Cleanup-Sweep-Round2`（**不刪 / 不留半套** — 若分批則 guard 也分批：先不加 `error` guard 直到全清，或加 guard 但對未清的檔 `/* eslint-disable react/forbid-dom-props */` file-level + reason + carryover AD）。但**先試一次做完** |

### Day 0 三-prong drift findings (added 2026-05-11 — per sprint-workflow.md §Step 2.5; full catalog in progress.md Day 0)

> Per §Step 2.5: drift findings go here (preserve "what was originally planned vs. what reality forced"), NOT silently into §Technical Spec / §US-B1. The checklist (execution truth) reflects the adjusted approach.

- **D-PRE-1** 🟡 (approach shift, < 5% scope): `eslint-plugin-react` is NOT a frontend dep (only `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` + `eslint-plugin-jsx-a11y`). So `react/forbid-dom-props` / `react/forbid-component-props` — the rules §US-B1 / §Technical Spec originally specified — are unavailable. **Adjusted approach**: use ESLint's built-in `no-restricted-syntax` with a `JSXAttribute[name.name='style']` selector + a helpful message; escape hatch = `// eslint-disable-next-line no-restricted-syntax -- <reason>`. Dep-free, plain-ESLint, same deliverable ("no-inline-style lint guard, default-deny + reasoned exceptions"). `no-restricted-syntax` is not currently configured → adds cleanly. (Alternative considered: add `eslint-plugin-react` as a dev dep — rejected, YAGNI; the selector approach is dep-free and the message is just as helpful.)
- **D-PRE-2** 🟡: `a11y-scan.spec.ts` scans `GATED_ROUTES` (`/chat-v2 /cost-dashboard /sla-dashboard /admin-tenants /tenant-settings /governance /verification /loop-debug /memory`) via the 57.14 `mockApi` helper (catch-all `**/api/v1/**` → 503, then `/auth/me` → 200) → the data-driven migration targets (`CostBreakdownTable` rows / `TenantList*` rows / `ApprovalList` items / `SLAMetricsCard`) render as `<ErrorRetry>`, not populated UI; the chat-v2 panels the disable-comment names may not render under 503 either. ⇒ re-enabling `color-contrast` (US-B1) may already be ≈green; the cleanup is still valuable (convention + the low-contrast hex IS in source). If red → offenders self-identify → confirm ⊆ the 14 files or log NEW `AD-Color-Contrast-Round2` (already covered in Risk matrix).
- **D-PRE-3** 🟢: `STYLE.md` already has §1 "Tailwind Utility-First" (with "Rules") / §2 "Color Tokens" / §3 "Risk Badge Palette" (with "Reference component" + "Future codification candidate"). ⇒ the §US-B1 "Inline styles" guard content should *extend* §1 "Rules" + add an escape-hatch sub-section (not a new top-level §); and US-A2's `ApprovalCard` `riskColor` migration must ALIGN with §3 "Risk Badge Palette" + its "Reference component" — read §3 before mapping risk colours.
- **D-PRE-4** 🟢: no vitest spec asserts `toHaveStyle(...)` / `.style` on the 14 components ⇒ the Risk-matrix row "vitest asserts inline-style literal → migration fails" probability drops to ~0 (still verify other per-file assertions in US-A2).
- **Path note**: `16-frontend-design.md` lives at `agent-harness-planning/16-frontend-design.md` (top level), NOT under `phase-57-frontend-saas/`; `tailwind.config` is `.ts` not `.js`. (Doc-sync targets corrected accordingly.)

### Day 1 scope revision (2026-05-11 — user chose (B) Tiered; per sprint-workflow.md §Step 2.5 "20-50% shift → revise §Acceptance/§Workload, re-confirm with user")

**D-DAY1-1**: plan §Background said "80 `style={{}}` / 14 files"; re-survey (`grep -rEn "style=\{" frontend/src --include="*.tsx"`) = **15 files / 133 `style=` JSX attrs** (80 inline-literal + 53 `style={objVar}`/`style={fn()}`) + ~6 module-level `Record<string,CSSProperties>` stylesheet objects + ~5 helper fns returning `CSSProperties`. The `no-restricted-syntax` `JSXAttribute[name.name='style']` guard flags ALL `style=` regardless of value shape ⇒ to pass at `error`, all 133 must be migrated or carry `eslint-disable`. >20% shift + the `ChatLayout.tsx` "Phase 58+ defer" header note ⇒ paused for a user scope decision.

**User chose (B) Tiered** — revised scope:
- **This sprint (10 files)**: `ApprovalCard` / `ToolCallCard` / `MessageList` / `SubagentTree` (chat-v2/subagent — `color-contrast` re-enable prerequisite) + `CostBreakdownTable` / `MonthPicker` / `ApprovalList` / `TenantListTable` / `TenantListPagination` / `TenantListFilters` (3 visual-regression snapshots + a11y). ≈ 70 `style=` attrs.
- **Deferred → NEW `AD-Inline-Style-Cleanup-Sweep-Round2` (5 files)**: `ChatLayout` (its header's Phase-58 defer note) / `InputBar` / `TenantSettingsView` (27) / `TenantSettingsEditForm` (13) / `SLAMetricsCard` (4, incl dynamic bar widths). ≈ 63 `style=` attrs. Each gets a top-of-file `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */` so the `error`-level guard passes for everything else. Logged in retrospective Q4.
- **Unchanged**: `color-contrast` axe rule re-enabled (US-B1); 3 visual baselines (cost-dashboard / governance / admin-tenants) refreshed via the 57.14 workflow (US-C1); guard `no-restricted-syntax` = `error`; Day 0-3; calibration `frontend-refactor-mechanical` HYBRID 0.50 (~4-6 hr committed — the tiered scope ≈ what the original plan actually estimated).
- §Acceptance Criteria (A1/A2) + §Deliverables + checklist §1.2/§2.1/§2.3 read "10 files this sprint, 5 → Round2". §Technical Spec's "Static → Tailwind 對照" + "Dynamic case 處理" tables remain valid (they describe the technique, not the file list).

### Roll-back plan
- 每檔（或每組相關檔）一個 commit；某檔改壞可單獨 revert（feature branch）。
- ESLint guard / a11y re-enable 各一個 commit；若 guard 太吵可單獨調或 revert。
- 整個 branch 在 PR 前都可 reset；merge 後若有 visual / a11y regression 開 hotfix PR。
- 若 visual baseline 重產失敗（最壞）→ feature branch 的 `visual-regression.spec.ts` CI 紅 → PR 描述註明「intentional — baseline pending refresh」→ merge 後在 main 上跑 workflow 補（fallback 路徑，retrospective Q4）。核心交付（inline style 清掉 + 色合規 + guard + a11y 重開）不依賴 baseline 重產。

---

## Workload (calibrated)

### Bottom-up estimate by US
| US | 估計 | 備註 |
|----|------|------|
| A1 | 1.5-2 hr | 14 檔逐行 grep + 讀上下文 + 分 static/dynamic + 建 migration 表（80 occurrences，多數 trivial；dynamic 約 5-10 個要想策略）|
| A2 | 3-5 hr | 14 檔 `style={{}}` → Tailwind class（54 個集中在 3 檔，其餘 26 個散在 11 檔）+ 每檔 vitest 驗 + 每檔 MHist + dynamic 的 CSS-var/class-set 改寫 + 跑全套 vitest + 可能調 1-2 個 style 斷言 |
| B1 | 1.5-2.5 hr | eslint.config.js +2 rules + a11y-scan.spec.ts 移 disableRules + STYLE.md §Inline styles（規則+3 逃生口+範例+cross-ref）+ npm run lint 驗 + npm run e2e -- a11y-scan 驗（含可能回頭修色）|
| C1 | 1.5-2 hr | full validation sweep + gh workflow run visual-baseline + 等 + 下載 artifact + commit baseline + eyeball diff + retrospective Q1-Q7 + memory + 3 doc syncs + PR |
| **Bottom-up total** | **~7.5-11.5 hr** | |

### Calibrated commit
NEW class `frontend-refactor-mechanical` HYBRID 0.50 (1st application) → **7.5-11.5 hr × 0.50 ≈ 4-6 hr** committed. Day 0-3（4 days；Day 0 setup+三-prong / Day 1-2 Group A+B / Day 3 closeout）。Day 3 retrospective Q2 驗 ratio；若 |delta| > 30% → 記 AD-Sprint-Plan-N。

> **這是 focused 機械重構 sprint**（~4-6 hr，與 57.14 同量級）。不切分（已夠小）。Day 數 4（Day 0-3）而非預設 5——scope 已小，5 天會是 padding；per sprint-workflow.md §Step 2「scope 差異透過內容調整」，此處透過減少 Day 數反映 scope（仍含完整 Day 0 三-prong + Day N closeout 結構）。
