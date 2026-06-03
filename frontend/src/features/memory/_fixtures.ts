/**
 * File: frontend/src/features/memory/_fixtures.ts
 * Purpose: Memory page op-timeline fixtures — TIME_TRAVEL_MARKS / MEMORY_OPS_TIMELINE + hand-ported RECENT_MEMORY_OPS.
 * Category: Frontend / memory / fixtures
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of the op-timeline portion of
 *   `reference/design-mockups/page-governance.jsx` + hand-ported
 *   `RECENT_MEMORY_OPS` from inline mockup table (L561-566).
 *
 *   Sprint 57.73 Track C: the matrix + header fixtures (SCOPES / TIME_SCALES /
 *   MEMORY_ENTRIES / TOTAL_ENTRIES) were removed — MemoryMatrix + MemoryPageHeader
 *   now consume the real GET /api/v1/memory/matrix aggregate. The op-timeline
 *   fixtures below remain because memory writes emit zero audit rows (no backend
 *   producer for the per-op history / version log — deferred, AD-Memory-OpsHistory-Backend).
 *   They feed TimeTravelScrubber + RecentMemoryOpsCard, both of which carry an
 *   AP-2 BackendGapBanner.
 *
 * Key Components:
 *   - TimeTravelMark: 6 time markers along 24h scrubber
 *   - MemoryOpTimelinePoint: 12 op markers behind scrubber
 *   - RecentMemoryOp: 5-row hand-ported recent-ops table
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — remove orphaned matrix/header fixtures (matrix wired to real /matrix)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L561-566 (RECENT_MEMORY_OPS hand-port)
 *   - ./components/TimeTravelScrubber.tsx ./components/RecentMemoryOpsCard.tsx
 */

export type MemoryScopeId = "system" | "tenant" | "role" | "user" | "session";

export interface TimeTravelMark {
  t: number; // minutes ago; 0 = now, negative = past
  label: string;
  at: string;
}

export interface MemoryOpTimelinePoint {
  t: number; // minutes ago
  op: "WRITE" | "READ" | "EXPIRE";
  scope: MemoryScopeId;
  k: string;
}

export interface RecentMemoryOp {
  op: "WRITE" | "READ" | "EXPIRE";
  scope: string;
  k: string;
  v: string;
  by: string;
  at: string;
}

export const TIME_TRAVEL_MARKS: TimeTravelMark[] = [
  { t: 0, label: "now", at: "10:42:28" },
  { t: -5, label: "5m ago", at: "10:37:00" },
  { t: -30, label: "30m ago", at: "10:12:00" },
  { t: -120, label: "2h ago", at: "08:42:00" },
  { t: -360, label: "6h ago", at: "04:42:00" },
  { t: -1440, label: "1d ago", at: "yesterday" },
];

export const MEMORY_OPS_TIMELINE: MemoryOpTimelinePoint[] = [
  { t: 0, op: "WRITE", scope: "session", k: "evidence" },
  { t: -1, op: "WRITE", scope: "session", k: "root_cause" },
  { t: -2, op: "READ", scope: "tenant", k: "hitl.risk_high" },
  { t: -4, op: "READ", scope: "user", k: "preferences.rca_format" },
  { t: -7, op: "WRITE", scope: "tenant", k: "anomaly.token_spike" },
  { t: -8, op: "READ", scope: "system", k: "policy.tripwires" },
  { t: -11, op: "EXPIRE", scope: "session", k: "scratchpad.q4_audit" },
  { t: -15, op: "WRITE", scope: "user", k: "shortcuts" },
  { t: -42, op: "READ", scope: "tenant", k: "plan" },
  { t: -120, op: "WRITE", scope: "tenant", k: "usage.tokens" },
  { t: -240, op: "READ", scope: "user", k: "tz" },
  { t: -380, op: "WRITE", scope: "session", k: "severity" },
];

export const RECENT_MEMORY_OPS: RecentMemoryOp[] = [
  {
    op: "WRITE",
    scope: "session.sess_4tk2p",
    k: "root_cause",
    v: "pgbouncer pool too small",
    by: "incident-responder",
    at: "10:42:27",
  },
  {
    op: "READ",
    scope: "user.jamie",
    k: "preferences.rca_format",
    v: "5-whys + timeline",
    by: "incident-responder",
    at: "10:42:24",
  },
  {
    op: "READ",
    scope: "tenant.acme-prod",
    k: "hitl.risk_high",
    v: "always_ask",
    by: "incident-responder",
    at: "10:42:26",
  },
  {
    op: "WRITE",
    scope: "tenant.acme-prod",
    k: "anomaly.token_spike",
    v: "tenant_3kp9 +320%",
    by: "compliance-auditor",
    at: "10:35:11",
  },
  {
    op: "EXPIRE",
    scope: "session.sess_91kxu",
    k: "scratchpad.q4_audit",
    v: "—",
    by: "system",
    at: "10:31:00",
  },
];
