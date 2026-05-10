/**
 * File: frontend/lighthouserc.cjs
 * Purpose: Lighthouse CI config — perf / a11y / best-practices budgets for the public login page.
 * Category: Frontend / CI / performance (Sprint 57.13 US-B7)
 * Scope: Phase 57 / Sprint 57.13 US-B7
 *
 * Description:
 *   Run via `npm run lhci` (= `lhci autorun`) or the frontend-lighthouse.yml
 *   workflow. `lhci autorun` builds nothing itself — it expects `dist/` to
 *   already exist (CI does `npm run build` first), then `startServerCommand`
 *   serves it via `vite preview` (which does SPA fallback, unlike a bare static
 *   server) and runs Lighthouse against the URL list. Only `/auth/login` is
 *   listed: it's the one page that renders fully without auth/backend (the rest
 *   need a JWT + API). Assertions: a11y is a hard `error` gate (≥ 0.9); perf /
 *   best-practices / FCP / TTI are `warn` (informational while the bundle is
 *   being optimized — see AD-Bundle-Size). Reports upload to
 *   temporary-public-storage (no token needed).
 *
 *   CommonJS (.cjs) on purpose — package.json is "type": "module", and LHCI
 *   loads its config via require(). Mirrors i18next-parser.config.cjs.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 8)
 *
 * Related:
 *   - .github/workflows/frontend-lighthouse.yml (runs this on PRs touching frontend/**)
 *   - frontend/package.json "lhci" script
 */

module.exports = {
  ci: {
    collect: {
      startServerCommand: "npm run preview -- --port 4173 --strictPort",
      url: ["http://localhost:4173/auth/login"],
      numberOfRuns: 1,
      settings: {
        // CI containers run Chrome unsandboxed.
        chromeFlags: "--no-sandbox --headless=new",
      },
    },
    assert: {
      assertions: {
        "categories:accessibility": ["error", { minScore: 0.9 }],
        "categories:performance": ["warn", { minScore: 0.7 }],
        "categories:best-practices": ["warn", { minScore: 0.8 }],
        "first-contentful-paint": ["warn", { maxNumericValue: 2000 }],
        interactive: ["warn", { maxNumericValue: 4000 }],
      },
    },
    upload: { target: "temporary-public-storage" },
  },
};
