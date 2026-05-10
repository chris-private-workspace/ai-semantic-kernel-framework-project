/**
 * File: frontend/src/components/ui/index.ts
 * Purpose: Barrel export for the design-system component layer.
 * Category: Frontend / components / ui (Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Single import surface — `import { Button, TableSkeleton, EmptyState } from
 *   "@/components/ui"` (or the relative equivalent). All loading / empty / error
 *   UX in feature pages MUST come from here, not bespoke inline markup (see
 *   CONVENTION.md §design-system addendum).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4; Radix Dialog/DropdownMenu added Day 5 US-B3)
 */

export { Badge, badgeVariants, type BadgeProps } from "./badge";
export { Button, buttonVariants, type ButtonProps } from "./button";
export { Card, CardContent, CardFooter, CardHeader, CardTitle } from "./card";
export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
} from "./dialog";
export {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";
export { EmptyState, type EmptyStateProps } from "./empty-state";
export { ErrorRetry, type ErrorRetryProps } from "./error-retry";
export { CardSkeleton, Skeleton, TableSkeleton } from "./skeleton";
