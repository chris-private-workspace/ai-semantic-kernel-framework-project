/**
 * File: frontend/src/components/ThemeProvider.tsx
 * Purpose: Light/dark theme context — toggleTheme + localStorage persistence; drives the mockup [data-theme] attribute.
 * Category: Frontend / components (Sprint 57.7 US-B2 Frontend Foundation 1/N)
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3 → Sprint 57.28 US-C2 (verbatim-CSS foundation switch)
 *
 * Description:
 *   React Context with `theme: 'light' | 'dark'` + `toggleTheme()`. Persists
 *   user preference to localStorage under key `ipa-theme`.
 *
 *   Sprint 57.28 (verbatim-CSS foundation switch) — theme is now driven by the
 *   mockup mechanism. `styles-mockup.css` scopes --bg/--fg/--border/... by
 *   `[data-theme][data-variant]`, so the provider sets `data-theme` on <html>
 *   ("dark" | "light"). `data-variant="linear"` + `data-density` stay as the
 *   index.html static defaults (future variant/density switching can mount here).
 *   The shadcn `.dark` class is ALSO kept in sync during the Phase 1 transition —
 *   the not-yet-re-pointed pages still consume shadcn `:root`/`.dark`-scoped
 *   tokens from index.css; Phase 2 drops the `.dark` toggle as those pages
 *   re-point off shadcn utilities.
 *
 *   Light + dark are both supported — the mockup has a full light theme
 *   (`reference/design-mockups/styles.css` `[data-theme="light"]`, D-PRE-1).
 *
 *   Initial theme resolution order:
 *   1. localStorage[ipa-theme] (user override via top-header theme toggle)
 *   2. 'dark' default (mockup :root is dark-linear; Sprint 57.20+ dark-default intent)
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.28 US-C2 — theme drives mockup [data-theme]; .dark kept for Phase 1
 *   - 2026-05-18: Sprint 57.21 Day 4 D-DAY4-6 — `resolveInitialTheme` final fallback `light`→`dark`
 *   - 2026-05-10: Initial creation (Sprint 57.7 US-B2)
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type FC,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (next: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "ipa-theme";

function resolveInitialTheme(): Theme {
  // Dark-default regardless of OS preference: the mockup :root is dark-linear
  // and index.html carries the static data-theme="dark"; the user can switch
  // to light via the top-header theme toggle (persisted to localStorage).
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "dark";
}

// === applyHtmlTheme: drive both the mockup and the shadcn theme mechanisms ===
// Why: Sprint 57.28 switched the CSS foundation to verbatim mockup CSS, which
// scopes its tokens by the `[data-theme]` attribute — NOT the shadcn `.dark`
// class. During the Phase 1 transition both must move together: `data-theme`
// for styles-mockup.css, `.dark` for the index.css shadcn tokens the
// not-yet-re-pointed pages still read. Phase 2 removes the `.dark` line.
function applyHtmlTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  html.setAttribute("data-theme", theme);
  html.classList.toggle("dark", theme === "dark");
}

export const ThemeProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => resolveInitialTheme());

  useEffect(() => {
    applyHtmlTheme(theme);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggleTheme = useCallback(
    () => setThemeState((prev) => (prev === "light" ? "dark" : "light")),
    [],
  );

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used inside <ThemeProvider>");
  }
  return ctx;
}
