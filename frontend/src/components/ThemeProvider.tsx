/**
 * File: frontend/src/components/ThemeProvider.tsx
 * Purpose: Light/dark theme context — toggleTheme + localStorage persistence.
 * Category: Frontend / components (Sprint 57.7 US-B2 Frontend Foundation 1/N)
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3
 *
 * Description:
 *   React Context with `theme: 'light' | 'dark'` + `toggleTheme()`. Persists
 *   user preference to localStorage under key `ipa-theme`. Applies the
 *   shadcn `dark` class to <html> when theme === 'dark' (per index.css
 *   :root vs .dark CSS variable scopes).
 *
 *   Initial theme resolution order:
 *   1. localStorage[ipa-theme] (user override via top-header theme toggle)
 *   2. 'dark' default (Sprint 57.20 mockup dark-default intent; strict — no
 *      matchMedia OS-preference path because Sprint 57.20 design directive
 *      hard-coded dark regardless of OS)
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3)
 * Last Modified: 2026-05-18
 *
 * Modification History (newest-first):
 *   - 2026-05-18: Sprint 57.21 Day 4 D-DAY4-6 — `resolveInitialTheme` final fallback `light`→`dark` to honour Sprint 57.20 index.html `class="dark"` intent; flip matchMedia check to light-preference override
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
  // Sprint 57.21 Day 4 D-DAY4-6 reality-fix: Sprint 57.20 set index.html
  // class="dark" (mockup dark-default intent) but this resolver previously
  // returned "light" as final fallback, causing the ThemeProvider's mount
  // effect to strip the static "dark" class. Sprint 57.20 strict intent =
  // dark-default REGARDLESS of OS preference; user can toggle via top-header
  // theme button if they want light.
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "dark";
}

function applyHtmlClass(theme: Theme): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export const ThemeProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => resolveInitialTheme());

  useEffect(() => {
    applyHtmlClass(theme);
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
