# Sprint 57.77 Progress — Memory ops-history frontend

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-77-plan.md`
**Checklist**: `...sprint-57-77-checklist.md`
**Branch**: `feature/sprint-57-77-memory-ops-history-frontend` (from `main` `2947010a`)
**Closes**: `AD-Memory-OpsHistory-Backend` (frontend half; backend = Sprint 57.76)

---

## Day 0 — 2026-06-04 — Plan-vs-Repo Verify + Decisions

### Decisions (user-locked, AskUserQuestion ×1)
- **TimeTravel handling**: **Full wire** — RecentOps consumes real `GET /memory/ops`; TimeTravel marks derive from real `created_at_ms` (fixture removed); scrub cursor **really filters** RecentOps to `created_at_ms ≤ cursor`. Honest semantic = browse ops timeline, NOT point-in-time state reconstruction (deferred, retro 57.76 Q5). Keeps AP-4 clean (scrub has real effect, not Potemkin slider).
- **Split**: frontend-only (backend shipped 57.76). Agent-delegated: yes (Track A frontend code-implementer + parent re-verify).
- **FE type**: mirror backend wire verbatim (`MemoryOpItem` {op,scope,key,time_scale,value_snapshot,actor,created_at_ms}); remove fixture-era `RecentMemoryOp {op,scope,k,v,by,at}`; render maps key→Key/value_snapshot→Value/actor→By/created_at_ms→When.

### Day-0 verify (2 researcher passes + parent, main `2947010a`)
- **D-DAY0-1 (mockup line drift)**: retro `:556-579` → actual `:557-579` (RecentOps) + `:600-656` (scrubber). Plan §3 uses corrected refs.
- **D-DAY0-2 (op/scope value drift)**: `op` ∈ {WRITE,EVICT} (not READ/EXPIRE); `scope` ∈ {user,tenant} only (role/system raise, session in-memory → not recorded). Render uses real value set.
- **D-DAY0-3 (wire shape, authoritative)**: `MemoryOpItem` (`memory.py:153-166`) {op,scope,key,time_scale,value_snapshot,actor,created_at_ms}; `MemoryOpsResponse` (:169-171) {ops,next_cursor}; `before`/`next_cursor` = created_at_ms strict-older. FE type mirrors wire; fixture type removed.
- **D-DAY0-4 (net-new infra)**: no useMemoryOps/fetchOps/API-type. Mirror targets: `useMemoryMatrix.ts:31-39` + `fetchMatrix` (`memoryService.ts:123-131`).
- **D-DAY0-5 (greenfield tests)**: 0 component Vitest; `memoryService.test.ts` has no fetchMatrix test; no Playwright memory spec. New coverage greenfield.
- **D-DAY0-6 (inline-style)**: both targets use file-top `eslint-disable no-restricted-syntax`; new inline styles covered. Prong-2.5: shadcn residue 0, hex/oklch 0.
- **D-DAY0-7 (scrub no real consumer today)**: `MemoryView.tsx:73-90` owns cursor but MemoryMatrix ignores it → scrub visual-only. Full-wire fixes (cursor → RecentOps filter).

### Prong 1 (path) — GREEN
All confirmed: `hooks/useMemoryMatrix.ts`, `services/memoryService.ts` (fetchMatrix :123-131), `types.ts` (MemoryMatrixResponse :93-97), `components/{RecentMemoryOpsCard,TimeTravelScrubber,MemoryView}.tsx`, `_fixtures.ts` (3 ops fixtures), `api/v1/memory.py` (/ops :527-571, MemoryOpItem :153-166).

### Prong 2 (content) — researcher-confirmed
- RecentMemoryOpsCard fixture-based no-props + stale banner (:100); TimeTravelScrubber fixture marks + stale banner (:162); MemoryView owns cursor+playing+playback setInterval; useMemoryMatrix minimal TanStack; fetchMatrix simple GET; no offset for ops (`before` cursor).

### go/no-go = **GO** (Day 1 data layer). All touch-points are net-new wiring; components already mockup-ported; no >20% scope drift.

---

## Day 1-3 — Frontend wire (Track A, agent-delegated code-implementer) + parent header migration

Single frontend track (backend live since 57.76). Agent wall-clock ~8.5 min; parent Day-0 2-researcher research + header migration + full re-verify.

### Implemented (agent — Track A)
- **API types** (`types.ts` +31): `MemoryOpItem` + `MemoryOpsResponse` mirror wire verbatim (op/scope/key/time_scale/value_snapshot/actor/created_at_ms; ops[]+next_cursor).
- **fetchOps** (`memoryService.ts` +22): own `URLSearchParams` (`limit` always; `before` only when provided — NOT offset-based `_buildPageParams`); `GET /ops`; `_handleResponse<MemoryOpsResponse>`.
- **useMemoryOps** (`hooks/useMemoryOps.ts` NEW): mirrors `useMemoryMatrix` verbatim (`MEMORY_OPS_QUERY_KEY=["memory","ops"]`, queryFn `fetchOps(50, undefined, signal)`, staleTime 30_000).
- **RecentMemoryOpsCard** (+wire): `useMemoryOps()` + `cursor?` prop filters `created_at_ms ≤ cursor`; 6-col render (op→Badge / scope / key→`—` / value_snapshot→ellipsis 240 / actor→`—` / created_at_ms→`formatMs` HH:MM:SS); loading/error/empty mockup-native rows; drop `RECENT_MEMORY_OPS` + AP-2 banner.
- **TimeTravelScrubber** (+wire): marks from real `created_at_ms` domain `[minMs,maxMs]`; `hasDomain` guard (ops≥2 && maxMs>minMs) → empty hint + disabled slider; scrub maps position→ms→`onCursor(ms)`; WRITE→`var(--memory)` / EVICT→`var(--warning)` marks; drop fixtures + banner.
- **MemoryView** (+wire): `cursor: number|null` (ms); playback `setInterval` advances cursor over `[minMs,maxMs]` (pause+reset null at end; 0/1 op → no-op); pass cursor → RecentOps.
- **_fixtures.ts DELETED**: all 3 ops fixtures + 3 orphan types + `MemoryScopeId` had 0 external importers → empty module removed (not left orphan; Karpathy §3).
- **Tests**: NEW `useMemoryOps.test.tsx` + `memory-ops.spec.ts` (e2e); rewrote 4 existing `tests/unit/memory/*` (memoryService/RecentOps/TimeTravel/MemoryView) for real-data behavior + extended memoryService with fetchOps cases.

### Drift findings (parent review, Before-Commit item 7)
- **D-DAY1-1 (MemoryPageHeader cursor minute-offset — incomplete-wire)**: agent passed hardcoded `<MemoryPageHeader cursor={0}>` to avoid touching the out-of-scope 57.73 header, leaving its time-travel Badge/button permanently inert + a dead `cursor < 0` branch; scrub did not reflect in the header. **User-approved scope expansion (AskUserQuestion ×2nd)** → parent migrated `MemoryPageHeader` cursor `minute-offset → ms|null` (`isTimeTravel = cursor != null`; Badge shows `formatMs(cursor)` HH:MM:SS; eliminated dead branch) + `MemoryView` computes `headerCursor` (active only when scrubbed strictly before latest) + updated `MemoryPageHeader.test` (cursor=null/past-ms semantics, timezone-safe Badge prefix assert) + `MemoryView.test` comment.
- **D-DAY1-2 (test location)**: plan §3.7/§4 assumed colocated `src/**/*.test.tsx` NEW; reality = Vitest `include` is `tests/unit/**` only, and 4 memory component tests already existed (57.73). Agent rewrote them in place (edit, not delete) + placed new ones under `tests/unit/memory/` + `tests/e2e/memory/`. No coverage lost.
- **D-DAY1-3 (scope doc)**: backend `MemoryOpItem.scope` docstring says user/tenant/role; only user/tenant actually emit (57.76). FE types `scope: string` — non-issue.

### Parent re-verify (Before-Commit item 7) — all gates green (parent-run)
- `npm run build` tsc 0; `npm run lint` exit 0 (3 pre-existing jsx-ast-utils TSSatisfies info, not errors); `npm run test` **750 passed / 132 files** (the "kaboom" line is AuthShell error-boundary's intentional throw, not a failure); `npm run check:mockup-fidelity` **byte-identical + baseline 50 unchanged** (pure data-wiring, 0 color literals); `npx playwright test memory-ops` **3 passed** (happy / scrub-filter / 403-error; ECONNREFUSED = telemetry proxy to absent backend, harmless).
- Read ALL agent-changed code + own header migration: cursor filter real (not Potemkin — e2e `slider.fill("0")` proves newer op hidden); `hasDomain` guards div-by-zero; banners + fixtures removed; mockup classes verbatim (CSS var, no hex/oklch/shadcn); English state copy; tests non-vacuous (TimeTravel asserts `onCursor((MIN+MAX)/2)` midpoint; memoryService asserts `before` only-when-provided).

---

## Day 4 — Closeout

- CHANGE-045; retrospective.md Q1-Q7; checklist all `[x]` (push+PR left unchecked, user-gated); MEMORY subfile + pointer; CLAUDE.md lean; next-phase-candidates.md (AD-Memory-OpsHistory-Backend **fully closed** — backend 57.76 + frontend 57.77).
- **No design note** (feature-continuation: data-wiring of the shipped GET /memory/ops into mockup-ported components; no new contract / no 17.md change).
- Calibration: `medium-frontend` 0.65 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 — CAVEATED (15th consecutive agent-delegated no-clean-wall-clock; the parent header-migration + 2-researcher Day-0 + full re-verify dominate wall-clock).
- AD status: `AD-Memory-OpsHistory-Backend` **fully closed**. Remaining Area-A: FE `/subagents` real list (`AD-Subagent-RealList-Phase58`) — the last item.

---
