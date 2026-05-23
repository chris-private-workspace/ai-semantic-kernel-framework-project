/**
 * File: frontend/tests/unit/components/ui/radix.test.tsx
 * Purpose: Unit tests for the Radix-based ui primitives — Dialog only.
 * Category: Frontend / tests / unit / components / ui
 * Scope: Phase 57 / Sprint 57.13 US-B3 → Sprint 57.30 Day 5 (DropdownMenu drop)
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 5 — drop DropdownMenu test block + import (orphan cleanup after UserMenu Radix-drop)
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 5)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../../../../src/components/ui/dialog";

describe("components/ui — Dialog", () => {
  it("does not render content when closed", () => {
    render(
      <Dialog open={false}>
        <DialogContent>
          <DialogTitle>Hidden</DialogTitle>
        </DialogContent>
      </Dialog>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("renders content + title + footer when open", () => {
    render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review approval</DialogTitle>
          </DialogHeader>
          <DialogFooter>
            <button>Approve</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Review approval")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
  });

  it("ESC fires onOpenChange(false) in controlled mode", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    render(
      <Dialog open onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogTitle>X</DialogTitle>
        </DialogContent>
      </Dialog>,
    );
    await user.keyboard("{Escape}");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("the built-in close (X) button fires onOpenChange(false)", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    render(
      <Dialog open onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogTitle>X</DialogTitle>
        </DialogContent>
      </Dialog>,
    );
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
