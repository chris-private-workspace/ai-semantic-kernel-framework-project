/**
 * File: frontend/i18next-parser.config.cjs
 * Purpose: i18next-parser config — scans src/ for t("...") calls and updates the en/zh-TW JSON bundles.
 * Category: Frontend / i18n / tooling (Sprint 57.13 US-B5)
 * Scope: Phase 57 / Sprint 57.13 US-B5
 *
 * Description:
 *   Run via `npm run i18n:extract`. Walks src/**/*.{ts,tsx}, collects translation
 *   keys (default keySeparator `.`, namespaceSeparator `:`), and writes
 *   src/i18n/locales/{en,zh-TW}/{ns}.json. Missing keys are added with an empty
 *   value (English file uses the key as the default value); existing translations
 *   are kept. `keepRemoved: true` so nothing is dropped silently — prune by hand.
 *
 *   CommonJS (.cjs) on purpose: package.json is "type": "module", and
 *   i18next-parser loads its config via require().
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 7)
 *
 * Related:
 *   - frontend/src/i18n/index.ts (the matching i18next init: same ns + separators)
 */

module.exports = {
  locales: ["en", "zh-TW"],
  defaultNamespace: "common",
  namespaceSeparator: ":",
  keySeparator: ".",
  input: ["src/**/*.{ts,tsx}"],
  output: "src/i18n/locales/$LOCALE/$NAMESPACE.json",
  // English bundle: fall back to the key text; other locales start empty.
  useKeysAsDefaultValue: false,
  defaultValue: (locale, _ns, key) => (locale === "en" ? key : ""),
  keepRemoved: true,
  sort: true,
  createOldCatalogs: false,
};
