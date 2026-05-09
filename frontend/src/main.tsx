/**
 * File: frontend/src/main.tsx
 * Purpose: React DOM root — wraps App in Theme + ErrorBoundary + QueryClient + Toaster.
 * Category: Frontend / root (Sprint 57.7 US-B2 Frontend Foundation 1/N)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.7 US-B2 — wrap providers (Theme + ErrorBoundary + Query + Sonner)
 *   - 2026-05-09: Sprint 57.7 US-B1 — import index.css for Tailwind 4 + shadcn vars
 *   - Initial: BrowserRouter + App
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import App from "./App";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { ThemeProvider } from "./components/ThemeProvider";
import "./index.css";

// Single QueryClient instance per app — staleTime 30s is a sensible default
// for SaaS dashboards that prefer freshness over over-fetching. retry:false
// aligns with the SaaS UX where 4xx/5xx surfaces immediately + a manual
// "Retry" button is provided per-page (cost / sla / tenant-settings); avoids
// auto-retry storms against admin endpoints + matches the e2e contract that
// the first failure renders the error UX (Sprint 57.9 US-6 Day 4).
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});

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
