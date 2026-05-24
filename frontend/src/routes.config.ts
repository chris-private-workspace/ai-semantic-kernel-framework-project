/**
 * File: frontend/src/routes.config.ts
 * Purpose: Single-source page registry for all V2 frontend routes (active + PROP/DRAFT scaffolding).
 * Category: Frontend / routing / single-source registry
 * Scope: Phase 57 / Sprint 57.18 US-C1 (mockup integration foundation; 6-category refactor)
 *
 * Description:
 *   Central registry consumed by:
 *     1. App.tsx — generates <Route> elements via .map(ROUTES.filter(active && component))
 *     2. Sidebar.tsx — generates nav links via .map(ROUTES) grouped by CATEGORY_ORDER
 *     3. ComingSoonPlaceholder.tsx — looks up current route via useLocation().pathname
 *
 *   31 entries (Sprint 57.18) cover the operator portal full nav vocabulary per
 *   design/operator-portal/shell.jsx ROUTES (mirror Sprint 57.18 mockup integration):
 *     - operations (10): chat-v2 + loop-debug + memory + 7 NEW PROP stubs
 *     - business (1): 1 NEW PROP stub (incidents)
 *     - governance (5): governance + verification + audit-log + 2 NEW PROP stubs
 *     - observability (5): cost-dashboard + sla-dashboard + 3 NEW PROP stubs
 *     - resources (3): feature-flags + 2 NEW PROP stubs
 *     - admin (7): admin-tenants + tenant-settings + 3 NEW PROP stubs + profile + mfa
 *
 *   Three-state convention (per design/operator-portal/AGENTS.md §5):
 *     - active=true (existing only): full implementation shipped
 *     - active=true + proposed=true (NEW Sprint 57.18 PROP): V2 backend ABC exists,
 *       frontend stub renders ComingSoonPlaceholder until Sprint 57.19+ real port
 *     - active=false + designed=true (DRAFT): V2 routes.config marks future entry;
 *       sidebar shows DRAFT badge; no <Route> generated
 *
 *   Inactive entries without designed=true → grayed link + "Coming soon" tooltip.
 *
 *   Auth routes (/auth/login, /auth/callback) are NOT in this registry — they
 *   use AuthShell (no sidebar) and are wired directly in App.tsx.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-16
 *
 * Modification History:
 *   - 2026-05-16: Sprint 57.18 — +18 PROP stubs + RouteCategory 3→6 + 13 re-categorized + proposed/designed flags (closes AD-Mockup-Integration-Foundation Phase 1)
 *   - 2026-05-10: Sprint 57.13 US-B5 — add nameKey (i18n key for sidebar label; common.nav.*)
 *   - 2026-05-10: Sprint 57.12 US-8 Day 4 — Loop Debug + Memory active=true + lazy imports (Agent Harness UI Suite)
 *   - 2026-05-10: Sprint 57.11 US-6 Day 4 — Verification active=true + lazy component import
 *   - 2026-05-09: Sprint 57.9 US-1 Day 1 — Governance active=true + lazy component import
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-3 — page registry)
 *
 * Related:
 *   - frontend/src/App.tsx (consumes ROUTES.filter(r => r.active && r.component))
 *   - frontend/src/components/Sidebar.tsx (consumes ROUTES + CATEGORY_ORDER)
 *   - frontend/src/components/ComingSoonPlaceholder.tsx (universal PROP/DRAFT stub)
 *   - design/operator-portal/shell.jsx (mockup ROUTES authoritative source)
 *   - design/operator-portal/INTEGRATION-LOG.md (port progress tracking)
 *   - 16-frontend-design.md §V2 Ship Timeline
 */

import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  BarChart3,
  Brain,
  Building2,
  CheckCheck,
  Code2,
  Cpu,
  Database,
  DollarSign,
  EyeOff,
  GitBranch,
  GitFork,
  LayoutDashboard,
  Lock,
  MessageSquare,
  Minimize2,
  Radio,
  ScrollText,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  ToggleLeft,
  User,
  UserPlus,
  Workflow,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType, LazyExoticComponent } from "react";
import { lazy } from "react";

export type RouteCategory =
  | "operations"     // daily operator workflow — chat / agent / loop / memory / state
  | "business"       // IPA 5 domains — incidents (patrol/correlation/RCA/audit)
  | "governance"     // HITL + audit + verification + redaction + safety guardrails
  | "observability"  // Cat 12 dashboards — cost / SLA / cache / SSE / devui
  | "resources"      // platform resources — models / tools / flags
  | "admin";         // tenant + identity + pricing — tenants / settings / onboarding / pricing / rbac / profile / mfa

export const CATEGORY_ORDER: RouteCategory[] = [
  "operations",
  "business",
  "governance",
  "observability",
  "resources",
  "admin",
];

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
  /** false = no <Route> generated; sidebar shows grayed link */
  active: boolean;
  /** V2 backend ABC exists, frontend stub renders ComingSoonPlaceholder (sidebar PROP badge) */
  proposed?: boolean;
  /** V2 routes.config marks future entry (sidebar DRAFT badge; Sprint 57.19+ to promote) */
  designed?: boolean;
  /** Lazy-loaded page component (required when active=true) */
  component?: LazyExoticComponent<ComponentType<unknown>>;
}

