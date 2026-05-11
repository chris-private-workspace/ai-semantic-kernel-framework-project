---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-16-plan.md
Purpose: Sprint 57.16 plan — AD-Inline-Style-Cleanup-Sweep-Round2. Migrate the 5 deferred feature components (ChatLayout / InputBar / SLAMetricsCard / TenantSettingsView / TenantSettingsEditForm — ~62 `style=` JSX attrs + their module-level `Record<string,CSSProperties>` stylesheets + helper fns) from inline `style=` to Tailwind utility classes (each currently carries a top-of-file `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2 */` from Sprint 57.15); remove those 5 file-level disables; flip `/chat-v2` back to full `color-contrast` in `a11y-scan.spec.ts` (drop the `allowLowContrast` special case — ChatLayout + InputBar's `#7c8696`-on-`#fbfbfd`/`#fff` ≈ 3.7-3.9:1 sub-AA placeholder/status text is the only thing keeping it disabled). Closes the Sprint 57.15 carryover. Phase 57+ Frontend SaaS — mechanical refactor / a11y-hardening tier-2 sprint.
Category: Frontend / a11y / DevOps (lint config)
Scope: Phase 57 / Sprint 57.16

Description:
    Sprint 57.15 (AD-Inline-Style-Cleanup-Sweep, tier 1 of 2) migrated 10 of 15
    feature components' inline `style=` to Tailwind, added the `no-restricted-syntax`
    `JSXAttribute[name.name='style']` ESLint guard (`error`), and re-enabled the
    `color-contrast` axe rule for 8 of 9 gated routes + the auth pages. The
    remaining 5 files were deferred to `AD-Inline-Style-Cleanup-Sweep-Round2`
    (this sprint) and each got a top-of-file `/* eslint-disable no-restricted-syntax
    -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */` so the `error`-level guard
    passes for everything else. `/chat-v2` is the one route still on
    `.disableRules(["color-contrast"])` (via the `allowLowContrast` param) because
    `ChatLayout.tsx` (a Round2 file) renders sidebar/inspector placeholder text in
    hardcoded `#7c8696` ≈ 3.7:1 on its `#fbfbfd` surface (and `InputBar.tsx` —
    also Round2 — has `#7c8696` topRow/`○ idle` status text ≈ 3.9:1 on white).

    This sprint:

    A. Migrate the 5 deferred files (US-A1 triage + US-A2 migrate) — ~62 `style=`
       JSX attrs across `ChatLayout` (8 + `styles` Record(6)) / `InputBar` (10 +
       `styles` Record(7) + `statusStyle`/`modeButton`/`sendBtn` helper fns +
       `statusPill` fn) / `SLAMetricsCard` (4; its 3 dynamic colours/bg come from
       a 3-way enum `noData`/`pass`/`fail` → finite class lookup, NOT continuous —
       the "dynamic bar widths" in its current eslint-disable reason is stale, the
       file has none) / `TenantSettingsView` (27 + `stateBadgeColor`/`planBadgeColor`
       helper fns returning hex — enum-driven) / `TenantSettingsEditForm` (13;
       pure static). The overwhelming majority is static literal → Tailwind utility
       class (compliant colour tokens for the sub-AA hex: `#666`/`#5a6377`/`#7c8696`/
       `#444` → `text-muted-foreground`; `#3b4252` → `text-foreground`; `#a00`/`#9d2e2e`
       → `text-danger`; `#e2e6ee`/`#d8dde7`/`#ddd`/`#ccc`/`#a00` → `border-border`/
       `border-danger`; `#fbfbfd`/`#f0f0f0`/`#f6f6f6`/`#fff5f5` → `bg-muted`/`bg-muted/30`/
       `bg-card`/`bg-danger/10`; `#5a78c8`/`#2f9c59`/`#1a7f37`/`#e6f4ea` → `bg-primary`/
       `text-success`/`bg-success/10`; `#c43d3d`/`#c0c8d6`/`#fce8e6` → `bg-danger`/
       `bg-muted-foreground`/`bg-danger/10`). The few enum-driven cases (risk-ish
       state badges in `TenantSettingsView` + `SLAMetricsCard` pass/fail/no-data +
       `InputBar` status pill + mode toggle active state) map to finite Tailwind
       class lookups per STYLE.md §1 "Inline-style escape hatches" → "finite class
       lookup" (mirror the Sprint 57.15 `ApprovalCard` `RISK_TEXT_CLASS` /
       `SubagentTree` `DEPTH_INDENT` pattern). NO CSS-custom-property escape hatch
       expected this sprint (no genuinely-continuous value among the 5). Each file
       gets its top-of-file `/* eslint-disable no-restricted-syntax */` REMOVED +
       MHist +1 line. Verify each renders/behaves identically (vitest unchanged).

    B. Flip `/chat-v2` to full `color-contrast` + remove the guard's last escape
       hatch (US-B1) — `a11y-scan.spec.ts`: remove the `allowLowContrast` parameter
       from `scan(page, label, allowLowContrast)` + the conditional
       `builder.disableRules(["color-contrast"])` + the `route === "/chat-v2"` arg
       at the loop call site → all 9 gated routes + the auth pages now get the full
       axe rule set; update the file-header comments + MHist (no more `/chat-v2`
       special case). Re-run `npm run e2e -- a11y/a11y-scan.spec.ts` — should be
       green now that ChatLayout + InputBar use AA-compliant `text-muted-foreground`
       (≈ 4.6:1 on `bg-muted`, ≈ 4.9:1 on white). If still red → ChatLayout/InputBar
       migration picked a too-light colour (NOT a spec change) → fix the colour.
       Also: STYLE.md §1 "Inline-style escape hatches" → drop the "(see
       `features/chat_v2/components/ChatLayout.tsx` et al. — pending
       `AD-Inline-Style-Cleanup-Sweep-Round2`)" sentence's example list (the
       whole-legacy-file `/* eslint-disable */` pattern stays documented, just
       without a current live example since none remain after this sprint); MHist
       += 57.16 entry.

    C. Closeout (US-C1) — full validation sweep (npm lint + build + vitest +
       playwright) + visual-baseline sanity (the 5 Round2 files are NOT in the 6
       `visual-regression.spec.ts` snapshot routes — app-shell / auth-login /
       verification-recent / cost-dashboard / governance / admin-tenants — and even
       if they were, the snapshot captures the loading/skeleton state before data
       fetch, per Sprint 57.15 finding; so visual baselines are expected unchanged
       and NO `gh workflow run` is needed — but `git diff --stat` is checked to
       confirm 0 snapshotted-route files touched; if any unexpectedly is, fall back
       to the 57.14 workflow path) + retrospective Q1-Q7 + memory snapshot + doc
       syncs (16-frontend-design.md timeline / sprint-workflow.md calibration +1 row
       — `frontend-refactor-mechanical` 2nd data point / STYLE.md done in US-B1 /
       SITUATION + CLAUDE.md deferred post-merge) + PR.

    Deferred OUT of this sprint (explicitly): `AD-Lighthouse-Visual-Hard-Gate`
    (turn `visual-regression.spec.ts` + `frontend-lighthouse.yml` from advisory to
    required CI checks, + the companion `waitForLoadState("networkidle")` in the
    visual specs to cover populated states) stays a separate carryover — baselines
    are confirmed stable (Sprint 57.15 workflow run = 0 diffs) but flipping to
    required is its own sprint. The 57.13 carryovers (AD-Bundle-Size optional /
    AD-i18n-Feature-Namespaces / AD-WorkOS-Prod-Redirect-Flow / AD-Frontend-RUM-SessionReplay
    / D-DAY4-2) stay untouched.

Created: 2026-05-11 (Sprint 57.16 drafting; closes the Sprint 57.15 carryover AD-Inline-Style-Cleanup-Sweep-Round2)
Last Modified: 2026-05-11
Status: Closed (Day 3 closeout — 4/4 USs done; 5/5 deferred files migrated, all 5 file-level eslint-disables removed → frontend/src 0 real inline style=; /chat-v2 color-contrast re-enabled → 9/9 gated routes + auth pages full axe rule; STYLE.md §1 cleaned; no visual-baseline workflow needed (5 files not in 6 snapshot routes); calibration ratio ~1.86 over band → AD-Sprint-Plan-13 propose 0.50→0.80 for 3rd+ app; PR opened, merge deferred to user — see retrospective.md)

Modification History (newest-first):
    - 2026-05-11: Day 3 closeout — validation sweep green (lint silent / vitest 236 / a11y-scan 2/2 with /chat-v2 full color-contrast / full e2e 40 pass 7 skip 0 fail / build 297.89 kB byte-identical / 0 backend changes); no visual-baseline workflow run; retrospective Q1-Q7 + 8-point self-check + rolling-planning self-check; memory snapshot; doc syncs (16-frontend-design.md V2 Ship Timeline +1 / sprint-workflow.md calibration matrix +1 data point + AD-Sprint-Plan-13 / STYLE.md done Day 2); plan/checklist MHist closeout; PR opened; Status → Closed
    - 2026-05-11: Day 2 — US-A2 tenant-settings (TenantSettingsView + TenantSettingsEditForm migrated) + US-B1 (a11y-scan /chat-v2 color-contrast flip — removed allowLowContrast param/conditional disableRules/route arg; STYLE.md §1 escape-hatch ChatLayout reference removed); all 5 file-level eslint-disables removed; functional scope complete
    - 2026-05-11: Day 1 — US-A1 triage + migration table; US-A2 chat-v2 (ChatLayout + InputBar) + sla-dashboard (SLAMetricsCard) migrated; 3/5 file-level disables removed; chat-v2 e2e regression sentinel green
    - 2026-05-11: Day 0 — 三-prong done; 4 D-PRE findings catalogued (D-PRE-1🟢 5-file scope unchanged; D-PRE-2🟢 0 vitest style-literal assertion; D-PRE-3🟡 STYLE.md §3 stale path; D-PRE-4🟡 STYLE.md §2 vs config token drift — strategy: critical-path uses verified tokens, elsewhere aligns with 57.15 vocab)
    - 2026-05-11: Initial creation (Sprint 57.16 — AD-Inline-Style-Cleanup-Sweep-Round2; 4 USs / Day 0-3; mirrors Sprint 57.15 structure)

