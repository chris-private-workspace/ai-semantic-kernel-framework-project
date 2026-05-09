/**
 * File: frontend/src/App.tsx
 * Purpose: Root router — generates routes from routes.config single-source registry.
 * Category: Frontend / app-root
 *
 * Description:
 *   Sprint 57.8 US-3 refactor: routes derived from `routes.config.ts`
 *   (.filter(active).map(<Route>)) instead of inline hand-listed routes.
 *   React.lazy + Suspense enable per-page code-splitting.
 *
 *   Auth routes (/auth/*) NOT in registry — they use AuthShell (renamed
 *   from AppShell.tsx per Day 0 Decision B1; no sidebar for unauthed UX).
 *
 *   Legacy placeholder routes (/governance + /verification) preserved
 *   intentionally pending Phase 57.9 + 57.10 real ship sprints. Per Sprint
 *   57.5 reality check, these are placeholder pages that render minimal
 *   stub UI; removing them would 404 any direct visitors during transition.
 *   When 57.9 / 57.10 ship → set active=true in routes.config + delete from
 *   here = single-source restored.
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-1 — drop legacy /governance/* route + import (single-source restored)
 *   - 2026-05-10: Sprint 57.8 US-3 — refactor to consume routes.config + lazy-load
 *   - 2026-05-09: Sprint 57.7 Day 2 — add /auth/login + /auth/callback routes (US-A2)
 *   - 2026-05-07: Sprint 57.4 Day 4 — add /admin-tenants route + Home Link (US-5)
 *   - 2026-05-07: Sprint 57.3 Day 4 — add /tenant-settings route + Home Link (US-5)
 *   - 2026-05-06: Sprint 57.1 Day 3 — add /cost-dashboard + /sla-dashboard routes (US-4)
 *   - 2026-04-2x: Sprint 49.1 — initial placeholder router with /chat-v2 + /governance + /verification
 */

import { Suspense } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import CallbackPage from "./pages/auth/callback";
import LoginPage from "./pages/auth/login";
import VerificationPage from "./pages/verification";
import { ROUTES } from "./routes.config";

function Home() {
  // Sprint 57.8: simple landing — list active pages dynamically from registry
  // (was hand-curated <ul> per phase). Removed inline style; minimal padding
  // OK at root since AppShellV2 isn't applicable (Home is pre-redirect landing).
  const activeRoutes = ROUTES.filter((r) => r.active);
  return (
    <div className="p-8 font-sans">
      <h1 className="mb-4 text-2xl font-semibold">IPA Platform V2</h1>
      <p className="mb-4">
        <strong>Status:</strong> Phase 57+ Sprint 57.8 — AppShell V2 + chat-v2 frontend real ship.
      </p>
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
        Auth: <Link to="/auth/login" className="text-blue-600 hover:underline">/auth/login</Link> (Sprint 57.7 OIDC PKCE)
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
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/" element={<Home />} />

        {/* Auth routes — outside registry per Day 0 Decision B1 (use AuthShell, no sidebar) */}
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<CallbackPage />} />

        {/* Active routes generated from routes.config single-source */}
        {ROUTES.filter((r) => r.active && r.component).map((r) => {
          const Component = r.component!;
          return <Route key={r.path} path={`${r.path}/*`} element={<Component />} />;
        })}

        {/* Legacy placeholder routes — preserved until Phase 57.10 real ship sprint
            promotes verification to registry active=true (then delete from here).
            governance promoted Sprint 57.9 (single-source restored). */}
        <Route path="/verification/*" element={<VerificationPage />} />

        {/* Catch-all → Home (vs explicit 404 page; revisit Phase 58.x with NotFoundPage) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
