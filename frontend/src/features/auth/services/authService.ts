/**
 * File: frontend/src/features/auth/services/authService.ts
 * Purpose: V2 auth fetch wrapper + /auth/me client + post-login redirect helpers.
 * Category: Frontend / auth / services
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Description:
 *   Foundational auth service consumed by ALL feature services + the
 *   authStore. Provides:
 *
 *   1. fetchWithAuth(url, init, opts?) — fetch() wrapper; sends cookies
 *      (credentials:"include") and adds Authorization: Bearer ONLY when a
 *      dev-login token is present in localStorage. Production browsers
 *      authenticate via the httpOnly v2_jwt cookie set by /api/v1/auth/callback.
 *      On a 401 it (by default) toasts "session expired", clears local auth
 *      state, stashes the current path, and navigates to /auth/login —
 *      callers that handle 401 themselves (fetchAuthMe / logout) opt out via
 *      { redirectOn401: false }.
 *   2. fetchAuthMe() — GET /api/v1/auth/me → {user, tenant, roles} | null
 *      (null on 401). Used by authStore.bootstrap().
 *   3. setPostLoginRedirect / consumePostLoginRedirect — stash the page the
 *      user was heading to so /auth/callback can return there.
 *   4. getDevToken / setDevToken / clearDevToken — dev fake-login token in
 *      localStorage (US-A4 path; absent in normal cookie flow).
 *   5. isAuthenticated() — reads authStore status (Sprint 57.13: source of
 *      truth moved from "localStorage has a token" to "authStore.status").
 *   6. logout() — POST /api/v1/auth/logout, clear local state, redirect to
 *      vendor signout (or /auth/login on error).
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B4 — fetchWithAuth reports network failure + 5xx via reportError
 *   - 2026-05-10: Sprint 57.13 US-B1 — fetchWithAuth 401 → toast + clear + redirect (redirectOn401 opt-out)
 *   - 2026-05-10: Sprint 57.13 US-A1 — add fetchAuthMe; isAuthenticated reads authStore; rename JWT helpers → dev-token; logout clears authStore
 *   - 2026-05-09: Initial creation (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py (login + callback + me + logout endpoints)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap consumer)
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/lib/toast.ts (toastError on 401)
 *   - frontend/src/lib/observability.ts (reportError on network / 5xx)
 */

import { reportError } from "../../../lib/observability";
import { toastError } from "../../../lib/toast";
import { useAuthStore } from "../store/authStore";
import type { AuthMeResponse } from "../store/authStore";

const DEV_TOKEN_KEY = "v2_jwt";
const REDIRECT_KEY = "v2_post_login_redirect";

/** Dev fake-login token (US-A4) — absent in the normal httpOnly-cookie flow. */
export function getDevToken(): string | null {
  return localStorage.getItem(DEV_TOKEN_KEY);
}

export function setDevToken(token: string): void {
  localStorage.setItem(DEV_TOKEN_KEY, token);
}

export function clearDevToken(): void {
  localStorage.removeItem(DEV_TOKEN_KEY);
}

export function setPostLoginRedirect(path: string): void {
  sessionStorage.setItem(REDIRECT_KEY, path);
}

export function consumePostLoginRedirect(): string {
  const path = sessionStorage.getItem(REDIRECT_KEY);
  sessionStorage.removeItem(REDIRECT_KEY);
  return path || "/cost-dashboard";
}

interface FetchWithAuthOptions {
  /** When true (default) a 401 toasts + clears auth + navigates to /auth/login. */
  redirectOn401?: boolean;
}

function handleAuthExpired(): void {
  toastError("登入已過期，請重新登入");
  clearDevToken();
  useAuthStore.getState().clear();
  setPostLoginRedirect(window.location.pathname + window.location.search);
  window.location.href = "/auth/login";
}

/**
 * fetch() wrapper used by all feature services + authStore. Always sends
 * cookies; adds Authorization: Bearer only if a dev-login token exists in
 * localStorage (so the normal cookie flow doesn't need JS-readable tokens).
 *
 * On a 401 it (by default) treats the session as expired: toast + clear local
 * auth state + stash current path + navigate to /auth/login. The response is
 * still returned so callers can inspect it. fetchAuthMe() / logout() opt out
 * via { redirectOn401: false } because they handle 401 themselves.
 */
export async function fetchWithAuth(
  input: RequestInfo | URL,
  init?: RequestInit,
  opts?: FetchWithAuthOptions,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  const devToken = getDevToken();
  if (devToken) {
    headers.set("Authorization", `Bearer ${devToken}`);
  }
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : String(input);
  let res: Response;
  try {
    res = await fetch(input, { ...init, headers, credentials: "include" });
  } catch (err) {
    // Network failure (DNS / offline / CORS). Surface to observability, then rethrow.
    reportError(err, { url, kind: "network" });
    throw err;
  }
  if (res.status === 401 && opts?.redirectOn401 !== false) {
    handleAuthExpired();
  }
  if (res.status >= 500) {
    reportError(new Error(`HTTP ${res.status} from ${url}`), { url, status: res.status });
  }
  return res;
}

/**
 * GET /api/v1/auth/me. Returns the parsed identity payload, or null when the
 * server says 401 (no / invalid / expired session). Throws only on network
 * failure or unexpected (5xx) responses so callers can distinguish "not
 * logged in" (null) from "backend down" (throw).
 */
export async function fetchAuthMe(): Promise<AuthMeResponse | null> {
  const res = await fetchWithAuth("/api/v1/auth/me", undefined, { redirectOn401: false });
  if (res.status === 401) return null;
  if (!res.ok) {
    throw new Error(`/auth/me failed: ${res.status}`);
  }
  return (await res.json()) as AuthMeResponse;
}

/** True iff authStore has resolved to an authenticated session. */
export function isAuthenticated(): boolean {
  return useAuthStore.getState().status === "authenticated";
}

export async function logout(): Promise<void> {
  let redirectTo = "/auth/login";
  try {
    const response = await fetchWithAuth("/api/v1/auth/logout", { method: "POST" }, {
      redirectOn401: false,
    });
    if (response.ok) {
      const body = (await response.json()) as { redirect_to: string };
      redirectTo = body.redirect_to;
    }
  } catch {
    // Network error — still clear local state + go to login.
  }
  clearDevToken();
  useAuthStore.getState().clear();
  window.location.href = redirectTo;
}
