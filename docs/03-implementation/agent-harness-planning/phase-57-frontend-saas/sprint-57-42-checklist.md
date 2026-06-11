# Sprint 57.42 — Checklist

[Plan](sprint-57-42-plan.md)

**Single-domain `frontend-mockup-strict-rebuild`** (mirror 57.41 5-phase Day-numbering): Day 0 / Day 1 / Day 2 / Day 2.5 / Day 3

---

## Day 0 — Plan + Checklist + 3-prong + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.41 template mirror)
- [x] **Read Sprint 57.41 plan + checklist § structure outline** (per sprint-workflow §Step 1 format-consistency rule)
- [x] **Draft `sprint-57-42-plan.md`** mirroring 57.41 §0-9 (9 sections) with single-domain scope
- [x] **Draft `sprint-57-42-checklist.md`** mirroring 57.41 Day 0/1/2/2.5/3 structure adapted for memory matrix rebuild

### 0.2 Step 2.5 Prong 1 — Path verify (single domain scope)
- [x] **Production page mount path verify** — `frontend/src/pages/memory/index.tsx` exists (73 lines; outer 2-tab `recent` + `by-scope` with nested Routes; per §1.4 Option B will be DROPPED)
- [x] **Production component tree path verify** — `frontend/src/features/memory/components/{MemoryRecentList,MemoryByScopeBrowser,MemoryScopeBadge}.tsx` all exist (3 vintage components from Sprint 57.12)
- [x] **Production hooks path verify** — `frontend/src/features/memory/hooks/{useMemoryByScope,useMemoryByTime,useMemoryRecent}.ts` all exist (3 hooks)
- [x] **Production service path verify** — `frontend/src/features/memory/services/memoryService.ts` exists; `frontend/src/features/memory/types.ts` exists
- [x] **Mockup source path verify** — `reference/design-mockups/page-governance.jsx` exists; `const SCOPES = [` @ L410-416 + `const TIME_SCALES =` @ L417 + `const MEMORY_ENTRIES = {` @ L419-435 + `const TIME_TRAVEL_MARKS =` @ L438-445 + `const MEMORY_OPS_TIMELINE =` @ L447-460; `const MemoryPage = () =>` @ L462-598 (~137 lines) + `const TimeTravelScrubber = ({...}) =>` @ L600-656 (~57 lines)
- [ ] **mockup-ui primitive presence check** — `grep -nE "^export (function|const) (Stat|Card|Badge|Icon|Field|BackendGapBanner|Button)" frontend/src/components/mockup-ui.tsx` → log which primitives are present (Sprint 57.40 post-promotion + 57.41 should have all; confirm `Field` (Sprint 57.34 promotion) + `Icon` size prop + `clock` / `download` / `plus` / `play` / `pause` / `memory` / `warn` icon name presence)
- [ ] **Vitest spec presence check** — `Glob frontend/tests/unit/memory/*.test*` → identify existing specs (`memoryService.test.ts` likely; potentially none for the 3 vintage components)
- [ ] **e2e spec presence check** — `Glob frontend/tests/e2e/memory/*.spec.ts` → confirm `memory-page.spec.ts` exists; identify what needs adaptation
- [ ] **routes.config.ts path verify** — `Glob frontend/src/routes.config.ts` exists; grep `memory` entries → confirm `/memory` parent + decide if sub-routes (`/memory/recent` + `/memory/by-scope`) need dropping
- [ ] **App.tsx routing path verify** — `grep -n "memory" frontend/src/App.tsx` → confirm `<Route path="memory/*"` or similar parent route mount