export const ROUTES: RouteEntry[] = [
  // === Operations (10) ===
  {
    name: "Overview",
    nameKey: "nav.overview",
    path: "/overview",
    icon: LayoutDashboard,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/overview")),
  },
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
    name: "Orchestrator",
    nameKey: "nav.orchestrator",
    path: "/orchestrator",
    icon: Sparkles,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/orchestrator")),
  },
  {
    name: "Subagents",
    nameKey: "nav.subagents",
    path: "/subagents",
    icon: GitFork,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/subagents")),
  },
  {
    name: "Loop Debug",
    nameKey: "nav.loopDebug",
    path: "/loop-debug",
    icon: Workflow,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/loop-debug")),
  },
  {
    name: "Memory",
    nameKey: "nav.memory",
    path: "/memory",
    icon: Brain,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/memory")),
  },
  {
    name: "State Inspector",
    nameKey: "nav.stateInspector",
    path: "/state-inspector",
    icon: Database,
    category: "operations",
    active: true,
    component: lazy(() => import("./pages/state-inspector")),
  },
  {
    name: "Compaction",
    nameKey: "nav.compaction",
    path: "/compaction",
    icon: Minimize2,
    category: "operations",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/compaction")),
  },
  {
    name: "JIT Retrieval",
    nameKey: "nav.jitRetrieval",
    path: "/jit-retrieval",
    icon: Search,
    category: "operations",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/jit-retrieval")),
  },
  {
    name: "Subagent Tree",
    nameKey: "nav.subagentTree",
    path: "/subagent-tree",
    icon: GitBranch,
    category: "operations",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/subagent-tree")),
  },
  // === Business (1) ===
  {
    name: "Incidents",
    nameKey: "nav.incidents",
    path: "/incidents",
    icon: AlertTriangle,
    category: "business",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/incidents")),
  },
  // === Governance (5) ===
  {
    name: "Governance",
    nameKey: "nav.governance",
    path: "/governance",
    icon: ShieldCheck,
    category: "governance",
    active: true,
    component: lazy(() => import("./pages/governance")),
  },
  {
    name: "Verification",
    nameKey: "nav.verification",
    path: "/verification",
    icon: CheckCheck,
    category: "governance",
    active: true,
    component: lazy(() => import("./pages/verification")),
  },
  {
    name: "Audit Log",
    nameKey: "nav.auditLog",
    path: "/audit-log",
    icon: ScrollText,
    category: "governance",
    active: false,
    designed: true,
  },
  {
    name: "Redaction",
    nameKey: "nav.redaction",
    path: "/redaction",
    icon: EyeOff,
    category: "governance",
    active: true,
    component: lazy(() => import("./pages/redaction")),
  },
  {
    name: "Error Policy",
    nameKey: "nav.errorPolicy",
    path: "/error-policy",
    icon: AlertOctagon,
    category: "governance",
    active: true,
    component: lazy(() => import("./pages/error-policy")),
  },
  // === Observability (5) ===
  {
    name: "Cost Dashboard",
    nameKey: "nav.costDashboard",
    path: "/cost-dashboard",
    icon: BarChart3,
    category: "observability",
    active: true,
    component: lazy(() => import("./pages/cost-dashboard")),
  },
  {
    name: "SLA Dashboard",
    nameKey: "nav.slaDashboard",
    path: "/sla-dashboard",
    icon: Activity,
    category: "observability",
    active: true,
    component: lazy(() => import("./pages/sla-dashboard")),
  },
  {
    name: "Cache Manager",
    nameKey: "nav.cacheManager",
    path: "/cache-manager",
    icon: Database,
    category: "observability",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/cache-manager")),
  },
  {
    name: "SSE Inspector",
    nameKey: "nav.sseInspector",
    path: "/sse",
    icon: Radio,
    category: "observability",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/sse")),
  },
  {
    name: "DevUI",
    nameKey: "nav.devui",
    path: "/devui",
    icon: Code2,
    category: "observability",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/devui")),
  },
  // === Resources (3) ===
  {
    name: "Feature Flags",
    nameKey: "nav.featureFlags",
    path: "/feature-flags",
    icon: ToggleLeft,
    category: "resources",
    active: false,
    designed: true,
  },
  {
    name: "Models",
    nameKey: "nav.models",
    path: "/models",
    icon: Cpu,
    category: "resources",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/models")),
  },
  {
    name: "Tools",
    nameKey: "nav.tools",
    path: "/tools",
    icon: Wrench,
    category: "resources",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/tools")),
  },
  // === Admin (7) ===
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
    name: "Tenant Onboarding",
    nameKey: "nav.tenantOnboarding",
    path: "/admin/tenant-onboarding",
    icon: UserPlus,
    category: "admin",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/tenant-onboarding")),
  },
  {
    name: "Pricing",
    nameKey: "nav.pricing",
    path: "/admin/pricing",
    icon: DollarSign,
    category: "admin",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/pricing")),
  },
  {
    name: "RBAC",
    nameKey: "nav.rbac",
    path: "/rbac",
    icon: ShieldCheck,
    category: "admin",
    active: true,
    proposed: true,
    component: lazy(() => import("./pages/rbac")),
  },
  {
    name: "User Profile",
    nameKey: "nav.userProfile",
    path: "/profile",
    icon: User,
    category: "admin",
    active: false,
    designed: true,
  },
  {
    name: "MFA Settings",
    nameKey: "nav.mfaSettings",
    path: "/mfa",
    icon: Lock,
    category: "admin",
    active: false,
    designed: true,
  },
];
