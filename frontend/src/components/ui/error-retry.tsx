/**
 * File: frontend/src/components/ui/error-retry.tsx
 * Purpose: <ErrorRetry> — page-level fetch-failure panel with a Retry button.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Canonicalises STYLE.md §8. Render when a TanStack Query is `isError`. `onRetry`
 *   wires to `refetch()`. `error` (an Error) or `message` (a string) supplies the
 *   detail line. The Retry button is a real `<button>` with accessible name
 *   "Retry" so the STYLE.md §8 `retryClicked`-flag e2e mock pattern works against
 *   it unchanged. NOTE: STYLE.md §8 sample writes `text-danger`; this app has no
 *   `danger` Tailwind token — `text-destructive` (which exists) is used here.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 *
 * Related:
 *   - STYLE.md §8 (Error Retry UX Pattern — canonical layout)
 *   - frontend/src/components/ui/button.tsx (Retry button)
 */

import type { FC } from "react";

import { cn } from "../../lib/utils";
import { Button } from "./button";

export interface ErrorRetryProps {
  /** The thrown Error (preferred). */
  error?: Error | null;
  /** Headline; defaults to "Failed to load data". */
  message?: string;
  onRetry: () => void;
  className?: string;
}

export const ErrorRetry: FC<ErrorRetryProps> = ({ error, message, onRetry, className }) => (
  <div className={cn("flex flex-col items-center py-12 text-center", className)}>
    <p className="mb-2 text-destructive">{message ?? "Failed to load data"}</p>
    <p className="mb-4 text-sm text-muted-foreground">{error?.message ?? "Unknown error"}</p>
    <Button variant="outline" onClick={onRetry}>
      Retry
    </Button>
  </div>
);