### 0.3 Step 2.5 Prong 2 — Content verify
- [ ] **Production memory/index.tsx content shape verify** — re-confirm outer 2-tab structure (NavLink "Recent" + "By Scope" + nested Routes with `index` redirect to `recent` + `*` fallback); this IS being dropped per §1.4 Option B
- [ ] **Production MemoryRecentList.tsx content verify** — confirm layer dropdown filter + paginated table + Prev/Next footer + Sprint 57.33 defensive `?? []` guards; ORPHAN DELETE per Karpathy §3
- [ ] **Production MemoryByScopeBrowser.tsx content verify** — confirm 5-layer cards + drill-in detail; ORPHAN DELETE per Karpathy §3
- [ ] **Production MemoryScopeBadge.tsx content verify** — read lines for usage hints; cross-grep consumers (Prong 2.5 below)
- [ ] **`MemoryEntry` / scope enum types verify** — `grep -B 2 -A 20 "MemoryEntry\|MemoryScope\|MemoryLayer" frontend/src/features/memory/types.ts` → confirm shape fields; document gaps as candidates for `AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint` mapping
- [ ] **Backend `/api/v1/memory/*` response schema verify** — `Glob backend/src/api/v1/memory/router.py` (or `chat.py` if memory endpoints embedded) + grep response model → confirm field shape; document gaps
- [ ] **`useMemoryRecent` query shape verify** — `Read frontend/src/features/memory/hooks/useMemoryRecent.ts` → confirm returns envelope `{items, total, has_more}` (per Sprint 57.33 defensive pattern); decide RecentMemoryOpsCard wire path (real-data via mapping vs fixture-only)
- [ ] **`useMemoryByScope` + `useMemoryByTime` consumer grep** — `grep -rn "useMemoryByScope\|useMemoryByTime" frontend/src` → if 0 outside the 2 parents (MemoryRecentList + MemoryByScopeBrowser), safe to delete; non-zero = deprecate with TODO

### 0.4 Step 2.5 Prong 2.5 — Child component tree depth audit (AP-Phase2-A/B/C anti-patterns) — AD-Plan-5
- [ ] **Enumerate child component tree** — `grep -nE "import.*from.*@/features/memory" frontend/src/pages/memory/index.tsx` (depth-1: MemoryRecentList + MemoryByScopeBrowser); both scheduled for delete
- [ ] **AP-Phase2-C grep on the 3 vintage components** — `grep -E "bg-card|text-foreground|border-border|bg-muted|text-muted-foreground" frontend/src/features/memory/components/*.tsx` → catalog residue (these will be deleted, but grep result informs whether Sprint 57.33 fixed all or any residue remains; informational only)
- [ ] **MemoryScopeBadge consumer breadth grep** — `grep -rn "MemoryScopeBadge" frontend/src --include="*.tsx" --include="*.ts"` → if 0 outside the 2 parent components, safe to orphan delete (AC13); if non-zero = keep + document carryover
- [ ] **STYLE.md §3 inline `style=` escape comment grep on planned NEW components** — N/A pre-creation; Day 1 agent task brief mandates escape comments on inline-style usage per Sprint 57.40 FIX-015 lesson
- [ ] **AP-Phase2-A outer wrapper artifact grep on pages/memory/index.tsx** — `grep -nE "<div style=\\{\\{[^}]*padding" frontend/src/pages/memory/index.tsx` → should be 0 (AppShellV2 handles page padding)
- [ ] **Layout-class fullBleed grep** — `grep -nE "fullBleed" frontend/src/pages/memory/index.tsx` → memory is NOT fullBleed page (matrix fits normal content area within AppShellV2 chrome), confirm

### 0.5 Step 2.5 Prong 3 — Schema verify
- [x] **N/A — no DB schema / migration / ORM changes in Sprint 57.42** (frontend-only sprint; backend `/api/v1/memory/*` endpoints unchanged; backend cursor-aware matrix + ops timeline + erasure endpoints are AP-2 deferred Phase 58+ per carryover ADs)

### 0.6 Catalog drift findings in progress.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-42/progress.md`**
  - Day 0 entry with "Drift findings" header
  - Any Prong 1 / 2 / 2.5 grep results that don't match Plan §3 spec → log as D-DAY0-X
  - Anticipated D-DAY0-1: route-sweep.mjs `/memory/recent` + `/memory/by-scope` entries decision (drop vs preserve redirect-aware capture)
  - Anticipated D-DAY0-2: MemoryScopeBadge consumer breadth grep verdict (orphan delete vs keep)
  - Anticipated D-DAY0-3: `useMemoryByScope` + `useMemoryByTime` consumer grep verdict (delete vs deprecate)
  - Anticipated D-DAY0-4: `useMemoryRecent` shape mismatch verdict (real-data RecentMemoryOpsCard vs fixture-only)
  - Decide go/no-go: ≤20% shift → continue; 20-50% → revise plan §Acceptance + §Workload; >50% → abort & redraft
  - DoD: progress.md exists with Day 0 entry summarizing single-domain scope confirmation