Related:
    - sprint-57-15-plan.md (structural template per sprint-workflow.md §Step 1 — most recent completed sprint)
    - docs/03-implementation/agent-harness-execution/phase-57/sprint-57-15/retrospective.md (Q4 — AD-Inline-Style-Cleanup-Sweep-Round2 logged + the 5 deferred files listed) + sprint-57-15/progress.md (D-DAY1-1 scope finding + the (B) Tiered decision)
    - frontend/STYLE.md (Sprint 57.10 → 57.15 — §1 "Tailwind Utility-First" Rules + "Inline-style escape hatches" sub-§ + §3 Risk Badge Palette) + frontend/CONVENTION.md
    - frontend/eslint.config.js (Sprint 57.15 — the `no-restricted-syntax` `JSXAttribute[name.name='style']` guard) + frontend/tests/e2e/a11y/a11y-scan.spec.ts (Sprint 57.15 — the `allowLowContrast`/`route === "/chat-v2"` special case this sprint removes)
    - frontend/src/components/ui/* (the design-system layer — already inline-style-clean; the migration targets only feature components) + frontend/tailwind.config.ts (shadcn token bridge: border / background / foreground / primary / muted / destructive)
    - .claude/rules/frontend-react.md / file-header-convention.md / sprint-workflow.md / anti-patterns-checklist.md
---

# Sprint 57.16 — AD-Inline-Style-Cleanup-Sweep-Round2（5 deferred 檔 inline-style → Tailwind + `/chat-v2` color-contrast 全開）

## Sprint Goal

把 Sprint 57.15 (B) Tiered 決策延後的 5 個 feature component（`ChatLayout` / `InputBar` / `SLAMetricsCard` / `TenantSettingsView` / `TenantSettingsEditForm`——~62 個 `style=` JSX attr + 它們的 module-level `Record<string,CSSProperties>` stylesheet + helper fn；目前各帶 top-of-file `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2 */`）的 inline style 遷移到 Tailwind utility class（hardcode 的 sub-AA hex——`#666` / `#5a6377` / `#7c8696` / `#444`——換成合規的 `text-muted-foreground` 之類 design token）；少數 enum-driven 動態色（`TenantSettingsView` 的 state/plan badge、`SLAMetricsCard` 的 pass/fail/no-data、`InputBar` 的 status pill + mode toggle active）用 finite Tailwind class lookup（mirror Sprint 57.15 `ApprovalCard` `RISK_TEXT_CLASS` / `SubagentTree` `DEPTH_INDENT` pattern）；移除這 5 檔的 file-level eslint-disable + 每檔 MHist +1。把 `a11y-scan.spec.ts` 的 `/chat-v2` 特例（`scan(page, label, allowLowContrast)` 的 `allowLowContrast` 參數 + 條件式 `.disableRules(["color-contrast"])` + loop call site 的 `route === "/chat-v2"` arg）整個移除——9 個 gated route + auth pages 全部跑 full axe rule set（ChatLayout + InputBar 遷移後用 AA-compliant 的 `text-muted-foreground` ≈ 4.6:1 on `bg-muted` / ≈ 4.9:1 on white，`color-contrast` 應綠）。更新 `STYLE.md` §1 "Inline-style escape hatches" 把 ChatLayout 的 live example reference 拿掉（pattern 留著、live example 沒了——本 sprint 後無 legacy 檔殘留）。Closes the Sprint 57.15 carryover `AD-Inline-Style-Cleanup-Sweep-Round2`。

---

## Background

### 為什麼這個 sprint 存在（Sprint 57.15 carryover tier 2 of 2）

Sprint 57.15 用了 (B) Tiered 決策（D-DAY1-1：plan 寫「80 `style={{}}` / 14 檔」、re-survey 是 15 檔 / 133 `style=` attr——`no-restricted-syntax` `JSXAttribute[name.name='style']` selector 抓所有 `style=` 不分 value shape，要過 `error` 全部 133 都得遷移或 eslint-disable）→ 本 sprint 10 檔（chat-v2/subagent 4 + visual/a11y 6，其中 `ApprovalList` 是 no-op）、5 檔 → NEW `AD-Inline-Style-Cleanup-Sweep-Round2`（本 sprint）。那 5 檔目前各帶 top-of-file `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */`（`error`-level guard 對它們 disable、對其他全 enable）。

5 檔現況（grep `style=` 於 `frontend/src` 2026-05-11；Day 0 三-prong 再 pin）：

| 檔 | `style=` attrs | 額外 stylesheet / helper | dynamic? | 在 visual snapshot 內 | 阻擋 `/chat-v2` color-contrast? |
|---|---|---|---|---|---|
| `features/chat_v2/components/ChatLayout.tsx` | 8 | `styles` Record(6 keys) | 無（純靜態 layout chrome）| 否（chat-v2 不在 6 snapshot route）| ✅ `#7c8696` sidebar/inspector placeholder ≈ 3.7:1 on `#fbfbfd` |
| `features/chat_v2/components/InputBar.tsx` | 10 | `styles` Record(7) + `statusStyle()`/`modeButton()`/`sendBtn()` + `statusPill()` 回 `{label,color}` | enum-driven 色（status 4-way、mode active 2-way）| 否 | ✅ `#7c8696` topRow + `○ idle` 狀態 ≈ 3.9:1 on white；`#5a6377` mode-inactive ≈ 5.9:1 ✅ |
| `features/sla-dashboard/components/SLAMetricsCard.tsx` | 4 | — | enum-driven 色/bg（3-way: noData/pass/fail）；**注意**：目前 file-level disable reason 寫「includes dynamic bar widths」是 stale——檔裡沒有 bar width，只有 `border: 2px solid ${color}` + `backgroundColor: bg`，color/bg 都來自 3-way enum → finite class lookup（不需 CSS-var）。Day 0 三-prong 確認。| 否（sla-dashboard 不在 6 snapshot route）| 否（chat-v2 不掃 sla-dashboard component）|
| `features/tenant-settings/components/TenantSettingsView.tsx` | 27 | `stateBadgeColor()` / `planBadgeColor()` 回 hex | enum-driven 色（state 5-way → 3-bucket、plan 2-way）；其餘純靜態 | 否（tenant-settings 不在 6 snapshot route）| 否 |
| `features/tenant-settings/components/TenantSettingsEditForm.tsx` | 13 | — | 無（純靜態：`marginTop`/`border 1px solid #ccc`/`display:block`/`fontWeight:600`/`width:100%`/`padding`/`color:#a00`/`fontSize`/`fontFamily:monospace`/`display:flex`/`gap`）| 否 | 否 |
| **合計** | **~62** | 2 個 `Record<string,CSSProperties>` + 4 helper fn | 4 檔有 enum-driven 色，0 檔有真連續值 | 0 檔在 6 snapshot route | 2 檔（`ChatLayout` + `InputBar`）阻擋 `/chat-v2` |

兩個 sprint goal：(1) 清掉這 5 檔的 inline style（一致性 + 鎖住 57.15 的成果——`no-restricted-syntax` guard 對它們也 enable）；(2) `/chat-v2` 是唯一還 disable `color-contrast` 的 route——ChatLayout + InputBar 的 `#7c8696` 一遷移到 `text-muted-foreground` 就能全開（→ `a11y-scan.spec.ts` 變「9 gated route + auth pages 全 axe rule 啟用」，無任何 disable）。

### 為什麼這個 sprint *不* 重產 visual baseline（與 57.15 對照）

Sprint 57.15 因為 migration 目標檔有 7 個 render 在 cost-dashboard / governance / admin-tenants 3 個 snapshot 裡 → 順帶跑了 57.14 的 `visual-baseline` workflow（結果 0 diff——migrated component 在 snapshot 裡看不到，因為 spec 在 `app-shell` 一可見就截圖、data fetch resolve 之前 → 抓 loading/`<TableSkeleton>` 狀態）。本 sprint 的 5 檔——`ChatLayout`/`InputBar`（chat-v2，**不在** 6 snapshot route）、`SLAMetricsCard`（sla-dashboard，不在）、`TenantSettings{View,EditForm}`（tenant-settings，不在）——**沒有任何一個 render 在 6 個 `visual-regression.spec.ts` snapshot 裡**。所以 visual baseline 預期 0 變化、**不跑 `gh workflow run`**——只在 Day 3 `git diff --stat main..HEAD` 確認沒碰到 snapshotted-route 檔（若意外碰到 → fallback 走 57.14 workflow path + retrospective Q4 記）。這比 57.15 簡單。`AD-Lighthouse-Visual-Hard-Gate`（把 `visual-regression.spec.ts` + `frontend-lighthouse.yml` 從 advisory 轉 required CI check + companion `waitForLoadState("networkidle")` 覆蓋 populated state）仍是 separate carryover——baselines 已確認穩定（57.15 workflow run = 0 diff）但「轉 required」是它自己的 sprint。

### 17.md / V2 紀律對齊

