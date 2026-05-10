/**
 * File: frontend/src/components/ui/skeleton.tsx
 * Purpose: Loading-skeleton primitives — Skeleton (base pulse box) + TableSkeleton + CardSkeleton.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Canonicalises the inline `animate-pulse` skeletons that Sprint 57.9 + 57.x
 *   feature pages duplicated. Per STYLE.md §6:
 *     - <Skeleton>      — a single pulsing rounded box (compose freely)
 *     - <TableSkeleton> — N rows × M cols of <td> pulse bars (default 5×6)
 *     - <CardSkeleton>  — N dashboard summary cards, each 3 stacked bars (default 3)
 *   Skeletons (not spinners) for page-level loads — they reserve layout + show
 *   the expected shape.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 *
 * Related:
 *   - STYLE.md §6 (Loading Skeleton Pattern — canonical code these mirror)
 *   - frontend/src/components/ui/index.ts (barrel)
 */

import type { FC } from "react";

import { cn } from "../../lib/utils";

export const Skeleton: FC<{ className?: string }> = ({ className }) => (
  <div className={cn("animate-pulse rounded bg-muted", className)} />
);

export const TableSkeleton: FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 6 }) => (
  <table className="w-full">
    <tbody>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="border-b border-border">
          {Array.from({ length: cols }).map((__, j) => (
            <td key={j} className="p-2">
              <Skeleton className="h-4 w-full" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);

export const CardSkeleton: FC<{ count?: number }> = ({ count = 3 }) => (
  <div className={cn("grid gap-4", count === 3 ? "grid-cols-3" : "grid-cols-2")}>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="space-y-2 rounded-lg border border-border p-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-3 w-20" />
      </div>
    ))}
  </div>
);
