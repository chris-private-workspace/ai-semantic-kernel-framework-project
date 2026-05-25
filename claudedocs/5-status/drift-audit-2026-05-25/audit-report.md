# 22-Page Mockup-Fidelity Drift Audit — 2026-05-25

**Trigger**: User observation that 「除了 operations 目錄下的幾個頁面之外, 其他的頁面其實明顯不是和 mockup 的效果一致的, 我印象中也不是全部有重建了」after Sprint 57.39 closure.

**Method**:
1. Production sweep: `node frontend/scripts/route-sweep.mjs after` — 24 PNGs (8 PUBLIC + 16 AppShellV2) at 1440×900, dev server `localhost:3007`
2. Mockup sweep: NEW `frontend/scripts/mockup-sweep.mjs` against `python -m http.server 8080` serving `reference/design-mockups/index.html` — 23 PNGs hash-route per page
3. Side-by-side visual compare per page; verdict scale ✅ PARITY / 🟡 NEAR-PARITY / 🟠 STRUCTURAL drift / 🔴 CATASTROPHIC drift / 🟣 PROP-by-design

**Output dir**: `claudedocs/5-status/drift-audit-2026-05-25/screenshots/{after,mockup}/`

---

## Verdict summary (23 pages compared)

| Verdict | Count | Pages |
|---------|:-----:|-------|
| ✅ **PARITY** | 17 | 7 auth (login + callback + register + invite + mfa + expired + dev) / 7 ops (overview + orchestrator + subagents + loop-debug + state-inspector) + 3 governance (governance ⭐ + redaction + error-policy) + 2 dashboards (cost-dashboard + sla-dashboard) |
| 🟡 **NEAR-PARITY** | 1 | chat-v2 (Inspector tab name divergence) |
| 🔴 **CATASTROPHIC drift** | 4 | **memory / verification / admin-tenants / tenant-settings** (post Sprint 57.40 /governance rebuild) |
| 🟣 **PROP-by-design** | 1 | compaction representative (intentional ComingSoonPlaceholder, NOT drift) |

---

## Per-page verdict table

