/**
 * File: frontend/src/features/auth/components/RequireAuth.tsx
 * Purpose: Route gate — render children only when authStore.status === "authenticated".
 * Category: Frontend / auth / components
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Description:
 *   Wraps a page's content. Three states driven by authStore:
 *     - "unknown"       → loading spinner (App.tsx is still running bootstrap;
 *                          must NOT redirect yet or the user flashes /auth/login)
 *     - "anonymous"     → stash the attempted URL + <Navigate to="/auth/login">
 *     - "authenticated" → render children
 *
 *   Replaces the per-page `if (!isAuthenticated()) { setPostLoginRedirect(...);
 *   return <Navigate.../> }` boilerplate that 9 pages copy-pasted (Sprint
 *   57.13 US-A1) — one place to evolve the gate (e.g. role checks later).
 *
 * Created: 2026-05-10 (Sprint 57.13 US-A1)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Initial creation (Sprint 57.13 US-A1)
 *
 * Related:
 *   - frontend/src/features/auth/store/authStore.ts (status source)
 *   - frontend/src/features/auth/services/authService.ts (setPostLoginRedirect)
 *   - frontend/src/App.tsx (<AuthBootstrap> runs bootstrap before any gate)
 */

import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { setPostLoginRedirect } from "../services/authService";
import { useAuthStore } from "../store/authStore";

export function RequireAuth({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);
  const location = useLocation();

  if (status === "unknown") {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }
  if (status === "anonymous") {
    const target = `${location.pathname}${location.search}`;
    // Stash for the dev-login + fallback path; also pass via query so the
    // login page forwards it to the backend (→ /auth/callback?next=...).
    setPostLoginRedirect(target);
    return <Navigate to={`/auth/login?redirect_to=${encodeURIComponent(target)}`} replace />;
  }
  return <>{children}</>;
}
