/**
 * File: frontend/src/features/auth/store/authStore.ts
 * Purpose: Single source of truth for the SPA's authentication state.
 * Category: Frontend / auth / store (Zustand)
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Description:
 *   Holds {status, user, tenant, roles}. `status` starts "unknown"; App.tsx
 *   runs bootstrap() once on mount, which calls GET /api/v1/auth/me and
 *   transitions to "authenticated" (payload) or "anonymous" (401). Route
 *   gates (<RequireAuth>) + the shell read this — never localStorage.
 *
 *   Why a store (not a one-shot fetch in App): the user/tenant/roles are
 *   needed by UserMenu, route gates, and tenant-scoped pages (Sprint 57.13
 *   US-A2 reads authStore.tenant.id instead of a URL ?tenant_id=). Zustand's
 *   selective subscriptions keep those re-renders cheap.
 *
 * Created: 2026-05-10 (Sprint 57.13 US-A1)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Initial creation (Sprint 57.13 US-A1)
 *
 * Related:
 *   - frontend/src/features/auth/services/authService.ts (fetchAuthMe)
 *   - frontend/src/features/auth/components/RequireAuth.tsx (gate consumer)
 *   - frontend/src/App.tsx (bootstrap on mount)
 *   - backend/src/api/v1/auth.py GET /auth/me (AuthMeResponse shape)
 */

import { create } from "zustand";

import { fetchAuthMe } from "../services/authService";

export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
}

export interface AuthTenant {
  id: string;
  name: string;
  code: string;
}

/** Mirrors backend AuthMeResponse (api/v1/auth.py). */
export interface AuthMeResponse {
  user: AuthUser;
  tenant: AuthTenant;
  roles: string[];
}

export type AuthStatus = "unknown" | "authenticated" | "anonymous";

interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  tenant: AuthTenant | null;
  roles: string[];
  /** Fetch /auth/me and resolve status. Safe to call repeatedly. */
  bootstrap: () => Promise<void>;
  /** Drop session state → "anonymous" (used by logout). */
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: "unknown",
  user: null,
  tenant: null,
  roles: [],
  bootstrap: async () => {
    try {
      const me = await fetchAuthMe();
      if (me) {
        set({ status: "authenticated", user: me.user, tenant: me.tenant, roles: me.roles });
      } else {
        set({ status: "anonymous", user: null, tenant: null, roles: [] });
      }
    } catch {
      // Backend unreachable — treat as anonymous so the app still renders
      // (route gates send the user to /auth/login rather than hanging on a
      // spinner forever). The login page surfaces backend errors separately.
      set({ status: "anonymous", user: null, tenant: null, roles: [] });
    }
  },
  clear: () => set({ status: "anonymous", user: null, tenant: null, roles: [] }),
}));
