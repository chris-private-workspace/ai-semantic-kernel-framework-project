/**
 * File: frontend/tests/unit/components/AuthShell.test.tsx
 * Purpose: Unit tests for AuthShell + ThemeProvider + AppErrorBoundary.
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3 → Sprint 57.8 US-4 (renamed) → Sprint 57.23 US-B1 (mockup rewrite cascade)
 *
 * Description:
 *   Tests covering Sprint 57.23 US-B1 AuthShell rewrite to mockup full-screen centered:
 *   1. AuthShell renders children inside the data-testid="auth-shell" container + brand text
 *   2. AuthShell renders footer slot when provided (Sprint 57.23 renamed from headerActions)
 *   3. ThemeProvider toggles html.dark class + persists to localStorage
 *   4. AppErrorBoundary catches thrown error + renders fallback + reset works
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3 — initial as AppShell.test.tsx)
 *
 * Modification History:
 *   - 2026-05-18: Sprint 57.23 US-B1 — adapt AuthShell selectors for mockup rewrite (brand link → text; headerActions → footer)
 *   - 2026-05-10: Sprint 57.8 US-4 — rename test file + symbol references AppShell → AuthShell
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppErrorBoundary } from "../../../src/components/AppErrorBoundary";
import { AuthShell } from "../../../src/components/AuthShell";
import { ThemeProvider, useTheme } from "../../../src/components/ThemeProvider";

describe("AuthShell", () => {
  it("renders children inside the auth-shell container + brand text + subtitle", () => {
    render(
      <MemoryRouter>
        <AuthShell>
          <p>hello cost dashboard</p>
        </AuthShell>
      </MemoryRouter>,
    );
    expect(screen.getByText("hello cost dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("auth-shell")).toBeInTheDocument();
    expect(screen.getByText("IPA Platform")).toBeInTheDocument();
    expect(screen.getByText("V2 · loop-first")).toBeInTheDocument();
  });

  it("renders footer slot when provided", () => {
    render(
      <MemoryRouter>
        <AuthShell footer={<span>By signing in you agree to the Terms</span>}>
          <p>body</p>
        </AuthShell>
      </MemoryRouter>,
    );
    expect(screen.getByText(/By signing in you agree to the Terms/)).toBeInTheDocument();
  });
});

describe("ThemeProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
  });
  afterEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  // Tiny consumer used to drive toggleTheme from inside the provider.
  function Toggler() {
    const { theme, toggleTheme } = useTheme();
    return (
      <button onClick={toggleTheme} aria-label="toggle">
        theme={theme}
      </button>
    );
  }

  it("toggle persists theme to localStorage + applies html.dark class", () => {
    render(
      <ThemeProvider>
        <Toggler />
      </ThemeProvider>,
    );
    // Sprint 57.21 Day 4 D-DAY4-6: dark is now the default (Sprint 57.20 mockup
    // dark-default intent — no matchMedia OS-preference path).
    expect(screen.getByText(/theme=dark/)).toBeInTheDocument();
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(window.localStorage.getItem("ipa-theme")).toBe("dark");

    // Toggle once → light (user opt-out)
    fireEvent.click(screen.getByRole("button", { name: "toggle" }));
    expect(screen.getByText(/theme=light/)).toBeInTheDocument();
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(window.localStorage.getItem("ipa-theme")).toBe("light");
  });
});

describe("AppErrorBoundary", () => {
  it("renders fallback Reset button + heading when child throws", () => {
    function Boom() {
      throw new Error("kaboom");
    }
    // Suppress React's expected console.error for thrown render error.
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      render(
        <AppErrorBoundary>
          <Boom />
        </AppErrorBoundary>,
      );
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
      expect(screen.getByText(/kaboom/)).toBeInTheDocument();
    } finally {
      errSpy.mockRestore();
    }
  });
});

