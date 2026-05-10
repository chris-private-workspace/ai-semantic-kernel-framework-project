/**
 * File: frontend/src/components/UserMenu.tsx
 * Purpose: Header avatar dropdown — show current user (authStore) + role badges + sign out.
 * Category: Frontend / components / auth-aware
 * Scope: Phase 57 / Sprint 57.8 US-2 → Sprint 57.13 US-A1 (authStore) → Sprint 57.13 US-B3 (Radix DropdownMenu)
 *
 * Description:
 *   Avatar circle in AppShellV2's header right slot. Click → menu showing the
 *   signed-in user (display name / email) + role <Badge>s + Sign out (calls
 *   logout() — backend /auth/logout + clear authStore + redirect to vendor signout).
 *   Renders null unless authStore.status === "authenticated".
 *
 *   Sprint 57.13 US-B3: replaced the hand-rolled popover (useState/useRef/useEffect
 *   for outside-click + ESC) with components/ui <DropdownMenu> (Radix) — focus,
 *   keyboard nav, ESC/outside-click close, and role="menu"/"menuitem" come for free.
 *   A locale switcher item slot is reserved for US-B5 (i18n).
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 2)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B3 — swap custom popover → <DropdownMenu>; add role badges
 *   - 2026-05-10: Sprint 57.13 US-A1 — read authStore.user instead of decoding the JWT; sign out via logout()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-2)
 *
 * Related:
 *   - frontend/src/components/ui/dropdown-menu.tsx (Radix wrapper)
 *   - frontend/src/features/auth/store/authStore.ts (user + status + roles)
 *   - frontend/src/features/auth/services/authService.ts (logout)
 *   - frontend/src/components/AppShellV2.tsx (host via userMenu prop slot)
 */

import { LogOut, User as UserIcon } from "lucide-react";
import type { FC } from "react";

import {
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui";
import { logout } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";
import { cn } from "@/lib/utils";

export const UserMenu: FC = () => {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const roles = useAuthStore((s) => s.roles);

  if (status !== "authenticated" || user === null) return null;

  const label = user.display_name?.trim() || user.email;
  const initial = label ? label.charAt(0).toUpperCase() : "?";
  const showEmailLine = Boolean(user.display_name?.trim()) && user.email !== label;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          "inline-flex h-8 w-8 items-center justify-center rounded-full",
          "bg-primary text-primary-foreground text-sm font-medium",
          "hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
        aria-label="User menu"
      >
        {initial === "?" ? <UserIcon size={16} /> : initial}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" aria-label="User menu options">
        <DropdownMenuLabel className="font-normal">
          <div className="text-xs text-muted-foreground">Signed in as</div>
          <div className="truncate text-sm font-medium text-foreground">{label}</div>
          {showEmailLine && (
            <div className="truncate text-xs text-muted-foreground">{user.email}</div>
          )}
          {roles.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {roles.map((r) => (
                <Badge key={r} variant="outline">
                  {r}
                </Badge>
              ))}
            </div>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void logout()}>
          <LogOut size={14} />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
