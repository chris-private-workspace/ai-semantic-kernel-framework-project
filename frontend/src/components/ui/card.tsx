/**
 * File: frontend/src/components/ui/card.tsx
 * Purpose: shadcn-style Card primitives — Card / CardHeader / CardTitle / CardContent / CardFooter.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Plain composable card layout (Tailwind only — no Radix). Uses the
 *   semantic surface tokens that exist in tailwind.config (border / background /
 *   foreground / muted) — there is no `--card` token in this app's index.css,
 *   so the surface is `bg-background border border-border` (matches STYLE.md §6's
 *   `rounded-lg border border-border p-4`).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 *
 * Related:
 *   - frontend/src/lib/utils.ts (cn)
 *   - STYLE.md §6 (3-card skeleton mirrors this card's outer shape)
 */

import { type HTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-lg border border-border bg-background text-foreground", className)}
      {...props}
    />
  ),
);
Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-4", className)} {...props} />
  ),
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    // Content is supplied by the consumer via children (standard shadcn primitive);
    // the lint rule can't see through the {...props} spread.
    // eslint-disable-next-line jsx-a11y/heading-has-content
    <h3 ref={ref} className={cn("text-lg font-semibold leading-none tracking-tight", className)} {...props} />
  ),
);
CardTitle.displayName = "CardTitle";

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-4 pt-0", className)} {...props} />
  ),
);
CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center p-4 pt-0", className)} {...props} />
  ),
);
CardFooter.displayName = "CardFooter";