### 0.7 Capture before baseline (route-sweep)
- [ ] **Re-point `frontend/scripts/route-sweep.mjs` OUT_DIR** to `sprint-57-42-memory-matrix-rebuild` (1-line edit + MHist entry; mirror Sprint 57.41 D-DAY0 pattern)
- [ ] **Dev server check on port 3007** — if not running, start `cd frontend && npm run dev -- --port 3007` (do not stop any node.js process per session guidance)
- [ ] **Run sweep before**: `node frontend/scripts/route-sweep.mjs before` → 24 PNGs in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-42/artifacts/memory-matrix-rebuild/screenshots/before/`
- [ ] **Verify**: 24 files in before/ + no new failed routes (8 PUBLIC + 16 AppShellV2 per FIX-018 auto-derive)

### 0.8 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirm 498/498** (`cd frontend && npm test -- --reporter=dot`)
- [ ] **mockup-fidelity guard exit 0** (`node frontend/scripts/check-mockup-fidelity.mjs`) → baseline 46
- [ ] **Lint baseline** — `npm run lint` (non-silent per `.claude/rules/sprint-workflow.md §Before Commit Checklist` — no `--silent` swallow per Sprint 57.40 FIX-020-B lesson)

### 0.9 Day 0 user review checkpoint
- [ ] **Present plan + checklist summary to user** — `Sprint 57.42 Day 0 ready. Plan = ~360 lines. Checklist = ~210 lines. Single-domain frontend-mockup-strict-rebuild 0.60 (8th data point). Scope = 6 NEW components + _fixtures.ts + 3 vintage components orphan delete + outer 2-tab DROP (single MemoryView mount) + backward-compat redirects + route-sweep mock + drift audit report update.`
- [ ] **Wait for user green-light before Day 1 code starts** — per CLAUDE.md §Sprint Execution Workflow Step 1+2

---

## Day 1 — 6 NEW components + 3 vintage orphan delete + 2-tab drop (agent-delegated 10th consecutive)

### 1.1 Agent delegation prep
- [ ] **Read mockup `page-governance.jsx:410-460`** (5 fixture consts SCOPES / TIME_SCALES / MEMORY_ENTRIES / TIME_TRAVEL_MARKS / MEMORY_OPS_TIMELINE)
- [ ] **Read mockup `page-governance.jsx:462-598`** (MemoryPage + page-head + memory-matrix + grid-main 2-col)
- [ ] **Read mockup `page-governance.jsx:600-656`** (TimeTravelScrubber Card with slider + op markers + cursor display)
- [ ] **Read existing mockup-ui primitives** — confirm Card / Badge / Button / Icon / Field / BackendGapBanner exports + icon name set
- [ ] **Read existing `useMemoryRecent` hook + memoryService** — confirm query shape + service signature (Day 1 RecentMemoryOpsCard wire decision reference)
- [ ] **Prepare agent task brief**:
  - Scope = 6 NEW components (per plan §3.2) + `_fixtures.ts` (verbatim port of 5 mockup consts) + drop outer 2-tab in `pages/memory/index.tsx` + orphan delete 2-3 vintage components per Day 0 verdict
  - Preserve `RequireAuth` + `AppShellV2` wrap in `pages/memory/index.tsx`
  - Preserve `useMemoryRecent` hook + `memoryService` IF Day 0 Prong 2 confirms RecentMemoryOpsCard real-data wire path; otherwise fixture-only
  - DROP 2-tab nav + nested Routes per §1.4 Option B
  - Add backward-compat redirects `/memory/recent` → `/memory` + `/memory/by-scope` → `/memory` in App.tsx (or routes.config.ts per Day 0 verdict)
  - Use mockup verbatim CSS classes per Sprint 57.28 foundation; inline `style=` literals per `AD-Inline-Style-Rule-vs-Verbatim-Method` (file-level `eslint-disable no-restricted-syntax` with rationale per Sprint 57.40 FIX-015 lesson)
  - MemoryMatrix cursor-aware visibility filter per plan §3.7 (3 conditional cases: session.day decay / day vanish 2h+ / else show all)
  - 3 AP-2 BackendGapBanner declarations minimum (MemoryMatrix matrix query + RecentMemoryOpsCard ops timeline + GdprErasureCard erasure endpoint)
  - TimeTravelScrubber 200ms setInterval auto-playback with `useEffect` cleanup `clearInterval` on unmount

### 1.2 Primitive lifts (if Day 0 0.2 grep showed missing)
- [ ] **Confirm all primitives present** — Card / Badge / Button / Icon / Field / BackendGapBanner should all be in mockup-ui.tsx post Sprint 57.40 + 57.41 promotions; if Field Select wrap missing, lift from mockup `page-governance.jsx:586-591` Field+select pattern; if Icon size prop or memory/warn names missing, lift from mockup usage

### 1.3 6 NEW component creation + `_fixtures.ts` (agent-delegated 1st invocation — 10th consecutive code-implementer)
- [ ] **Delegate to `code-implementer` agent** (1st invocation):
  - Input: 6 component specs from plan §3.2 + mockup source line ranges (`page-governance.jsx:410-460` fixtures + `:462-598` MemoryPage + `:600-656` TimeTravelScrubber) + plan §3.7 cursor-aware filter logic + plan §3.8 verbatim fixture port instruction
  - Output: 6 NEW files (MemoryPageHeader / TimeTravelScrubber / MemoryMatrix / RecentMemoryOpsCard / GdprErasureCard / MemoryView) + `_fixtures.ts`
  - DoD: TS 0 errors / lint clean / each component renders standalone if isolated / fixtures verbatim-mapped from mockup

### 1.4 Page restructure + 3 vintage orphan delete + redirects
- [ ] **Edit `frontend/src/pages/memory/index.tsx`** — drop 2-tab nav + nested Routes; single `<MemoryView />` mount; preserve `<RequireAuth>` + `<AppShellV2 pageTitle="Memory">`; ~73 → ~30 lines; update MHist
- [ ] **Add backward-compat redirects** — In `App.tsx` (or `routes.config.ts` per Day 0 verdict): `<Route path="memory/recent" element={<Navigate to="/memory" replace />} />` + `<Route path="memory/by-scope" element={<Navigate to="/memory" replace />} />`
- [ ] **Delete `frontend/src/features/memory/components/MemoryRecentList.tsx`** (per Karpathy §3)
- [ ] **Delete `frontend/src/features/memory/components/MemoryByScopeBrowser.tsx`** (per Karpathy §3)
- [ ] **Conditional delete `frontend/src/features/memory/components/MemoryScopeBadge.tsx`** — IF Day 0 Prong 2.5 grep returned 0 consumers outside the 2 deleted parents; ELSE keep + document carryover AD-Memory-ScopeBadge-Consumers
- [ ] **Conditional delete vintage hooks** `useMemoryByScope.ts` + `useMemoryByTime.ts` — IF Day 0 Prong 2 grep returned 0 consumers outside the 2 deleted parents; ELSE deprecate with TODO carryover
- [ ] **Mark 10th consecutive code-implementer delegation** in progress.md Day 1 entry

### 1.5 Vitest spec verify (decide at agent finish)
- [ ] **Run Vitest** — `npm test -- --reporter=dot`
- [ ] **If 498 - N (vintage component tests if any) = baseline** → confirm baseline before NEW specs
- [ ] **If any unrelated fail** → adapt spec (prefer text/role/testid assertions over class-name per Sprint 57.37 D-DAY3-1 class-swap-resilient convention)
- [ ] DoD: Vitest passes (count adjusted for vintage component deletes if applicable)

### 1.6 Day 1 drift catalog + commit
- [ ] **progress.md Day 1 entry** — actual hr vs ~5.0 est (agent-delegated likely ~30-50 min wall-clock per Sprint 57.39+57.40+57.41 pattern); drift findings if any (D-DAY1-X format)
- [ ] **Commit**: `feat(frontend, sprint-57-42): /memory Memory Layers matrix full rebuild — 6 NEW components + _fixtures.ts + 3 vintage orphan delete + outer 2-tab DROP + backward-compat redirects`

---

## Day 2 — Vitest specs + route-sweep mock + mockup-fidelity threshold + drift audit report update

### 2.1 Vitest spec migration
- [ ] **Confirm vintage test deletes** — if `MemoryRecentList.test.tsx` / `MemoryByScopeBrowser.test.tsx` / `MemoryScopeBadge.test.tsx` exist, delete with parent components; confirm gone via Glob
- [ ] **Preserve `memoryService.test.ts`** unchanged (service layer not touched)
- [ ] **Audit `frontend/tests/e2e/memory/memory-page.spec.ts`** — adapt or delete per scope (2-tab-flow tests obsolete; replace with mockup-shape view assertions if time permits — best-effort Day 2)

### 2.2 NEW Vitest specs (+5-8 NEW specs target)
- [ ] **NEW `MemoryPageHeader.test.tsx`** — 1-2 tests: title + sub + route-pill + entries count + 3 buttons render / cond time-travel Badge shows when cursor<0 / "Return to now" label swap
- [ ] **NEW `TimeTravelScrubber.test.tsx`** — 2 tests: slider value mapping (cursor 0 ↔ slider 0; cursor -1440 ↔ slider 100) / play/pause toggle state (Replay 24h ↔ Pause label swap) + `useEffect` setInterval cleanup on unmount
- [ ] **NEW `MemoryMatrix.test.tsx`** — 2-3 tests: 5×3 grid header row + 5 scope rows render / cursor=0 shows all entries / cursor=-5 day.session shows 1 entry, cursor=-130 day.* all shows 0 / "+N more" overflow with >4 entries
- [ ] **NEW `RecentMemoryOpsCard.test.tsx`** — 1 test: 6-col table headers render + Op Badge memory-tone for WRITE/READ/EXPIRE rows + AP-2 BackendGapBanner declared
- [ ] **NEW `GdprErasureCard.test.tsx`** — 1 test: Subject id input + Reason select with 3 options + Issue tombstone danger button + AP-2 BackendGapBanner declared
- [ ] DoD: Vitest baseline (after vintage deletes) + 5-8 NEW = ~498-505/505 (exact count depends on vintage test count deleted; document in progress.md Day 2)

### 2.3 D-DAY0-1 candidate: route-sweep mock fix
- [ ] **Edit `frontend/scripts/route-sweep.mjs`** — per Day 0 verdict: drop `/memory/recent` + `/memory/by-scope` route entries (since redirected) OR keep as redirect-capture entries; add `/api/v1/memory/{ops/recent,matrix}` envelope-shape mocks (3rd application of `AD-RouteSweep-Envelope-Mock-Convention` post Sprint 57.40 + 57.41)
- [ ] **MHist entry** added with reference to Sprint 57.40 + 57.41 governance/verification precedents (3rd application)
- [ ] **Smoke test**: `node scripts/route-sweep.mjs before --list-only` → 22-24 routes intact (depending on /memory/recent + /memory/by-scope retention decision); derive logic unchanged

### 2.4 mockup-fidelity threshold update
- [ ] **Run guard** — live count vs baseline 46
- [ ] **Update `HEX_OKLCH_BASELINE`** 46 → expected 46-50 (per plan §3.6 +0-4 budget: matrix dot palette / op markers / cursor warning / hover bg — all var-based so most go through); within ≤50 envelope; if >54 unexpected, document as drift D-DAY2-X for color consolidation
- [ ] **MHist entry** added with mockup-token-vocabulary precedent reference

### 2.5 Drift audit report update
- [ ] **Edit `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`** — `/memory` verdict 🔴 CATASTROPHIC → ✅ PARITY (post-rebuild)
- [ ] **Update verdict summary table** — 18 PARITY → 19 (+1 NEAR-PARITY); 3 CATASTROPHIC → 2 (admin-tenants / tenant-settings remain)
- [ ] **Update Recommendations section** — strike Sprint 57.42-closed #2 (memory matrix rebuild via Sprint 57.42); promote remaining to 1–2; add note `AD-RouteSweep-Envelope-Mock-Convention` reaches 3rd application

### 2.6 Day 2 drift catalog + commit
- [ ] **progress.md Day 2 entry** — full Day 2 narrative with calibration data + commit SHA back-fill
- [ ] **Commit**: `chore(frontend, sprint-57-42): Day 2 — +5-8 NEW Vitest specs + route-sweep envelope mock 3rd application + mockup-fidelity baseline 46->48-50 + drift audit report memory PARITY update`

---

## Day 2.5 — Capture after baseline + 22-route sweep diff review + fidelity verdict

### 2.5.1 Capture after baseline (route-sweep)
- [ ] **Run sweep after**: `node frontend/scripts/route-sweep.mjs after` → 22-24 PNGs in `screenshots/after/` (count depends on Day 0 verdict on /memory/recent + /memory/by-scope retention)
- [ ] **Verify**: 22-24 files in after/ + 0 failed routes (8 PUBLIC + 14-16 AppShellV2)

### 2.5.2 Before/after diff review
- [ ] **Compare each route**: before/X.png vs after/X.png via python sha256
- [ ] **Classify**: IDENTICAL / CHANGED / FAIL
- [ ] **Expected CHANGED set**: `/memory` (rebuild) + possibly `/memory/recent` + `/memory/by-scope` (if kept as redirect captures, both show same rebuild)
- [ ] **Confirm 0 UNINTENDED regressions** in other 21 routes (sub-300 byte noise acceptable per Sprint 57.40 envelope)
- [ ] **Manual click test redirects**: `/memory/recent` → `/memory` (redirect 200ms ok) + `/memory/by-scope` → `/memory` (same)

### 2.5.3 Fidelity verdict (/memory only)
- [ ] **`/memory` verdict**: aim ✅ **PARITY** — structural check (page-head with 3 actions / TimeTravelScrubber 24h interactive / 5×3 memory-matrix grid with 5 SCOPE rows + 3 TIME_SCALES cols / 2-col grid-main with RecentMemoryOpsCard + GdprErasureCard / 3 AP-2 banners)
- [ ] DoD: verdict recorded in progress.md Day 2.5 §2.5.3; retrospective.md §Q1 will fold-in Day 3 closeout

### 2.5.4 Side-by-side mockup compare (re-use mockup-sweep.mjs)
- [ ] **Mockup re-shoot** — `node frontend/scripts/mockup-sweep.mjs` regenerate `claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/memory.png` (or reuse existing if static)
- [ ] **Visual compare**: production `after/memory.png` vs mockup → verdict
- [ ] **Evidence saved**: 3-way pair (BEFORE day0 / AFTER day1 / MOCKUP reference) in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-42/artifacts/memory-matrix-rebuild/before-after/`

