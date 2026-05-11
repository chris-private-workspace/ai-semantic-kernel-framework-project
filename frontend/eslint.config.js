// ESLint 9 flat config — IPA Platform V2 frontend.
// Sprint 49.1 minimal config; Sprint 57.13 US-B6 adds eslint-plugin-jsx-a11y (accessibility lint);
// Sprint 57.15 adds no-restricted-syntax for the JSX `style=` prop (no-inline-style guard;
// eslint-plugin-react isn't a dep, so the built-in no-restricted-syntax selector is used —
// it catches `<div style={…}>` and `<Comp style={…}>` alike; AD-Inline-Style-Cleanup-Sweep).

import tseslint from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default [
  {
    ignores: [
      "dist",
      "node_modules",
      "vite.config.js",
      "vite.config.d.ts",
      "*.tsbuildinfo",
    ],
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        document: "readonly",
        window: "readonly",
        console: "readonly",
        HTMLElement: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "jsx-a11y": jsxA11y,
    },
    rules: {
      ...jsxA11y.flatConfigs.recommended.rules,
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      // No-inline-style guard (STYLE.md §1). Catches the JSX `style=` prop on
      // DOM elements and components. For genuinely-dynamic values (computed
      // dimensions, progress %) set a CSS custom property and read it via a
      // Tailwind arbitrary value (e.g. `pl-[var(--x)]`), or — last resort —
      // add `// eslint-disable-next-line no-restricted-syntax -- <reason>`.
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='style']",
          message:
            "Use Tailwind utility classes instead of inline `style` (STYLE.md §1). For dynamic values, use a CSS custom property + Tailwind arbitrary value, or add `// eslint-disable-next-line no-restricted-syntax -- <reason>`.",
        },
      ],
    },
  },
];
