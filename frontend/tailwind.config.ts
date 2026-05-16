/**
 * File: frontend/tailwind.config.ts
 * Purpose: Tailwind CSS v4 configuration — content paths + theme + dark mode strategy.
 * Category: Frontend / build config
 * Scope: Phase 57 / Sprint 57.7 US-B1 (Frontend Foundation 1/N install)
 *
 * Modification History:
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
        // shadcn CSS variable bridge — actual values set in src/index.css
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
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
        // NEW Sprint 57.18 — mockup semantic tokens (US-B1)
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        danger: {
          DEFAULT: "hsl(var(--danger))",
          foreground: "hsl(var(--danger-foreground))",
        },
        thinking: {
          DEFAULT: "hsl(var(--thinking))",
          foreground: "hsl(var(--thinking-foreground))",
        },
        tool: {
          DEFAULT: "hsl(var(--tool))",
          foreground: "hsl(var(--tool-foreground))",
        },
        memory: {
          DEFAULT: "hsl(var(--memory))",
          foreground: "hsl(var(--memory-foreground))",
        },
        info: {
          DEFAULT: "hsl(var(--info))",
          foreground: "hsl(var(--info-foreground))",
        },
        // NEW Sprint 57.18 — mockup risk severity tokens (US-B1)
        risk: {
          low: "hsl(var(--risk-low))",
          medium: "hsl(var(--risk-medium))",
          high: "hsl(var(--risk-high))",
          critical: "hsl(var(--risk-critical))",
        },
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