### 2.5.5 Day 2.5 drift + commit
- [ ] **progress.md Day 2.5 entry** — full sweep summary + verdict + evidence stage + redirect verification
- [ ] **Commit**: `chore(sprint-57-42): Day 2.5 — after-baseline N PNGs + N IDENTICAL/M CHANGED diff + /memory PARITY verdict + 3-way evidence pair + redirect spot-check`

---

## Day 3 — Closeout (retro + matrix update + memory + push + PR)

### 3.1 Retrospective
- [ ] **Create retrospective.md** with Q1-Q7 sections — mirroring Sprint 57.41 format (commits / Q1-Q5 narrative depth + Q6 verbatim-CSS / Q7 N/A SKIP)
- [ ] **Q2 single-domain calibration ratio** — actual / committed ≈ TBD; classify vs [0.85, 1.20] band
- [ ] **Q2 8th data point narrative** — 8-pt window 0.59/1.19/0.88/0.95/1.18/0.36/0.18/TBD; compute mean; `When to adjust` per 3-sprint window rule (if Sprint 57.42 also < 0.7 → 3rd consecutive below-band → lower-trigger MET → propose Sprint 57.43 lift)
- [ ] **Q4 audit debt** — Time-travel Badge cond / 3 AP-2 fixture banners (matrix / ops / erasure) / New entry modal stub / Old URL redirects retention / vintage hooks deprecation; documented as carryover ADs
- [ ] **Q5 carryover candidates** — AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint / AD-Memory-Ops-Timeline-Backend-Endpoint / AD-Memory-GDPR-Erasure-Backend-Endpoint / AD-Memory-Vintage-Hooks-Cleanup / AD-Memory-Old-URL-Redirect-Phase58-Retire / AD-Memory-New-Entry-Modal-Phase58 / AD-Sprint-Plan-Agent-Delegation-Factor-Modifier (5th cross-class data point — activation criteria fully met) / AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift-trigger (conditional — if ratio < 0.7)
- [ ] **Q6 verbatim-CSS protocol compliance** — Layer 2 diff 0 / Layer 4 collision 0 / HEX_OKLCH_BASELINE bump within ≤50 envelope / guard PASS

