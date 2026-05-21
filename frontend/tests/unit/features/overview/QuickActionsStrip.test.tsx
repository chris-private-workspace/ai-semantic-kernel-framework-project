/**
 * File: frontend/tests/unit/features/overview/QuickActionsStrip.test.tsx
 * Purpose: Vitest coverage for QuickActionsStrip — 4 buttons rendered + navigation.
 * Category: Frontend / Tests / features / overview
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { QuickActionsStrip } from "@/features/overview/components/QuickActionsStrip";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("QuickActionsStrip", () => {
  it("renders exactly 4 action buttons", () => {
    render(wrap(<QuickActionsStrip />));
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(4);
  });

  it("renders the New Chat, Review, Tenants, and Verification labels", () => {
    render(wrap(<QuickActionsStrip />));
    expect(screen.getByText(/new chat session/i)).toBeInTheDocument();
    expect(screen.getByText(/review approvals/i)).toBeInTheDocument();
    expect(screen.getByText(/tenants console/i)).toBeInTheDocument();
    expect(screen.getByText(/verification log/i)).toBeInTheDocument();
  });

  it("renders sub-labels for each action", () => {
    render(wrap(<QuickActionsStrip />));
    expect(screen.getByText(/start a chat/i)).toBeInTheDocument();
    expect(screen.getByText(/hitl queue/i)).toBeInTheDocument();
  });

  it("navigates on button click without throwing", async () => {
    const user = userEvent.setup();
    render(wrap(<QuickActionsStrip />));
    const buttons = screen.getAllByRole("button");
    // clicking any button should not throw
    await user.click(buttons[0]);
    await user.click(buttons[1]);
    await user.click(buttons[2]);
    await user.click(buttons[3]);
  });
});
