/**
 * File: frontend/src/routes.config.ts
 * Purpose: Single-source page registry for all 11 V2 frontend pages.
 * Category: Frontend / routing / single-source registry
 * Scope: Phase 57 / Sprint 57.8 US-3 Day 1
 *
 * Description:
 *   Central registry consumed by:
 *     1. App.tsx — generates <Route> elements via .map(ROUTES.filter(active))
 *     2. Sidebar.tsx — generates nav links via .map(ROUTES) grouped by category
 *
 *   Adding/removing a frontend page = single edit here, not 2 places.
 *   Inactive entries (active: false) are shown grayed in sidebar with
 *   "Coming soon" tooltip but produce no <Route>.
 *
 *   13 entries cover the V2 frontend roadmap per 16-frontend-design.md:
 *     - Operations (3): Chat (V2) / Cost / SLA
 *     - Admin (8): Tenants / Tenant Settings / Audit Log / Feature Flags / Governance / Verification / Loop Debug / Memory
 *     - Settings (2): User Profile / MFA Settings
 *
 *   active=true (9): Chat V2 / Cost / SLA / Tenants / Tenant Settings / Governance (57.9) / Verification (57.11) / Loop Debug (57.12) / Memory (57.12)
 *   active=false (4): placeholders for future Phase 57.13+ ships
 *
 *   Auth routes (/auth/login, /auth/callback) are NOT in this registry —
 *   they use AuthShell (no sidebar) and are wired directly in App.tsx.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B5 — add nameKey (i18n key for sidebar label; common.nav.*)
 *   - 2026-05-10: Sprint 57.12 US-8 Day 4 — Loop Debug + Memory active=true + lazy imports (Agent Harness UI Suite)
 *   - 2026-05-10: Sprint 57.11 US-6 Day 4 — Verification active=true + lazy component import
 *   - 2026-05-09: Sprint 57.9 US-1 Day 1 — Governance active=true + lazy component import
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-3 — page registry)
 *
 * Related:
 *   - frontend/src/App.tsx (consumes ROUTES.filter(r => r.active && r.component))
 *   - frontend/src/components/Sidebar.tsx (consumes ROUTES grouped by category)
 *   - 16-frontend-design.md §V2 Ship Timeline
 */

import {
  Activity,
  BarChart3,
  Brain,
  Building2,
  CheckCheck,
  Lock,
  MessageSquare,
  ScrollText,
  Settings2,
  ShieldCheck,
  ToggleLeft,
  User,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType, LazyExoticComponent } from "react";
import { lazy } from "react";

export type RouteCategory = "operations" | "admin" | "settings";

export interface RouteEntry {
  /** English display name — dev/debug fallback when i18n is unavailable. */
  name: string;
  /** i18n key for the sidebar label (resolved against the `common` namespace, e.g. `nav.costDashboard`). */
  nameKey: string;
  /** React Router path */
  path: string;
  /** lucide-react icon component */
  icon: LucideIcon;
  /** Sidebar grouping */
  category: RouteCategory;
  /** false = grayed out + "Coming soon" tooltip; no <Route> generated */
  active: boolean;
  /** Lazy-loaded page component (only required when active=true) */
  component?: LazyExoticComponent<ComponentType<unknown>>;
}

export const ROUTES: RouteEntry[] = [
  // === Operations ===
  {
    name: "Chat (V2)",
    nameKey: "nav.chatV2",
    path: "/chat-v2",
    icon: MessageSquare,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/chat-v2")),
  },
  {
    name: "Cost Dashboard",
    nameKey: "nav.costDashboard",
    path: "/cost-dashboard",
    icon: BarChart3,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/cost-dashboard")),
  },
  {
    name: "SLA Dashboard",
    nameKey: "nav.slaDashboard",
    path: "/sla-dashboard",
    icon: Activity,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/sla-dashboard")),
  },
  // === Admin ===
  {
    name: "Tenants",
    nameKey: "nav.tenants",
    path: "/admin-tenants",
    icon: Building2,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/admin-tenants")),
  },
  {
    name: "Tenant Settings",
    nameKey: "nav.tenantSettings",
    path: "/tenant-settings",
    icon: Settings2,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/tenant-settings")),
  },
  {
    name: "Audit Log",
    nameKey: "nav.auditLog",
    path: "/audit-log",
    icon: ScrollText,
    category: "admin",
    active: false,
  },
  {
    name: "Feature Flags",
    nameKey: "nav.featureFlags",
    path: "/feature-flags",
    icon: ToggleLeft,
    category: "admin",
    active: false,
  },
  {
    name: "Governance",
    nameKey: "nav.governance",
    path: "/governance",
    icon: ShieldCheck,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/governance")),
  },
  {
    name: "Verification",
    nameKey: "nav.verification",
    path: "/verification",
    icon: CheckCheck,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/verification")),
  },
  {
    name: "Loop Debug",
    nameKey: "nav.loopDebug",
    path: "/loop-debug",
    icon: Workflow,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/loop-debug")),
  },
  {
    name: "Memory",
    nameKey: "nav.memory",
    path: "/memory",
    icon: Brain,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/memory")),
  },
  // === Settings ===
  {
    name: "User Profile",
    nameKey: "nav.userProfile",
    path: "/profile",
    icon: User,
    category: "settings",
    active: false,
  },
  {
    name: "MFA Settings",
    nameKey: "nav.mfaSettings",
    path: "/mfa",
    icon: Lock,
    category: "settings",
    active: false,
  },
];