- `17-cross-category-interfaces.md`：N/A——0 NEW agent-harness contract / ABC / LoopEvent / migration / API endpoint；只動前端 component + e2e spec + STYLE.md（不動 ESLint config 的 rule 集合——57.15 已加 `no-restricted-syntax` guard，本 sprint 只是讓那 5 檔的 file-level disable 消失，guard 本身不變）。
- Multi-tenant 鐵律：N/A（不動 backend / DB / API）。
- LLM Provider Neutrality：N/A（不碰 `agent_harness/`；Tailwind / @axe-core 非 LLM SDK）。
- CC Reference 不照搬：N/A（前端樣式重構）。
- 04 anti-patterns：AP-2 no orphan（移除 5 個 file-level eslint-disable 後 `no-restricted-syntax` guard 對這 5 檔也 enable——guard 真的會 fail；`/chat-v2` color-contrast 全開後真的會 scan ChatLayout/InputBar）；AP-4 no Potemkin（migration 後 sub-AA hex 真消失、`/chat-v2` 不再有特例）；AP-6 YAGNI（**不**順手做設計系統全面替換 / **不**為「將來」加沒被要求的 token / **不**重構沒壞的 component 邏輯——只 `style=` → `className`；`SLAMetricsCard` 的 3-way enum 色用 finite lookup，**不**強上 CSS-var 因為沒有真連續值）。

---

## User Stories

### Group A — Inline-style → Tailwind migration（5 deferred 檔）

#### US-A1: Day 0 三-prong 後逐檔 triage 所有 `style=`，分 static / enum-dynamic，建 migration 表

**作為** 開發者，**我希望** 5 個檔的 ~62 個 `style=` call site（含 2 個 `Record<string,CSSProperties>` + 4 個 helper fn）被逐一分類（static literal → Tailwind class / enum-driven → finite class lookup）並有一張對照表，**以便** 遷移有依據、不漏不錯。

- Day 0 三-prong 後對每檔 `grep -n "style=\|CSSProperties"` + 讀上下文，分類：
  - **static**：literal object / Record value，CSS 值全是常數（`padding`、`borderRight: "1px solid #e2e6ee"`、`color: "#3b4252"`、`background: "#fbfbfd"`、`fontSize: 14`、`overflowY: "auto"`、`marginTop`、`fontWeight: 600`、`display: "grid"`、`gridTemplateColumns`、`height: "calc(100vh - 6.5rem)"`、…）→ 對應 Tailwind utility（`p-4`、`border-r border-border`、`text-foreground`、`bg-muted`、`text-sm`、`overflow-y-auto`、`mt-4`、`font-semibold`、`grid`、`grid-cols-[240px_1fr_280px]`、`h-[calc(100vh-6.5rem)]`、…）。對 sub-AA hex：對照 `tailwind.config.ts` theme + STYLE.md §2 token table（`#666`/`#5a6377`/`#7c8696`/`#444` → `text-muted-foreground`；`#3b4252`/`#2c2c33` → `text-foreground`；`#a00`/`#9d2e2e` → `text-danger`；`#1a7f37`/`#2f9c59` → `text-success`；`#5a78c8` → `text-primary`/`bg-primary`；`#c43d3d` → `bg-danger`；`#c0c8d6` → `bg-muted-foreground`；`#e2e6ee`/`#d8dde7`/`#ddd`/`#ccc` → `border-border`；`#fbfbfd`/`#f0f0f0`/`#f6f6f6` → `bg-muted`/`bg-muted/30`；`#fff5f5`/`#fce8e6` → `bg-danger/10`；`#e6f4ea` → `bg-success/10`；`#fff` 顯式背景 → `bg-card` 或 `bg-background`；`#f5c2c2` → `border-danger/40`）。
  - **enum-dynamic**：值來自有限集（`SLAMetricsCard` 的 `noData ? "#888" : passing ? "#1a7f37" : "#a00"` + 對應 bg / `TenantSettingsView` 的 `stateBadgeColor(state)` 5-way → 3-bucket {active→success / provisioning|requested→warning / suspended|archived→muted} + `planBadgeColor` 2-way / `InputBar` 的 `statusPill` 4-way {running→primary / completed→success / cancelled→warning / error→danger / 其餘→muted-foreground} + `modeButton(active)` 2-way）→ finite Tailwind class lookup（mirror Sprint 57.15 `ApprovalCard` `RISK_TEXT_CLASS` / `SubagentTree` `DEPTH_INDENT` pattern；literal class strings 讓 JIT 看得到；移除原 hex-returning 變數/helper fn，改回 class-string）。
  - **(預期不需) continuous**：本 sprint 的 5 檔沒有真連續值（`SLAMetricsCard` 的 disable reason 寫的「dynamic bar widths」是 stale——檔裡沒有）。若 Day 0 三-prong 發現有 → 用 CSS custom property + Tailwind arbitrary value（STYLE.md §1 escape hatch 2）+ `// eslint-disable-next-line no-restricted-syntax -- CSS var only, <reason>`。
- 在 `progress.md` Day 1 列 migration 表：檔 / 行（或 stylesheet key / helper fn 名）/ 原 inline style / 分類 / 目標（Tailwind class 或 finite lookup 名）。
- **不改 component 邏輯 / 結構**（只 `style=` → `className`，必要時加 wrapper class 或把 `Record<string,CSSProperties>` 換成 `Record<string,string>` class-map）；**不刪 component**；**不順手**做設計系統替換；**不**為沒有真連續值的 case 強上 CSS-var。

**驗收**：`progress.md` Day 1 有完整 migration 表（5 檔 / ~62 occurrences + 2 stylesheet + 4 helper fn / static|enum-dynamic / 目標）；enum-dynamic 的 finite lookup 策略明確。

#### US-A2: 執行遷移——5 檔 `style=` → Tailwind class（enum 用 finite lookup）+ 移除 file-level eslint-disable + 逐檔驗渲染不變

**作為** 開發者，**我希望** 5 檔的 inline style 都換成 Tailwind utility class（enum 的按 US-A1 finite lookup）、5 個 file-level `/* eslint-disable no-restricted-syntax */` 移除、每檔 MHist +1，**以便** 樣式集中可維護、sub-AA 色消失、`no-restricted-syntax` guard 對全 codebase 生效、`/chat-v2` color-contrast 可全開。

- 按 migration 表逐檔改；每改一檔跑該 feature 的 vitest（`npm run test -- <feature>`）確認不變；改完跑全套 vitest（baseline 236 pass）。
- 移除每檔 line 1 的 `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */`（migration 完成後不再需要）。
- hex → token：先用 `tailwind.config.ts` theme + `components/ui/` 用的 token + STYLE.md §2 table；找不到合適的才用 Tailwind 內建色階（取 ≥ 4.5:1）；**不新增** design token（YAGNI）。
- `SLAMetricsCard`：3-way enum 色/bg → finite lookup（e.g. `const STATE = { noData: { text: "text-muted-foreground", border: "border-border", bg: "bg-muted" }, pass: { text: "text-success", border: "border-success", bg: "bg-success/10" }, fail: { text: "text-danger", border: "border-danger", bg: "bg-danger/10" } }` + `cn()`）；移除 `color`/`bg` hex 變數。改完更新該檔 file-level disable reason 的 stale「dynamic bar widths」措辭——不，直接移除整行（migration 完成）。
- `TenantSettingsView`：`stateBadgeColor`/`planBadgeColor` → `stateBadgeClass`/`planBadgeClass` 回 Tailwind class string（`bg-success`/`bg-warning`/`bg-muted-foreground` // `bg-primary`/`bg-muted-foreground`）；`#666` description → `text-muted-foreground`；`#a00` "No tenant" → `text-danger`；`#f0f0f0` `<pre>` bg → `bg-muted`（+ STYLE.md §4 `font-mono text-xs bg-muted rounded p-2 overflow-auto`）；其餘 27 個 static → Tailwind。
- `TenantSettingsEditForm`：13 個 static → Tailwind（`#ccc` border → `border-border`；`#a00` → `text-danger`；textarea `fontFamily: monospace` → `font-mono`；按 STYLE.md §4 code-display pattern 整理 textarea）。
- `ChatLayout`：`styles` Record(6) → `className`（grid layout `grid grid-cols-[240px_1fr_280px] h-[calc(100vh-6.5rem)]`；sidebar/inspector `border-r/l border-border bg-muted p-4 text-sm/text-[13px] text-foreground overflow-y-auto`；placeholder `text-[13px] leading-relaxed text-muted-foreground`；h3 `mt-0 text-[13px] text-muted-foreground`——`#5a6377` ≈ 5.9:1 ✅ 但統一用 token）；`gridTemplateAreas` → 直接用 grid column order（3 個 child 依序就是 sidebar/main/inspector，不需 named areas）。drop `import type { CSSProperties }`。**這檔是 `/chat-v2` color-contrast 全開的前提**——確認 placeholder 用 `text-muted-foreground`（在 `bg-muted` ≈ 4.6:1 ✅ AA）。
- `InputBar`：`styles` Record(7) + `statusStyle`/`modeButton`/`sendBtn` helper fn + `statusPill` → Tailwind；container `border-t border-border bg-card px-6 py-3 flex flex-col gap-2`；topRow `flex items-center gap-2.5 text-xs text-muted-foreground`（`#7c8696` → `text-muted-foreground` ✅ — 這是 `/chat-v2` 全開的另一前提）；`statusPill` 4-way → `STATUS_PILL = { running: {label:"● running", cls:"text-primary"}, completed: {label:"● completed", cls:"text-success"}, cancelled: {label:"● cancelled", cls:"text-warning"}, error: {label:"● error", cls:"text-danger"} }` fallback `{label:"○ idle", cls:"text-muted-foreground"}`；`modeButton(active)` → `cn("px-2 py-0.5 rounded-sm border border-border text-[11px] cursor-pointer", active ? "bg-primary text-white" : "bg-card text-muted-foreground")`；`sendBtn(disabled)` → `cn("px-4 py-2 rounded-md border-none text-white text-sm font-medium", disabled ? "bg-muted-foreground cursor-not-allowed" : "bg-primary cursor-pointer")`；`stopBtn` → `bg-danger ... text-white`；textarea per STYLE.md §4-ish（`flex-1 resize-none border border-border rounded-md px-3 py-2.5 text-sm leading-relaxed min-h-11 max-h-40 outline-none`）；errorBanner → `bg-danger/10 text-danger border border-danger/40 px-2.5 py-1.5 rounded text-xs`。drop `import type { CSSProperties }`。
- 每改一檔的 file-header MHist 加 1 行（`- 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep-Round2)`，≤ E501）；ChatLayout 的 file-header Description 裡「Inline styles only kept (Sprint 50.2 baseline; Phase 58+ Tailwind migration ...)」段落改成「migrated to Tailwind in Sprint 57.16」（不再 pending）。
- `git diff` 確認改的都是 `frontend/src/features/**/*.tsx`；無 component 邏輯改動。

