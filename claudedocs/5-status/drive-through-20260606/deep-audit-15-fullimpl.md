# Deep Drive-Through — 15 full-impl pages (2026-06-07)

**Purpose**: Second-pass, per-control drive-through of the 15 full-impl frontend pages. The 2026-06-06 `audit.md` was a single-pass visual+network sweep that classified pages but left most interactive controls marked "untested this pass". This pass actually *drives* every action control (click → observe effect), verifies the FIX-028/029/030 fixes landed, and re-classifies pages on real interaction evidence — per CLAUDE.md §Drive-Through Acceptance Hard Constraint (gate-green ≠ usable).
**Category / Scope**: Status / Drive-Through deep audit (15 full-impl pages only; 12 proposed stubs + 8 auth covered by `audit.md`)
**Created**: 2026-06-07
**Status**: Complete (15/15 driven)
**Method**: Playwright MCP single browser session, real UI (:3007) + real backend (:8000, `--reload` on current main incl. FIX-028/029/030) + real LLM (Azure gpt-5.2). dev-login as `dan@acme.com · admin`. Screenshots in `shots-deep/`.

> Builds on `audit.md` (2026-06-06, 35-page surface sweep). This file = deep interaction layer for the 15 full-impl pages.

---

## 1. Headline

- **All 3 prior fixes verified live**: FIX-028 (sla-report 500 → 200), FIX-029 (orchestrator gap banner), FIX-030 (overview KPI banner + admin-tenants "50 tenants" header).
- **Spine is genuinely real, confirmed first-hand**: chat-v2 main flow drove end-to-end (real gpt-5.2 → answer rendered → verification passed → full TAO trace → **cost_ledger rose $0.034 → $0.038 on the cost-dashboard**). governance / verification / memory / subagents / cost / sla / tenant-settings all hit real 200 APIs.
- **Deep interaction caught 3 dead-control findings the surface audit missed** (NEW-1/2/3): action controls that look functional but do nothing, with no disclosure. Two of the 15 pages downgrade from 🟢→🟡 on this.
- **Two GOLD honesty patterns already exist in the codebase** and should be the template for fixing the dead controls: memory's *click → "backend gap" alert*, and tenant-settings' *disable-when-empty*.
- **RBAC still cosmetic** (ISSUE-6 confirmed): logged in as `admin`, every page renders role `user`.

---

## 2. Per-page verdicts (deep)

Legend: 🟢 達標 · 🟡 混合(real core + dead/labelled gaps) · 🔴 problem

