/**
 * File: frontend/src/App.tsx
 * Purpose: Root router + Home nav. Routes extended each phase.
 * Category: Frontend / app-root
 *
 * Modification History:
 *   - 2026-05-07: Sprint 57.4 Day 4 — add /admin-tenants route + Home Link (US-5)
 *   - 2026-05-07: Sprint 57.3 Day 4 — add /tenant-settings route + Home Link (US-5)
 *   - 2026-05-06: Sprint 57.1 Day 3 — add /cost-dashboard + /sla-dashboard routes (US-4)
 *   - 2026-04-2x: Sprint 49.1 — initial placeholder router with /chat-v2 + /governance + /verification
 */

import { Link, Route, Routes } from "react-router-dom";
import AdminTenantsPage from "./pages/admin-tenants";
import ChatV2Page from "./pages/chat-v2";
import CostDashboardPage from "./pages/cost-dashboard";
import GovernancePage from "./pages/governance";
import SLADashboardPage from "./pages/sla-dashboard";
import TenantSettingsPage from "./pages/tenant-settings";
import VerificationPage from "./pages/verification";

// Sprint 49.1 placeholder router. Real navigation / layout shell
// lands in Phase 50.2 (chat-v2 main flow) and is extended each phase.
function Home() {
  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>IPA Platform V2</h1>
      <p>
        <strong>Status:</strong> Phase 57+ SaaS Frontend 3/N — Sprint 57.4 Admin Tenants Console list bundle.
      </p>
      <p>Pages currently registered:</p>
      <ul>
        <li>
          <Link to="/chat-v2">/chat-v2</Link> — Phase 50.2 main flow
        </li>
        <li>
          <Link to="/governance">/governance</Link> — Phase 53.3 HITL UI
        </li>
        <li>
          <Link to="/verification">/verification</Link> — Phase 54.1 verifier panel
        </li>
        <li>
          <Link to="/cost-dashboard">/cost-dashboard</Link> — Sprint 57.1 cost ledger summary (admin-platform role)
        </li>
        <li>
          <Link to="/sla-dashboard">/sla-dashboard</Link> — Sprint 57.1 SLA report (admin-platform role)
        </li>
        <li>
          <Link to="/tenant-settings">/tenant-settings</Link> — Sprint 57.3 tenant CRUD R+U (admin-platform role)
        </li>
        <li>
          <Link to="/admin-tenants">/admin-tenants</Link> — Sprint 57.4 admin tenants console list (admin-platform role)
        </li>
      </ul>
      <p>
        Backend health: <code>GET /api/v1/health</code> (proxied to localhost:8001)
      </p>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/chat-v2/*" element={<ChatV2Page />} />
      <Route path="/governance/*" element={<GovernancePage />} />
      <Route path="/verification/*" element={<VerificationPage />} />
      <Route path="/cost-dashboard/*" element={<CostDashboardPage />} />
      <Route path="/sla-dashboard/*" element={<SLADashboardPage />} />
      <Route path="/tenant-settings/*" element={<TenantSettingsPage />} />
      <Route path="/admin-tenants" element={<AdminTenantsPage />} />
    </Routes>
  );
}
