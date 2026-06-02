/**
 * File: frontend/tests/unit/chat_v2/components/HandoffBanner.test.tsx
 * Purpose: Vitest coverage for HandoffBanner — render target/reason + dismiss.
 * Category: Frontend / Tests / chat_v2 / components / unit
 * Scope: Phase 57 / Sprint 57.69 (A-3b slice 2 — FE session-pivot + banner)
 *
 * Description:
 *   - Renders nothing when chatStore.handoffBanner is null
 *   - Renders target agent + reason when handoffBanner is set
 *   - Dismiss button calls dismissHandoffBanner (banner disappears)
 *
 * Created: 2026-06-02 (Sprint 57.69)
 *
 * Modification History (newest-first):
 *   - 2026-06-02: Initial creation (Sprint 57.69 A-3b slice 2)
 *
 * Related:
 *   - frontend/src/features/chat_v2/components/HandoffBanner.tsx
 *   - frontend/src/features/chat_v2/store/chatStore.ts
 *   - sprint-57-69-plan.md §3.4 (US-4)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { HandoffBanner } from "@/features/chat_v2/components/HandoffBanner";
import { useChatStore } from "@/features/chat_v2/store/chatStore";

describe("HandoffBanner (Sprint 57.69)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  it("renders nothing when handoffBanner is null", () => {
    const { container } = render(<HandoffBanner />);
    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId("handoff-banner")).not.toBeInTheDocument();
  });

  it("renders target agent + reason when handoffBanner is set", () => {
    useChatStore
      .getState()
      .pivotSession("sess-child", { targetAgent: "researcher", reason: "needs deep research" });
    render(<HandoffBanner />);
    expect(screen.getByTestId("handoff-banner")).toBeInTheDocument();
    // Target agent appears in the badge copy (繁中 "已交棒給 {agent}").
    expect(screen.getByText(/researcher/)).toBeInTheDocument();
    // Reason rendered in the body.
    expect(screen.getByText(/needs deep research/)).toBeInTheDocument();
  });

  it("dismiss button calls dismissHandoffBanner (banner disappears)", () => {
    useChatStore
      .getState()
      .pivotSession("sess-child", { targetAgent: "reviewer", reason: "policy review" });
    render(<HandoffBanner />);
    expect(screen.getByTestId("handoff-banner")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("handoff-banner-dismiss"));

    expect(useChatStore.getState().handoffBanner).toBeNull();
    expect(screen.queryByTestId("handoff-banner")).not.toBeInTheDocument();
  });
});
