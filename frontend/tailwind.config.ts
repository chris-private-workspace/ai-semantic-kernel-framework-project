/**
 * File: frontend/tailwind.config.ts
 * Purpose: Tailwind CSS v4 configuration — content paths + theme + dark mode strategy.
 * Category: Frontend / build config
 * Scope: Phase 57 / Sprint 57.7 US-B1 (Frontend Foundation 1/N install)
 *
 * Modification History:
 *   - 2026-05-22: Sprint 57.28 — Layer 4 bridge rework: mockup tokens hsl(var(--X))→var(--X) (oklch); de-collide --primary/--border → --sc-*
 *   - 2026-05-16: Sprint 57.18 — +7 semantic tokens + 4 risk levels + Geist font (closes AD-Style-Token-Config-Audit)
 *   - 2026-05-09: Initial creation (Sprint 57.7 US-B1 Day 2 PM)
 */

import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class", // toggle via html.dark — ThemeProvider US-B2 Day 3
  theme: {
    extend: {
      colors: {
        // Sprint 57.28 Layer 4 — two bridge styles co-exist during the Phase 1→2
        // transition: shadcn-system tokens (HSL, src/index.css) keep `hsl(var(--X))`;
        // mockup tokens (oklch, verbatim src/styles-mockup.css) use bare `var(--X)`.
        // shadcn --primary/--border are de-collided as --sc-primary/--sc-border.
        // --- shadcn-system (HSL) — retired page-by-page in the Phase 2 re-point epic ---
        border: "hsl(var(--sc-border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--sc-primary))",
          foreground: "hsl(var(--sc-primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        // --- mockup-system (oklch, verbatim from styles-mockup.css) — bare var(--X) ---
        // semantic: base owned by styles-mockup.css; *-foreground is production-only (HSL).
        success: {
          DEFAULT: "var(--success)",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "var(--warning)",
          foreground: "hsl(var(--warning-foreground))",
        },
        danger: {
          DEFAULT: "var(--danger)",
          foreground: "hsl(var(--danger-foreground))",
        },
        thinking: {
          DEFAULT: "var(--thinking)",
          foreground: "hsl(var(--thinking-foreground))",
        },
        tool: {
          DEFAULT: "var(--tool)",
          foreground: "hsl(var(--tool-foreground))",
        },
        memory: {
          DEFAULT: "var(--memory)",
          foreground: "hsl(var(--memory-foreground))",
        },
        info: {
          DEFAULT: "var(--info)",
          foreground: "hsl(var(--info-foreground))",
        },
        risk: {
          low: "var(--risk-low)",
          medium: "var(--risk-medium)",
          high: "var(--risk-high)",
          critical: "var(--risk-critical)",
        },
        bg: {
          DEFAULT: "var(--bg)",
          1: "var(--bg-1)",
          2: "var(--bg-2)",
          3: "var(--bg-3)",
          hover: "var(--bg-hover)",
        },
        fg: {
          DEFAULT: "var(--fg)",
          muted: "var(--fg-muted)",
          subtle: "var(--fg-subtle)",
        },
        "border-strong": "var(--border-strong)",
        "primary-soft": "var(--primary-soft)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ['"Geist"', '"Noto Sans TC"', "ui-sans-serif", "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
        mono: ['"Geist Mono"', "ui-monospace", '"JetBrains Mono"', "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
