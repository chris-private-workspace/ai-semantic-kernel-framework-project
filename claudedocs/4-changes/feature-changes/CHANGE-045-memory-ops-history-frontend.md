# CHANGE-045: Memory ops-history frontend wiring

**Date**: 2026-06-04
**Sprint**: 57.77
**Scope**: Frontend / Category 3 (Memory) — data-wiring of the shipped `GET /memory/ops`
**Closes**: `AD-Memory-OpsHistory-Backend` (frontend half → AD **fully closed**: backend 57.76 + frontend 57.77)

## Problem
Sprint 57.76 shipped the backend `memory_ops` table + `GET /memory/ops`, but the memory page's two ops widgets (`RecentMemoryOpsCard`, `TimeTravelScrubber`) still rendered fixtures with a now-stale gap banner pointing at the just-shipped AD. The time-travel scrub also had no real consumer (MemoryMatrix ignores cursor) — a visual-only slider.

## Root Cause
Backend-then-FE split (57.76 backend / 57.77 frontend), mirroring the 57.70→57.71 precedent. The FE wiring infra (hook + service `fetchOps` + API types) was entirely net-new.

## Solution
- NEW `useMemoryOps` hook (mirrors `useMemoryMatrix`: queryKey `["memory","ops"]`, staleTime 30s) + `memoryService.fetchOps(limit, before?, signal?)` (own `URLSearchParams`; `before` only when provided) + `MemoryOpItem`/`MemoryOpsResponse` types (wire-verbatim).
- `RecentMemoryOpsCard` consumes the hook + optional `cursor` prop filtering `created_at_ms ≤ cursor` (honest browse-ops-timeline, **not** state reconstruction — user-locked via AskUserQuestion); loading/error/empty mockup-native rows; dropped fixture + stale AP-2 banner.
- `TimeTravelScrubber` marks derive from the real `created_at_ms` domain `[minMs,maxMs]` (`hasDomain` guards div-by-zero; empty → hint + disabled slider); scrub maps position→ms→`onCursor(ms)`; dropped fixtures + banner.
- `MemoryView` cursor = `number|null` (ms); playback `setInterval` advances over the real op range; passes `cursor` to RecentOps + a computed `headerCursor` to the header.
- `MemoryPageHeader` cursor migrated minute-offset → `ms|null` (parent review **D-DAY1-1**, user-approved): time-travel Badge shows `HH:MM:SS`; dead `cursor < 0` branch eliminated.
- Deleted `_fixtures.ts` (3 ops fixtures + 3 orphan types + `MemoryScopeId`; grep-confirmed 0 importers).

Commits: `90017c2d` (Day-0), `6ec7024e` (Track A frontend + header migration).

## Verification (parent-run, Before-Commit item 7)
- `npm run build` tsc 0; `npm run lint` exit 0 (3 pre-existing jsx-ast-utils info); `npm run test` **750 passed / 132 files**; `npm run check:mockup-fidelity` byte-identical + baseline 50 unchanged; `npx playwright test memory-ops` **3 passed** (happy / scrub-filter / 403-error). The e2e scrub test (`slider.fill("0")` → newer op hidden, older survives) proves the cursor filter is real (AP-4).

## Impact
Frontend-only. No backend / wire-schema / migration / `styles-mockup.css` change. Memory page Recent Ops + TimeTravel now fully real; `AD-Memory-OpsHistory-Backend` end-to-end closed.
