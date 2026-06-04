# Sprint 57.77 Plan — Memory ops-history frontend (useMemoryOps hook + RecentOps/TimeTravel wire + remove fixtures) (closes AD-Memory-OpsHistory-Backend frontend half)

**Branch**: `feature/sprint-57-77-memory-ops-history-frontend` (from `main` `2947010a`)
**Closes**: `AD-Memory-OpsHistory-Backend` (frontend half; backend shipped Sprint 57.76 PR #242)
**Scope**: Frontend-only. Backend `GET /memory/ops` is live (`api/v1/memory.py:527-571`); this sprint wires it into the memory page and removes the 3 ops fixtures + 2 stale gap banners.

---

## 0. Background

Sprint 57.76 shipped the backend half of memory ops-history: `memory_ops` table (append-only, Option B) + user/tenant layer write/evict emit + `GET /memory/ops` (cursor-paginated, `require_audit_role`, tenant-scoped). The memory page's two ops widgets (`RecentMemoryOpsCard`, `TimeTravelScrubber`) still render fixtures with a now-stale gap banner pointing at this very AD. This sprint completes the chain: real `useMemoryOps` hook (mirror `useMemoryMatrix`) → both widgets consume it → fixtures + banners removed → first-ever Vitest/e2e coverage.

**User decision (AskUserQuestion, 2026-06-04)**: **Full wire** — RecentOps consumes real `GET /memory/ops`; TimeTravel marks derive from real `created_at_ms` (fixture removed); scrub cursor **really filters** RecentOps to ops at/before the cursor time. Honest semantics = *browsing the ops timeline*, NOT point-in-time memory-state reconstruction (the latter is deferred — retro 57.76 Q5). This keeps AP-4 clean: the scrubber has a real effect (filtering the visible ops), not a Potemkin slider.

### Day-0 ground-truth (2 researcher passes, main `2947010a`)
- **D-DAY0-1 (mockup line drift)**: retro cited `page-governance.jsx:556-579`; actual = `:557-579` (RecentOps card) + `:600-656` (TimeTravel scrubber). Plan §3 uses corrected refs.
- **D-DAY0-2 (op/scope value drift)**: backend `op` ∈ {`WRITE`,`EVICT`} (NOT fixture's `READ`/`EXPIRE`); `scope` ∈ {`user`,`tenant`} only (role/system raise → not recorded; session in-memory → not recorded). Badge + any op-label rendering must use the real value set.
- **D-DAY0-3 (wire shape — authoritative)**: `MemoryOpItem` (`memory.py:153-166`) = `{op, scope, key, time_scale, value_snapshot, actor, created_at_ms}`; `MemoryOpsResponse` (`:169-171`) = `{ops, next_cursor}`. `next_cursor`/`before` = `created_at_ms` (strict-older). FE API type mirrors the wire verbatim (single-source); the fixture-era `RecentMemoryOp {op,scope,k,v,by,at}` (`_fixtures.ts:52-59`) is removed, render maps `key→Key / value_snapshot→Value / actor→By / created_at_ms→When(HH:MM:SS)`.
- **D-DAY0-4 (all net-new infra)**: no `useMemoryOps`, no `fetchOps`, no `MemoryOpItem`/`MemoryOpsResponse` API type. `useMemoryMatrix.ts` (`:31-39`) + `memoryService.fetchMatrix` (`:123-131`) are the exact mirror targets.
- **D-DAY0-5 (greenfield tests)**: zero Vitest for any memory component; `memoryService.test.ts` covers `fetchRecent/fetchByScope/fetchByTime` + error paths but has **no `fetchMatrix` test** (57.73 shipped it untested). No Playwright memory spec exists. New coverage is greenfield (set precedent).
- **D-DAY0-6 (inline-style convention)**: both target components use a single **file-top** `eslint-disable no-restricted-syntax` (not per-line). New inline styles stay covered; no per-line disable churn needed. Prong-2.5 child audit: shadcn-utility residue **0**, hex/oklch literals **0** in both files.
- **D-DAY0-7 (scrub has no real consumer today)**: `MemoryView.tsx:73-90` owns `cursor`+`playing` but `MemoryMatrix` ignores `cursor` → scrub is currently visual-only. Full-wire fixes this: cursor feeds RecentOps filtering.

---

## 1. Sprint Goal

Wire the memory page's Recent Ops + TimeTravel widgets to the live `GET /memory/ops`, with a real client-side scrub-filter, and remove all ops fixtures + stale gap banners — completing `AD-Memory-OpsHistory-Backend` end-to-end.

---

## 2. User Stories

- **US-1** — 作為 auditor，我希望 memory page 的 Recent Ops 表格顯示真實的 memory WRITE/EVICT 操作（key/value/actor/time），以便審計 memory 變更歷史。
- **US-2** — 作為 auditor，我希望 TimeTravel 時間軸上的 marks 反映真實 ops 的時間分布，且 scrub/play 能真實過濾 Recent Ops 到該時間點，以便聚焦特定時間窗。
- **US-3** — 作為前端維護者，我希望 `useMemoryOps` hook + `fetchOps` service mirror 既有 `useMemoryMatrix`/`fetchMatrix` 模式，以便 data-layer 一致可維護。
- **US-4** — 作為維護者，我希望移除 3 個 ops fixtures + 2 個 stale gap banner，以便 memory feature 無 orphan code（AP-2）。
- **US-5** — 作為 QA，我希望有 Vitest（fetchOps + hook + 兩個 component + scrub-filter）+ Playwright e2e 覆蓋，以便回歸保護。

---

## 3. Technical Specifications

### 3.0 Architecture
`useMemoryOps()` (TanStack, dedup'd query key) → `memoryService.fetchOps()` → `GET /api/v1/memory/ops`. `MemoryView` owns `cursor` (ms) + `playing`; both widgets call `useMemoryOps()` (React Query dedups, same as MemoryMatrix+Header share `useMemoryMatrix`). `cursor` flows as a prop into `RecentMemoryOpsCard` to filter `ops` to `created_at_ms ≤ cursor`. Honest semantic: scrub = browse-ops-timeline, not reconstruct-state.

### 3.1 `fetchOps` + `useMemoryOps` (US-3) — `services/memoryService.ts` + `hooks/useMemoryOps.ts`
- `memoryService.fetchOps(limit = 50, before?: number, signal?)`: build `URLSearchParams` (`limit` always; `before` only when provided — do NOT reuse offset-based `_buildPageParams`); `GET ${API_BASE}/ops?...`; `_handleResponse<MemoryOpsResponse>`. Add right after `fetchMatrix` (`:131`).
- `useMemoryOps()` (NEW `hooks/useMemoryOps.ts`): mirror `useMemoryMatrix` verbatim — `MEMORY_OPS_QUERY_KEY = ["memory","ops"]`, `queryFn: ({signal}) => memoryService.fetchOps(50, undefined, signal)`, `staleTime: 30_000`. Consumers read `isLoading`/`isError`.

### 3.2 API types (US-1) — `features/memory/types.ts`
NEW (mirror wire verbatim; place beside `MemoryMatrixResponse` `:93-97`):
```ts
export interface MemoryOpItem {
  op: string;                    // "WRITE" | "EVICT"
  scope: string;                 // "user" | "tenant"
  key: string | null;
  time_scale: string | null;
  value_snapshot: string | null;
  actor: string | null;
  created_at_ms: number;
}
export interface MemoryOpsResponse {
  ops: MemoryOpItem[];
  next_cursor: number | null;
}
```

### 3.3 RecentMemoryOpsCard wire (US-1) — `components/RecentMemoryOpsCard.tsx`
- Add optional prop `{ cursor?: number | null }` (default null = show all).
- Internal `useMemoryOps()`; on data, filter `ops.filter(o => cursor == null || o.created_at_ms <= cursor)`.
- Render existing 6-col mockup table (`Op/Scope/Key/Value/By/When`, classes `table`/`mono`/`subtle`, `<Badge tone="memory">`): `op`→Op badge, `scope`→Scope, `key`→Key (mono, `—` if null), `value_snapshot`→Value (mono, 240px ellipsis, `—` if null), `actor`→By (subtle, `—` if null), `created_at_ms`→When (`HH:MM:SS` via a small `formatMs` helper).
- States (mockup-native, NOT shadcn skeletons): loading → subtle "Loading…" row; error → subtle error row (`error.message`); empty → "No memory operations recorded yet." row.
- **Remove** `RECENT_MEMORY_OPS` import + the AP-2 gap banner (`:100`).

### 3.4 TimeTravelScrubber marks from ops (US-2) — `components/TimeTravelScrubber.tsx`
- Internal `useMemoryOps()`; derive marks from real `ops` `created_at_ms`: domain `[minMs, maxMs]`; each op → mark at normalized position `(created_at_ms - minMs)/(maxMs - minMs)`. Empty ops → no marks (+ subtle "no operations" hint).
- Keep mockup props `{cursor, onCursor, playing, onPlay}` + scrubber/play UI verbatim (`:600-656` mockup classes).
- `cursor` is an ms timestamp in `[minMs, maxMs]`; scrubbing sets `onCursor(ms)`.
- **Remove** `MEMORY_OPS_TIMELINE` + `TIME_TRAVEL_MARKS` imports + the stale gap banner (`:162`).

### 3.5 MemoryView wiring (US-2) — `components/MemoryView.tsx`
- Initialize `cursor` to `null` (= latest/all) rather than a fixture index; `useMemoryOps()` here too (or read range from widgets) to bound the playback `setInterval` to `[minMs, maxMs]` and advance cursor across real op times; pause/reset at end.
- Pass `cursor` to `RecentMemoryOpsCard`; pass `{cursor, onCursor, playing, onPlay}` to `TimeTravelScrubber` (unchanged shape).
- No layout/mount-order change (`MemoryPageHeader → TimeTravelScrubber → MemoryMatrix → grid-main[RecentMemoryOpsCard + GdprErasureCard]`).

### 3.6 Remove fixtures + banners (US-4) — `features/memory/_fixtures.ts`
- Remove `RECENT_MEMORY_OPS` (`:85`), `MEMORY_OPS_TIMELINE` (`:70`), `TIME_TRAVEL_MARKS` (`:61`) + their now-orphan types (`RecentMemoryOp`/`TimeTravelMark`/`MemoryOpTimelinePoint`) once no consumer remains. Grep-confirm 0 remaining imports before deleting.

### 3.7 Tests (US-5)
- `services/memoryService.test.ts` (extend): `fetchOps` builds `?limit=50` and `?limit=&before=` correctly; parses `MemoryOpsResponse`; surfaces error detail (sets the missing-fetchMatrix-test precedent forward for ops).
- NEW `hooks/useMemoryOps.test.tsx`: query key + queryFn forwards signal (mirror any useMemoryMatrix test if present, else greenfield).
- NEW `components/RecentMemoryOpsCard.test.tsx`: real rows render; null fields → `—`; cursor filter drops newer ops; loading/error/empty states.
- NEW `components/TimeTravelScrubber.test.tsx`: marks derived from ops; empty ops → no marks; onCursor fires on scrub.
- NEW Playwright e2e `tests/e2e/memory/memory-ops.spec.ts`: mock `GET /api/v1/memory/ops`; assert RecentOps rows + scrub filters; assert `require_audit_role` 403 path renders error (mock 403).

### 3.8 Lint / mockup-fidelity validation
- `npm run lint` (NO `--silent` — Before-Commit item 7), `npm run build` (tsc 0), `npm run test` (Vitest), `npm run check:mockup-fidelity` (CSS byte-identical + `HEX_OKLCH_BASELINE` unchanged — pure data-wiring adds 0 color literals), `npx playwright test memory-ops`.

---

## 4. File Change List

> **As-shipped** (reconciled at closeout; see §8 D-DAY1-2 test-location drift): tests live under `frontend/tests/unit/memory/` + `frontend/tests/e2e/memory/` (Vitest `include` = `tests/unit/**`), NOT colocated `src/`; the 4 memory component tests already existed (57.73) and were rewritten in place. MemoryPageHeader migration added per §8 D-DAY1-1 (user-approved).

**NEW (3)**
- `frontend/src/features/memory/hooks/useMemoryOps.ts`
- `frontend/tests/unit/memory/useMemoryOps.test.tsx`
- `frontend/tests/e2e/memory/memory-ops.spec.ts`

**EDIT (10)**
- `frontend/src/features/memory/services/memoryService.ts` (+fetchOps)
- `frontend/src/features/memory/types.ts` (+MemoryOpItem/MemoryOpsResponse)
- `frontend/src/features/memory/components/RecentMemoryOpsCard.tsx` (wire + cursor filter, remove banner)
- `frontend/src/features/memory/components/TimeTravelScrubber.tsx` (marks from ops, remove banner)
- `frontend/src/features/memory/components/MemoryView.tsx` (cursor ms init + playback + headerCursor)
- `frontend/src/features/memory/components/MemoryPageHeader.tsx` (cursor minute-offset → ms|null migration; §8 D-DAY1-1)
- `frontend/tests/unit/memory/memoryService.test.ts` (+fetchOps cases)
- `frontend/tests/unit/memory/{RecentMemoryOpsCard,TimeTravelScrubber,MemoryView,MemoryPageHeader}.test.tsx` (rewrite for real-data + header migration)

**DELETE (1)**
- `frontend/src/features/memory/_fixtures.ts` (3 ops fixtures + 3 orphan types + MemoryScopeId; grep-confirmed 0 importers)

**NO backend / wire-schema / migration change.**

---

## 5. Acceptance Criteria

- RecentMemoryOpsCard renders real rows from `GET /memory/ops` (WRITE/EVICT, user/tenant); null fields → `—`; no fixture import.
- TimeTravel marks reflect real op times; scrub `cursor` filters RecentOps to `created_at_ms ≤ cursor`; play animates across the real time range.
- Both stale gap banners removed; `_fixtures.ts` has 0 ops fixtures + 0 orphan types; grep confirms no remaining fixture imports.
- `useMemoryOps`/`fetchOps` mirror the matrix pattern (queryKey shape, staleTime, signal forwarding).
- Vitest: fetchOps + hook + both components (incl. scrub-filter + states) green; e2e memory-ops green.
- Gates: lint (no `--silent`) 0, build tsc 0, Vitest all green, `check:mockup-fidelity` byte-identical + baseline unchanged, Playwright memory-ops green.

---

## 6. Deliverables

- [ ] `fetchOps` + `useMemoryOps` (mirror matrix)
- [ ] `MemoryOpItem`/`MemoryOpsResponse` API types
- [ ] RecentMemoryOpsCard wired + cursor filter + states + banner removed
- [ ] TimeTravelScrubber marks from real ops + banner removed
- [ ] MemoryView cursor init + playback over real op times
- [ ] 3 ops fixtures + orphan types removed (grep-confirmed)
- [ ] Vitest (fetchOps + hook + 2 components) + Playwright e2e
- [ ] All gates green; closeout docs (CHANGE-045 + progress + retro + MEMORY + CLAUDE lean)

---

## 7. Workload Calibration

Scope class `medium-frontend` (0.65) + `agent_factor` `mechanical-greenfield-design-decisions` (0.65 — NEW hook mirror + NEW API types + NEW scrub→filter UX state design). **Agent-delegated: yes** (single Track A frontend code-implementer + parent Day-0 research + full re-verify).

Bottom-up est ~12 hr → class-calibrated commit ~7.8 hr (mult 0.65) → agent-adjusted commit ~5 hr (agent_factor 0.65).

---

## 8. Dependencies & Risks

- **Risk: scrub-filter Potemkin** — mitigated by user-locked design: cursor really filters RecentOps (real effect), honest "browse ops" semantics; no fake state reconstruction. Verify in Vitest (cursor drops newer ops).
- **Risk: empty ops domain** — fresh tenant has 0 ops → marks domain `[minMs,maxMs]` div-by-zero. Mitigate: empty → no marks + subtle hint; cursor disabled/no-op.
- **Risk: `created_at_ms` formatting / timezone** — render `HH:MM:SS` from ms; client-local is acceptable for an activity timeline (matches mockup's relative "When"). Document in component.
- **Risk Class C (test isolation)** — Vitest component tests mock the hook/fetch (no real PG); e2e mocks the route. No module-singleton concern.
- **Dependency**: backend `GET /memory/ops` live (57.76); `require_audit_role` means non-auditor → 403 (e2e covers the error render).

**Closeout drift findings (parent review, Before-Commit item 7)**:
- **D-DAY1-1 (MemoryPageHeader cursor — incomplete-wire, user-approved scope expansion)**: agent passed hardcoded `cursor={0}` to the out-of-scope 57.73 header → its time-travel Badge/button inert + a dead `cursor < 0` branch. Per user AskUserQuestion (2nd), migrated header cursor minute-offset → ms|null (`isTimeTravel = cursor != null`; Badge HH:MM:SS; dead branch removed); MemoryView computes `headerCursor` (active only when scrubbed strictly before latest). Added to §4 EDIT.
- **D-DAY1-2 (test-location)**: plan §3.7/§4 assumed colocated `src/**/*.test.tsx` NEW; Vitest `include` is `tests/unit/**` only + 4 memory component tests already existed (57.73). Rewritten in place (no coverage lost). §4 reconciled.

---

## 9. Out of Scope (this sprint; carryover)

- **READ-path ops** — only WRITE/EVICT emitted (57.76); sampled reads = future.
- **role/session/system ops** — those layers raise / in-memory (57.76); not recorded.
- **Point-in-time state reconstruction** — scrub is ops-browsing, not snapshot replay (retro 57.76 Q5 deeper capability).
- **Server-side ops filtering by time window** — this sprint filters client-side from a single page; server `before` cursor used only for pagination, not the scrub.
- **FE `/subagents` real list** (`AD-Subagent-RealList-Phase58`) — the last Area-A remaining item.