### 3.2 Calibration matrix update (`sprint-workflow.md §Scope-class multiplier matrix`)
- [ ] **`frontend-mockup-strict-rebuild` row update** — append Sprint 57.42 as 8th data point (ratio TBD + 8-pt mean); status decision per `When to adjust` rule
- [ ] **MHist entry** — Sprint 57.42 Day 3 entry added with 8th data point notation; if ratio < 0.7, document as 5th cross-class data point for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` activation evaluation + 3rd consecutive class below-band trigger
- [ ] **Agent-delegation factor modifier proposal status check** — 5-data-point cross-class evidence threshold confirmed exceeded; document in Q4 + Q5 + propose Sprint 57.43 retro structural decision (Option A coefficient 0.55 OR Option B per-class split)

### 3.3 Memory subfile + MEMORY.md pointer
- [ ] **Create `memory/project_phase57_42_memory_matrix_rebuild.md`** with sprint detail (goal/shipped/calibration/Phase-2 progress/carryover ADs/anomalies/commits/related)
- [ ] **Add MEMORY.md entry** — quality pointer with topic + keywords + subfile link per §Sprint Closeout Update Policy (~250-300 char ceiling)

### 3.4 next-phase-candidates.md
- [ ] **Add Sprint 57.42 carryover section** at top with shipped summary + calibration + Phase-2 epic progress
- [ ] **Update Phase-2 epic progress** — 3 → 2 🔴 CATASTROPHIC remaining (admin-tenants / tenant-settings) + 1 NEAR-PARITY (chat-v2 rename) + 19 PARITY
- [ ] **Add 4-6 NEW carryover ADs** (#60+ continuation) ordered by ROI per audit Recommendations remaining

### 3.5 CLAUDE.md minimal touch (per §Sprint Closeout Update Policy)
- [ ] **Update `Current Sprint` row** with Sprint 57.42 1-line + redirect to memory subfile + next-phase-candidates.md
- [ ] **Update `Last Updated` footer** — 1-line per §Sprint Closeout Policy navigator format
- [ ] **NO retro detail packed into table cells** (REFACTOR-001 discipline observed)

### 3.6 Commit closeout + push + PR
- [ ] **Final commit**: `chore(sprint-57-42): Day 3 closeout — retro + matrix + memory + CLAUDE.md`
- [ ] **Push**: `git push -u origin feature/sprint-57-42-memory-matrix-rebuild` (per CLAUDE.md "Confirmation on Destructive Only" — push needs explicit user authorization)
- [ ] **Open PR**: `gh pr create --base main --title "feat(frontend, sprint-57-42): /memory Memory Layers matrix full mockup-fidelity rebuild (closes drift audit 2026-05-25 #2 priority CATASTROPHIC)"`
- [ ] **Wait for CI green** → squash-merge ready → user confirmation before merge

---

## Sprint 57.42 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] **CLAUDE.md changes**: Only Current Sprint row + Last Updated footer (no per-sprint history table additions)?
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)?
- [ ] **Sprint detail preserved**: memory subfile + retrospective.md with full content?
- [ ] **Carryover / open items**: documented in `next-phase-candidates.md` (NOT in CLAUDE.md / MEMORY.md prose)?
- [ ] **Calibration ratio**: tracked in `sprint-workflow.md §Scope-class multiplier matrix` (8th data point + 8-pt mean)?
- [ ] **Agent-delegation factor modifier**: 5th cross-class data point status logged in Q4 + Q5 (activation criteria fully met)?
- [ ] **Class baseline lower-trigger**: 3-sprint window 57.40+57.41+57.42 evaluation logged (if 3rd consecutive < 0.7 → lift trigger MET → propose Sprint 57.43)?
- [ ] **Phase-2 epic progress note**: post-sprint 3 → 2 🔴 CATASTROPHIC remaining (next high-ROI candidates = `/admin-tenants` tenants table rebuild ~12-15 hr OR `/tenant-settings` 6-tab rebuild ~15-20 hr OR `/chat-v2` Inspector tab rename ~30 min quick win)
- [ ] **Drift audit report updated**: `/memory` verdict ✅ PARITY in `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`?
