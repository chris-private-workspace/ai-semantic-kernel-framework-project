# FIX-030: drive-through audit minor-items bundle (3 fixes)

**Date**: 2026-06-07
**Sprint**: post-57.87 (drive-through audit follow-up)
**Scope**: Frontend honesty (overview + admin-tenants) + backend correctness (registration)

Bundles the genuinely-minor 🟡🟢 items from the 2026-06-06 35-page drive-through
audit. The 4th audit item (`AD-ChatV2-Inspector-Turn-Metadata-Wire`) is **NOT** in
this bundle — see "Deferred" below.

---

## Item A — `AD-Overview-TopKPI-Fixture-Label` (🟡 AP-4 honesty)

**Problem**: /overview top-4 KPI cards (active sessions 14 / HITL 3 / cost MTD $2,847
/ SLA p95 1.84s) are fixture, unlabeled. $2,847 contradicts the real cost_ledger
(~$0.03). The 5 widgets below already carry their own `BackendGapBanner`; the KPI
row was the gap.

**Fix**: add one `BackendGapBanner` under the KPI row (the same canonical AP-2 marker
the rest of the page uses). New `overview.kpiBackendGap` i18n key (en + zh-TW).
Mockup-faithful: additive banner, no Stat widget mutated.

Files: `frontend/src/pages/overview/OverviewPage.tsx`, `frontend/src/i18n/locales/{en,zh-TW}/common.json`.

## Item B — `AD-AdminTenants-ListHeader-Fixture-String` (🟢 honesty)

**Problem**: /admin-tenants "All tenants" card subtitle was the hardcoded fixture
string `"48 active · 3 anomalies in last 24h"` — contradicts the real loaded rows
(and the stats strip's real "Active tenants" count). "anomalies in last 24h" has no
backend.

**Fix**: derive the subtitle from the real loaded rows — `` `${tenants.length} tenants` ``
(the table is already wired to GET /api/v1/admin/tenants). Drop the fixture string
+ delete the now-orphan `_fixtures.ts` (its only export; Karpathy §3). Test asserts
the real count renders + the "48 active" string is gone.

Files: `frontend/src/features/admin-tenants/components/TenantsTable.tsx`,
deleted `frontend/src/features/admin-tenants/_fixtures.ts`,
`frontend/tests/unit/admin-tenants/TenantsTable.test.tsx`.

Obsolete-test removal: `frontend/tests/unit/admin-tenants/_fixtures.test.ts` was a
single-assertion test that pinned `TABLE_SUBTITLE === "48 active · 3 anomalies …"` —
i.e. it locked the exact fixture string this fix removes. Its subject (`_fixtures.ts`)
is deleted, so the test is an orphan; the honest behavior is now covered in
`TenantsTable.test.tsx` (asserts the real `N tenants` subtitle renders + the "48 active"
string is gone). This is a subject-removed deletion, not a skip-to-pass.

## Item C — `AD-Register-Concurrent-Slug-Race` (🟡 backend correctness)

**Problem**: the audit suspected the register wizard's double POST created two
same-slug tenants. **Investigation corrected this**: `tenants.code` already has a DB
`unique=True` constraint, so duplicates are impossible. Empirically (concurrent probe
against the live backend): two same-slug registrations returned **req0: 201, req1:
500** — not two 201s, not a duplicate. The real bug: the second concurrent request
gets a raw **500** (unhandled `IntegrityError`) instead of the clean **409** the
serialized path returns. This affects production too (two people racing for the same
workspace URL), not just dev StrictMode.

**Fix**: wrap the tenant INSERT flush in `try/except IntegrityError` →
`raise TenantSlugTakenError()` (409). No migration (the unique constraint already
exists). Deterministic regression test via a mock session (pre-check returns None →
race window; flush raises IntegrityError → assert TenantSlugTakenError).

Files: `backend/src/platform_layer/identity/registration.py`,
`backend/tests/unit/platform_layer/identity/test_registration_service.py`.

---

## Deferred (NOT in this bundle)

**`AD-ChatV2-Inspector-Turn-Metadata-Wire`** — kept open. It is **not** a minor
label fix: `InspectorTurn` is already HONEST (renders "—" for unwired fields, not
fake values), so it is not a Potemkin/drive-through violation. Wiring the real values
needs store + backend-SSE work:
- `trace_id` IS available (injected into every SSE frame via `sse.py`) → cheap to map.
- `span_id` is on span events (the store already tracks `spans`).
- BUT `tokens_out` / `cost` are NOT in the SSE stream (cost is written server-side to
  cost_ledger only) → emitting them needs a backend `event_wire_schema` change.
This is a scoped wiring task (frontend store + backend SSE), tracked for a dedicated slice.

## Verification
- Backend: `black/isort/flake8/mypy` clean; registration unit tests green; `run_all.py` 10/10.
- Frontend: `npm run lint` (no `--silent`) + `npm run build` + `check:mockup-fidelity`
  (oklch baseline unchanged — banner uses semantic tokens); Vitest overview + admin-tenants green.
- **Drive-through** (real UI :3007 + clean-restart backend): /overview KPI banner renders;
  /admin-tenants subtitle shows the real count; concurrent register probe → **201 + 409** (was 201 + 500).

## Impact
2 frontend honesty fixes (additive banner + real-data subtitle, 1 orphan file removed)
+ 1 backend correctness fix (race → 409, no migration). No schema change. No mockup CSS change.