| # | Page | Verdict | Real API (200) | Deep-interaction findings |
|---|------|---------|----------------|---------------------------|
| 1 | cost-dashboard | 🟢/🟡 | `cost-summary?month` | "By tenant" + "CSV" buttons **genuinely `disabled`** (honest, not dead-clickable); 8 fixture notes; spend $0.034→$0.038 real. Minor: top-KPI deltas (+8.4% / +2.1M) likely fixture, unlabelled. |
| 2 | overview | 🟡 | `loops?status=running` | **FIX-030 verified**: 6 BackendGapBanners incl. the new KPI-row one disclosing $2,847 is fixture. Quick-action "Open Loop Debug" **really navigates** → /loop-debug. 12 notes. |
| 3 | orchestrator | 🟡 (was 🔴) | none (all fixture) | **FIX-029 verified**: "⚠️ Backend orchestrator config / deploy API pending Phase 58+" banner present. BUT **"Deploy" = dead control** (click → no toast, no network, no effect). → NEW-3. |
| 4 | subagents | 🟡 (was 🟢) | `subagents` | Real agent_catalog (researcher/reviewer/planner) renders. BUT **all 3 action controls dead+unlabelled** ("Sync from repo" / "New subagent" / "Test invoke" → no modal/toast/API). → NEW-1. |
| 5 | loop-debug | 🟡 | none (DEMO) | DEMO labelled. **Scrubber is interactive** — set slider → counter `18/18`→`03/18` (functional fixture playback). Filters + 1-16× speed present. |
| 6 | memory | 🟢 | `memory/matrix` + `memory/ops` | Real data, honest empty states. **"New entry" → alert "backend gap (Phase 58+) — memory POST endpoint pending"** = GOLD honesty pattern. |
| 7 | state-inspector | 🟡 | (`?session_id` live path) | Version chain fixture but labelled; "Restore from version" surfaces the AD-State-VersionChain-Phase58 backend-gap disclosure. |
| 8 | governance | 🟢 (upgraded) | `governance/approvals` + **`audit/log`** | Approvals real (empty "No pending approvals"). **Audit Log tab → real `GET /audit/log` 200, ~17 rows, NO fixture note** (better than audit's "peripheral demo"). Only stat chips (Approved 184…) demo. |
| 9 | verification | 🟢 | `verification/recent` | 45 judge-signal hits = real B-8 llm_judge log (incl. this session's chat + 57.83 tests). Peripheral KPIs labelled "aggregation endpoint pending". |
| 10 | redaction | 🟡 | none (fixture) | Whole-page fixture, clearly labelled ("observation-masker API not yet shipped"). 8-pattern catalog renders. |
| 11 | error-policy | 🟡 | none (fixture) | Fixture clearly labelled (AD-ErrorPolicy-Backend-API). "Force close" surfaces the backend-gap disclosure. |
| 12 | sla-dashboard | 🟢 (was 🔴) | **`sla-report?month`** | **FIX-028 verified**: sla-report **200** (was HTTP 500), **no "Failed to load" alert**, full dashboard renders (latency dist / SLO / slow-ops / error-rate). Peripheral "visual-only" labelled. |
| 13 | admin-tenants | 🟡 (was 🟢) | `admin/tenants` + `/stats` | **FIX-030 verified**: header "50 tenants" (real count), fixture string "48 active · 3 anomalies" gone. Real 50-row list. BUT **toolbar dead+unlabelled**: "Filter by name…" is a static `<span>` faking a search box (no input), "Plan: all" / "Sort: runs" → no menu/effect. → NEW-2. |
| 14 | tenant-settings | 🟢 | `admin/tenants/{id}` + `/identity` + `/feature-flags` | 6 tabs, real DB data. FF tab: real GET (empty), honest note, **"Edit" button correctly `disabled` when no flags** = GOLD pattern. Write path (57.54-57.57) backend-verified but not UI-drivable with empty data. Minor: tab badge "14" vs body "No feature flags registered". |
| 15 | chat-v2 | 🟢 ⭐ | **`POST /chat/`** | **MAIN-FLOW DRIVE-THROUGH PASS**: "What is the capital of Japan?" → real gpt-5.2 → **"Tokyo" rendered** → **Verification passed** → full TAO trace (loop_start/compaction/prompt_build/llm_call/checkpoint/verification/loop_end/end_turn) → **cost_ledger $0.034→$0.038**. ISSUE-5 (Inspector Turn metadata "—") still open, deferred. |

**Tally**: 🟢 達標 7 (memory, governance, verification, sla-dashboard, tenant-settings, chat-v2, cost-dashboard) · 🟡 混合 8 · 🔴 0. (orchestrator + sla-dashboard both left the 🔴 column thanks to FIX-029/028.)

---

## 3. Fix verifications (this session, first-hand)

| Fix | Prior symptom | Now | Evidence |
|-----|---------------|-----|----------|
| **FIX-028** | `/sla-report → 500`, "Failed to load data" alert | `/sla-report → 200`, dashboard renders, no alert | shots-deep/12 + network 200 |
| **FIX-029** | orchestrator unlabelled Potemkin | gap banner present | shots-deep/03 + banner text |
| **FIX-030 (overview)** | $2,847 KPI unlabelled fixture | KPI-row BackendGapBanner present (6 total) | shots-deep/02 |
| **FIX-030 (admin-tenants)** | header "48 active · 3 anomalies" fixture string | header "50 tenants" real count | shots-deep/13 |
| **ISSUE-6 (RBAC)** | admin selected, renders user | **still cosmetic** (confirmed open) | shots-deep/00 |

---

## 4. New findings (deep pass)

| ID | Sev | Finding | Where | Suggested fix |
|----|-----|---------|-------|---------------|
| **NEW-1** | 🟡 AP-4 | subagents 3 action controls dead+unlabelled (Sync from repo / New subagent / Test invoke → no modal/toast/API) | /subagents | Adopt memory's click→"backend gap" alert, OR `disabled` |
| **NEW-2** | 🟡 AP-4 | admin-tenants toolbar dead+unlabelled: "Filter by name…" is a static `<span>` faking a search input (no `<input>` exists); "Plan: all" / "Sort: runs" → no effect | /admin-tenants | Wire client-side filter/sort, OR `disabled` + disclosure |
| **NEW-3** | 🟡 AP-4 | orchestrator "Deploy" (and config form controls) dead-clickable; FIX-029 banner discloses at page level but individual controls still silently do nothing | /orchestrator | `disabled` the config controls, OR toast on click (banner alone insufficient per drive-through DoD) |
| NEW-4 | 🟢 minor | Route-change cancels React-Query requests → `AbortError: signal is aborted without reason` logged as `kind: network` error via `observability.ts:42` (telemetry noise, not a real failure) | global | Filter AbortError from network-error telemetry |
| NEW-5 | 🟢 minor | `POST /api/v1/telemetry/frontend → ERR_ABORTED` (frontend telemetry beacon aborting) | global | Investigate beacon lifecycle |
| NEW-6 | 🟢 minor | tenant-settings FF tab badge "14" vs body "No feature flags registered for this tenant" | /tenant-settings | Clarify badge = registry count vs tenant overrides |
| NEW-7 | 🟢 minor | cost-dashboard + overview top-KPI deltas (+8.4% / +2.1M) likely fixture, unlabelled | /cost-dashboard, /overview | Add to existing fixture note coverage |

---

## 5. Cross-cutting observations

- **Honest-fixture labelling is the strong norm**: 12 of 15 pages prominently disclose their fixture/demo widgets with `⚠️ … pending Phase 58+ AD-…` notes. The dead-control findings (NEW-1/2/3) are the *exceptions* where action controls were left interactive-looking with no disclosure.
- **Two GOLD patterns to standardize on** (already in-codebase):
  1. **memory** — write control click → `alert("backend gap (Phase 58+) — … endpoint pending")`.
  2. **tenant-settings** — control `disabled` when there's no data to act on (FF "Edit" button).
  - Same codebase ships both the right pattern and the dead-control anti-pattern. NEW-1/2/3 = make the dead controls follow memory/tenant-settings.
- **The spine is real, not Potemkin** (first-hand): chat-v2 main flow + governance audit-log + verification judge-log + memory matrix/ops + subagents catalog + cost-summary + sla-report all returned real 200s and rendered real data this session.
- **`net::ERR_ABORTED` duplicate request pattern** seen on nearly every page is React StrictMode dev double-invoke + route-change cancellation — a dev-mode artifact, not a backend defect (the paired real request returns 200).

---

## 6. Next-sprint candidates (added to `next-phase-candidates.md`)

- `AD-Subagents-DeadControls-Disable-Or-Alert` (NEW-1)
- `AD-AdminTenants-Toolbar-Filter-Sort-Wire-Or-Disable` (NEW-2)
- `AD-Orchestrator-DeadControls-Disable-Or-Toast` (NEW-3, complements FIX-029 banner)
- `AD-Observability-AbortError-Network-Noise-Filter` (NEW-4)
- (carryover, unchanged) `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5), `AD-RBAC-DB-To-JWT-Wiring-Phase58` (ISSUE-6)

---

## 7. Screenshots

`shots-deep/`: 00-rbac · 01-cost-dashboard · 02-overview · 03-orchestrator · 04-subagents · 05-loop-debug · 06-memory · 07-state-inspector · 08-governance · 09-verification · 10-redaction · 11-error-policy · 12-sla-dashboard · 13-admin-tenants · 14-tenant-settings · 14b-tenant-settings-flags · 15a-chatv2-initial · 15b-chatv2-answer