**Tests**：無新增 unit test（純樣式重構；既有 vitest 涵蓋 render；component 行為不變）。若某檔的 test 斷言了 inline style 的字面值（`toHaveStyle({...})`）→ 改該斷言對齊新 class（`toHaveClass(...)`）或刪過度具體的斷言；Day 0 三-prong Prong 2 抽樣確認（57.15 D-PRE-4 對那 10 檔是 0 個——本 sprint 對這 5 檔再抽樣，特別是 `chat-v2` 的 `InputBar` / `ChatLayout` 可能有 layout test）。

**驗收**：`git diff` 只動 `frontend/src/features/**`；5 個 file-level `/* eslint-disable no-restricted-syntax */` 全移除；`grep -rEn "style=\{" frontend/src --include="*.tsx"` → 0 命中（所有 `style=` 都遷移完——本 sprint 之後 codebase 無任何 inline `style=`，除非有 CSS-var escape hatch 帶 inline `eslint-disable-next-line`——預期 0 個）；`npm run lint`（含 `no-restricted-syntax` guard + `--report-unused-disable-directives`）0 error；`npm run test`（vitest）綠（236 pass，或調斷言後綠）；`npm run build`（main bundle ≈ 不變或微降）。

### Group B — `/chat-v2` color-contrast 全開 + STYLE.md cleanup

#### US-B1: `a11y-scan.spec.ts` 移除 `allowLowContrast` 特例（9 routes + auth pages 全 axe rule）+ `STYLE.md` §1 cleanup

**作為** 維運者，**我希望** `a11y-scan.spec.ts` 不再對 `/chat-v2` 特例 disable `color-contrast`、`STYLE.md` 的 escape-hatch 文件不再指向已消失的 legacy 檔，**以便** a11y 護欄完整（9 個 gated route + auth pages 全 axe rule）、文件不過時。

- `frontend/tests/e2e/a11y/a11y-scan.spec.ts` —
  - `scan(page, label, allowLowContrast = false)` → `scan(page, label)`（移除第 3 參數 + 函數體裡的 `if (allowLowContrast) builder.disableRules(["color-contrast"])` 整段）。
  - loop call site `await scan(page, route, route === "/chat-v2")` → `await scan(page, route)`。
  - 移除/更新相關 comment（不再提 `/chat-v2` 的 ChatLayout placeholder / Round2 defer）；file-header MHist += 1（`- 2026-05-11: Sprint 57.16 — /chat-v2 color-contrast re-enabled (ChatLayout/InputBar migrated to AA tokens); all 9 gated routes + auth pages now full axe rule set`，≤ E501）。
- `frontend/STYLE.md` — §1 "Inline-style escape hatches" 最後一段「For a whole legacy file that hasn't been migrated yet, a top-of-file `/* eslint-disable no-restricted-syntax -- <AD reference> */` keeps the `error`-level guard on for everything else (see `features/chat_v2/components/ChatLayout.tsx` et al. — pending `AD-Inline-Style-Cleanup-Sweep-Round2`).」→ 把「(see ... — pending `AD-Inline-Style-Cleanup-Sweep-Round2`)」拿掉（pattern 文字留著、live example reference 沒了——本 sprint 後無 legacy 檔殘留；可改成「(no live examples remain after Sprint 57.16; the pattern stays documented for future bulk migrations)」）。MHist += 57.16 entry；`Last Modified` → 2026-05-11。若 `CONVENTION.md` 有對應 cross-ref 也順手 check（不重複內容）。
- 跑 `npm run lint`（含 guard——應 0 error，因為 US-A2 已清乾淨 + 5 個 file-level disable 已移除）；跑 `npm run e2e -- a11y/a11y-scan.spec.ts`（含 `/chat-v2` 的 full `color-contrast`——應綠；若紅則是 US-A2 給 ChatLayout/InputBar 挑了太淺的色 → 回去修色，**不是改 spec**）；跑 `npx playwright test`（含 chat-v2 的 4 個 57.8 e2e + approval-card.spec.ts——regression sentinel；ChatLayout/InputBar 結構若飄會被抓）。

**驗收**：`a11y-scan.spec.ts` 無 `allowLowContrast` / 無任何 `.disableRules(["color-contrast"])`；`npm run e2e -- a11y/a11y-scan.spec.ts` 綠（9 gated route + auth pages 全 axe rule）；`npm run lint` 0 error；`npx playwright test` 40+ pass / 0 fail（含 chat-v2 regression sentinel）；`STYLE.md` §1 escape-hatch 文字不再指向 ChatLayout；MHist + Last Modified 更新。

### Group C — Closeout

#### US-C1: 驗證 sweep + visual baseline sanity + retrospective + memory + doc syncs + PR

**作為** AI 助手，**我希望** sprint 收尾完整（驗證 / visual baseline sanity / 文件 / memory / PR），**以便** 下個 session 接得上、CI 全綠。

- Full validation sweep: `cd frontend && npm run lint`（含 guard，0 error）`&& npm run build`（main bundle ≈ 不變或微降；記 byte size）`&& npm run test`（vitest 236 pass，或調斷言後綠）`&& npx playwright test`（綠——本機 Windows `visual-regression.spec.ts` 6 個仍 opt-in skip；其餘 40+ pass / 0 fail，含 a11y-scan 的 `/chat-v2` full color-contrast + chat-v2 4 e2e + approval-card）；backend untouched — `git diff --stat main..HEAD` 確認 0 `backend/` 改動（→ backend baseline 不變：pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / 0 LLM SDK leak；不重跑）。
- **Visual baseline sanity**：本 sprint 5 檔（`ChatLayout`/`InputBar` 是 chat-v2、`SLAMetricsCard` 是 sla-dashboard、`TenantSettings{View,EditForm}` 是 tenant-settings）——**沒一個** render 在 6 個 `visual-regression.spec.ts` snapshot route（app-shell / auth-login / verification-recent / cost-dashboard / governance / admin-tenants）裡 → visual baseline 預期 0 變化、**不跑 `gh workflow run`**。Day 3 只 `git diff --stat main..HEAD` 確認沒碰到任何會出現在 6 snapshot 裡的檔（chat-v2 / sla-dashboard / tenant-settings 都不在；`pages/` 也沒動）→ 記 progress.md。**誠實標**：若意外發現某改的檔會 render 在 snapshot 裡 → fallback 走 57.14 workflow path（`gh workflow run "Playwright E2E" --ref feature/sprint-57-16-...` → 下載 artifact compare/commit）+ retrospective Q4 `AD-Visual-Baseline-Refresh-57.16`。但**預期不需要**——這是與 57.15 最大的差別（57.15 有 7 檔 render 在 3 snapshot 裡所以跑了 workflow；本 sprint 0 檔）。
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-16/progress.md` — Day 0-3 daily entries + D-PRE / D-DAY drift catalog + migration 表（Day 1）。
- 同目錄 `retrospective.md` — Q1-Q7（Q2 ratio：`actual/bottom-up` + `actual/committed`——前車 57.15 是 `actual/committed` ≈ 1.7 OVER band 但 `actual/bottom-up` ≈ 0.89，本 sprint 是 `frontend-refactor-mechanical` 第 2 data point，依 §Calibration matrix 3-sprint window rule **KEEP 0.50**——但 retro Q6 要記：若本 sprint 也 `actual/committed > 1.2`（2/2 over band）→ 提案下個 refactor sprint 用 0.70-0.80（per matrix note「if next 1-2 also > 1.2 → AD-Sprint-Plan-N propose 0.50→0.70-0.80」）；Q4 carryover AD：`AD-Lighthouse-Visual-Hard-Gate` 仍 open / 57.13 carryover / doc nits；Q5 Phase 57.17+ candidate names only；Q7 N/A——not a spike）。
- memory: `~/.claude/projects/.../memory/project_phase57_16_inline_style_round2.md` + `MEMORY.md` index +1 row（Recent Sprints top）。
- in-sprint doc syncs: `16-frontend-design.md`（V2 Ship Timeline +1 entry — inline-style sweep Round2 5/5 → all 15 feature components Tailwind-clean + `/chat-v2` color-contrast re-enabled → 9/9 gated routes + auth pages full axe rule + `no-restricted-syntax` guard now covers entire codebase with 0 file-level disables）/ `.claude/rules/sprint-workflow.md`（calibration matrix `frontend-refactor-mechanical` row 更新——+1 data point 57.16=<ratio>；2-data-point mean；verdict KEEP 0.50 or propose lift per 3-sprint window rule）/ `STYLE.md`（已在 US-B1）/ checklist [x] + plan/checklist header MHist closeout（Status: Draft → Closed）。
- post-merge doc syncs: `CLAUDE.md`（main HEAD + Latest Sprint row + Next Phase 候選 — 移除 `AD-Inline-Style-Cleanup-Sweep-Round2`；a11y color-contrast 現已 9/9 全開；carryover update）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分。
- PR: `git push` feature branch → `gh pr create`；solo-dev review_count=0；等 5 active CI checks 綠（含 `Frontend E2E` — a11y-scan `/chat-v2` full color-contrast 應綠 + visual-regression baselines 不變應綠 + chat-v2 4 e2e 應綠）；merge 由 user 決定（surface PR，不自行 merge per executing-actions-with-care）。

**驗收**：PR 開好；5 active CI checks 綠；retrospective.md 8 條 sprint-workflow self-check 全 ✅；memory snapshot 寫好。

---

## Technical Specifications

### Migration 流程（US-A1 → US-A2）

```
1. Day 0 三-prong: grep -rEn "style=\{|CSSProperties" frontend/src/features/{chat_v2,sla-dashboard,tenant-settings} → pin 5 檔 ~62 occurrences;
   讀 tailwind.config.ts theme + components/ui/ 用的 token + STYLE.md §1-§4;
   讀 a11y-scan.spec.ts 的 allowLowContrast/scan() + loop call site; 讀 eslint.config.js 的 no-restricted-syntax guard（不改它）;
   抽樣 2-3 個 vitest（特別 chat-v2 的 InputBar/ChatLayout）是否斷言 inline style 字面值; 確認 SLAMetricsCard 是否真有 bar width（disable reason 寫的——預期 stale 沒有）