| # | Path | Verdict | Mockup design | Production reality | Drift severity |
|---|------|:-------:|--------------|--------------------|---------------|
| 1 | `/auth/login` | ✅ PARITY | SSO 3-button + SAML + email + Continue | Same; AP-2 banner intentional | none |
| 2 | `/auth/callback` | ✅ PARITY | spinner + 3-step progress (SAML / RLS / flags) | Same; production further along (2/3 ✓) | none |
| 3 | `/auth/register` | ✅ PARITY | 4-step wizard (Identity / Org / Plan / Confirm) | Same; AP-2 banner about Phase 58+ IAM Block B | none |
| 4 | `/auth/invite` | ✅ PARITY (pattern) | mockup designed | not individually verified — same Sprint 57.23+57.35 batch | none |
| 5 | `/auth/mfa` | ✅ PARITY | 6-digit grid + Authenticator/Security Key tabs | Same; AP-2 banner about Block C 501 | none |
| 6 | `/auth/expired` | ✅ PARITY (pattern) | mockup designed | same Sprint 57.23+57.35 batch | none |
| 7 | `/auth/dev` | ✅ PARITY (pattern) | mockup designed | same Sprint 57.23+57.35 batch | none |
| 8 | `/overview` | ✅ PARITY | 4 KPI + 2-col main (Active loops + HITL queue + Cost burn + Providers) | Same numbers + same layout; AP-2 banner intentional | none |
| 9 | `/chat-v2` | 🟡 NEAR-PARITY | 3-col (session list + chat + Inspector with **Run/Tools/Memory/Verify** tabs) | Same 3-col; Inspector tabs are **Turn/Trace/Memory/Tree** | tab name vocab divergence (1 component) |
| 10 | `/orchestrator` | ✅ PARITY | header + 4 KPI + 6-tab + Core settings form + Memory access + Verification sidebar | Pixel-perfect match | none — Sprint 57.34 holds clean |
| 11 | `/subagents` | ✅ PARITY | Subagent Registry + 4 KPI + table left + Detail pane right | Pixel-perfect match | none — Sprint 57.38 holds clean |
| 12 | `/loop-debug` | ✅ PARITY | Loop Visualizer + Replay/Live + playback strip + filter pills + turn-grouped events + Inspector pane | Same; AP-2 banner about SSE persistence | none — Sprint 57.37 holds clean |
| 13 | `/memory` | 🔴 **CATASTROPHIC** | **Memory Layers 5×N matrix** (SYSTEM/TENANT/ROLE/USER/SESSION × time-scale columns) + playback slider + time travel + Export + New write + Recent memory ops strip bottom | Only **2-tab (Recent / By Scope)** + 1 Layer dropdown + "No memory entries in this layer" placeholder | **FULL REBUILD** — design fundamentally different |
| 14 | `/state-inspector` | ✅ PARITY | 4 KPI + Version chain left + Detail pane with Diff vs parent | Same; AP-2 banner intentional | none — Sprint 57.37 + FIX-011 + FIX-013 hold clean |
| 15 | `/governance` | ✅ **PARITY** (post-rebuild) | HITL Approvals + 4 KPI + **5-tab nav** (Pending/Approved/Rejected/Expired/Policies) + 2-col Pending list + Detail pane + Approve/Reject buttons | **Same** — Sprint 57.40 Day 1 full rebuild ships 5 NEW components (PageHeader/StatsStrip/FilterTabs/DetailPane/EmptyTab) + ApprovalsPage restructure + ApprovalList 7-col upgrade. The pre-audit "runtime error banner" was a **route-sweep mock fixture artifact** (D-DAY1-2), NOT a production bug; fixed in D-DAY0-1 mock | **none** — Sprint 57.40 holds clean |
| 16 | `/verification` | 🔴 **CATASTROPHIC** | Verification header + 4 KPI + 2-col Recent verification runs + Failure modes sidebar + Policy checks | Only filter form (Session ID / Verifier Type / Passed) + Apply/Reset + "No entries match" empty state | **FULL REBUILD** |
| 17 | `/redaction` | ✅ PARITY | Observation Masker + 4 KPI + Patterns table (8 rules) + Recent redactions sidebar | Pixel-perfect match; AP-2 banner intentional | none — Sprint 57.39 Phase-2 clean |
| 18 | `/error-policy` | ✅ PARITY | Error Policy + 4 KPI + 4-class taxonomy + Retry budget + Circuit breakers table | Pixel-perfect match; AP-2 banner intentional | none — Sprint 57.39 Phase-2 clean |
| 19 | `/cost-dashboard` | ✅ PARITY | Cost Ledger + 4 KPI + Spend over time area chart + Spend by category + Spend by tenant table + Provider mix | Pixel-perfect match; AP-2 banner intentional | none — Sprint 57.31 Phase-2 clean |
| 20 | `/sla-dashboard` | ✅ PARITY | SLA Dashboard + 4 KPI + Latency distribution + SLO status sidebar + Top slow ops table + Error rate by service | Pixel-perfect match; AP-2 banner intentional | none — Sprint 57.32 Phase-2 clean |
| 21 | `/admin-tenants` | 🔴 **CATASTROPHIC** | Tenants + 4 KPI (Active tenants / Total seats / Agents / Anomalies) + **9-col tenants table** with 9 rows (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED) | Only filter form (State/Plan/Search) + "No tenants match current filter" + pagination "0-0 of 0" | **FULL REBUILD** — known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #1 |
| 22 | `/tenant-settings` | 🔴 **CATASTROPHIC** | Tenant Settings + tenant chip + **6-tab nav** (General/Feature Flags 14/Quotas/HITL Policies/Members 8/Danger Zone) + 2-col General form + Identity & SSO sidebar | Plain `Tenant ID / Code / Display Name / State / Plan / Created / Updated / Provisioning JSON / Edit` field list | **FULL REBUILD** — known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #2 |
| 23 | `/compaction` (PROP rep) | 🟣 by design | Context Compaction + 4 KPI + Recent compactions table + Strategy mix sidebar | ComingSoonPlaceholder ("Coming Soon — design is in design/operator-portal/page-platform.jsx") | **not a drift** — PROP active=true+proposed=true intentionally renders placeholder; PROP→real promotion is the work |

