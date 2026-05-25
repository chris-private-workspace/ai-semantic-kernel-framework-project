/**
 * File: frontend/src/features/admin-tenants/_fixtures.ts
 * Purpose: Verbatim TENANTS + stats fixtures ported from mockup `page-admin.jsx` L322-355.
 * Category: Frontend / admin-tenants / fixtures
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild — Option A fixture-first)
 *
 * Description:
 *   Backend `TenantListItem` schema (backend/src/api/v1/admin/tenants.py) lacks
 *   5 of 9 mockup columns (seats / region / agents / runs24 / status). Per
 *   D-DAY0-6 Option A LOCKED IN, the Day-1 rebuild uses these fixtures verbatim
 *   and marks the table with AP-2 BackendGapBanner; backend wire deferred Phase 58+
 *   (see AD-AdminTenants-Backend-Schema-Extension).
 *
 * Key Components:
 *   - TENANTS_FIXTURE: 8-tenant verbatim port (L323-332)
 *   - STATS_FIXTURE: 4-stat verbatim port (L350-355)
 *   - TABLE_SUBTITLE: card sub line (L357)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L322-355
 *   - docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-43-plan.md
 */

export interface TenantFixture {
  id: string;
  name: string;
  plan: "Starter" | "Pro" | "Enterprise";
  seats: number;
  region: string;
  agents: number;
  runs24: number;
  status: "active" | "quota-warn" | "anomaly";
  created: string;
}

export const TENANTS_FIXTURE: TenantFixture[] = [
  { id: "tenant_01h9a2", name: "acme-prod", plan: "Pro", seats: 8, region: "ap-east-1", agents: 12, runs24: 14820, status: "active", created: "2024-11-04" },
  { id: "tenant_01h7zz", name: "globex-eu", plan: "Pro", seats: 12, region: "eu-west-1", agents: 18, runs24: 9820, status: "active", created: "2024-09-12" },
  { id: "tenant_01h6kp", name: "initech-jp", plan: "Enterprise", seats: 42, region: "ap-northeast-1", agents: 28, runs24: 18420, status: "active", created: "2023-06-22" },
  { id: "tenant_01h22a", name: "umbrella-us", plan: "Pro", seats: 6, region: "us-east-1", agents: 7, runs24: 3820, status: "active", created: "2025-01-30" },
  { id: "tenant_01j33b", name: "wonka-apac", plan: "Starter", seats: 3, region: "ap-southeast-1", agents: 4, runs24: 220, status: "quota-warn", created: "2025-02-14" },
  { id: "tenant_01k77c", name: "stark-prod", plan: "Pro", seats: 9, region: "us-west-2", agents: 11, runs24: 1820, status: "active", created: "2024-04-08" },
  { id: "tenant_01n44d", name: "wayne-corp", plan: "Enterprise", seats: 22, region: "us-east-1", agents: 19, runs24: 880, status: "active", created: "2023-11-19" },
  { id: "tenant_3kp9",   name: "tenant_3kp9", plan: "Starter", seats: 2, region: "ap-east-1", agents: 1, runs24: 12200, status: "anomaly", created: "2026-05-01" },
];

export interface StatFixture {
  label: string;
  value: string;
  delta: string;
  deltaDir: "up" | "down";
}

export const STATS_FIXTURE: StatFixture[] = [
  { label: "Active tenants", value: "48", delta: "+3", deltaDir: "up" },
  { label: "Total seats", value: "284", delta: "+18", deltaDir: "up" },
  { label: "Agents deployed", value: "612", delta: "+24", deltaDir: "up" },
  { label: "Anomalies", value: "1", delta: "+1", deltaDir: "down" },
];

export const TABLE_SUBTITLE = "48 active · 3 anomalies in last 24h";
