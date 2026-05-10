/**
 * File: frontend/src/components/ui/badge.tsx
 * Purpose: shadcn-style <Badge> — cva variants incl. the STYLE.md §3 4-level risk palette.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Inline status pill. Generic variants: default / secondary / outline /
 *   destructive. Risk variants (STYLE.md §3 — same hex values as the canonical
 *   ApprovalCard so visual continuity holds): risk-low / risk-medium / risk-high
 *   / risk-critical. Existing per-feature badges (AuditChainBadge / VerifierTypeBadge
 *   / MemoryScopeBadge) keep their own colour logic for now — this <Badge> is the
 *   shared shell new code should reach for.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 *
 * Related:
 *   - STYLE.md §3 (Risk Badge Palette — hex values mirrored here)
 *   - frontend/src/lib/utils.ts (cn)
 */

/* eslint-disable react-refresh/only-export-components -- shadcn pattern: component + cva variants co-located */

import { type VariantProps, cva } from "class-variance-authority";
import type { FC, HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "border-border text-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        // STYLE.md §3 risk palette (hex matches features/governance/components/ApprovalCard.tsx).
        "risk-low": "border-transparent bg-[#2e7d32]/10 text-[#2e7d32]",
        "risk-medium": "border-transparent bg-[#ed6c02]/10 text-[#ed6c02]",
        "risk-high": "border-transparent bg-[#d84315]/10 text-[#d84315]",
        "risk-critical": "border-transparent bg-[#b71c1c]/10 text-[#b71c1c]",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge: FC<BadgeProps> = ({ className, variant, ...props }) => (
  <span className={cn(badgeVariants({ variant }), className)} {...props} />
);

export { badgeVariants };
