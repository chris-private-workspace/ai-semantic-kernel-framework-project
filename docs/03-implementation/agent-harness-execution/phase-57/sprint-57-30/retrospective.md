# Sprint 57.30 — Retrospective (Day 5 closeout)

**Date**: 2026-05-23
**Branch**: `feature/sprint-57-30-chatv2-shell-repoint` (squash-merge to main pending PR)
**Base SHA**: `2d9d9e9f` (main; Sprint 57.29 squash-merge PR #163)
**Sprint Goal**: 2nd Phase-2 per-page verbatim-CSS re-point on `/chat-v2` + carryover shell hotfix (closes `AD-UserMenu-Mockup-Structural-Deltas` from Sprint 57.29)

## Q1 — What went well

1. **First-pass success across all 4 implementation days**. Day 1 (UserMenu Radix-drop + avatar split), Day 2 (6 shell/composer components), Day 3 (7 turns + blocks), Day 4 (6 inspector + blocks + ApprovalCard) — every `code-implementer` agent delegation produced 5-gate-green code on first run, with at most 1 spec adaptation per day (Day 4's `blocks.test.tsx:108` `.border-danger/40` → `.block.verification.failed`). No agent had to re-do work.

2. **PARITY verdict on `/chat-v2`** — the sprint's primary deliverable. Triage agent confirmed: 3-col `.chat-shell` grid + ChatHeader `.panel-toggle` + `.session-item` pills + `.composer` band + filled `Send` button + **Inspector 4-tab pill nav (Turn / Trace / Memory / Tree)** — all 10+ mockup elements visibly rendered in production. Before-state's `Inspector` was a single text heading "Turn Trace Memory Tree"; after-state is a proper 4-tab navigator. The largest structural transition in the sprint.

3. **`AD-UserMenu-Mockup-Structural-Deltas` closed clean** (Sprint 57.29 carryover). Day 1 visual verification (`day1-usermenu-flush.png` + `day1-usermenu-trigger-26.png`) confirmed both user-reported bugs resolved at pixel level: avatar trigger 26×26 (was 36×36 — 38% over-inflated); dropdown panel flush against topbar bottom edge (was ~5-8px gap from Radix portal positioning override).

4. **Day-0 三-prong second fully-applied sprint of the Phase-2 era** — 6 drift findings catalogued before any Day 1 code: D1 GREEN (Radix-drop scope contained to `UserMenu.tsx`), D2 RED (avatarStyle reuse root cause confirmed), D3 GREEN (Topbar Icon sizes match mockup — user "icons bigger" perception = 100% avatar 38% inflation effect; ~15 min Day 1 audit work saved), D4+D5 YELLOW deferred (Topbar raw `<button>` vs mockup `<Button>` primitive; missing Tweaks button), D6 GREEN (chat-v2 mockup CSS classes already in `styles-mockup.css`). The Prong-2 content-verify caught **D3** (turning a planned audit task into a "0 fix" close); without Day-0 ROI, the audit would have consumed ~30 min of Day 1.

5. **22-route regression sweep: 0 catastrophic / 0 structural-regression** — meets plan §Acceptance Criteria. Final triage: 1 🟢 PARITY (chat-v2) + 18 🟡 acceptable-cosmetic (avatar 36→26 shell-wide) + 3 ⚪ pre-existing fails (`/subagents` `/memory` `/verification` — Sprint 57.29 `AD-Overview-PreExisting-Route-Crashes` carryover, before == after on those routes).

6. **Day 5 orphan cleanup bonus** — dropping `frontend/src/components/ui/dropdown-menu.tsx` (after UserMenu Radix-drop made it a 0-consumer orphan) + `npm uninstall @radix-ui/react-dropdown-menu` saved **116.87 KB / 38.37 KB gzipped** from the production bundle. Closes the "extract `useDismiss` hook deferred until 2nd consumer arrives" deferred decision cleanly: we never needed Radix, so the wrapper itself was YAGNI debt from Sprint 57.13 US-B3.

## Q2 — What didn't go well + calibration ratio

**Calibration**:
- Bottom-up estimate per plan §Workload: ~17-21 hr
- Committed (HYBRID 0.60 blend): ~10-13 hr
- **Actual**: ~4-5 hr of agent-assisted wall-clock across 5 days (orchestrator + 4 code-implementer agents + 1 triage agent)
- **Ratio actual / committed ≈ 0.35-0.50** — **BELOW [0.85, 1.20] band** by ~0.35

Why under-band:
1. Phase-1 structural rewrite (Sprint 57.21) had already aligned chat-v2 structure to mockup pattern — Phase-2 was "CSS-class swap per file" not "rewrite from scratch".
2. Sprint 57.28 verbatim CSS foundation made the per-component edit one-pass-per-file (every needed `.chat-shell` / `.session-item` / `.block.thinking` etc. already in `styles-mockup.css`).
3. Day 1 hotfix bundled in (~3-4 hr estimated) but actually ~45 min after agent first-pass success.
4. Agent-assisted pacing accelerated: Day 1 ~45 min / Day 2 ~10 min/file / Day 3 ~9 min/file / Day 4 ~8 min/file (pattern reuse compounded).

**Pattern**: this is the 2nd application of `frontend-verbatim-css-repoint` class. Sprint 57.29 was 1st (ratio ≈1.0, in-band middle, agent-assisted compressed but per-day-tracked). Sprint 57.30 ratio diverges meaningfully (~0.40). With 2 data points spanning the band edge, this could be either (a) a true bimodal class needing split (like Sprint 57.20-21 `frontend-mockup-direct-port` split into token-sweep vs structural-rewrite), or (b) sampling noise from compressed agent-assisted sessions.

**Per `When to adjust` 3-sprint window rule**: KEEP `frontend-verbatim-css-repoint` 0.60 baseline. If Sprint 57.31+ ratio drifts low again (3rd data point in same range), propose split between "structural-heavy re-point" (0.65) and "css-swap-only re-point" (0.40). Logged as carryover `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`.

## Q3 — What we learned (generalizable)

1. **"Mockup is two layers" is reinforced by this sprint**. The lesson Sprint 57.22 / `frontend-mockup-fidelity.md` established — visual layer is `styles.css` (verbatim-copied to `styles-mockup.css`) + component layer is `*.jsx` (rewritten as typed `.tsx`) — held perfectly across 23 production component edits. NOT ONE component needed to "translate" a mockup style into Tailwind for production; every visual literal was either a mockup CSS class consumed directly OR a verbatim inline-style copied byte-for-byte.

2. **shadcn primitives are an interaction-only fallback, not a styling layer**. Day 2 dropped `<Badge>` + `<Button>` from chat-v2 shell components (shadcn `<Badge variant="...">` API mismatched mockup `.badge.thinking` CSS class form). Day 4 dropped `<Tabs>` from ChatInspector (uses pre-Sprint-57.18 design-system tokens). Pattern: when mockup styling diverges from shadcn defaults, use mockup class form verbatim. When mockup styling matches shadcn primitive's actual computed style (e.g. some `<Button variant="ghost" size="sm">` rendering exactly `.btn.ghost[data-size="sm"]`), the shadcn primitive is OK — but verify it's not introducing token drift first.

3. **Radix dependencies should be evaluated for portal-positioning impact**. `AD-UserMenu-Mockup-Structural-Deltas` root cause was Radix `<DropdownMenu>`'s floating-ui portal overriding `position: absolute; top: 50; right: 12` verbatim styles. The lesson: any 3rd-party primitive that owns positioning (floating-ui, popper.js, focus-trap) can defeat verbatim CSS. Use Radix `<Dialog>` only when its modal-overlay positioning IS the intent; use mockup `useDismiss` hook + native positioning otherwise.

4. **Day-0 Prong-2 content-verify ROI on `AD-Plan-3` continues to validate**. Day 0 caught D3 (Topbar Icon sizes already correct; user's "icon big" perception was 100% the avatar 36→26 effect). Without it, Day 1's US-B3 audit would have done 30 min of icon-by-icon comparison, only to find 0 drift. ROI estimate: ~15-20 min Day 0 cost saved ~30 min Day 1 = 1.5-2× — modest but compounding (4 sprints of consistent ROI since AD-Plan-3 promotion).

5. **Orphan cleanup adds to PR's positive bundle-size delta**. Removing `dropdown-menu.tsx` + `@radix-ui/react-dropdown-menu` dependency was technically a Day 5 polish step, but it's a 116 KB raw / 38 KB gzipped improvement to the production bundle — a meaningful frontend performance win. Pattern: after any Radix-drop / shadcn-drop refactor, audit `package.json` for the now-unused dependency.

## Q4 — Audit Debt deferred (carryover)

Logged in `claudedocs/1-planning/next-phase-candidates.md`:

- **`AD-Topbar-Use-Button-Primitive`** (YELLOW, Sprint 57.30 D4 finding) — production Topbar uses raw `<button className="btn ghost" data-size="sm">` instead of mockup-ui `<Button>` primitive. Rendered DOM is byte-identical (Button just wraps the same shell). Defer to a cosmetic-code-style cleanup sprint; not a visual drift.
- **`AD-Topbar-Tweaks-Panel-Phase58+`** (YELLOW, Sprint 57.30 D5 finding) — mockup `shell.jsx:218` has a `<Button icon="sliders" onToggleTweaks>` Tweaks button; production omits it (no Tweaks panel implementation). Defer to Phase 58+ when Tweaks panel ships.
- **`AD-Tsconfig-Node-NoEmit`** (NEW Sprint 57.30 Day 1 finding) — `tsc --strict` reports pre-existing `TS6310: referenced project tsconfig.node.json may not disable emit` since Day 0 baseline `5c0ce0dd`. Not introduced by Sprint 57.30. Defer to a tooling cleanup sprint or separate PR.
- **`AD-ApprovalCard-Legacy-Phase58-Migrate`** (YELLOW, Day 4 finding) — `ApprovalCard` confirmed legacy per `chatStore.ts:L324` dual-emit comment; HITLTurn is canonical Phase-1 chat-inline render. ApprovalCard re-pointed for completeness this sprint, but still 0 main render path uses it. Migrate governance integration to HITLTurn-only in Phase 58+, then delete ApprovalCard.
- **`AD-Sprint-Plan-frontend-verbatim-bimodal-watch`** (NEW Sprint 57.30 Day 5 calibration) — `frontend-verbatim-css-repoint` 0.60 baseline 2-data-point: 57.29 ≈1.0 vs 57.30 ≈0.40. Watch 3rd data point; if continues low, propose split between "structural-heavy" (0.65) and "css-swap-only" (0.40). Per `When to adjust` 3-sprint rule, KEEP 0.60 baseline this iteration.

## Q5 — Next steps (carryover candidates, rolling planning discipline)

Per `claudedocs/1-planning/next-phase-candidates.md`, the Phase-2 per-page re-point backlog after Sprint 57.30:

**Active** (12 🟡 AppShellV2 routes remaining):
- `/orchestrator` / `/loop-debug` / `/state-inspector` (debug UIs; visual simple but structural; expected smaller scope)
- `/cost-dashboard` / `/sla-dashboard` (rich dashboards; Sprint 57.24-25 pattern already validated; expected mid-scope)
- `/admin-tenants` / `/tenant-settings` / `/governance` / `/audit-log` / `/redaction` / `/incidents` / `/error-policy` (admin / governance pages)

**Pre-existing crash fix** (3 routes; separate sprint class):
- `/subagents` / `/memory` / `/verification` — pre-existing content crashes; `AD-Overview-PreExisting-Route-Crashes` carryover from 57.29. Sprint 57.31 candidate: a "frontend-page-bug-fix" class sprint at 0.45 mid-band (smaller than re-point sprints, focused on broken-state recovery).

**Infra / debt**:
- `AD-CI-7-GHA-PR-Permission` (Sprint 57.29 carryover; baseline-regen workflow auto-PR step still fails; manual ff-merge workaround acceptable for now).
- `AD-Tsconfig-Node-NoEmit` (NEW Sprint 57.30).
- `AD-Inline-Style-Rule-vs-Verbatim-Method` (Sprint 57.29 carryover; lint rule policy iteration).
- `AD-MockupFidelity-Guard-TokenRelative-Oklch` (Sprint 57.29 carryover; CI guard tuning).

User to direct next sprint per rolling planning discipline (no preemptive plan-writing).

## Q6 — Solo-dev policy validation

- **enforce_admins=true**: still active ✅
- **review_count=0**: still in effect ✅ (Solo-dev policy permanently in place since Sprint 53.2)
- **5 required CI checks**: backend-ci / V2 Lint / Frontend E2E / Backend Smoke / Backend Lint — all expected green on PR
- **No `--admin` bypass used**: ✅
- **No `--no-verify` / `--force` used**: ✅
- **Plan + Checklist → Code → Update → Progress → Retro flow followed**: ✅ (5-step V2 sprint workflow honoured)
- **5 commits per day pattern**: ✅ (Day 0 / 1 / 2 / 3 / 4 + Day 5 closeout = 6 commits on feature branch)
- **Karpathy §1 stop-on-ambiguity**: ✅ (AskUserQuestion used twice on Day 0 for UserMenu architecture + Day 0 go-ahead; afterwards executed within aligned scope per `feedback_tool_result_is_not_turn_boundary.md`)
- **Karpathy §2 simplicity-first**: ✅ (`useDismiss` inlined in UserMenu.tsx; not extracted until 2nd consumer arrives)
- **Karpathy §3 orphan-cleanup-of-own-changes**: ✅ (Day 5 dropped `dropdown-menu.tsx` + `ui/index.ts` re-export — orphans this sprint's UserMenu Radix-drop created — plus `npm uninstall` the now-unused Radix dep for bundle size win)

---

**Sprint 57.30 STATUS: COMPLETE PENDING MERGE**. PARITY achieved on `/chat-v2`; shell hotfix landed; 22-route sweep 0 regression; Radix orphan cleaned; bundle -116 KB. Ready for PR + CI green → squash-merge to main.
