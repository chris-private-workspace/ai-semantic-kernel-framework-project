/**
 * File: frontend/tests/unit/components/ui/radix.test.tsx
 * Purpose: Unit tests for the Radix-based ui primitives — Dialog + DropdownMenu.
 * Category: Frontend / tests / unit / components / ui
 * Scope: Phase 57 / Sprint 57.13 US-B3
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 5)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../../../../src/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../../../../src/components/ui/dropdown-menu";

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

describe("components/ui — DropdownMenu", () => {
  function Harness({ onSelect }: { onSelect: () => void }) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger aria-label="open menu">Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Account</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={onSelect}>Sign out</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  it("does not render the menu until the trigger is clicked", () => {
    render(<Harness onSelect={vi.fn()} />);
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("opening shows menu + label + menuitem", async () => {
    const user = userEvent.setup();
    render(<Harness onSelect={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "open menu" }));
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.getByText("Account")).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Sign out" })).toBeInTheDocument();
  });

  it("clicking an item fires onSelect and closes the menu", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<Harness onSelect={onSelect} />);
    await user.click(screen.getByRole("button", { name: "open menu" }));
    await user.click(screen.getByRole("menuitem", { name: "Sign out" }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("trigger reflects open state via aria-expanded", async () => {
    const user = userEvent.setup();
    render(<Harness onSelect={vi.fn()} />);
    const trigger = screen.getByRole("button", { name: "open menu" });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    await user.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
  });

  it("works inside a stateful host (controlled-ish open via re-render)", async () => {
    const user = userEvent.setup();
    function StatefulHost() {
      const [n, setN] = useState(0);
      return (
        <>
          <span data-testid="count">{n}</span>
          <DropdownMenu>
            <DropdownMenuTrigger aria-label="open">trigger</DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onSelect={() => setN((v) => v + 1)}>Increment</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </>
      );
    }
    render(<StatefulHost />);
    await user.click(screen.getByRole("button", { name: "open" }));
    await user.click(screen.getByRole("menuitem", { name: "Increment" }));
    expect(screen.getByTestId("count")).toHaveTextContent("1");
  });
});
