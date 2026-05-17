# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **2026-04-28 更新**：本專案進入 **V2 重構（Phase 49+）**，不再以 Microsoft Agent Framework 為主架構。V1 內容已歸檔至 `CLAUDE.backup.md`。

---

## ⚠️ 最關鍵閱讀順序（每次 session 必讀）

1. **本檔案**（CLAUDE.md）— 高層導航
2. **`docs/03-implementation/agent-harness-planning/README.md`** — V2 規劃權威入口
3. **`docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`** — 3 大最高指導原則（必讀）
4. **`docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`** — Single-source 介面權威表
5. 🆕 **`claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`** — Phase 57.7-57.9 active reference（識別 Top 10 critical gaps + Adjusted Roadmap + Buy-vs-Build 9 條決策；Phase 58.0+ 進入 Tier 1 後可降為條件性 reference）

> **權威排序**：`agent-harness-planning/` 21 份 V2 文件（20 規劃 + 1 review）> 本 CLAUDE.md > 任何 V1 文件 / 既有代碼。
> 衝突時以 V2 規劃為準。

---

## AI Assistant Notes

- **Project Location**: Windows (`C:\Users\Chris\Downloads\ai-semantic-kernel-framework-project`)
- **Server Startup**: Use `cmd /c` or direct terminal execution, NOT `start /D` or `start /B`

```bash
# Recommended (Windows)
cmd /c "cd /d <project_path>\backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
```

> **注意**：V1 backend / frontend 已封存於 `archived/v1-phase1-48/`（Sprint 49.1 完成）。啟動命令對應新 V2 backend 結構。

---

## Core Vision & Design Philosophy

> **本節定義專案根本方向。所有設計決策、建議、實作必須對齊。**

### Mission

Build enterprise AI agent teams that work like **human professional teams** — 不只是用既有框架，而是設計**業界第一個「企業級治理 + Claude Code 級閉環」混合 agent 平台**。

### Agent Team Design Principles

平台交付的 agent 必須是：
1. **Professional** — 領域專長，不是通用聊天
2. **Planned** — 結構化，不是 ad-hoc
3. **Memory-equipped** — 記得過去互動、決策、上下文
4. **Autonomous** — 自我組織、規劃、執行、重試
5. **Controllable** — 隨時可由人介入
6. **Transparent** — 所有過程與決策可審計
7. **Security-compliant** — 遵循企業合規
8. **Multi-intelligent** — 多專業 agent 協作
9. **Knowledge-aware** — RAG / 企業知識
10. **Action-capable** — 真實工具執行，不只對話

### Development Philosophy

- MAF / Claude SDK / AG-UI / Claude Code 是**靈感與參考**，**不是設計邊界**
- 許多企業需求需要**自研架構**，沒有單一框架完整提供
- **不要**「MAF 已經有 X，用 MAF 的」 — 要問「需要什麼效果」再 co-design
- Hybrid orchestrator（code-enforced steps + LLM routing）是**有意設計**，不是 workaround
- **使用者出構想，AI 助手執行協調** — 一起設計尚未存在的東西

---

## V2 Refactor Status（Phase 49+）

