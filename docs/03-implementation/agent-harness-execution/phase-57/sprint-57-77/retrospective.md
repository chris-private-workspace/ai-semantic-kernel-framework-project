# Sprint 57.77 Retrospective — Memory ops-history frontend

**Closed**: 2026-06-04
**Branch**: `feature/sprint-57-77-memory-ops-history-frontend`
**Commits**: `90017c2d` (Day-0) + `6ec7024e` (Track A frontend + header migration) + closeout

---

## Q1 — Goal & delivery
Closed the **frontend half** of `AD-Memory-OpsHistory-Backend` → the AD is now **fully closed** (backend 57.76 + frontend 57.77). Delivered: `useMemoryOps` hook (mirror `useMemoryMatrix`) + `fetchOps` service + `MemoryOpItem`/`MemoryOpsResponse` wire-verbatim types; RecentMemoryOpsCard consumes `GET /memory/ops` with a real cursor-filter; TimeTravelScrubber marks derive from real `created_at_ms` + scrub really filters RecentOps; MemoryView cursor = ms|null + playback over the real op range; 3 ops fixtures + 2 stale gap banners removed; first-ever Vitest component coverage + Playwright e2e. User-locked **full wire** (AskUserQuestion): scrub = browse-ops-timeline (honest, not state reconstruction) → AP-4 clean.

## Q2 — Calibration
Scope class `medium-frontend` (0.65) + `agent_factor` `mechanical-greenfield-design-decisions` (0.65 — NEW hook mirror + NEW API types + NEW scrub→filter UX state). **Agent-delegated: yes** (single Track A frontend code-implementer ~8.5 min wall-clock + parent Day-0 2-researcher + header migration + full re-verify + closeout). Bottom-up ~12 hr → class-calibrated ~7.8 hr → agent-adjusted ~5 hr. **15th consecutive agent-delegated sprint with NO clean wall-clock** → ratio CAVEATED (`AD-Calibration-AgentDelegated-WallClock-Measure`); the parent header migration + 2-researcher Day-0 + full re-verify dominate the wall-clock, so the agent's ~8.5 min is not a usable per-sprint signal.

## Q3 — What went well
- **Day-0 2-researcher front-load paid off**: the authoritative wire shape (`MemoryOpItem` field names, WRITE/EVICT not READ/EXPIRE, user/tenant-only scope, `created_at_ms` cursor) + mirror targets (`useMemoryMatrix`/`fetchMatrix`) + greenfield-test reality were all known before Day 1 → the hook/service/types mirrored first-pass, zero rework.
- **AP-4 scrub design held**: the user-locked "scrub really filters RecentOps" decision turned a potential Potemkin slider into a real effect; the e2e `slider.fill("0")` test proves the newer op disappears + the older survives — a real behavioral assertion, not a visual one.
- **Mockup-fidelity clean**: pure data-wiring added 0 hex/oklch literals; `check:mockup-fidelity` byte-identical + baseline 50 unchanged. CSS-var colors (`var(--memory)`/`var(--warning)`) for the op marks.
- **Honest fixture removal**: `_fixtures.ts` had 0 external importers after wiring → deleted the whole module (not left orphan); grep-confirmed before deletion (Karpathy §3).

## Q4 — What to improve / lessons
- **Incomplete-wire caught at parent review (the real lesson)**: the agent passed hardcoded `<MemoryPageHeader cursor={0}>` to avoid touching the out-of-scope 57.73 header — but that left the header's time-travel Badge/button permanently inert + a dead `cursor < 0` branch, and the scrub never reflected in the header. This is a classic "agent stays narrowly in-scope and leaves a half-wired seam" pattern. **Lesson**: when delegating a "wire X into the page" task, the parent re-verify must trace the cursor/state ALL the way through every consumer in the page (here: header was a 3rd consumer the plan under-scoped), not just the two widgets named in the plan. The Prong-2.5 child-component-tree audit exists for exactly this — but it audits *styling* drift; this was a *state-wiring* seam. Consider extending the Day-0 frontend audit to also enumerate "who else consumes the state being migrated" (here: grep `cursor` consumers of MemoryView). Caught + fixed via AskUserQuestion (user approved the scope expansion); no harm shipped.
- **Plan §4 test-location drift**: plan assumed colocated `src/**/*.test.tsx` were NEW; reality = Vitest `include` is `tests/unit/**` and 4 memory component tests already existed (57.73). A Day-0 Prong-1 path check on the *test* files (not just product files) would have caught this — same lesson as Sprint 57.66's test-infra-file-verify, applied to frontend Vitest layout. Reconciled at closeout; no coverage lost (rewrite-in-place).

## Q5 — Carryover
- **READ-path ops** — write/evict only (57.76 backend); sampled reads a future option.
- **role/session/system layer ops** — those layers raise / in-memory (57.76); not recorded → never appear in RecentOps/marks.
- **Point-in-time state reconstruction** — scrub is ops-browsing (filter visible ops by time); replaying snapshots to rebuild memory state at an arbitrary timestamp is a deeper future capability (retro 57.76 Q5).
- **Server-side ops time-window filtering** — this sprint filters client-side from a single 50-row page; the server `before` cursor is wired in `fetchOps` but only used for pagination, not the scrub. Deep-history scrub would need server-side windowed fetch.
- **FE `/subagents` real list** (`AD-Subagent-RealList-Phase58`) — **the last Area-A remaining item** (agent_catalog specs already exist; needs tenant-facing GET + FE re-mount, mirrors 57.73 admin-tenants re-mount).

## Q6 — Anti-pattern / discipline check
- AP-4 (no Potemkin) ✅ — RecentOps renders real persisted ops; scrub really filters (e2e-proven); empty/role/session honest non-render (not faked); header dead `cursor < 0` branch eliminated. AP-2 (no orphan) ✅ — fixtures + 2 stale banners removed, `_fixtures.ts` deleted (0 importers), wire is on the live page path. Mockup-fidelity ✅ (byte-identical CSS, baseline 50, var-colors, no shadcn residue). LLM-neutrality N/A (frontend, no LLM). Sprint workflow ✅ (plan→checklist→Day-0→code→progress→retro). File headers ✅ (MHist on all touched + 1 new). English state copy (57.73 lesson honored).

## Q7 — Closeout verification (parent-run)
- build tsc 0; lint exit 0 (3 pre-existing jsx-ast-utils info); Vitest **750 passed / 132 files**; `check:mockup-fidelity` byte-identical + baseline 50; Playwright `memory-ops` 3 passed (happy / scrub-filter / 403-error).
- **No design note** (feature-continuation: data-wiring of the shipped GET /memory/ops into mockup-ported components; no new contract / no 17.md change).
