/**
 * File: frontend/src/lib/toast.ts
 * Purpose: Thin app-wide toast helpers over `sonner` — single import surface
 * so call sites don't reach into the vendor API directly.
 * Category: Frontend / lib (Sprint 57.13 US-B1 — Toast system)
 * Scope: Phase 57 / Sprint 57.13 US-B1
 *
 * Description:
 *   `<Toaster richColors position="top-right" />` is mounted once in main.tsx
 *   (Sprint 57.7 US-B2). These wrappers keep call sites decoupled from sonner
 *   and let us normalise unknown error values into a readable string in one
 *   place (used by lib/queryClient.ts mutationCache.onError and authService).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 3)
 *
 * Related:
 *   - frontend/src/main.tsx (mounts <Toaster>)
 *   - frontend/src/lib/queryClient.ts (mutationCache.onError → toastError)
 *   - frontend/src/features/auth/services/authService.ts (401 → toastError)
 */

import { toast } from "sonner";

export function toastError(message: string): void {
  toast.error(message);
}

export function toastSuccess(message: string): void {
  toast.success(message);
}

export function toastInfo(message: string): void {
  toast(message);
}

/** Best-effort human-readable string from an unknown thrown value. */
export function errorMessage(err: unknown, fallback = "發生未預期的錯誤"): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === "string" && err) return err;
  return fallback;
}