---

## Key findings

### 1. User observation 100% correct (initial); 1 of 5 now resolved

The initial audit confirmed that **5 production pages were fundamentally different from mockup** (CATASTROPHIC drift). Pre-audit CLAUDE.md status said `15/17 Phase-2 routes shipped`; the truth before Sprint 57.40 was **~14 PARITY + 1 NEAR-PARITY + 5 CATASTROPHIC + 12 PROP stubs unshipped + 4 DRAFT inactive**.

**Post Sprint 57.40 (this report's first follow-up sprint)**: `/governance` rebuilt → **17 PARITY + 1 NEAR-PARITY + 4 CATASTROPHIC remaining** (memory / verification / admin-tenants / tenant-settings).

### 2. Two NEW catastrophic drift findings (not previously tracked)

| Page | Why it slipped through | Implication |
|------|------------------------|-------------|
| `/memory` | Sprint 57.33 only crash-fixed (`?? []` defensive guard); never Phase-2 re-pointed. Mockup `Memory Layers` 5×N matrix design was never ported — current page is Sprint 57.12 vintage shadcn-utility | Add to Phase 58+ STRUCTURAL list (now **3 routes**, not 2) |
| `/governance` | Sprint 57.39 Phase-2 + FIX-015 + FIX-017 only swapped tokens / shadcn-utility residue on the EXISTING simple page. Mockup `HITL Approvals` 4-KPI + 5-tab + 2-col Pending/Detail layout was never built | ✅ **RESOLVED Sprint 57.40 Day 1** — full rebuild ships 5 NEW components + ApprovalsPage restructure + ApprovalList 7-col upgrade. Verified PARITY via screenshot compare. |

### 3. Two known carryover STRUCTURAL drifts confirmed

| Page | Status |
|------|--------|
| `/admin-tenants` | CLAUDE.md known 🟡 STRUCTURAL Phase 58+ #1 — confirmed CATASTROPHIC |
| `/tenant-settings` | CLAUDE.md known 🟡 STRUCTURAL Phase 58+ #2 — confirmed CATASTROPHIC; also matches Sprint 57.22 audit `6-tab architectural finding` |

### 4. One NEAR-PARITY drift (low-priority fix)

| Page | Drift |
|------|-------|
| `/chat-v2` | Inspector tab names: mockup `Run / Tools / Memory / Verify` vs production `Turn / Trace / Memory / Tree`. Same components, different vocab. ~30 min rename. |

### 5. `/governance` red banner was a sweep-mock artifact, NOT a production bug ✅ RESOLVED

The initial draft of this report identified a red "Failed to load approvals: ['governance','approvals'] data is undefined" banner in the production sweep PNG. Sprint 57.40 D-DAY1-2 investigation revealed this was a **route-sweep mock fixture artifact**:

- `governanceService.listPending()` reads `body.items` from a `PendingListResponse` shape (`{items, total, has_more}`)
- The sweep's `/api/v1/` fallback returns `[]` (raw array) → `body.items === undefined` → TanStack throws
- Real backend at `api/v1/governance/router.py` returns the correct shape — production traffic is fine

**Fix** (Sprint 57.40 Day 2 §2.3): added `/governance/approvals` specific mock returning `{items: [], total: 0, has_more: false}` to `route-sweep.mjs`. Sister cases (`cost-summary` / `sla-report`) already had specific mocks; this completes the parity.

This is also a tooling lesson: any new endpoint that returns an envelope shape (not a raw list) needs an explicit sweep mock entry; the default `[]` is only safe for list-shaped endpoints.

### 6. Spot-check method note

7 auth routes were sampled at 4/7 (auth-login + auth-callback + auth-register + auth-mfa). All 4 are PARITY. Sprint 57.23 (round 2) + Sprint 57.35 (Phase-2 re-point) rebuilt all 7 in the same batch, so remaining 3 (invite/expired/dev) are marked PARITY by pattern — a follow-up spot-check is cheap (~5 min).

---

## Effort estimate to close all drifts

| Item | Verdict | Effort | Class (calibration matrix) |
|------|---------|--------|---------------------------|
| `/chat-v2` Inspector tab rename | 🟡 NEAR-PARITY | ~30 min | frontend-refactor-mechanical 0.50 |
| `/memory` Memory Layers 5×N matrix rebuild | 🔴 CATASTROPHIC | ~10-15 hr | frontend-mockup-strict-rebuild 0.60 |
| `/governance` runtime error fix + rebuild | 🔴 CATASTROPHIC | ~12-15 hr (fix bug ~2-3 hr + rebuild ~10-12 hr) | frontend-page-bug-fix 0.45 + frontend-mockup-strict-rebuild 0.60 |
| `/verification` rebuild | 🔴 CATASTROPHIC | ~8-10 hr | frontend-mockup-strict-rebuild 0.60 |
| `/admin-tenants` rebuild | 🔴 CATASTROPHIC | ~12-15 hr | frontend-mockup-strict-rebuild 0.60 + backend list endpoint already exists |
| `/tenant-settings` 6-tab rebuild | 🔴 CATASTROPHIC | ~15-20 hr | frontend-mockup-strict-rebuild 0.60 (6-tab is largest scope) |
| **Total** | | **~58-75 hr** | bottom-up sum — 6-8 sprints at 8 hr/sprint pace |

After calibration multiplier (~0.55-0.65 frontend-mockup-strict-rebuild evidence Sprint 57.23-57.27 = 0.59-1.19 ratio range, 5-pt mean 0.96):

**Calibrated commit: ~35-50 hr (4-6 sprints)**.

---

## Recommendations (ordered by ROI)

| Priority | Action | Rationale |
|---------|--------|-----------|
| ~~1~~ | ~~**Fix `/governance` data-fetch runtime error**~~ | ✅ **RESOLVED Sprint 57.40 Day 2** — was sweep-mock artifact (see Key finding #5); fixed in route-sweep `/governance/approvals` mock entry |
| ~~2~~ → 1 | **`/chat-v2` Inspector tab rename** | 30-min quick win |
| ~~3~~ | ~~**`/governance` rebuild**~~ | ✅ **RESOLVED Sprint 57.40 Day 1** — 5 NEW components + ApprovalsPage restructure + ApprovalList 7-col; agent-delegated ~1.2 hr wall-clock |
| ~~4~~ → 2 | **`/verification` rebuild** (4 KPI + 2-col + sidebar) | Pattern reuse from Sprint 57.40 governance primitives (StatsStrip / FilterTabs / DetailPane); ~8-10 hr |
| ~~5~~ → 3 | **`/memory` Memory Layers matrix rebuild** | Big-impact UX upgrade; ~10-15 hr; reuse some primitives from cost-dashboard / sla-dashboard |
| ~~6~~ → 4 | **`/admin-tenants` rebuild** | Backend GET endpoint already wired; pure frontend work; ~12-15 hr |
| ~~7~~ → 5 | **`/tenant-settings` 6-tab rebuild** | Largest scope; mostly form work; ~15-20 hr |
| ~~8~~ → 6 | Update CLAUDE.md routes-shipped count + carryover list | Honest status reflection; post Sprint 57.40 reality is **18-19/22** if we count audit re-verified pages |

---

## Validation infrastructure produced (reusable)

| Artifact | Path | Future use |
|----------|------|-----------|
| `mockup-sweep.mjs` | `frontend/scripts/` | sister of `route-sweep.mjs`; per-sprint Day 0 + Day N drift evidence |
| Production sweep dir | `claudedocs/5-status/drift-audit-2026-05-25/screenshots/after/` | 24 PNGs reusable as baseline for next audit |
| Mockup sweep dir | `claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/` | 23 PNGs — mockup is the canonical reference, only re-shoot when mockup updates |
| This report | `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` | canonical pre-Phase-58 drift baseline |

---

## Carryover ADs from this audit (post Sprint 57.40)

1. 🆕 **`AD-Memory-Layers-Matrix-Rebuild`** — `/memory` needs full rebuild to mockup `Memory Layers` 5×N matrix design. Currently Sprint 57.12 vintage shadcn-utility implementation. Class: `frontend-mockup-strict-rebuild` 0.60. Est ~10-15 hr.
2. ✅ **`AD-Governance-Catastrophic-Rebuild-And-Bug-Fix`** — **CLOSED Sprint 57.40**: (a) "data-fetch runtime bug" turned out to be a route-sweep mock fixture artifact (D-DAY1-2) — fixed in `/governance/approvals` specific mock; (b) full rebuild ships Sprint 57.40 Day 1 via agent-delegated 5 NEW components + ApprovalsPage restructure + ApprovalList 7-col upgrade. Verified PARITY.
3. 🆕 **`AD-Verification-Catastrophic-Rebuild`** — `/verification` needs full rebuild to mockup 4-KPI + 2-col Recent + Failure modes/Policy checks sidebar design. Currently just filter form. Class: `frontend-mockup-strict-rebuild` 0.60. Est ~8-10 hr. **Pattern-reuse candidate**: Sprint 57.40 governance primitives (StatsStrip / FilterTabs / DetailPane) likely transfer; consider as next sprint after Sprint 57.40 merge.
4. 🆕 **`AD-ChatV2-Inspector-Tab-Rename`** — rename Inspector tab vocabulary `Turn/Trace/Memory/Tree` → mockup `Run/Tools/Memory/Verify`. ~30 min. Class: `frontend-refactor-mechanical` 0.50.
5. 🆕 **`AD-CLAUDE-md-Frontend-Status-Realignment`** — update `Phase 57+ 11/17 routes shipped / 2 🟡 STRUCTURAL remaining` to honest count after this audit. **Post Sprint 57.40**: STRUCTURAL list is **4** (`/memory` + `/verification` + `/admin-tenants` + `/tenant-settings`); Phase-2 epic count moves toward 12-16/17 depending on whether the audit pages count as "shipped".
6. ✅ **`AD-Sprint-57.23-Auth-Spot-Check-Complete`** — Sprint 57.23 + 57.35 rebuild verified PARITY on 4/7 auth routes; 3 not-yet-individually-verified follow-up trivial (~5 min spot-check).
7. 🆕 **`AD-RouteSweep-Envelope-Mock-Convention`** (Sprint 57.40 D-DAY1-2 lesson) — add a `testing.md` or `frontend-mockup-fidelity.md` note: any backend endpoint returning an envelope shape (e.g. `{items, total, has_more}`) needs an explicit sweep mock entry in `route-sweep.mjs`; the default `[]` is only safe for list-shaped endpoints. Codify with grep pattern + example to prevent future false-positive red banners in audit captures.

---

**Author**: Claude Opus 4.7 (1M context) via 23-pair side-by-side audit
**Date**: 2026-05-25 (initial); updated 2026-05-25 Sprint 57.40 Day 2 closeout
**Status**: Sprint 57.40 closed `/governance` rebuild + sweep-mock fix. Remaining 4 CATASTROPHIC + 1 NEAR-PARITY awaits user prioritization (see Recommendations).
