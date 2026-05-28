/**
 * File: frontend/src/features/tenant-settings/_fixtures.ts
 * Purpose: Mockup fixtures for tabs NOT yet wired to backend (post Sprint 57.50 migration).
 * Category: Frontend / tenant-settings / fixtures
 * Scope: Phase 57 / Sprint 57.44 Day 1 (initial verbatim port) → Sprint 57.50 Day 1 (Identity cleanup)
 *
 * Description:
 *   Sprint 57.44 initial: ported the entire mockup 6-tab fixture set from
 *   `page-admin.jsx:411-621` because backend TenantResponse only exposed 10
 *   baseline fields.
 *
 *   Sprint 57.46/47/48 backend extensions + Sprint 57.49/57.50 frontend migration
 *   wave removed 6 fixture sections (FEATURE_FLAGS / QUOTAS / RATE_LIMITS /
 *   HITL_POLICIES / MEMBERS / IDENTITY) — all real-data backed now.
 *
 *   Retained fixtures:
 *   - DANGER_OPS — UI-only actions (Suspend / Rotate / Tombstone / Delete);
 *     destructive endpoint integration is intentional Phase 58+ scope
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-28: Sprint 57.58 Track D — +LIVE_USAGE_FIXTURE (RateLimits live usage Card test/storybook data)
 *   - 2026-05-26: Sprint 57.50 — drop IDENTITY_FIXTURE (closes IdentityFixture-Cleanup); cleanup SEATS stale comment
 *   - 2026-05-26: Sprint 57.49 — drop 5 migrated sections (FF/Quotas/RateLimits/HITL/Members/General)
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — verbatim mockup port for 6-tab rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L606-610 (DANGER_OPS)
 *   - ./components/tabs/DangerZoneTab.tsx (DANGER_OPS consumer)
 */

export interface DangerOp {
  k: string;
  v: string;
  btn: string;
}

export const DANGER_OPS: DangerOp[] = [
  { k: "Suspend tenant", v: "Block all new sessions and tool calls. Existing sessions complete.", btn: "Suspend" },
  { k: "Rotate all API keys", v: "Invalidate every active key. Operators must re-issue.", btn: "Rotate" },
  { k: "Tombstone all PII", v: "GDPR Art. 17. Memory entries marked subject-erased; audit chain preserves hashes.", btn: "Tombstone" },
  { k: "Delete tenant", v: "Permanent. Cannot be undone. WORM audit retained 7 years per compliance.", btn: "Delete" },
];

/* === Sprint 57.58 Track D — RateLimits live usage fixture ===
 *
 * Mirrors backend RateLimitsUsageResponse shape ({items: [{resource, window,
 * limit, current, reset_at}]}). Spans the 3 color thresholds the Live usage
 * Card renders: green (<70%), yellow (70-90%), red (>90%). reset_at values are
 * UNIX epoch SECONDS; tests stub Date.now to assert the countdown rendering.
 */

export interface LiveUsageEntry {
  resource: string;
  window: number;
  limit: number;
  current: number;
  reset_at: number;
}

export const LIVE_USAGE_FIXTURE: LiveUsageEntry[] = [
  // green: 30 / 100 = 30%
  { resource: "api_requests", window: 60, limit: 100, current: 30, reset_at: 1_900_000_060 },
  // yellow: 16 / 20 = 80%
  { resource: "agent_runs", window: 60, limit: 20, current: 16, reset_at: 1_900_000_055 },
  // red: 95 / 100 = 95%
  { resource: "tool_calls", window: 60, limit: 100, current: 95, reset_at: 1_900_000_058 },
];
