/**
 * File: frontend/src/App.tsx
 * Purpose: Root router — generates routes from routes.config single-source registry + boots auth state.
 * Category: Frontend / app-root
 *
 * Description:
 *   Routes derived from `routes.config.ts` (.filter(active).map(<Route>));
 *   React.lazy + Suspense enable per-page code-splitting.
 *
 *   <AuthBootstrap> runs authStore.bootstrap() once on mount (GET /auth/me)
 *   so route gates (<RequireAuth>) and the shell have a resolved auth state.
 *   It renders children immediately — public routes (Home, /auth/*) don't
 *   wait; gated pages show their own spinner until status resolves.
 *
 *   Auth routes (/auth/*) NOT in registry — they use AuthShell (no sidebar).
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B9 — lazy-load /auth/login + /auth/callback (keep their ui/ component cost out of the main bundle)
 *   - 2026-05-10: Sprint 57.13 US-A1 — add <AuthBootstrap>; drop redundant legacy /verification route (registry covers it since 57.11)
 *   - 2026-05-09: Sprint 57.9 US-1 — drop legacy /governance/* route + import (single-source restored)
 *   - 2026-05-10: Sprint 57.8 US-3 — refactor to consume routes.config + lazy-load
 *   - 2026-05-09: Sprint 57.7 Day 2 — add /auth/login + /auth/callback routes (US-A2)
 *   - 2026-05-07: Sprint 57.4 Day 4 — add /admin-tenants route + Home Link (US-5)
 *   - 2026-05-07: Sprint 57.3 Day 4 — add /tenant-settings route + Home Link (US-5)
 *   - 2026-05-06: Sprint 57.1 Day 3 — add /cost-dashboard + /sla-dashboard routes (US-4)
 *   - 2026-04-2x: Sprint 49.1 — initial placeholder router with /chat-v2 + /governance + /verification
 */

import { Suspense, lazy, useEffect, type ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { useAuthStore } from "./features/auth/store/authStore";
import { ROUTES } from "./routes.config";

const LoginPage = lazy(() => import("./pages/auth/login"));
const CallbackPage = lazy(() => import("./pages/auth/callback"));

/**
 * Runs authStore.bootstrap() once on app mount, then renders children. Public
 * routes render during bootstrap; gated pages spinner via <RequireAuth>.
 */
function AuthBootstrap({ children }: { children: ReactNode }) {
  useEffect(() => {
    void useAuthStore.getState().bootstrap();
  }, []);
  return <>{children}</>;
}

function Home() {
  // Simple landing — list active pages dynamically from the registry.
  const activeRoutes = ROUTES.filter((r) => r.active);
  return (
    <div className="p-8 font-sans">
      <h1 className="mb-4 text-2xl font-semibold">IPA Platform V2</h1>
      <p className="mb-2">Active pages (consume routes.config single-source):</p>
      <ul className="list-disc pl-6">
        {activeRoutes.map((r) => (
          <li key={r.path}>
            <Link to={r.path} className="text-blue-600 hover:underline">
              {r.path}
            </Link>{" "}
            — {r.name}
          </li>
        ))}
      </ul>
      <p className="mt-4">
        Auth: <Link to="/auth/login" className="text-blue-600 hover:underline">/auth/login</Link>
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        Backend health: <code>GET /api/v1/health</code> (proxied to localhost:8000)
      </p>
    </div>
  );
}

function PageLoading() {
  return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
}

export default function App() {
  return (
    <AuthBootstrap>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/" element={<Home />} />

          {/* Auth routes — outside registry (use AuthShell, no sidebar) */}
          <Route path="/auth/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<CallbackPage />} />

          {/* Active routes generated from routes.config single-source */}
          {ROUTES.filter((r) => r.active && r.component).map((r) => {
            const Component = r.component!;
            return <Route key={r.path} path={`${r.path}/*`} element={<Component />} />;
          })}

          {/* Catch-all → Home (revisit Phase 58.x with a NotFoundPage) */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AuthBootstrap>
  );
}
