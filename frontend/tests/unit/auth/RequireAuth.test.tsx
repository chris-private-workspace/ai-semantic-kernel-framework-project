/**
 * File: frontend/tests/unit/auth/RequireAuth.test.tsx
 * Purpose: Unit test — <RequireAuth> route gate (spinner / redirect / render).
 * Category: Frontend / tests / unit / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 1)
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { RequireAuth } from "../../../src/features/auth/components/RequireAuth";
import { useAuthStore } from "../../../src/features/auth/store/authStore";

function renderGuardedAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/governance"
          element={
            <RequireAuth>
              <div>SECRET CONTENT</div>
            </RequireAuth>
          }
        />
        <Route path="/auth/login" element={<div>LOGIN PAGE</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("<RequireAuth>", () => {
  beforeEach(() => {
    sessionStorage.clear();
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  afterEach(() => {
    sessionStorage.clear();
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  it("status 'unknown' → renders the loading spinner, not the children", () => {
    useAuthStore.setState({ status: "unknown" });
    renderGuardedAt("/governance");
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByText("SECRET CONTENT")).toBeNull();
    expect(screen.queryByText("LOGIN PAGE")).toBeNull();
  });

  it("status 'anonymous' → redirects to /auth/login and stashes the attempted path", () => {
    useAuthStore.setState({ status: "anonymous" });
    renderGuardedAt("/governance");
    expect(screen.getByText("LOGIN PAGE")).toBeInTheDocument();
    expect(screen.queryByText("SECRET CONTENT")).toBeNull();
    expect(sessionStorage.getItem("v2_post_login_redirect")).toBe("/governance");
  });

  it("status 'authenticated' → renders the children", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: { id: "u-1", email: "a@b.test", display_name: "A" },
      tenant: { id: "t-1", name: "Acme", code: "ACME" },
      roles: ["user"],
    });
    renderGuardedAt("/governance");
    expect(screen.getByText("SECRET CONTENT")).toBeInTheDocument();
    expect(screen.queryByText("LOGIN PAGE")).toBeNull();
  });
});
