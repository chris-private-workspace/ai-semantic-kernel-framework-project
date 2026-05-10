/**
 * File: frontend/src/lib/observability.ts
 * Purpose: Frontend observability — Sentry error reporting (opt-in via DSN) + Web Vitals beacons.
 * Category: Frontend / lib (Sprint 57.13 US-B4 — frontend observability)
 * Scope: Phase 57 / Sprint 57.13 US-B4
 *
 * Description:
 *   Three entry points:
 *     - initObservability() — called once at startup. If VITE_SENTRY_DSN is set,
 *       dynamic-imports @sentry/react and calls Sentry.init(). No DSN → no-op
 *       (so dev / CI never ship telemetry). Dynamic import keeps the ~100 kB
 *       Sentry bundle out of the main chunk.
 *     - reportError(err, ctx?) — ALWAYS console.error; if Sentry is live,
 *       captureException; ALSO fire-and-forget POST /api/v1/telemetry/frontend-error
 *       so the Cat 12 backend records it regardless of Sentry. Never throws.
 *     - reportWebVitals() — onCLS/onFCP/onLCP/onINP/onTTFB → POST
 *       /api/v1/telemetry/frontend (navigator.sendBeacon, fetch+keepalive fallback).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 6)
 *
 * Related:
 *   - backend/src/api/v1/telemetry.py (POST /telemetry/frontend + /frontend-error — Cat 12)
 *   - frontend/src/main.tsx (calls initObservability + reportWebVitals at startup)
 *   - frontend/src/components/AppErrorBoundary.tsx (onError → reportError)
 *   - frontend/src/features/auth/services/authService.ts (5xx/network → reportError)
 */

type SentryModule = typeof import("@sentry/react");

let sentry: SentryModule | null = null;
let sentryInitStarted = false;

const VITALS_ENDPOINT = "/api/v1/telemetry/frontend";
const ERROR_ENDPOINT = "/api/v1/telemetry/frontend-error";

function getSentryDsn(): string | undefined {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  return typeof dsn === "string" && dsn.trim() ? dsn.trim() : undefined;
}

/** Fire-and-forget POST — sendBeacon when available (survives page unload), else fetch+keepalive. */
function beacon(url: string, body: unknown): void {
  const payload = JSON.stringify(body);
  try {
    if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
      const ok = navigator.sendBeacon(url, new Blob([payload], { type: "application/json" }));
      if (ok) return;
    }
    void fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* never let telemetry break the app */
  }
}

/** Call once at startup. Initializes Sentry only when VITE_SENTRY_DSN is set. */
export async function initObservability(): Promise<void> {
  const dsn = getSentryDsn();
  if (!dsn || sentryInitStarted) return;
  sentryInitStarted = true;
  try {
    sentry = await import("@sentry/react");
    sentry.init({
      dsn,
      environment: import.meta.env.MODE,
      tracesSampleRate: 0.1,
    });
  } catch (err) {
    // Sentry import/init failed — degrade gracefully; observability is best-effort.
    console.error("Sentry init failed", err);
    sentry = null;
  }
}

/** Report an error. Always logs; captures to Sentry if live; beacons to Cat 12 backend. Never throws. */
export function reportError(err: unknown, ctx?: Record<string, unknown>): void {
  console.error(err, ctx ?? "");
  try {
    if (sentry) {
      sentry.captureException(err, ctx ? { extra: ctx } : undefined);
    }
  } catch {
    /* ignore */
  }
  const error = err instanceof Error ? err : new Error(String(err));
  beacon(ERROR_ENDPOINT, {
    message: error.message,
    stack: error.stack,
    url: typeof window !== "undefined" ? window.location.href : undefined,
    user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    context: ctx,
  });
}

/** Subscribe to Core Web Vitals and beacon each metric to the Cat 12 backend. Call once at startup. */
export function reportWebVitals(): void {
  void import("web-vitals")
    .then(({ onCLS, onFCP, onLCP, onINP, onTTFB }) => {
      const send = (metric: {
        name: string;
        value: number;
        id: string;
        rating: string;
        navigationType: string;
      }): void => {
        beacon(VITALS_ENDPOINT, {
          name: metric.name,
          value: metric.value,
          id: metric.id,
          rating: metric.rating,
          navigationType: metric.navigationType,
          url: typeof window !== "undefined" ? window.location.href : undefined,
        });
      };
      onCLS(send);
      onFCP(send);
      onLCP(send);
      onINP(send);
      onTTFB(send);
    })
    .catch(() => {
      /* web-vitals load failed — skip; non-critical */
    });
}
