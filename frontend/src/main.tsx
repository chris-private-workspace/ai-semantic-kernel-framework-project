/**
 * File: frontend/src/main.tsx
 * Purpose: React DOM root — wraps App in Theme + ErrorBoundary + QueryClient + Toaster.
 * Category: Frontend / root (Sprint 57.7 US-B2 Frontend Foundation 1/N)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B4 — initObservability() + reportWebVitals() at startup
 *   - 2026-05-10: Sprint 57.13 US-B1 — QueryClient moved to lib/queryClient.ts (mutationCache toast)
 *   - 2026-05-10: Sprint 57.7 US-B2 — wrap providers (Theme + ErrorBoundary + Query + Sonner)
 *   - 2026-05-09: Sprint 57.7 US-B1 — import index.css for Tailwind 4 + shadcn vars
 *   - Initial: BrowserRouter + App
 */

import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import App from "./App";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { ThemeProvider } from "./components/ThemeProvider";
import "./index.css";
import { initObservability, reportWebVitals } from "./lib/observability";
import { queryClient } from "./lib/queryClient";

// Best-effort, fire-and-forget; never blocks render. Sentry only when VITE_SENTRY_DSN is set.
void initObservability();
reportWebVitals();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
          <Toaster richColors position="top-right" />
        </QueryClientProvider>
      </AppErrorBoundary>
    </ThemeProvider>
  </React.StrictMode>,
);
