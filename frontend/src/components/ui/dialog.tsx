/**
 * File: frontend/src/components/ui/dialog.tsx
 * Purpose: shadcn-style modal Dialog primitives wrapping @radix-ui/react-dialog.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B3)
 * Scope: Phase 57 / Sprint 57.13 US-B3
 *
 * Description:
 *   Thin Radix Dialog wrapper. Exports:
 *     - Dialog / DialogTrigger / DialogClose / DialogPortal — Radix re-exports
 *     - DialogOverlay — dimmed backdrop
 *     - DialogContent — centered panel (portals to <body>) with an X close button
 *     - DialogHeader / DialogFooter — layout wrappers
 *     - DialogTitle / DialogDescription — accessible title/description (Radix)
 *   Controlled use: <Dialog open onOpenChange={...}><DialogContent>…</DialogContent></Dialog>.
 *   Radix gives focus-trap + ESC-to-close + outside-click-to-close + aria wiring
 *   for free (replaces the hand-rolled overlay+stopPropagation pattern).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4 — actually US-B3 / Day 5)
 *
 * Related:
 *   - @radix-ui/react-dialog (already in package.json, 57.7 D-PRE-6)
 *   - frontend/src/features/governance/components/DecisionModal.tsx (consumer)
 */

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { type HTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogPortal = DialogPrimitive.Portal;
export const DialogClose = DialogPrimitive.Close;

export const DialogOverlay = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn("fixed inset-0 z-50 bg-black/45 data-[state=open]:animate-in", className)}
    {...props}
  />
));
DialogOverlay.displayName = "DialogOverlay";

export const DialogContent = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-1/2 top-1/2 z-50 grid w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4",
        "rounded-lg border border-border bg-background p-6 shadow-2xl",
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close
        className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = "DialogContent";

export const DialogHeader = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-1.5 text-left", className)} {...props} />
);
DialogHeader.displayName = "DialogHeader";

export const DialogFooter = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex justify-end gap-2", className)} {...props} />
);
DialogFooter.displayName = "DialogFooter";

export const DialogTitle = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-xl font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
DialogTitle.displayName = "DialogTitle";

export const DialogDescription = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
DialogDescription.displayName = "DialogDescription";
