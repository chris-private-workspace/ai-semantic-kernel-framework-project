/**
 * File: frontend/src/components/ui/dropdown-menu.tsx
 * Purpose: shadcn-style DropdownMenu primitives wrapping @radix-ui/react-dropdown-menu.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B3)
 * Scope: Phase 57 / Sprint 57.13 US-B3
 *
 * Description:
 *   Thin Radix DropdownMenu wrapper. Exports:
 *     - DropdownMenu / DropdownMenuTrigger / DropdownMenuPortal — Radix re-exports
 *     - DropdownMenuContent — portalled menu surface (uses bg-background — this
 *       app's tailwind.config has no `popover` token)
 *     - DropdownMenuItem / DropdownMenuSeparator / DropdownMenuLabel
 *   Radix gives keyboard nav + focus + ESC/outside-click close + `role="menu"` /
 *   `role="menuitem"` for free (replaces the hand-rolled popover in UserMenu).
 *
 * Created: 2026-05-10 (Sprint 57.13 US-B3 / Day 5)
 *
 * Related:
 *   - @radix-ui/react-dropdown-menu (installed Sprint 57.13 Day 5)
 *   - frontend/src/components/UserMenu.tsx (consumer)
 */

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

import { cn } from "../../lib/utils";

export const DropdownMenu = DropdownMenuPrimitive.Root;
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
export const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

export const DropdownMenuContent = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 6, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[12rem] overflow-hidden rounded-md border border-border bg-background p-1 text-foreground shadow-md",
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
));
DropdownMenuContent.displayName = "DropdownMenuContent";

export const DropdownMenuItem = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none",
      "focus:bg-muted data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = "DropdownMenuItem";

export const DropdownMenuSeparator = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-border", className)}
    {...props}
  />
));
DropdownMenuSeparator.displayName = "DropdownMenuSeparator";

export const DropdownMenuLabel = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn("px-2 py-1.5 text-xs font-semibold text-muted-foreground", className)}
    {...props}
  />
));
DropdownMenuLabel.displayName = "DropdownMenuLabel";
