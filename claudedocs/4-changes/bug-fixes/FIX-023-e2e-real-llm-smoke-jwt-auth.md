# FIX-023: e2e-real-llm-smoke.yml two latent bugs (JWT auth + SSE event name)

**Date**: 2026-06-01
**Sprint**: C-11 (integration-gap follow-up; non-sprint chore)
**Severity**: Medium (latent — gate never ran green so neither surfaced)
**Scope**: CI / E2E real-LLM verification
**Status**: ✅ Fixed + fully proven live (all 5 gate assertions pass against a real Azure call)

## Problem

`.github/workflows/e2e-real-llm-smoke.yml` (Sprint 57.6, the canonical real-LLM
e2e gate) authenticates its chat POST with only `-H "X-Tenant-Id: <id>"` and no
JWT. The chat endpoint `/api/v1/chat/` is NOT in `TenantContextMiddleware`'s
`EXEMPT_PATH_PREFIXES`, and that middleware **dropped X-Tenant-Id support** in
Sprint 52.5 Day 6.1 (now requires a V2 JWT via Bearer header or `v2_jwt` cookie,
because header-sourced tenant_id is trivially spoofable). So the request would
`401` at the middleware **before reaching the LLM** — the gate could never pass.

Secondary: the inline "Seed default tenant + admin user" step called
`get_db_session_with_tenant(tenant_id=None)` (not its real signature) and
`Tenant(name=, state=, plan=)` (not its real columns) — it would also crash.

**Bug #2 (SSE event name)**: the stream-content assertion was
`grep -q "event: loop_completed"`, but the serializer maps `LoopCompleted` →
`event: loop_end` (`sse.py:199`; documented `sse.py:21`). There is no
`loop_completed` event — the assertion would fail even with auth fixed and a
successful LLM call. Confirmed locally: an echo_demo stream emits
`loop_start … llm_response … loop_end` (no `loop_completed`).

## Root Cause

The workflow was authored Sprint 57.6 (2026-05-08) but **never ran green**: it
requires `AZURE_OPENAI_*` GitHub Secrets that were never provisioned (AD-CI-6),
and the `schedule` trigger is commented out. With no green run, the auth drift
(introduced 52.5 Day 6.1, predating the workflow) and the broken seed step sat
undetected. Discovered during C-11 analysis when attempting to actually run it.

## Solution

Replace the removed header-auth + broken seed with the real dev auth route:

1. **New "Authenticate (dev-login → v2_jwt cookie)" step**: `POST
   /api/v1/auth/dev-login?tenant_code=smoke&email=smoke@example.com` (an EXEMPT
   route, dev-only, `settings.env` defaults to `"development"` so it's live in
   CI). It auto-creates a dev Tenant + User and sets the `v2_jwt` cookie the
   middleware reads. Cookie saved to `/tmp/cookies.txt`.
2. **Removed the broken inline seed step** (dev-login does the create).
3. **Chat POST**: `-H "X-Tenant-Id: ..."` → `-b /tmp/cookies.txt` (send cookie).
4. **`.env`**: added `ENV=development` + `COOKIE_SECURE=false` so dev-login is
   live and sets a non-Secure cookie over plain HTTP in CI.
5. **Pre-chat row-count capture moved AFTER dev-login** so any rows dev-login
   writes are in the baseline; the delta then reflects only the chat request.

RLS note: `cost_ledger` (migration 0016) and `audit_log` use `ENABLE` (not
`FORCE`) ROW LEVEL SECURITY, so the workflow's `psql` `count(*)` (connecting as
table-owner `ipa`) bypasses RLS — the delta assertions remain valid.

## Verification

Proven LIVE on 2026-06-01 — a fresh backend started from the current tree
(repo-root `.env` with real Azure key) on port 8001, exercising the exact
workflow sequence (dev-login cookie → real_llm chat → DB delta), short-lived,
then killed (the long-running :8000 dev backend was untouched):

- YAML parses (`yaml.safe_load` → OK); step order Authenticate → pre-count → chat → post-count
- dev-login → `v2_jwt` cookie set (200); echo_demo chat with cookie → 200 (passes the 401 middleware) — **auth fix proven**
- SSE event names observed: `loop_start … llm_response … loop_end` (no `loop_completed`) — **event-name fix proven**
- **real_llm call → HTTP 200** (NOT 503); real Azure reply "Hello there, nice to meet you."
- **SSE contains `loop_end`** ✓
- **cost_ledger delta = 2** (≥2 ✓) — input+output split, written because the fresh backend wired the FIX-022 PricingLoader at startup (log: "pricing loader wired … llm_pricing.yml")
- **audit_log delta = 1** (≥1 ✓)
- Cost: ~$0.005 (two `Say hello in 5 words` calls, max_tokens guard)

Note: the long-running dev backend on :8000 (3-day uptime, started **before**
FIX-022) showed `cost_ledger=0` — confirming the cost-ledger write depends on
`_wire_pricing_loader()` at startup (`main.py:165`). The CI workflow always
starts a fresh backend, so it wires the loader; this was process staleness on
the dev box, not a workflow flaw.

CI: a real `workflow_dispatch` run still needs `AZURE_OPENAI_*` GitHub Secrets
(AD-CI-6). This fix makes the gate *correct + locally-proven*, not
*runnable-without-secrets*.

## Impact

CI-only (single workflow file). No backend/app code changed. Makes the canonical
real-LLM e2e gate actually pass once Azure secrets are provisioned. Does not by
itself enable the gate (secrets + uncommenting `schedule` still pending per
AD-CI-6). Corrects C-11 analysis claim "gate already built" → "gate built but had
latent auth drift, now fixed".
