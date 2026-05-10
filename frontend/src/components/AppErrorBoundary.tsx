/**
 * File: frontend/src/components/AppErrorBoundary.tsx
 * Purpose: Top-level error boundary — catches uncaught render errors with reset + reportError.
 * Category: Frontend / components (Sprint 57.7 US-B2 Frontend Foundation 1/N)
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3 → Sprint 57.13 US-B4 (wire reportError)
 *
 * Description:
 *   Wraps `react-error-boundary.ErrorBoundary` with a custom Tailwind-styled
 *   fallback Card. Reset button re-renders children (typical pattern: user
 *   navigates back / re-mounts page). Sprint 57.13 US-B4: an uncaught render
 *   error now also flows to `reportError(error, { componentStack })` →
 *   console.error + Sentry (if DSN) + Cat 12 backend beacon.
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B4 — onError → reportError (was a placeholder note)
 *   - 2026-05-10: Initial creation (Sprint 57.7 US-B2)
 *
 * Related:
 *   - frontend/src/lib/observability.ts (reportError)
 */

import type { FC, ReactNode } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";

import { reportError } from "@/lib/observability";

function DefaultFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div
      role="alert"
      className="m-6 rounded-lg border border-destructive/40 bg-destructive/5 p-6"
    >
      <h2 className="text-lg font-semibold text-destructive">Something went wrong</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        An unexpected error occurred while rendering this view.
      </p>
      <pre className="mt-3 max-h-40 overflow-auto rounded bg-muted p-2 text-xs text-muted-foreground">
        {error instanceof Error ? error.message : String(error)}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-4 inline-flex items-center rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
      >
        Reset
      </button>
    </div>
  );
}

interface AppErrorBoundaryProps {
  children: ReactNode;
  onReset?: () => void;
}

export const AppErrorBoundary: FC<AppErrorBoundaryProps> = ({ children, onReset }) => {
  return (
    <ErrorBoundary
      FallbackComponent={DefaultFallback}
      onReset={onReset}
      onError={(error, info) => {
        reportError(error, { componentStack: info.componentStack });
      }}
    >
      {children}
    </ErrorBoundary>
  );
};
