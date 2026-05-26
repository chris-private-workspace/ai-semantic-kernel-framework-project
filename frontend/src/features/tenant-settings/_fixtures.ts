/**
 * File: frontend/src/features/tenant-settings/_fixtures.ts
 * Purpose: Verbatim port of mockup tenant-settings 6-tab data arrays (Sprint 57.44 rebuild).
 * Category: Frontend / tenant-settings / fixtures
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A fixture-first)
 *
 * Description:
 *   Backend TenantSettingsResponse only exposes `id / code / display_name / state
 *   / plan / provisioning_progress / onboarding_progress / meta_data / created_at
 *   / updated_at`; the mockup 6-tab IA references many more fields (region /
 *   locale / retention / feature flags / quotas / rate limits / HITL policies /
 *   members / SSO config / etc.) that are NOT yet wired to backend. Per D-DAY0-4
 *   Option A decision, ship the full 6-tab visual layout with fixture data +
 *   BackendGapBanner declaring Phase 58+ gap (AP-2 honesty).
 *
 *   Only `display_name` is live-wired to backend via useTenantSettingsSave;
 *   everything else in this file is verbatim port from `page-admin.jsx:411-621`.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — verbatim mockup port for 6-tab rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L481-491 / L512-516 / L533-535 / L548-551 / L576-583 / L606-610
 *   - components/tabs/* (consumers)
 */

export interface FeatureFlag {
  k: string;
  desc: string;
  def: string;
  on: boolean | number;
  ctl?: "num";
}

export interface Quota {
  k: string;
  used: number;
  max: number;
  unit: string;
  pct: number;
}

export interface RateLimit {
  label: string;
  value: string;
}

export interface HITLPolicy {
  risk: "critical" | "high" | "medium" | "low";
  policy: "always_ask" | "ask_once" | "auto";
  sla: string;
  approvers: string;
  off: string[];
}

export interface Member {
  n: string;
  e: string;
  r: "admin" | "operator" | "compliance";
  a: string;
  c: number;
}

export interface DangerOp {
  k: string;
  v: string;
  btn: string;
}

export const FEATURE_FLAGS: FeatureFlag[] = [
  { k: "subagent.fork.enabled", desc: "Allow concurrent fork mode", def: "on", on: true },
  { k: "subagent.max_depth", desc: "Maximum subagent recursion depth", def: "5", on: 5, ctl: "num" },
  { k: "memory.long_term_write", desc: "Allow writes to user/tenant memory", def: "on", on: true },
  { k: "tool.sandbox_full", desc: "Permit FULL_SANDBOX tool runs", def: "off", on: false },
  { k: "hitl.escalate_to_teams", desc: "Mirror HITL events to MS Teams", def: "on", on: true },
  { k: "verification.required", desc: "Block tool output without verification", def: "on", on: true },
  { k: "loop.max_iterations", desc: "Hard ceiling on loop turns", def: "30", on: 30, ctl: "num" },
  { k: "streaming.thinking", desc: "Stream thinking blocks to client", def: "on", on: true },
];

export const QUOTAS: Quota[] = [
  { k: "Tokens / month", used: 4.2, max: 10, unit: "M", pct: 42 },
  { k: "Runs / day", used: 14820, max: 50000, unit: "", pct: 30 },
  { k: "Subagents concurrent", used: 3, max: 20, unit: "", pct: 15 },
  { k: "Memory entries", used: 18200, max: 100000, unit: "", pct: 18 },
  { k: "Audit storage", used: 240, max: 1024, unit: " MB", pct: 23 },
];

export const RATE_LIMITS: RateLimit[] = [
  { label: "API requests", value: "100 / min" },
  { label: "Tool calls", value: "1,000 / min" },
  { label: "SSE connections", value: "50 concurrent" },
];

export const HITL_POLICIES: HITLPolicy[] = [
  { risk: "critical", policy: "always_ask", sla: "5m", approvers: "@platform-l2 + @on-call-mgr", off: ["Teams", "Email"] },
  { risk: "high", policy: "always_ask", sla: "15m", approvers: "@platform-l2", off: ["Teams"] },
  { risk: "medium", policy: "ask_once", sla: "60m", approvers: "@platform-l1", off: [] },
  { risk: "low", policy: "auto", sla: "—", approvers: "—", off: [] },
];

export const MEMBERS: Member[] = [
  { n: "Jamie Liu", e: "jamie@acme.com", r: "operator", a: "now", c: 250 },
  { n: "Priya Mishra", e: "priya@acme.com", r: "compliance", a: "8m ago", c: 350 },
  { n: "Sam Wong", e: "sam@acme.com", r: "operator", a: "2h ago", c: 210 },
  { n: "Yui Kato", e: "yui@acme.com", r: "operator", a: "yesterday", c: 30 },
  { n: "Dan O'Brien", e: "dan@acme.com", r: "admin", a: "3 days ago", c: 290 },
  { n: "Rae Tan", e: "rae@acme.com", r: "operator", a: "1 week ago", c: 340 },
  { n: "Ben Park", e: "ben@acme.com", r: "operator", a: "2 weeks ago", c: 80 },
  { n: "Mira Habib", e: "mira@acme.com", r: "admin", a: "1 month ago", c: 10 },
];

export const DANGER_OPS: DangerOp[] = [
  { k: "Suspend tenant", v: "Block all new sessions and tool calls. Existing sessions complete.", btn: "Suspend" },
  { k: "Rotate all API keys", v: "Invalidate every active key. Operators must re-issue.", btn: "Rotate" },
  { k: "Tombstone all PII", v: "GDPR Art. 17. Memory entries marked subject-erased; audit chain preserves hashes.", btn: "Tombstone" },
  { k: "Delete tenant", v: "Permanent. Cannot be undone. WORM audit retained 7 years per compliance.", btn: "Delete" },
];

export const GENERAL_FIXTURE = {
  region: "ap-east-1",
  locale: "zh-TW",
  retentionDays: 365,
};

export const IDENTITY_FIXTURE = {
  provider: "SAML 2.0 · WorkOS",
  scim: "enabled",
  allowedDomains: "acme.com, acme.io",
  mfa: "required",
};

export const SEATS_FIXTURE = 8;