2. Day 1 US-A1: 逐檔 grep -n + 讀上下文 → migration 表（static→Tailwind class / enum-dynamic→finite class lookup）
3. Day 1-2 US-A2: 逐檔改; 移除 file-level eslint-disable; 每改跑 npm run test -- <feature>; 改完跑全套 vitest;
   每檔 file-header MHist +1 行（ChatLayout 另改 Description「pending Phase 58」段→「migrated Sprint 57.16」）; git diff 確認只動 src/features/**
4. Day 2 US-B1: a11y-scan.spec.ts 移 allowLowContrast 特例（9 routes + auth pages 全 axe rule）; STYLE.md §1 escape-hatch live-example reference 拿掉;
   npm run lint (0 err) + npm run e2e -- a11y/a11y-scan.spec.ts (綠) + npx playwright test (chat-v2 regression sentinel)
5. Day 3 US-C1: full sweep + git diff --stat 確認 0 snapshotted-route 檔（→ 不跑 visual-baseline workflow）+ retro + memory + doc syncs + PR
```

### Static → Tailwind 對照（樣本；完整在 Day 1 migration 表）

| 原 inline style | Tailwind class |
|-----------------|----------------|
| `padding: "1rem"` | `p-4` |
| `padding: "0.75rem 1.5rem"` | `px-6 py-3` |
| `padding: "0.6rem 0.8rem"` | `px-3 py-2.5`（近似；或 `px-[0.8rem] py-[0.6rem]` 若要精確）|
| `color: "#666"` / `"#5a6377"` / `"#7c8696"` / `"#444"` | `text-muted-foreground`（≈ 4.6:1 on `bg-muted` / ≈ 4.9:1 on white — AA ✅）|
| `color: "#3b4252"` / `"#2c2c33"` | `text-foreground` |
| `color: "#a00"` / `"#9d2e2e"` | `text-danger` |
| `color: "#1a7f37"` / `"#2f9c59"` | `text-success` |
| `color: "#5a78c8"` / `background: "#5a78c8"` | `text-primary` / `bg-primary` |
| `background: "#c43d3d"` | `bg-danger` |
| `background: "#c0c8d6"` | `bg-muted-foreground` |
| `border: "1px solid #e2e6ee"` / `"#d8dde7"` / `"#ddd"` / `"#ccc"` | `border border-border`（`borderRight`/`borderLeft`/`borderTop` → `border-r`/`border-l`/`border-t`）|
| `border: "1px solid #f5c2c2"` | `border border-danger/40` |
| `background: "#fbfbfd"` / `"#f0f0f0"` / `"#f6f6f6"` | `bg-muted`（或 `bg-muted/30` 給淡的）|
| `background: "#fff5f5"` / `"#fce8e6"` | `bg-danger/10` |
| `background: "#e6f4ea"` | `bg-success/10` |
| `background: "#fff"` 顯式 | `bg-card`（或 `bg-background`）|
| `borderRadius: 8` / `"0.5rem"` | `rounded-md`（8px ≈ shadcn `--radius` 預設）/ `rounded-lg` |
| `borderRadius: 4` / `6` | `rounded-sm` / `rounded` |
| `width: "100%"` | `w-full` |
| `flex: 1` | `flex-1` |
| `display: "flex"` + `flexDirection: "column"` | `flex flex-col` |
| `display: "grid"` + `gridTemplateColumns: "240px 1fr 280px"` | `grid grid-cols-[240px_1fr_280px]` |
| `gridTemplateRows: "1fr"` | `grid-rows-[1fr]`（或省——單行不需）|
| `height: "calc(100vh - 6.5rem)"` | `h-[calc(100vh-6.5rem)]` |
| `overflowY: "auto"` / `overflow: "hidden"` | `overflow-y-auto` / `overflow-hidden` |
| `marginTop: "1rem"` / `0.5rem` / `0` | `mt-4` / `mt-2` / `mt-0` |
| `margin: 0` / `"0.5rem 0"` | `m-0` / `my-2` |
| `fontStyle: "italic"` | `italic` |
| `fontWeight: 600` / `700` / `"bold"` / `500` | `font-semibold` / `font-bold` / `font-bold` / `font-medium` |
| `fontSize: 14` / `13` / `12` / `11` / `"0.85rem"` / `"1.5rem"` / `"0.8rem"` | `text-sm` / `text-[13px]` / `text-xs` / `text-[11px]` / `text-[0.85rem]`（或 `text-sm`）/ `text-2xl` / `text-xs` |
| `fontFamily: "inherit"` | （刪——已繼承）|
| `fontFamily: "monospace"` | `font-mono` |
| `lineHeight: 1.5` | `leading-relaxed`（1.625）或 `leading-[1.5]` |
| `gap: "0.5rem"` / `"0.6rem"` / `4` / `"0.3rem"` | `gap-2` / `gap-2.5`（近似）/ `gap-1` / `gap-1`（近似）|
| `cursor: "pointer"` / `"not-allowed"` | `cursor-pointer` / `cursor-not-allowed` |
| `resize: "none"` | `resize-none` |
| `outline: "none"` | `outline-none` |
| `minHeight: 44` / `maxHeight: 160` / `minWidth: "200px"` | `min-h-11` / `max-h-40` / `min-w-[200px]` |
| `alignItems: "center"` / `"flex-end"` | `items-center` / `items-end` |
| `marginLeft: "auto"` | `ml-auto` |
| `display: "inline-flex"` / `"block"` | `inline-flex` / `block` |
| `border: "none"` | `border-none` |
| `textAlign: "left"` / `"right"` | `text-left` / `text-right` |
| `borderCollapse: "collapse"` | `border-collapse` |

> 近似值（`gap-2.5` ≈ `0.6rem` 實際是 `0.625rem`；`px-3 py-2.5` ≈ `0.8rem 0.6rem`）：若該值在 visual snapshot 內就用 arbitrary value 求精確（本 sprint 0 個在 snapshot 內 → 可接受 snap-to-scale 的近似——但 layout 不該明顯飄；chat-v2 的 4 個 e2e 是 regression sentinel）。

### Enum-dynamic case 處理（finite class lookup；完整在 Day 1 migration 表）

| 檔 | 原 dynamic | finite lookup 策略 |
|---|---|---|
| `SLAMetricsCard.tsx` | `color = noData ? "#888" : passing ? "#1a7f37" : "#a00"`；`bg = noData ? "#f6f6f6" : passing ? "#e6f4ea" : "#fce8e6"` | `const SLA_STATE = { noData: { text: "text-muted-foreground", border: "border-border", bg: "bg-muted" }, pass: { text: "text-success", border: "border-success", bg: "bg-success/10" }, fail: { text: "text-danger", border: "border-danger", bg: "bg-danger/10" } } as const`；`const st = noData ? SLA_STATE.noData : passing ? SLA_STATE.pass : SLA_STATE.fail`；card `cn("p-4 rounded-lg border-2 min-w-[200px]", st.border, st.bg)`；value `<p>` `cn("my-2 text-2xl font-bold", st.text)`；status `<p>` `cn("m-0 text-xs", st.text)`；label `<p>` `m-0 text-[0.85rem] text-muted-foreground`（`#444` → token）；移除 `color`/`bg` hex 變數 |
| `TenantSettingsView.tsx` | `stateBadgeColor(state)`（5-way → 3-bucket hex）；`planBadgeColor(plan)`（2-way hex）| `stateBadgeColor` → `stateBadgeClass(state)` 回 `"bg-success"` (ACTIVE) / `"bg-warning"` (PROVISIONING\|REQUESTED) / `"bg-muted-foreground"` (SUSPENDED\|ARCHIVED\|default)；`planBadgeColor` → `planBadgeClass(plan)` 回 `"bg-primary"` (ENTERPRISE) / `"bg-muted-foreground"` (else)；badge span `cn("px-2 py-0.5 rounded-sm text-white text-[0.85rem]", stateBadgeClass(data.state))`；同 plan |
| `InputBar.tsx` | `statusPill(status)` 回 `{label, color: hex}`（4-way + default）；`modeButton(active)` hex bg/color；`sendBtn(disabled)` hex bg；`stopBtn` hex；`statusStyle(color)` 用 `color` | `STATUS_PILL = { running: {label:"● running", cls:"text-primary"}, completed: {label:"● completed", cls:"text-success"}, cancelled: {label:"● cancelled", cls:"text-warning"}, error: {label:"● error", cls:"text-danger"} } as const`；`const pill = STATUS_PILL[status] ?? {label:"○ idle", cls:"text-muted-foreground"}`；status span `cn("inline-flex items-center gap-1 font-medium", pill.cls)`；mode button `cn("px-2 py-0.5 rounded-sm border border-border text-[11px] cursor-pointer", active ? "bg-primary text-white" : "bg-card text-muted-foreground")`；send button `cn("px-4 py-2.5 rounded-md border-none text-white text-sm font-medium", disabled ? "bg-muted-foreground cursor-not-allowed" : "bg-primary cursor-pointer")`；stop button `px-4 py-2.5 rounded-md border-none bg-danger text-white text-sm font-medium cursor-pointer`；移除 4 個 helper fn + `statusPill` 改名/改回 class-based |

> 全是 finite enum lookup（literal class strings → JIT 看得到），**無** CSS-custom-property escape hatch，**無** inline `eslint-disable-next-line`（5 個 file-level disable 全移除後該 codebase 0 個 inline `style=`）。若 Day 0 三-prong 發現某個我以為是 enum 的其實是連續值 → 用 STYLE.md §1 escape hatch 2（CSS var + arbitrary value + `eslint-disable-next-line` + reason），記 Day 0 drift。

### `a11y-scan.spec.ts` `/chat-v2` color-contrast 全開（US-B1）

```typescript
// 現況（Sprint 57.15）:
//   async function scan(page: Page, label: string, allowLowContrast = false): Promise<void> {
//     const builder = new AxeBuilder({ page });
//     if (allowLowContrast) { builder.disableRules(["color-contrast"]); }  // ← 只 /chat-v2
//     ...
//   }
//   ...
//   await scan(page, route, route === "/chat-v2");
// 改成（ChatLayout + InputBar 已遷移到 AA token → 全開）:
//   async function scan(page: Page, label: string): Promise<void> {
//     const builder = new AxeBuilder({ page });
//     ...
//   }
//   ...
//   await scan(page, route);
// + 更新 file-header comment（移除「/chat-v2 still disabled — ChatLayout placeholder...」段；改成「all 9 gated routes + auth pages get the full axe rule set (Sprint 57.16)」）
// + MHist += 57.16 entry
// 若全開後 /chat-v2 仍紅（ChatLayout/InputBar 漏了某個 sub-AA 色）→ 回去修色，不改 spec。
```

### `STYLE.md` §1 "Inline-style escape hatches" cleanup（US-B1）

```markdown
# 現況最後一段:
For a whole legacy file that hasn't been migrated yet, a top-of-file
`/* eslint-disable no-restricted-syntax -- <AD reference> */` keeps the
`error`-level guard on for everything else (see `features/chat_v2/components/ChatLayout.tsx`
et al. — pending `AD-Inline-Style-Cleanup-Sweep-Round2`).

# 改成（本 sprint 後無 legacy 檔殘留）:
For a whole legacy file that hasn't been migrated yet, a top-of-file
`/* eslint-disable no-restricted-syntax -- <AD reference> */` keeps the
`error`-level guard on for everything else. (No live examples remain after
Sprint 57.16 — the entire `frontend/src` is inline-style-clean — but the
pattern stays documented for future bulk migrations.)
```

