/**
 * File: frontend/src/features/cost-dashboard/__fixtures__/tenantTop8.ts
 * Purpose: Top-8 tenant spend table fixture for /cost-dashboard TenantTopTable (Sprint 57.24 US-C2).
 * Category: Frontend / cost-dashboard / fixtures
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C2
 *
 * Description:
 *   Mirrors mockup reference/design-mockups/page-admin.jsx:263-270 inline
 *   array. Cross-tenant data is admin-scope; backend `/api/v1/admin/cost-summary`
 *   currently scoped to single tenant per Sprint 57.13 US-A2 RequireAuth.
 *   Cross-tenant aggregation API pending Phase 58+
 *   AD-Cost-Dashboard-Backend-Extensions.
 *
 *   `pct` denotes quota usage; > 100 indicates over-quota (danger tone); > 80
 *   warning tone; else success. `alert` flags rows that also surface an
 *   anomaly Badge in the tenant cell per mockup.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C2)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C2)
 */

export interface TenantTopRow {
  slug: string;
  plan: "Starter" | "Pro" | "Enterprise";
  tokens: string; // "4.2M" pre-formatted
  cost: number; // dollars
  pct: number; // quota usage 0-N (can exceed 100)
  alert?: boolean; // surfaces anomaly Badge
}

export const TENANT_TOP_8_FIXTURE: TenantTopRow[] = [
  { slug: "acme-prod", plan: "Pro", tokens: "4.2M", cost: 842, pct: 42 },
  { slug: "globex-eu", plan: "Pro", tokens: "3.1M", cost: 624, pct: 62 },
  { slug: "initech-jp", plan: "Enterprise", tokens: "2.8M", cost: 581, pct: 14 },
  { slug: "umbrella-us", plan: "Pro", tokens: "1.7M", cost: 342, pct: 34 },
  { slug: "wonka-apac", plan: "Starter", tokens: "0.9M", cost: 184, pct: 92 },
  { slug: "stark-prod", plan: "Pro", tokens: "0.7M", cost: 138, pct: 7 },
  { slug: "wayne-corp", plan: "Enterprise", tokens: "0.5M", cost: 96, pct: 5 },
  { slug: "tenant_3kp9", plan: "Starter", tokens: "2.4M", cost: 480, pct: 320, alert: true },
];
