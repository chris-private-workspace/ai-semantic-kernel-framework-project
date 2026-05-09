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
 *   11 entries cover the V2 frontend roadmap per 16-frontend-design.md:
 *     - Operations (3): Chat (V2) / Cost / SLA
 *     - Admin (6): Tenants / Tenant Settings / Audit Log / Feature Flags / Governance / Verification
 *     - Settings (2): User Profile / MFA Settings
 *
 *   active=true (7): Chat V2 / Cost / SLA / Tenants / Tenant Settings / Governance (57.9) / Verification (57.11)
 *   active=false (4): placeholders for future Phase 57.12+ ships
 *
 *   Auth routes (/auth/login, /auth/callback) are NOT in this registry —
 *   they use AuthShell (no sidebar) and are wired directly in App.tsx.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-09
 *
 * Modification History:
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
  Building2,
  CheckCheck,
  Lock,
  MessageSquare,
  ScrollText,
  Settings2,
  ShieldCheck,
  ToggleLeft,
  User,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType, LazyExoticComponent } from "react";
import { lazy } from "react";

export type RouteCategory = "operations" | "admin" | "settings";

export interface RouteEntry {
  /** Display name in sidebar */
  name: string;
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
    path: "/chat-v2",
    icon: MessageSquare,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/chat-v2")),
  },
  {
    name: "Cost Dashboard",
    path: "/cost-dashboard",
    icon: BarChart3,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/cost-dashboard")),
  },
  {
    name: "SLA Dashboard",
    path: "/sla-dashboard",
    icon: Activity,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/sla-dashboard")),
  },
  // === Admin ===
  {
    name: "Tenants",
    path: "/admin-tenants",
    icon: Building2,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/admin-tenants")),
  },
  {
    name: "Tenant Settings",
    path: "/tenant-settings",
    icon: Settings2,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/tenant-settings")),
  },
  {
    name: "Audit Log",
    path: "/audit-log",
    icon: ScrollText,
    category: "admin",
    active: false,
  },
  {
    name: "Feature Flags",
    path: "/feature-flags",
    icon: ToggleLeft,
    category: "admin",
    active: false,
  },
  {
    name: "Governance",
    path: "/governance",
    icon: ShieldCheck,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/governance")),
  },
  {
    name: "Verification",
    path: "/verification",
    icon: CheckCheck,
    category: "admin",
    active: true,
    component: lazy(() => import("./pages/verification")),
  },
  // === Settings ===
  {
    name: "User Profile",
    path: "/profile",
    icon: User,
    category: "settings",
    active: false,
  },
  {
    name: "MFA Settings",
    path: "/mfa",
    icon: Lock,
    category: "settings",
    active: false,
  },
];