### Calibration class

`frontend-refactor-mechanical` — same class as Sprint 57.15 (1st application). HYBRID weighted blend over the 4 USs (mirror 57.15):
- US-A1+A2 (triage + migrate ~62 inline-style attrs / 2 stylesheets / 4 helper fns across 5 files; per-file render verify) ≈ `mechanical-refactor × 0.40-0.45` weight ~0.70 of sprint
- US-B1 (a11y-scan `/chat-v2` flip + STYLE.md cleanup) ≈ `ci-config+a11y × 0.55` weight ~0.10 (smaller than 57.15's US-B1 — no new guard, just removing a special case)
- US-C1 (closeout — no visual-baseline workflow this sprint) ≈ `closeout × 0.80` weight ~0.20
- Weighted blend ≈ **0.48 ≈ 0.50** — KEEP `frontend-refactor-mechanical` 0.50 mid-band per §Calibration matrix 3-sprint window rule (Sprint 57.15 was 1st data point, ratio `actual/committed` ≈ 1.7 OVER band but `actual/bottom-up` ≈ 0.89 — single-sprint outliers ignored). Sprint 57.16 = 2nd data point; if it ALSO runs `actual/committed > 1.2` → retro Q6 proposes 0.50→0.70-0.80 for the next refactor sprint (per matrix note "if next 1-2 also > 1.2").

---

## File Change List

> 完整精確清單在 Day 0 三-prong 後於 checklist 落實；以下為 plan 層級概覽。

### MODIFIED Frontend — src（migration 目標，5 檔；每檔移除 line 1 的 file-level eslint-disable + MHist +1）
- `frontend/src/features/chat_v2/components/ChatLayout.tsx`（8 `style=` + `styles` Record(6)；移除 file-level disable；Description「pending Phase 58」段 → 「migrated Sprint 57.16」）
- `frontend/src/features/chat_v2/components/InputBar.tsx`（10 `style=` + `styles` Record(7) + `statusStyle`/`modeButton`/`sendBtn` + `statusPill`）
- `frontend/src/features/sla-dashboard/components/SLAMetricsCard.tsx`（4 `style=`；3-way enum 色/bg → `SLA_STATE` finite lookup；移除 stale「dynamic bar widths」disable reason 整行）
- `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx`（27 `style=` + `stateBadgeColor`/`planBadgeColor` → `*Class`）
- `frontend/src/features/tenant-settings/components/TenantSettingsEditForm.tsx`（13 `style=`；純靜態）

### MODIFIED Frontend — config / spec / docs
- `frontend/tests/e2e/a11y/a11y-scan.spec.ts` — 移除 `allowLowContrast` 參數 + 條件式 `.disableRules(["color-contrast"])` + loop 的 `route === "/chat-v2"` arg；更新 comment + MHist
- `frontend/STYLE.md` — §1 "Inline-style escape hatches" 最後一段移除 ChatLayout live-example reference；MHist + Last Modified
- （視需要）`frontend/CONVENTION.md` — 若有對應 cross-ref（不重複內容；預期不需改）
- （視 vitest）若有 test 斷言 inline style 字面值 → 對應 spec 改斷言（57.15 對另 10 檔是 0 個——本 sprint 對這 5 檔再抽樣，特別 chat-v2）

### NOT touched（與 57.15 對照）
- `frontend/eslint.config.js` — 不改（`no-restricted-syntax` guard 是 57.15 加的，本 sprint 只讓 5 個 file-level disable 消失，rule 本身不變）
- `frontend/tests/e2e/visual/visual-regression.spec.ts` + `*-chromium-linux.png` baselines — 不改（5 檔都不在 6 snapshot route 裡 → 0 變化；不跑 `gh workflow run`，只 `git diff --stat` 確認）

### Doc syncs
- in-sprint: `16-frontend-design.md`（V2 Ship Timeline +1 — Round2 5/5 → all 15 feature components Tailwind-clean + `/chat-v2` color-contrast re-enabled → 9/9 gated routes + auth pages full axe rule + `no-restricted-syntax` guard 0 file-level disable）/ `.claude/rules/sprint-workflow.md`（calibration matrix `frontend-refactor-mechanical` row +1 data point 57.16）/ `STYLE.md`（已上）/ checklist [x] + plan/checklist MHist closeout
- post-merge: `CLAUDE.md`（main HEAD / Latest Sprint / Next Phase 候選 — 移除 `AD-Inline-Style-Cleanup-Sweep-Round2`；a11y color-contrast 9/9）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

---

## Acceptance Criteria

### Functional
- [ ] (A1) Day 0 三-prong 後 `progress.md` Day 1 有完整 migration 表（5 檔 / ~62 `style=` + 2 stylesheet Record + 4 helper fn / static|enum-dynamic / 目標 Tailwind class 或 finite lookup 名）。
- [ ] (A2) 5 檔的 `style=` 全遷移：static → Tailwind utility class（sub-AA hex → ≥ 4.5:1 的 design token / Tailwind 色階）；enum-dynamic → finite Tailwind class lookup（literal class strings；mirror 57.15 `ApprovalCard`/`SubagentTree`）。5 個 line-1 `/* eslint-disable no-restricted-syntax */` 全移除。`grep -rEn "style=\{" frontend/src --include="*.tsx"` → 0 命中（codebase 無任何 inline `style=`；若有 CSS-var escape hatch 則帶 inline `eslint-disable-next-line` + reason——預期 0 個）。`git diff` 只動 `frontend/src/features/**`；無 component 邏輯改動。每改的檔 file-header MHist +1 行（≤ E501）；ChatLayout Description「pending Phase 58」段改「migrated Sprint 57.16」。`npm run lint`（含 guard + `--report-unused-disable-directives`）0 error；`npm run test`（vitest）綠（236 pass，或調斷言後綠）。
- [ ] (B1) `a11y-scan.spec.ts` 無 `allowLowContrast` / 無任何 `.disableRules(["color-contrast"])`；`scan()` 是 2-arg；loop 是 `await scan(page, route)`；MHist + comment 更新。`npm run e2e -- a11y/a11y-scan.spec.ts` 綠（9 gated route + auth pages 全 axe rule）。`STYLE.md` §1 escape-hatch 文字不再指向 ChatLayout；MHist + Last Modified 更新。`npx playwright test` 含 chat-v2 4 e2e + approval-card.spec.ts 全綠（regression sentinel）。
- [ ] (C1) full validation sweep 綠：`npm run lint`（含 guard，0 error）+ `npm run build`（main bundle ≈ 不變或微降；記 byte）+ `npm run test`（vitest 236 pass）+ `npx playwright test`（40+ pass / 0 fail / visual 在 Windows 仍 opt-in skip）；backend untouched（`git diff --stat main..HEAD` = 0 `backend/`）；visual baseline sanity（`git diff --stat` 確認 0 snapshotted-route 檔 → 不跑 workflow；或誠實標 fallback）。

### Non-functional
- pytest baseline 1676 + 4 skip — 不變（不動 backend）；mypy --strict 0/306 — 不變；9 V2 lints 9/9 — 不變；Vite build main bundle ≈ 297.89 kB — ≈ 不變或微降（少了 inline style object 字面量 + 2 個 `Record<string,CSSProperties>` + 4 helper fn → 可能微降）；Vitest 236 — 不變（純樣式重構；若調過度具體的 style 斷言則對應數字微調，記 progress.md）；ESLint — 仍 silent（0 error；移除 5 個 file-level disable 後 guard 對全 codebase 生效，`--report-unused-disable-directives` 確認無 stale disable）；LLM SDK leak 0；新增 0 npm dep。
- Playwright e2e — 40+ pass / 7 skip（本機 Windows：6 visual opt-in + 1 connectivity）；CI ubuntu — 46 → 仍 46（visual 6 個跑，baseline 不變應綠；a11y-scan `/chat-v2` full color-contrast 應綠）。
- a11y — `a11y-scan.spec.ts` 從「8/9 routes color-contrast enabled」變「9/9 gated routes + auth pages 全 axe rule 啟用，0 disable」。
- codebase — `frontend/src` 0 個 inline `style=`（含 0 個 file-level eslint-disable）；全 15 個 feature component Tailwind-clean。

### Sprint workflow discipline
- Phase README（無需，沿用 phase-57-frontend-saas）→ plan（本檔）→ checklist → Day 0 三-prong → code（Day 1-2）→ 每 day update checklist + progress.md → retrospective（Day 3）→ PR。
- 三-prong（Day 0）：Prong 1 path verify（5 src 檔 + `eslint.config.js` + `a11y-scan.spec.ts` + `visual-regression.spec.ts` + `STYLE.md` + `CONVENTION.md` + `tailwind.config.ts` + `16-frontend-design.md` + `sprint-workflow.md` 存在）+ Prong 2 content verify（`tailwind.config.ts` theme token / `components/ui/` 用的 color class；`a11y-scan.spec.ts` 現有 `allowLowContrast`/`scan()` 簽名 + loop call site；`STYLE.md` §1 escape-hatch 段落 + §3 Risk Badge Palette；`eslint.config.js` 的 `no-restricted-syntax` guard（確認不需改）；隨機 2-3 個 vitest 是否斷言 inline style 字面值（特別 chat-v2 的 InputBar/ChatLayout layout test）；5 檔的 `style=` static vs enum-dynamic 比例抽樣；確認 `SLAMetricsCard` 沒有真 bar width（disable reason 寫的——預期 stale）；確認 5 檔的 line-1 file-level disable 存在）+ Prong 3 schema verify（N/A — 不動 DB / migration / ORM / API）。

### V2 紀律 9 項 self-check（each commit + PR）
1. Server-Side First — N/A（不動 backend）；前端樣式重構
2. LLM Provider Neutrality — N/A（不碰 agent_harness）；Tailwind / @axe-core 非 LLM SDK
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. 11+1 範疇 — N/A（純前端 component + e2e spec；無範疇雜湊）
6. 04 anti-patterns — AP-2 no orphan（移除 5 file-level disable → guard 對它們也 enable 真會 fail / `/chat-v2` color-contrast 全開真會 scan）/ AP-4 no Potemkin（migration 後 sub-AA hex 真消失 / `/chat-v2` 不再有特例）/ AP-6 YAGNI（不順手做設計系統全面替換 / 不加沒被要求的 token / 不重構沒壞的 component 邏輯 / 不為沒有真連續值的 case 強上 CSS-var）
7. Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. File header convention — plan/checklist/progress/retrospective header + MHist 1-line max；每改的 component 檔更新 MHist
9. Multi-tenant rule — N/A（不動 backend / DB / API）

---

## Deliverables (checklist mapping)

- [ ] US-A1: Day 0 三-prong → `progress.md` Day 1 完整 migration 表（5 檔 / ~62 occurrences / static|enum-dynamic / 目標）（sprint-57-16-checklist.md §1.1）
- [ ] US-A2: 5 檔 `style=` → Tailwind class（enum 用 finite lookup）+ 移除 5 個 file-level eslint-disable + 每檔 vitest 驗 + 每檔 MHist +1 + `grep "style=\{"` → 0 + `npm run test` 綠 + `git diff` 只動 `src/features/**`（§1.2-1.3）
- [ ] US-B1: `a11y-scan.spec.ts` 移 `allowLowContrast`/`route === "/chat-v2"` + `STYLE.md` §1 cleanup + `npm run lint` 0 err + `npm run e2e -- a11y/a11y-scan.spec.ts` 綠 + `npx playwright test` chat-v2 regression 綠（§2.1-2.2）
- [ ] US-C1: full validation sweep + visual baseline sanity（`git diff --stat` 確認 0 snapshotted-route 檔 → 不跑 workflow）+ retrospective Q1-Q7 + memory snapshot + 3 in-sprint doc syncs + PR (+ 2 deferred post-merge)（§3.1-3.8）
- [ ] Day 0 — Branch + 三-prong + calibration baseline（§0.1-0.6）
- [ ] Day 3 — Full validation + retro + memory + PR（§3.1-3.8）

---

## Dependencies & Risks

### External dependencies
- `eslint.config.js` 的 `no-restricted-syntax` `JSXAttribute[name.name='style']` guard（Sprint 57.15 加）— 本 sprint 依賴它在移除 5 個 file-level disable 後正確抓 codebase 任何殘留 `style=`（→ 應 0 個）。0 NEW npm package。
- 57.14 `visual-baseline` workflow — 本 sprint **預期不需要**（5 檔不在 6 snapshot route）；只在 Day 3 `git diff --stat` 意外發現碰到 snapshotted-route 檔時 fallback 用（retrospective Q4 記）。
- `npx playwright install chromium` — 本機已裝（`chromium-1217` ↔ Playwright 1.59.1）；e2e 跑 a11y-scan + chat-v2 regression 用。

### Risk matrix

| Risk | 機率 | 影響 | 緩解 |
|------|------|------|------|
| ChatLayout / InputBar 遷移後 `text-muted-foreground` 在它們的背景上**仍**不過 WCAG AA（`/chat-v2` color-contrast 全開會紅）| 低-中 | 中 | `text-muted-foreground` (`hsl(215.4 16.3% 46.9%)` ≈ `#64748b`) 在 `bg-muted` (`hsl(210 40% 96.1%)` ≈ `#f1f5f9`) ≈ 4.6:1 ✅ AA；在 white ≈ 4.9:1 ✅。但 ChatLayout sidebar 原 bg 是 `#fbfbfd`（比 `bg-muted` 淺一點）→ 遷移到 `bg-muted` 後對比更好；或保留 white 用 `bg-card`。US-A2 改完先跑 `npm run e2e -- a11y/a11y-scan.spec.ts`（含 `/chat-v2` full color-contrast）；紅 = 哪個色不夠 → 換更深的（`text-foreground` 給非-secondary 文字 / 確認 placeholder 真的用 `text-muted-foreground` 不是更淺的）。**修色不改 spec** |
| chat-v2 layout 飄（ChatLayout 的 grid / InputBar 的 flex 結構在 Tailwind 化後 pixel 不等價）→ chat-v2 4 個 57.8 e2e 紅 | 中 | 中 | Tailwind arbitrary value `grid-cols-[240px_1fr_280px]` / `h-[calc(100vh-6.5rem)]` 與原 inline 值**完全等價**；`gridTemplateAreas` 移除後 3 個 child 依序就是 sidebar/main/inspector（grid auto-placement 等價）；spacing 用 scale class（`p-4`=`1rem` 等價，`gap-2`=`0.5rem` 等價，`px-6 py-3` ≈ `0.75rem 1.5rem`——後者 `px-6`=`1.5rem` ✅ `py-3`=`0.75rem` ✅ 等價）。chat-v2 的 4 個 e2e（57.8）+ approval-card.spec.ts 是 regression sentinel——US-A2/B1 改完跑 `npx playwright test`；若紅 → 是 migration 錯（漏值/用錯 class）→ 修 migration 不接受 layout 飄。`gap-2.5`≈`0.625rem` vs `0.6rem` 的微差可接受（不在 visual snapshot；e2e 不 pixel-assert layout） |
| `SLAMetricsCard` 其實有真連續值（disable reason 寫的「dynamic bar widths」非 stale）| 低 | 低 | Day 0 三-prong 讀整個 `SLAMetricsCard.tsx` 確認——目前讀到的版本只有 `border: 2px solid ${color}` + `backgroundColor: bg`（3-way enum）+ 3 個 `<p>` 的 `color`（同 enum）；無 width。若 Day 0 發現有 → 用 CSS var + arbitrary value escape hatch（STYLE.md §1 #2）+ `eslint-disable-next-line` + reason，記 Day 0 drift（這仍是「migration 完成」——只是其中 1 個 case 走 escape hatch 而非 finite lookup）|
| vitest 有 test 斷言 inline style 字面值（chat-v2 的 InputBar/ChatLayout layout test）→ migration 後紅 | 中 | 低 | Day 0 三-prong Prong 2 抽樣確認；US-A2 改 component 時同步改該斷言（→ `toHaveClass` 或刪過度具體的）；記 progress.md（這算 spec 對齊 implementation，不算「改 spec 來跑綠」）|
| `npm run build` main bundle 大幅變化（不該）| 低 | 低 | 移除 inline style object + `Record<string,CSSProperties>` + helper fn → bundle 應微降或持平；Tailwind class 是已存在的 utility（不增 CSS）。Day 3 記 byte size；若 > ±2% 變化 → 查原因 |
| scope ratio > 1.20（under-estimate；前車 57.15 `actual/committed` ≈ 1.7 over）| 中 | 中 | KEEP `frontend-refactor-mechanical` 0.50 per matrix 3-sprint window（57.15 是 1st data point，single-sprint outlier ignored）；本 sprint = 2nd data point；Day 3 retro Q2 記 ratio；若 2/2 over band → retro Q6 提案下個 refactor sprint 用 0.70-0.80（per matrix note）。bottom-up est（見 §Workload）是基於 57.15 的 `actual/bottom-up` ≈ 0.89——bottom-up 是準的——所以 committed ~3-4.5 hr 應該 close |

### Day 0 三-prong drift findings (added 2026-05-11 — per sprint-workflow.md §Step 2.5; full catalog in progress.md Day 0)

> Per §Step 2.5: drift findings go here (preserve "what was originally planned vs. what reality forced"), NOT silently into §Technical Spec / §US-*. The checklist (execution truth) reflects the adjusted approach.

- **D-PRE-1** 🟢 (false-positive grep, 0 scope shift): `grep -rEn "style=\{" frontend/src --include="*.tsx"` returns 7 files, but only **5 are real** Round2 targets — `SubagentTree.tsx` + `governance/ApprovalList.tsx` matches are in JSDoc/comment text referencing the old pattern (57.15 already migrated those 2). Plan's 5-file scope stands.
- **D-PRE-2** 🟢 (risk drops to ~0): Grep `toHaveStyle\|getComputedStyle\|\.style\b\|backgroundColor` across `frontend/tests/unit/` (the proper test root — specs are NOT colocated under `src/features/`): 0 matches across all 57 vitest specs (incl `SLAMetricsCard.test.tsx` + `TenantSettingsEditForm.test.tsx`). Risk-matrix row "vitest asserts inline-style literal" probability → ~0.
- **D-PRE-3** 🟡 (out-of-scope doc nit; logged for retrospective Q4): `STYLE.md §3 "Reference component"` says `features/governance/components/ApprovalCard.tsx` but that file **does not exist** (governance has only `ApprovalList.tsx` + `ApprovalsPage.tsx`). The 57.15 D-DAY2-1 hotfix comment in `chat_v2/ApprovalCard.tsx` correctly references `governance/components/ApprovalList.tsx`. Stale path. Not blocking — `SLAMetricsCard` uses pass/fail/no-data not §3 risk palette, so US-A2 isn't affected.
- **D-PRE-4** 🟡 (out-of-scope doc/config drift; affects vocabulary choice): `STYLE.md §2` documents `success`/`warning`/`danger`/`card`/`accent`/`thinking`/`tool`/`memory` tokens + `primary: #3B82F6` blue, but `tailwind.config.ts` + `src/index.css` define only `{background, foreground, primary, secondary, destructive, muted, border, input, ring}` + nested `-foreground` variants (and `--primary` is actually dark slate `222.2 47.4% 11.2%`, not blue). 57.15 work uses `bg-success`/`bg-danger`/`bg-warning`/`bg-warning/10`/`border-warning` (verified in `chat_v2/ApprovalCard.tsx` L49-52, `admin-tenants/TenantListTable.tsx` L46-58) — these are likely no-op CSS at runtime (Tailwind silently ignores unknown class names), but 57.15 merged green because (a) `visual-regression.spec.ts` snapshots loading state before these components render, (b) `a11y-scan` data-driven targets render as `<ErrorRetry>` not these components, (c) lint/build don't validate class-name semantics. **Sprint 57.16 strategy**: (i) `/chat-v2` color-contrast critical path (ChatLayout/InputBar — these DO render under axe scan) uses only **verified-existing** tokens (`text-muted-foreground` ≈ `#64748b` HSL ≈ 4.6:1 on `bg-muted` / 4.9:1 on white — AA ✅; `bg-muted` ≈ `#f1f5f9`; `bg-background` `#fff`; `text-foreground` near-black; `bg-primary`/`text-primary` dark slate); (ii) elsewhere (SLAMetricsCard / TenantSettingsView / TenantSettingsEditForm / InputBar enum badges) **align with 57.15 vocabulary** (`bg-success` / `bg-warning` / `bg-danger` / `bg-muted-foreground`) for visual continuity — if no-op at runtime, that's a pre-existing 57.15 condition, NOT made worse this sprint; (iii) **Do NOT** extend `tailwind.config.ts` in 57.16 — out of scope, logged for separate future sprint `AD-Style-Token-Config-Audit`; (iv) Tailwind built-in palette (`bg-red-100`/`text-red-700`/`bg-green-100`/`bg-amber-100`) as fallback for cases needing visible colour where 57.15 vocab is uncertain.

### Roll-back plan
- 每檔（或每組相關檔——如 chat-v2 的 ChatLayout+InputBar 一組）一個 commit；某檔改壞可單獨 revert（feature branch）。
- `a11y-scan.spec.ts` 的 `/chat-v2` flip 一個 commit；若全開後 `/chat-v2` 仍紅且無法本 sprint 修色（不該——但若 ChatLayout 有 component 本身的 a11y 問題不只是色）→ revert 該 commit、保留 `allowLowContrast` 特例但 comment 改成新 AD；**不**假裝沒看到。
- 整個 branch 在 PR 前都可 reset；merge 後若有 a11y / chat-v2 regression 開 hotfix PR。
- 核心交付（5 檔 inline style 清掉 + 色合規 + 5 個 file-level disable 移除 + `/chat-v2` color-contrast 全開）彼此獨立——US-A2 可不依賴 US-B1 先 merge（但本 sprint 一起做一起 PR）。

---

## Workload (calibrated)

### Bottom-up estimate by US
| US | 估計 | 備註 |
|----|------|------|
| A1 | 0.5-1 hr | 5 檔逐行 grep + 讀上下文 + 分 static/enum-dynamic + 建 migration 表（~62 occurrences + 2 stylesheet + 4 helper fn；多數 trivial static；enum-dynamic 4 個要想 finite lookup）|
| A2 | 3-4 hr | `TenantSettingsView`(27) + `TenantSettingsEditForm`(13) 純靜態很機械 ~1.5-2 hr / `ChatLayout`(8 簡單) + `InputBar`(10 + 3 helper fn + statusPill) ~1.5 hr / `SLAMetricsCard`(4 + 3-way enum→finite lookup) ~0.5 hr；+ 每檔 vitest 驗 + 每檔 MHist + 移除 5 個 file-level disable + 跑全套 vitest + 可能調 1-2 個 layout 斷言 |
| B1 | 0.5-1 hr | a11y-scan.spec.ts 移 `allowLowContrast` 特例（3 處改：`scan()` 簽名 + 函數體 + loop call site）+ comment/MHist + STYLE.md §1 escape-hatch live-example reference 拿掉 + npm run lint 驗 + npm run e2e -- a11y-scan 驗（含可能回頭修色）+ npx playwright test 跑 chat-v2 regression sentinel |
| C1 | 1.5-2 hr | full validation sweep + git diff --stat 確認 0 snapshotted-route 檔（→ 不跑 workflow，比 57.15 省）+ retrospective Q1-Q7 + memory + 3 doc syncs + PR |
| **Bottom-up total** | **~5.5-8 hr** | |

### Calibrated commit
`frontend-refactor-mechanical` HYBRID 0.50 (2nd application) → **5.5-8 hr × 0.50 ≈ 3-4 hr** committed（與 user stated「~3-5 hr」一致）。Day 0-3（4 days；Day 0 setup+三-prong / Day 1-2 Group A+B / Day 3 closeout）。Day 3 retrospective Q2 驗 ratio（`actual/bottom-up` 應 ≈ 0.85-1.0 per 57.15 evidence；`actual/committed` 可能 > 1.2 因 0.50 haircut 偏狠——若 2/2 over band 則 Q6 提案 lift）；若 |delta vs 1.0| > 30% on `actual/committed` → 記 AD-Sprint-Plan-N。

> **這是 focused 機械重構 tier-2 sprint**（~3-4 hr，比 57.15 還小——5 檔 vs 10、無 visual baseline 重產、無新 guard）。不切分（已夠小）。Day 數 4（Day 0-3）與 57.14/57.15 一致——scope 已小，5 天會是 padding；per sprint-workflow.md §Step 2「scope 差異透過內容調整」（更少 file / 更短 USs），保留完整 Day 0 三-prong + Day N closeout 結構。

---

## Open questions for user

✅ 無 open question。User 2026-05-11 chat session 明確選定 Phase 57.16 = (a) `AD-Inline-Style-Cleanup-Sweep-Round2` — 5 deferred 檔 + flip `/chat-v2` 回 full color-contrast（CLAUDE.md Next Phase 候選 (a)）。Ready for plan + checklist review + Day 0 三-prong execution against main `afd7917b`.

> 下個 sprint（Phase 57.17）plan/checklist 將在 Sprint 57.16 closeout 時依 rolling planning discipline 起草（禁止預寫）。Phase 57.17+ 候選見 Sprint 57.16 retrospective Q5（含 `AD-Lighthouse-Visual-Hard-Gate` / IAM Block B spike / `AD-Bundle-Size` optional / Tier 1 IaC + DR drill / SOC 2 + SBOM / `AD-i18n-Feature-Namespaces` 等）。

---

**End of Sprint 57.16 Plan**
