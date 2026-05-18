/**
 * File: frontend/tests/unit/components/AuthShell.test.tsx
 * Purpose: Unit tests for Sprint 57.7 US-B2 (now AuthShell per Sprint 57.8 B1) + ThemeProvider + AppErrorBoundary.
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3 → Sprint 57.8 US-4 (renamed AppShell → AuthShell per Day 0 Decision B1)
 *
 * Description:
 *   4 tests covering Sprint 57.7 US-B2 components (renamed AppShell → AuthShell in 57.8):
 *   1. AuthShell renders children inside main + brand link
 *   2. AuthShell renders headerActions when provided
 *   3. ThemeProvider toggles html.dark class + persists to localStorage
 *   4. AppErrorBoundary catches thrown error + renders fallback + reset works
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3 — initial as AppShell.test.tsx)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.8 US-4 — rename test file + symbol references AppShell → AuthShell
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppErrorBoundary } from "../../../src/components/AppErrorBoundary";
import { AuthShell } from "../../../src/components/AuthShell";
import { ThemeProvider, useTheme } from "../../../src/components/ThemeProvider";

describe("AuthShell", () => {
  it("renders children inside the main slot + brand link", () => {
    render(
      <MemoryRouter>
        <AuthShell>
          <p>hello cost dashboard</p>
        </AuthShell>
      </MemoryRouter>,
    );
    expect(screen.getByText("hello cost dashboard")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "IPA Platform" })).toBeInTheDocument();
  });

  it("renders headerActions when provided", () => {
    render(
      <MemoryRouter>
        <AuthShell headerActions={<button>Refresh</button>}>
          <p>body</p>
        </AuthShell>
      </MemoryRouter>,
    );
    expect(screen.getByRole("button", { name: "Refresh" })).toBeInTheDocument();
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