| Attribute | Value |
|-----------|-------|
| **Phase** | V2 22/22 ✅ + SaaS Stage 1 3/3 ✅ + SaaS Frontend 16/N（57.1/57.3/57.4/57.7/57.8/57.9/57.11/57.12×2/57.13 Foundation 1/N COMPLETE/57.14 E2E Sweep/57.15 Inline-Style-Sweep/57.16 Inline-Style-Round2/57.17 Tailwind-v4-Directive-Hotfix/57.18 Mockup-Integration-Foundation/**57.19 Mockup-Operations-Port-Round-1**）+ 57.10 PIVOTED Convention Codify ✅ |
| **Latest Sprint** | 57.19 ✅ 2026-05-17 — **AD-Mockup-Operations-Port Round 1 + AD-Mockup-Existing-Pages-Drift-Audit** (Round 1 of multi-sprint AD-Mockup-Page-X-Port epic per user 2026-05-16 alignment; 14 priority units total, this sprint shipped 7 + audit). **11 USs delivered**: US-A1 brand color → mockup indigo `hsl` approximation of `oklch(0.62 0.16 250)` / US-B1-B4 backend Cat 1/3/7/11 gap fills (GET /api/v1/loops list + extended GET /api/v1/memory/recent with `scope_id`+`time_scale` + GET /api/v1/sessions/{id}/state snapshot + GET /api/v1/subagents stub) / US-C1-C4 Operations 4 pages (OverviewPage ~580 lines + OrchestratorPage ~570 lines with 6 sub-tabs + NEW `components/ui/tabs.tsx` ~75 lines + SubagentsPage ~390 lines inline 2-col NOT Sheet per D-DAY4-1 + StateInspectorPage ~370 lines hybrid live+fixture) / US-D1-D3 topbar overlays (CommandPalette ~200 lines cmdk@^1.1.1 inside shadcn Dialog + 4 groups Actions/Pages/Tenants/Sessions + global ⌘K/Ctrl+K hotkey via AppShellV2 / NotificationsPanel ~170 lines 6 mockup fixture items + tabs + mark-all + 4 severity tokens / UserMenu EXTENDED existing per D-DAY5-1 AP-4 avoidance +~50 LoC with 3 tenant fixtures + 4 nav items Profile/MFA/Preferences/Theme toggle) / US-F1 9-page DRIFT-REPORT.md ~330 lines (Tier 1 ~10.5 hr / Tier 2 ~5.5 hr / Tier 3 ~1 hr + Round 3 epic) / US-E1 in-sprint doc syncs. **NEW features layer**: `features/loops/{types,services,hooks}` + `features/subagents/{*}` + `features/state/{*}` (Cat 1/11/7 read facades). **i18n**: +165 keys (en + zh-TW). **12 drift findings catalogued**: D-PRE-1/2/3 (Day 0 三-prong scope verify) + D-PRE-4/5/6 (in-scope Day 0 fixes) + D-DAY1-1/2 + D-DAY2-1/2 (cosmetic) + D-DAY3-1 (AD-Loop-Session-Enrich-Phase58) + D-DAY3-5 (Playwright defer pattern) + D-DAY4-1 (SubagentDetail Sheet→inline scope tightening) + D-DAY4-2 (Cat 7 list gap → AD-State-VersionChain-Phase58) + D-DAY4-3 (Vitest getByText collision → getAllByText) + D-DAY5-1 (extend UserMenu vs create dead topbar/UserMenu.tsx) + D-DAY5-2 (useTheme cascade → 3 test files wrap ThemeProvider). **Visual screenshot capture DEFERRED to Sprint 57.20 Day 0** per Sprint 57.5 reality-check dual-scoring: code-level audit serves SCOPE estimation; runtime fidelity belongs in EXECUTION sprint (Spin-up cost ~30-45 min better amortized when retrofit work begins). **Anti-stop rule continued validation**: Sprint 57.18 codification (`memory/feedback_tool_result_is_not_turn_boundary.md` + 2 CLAUDE.md scope-narrowing edits) → Sprint 57.19 Day 1-5 had **0 frequent-stop incidents**. 18 commits on branch `feature/sprint-57-19-mockup-operations-port`. **Vitest 277/277** (236 baseline + 41 NEW; 0 regression) / tsc 0 / ESLint silent (1 autoFocus in CommandPalette suppressed with WCAG 2.4.3 reason) / build 2.78s / main bundle 310.38→320.76 kB (+10.38 kB) + dropdown-menu chunk 118.36 kB (cmdk + Radix code-split) / CSS ~35.0→~36.5 kB / Backend pytest baseline preserved (Day 2 +11 integration tests for US-B1-B4 all pass; Days 3-5 zero backend changes) / LLM SDK leak 0. **10 NEW carryover ADs**: (1) 🔴 AD-Mockup-Existing-Pages-Retrofit (DRIFT-REPORT Tier 1 ~10.5 hr = ~5.8 hr calibrated at NEW class `mockup-fidelity-retrofit` 0.55 1st app candidate; **TOP Sprint 57.20 candidate** per user 2026-05-17 directive); (2) AD-Subagent-RealList-Phase58; (3) AD-Loop-Session-Enrich-Phase58; (4) AD-Overview-Backend-Wire; (5) AD-Orchestrator-Backend-Wire; (6) AD-State-VersionChain-Phase58; (7) AD-CommandPalette-Backend-Wire; (8) AD-NotificationsPanel-Backend-Feed; (9) AD-UserMenu-Tenant-Switch; (10) AD-Sprint-Plan-NEW-mockup-port-class. (PR #147 → main `24d554f6`)。calibration NEW class **`mockup-page-port-with-backend-pairing-and-audit`** 0.60 (HYBRID weighted blend: backend Cat 1/3/7/11 stubs ×0.55 ~25% + frontend mockup-port ×0.55 ~50% + audit pass ×0.85 ~15% + closeout ×0.80 ~10%) 1st app — ratio `actual/committed` = **0.56** BELOW [0.85, 1.20] band by 0.29 (`actual/bottom-up` = 0.34 → bottom-up 2× too generous, 0.60 haircut insufficient); KEEP 0.60 per `When to adjust` 3-sprint window rule; if pattern recurs 2-3× → AD-Sprint-Plan-NEW propose 0.60 → 0.40. AP 11/11 PASS (AP-4 avoided via D-DAY5-1; AP-2 honest deferrals openly documented). 詳細 retro 見 `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-19/retrospective.md` + `memory/project_phase57_19_mockup_operations_port.md` |
| **Prev Sprint** | 57.18 ✅ 2026-05-16 — **AD-Design-Mockup-Integration-Foundation** (Phase 1 of multi-sprint mockup integration epic): `cp -r reference/design-mockups/` → `design/operator-portal/` (23 files: 3 md + 1 html + 1 css + 18 jsx) as long-term design reference + NEW `INTEGRATION-LOG.md` 28-row port tracking + README "Production Integration Cross-Ref" section. **+7 semantic tokens (success/warning/danger/thinking/tool/memory/info) + 4 risk levels (low/medium/high/critical) + 2 fontFamily arrays (Geist + Noto Sans TC chains)** in `tailwind.config.ts`; **+36 CSS vars** (:root + .dark each +18, HSL approximated from mockup oklch per plan §Technical Specifications conversion table) in `index.css`. **`routes.config.ts` full rewrite**: RouteCategory 3→6 categories (operations/business/governance/observability/resources/admin) + `proposed?`/`designed?` optional fields + `CATEGORY_ORDER` exported + 13 existing re-categorized + 18 NEW PROP stub routes = 31 entries. **NEW `ComingSoonPlaceholder.tsx`** (~120 lines, `useLocation()` + ROUTES lookup, PROP/DRAFT/Priority badges, dev-only mockup link, MOCKUP_FILE_HINT id→page-X.jsx) + **18 thin wrapper pages** (`frontend/src/pages/<id>/index.tsx` re-exporting ComingSoonPlaceholder for lazy() chunking). **Sidebar.tsx refactor**: 3-state badge matrix (PROP blue `bg-thinking/16 text-thinking` / DRAFT yellow `bg-warning/16 text-warning` / SOON gray) + propCount per category header (e.g. "Operations · 7 PROP") + `renderEntryBadge()` helper + `BADGE_BASE_CLASS` const. en/zh-TW `common.json` +22 keys (18 nav.* + 4 comingSoon.* with `{{file}}` interpolation) + 6 nav.category.* reorganized. **Closes**: AD-Style-Token-Config-Audit (Sprint 57.16 D-PRE-4) + AD-Post-Hotfix-Token-Audit (Sprint 57.17 carryover) **token-coverage portion only** (contrast-ratio audit of existing components deferred to Sprint 57.19+ first port when real components consume `bg-thinking`/`text-warning`/etc.). **Opens**: AD-Mockup-Page-X-Port multi-sprint epic + AD-Brand-Primary-Color-Decision (oklch cool indigo vs dark slate) + AD-Theme-Variant-Mechanism (4 mockup variants vs single .dark) + AD-Density-Variant-Mechanism (3 mockup densities vs none) + AD-Accent-Token-Gap (`bg-accent` undefined in shadcn). **User 2026-05-16 alignment via AskUserQuestion**: Q1 整體策略 = **C 階段式** (Sprint 57.18 = scaffold; Sprint 57.19+ rolling port) / Q2 第一輪 port = 全部 4 組 = **14 priority units** (Operations 4: overview/orchestrator/subagents/state-inspector + Topbar overlays 3: CommandPalette ⌘K/NotificationsPanel/UserMenu + Auth 補完 4: register/invite/mfa/expired + Governance 補完 3: redaction/error-policy/audit-log) / Q3 後端 gap 處理 = **前後端同 sprint** backend-gap pairing for Sprint 57.19+. **12 drift findings catalogued**: D-PRE-1/2/3 (out-of-scope) → 3 NEW carryover ADs; D-PRE-4/5/6 (in-scope) → closed this sprint; D-DAY1-1/2 + D-DAY2-1/2 (cosmetic plan-text arithmetic slips) → progress.md + retrospective documents; D-DAY2-3 (resolved): `const X: FC = ...` caused `FC<{}>` vs `LazyExoticComponent<ComponentType<unknown>>` variance mismatch → removed annotation; D-DAY2-4 (cascade): Sidebar.test.tsx 3→6 categories + `getAllByText("Governance")` for category-vs-route text collision. 7 commits on branch `feature/sprint-57-18-mockup-integration-foundation` (Day 0 `2e797101` user-supplied launch / Day 1 `c06d848a` US-A1 cp mockup + `7e6feec0` US-B1+B2 tokens / Day 2 `49590c25` US-C1 routes 6-cat + `651a7a70` US-C2 ComingSoonPlaceholder + 18 wrappers / Day 3 `ae8874a2` US-C3 Sidebar badges + `e65e8b44` US-D1 closeout). **Main bundle 297.89→310.38 kB (+12.49 KB from 18 lazy chunks + ComingSoonPlaceholder code-split). CSS ~32.55→~35.0 KB (+2.45 KB from new token tree-shake). Vitest 236/236 / tsc 0 / lint silent / build 2.52s. Backend baseline unchanged (pure frontend sprint).** **Anti-stop rule validated in-sprint**: Day 0 had 4 frequent-stop incidents (~5-10 min cumulative user time) — NEW `memory/feedback_tool_result_is_not_turn_boundary.md` codified "Tool result is progress signal NOT turn boundary; stop only on (a) ambiguous strategy (b) irreversible destructive action ahead (c) explicit user pause signal" + 2 Project CLAUDE.md scope-narrowing edits (`Ask Before Acting on STRATEGY` + `Confirmation on Destructive Only`); Karpathy §1 preserved per user preference. Day 1-3 had **0 frequent-stop incidents** validating the fix. (PR #145 → main `b5dc8a17`)。calibration NEW class **`mockup-integration-foundation`** 0.55 (HYBRID weighted blend of design-ref + tokens + routes + stubs + sidebar + closeout) 1st app — ratio `actual/committed` = 1.10 ✅ **bullseye** [0.85, 1.20] band (`actual/bottom-up` = 0.58; 0.55 multiplier validated within ±5%); KEEP 0.55 per `When to adjust` 3-sprint window rule. 詳細 retro 見 `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-18/retrospective.md` + `memory/project_phase57_18_mockup_integration_foundation.md` |
| **Prev-Prev Sprint** | 57.17 ✅ 2026-05-15 — **AD-Tailwind-v4-Directive-Hotfix** (single-line CSS config hotfix): 1-line edit to `frontend/src/index.css:6-8` replaces dead Tailwind v3 directives (`@tailwind base; @tailwind components; @tailwind utilities;`) with v4 syntax (`@import "tailwindcss"; @config "../tailwind.config.ts";`). Root cause: Sprint 57.7 US-B1 installed `tailwindcss@^4.2.4 + @tailwindcss/postcss@^4.2.4` but wrote v3-style CSS — v4 PostCSS plugin **silently no-op'd** the v3 directives, **0 utility classes emitted** since 57.7. **9 ship sprints (57.7-57.16) rendered as unstyled browser-default HTML at runtime** (Times-Roman serif, default `<ul>` bullets, raw `<input>` borders, no AppShellV2 layout, no shadcn Cards) while e2e + a11y + visual-regression all passed — they inspect ARIA/DOM/text-content, **NOT computed CSS**. User opened http://localhost:3007/ post-57.16 merge, saw broken UI, triggered this hotfix. Compiled CSS **14 KB → 32.55 KB** (+18 KB; v4 tree-shake aggressive). Manual Playwright MCP verified post-fix: `/auth/login` shadcn Card + slate-black WorkOS button + rounded inputs; `/chat-v2` AppShellV2 3-column + Lucide-icon sidebar + Cards + dropdown menu. **Cascade fix #1**: ChatLayout 4 nodes (Sessions h3+p, Inspector h3+p) `text-muted-foreground` → `text-foreground/80` — Sprint 57.16 MHist claimed 4.6:1 AA was theoretical (v3 directives dead so never rendered), real combo `#64748b` on `#f1f5f9` = 3.89:1 sub-AA; new 7.6:1 AAA on bg-muted via 80% opacity blend visually still muted. **Scope-control cascade defer**: post-fix axe surfaced 2nd sub-AA pair `text-red-500 #ef4444` on white = 3.76:1 (destructive banners) — broader shadcn slate audit out of hotfix scope, re-add `disableRules(["color-contrast"])` to a11y-scan with detailed AD note → NEW `AD-Post-Hotfix-Token-Audit` Phase 57.18+ TOP candidate. **3 reality-vs-paper cascade discoveries within single 4.5-hour sprint**: (1) Tailwind v3 dead since 57.7 / (2) Sprint 57.16 4.6:1 figure theoretical never measured / (3) Sprint 57.14 FIX-008 PR-create step never executed (57.14+57.15 had 0 baseline diffs so code path never ran — 57.17 first sprint to produce baseline diff + attempt create failed with "GitHub Actions is not permitted to create or approve pull requests" → manual `gh pr create` workaround → NEW `AD-CI-7-GHA-PR-Permission`). Common pattern: DOM/ARIA tests pass on broken state because failure mode is visual-only, not behavioural — Sprint 57.5 Reality Check "code 95% / runtime 40%" extended to CI infra level. Day 0 三-prong caught 2 path drifts cheaply (D-PRE-1 baselines at `*-snapshots/` not `__screenshots__/` / D-PRE-2 visual-baseline is JOB in playwright-e2e.yml:114-194 not separate workflow file). e2e 40 pass / 7 skip / 0 fail unchanged baseline; a11y 2 pass blocking 0; CI Linux push trigger run `25957695969` green on new baselines. **3 NEW carryover ADs** (AD-Tailwind-v4-Config-Migration / AD-Post-Hotfix-Token-Audit / AD-CI-7-GHA-PR-Permission) + 4 reaffirmed (Style-Token-Config now folds into Post-Hotfix-Token / A11y-Structural-Nits / Lighthouse-Visual-Hard-Gate now actionable / 57.13 5-item bundle). (PR #142 → main `a23cf524`)。calibration NEW class `frontend-css-engine-hotfix` 0.60 1st app — ratio `actual/committed` = 0.75 BELOW [0.85, 1.20] band by 0.10 (`actual/bottom-up` = 0.45; bottom-up too conservative for 1-line + targeted cascade); single data point KEEP 0.60 per `When to adjust` 3-sprint window rule. 詳細 retro 見 `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-17/retrospective.md` + `memory/project_phase57_17_tailwind_v4_hotfix.md` |
| **Prev-Prev-Prev Sprint** | 57.16 ✅ 2026-05-11 — **AD-Inline-Style-Cleanup-Sweep-Round2** (closes the Sprint 57.15 carryover, tier 2 of 2): migrated the **5 deferred** feature components (`ChatLayout`/`InputBar`/`SLAMetricsCard`/`TenantSettingsView`/`TenantSettingsEditForm`) inline `style=` → Tailwind utility classes — full rewrites of their `Record<string,CSSProperties>` stylesheets + helper fns (`InputBar` `statusPill`/`statusStyle`/`modeButton`/`sendBtn` → `STATUS_PILL` const Record + inline `cn()`; `SLAMetricsCard` 3-way enum colour → `SLA_STATE` finite lookup; `TenantSettingsView` `stateBadgeColor`/`planBadgeColor` → `stateBadgeClass`/`planBadgeClass` returning Tailwind classes). sub-AA hex → tokens (`#7c8696`/`#666`/`#5a6377`/`#444` → `text-muted-foreground` ≈ 4.6:1 on `bg-muted` AA; `#3b4252` → `text-foreground`; `#a00`/`#9d2e2e` → `text-danger`). **Removed all 5 file-level `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2 */` directives** → `frontend/src` now has **0 real inline `style=`** (only 2 JSDoc/comment history refs remain: `SubagentTree.tsx:43` + `governance/ApprovalList.tsx:11`); the `no-restricted-syntax` `JSXAttribute[name.name='style']` guard (57.15) is now active on the entire codebase with **0 file-level disables**. **`/chat-v2` color-contrast axe rule re-enabled** in `a11y-scan.spec.ts` — removed the `allowLowContrast` param + the conditional `disableRules(["color-contrast"])` + the `route === "/chat-v2"` loop arg → **all 9 gated routes + auth pages now run the full axe rule set with no per-route disable** (4 moderate/minor reported on `/chat-v2` = `heading-order`/`landmark-*` — structural a11y nits, pre-existing, NOT color-contrast → NEW `AD-A11y-Structural-Nits`). `STYLE.md §1` escape-hatch sub-§ no longer references ChatLayout (no live examples remain). **D-PRE-4 finding (out-of-scope, → NEW `AD-Style-Token-Config-Audit`)**: `STYLE.md §2` documents tokens (`success`/`warning`/`danger`/`card`/`accent`/...) NOT defined in `tailwind.config.ts` + `src/index.css` (which has only `background`/`foreground`/`primary`(dark-slate, not the documented `#3B82F6` blue)/`secondary`/`destructive`/`muted` + nested `-foreground`); 57.15+57.16 use `bg-success`/etc. = likely no-op CSS; Sprint 57.16 uses verified tokens for the `/chat-v2` color-contrast critical path, aligns with 57.15 vocab elsewhere (visual continuity), does NOT extend the config. **D-PRE-3 (out-of-scope)**: `STYLE.md §3 "Reference component"` path `governance/components/ApprovalCard.tsx` is stale (file doesn't exist; real is `chat_v2/components/ApprovalCard.tsx`). 0 `eslint.config.js`/`tailwind.config.ts` change; **0 `backend/` change** (`git diff --stat main..HEAD` = `frontend/STYLE.md` + 5 `frontend/src/features/**/*.tsx` + `a11y-scan.spec.ts` + 3 docs) → backend baselines unchanged; **no visual-baseline workflow run** (the 5 Round2 files — chat-v2/sla-dashboard/tenant-settings — aren't in the 6 `visual-regression.spec.ts` snapshot routes — the differentiator vs 57.15 which had 7 files in 3 snapshot routes). main bundle 297.89 kB byte-identical; Vitest 236 unchanged; chat-v2 e2e 10/10 (incl approval-card CRITICAL→`#b71c1c` colour-literal regression sentinel); full e2e 40 pass / 7 skip / 0 fail. (PR #139 → main `16195fb4`)。calibration `frontend-refactor-mechanical` HYBRID 0.50 2nd app — `actual/committed` ≈ 1.86 (over band again; `actual/bottom-up` ≈ 0.96 — bottom-up accurate, 0.50 haircut too aggressive) → 2/2 over band → **AD-Sprint-Plan-13: 0.50→0.80 for the 3rd+ `frontend-refactor-mechanical` application** (near top of band like `medium-backend` 0.80; KEEP 0.50 was the rule for 57.15+57.16). 詳細 retro 見 `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-16/retrospective.md` + `memory/project_phase57_16_inline_style_round2.md` |
| **Last Convention Codify Sprint** | 57.10 PIVOTED ✅ 2026-05-09 — Frontend Convention Codify (CONVENTION.md 667→4 §addenda 行 + STYLE.md 447 行;PR #122 main `7d85df4c`;57.13 加 CONVENTION §10-§13 design-system/i18n/a11y/performance;57.14 加 §8 hermetic-mocking + visual-baseline)|
| **main HEAD** | `24d554f6` (Sprint 57.19 via PR #147, 2026-05-17) |
| **Next Phase 候選** | Phase 57.20+ 候選（user 明確選定才起草 plan）：(a) **🔴 AD-Mockup-Existing-Pages-Retrofit Tier 1** (NEW 57.19 US-F1 DRIFT-REPORT output; **TOP per user 2026-05-17 directive**) — 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80). 5 pages: cost-dashboard (3 hr) + chat-v2 (3 hr) + memory (2 hr) + verification (2 hr) + governance (1.5 hr). Tier 2 ~5.5 hr → Sprint 57.21+; Tier 3 ~1 hr + Round 3 epic / (b) **AD-Mockup-Page-X-Port Round 3 Auth 4** (Sprint 57.19 carryover) — register / invite / mfa / expired paired with IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」 / (c) **AD-Mockup-Page-X-Port Round 4 Governance 3** (Sprint 57.19 carryover) — redaction / error-policy / audit-log (DRAFT→active promote) paired with Cat 9 endpoint extensions / (d) **AD-Backend-Wire bundle** (Sprint 57.19 4 NEW ADs: Subagent-RealList-Phase58 / Loop-Session-Enrich-Phase58 / Overview-Backend-Wire / Orchestrator-Backend-Wire) — backend persistence + aggregation for Operations 4 pages (current fixture/stub); can pair with retrofit work / (e) **AD-Tailwind-v4-Config-Migration** (57.17 carryover) — full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file（~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`） / (f) **AD-Post-Hotfix-Token-Audit** (NEW 57.17 contrast-ratio portion — folds INTO AD-Mockup-Existing-Pages-Retrofit Tier 1 work since same shadcn slate base sub-AA pairs) / (g) **🆕 AD-Brand-Primary-Color-Decision** (57.18 D-PRE-1; partially actioned by Sprint 57.19 US-A1 mockup indigo — finalization decision pending) / (h) **🆕 AD-Theme-Variant-Mechanism** (57.18 D-PRE-2) / (i) **🆕 AD-Density-Variant-Mechanism** (57.18 D-PRE-3) / (j) **AD-CI-7-GHA-PR-Permission** (57.17 carryover) — `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting / (k) **AD-Lighthouse-Visual-Hard-Gate** — baselines reliable post-57.17; required CI check / (l) **🆕 AD-CommandPalette-Backend-Wire** (NEW 57.19 US-D1) — tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index / (m) **🆕 AD-NotificationsPanel-Backend-Feed** (NEW 57.19 US-D2) — 6 mockup items local state; Cat 12 SSE/poll feed spec TBD / (n) **🆕 AD-UserMenu-Tenant-Switch** (NEW 57.19 US-D3) — wire tenant switching paired with Round 2 WorkOS SCIM / (o) IAM Block B spike ~12-18 hr — WorkOS SCIM/SAML/org-level / (p) AD-Bundle-Size code-split / (q) Tier 1 IaC + DR drill ~15-20 hr / (r) SOC 2 + SBOM ~12-15 hr / (s) AD-i18n-Feature-Namespaces / (t) **AD-A11y-Structural-Nits** (57.16 carryover) — `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one` |
| **Roadmap** | Phase 49-55 V2 ✅ / Phase 56-58 SaaS Stage 1 3/3 ✅ / Phase 57+ Frontend 16/N（57.1/57.3/57.4/57.7/57.8/57.9/57.11/57.12×2/57.13 Foundation 1/N COMPLETE/57.14 E2E Sweep/57.15 Inline-Style-Sweep/57.16 Inline-Style-Round2/57.17 Tailwind-v4-Directive-Hotfix/57.18 Mockup-Integration-Foundation/**57.19 Mockup-Operations-Port-Round-1**）/ 57.10 PIVOTED Convention Codify ✅ |
| **Tech Stack** | FastAPI + React 18 + PostgreSQL + Redis（V1 沿用）|
| **Architecture** | TAO/ReAct loop + 11+1 範疇 全 Level 4（Cat 9 L5）+ LLM Provider 中性（CI-enforced）+ Multi-tenant 3 鐵律 |
| **Branch Protection** | enforce_admins=true / **review_count=0**（solo-dev policy 永久，2026-05-03 Sprint 53.2 起）/ 5 active required CI checks |

詳見 `docs/03-implementation/agent-harness-planning/06-phase-roadmap.md`。

### V2 不是「修補 V1」也不是「全部砍掉」

- ❌ **不是修補 V1**：V1 真實對齊度 27%，11 範疇 8 個處於 Level 0-2
- ❌ **不是全部砍掉**：保留 V9 分析 / CC 30-wave 研究 / V1 教訓 / 部分 infrastructure 設計
- ❌ **也不是「再寫一批新規劃文件」**（2026-05-08 加入）：V2 22/22 完成後，新領域（IAM / SaaS Stage 2 / Public API / SOC 2 / EU CRA / EU AI Act / APAC PDPA）的 doc 必須**先 thin spike → retrospective → extract design note**，禁止因 gap analysis 結果預寫多份新文件（doc-level 同 sprint-level rolling 紀律；前車：21 docs : 22 sprints 1:1 比例下 dual scoring code 85% / runtime 40%）
- ✅ **是 11+1 範疇導向重新出發**

### V2 完成 ≠ SaaS-ready ⚠️

V2（Phase 55）達成「核心能力 + 業務領域 + canary」；SaaS Stage 1（多租戶內部 SaaS / billing / SLA / DR）在 Phase 56-58。
詳見 `agent-harness-planning/00-v2-vision.md`。

---

## V2 11+1 範疇

V2 嚴格按以下範疇組織代碼，**禁止跨範疇雜湊**：

| # | 範疇 | Phase |
|---|------|-------|
| 1 | Orchestrator Layer (TAO/ReAct) | 50.1 |
| 2 | Tool Layer | 51.1 |
| 3 | Memory（雙軸：5 scope × 3 time scale） | 51.2 |
| 4 | Context Mgmt（含 Prompt Caching） | 52.1 |
| 5 | Prompt Construction | 52.2 |
| 6 | Output Parsing | 50.1 |
| 7 | State Mgmt（含 Reducer + transient/durable） | 53.1 |
| 8 | Error Handling | 53.2 |
| 9 | Guardrails & Safety | 53.3 + 53.4 |
| 10 | Verification Loops | 54.1 |
| 11 | Subagent Orchestration（4 模式，**無 worktree**） | 54.2 |
| **12** | **Observability / Tracing**（cross-cutting） | 49.4 滲透所有 |

完整定義見 `agent-harness-planning/01-eleven-categories-spec.md`。

---

## V2 五大核心約束（必守）

### 約束 1：單一範疇歸屬原則
任何代碼必須明確歸屬於 11 範疇之一（或 platform / business_domain / infrastructure / adapters）。

### 約束 2：主流量驗證原則
任何功能必須能在 UnifiedChat-V2 → API → Agent Loop 主流量中驗證。**禁止 Potemkin Feature**。

### 約束 3：LLM Provider Neutrality（中性）⭐⭐⭐
- ❌ `agent_harness/**` 任何檔案禁止 `import openai` / `import anthropic`
- ❌ 工具定義禁止用 OpenAI / Anthropic 原生 schema
- ✅ 全透過 `adapters/_base/` 的 `ChatClient` ABC + 中性 `ToolSpec` + 中性 `Message`
- ✅ CI 強制 lint 檢查
- **驗收**：30 分鐘換 provider 不改代碼

### 約束 4：Anti-Pattern 檢查原則
每個 PR 必須通過 `04-anti-patterns.md` 11 條檢查清單。

### 約束 5：測試優先原則
- 範疇單元測試 ≥ 80%
- 範疇整合測試 ≥ 60%
- 端到端閉環測試 ≥ 1 個關鍵案例

---

## Frontend Mockup-Fidelity Hard Constraint（必守）⭐⭐⭐

> **加入 2026-05-17**（Sprint 57.19 Day 0；user 明確 directive）：所有 frontend 頁面設計與 UX 必須**完全跟隨**`reference/design-mockups/`版本。**功能差距**與**後端 gap** 通過後續 sprint 逐一處理；**最最最基本是 UI / UX 視覺呈現完全按 mockup 實作**。

### 唯一視覺真相來源

| 來源 | 角色 | 何時用 |
|------|------|--------|
| **`reference/design-mockups/`** | ⭐ **canonical visual source of truth** | 所有 frontend 頁面開發 / port / retrofit 時必須 1:1 對照 |
| `design/operator-portal/` | Sprint 57.18 cp 快照（同 content）+ INTEGRATION-LOG.md | 開發 reference；但**權威性低於** `reference/design-mockups/` |
| Sprint 57.18 wired tokens (`tailwind.config.ts` + `index.css`) | Mockup oklch HSL approximation | 翻譯 mockup 樣式時優先用這些 tokens |

### 禁止項

- ❌ 用 shadcn `Card` / `Badge` / `Button` 預設值替代 mockup 的 padding / radius / shadow / color 如果**視覺不一致**
- ❌ 用「production 簡化版」名義裁剪 mockup widget / 改 layout
- ❌ 自創 i18n copy 不對照 mockup `reference/design-mockups/i18n.jsx`
- ❌ 在 retrofit 既有頁時假設「現狀已 ship 就不重做」— 既有 8 頁（57.1-57.12）在 mockup 進專案前開發，**有 drift**，將通過 Sprint 57.20+ `AD-Mockup-Existing-Pages-Retrofit` 校準

### 允許項（escape hatches，per STYLE.md §3）

- ✅ Tailwind arbitrary values `text-[#hex]` / `p-[12px]` / `rounded-[10px]` — 當 Sprint 57.18 token 詞彙無對應時
- ✅ shadcn primitives（`<Dialog>` / `<Sheet>` / `<Tabs>` / `<DropdownMenu>` / `<Command>`）— 當 mockup 的 interaction 模式直接對應這些 primitives 時
- ✅ recharts 圖表 lib — 但**配色 / 軸標 / 資料形狀必須匹配 mockup**，不用 recharts 預設

### 後端 / 功能差距處理

- 後端尚未支援 mockup 顯示的某 widget → 該 widget **仍依 mockup 視覺實作**，data 用 fixture / placeholder；同 sprint 或後續 sprint 加 backend API（per 用戶 2026-05-16 Q3「前後端同 sprint」原則）
- 不允許**因為**後端沒有就改 mockup widget layout / 刪 widget

### Mockup-Fidelity DoD（每個 frontend port / retrofit task）

1. Playwright MCP screenshot mockup target（從 `reference/design-mockups/` via `python -m http.server`）at 1440×900 viewport
2. Playwright MCP screenshot production at same viewport
3. Side-by-side compare；drift severity = cosmetic / structural / functional
4. Cosmetic → 同 commit 內 iterate Tailwind classes 至 parity；structural / functional → 在同 sprint 或 retrofit sprint 處理（不可放棄）
5. Parity verdict 記入 progress.md / DRIFT-REPORT.md

### 既有 8 ship pages drift 狀態（2026-05-17 baseline）

`/cost-dashboard` (57.1) / `/sla-dashboard` (57.1) / `/admin/tenants` list (57.4) / `/admin/tenants/settings` (57.3) / `/auth/login` (57.7) / `/auth/callback` (57.7) / `/chat-v2` (57.8) / `/governance/*` 3 pages (57.9) / `/verification` (57.11) / `/memory` (57.12) — **全部 drift 等待 Sprint 57.19 US-F1 audit + Sprint 57.20 retrofit**。詳見 `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md`（Sprint 57.19 Day 5 產出）。

---

## 「Check Existing Before Building」— V2 版

建任何新 infra 前，**權威排序**：

1. **`agent-harness-planning/` 21 份 V2 規劃**（20 規劃 + 1 review；最高權威）
2. **Sprint 49.1+ plan/checklist** — 當前迭代決定
3. **PoC worktrees 驗證模式** — poc-tools / intent-classifier / memory-system / subagent-control / KB enterprise
4. **Phase 48 LLM-native orchestrator + 7 YAML configs**（已落地新基礎）
5. **既有 V2 代碼**（archive 範圍外的部分）

### ⛔ 禁止反模式

- ❌ 「MAF 已經有 X」— MAF 已封存於 `archived/v1-phase1-48/`，V2 不再以 MAF 為核心
- ❌ 翻 `reference/agent-framework/` 找實作 — 該目錄為 MAF upstream 鏡像，僅作歷史參考，禁止用於 V2 設計
- ❌ 擴充 `backend/src/integrations/agent_framework/` — 該目錄已不存在（隨 V1 一併封存到 archived/）
- ❌ **「先寫一批新規劃文件再實作」**（2026-05-08 加入）— Sprint 57.5 reality check 已揭示 V2 21 docs : 22 sprints 1:1 比例下 paper-vs-runtime drift 普遍存在（code 85% / runtime 40%）。新規劃文件**必須**從 1 個 thin vertical spike 的 retrospective extract，禁止因 gap analysis 結果預寫多份新文件（doc-level 同 sprint-level rolling 紀律）。詳見 `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md` §3 + SITUATION-V2-SESSION-START.md §6.5

---

## V2 規劃文件導航（21 份）

| 文件 | 用途 |
|------|------|
| `agent-harness-planning/README.md` | 整體導覽 |
| `00-v2-vision.md` | V2 願景（含 V2 ≠ SaaS-ready 聲明）|
| `01-eleven-categories-spec.md` | 11 範疇 + 範疇 12 完整定義 |
| `02-architecture-design.md` | 5 層架構 + 範疇 12 cross-cutting |
| `03-rebirth-strategy.md` | 重生策略（3 區分治、archive 處理）|
| `04-anti-patterns.md` | V1 教訓 11 條反模式 |
| `05-reference-strategy.md` | 參考資料策略 |
| `06-phase-roadmap.md` | **22 sprint 路線圖（5.5 個月）** |
| `07-tech-stack-decisions.md` | 技術選型 |
| `08-glossary.md` | 術語表 |
| `08b-business-tools-spec.md` | 業務領域工具 spec（5 domain × 24 工具）|
| `09-db-schema-design.md` | DB Schema |
| `10-server-side-philosophy.md` | ⭐ **3 大最高指導原則（必讀）**|
| `11-test-strategy.md` | 測試策略 |
| `12-category-contracts.md` | 範疇間整合契約 |
| `13-deployment-and-devops.md` | 部署 + CI/CD + Docker + DR |
| `14-security-deep-dive.md` | STRIDE / OWASP / GDPR |
| `15-saas-readiness.md` | SaaS Stage 1 規劃 |
| `16-frontend-design.md` | 前端 12 頁 sprint 對應 |
| `17-cross-category-interfaces.md` | ⭐ **跨範疇接口 single-source registry** |
| `v2-review-integration-report-20260428.md` | 兩輪 expert review 整合報告 |

---

## V1 歷史資產（保留參考）

V1 雖被 V2 取代，但下列資產持續保留作為**設計知識**：

| 資產 | 位置 | 用途 |
|------|------|------|
| V9 Codebase Analysis | `docs/07-analysis/V9/00-index.md` | V1 baseline（Phase 1-44，1028 files） |
| Claude Code Source Study | `docs/07-analysis/claude-code-study/` | V2 設計藍本（30 waves） |
| V8 Analysis | `docs/07-analysis/Overview/full-codebase-analysis/` | 歷史對比 |
| ClaudeDocs | `claudedocs/` | 持續使用（V2 新文件繼續寫入）|

> **使用準則**：V9 是 V1 的真相快照；引用時要標註「V1 baseline」，不能當作 V2 架構描述。

---

## Development Commands

> Sprint 49.1 已完成 backend / frontend 遷移；以下命令對應 V2 結構。

### Unified Dev Environment

```bash
# View status
python scripts/dev.py status

# Start services
python scripts/dev.py start              # All
python scripts/dev.py start backend
python scripts/dev.py start frontend

# Stop / Restart / Logs
python scripts/dev.py stop [service]
python scripts/dev.py restart [service]
python scripts/dev.py logs docker -f
```

### Service Ports

| Service | Port |
|---------|------|
| Backend | 8000 |
| Frontend | 3005 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| RabbitMQ | 5672 / 15672 |

---

## Code Standards

規則目錄 Hybrid 載入（2026-05-09 起）：

**🔴 Always-loaded（4 條 critical，自動進每個 session）**

| Rule | Scope |
|------|-------|
| `.claude/rules/sprint-workflow.md` | 5 步 sprint 流程 + Day 0 三-prong + calibration matrix |
| `.claude/rules/file-header-convention.md` | File header + MHist 1-line max |
| `.claude/rules/multi-tenant-data.md` | tenant_id 鐵律 + RLS + GDPR / PII |
| `.claude/rules/anti-patterns-checklist.md` | 11 條 PR 自檢 |

**📋 On-demand（10 條，需要時主動 Read `docs/rules-on-demand/X.md`）**

| Rule | Trigger |
|------|---------|
| `category-boundaries.md` | 新建檔案 / 跨範疇 import |
| `llm-provider-neutrality.md` | 動 LLM 呼叫 / 新 adapter |
| `adapters-layer.md` | 修改 `adapters/` |
| `observability-instrumentation.md` | 新增埋點 / Cat 12 |
| `code-quality.md` | mypy strict / 跨平台 lint 問題 |
| `testing.md` | Contract test / multi-tenant test |
| `git-workflow.md` | Commit message / branch naming |
| `backend-python.md` | Python backend 通用約定 |
| `frontend-react.md` | React/TS 通用約定 |
| `graphify-usage.md` | 用 graphify-out/ 探索 codebase |

> 完整 trigger 表 + 任務情境配對見 [`.claude/rules/README.md`](.claude/rules/README.md)。

### Quick Commands

```bash
# Backend
cd backend && black . && isort . && flake8 . && mypy . && pytest

# Frontend
cd frontend && npm run lint && npm run build
```

---

## Environment Setup

複製 `.env.example` 到 `.env`。關鍵變數：

```bash
# Database / Redis / RabbitMQ
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=ipa_password
REDIS_HOST=localhost
RABBITMQ_HOST=localhost

# Azure OpenAI（V2 主供應商）
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional adapters（V2 透過 adapter 層支援）
# ANTHROPIC_API_KEY=<key>
# OPENAI_API_KEY=<key>
```

---

## ClaudeDocs — AI Assistant Execution Docs

`claudedocs/` 是 AI 助手與開發者協作的動態執行紀錄，獨立於 `docs/`。

### Directory Structure

```
claudedocs/
├── 1-planning/          # 整體規劃
├── 2-sprints/           # Sprint 執行
├── 3-progress/          # 進度（daily / weekly / milestone）
├── 4-changes/           # 變更紀錄（bug-fixes / feature-changes）
├── 5-status/            # 狀態報告
├── 6-ai-assistant/      # AI 助手相關（prompts / analysis）
├── 7-archive/           # 歷史封存
├── CLAUDE.md            # 詳細索引
└── README.md            # 快速導覽
```

### AI Assistant Situation Prompts

依當前情境使用對應 prompt 模板：

| Situation | 文件 | 何時使用 |
|-----------|------|---------|
| **SITUATION-1** | `6-ai-assistant/prompts/SITUATION-1-PROJECT-ONBOARDING.md` | 專案初次接觸 |
| **SITUATION-2** | `SITUATION-2-FEATURE-DEV-PREP.md` | 功能開發準備 |
| **SITUATION-3** | `SITUATION-3-FEATURE-ENHANCEMENT.md` | 功能增強或修復 |
| **SITUATION-4** | `SITUATION-4-NEW-FEATURE-DEV.md` | 新功能開發執行 |
| **SITUATION-5** | `SITUATION-5-SAVE-PROGRESS.md` | 儲存進度、結束 session |
| **SITUATION-6** | `SITUATION-6-SERVICE-STARTUP.md` | 服務啟動、環境檢查 |
| **SITUATION-7** | `SITUATION-7-NEW-ENV-SETUP.md` | 新開發環境設置 |

### Change Record Conventions

修 bug 或實作變更時，於 `claudedocs/4-changes/` 建立對應文件：

| Type | Directory | Naming |
|------|-----------|--------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` |

### Daily Workflow

1. **開工前**：看 `claudedocs/3-progress/daily/` 最新 log
2. **修 bug**：在 `4-changes/bug-fixes/` 建 FIX
3. **功能變更**：在 `4-changes/feature-changes/` 建 CHANGE
4. **下班前**：用 SITUATION-5 儲存進度

---

## Developer Preferences

### Communication
- **Language**: 用戶溝通用繁體中文
- **Documentation**: CLAUDE.md / 設計文件用英文
- **Detail**: 詳細解釋並附理由
- **Confirmation on Destructive Only**: `git push` / `git reset --hard` / `git push --force` / 刪 production code / 改 shared infra / 改 CI/CD pipeline / 發外部訊息（Slack / email / PR comments）/ 上傳第三方 tool 前必問。**NOT destructive**: Write / Edit / Read 在已對齊 scope 內 / TaskCreate / Glob / Grep / Bash read-only 命令 / 創建 plan §File Change List 內預期的新檔。詳見 [`memory/feedback_tool_result_is_not_turn_boundary.md`](memory/feedback_tool_result_is_not_turn_boundary.md)。

### Code Style
- **Comments**: 程式碼註解用英文
- **Git Commit**: 功能完成才 commit
- **Testing**: 新功能必須附單元測試

### Behavior Rules
- **Proactive Assistance**: 主動參與開發
- **Ask Before Acting on STRATEGY**: 範圍模糊 / 多個有效方法 / 用戶意圖不明 / 新 sprint 方向時必先問。**NOT trigger**: tool result return / Write/Edit/Read 在已對齊的 scope 內 / sprint plan 內的下一步 / batch parallel tool calls。Karpathy §1「不清楚就停下」仍適用但限真 ambiguous decision，**不適用** tool chaining within aligned scope。詳見 [`memory/feedback_tool_result_is_not_turn_boundary.md`](memory/feedback_tool_result_is_not_turn_boundary.md)。
- **Deep Error Analysis**: 找根因，不貼膏藥
- **Never Delete Tests**: 不刪測試 / 不關測試 / 不跳測試
- **Never Delete Docs**: 未授權不刪文件
- **Never Delete Checklist Items**: 只能 `[ ]` → `[x]`，不能刪除未勾選項（Phase 42 Sprint 147 違規前車之鑑）
- **Check Existing Before Building**: 建新 infra 前，先查 V2 21 份規劃 + Sprint plan + PoC worktrees（**不是查 MAF/AG-UI/SDK** — 它們已封存於 archived/）

---

## Karpathy Coding Guidelines

> 減少常見 LLM coding 錯誤的行為守則。Source: [Andrej Karpathy](https://x.com/karpathy/status/2015883857489522876)

### 1. Think Before Coding
- 明說假設；不確定就問
- 多種解讀並陳，不要私下選一個
- 有更簡單方案就說；該 push back 就 push back
- 不清楚就停下、命名困惑、發問

### 2. Simplicity First
- 最少代碼解決問題
- 不寫沒被問的功能 / 不為單次使用造抽象 / 不加未要求的「彈性」
- 不為不可能的情境寫 error handling
- 200 行能變 50 行就重寫

### 3. Surgical Changes
- 只動必要的；不順手「改善」相鄰代碼
- 不重構沒壞的東西；配合既有風格即使你會做不同
- 看到無關的 dead code 就提一下，不刪
- 你的改動產生的 orphan 才清；既有的 dead code 不關你事

### 4. Goal-Driven Execution
- 任務轉成可驗證目標：「Add validation」→「寫無效輸入測試 → 通過」
- 多步任務先給簡短 plan：每步 + verify
- 強成功標準才能獨立 loop；弱標準需要不斷澄清

---

## File Header & Modification Convention

> 完整規範：[`.claude/rules/file-header-convention.md`](.claude/rules/file-header-convention.md)

### 三大原則

- ✅ **要寫**：檔案開頭 docstring（Purpose / Category / Created / Modification History）
- ✅ **要寫**：重要區塊開頭的 WHY 說明（含 Alternative considered）
- ❌ **不寫**：行內每行 `# this assigns x to y` 噪音
- ❌ **不寫**：「used by X」「added for Y」git log 已記錄的內容

### Python File Header 速查範本

```python
"""
File: <relative path>
Purpose: <一句話>
Category: <11+1 範疇之一>
Scope: <Sprint XX.Y / Phase ZZ>

Description:
    <2-5 行：做什麼、為何存在、與哪些範疇互動>

Key Components:
    - ClassA: <用途>
    - function_b(): <用途>

Created: YYYY-MM-DD (Sprint XX.Y)
Last Modified: YYYY-MM-DD

Modification History (newest-first):
    - YYYY-MM-DD: Initial creation (Sprint XX.Y) - <reason>

Related:
    - 01-eleven-categories-spec.md §<section>
    - 17-cross-category-interfaces.md Contract <N>
"""
```

> TypeScript / Markdown 範本見獨立 rule 檔。

### 三層級修改對應

| 改動類型 | 範例 | 文件處理 |
|---------|------|---------|
| **Trivial** | typo / format / rename 變數 | git log 即可，**不更新** Modification History |
| **Behavioral** | 修 bug / 新功能 / 重構邏輯 | ✅ 更新 Last Modified + 加 Modification History + 建 `claudedocs/4-changes/FIX-XXX` |
| **Structural** | 拆檔 / 範疇遷移 / 介面變更 | ✅ 上述全做 + 更新 Sprint progress + 視情況更新 17.md |

### 核心禁止

- ❌ 行內歷史註解（git blame 已有）
- ❌ 保留 dead code 註解（直接刪）
- ❌ Commit message 寫「update / fix / changes」（必須具體 type + scope + why）
- ❌ 行為變更跳過 `claudedocs/4-changes/`

> 例外（生成檔 / vendor / 空 `__init__.py` / 測試檔簡化）與完整禁止項見 [`file-header-convention.md`](.claude/rules/file-header-convention.md)。

---

## CRITICAL: Sprint Execution Workflow

> **強制流程。Phase 35-38（Sprint 107-120）違規前車之鑑，永不重蹈。**

每個 sprint 必須按以下順序：

### Step 1: Create Plan File
寫 code 前，建 `docs/03-implementation/agent-harness-planning/phase-XX-*/sprint-XXX-plan.md`：
- User Stories（作為 / 我希望 / 以便）
- Technical specifications
- File change list
- Acceptance criteria

> **🔴 格式一致性鐵律**：起草前必先讀**最近一個 completed sprint 的 plan**（不是 49.1 / 50.1 等舊樣板，是最新 closed 的）作為模板。
> 章節編號 / 章節命名 / Day 結構 / 每 task 細節水平**必須一致**。
> Sprint scope 差異透過**內容**調整（更多 stories / 更多 file），**不是透過結構**調整（多加章節 / 改 Day 數）。
> 例：51.2 plan 9 sections（0-9）→ 52.1 plan 必須也 9 sections + 命名一致；違反 = 用戶矯正成本（前車：52.1 v1→v3 三輪重寫）。

### Step 2: Create Checklist File
建 `phase-XX-*/sprint-XXX-checklist.md`：
- `- [ ]` 列出每個交付項
- 驗證標準
- 連結 plan

> **🔴 格式一致性鐵律**：同 Step 1 — 必讀最近 completed sprint checklist 為模板。
> Day 數預設 5（Day 0-4，與 V2 累計 sprint 一致）；Day 4 含 retro + closeout。
> 每 task 含：bold task 描述 / 3-6 sub-bullets（具體 case / 配置 / DoD）/ Verify command。
> 細節水平：同等 scope sprint，checklist 行數 ±20% 內。

### Step 3: Implement Code
plan + checklist 都有了才開始 code。

### Step 4: Update Checklist
進度推進時，將 `[ ]` 改 `[x]`。**禁止刪除未勾選項**。

### Step 5: Create Progress Doc
建 `docs/03-implementation/agent-harness-execution/sprint-XXX/progress.md`。

### 正確流程
```
Phase README → Sprint Plan → Sprint Checklist → Code → Update Checklist → Progress Doc
```

### 錯誤流程（Phase 35-38 發生過）
```
Phase README → Code → Progress Doc  ❌ 跳過 plan + checklist
```

參考範例：`agent-harness-planning/phase-49-foundation/sprint-49-1-plan.md` + `sprint-49-1-checklist.md`

---

## Important Notes

1. **Target Market**: 台灣 / 香港。技術詞英文，使用者面向繁體中文。
2. **BMAD Methodology**: 沿用 BMad Agile workflow。狀態追蹤於 `docs/bmm-workflow-status.yaml`。
3. **MAF Status**: V1 整合的 Microsoft Agent Framework 已於 Sprint 49.1 完成封存到 `archived/v1-phase1-48/`。V2 不再以 MAF 為核心；如需 multi-agent builder 才有條件保留 adapter。

---

## graphify

This project has a graphify knowledge graph at `graphify-out/`.

### Navigation rules
- 回答架構或代碼問題前，讀 `graphify-out/GRAPH_REPORT.md`（god nodes + community structure）
- 若 `graphify-out/wiki/index.md` 存在，優先用而非讀原始檔案
- 最佳閱讀順序：L1–10（summary）→ L2184–2322（god nodes + surprising connections + hyperedges）。用 Grep 跳到特定 community 在 L2323+

### Confidence handling（CRITICAL）
當前 graph 約 25% EXTRACTED / 75% INFERRED。
- **God Nodes 與 Community structure** — 高信任，可直接用
- **Surprising Connections** — 多為 INFERRED，當作假說，引用前用 Read/Grep 驗證
- **架構理由引用** — 用 `/graphify explain <node>` 確認支撐 edge 是 EXTRACTED（已驗證）還是 INFERRED（LLM 猜的）。若只有 INFERRED 支撐，回答時必須明示

### ⚠️ Scope Control
**`.graphifyignore` 必須存在於專案根**。`graphify update .` 不會記住初次 build 排除哪些目錄；缺少 `.graphifyignore` 會把 `reference/`（2,213 files）、`claudedocs sample/`（217 files）、debug PNG（~124 files）全納入。

驗證 scope：
```bash
python -c "from graphify.detect import detect; from pathlib import Path; r = detect(Path('.')); print(f'{r[\"total_files\"]} files, {r[\"graphifyignore_patterns\"]} ignore patterns')"
# 預期：~3,300 files、30 ignore patterns
```

若 >5,000 files，停下修 `.graphifyignore` 再繼續。

### Maintenance

| Command | When | Cost |
|---------|------|------|
| `graphify update .` | 代碼變更（.py / .ts / .tsx）| Free |
| `/graphify --update` | docs / markdown / PDF / image | Paid (LLM) |
| `/graphify .` | 全重建（罕用） | Paid (LLM) |

預設：每次 code commit 後跑 `graphify update .` — 它用 manifest.json diff，小變更幾乎瞬間完成。

---

## V1 Backup

V1 完整 CLAUDE.md 已保留於 `CLAUDE.backup.md`。如需查閱 V1 架構（MAF + Claude SDK + AG-UI）細節請參考。

---

**Last Updated**: 2026-05-17 (Sprint 57.19 — AD-Mockup-Operations-Port Round 1 + AD-Mockup-Existing-Pages-Drift-Audit. Round 1 of multi-sprint AD-Mockup-Page-X-Port epic. 11 USs: A1 brand → mockup indigo + B1-B4 backend Cat 1/3/7/11 gap fills + C1-C4 Operations 4 pages (Overview ~580 / Orchestrator ~570 + 6 sub-tabs + NEW components/ui/tabs.tsx / Subagents ~390 inline 2-col NOT Sheet per D-DAY4-1 / StateInspector ~370 hybrid live+fixture) + D1-D3 topbar overlays (CommandPalette ⌘K cmdk inside shadcn Dialog + 4 groups / NotificationsPanel 6 fixture items / UserMenu EXTEND existing per D-DAY5-1 AP-4 avoidance) + F1 9-page DRIFT-REPORT.md ~330 lines (Tier 1 ~10.5 hr) + E1 in-sprint doc syncs. NEW features layer (Cat 1/11/7 read facades). +165 i18n keys. NEW calibration class `mockup-page-port-with-backend-pairing-and-audit` 0.60 1st app ratio 0.56 BELOW band by 0.29 (actual/bottom-up 0.34 → bottom-up 2× too generous, 0.60 haircut insufficient; KEEP 0.60 per `When to adjust` 3-sprint window rule). Main bundle 310.38→320.76 kB (+10.38 KB) + dropdown-menu chunk 118.36 kB (cmdk + Radix code-split). Vitest 277/277 / tsc 0 / ESLint silent / build 2.78s / backend pytest baseline preserved. 18 commits. Anti-stop rule Day 1-5 zero incidents (Sprint 57.18 codification continued validation). 12 drift findings catalogued. Visual screenshot capture DEFERRED to Sprint 57.20 Day 0 per Sprint 57.5 reality-check dual-scoring. 10 NEW carryover ADs (TOP = AD-Mockup-Existing-Pages-Retrofit Tier 1 = Sprint 57.20 top candidate). PR #147 → main `24d554f6`)
**Recent Sprints (詳情見 memory/)**: 57.19 (AD-Mockup-Operations-Port Round 1 — 11 USs: A1 brand + B1-B4 backend + C1-C4 Operations 4 + D1-D3 topbar + F1 9-page DRIFT-REPORT.md; NEW class `mockup-page-port-with-backend-pairing-and-audit` 0.60 ratio 0.56 below band) / 57.18 (AD-Design-Mockup-Integration-Foundation — cp mockup → design/operator-portal/ + 11 semantic + 4 risk tokens + RouteCategory 3→6 + 18 PROP stubs + ComingSoonPlaceholder + 18 wrappers + Sidebar PROP/DRAFT/SOON badges; 0.55 1st app ratio 1.10 bullseye) / 57.17 (AD-Tailwind-v4-Directive-Hotfix — 1-line v4 directive fix + ChatLayout AA cascade + 3 reality-vs-paper cascade discoveries) / 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2 — 5 deferred inline `style=` → Tailwind + `/chat-v2` color-contrast re-enabled 9/9) / 57.15 (AD-Inline-Style-Cleanup-Sweep — 10/15 inline `style=` → Tailwind + guard + color-contrast 8/9) / 57.14 (AD-Frontend-E2E-Sweep — e2e suite green + visual CI mechanism) / 57.13 (Frontend Foundation 1/N COMPLETE — auth flow / design-system / obs / i18n / a11y / Lighthouse) / 57.12 (Agent Harness UI Suite) / 57.11 (Verification ship) / 57.10 (Convention Codify) / 57.9 (Governance ship)
**Project Start**: 2025-11-14
**Current Phase**: V2 22/22 ✅ + SaaS Stage 1 3/3 ✅ + SaaS Frontend 16/N（57.19 AD-Mockup-Operations-Port Round 1 + AD-Mockup-Existing-Pages-Drift-Audit — Round 1 of multi-sprint AD-Mockup-Page-X-Port epic per user 2026-05-16 alignment; 14 priority units total, this sprint shipped 7 + audit. 11 USs landed: US-A1 brand `oklch(0.62 0.16 250)` indigo / US-B1-B4 backend Cat 1/3/7/11 gap fills (loops list + memory scope_id+time_scale + state snapshot + subagents stub) + 11 integration tests / US-C1-C4 Operations 4 pages (Overview 580 lines / Orchestrator 570 lines with 6 sub-tabs + NEW components/ui/tabs.tsx ~75 lines / Subagents 390 lines inline 2-col D-DAY4-1 / StateInspector 370 lines hybrid live+fixture) / US-D1-D3 topbar overlays (CommandPalette ~200 lines cmdk@^1.1.1 + 4 groups + global ⌘K via AppShellV2 / NotificationsPanel ~170 lines 6 fixtures / UserMenu EXTEND existing per D-DAY5-1 AP-4) / US-F1 9-page DRIFT-REPORT.md ~330 lines (Tier 1 ~10.5 hr feeds Sprint 57.20 retrofit) / US-E1 in-sprint doc syncs. NEW features layer features/loops/{*} + features/subagents/{*} + features/state/{*} (Cat 1/11/7 read facades). +165 i18n keys en+zh-TW. 12 drift findings catalogued; D-DAY5-1 AP-4 avoidance (extend existing UserMenu vs create dead topbar/UserMenu.tsx); D-DAY5-2 cascade (3 test files wrap ThemeProvider). Visual screenshot capture DEFERRED to Sprint 57.20 Day 0 per Sprint 57.5 reality-check dual-scoring (code-level audit serves SCOPE; runtime fidelity belongs in EXECUTION sprint). Anti-stop rule: Day 1-5 zero frequent-stop incidents (Sprint 57.18 codification continued validation). 18 commits on branch `feature/sprint-57-19-mockup-operations-port`. Main bundle 310.38 → 320.76 kB (+10.38) + dropdown-menu chunk 118.36 kB (cmdk + Radix code-split). CSS ~35.0 → ~36.5 kB. Vitest 277/277 PASS (236 Sprint 57.18 baseline + 41 NEW; 0 regression) / tsc 0 / ESLint silent (1 autoFocus suppressed with WCAG 2.4.3) / build 2.78s / backend pytest baseline preserved / LLM SDK leak 0. (PR #147 → main `24d554f6`)。calibration NEW class `mockup-page-port-with-backend-pairing-and-audit` 0.60 (HYBRID weighted blend: backend Cat 1/3/7/11 ×0.55 ~25% + frontend mockup-port ×0.55 ~50% + audit pass ×0.85 ~15% + closeout ×0.80 ~10%) 1st app ratio actual/committed 0.56 BELOW [0.85, 1.20] band by 0.29 (actual/bottom-up 0.34 → bottom-up 2× too generous, 0.60 haircut insufficient); KEEP 0.60 baseline per `When to adjust` 3-sprint window rule; if pattern recurs 2-3× → AD-Sprint-Plan-NEW propose 0.60 → 0.40. AP 11/11 PASS）。Carryovers: 10 NEW (AD-Mockup-Existing-Pages-Retrofit 🔴 TOP Sprint 57.20 / AD-Subagent-RealList-Phase58 / AD-Loop-Session-Enrich-Phase58 / AD-Overview-Backend-Wire / AD-Orchestrator-Backend-Wire / AD-State-VersionChain-Phase58 / AD-CommandPalette-Backend-Wire / AD-NotificationsPanel-Backend-Feed / AD-UserMenu-Tenant-Switch / AD-Sprint-Plan-NEW-mockup-port-class) + 5 reaffirmed (AD-Post-Hotfix-Token-Audit folds INTO retrofit Tier 1 / AD-CI-7-GHA-PR-Permission / AD-Tailwind-v4-Config-Migration / AD-Lighthouse-Visual-Hard-Gate / AD-A11y-Structural-Nits). Phase 57.20+ 候選 20 條 pending user 明確選定（見上方表格 Next Phase 候選 row）。

[Sprint 57.18 historical row preserved below for chronological reference; see CLAUDE.md V2 Refactor Status table for current Prev Sprint detail.]
57.18 (closed) AD-Design-Mockup-Integration-Foundation — Phase 1 of multi-sprint mockup integration epic. cp `reference/design-mockups/` → `design/operator-portal/` (23 files: 3 md + 1 html + 1 css + 18 jsx) as long-term design reference + NEW `INTEGRATION-LOG.md` 28-row port tracking + README "Production Integration Cross-Ref" section. **+7 semantic tokens (success/warning/danger/thinking/tool/memory/info) + 4 risk levels (low/medium/high/critical) + 2 fontFamily arrays** in `tailwind.config.ts`; **+36 CSS vars** (:root + .dark each +18, HSL approximated from mockup oklch) in `index.css`. `routes.config.ts` full rewrite: RouteCategory 3→6 (operations/business/governance/observability/resources/admin) + `proposed?`/`designed?` optional fields + `CATEGORY_ORDER` exported + 13 existing re-categorized + 18 NEW PROP stub routes = 31 entries. NEW `ComingSoonPlaceholder.tsx` (~120 lines, `useLocation()` + ROUTES lookup, PROP/DRAFT/Priority badges, dev-only mockup link) + 18 thin wrapper pages. Sidebar.tsx refactor: 3-state badge matrix (PROP blue / DRAFT yellow / SOON gray) + propCount per category header + `renderEntryBadge()` helper + `BADGE_BASE_CLASS` const. en/zh-TW +22 i18n keys (18 nav.* + 4 comingSoon.*). **Closes**: AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit token-coverage portion only (contrast-ratio audit of existing components deferred to Sprint 57.19+ first port). **Opens**: AD-Mockup-Page-X-Port multi-sprint epic + AD-Brand-Primary-Color-Decision + AD-Theme-Variant-Mechanism + AD-Density-Variant-Mechanism + AD-Accent-Token-Gap. User 2026-05-16 AskUserQuestion alignment: C 階段式 + 14 priority units (Operations 4 + Topbar 3 + Auth 4 + Governance 3) + 前後端同 sprint backend-gap pairing for Sprint 57.19+. 12 drift findings catalogued (D-PRE-1/2/3 out-of-scope NEW ADs; D-PRE-4/5/6 closed in-scope; D-DAY1-1/2 + D-DAY2-1/2 cosmetic plan text arithmetic; D-DAY2-3 resolved FC variance fix; D-DAY2-4 Sidebar.test cascade). 7 commits on branch `feature/sprint-57-18-mockup-integration-foundation`. Main bundle 297.89→310.38 kB (+12.49 KB lazy chunks). CSS ~32.55→~35.0 KB (+2.45 KB tree-shake). Vitest 236/236 / tsc 0 / lint silent / build 2.52s. Backend baseline unchanged (pure frontend sprint). **Anti-stop rule validated in-sprint**: Day 0 had 4 frequent-stop incidents (~5-10 min cost) → NEW `memory/feedback_tool_result_is_not_turn_boundary.md` + 2 Project CLAUDE.md scope-narrowing edits (`Ask Before Acting on STRATEGY` + `Confirmation on Destructive Only`); Karpathy §1 preserved per user preference; Day 1-3 had 0 incidents. (PR #145 → main `b5dc8a17`)。calibration NEW class `mockup-integration-foundation` 0.55 (HYBRID weighted blend) 1st app ratio actual/committed 1.10 ✅ bullseye [0.85, 1.20] band (actual/bottom-up 0.58 validates 0.55 multiplier within ±5%); KEEP 0.55 per `When to adjust` 3-sprint window rule）。Carryovers: 5 NEW ADs (Mockup-Page-X-Port multi-sprint epic / Brand-Primary-Color-Decision / Theme-Variant-Mechanism / Density-Variant-Mechanism / Accent-Token-Gap) + 57.17 carryover (Post-Hotfix-Token-Audit contrast-ratio portion / CI-7-GHA-PR-Permission / Tailwind-v4-Config-Migration) + AD-Lighthouse-Visual-Hard-Gate / AD-A11y-Structural-Nits. Phase 57.19+ 候選 15 條 pending user 明確選定（見上方表格 Next Phase 候選 row）。

[Sprint 57.17 historical row preserved below for chronological reference; see CLAUDE.md V2 Refactor Status table for current Prev Sprint detail.]
57.17 (closed) AD-Tailwind-v4-Directive-Hotfix — 1-line edit to `frontend/src/index.css:6-8` replaces dead v3 directives with v4 `@import "tailwindcss"; @config "../tailwind.config.ts";`. Sprint 57.7 US-B1 installed `tailwindcss@^4.2.4 + @tailwindcss/postcss@^4.2.4` but wrote v3-style CSS — v4 PostCSS plugin **silently no-op'd** directives, 0 utility classes emitted since 57.7. 9 ship sprints 57.7-57.16 rendered as **unstyled browser-default HTML at runtime** (Times-Roman serif + bare `<ul>` bullets + raw `<input>` borders, no AppShellV2/no shadcn) while e2e + a11y + visual-regression all passed inspecting only ARIA/DOM/text. Compiled CSS 14 KB → 32.55 KB (+18 KB). Playwright MCP verified: `/auth/login` shadcn Card + slate-black WorkOS + rounded; `/chat-v2` AppShellV2 3-column + Lucide sidebar + Cards + dropdown. **Cascade fix**: ChatLayout 4 nodes `text-muted-foreground` → `text-foreground/80` (Sprint 57.16 claimed 4.6:1 was theoretical, real 3.89:1 sub-AA → new 7.6:1 AAA on bg-muted). **Color-contrast deferral**: post-fix axe surfaced 2nd sub-AA pair `text-red-500 #ef4444` on white = 3.76:1 (destructive banners) — broader audit out of hotfix scope, re-add `disableRules(["color-contrast"])` → NEW AD-Post-Hotfix-Token-Audit Phase 57.18+ TOP candidate. **3 reality-vs-paper cascade discoveries within single 4.5-hour sprint**: Tailwind v3 dead since 57.7 / Sprint 57.16 4.6:1 figure theoretical never measured / Sprint 57.14 FIX-008 PR-create never executed (first sprint to produce baseline diff + attempt — failed with `GitHub Actions is not permitted to create or approve pull requests` → manual `gh pr create` workaround). Day 0 三-prong caught 2 path drifts cheaply (D-PRE-1 baselines at `*-snapshots/` not `__screenshots__/` / D-PRE-2 visual-baseline is JOB in playwright-e2e.yml:114-194 not separate workflow file)). 3 NEW carryover ADs (AD-Tailwind-v4-Config-Migration / AD-Post-Hotfix-Token-Audit / AD-CI-7-GHA-PR-Permission) + 4 reaffirmed (Style-Token-Config folds into Post-Hotfix-Token / A11y-Structural-Nits / Lighthouse-Visual-Hard-Gate now actionable / 57.13 5-item bundle). e2e 40 pass / 7 skip / 0 fail unchanged baseline; a11y 2 pass blocking 0; CI Linux run `25957695969` green on new baselines. calibration NEW class `frontend-css-engine-hotfix` 0.60 1st app — ratio `actual/committed` = 0.75 BELOW band by 0.10, single data point KEEP 0.60 per `When to adjust` 3-sprint window rule）。Carryovers: AD-Post-Hotfix-Token-Audit (NEW, TOP) / AD-CI-7-GHA-PR-Permission (NEW) / AD-Tailwind-v4-Config-Migration (NEW) / AD-Lighthouse-Visual-Hard-Gate (now actionable) / AD-A11y-Structural-Nits (57.16, re-evaluable post-fix) / 57.13 5-item bundle 未動。Phase 57.18+ 候選 10 條 pending user 明確選定（見上方表格 Next Phase 候選 row）。

[Sprint 57.16 historical row preserved below for chronological reference; see CLAUDE.md V2 Refactor Status table for current Prev Sprint detail.]
57.16 (closed) AD-Inline-Style-Cleanup-Sweep-Round2 — 5 deferred feature components (`ChatLayout`/`InputBar`/`SLAMetricsCard`/`TenantSettingsView`/`TenantSettingsEditForm`) inline `style=` → Tailwind utility classes (full rewrites of their `Record<string,CSSProperties>` stylesheets + helper fns; sub-AA hex → verified tokens `text-muted-foreground`/`bg-muted`/etc. for the `/chat-v2` color-contrast critical path, 57.15 vocab elsewhere)；**all 5 file-level `/* eslint-disable no-restricted-syntax */` directives removed** → `frontend/src` 0 real inline `style=` (2 JSDoc/comment history refs only)；`no-restricted-syntax` `JSXAttribute[name.name='style']` guard now active codebase-wide with 0 file-level disables；**`/chat-v2` color-contrast axe rule re-enabled** in `a11y-scan.spec.ts` (removed `allowLowContrast` param/conditional `disableRules`/route arg) → all 9 gated routes + auth pages full axe rule set (4 moderate/minor on `/chat-v2` = `heading-order`/`landmark-*` structural nits → NEW `AD-A11y-Structural-Nits`)；`STYLE.md §1` escape-hatch ChatLayout reference removed；D-PRE-4 (out-of-scope → NEW `AD-Style-Token-Config-Audit`): `STYLE.md §2` token table drift；0 `eslint.config.js`/`tailwind.config.ts`/`backend/` change → backend baselines unchanged；no visual-baseline workflow run (5 Round2 files not in the 6 snapshot routes)；main bundle 297.89 kB byte-identical；chat-v2 e2e 10/10；full e2e 40 pass / 7 skip / 0 fail；calibration `frontend-refactor-mechanical` 0.50 2nd app ratio `actual/committed` ≈ 1.86 → 2/2 over band → AD-Sprint-Plan-13: 0.50→0.80 for the 3rd+ application）。Carryovers: AD-Lighthouse-Visual-Hard-Gate (baselines confirmed stable) / AD-Style-Token-Config-Audit (NEW) / AD-A11y-Structural-Nits (NEW) / AD-Bundle-Size(降 optional) / 57.13 carryover 未動。Phase 57.17+ 候選 8 條 pending user 明確選定（見上方表格 Next Phase 候選 row）。
**main HEAD**: `24d554f6` (Sprint 57.19 via PR #147, 2026-05-17)
**V2 Authority**: `docs/03-implementation/agent-harness-planning/` (21 docs — 20 規劃 + 1 review)
**V1 Reference**: `CLAUDE.backup.md` + `docs/07-analysis/V9/00-index.md`
