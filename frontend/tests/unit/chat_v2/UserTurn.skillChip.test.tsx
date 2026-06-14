/**
 * File: frontend/tests/unit/chat_v2/UserTurn.skillChip.test.tsx
 * Purpose: Vitest render coverage for the Sprint 57.116 user-turn force-load skill chip.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.116 (Skills Inspector affordance)
 *
 * Description:
 *   UserTurn renders a "⚡ {skill}" .route-pill chip when the turn carries a
 *   force-loaded skill (stamped from the server-confirmed loop_start.active_skill);
 *   absent → no chip. Mirrors the existing injected-tag .route-pill pattern.
 *
 * Modification History:
 *   - 2026-06-14: Initial creation (Sprint 57.116)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, test } from "vitest";

import { useAuthStore } from "@/features/auth/store/authStore";
import { UserTurn } from "@/features/chat_v2/components/turns/UserTurn";
import type { UserTurn as UserTurnType } from "@/features/chat_v2/types";

function seedAuth(): void {
  useAuthStore.setState({
    status: "authenticated",
    user: { id: "u-1", email: "jamie@acme.test", display_name: "Jamie Liu" },
    tenant: { id: "t-1", name: "Acme", code: "acme" },
    roles: ["operator"],
  });
}

const base = (extra: Partial<UserTurnType> = {}): UserTurnType => ({
  role: "user",
  id: "t_u1",
  at: "10:42:18",
  text: "write release notes",
  ...extra,
});

describe("UserTurn — force-load skill chip (Sprint 57.116)", () => {
  beforeEach(seedAuth);

  test("renders a ⚡ skill chip when activeSkill is set", () => {
    render(<UserTurn turn={base({ activeSkill: "release-notes" })} />);
    const chip = screen.getByTestId("user-turn-skill-chip");
    expect(chip).toHaveTextContent("release-notes");
    expect(chip).toHaveAttribute("title", "Skill: release-notes");
  });

  test("renders no chip when activeSkill is unset", () => {
    render(<UserTurn turn={base()} />);
    expect(screen.queryByTestId("user-turn-skill-chip")).not.toBeInTheDocument();
  });
});
