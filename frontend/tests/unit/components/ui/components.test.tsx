/**
 * File: frontend/tests/unit/components/ui/components.test.tsx
 * Purpose: Unit tests for the design-system component layer (components/ui/*).
 * Category: Frontend / tests / unit / components / ui
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Badge } from "../../../../src/components/ui/badge";
import { Button } from "../../../../src/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../src/components/ui/card";
import { EmptyState } from "../../../../src/components/ui/empty-state";
import { ErrorRetry } from "../../../../src/components/ui/error-retry";
import { CardSkeleton, Skeleton, TableSkeleton } from "../../../../src/components/ui/skeleton";

describe("components/ui — skeleton", () => {
  it("Skeleton renders a pulsing box + merges className", () => {
    const { container } = render(<Skeleton className="h-4 w-20" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("animate-pulse");
    expect(el.className).toContain("h-4");
    expect(el.className).toContain("w-20");
  });

  it("TableSkeleton renders rows × cols cells (default 5×6)", () => {
    const { container } = render(<TableSkeleton />);
    expect(container.querySelectorAll("tr")).toHaveLength(5);
    expect(container.querySelectorAll("td")).toHaveLength(30);
  });

  it("TableSkeleton respects custom rows/cols", () => {
    const { container } = render(<TableSkeleton rows={2} cols={3} />);
    expect(container.querySelectorAll("tr")).toHaveLength(2);
    expect(container.querySelectorAll("td")).toHaveLength(6);
  });

  it("CardSkeleton renders `count` cards (default 3)", () => {
    const { container } = render(<CardSkeleton />);
    // 3 outer card divs, each with 3 inner Skeleton bars
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(9);
  });
});

describe("components/ui — Button", () => {
  it("renders a <button> with default classes", () => {
    render(<Button>Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.tagName).toBe("BUTTON");
    expect(btn.className).toContain("bg-primary");
  });

  it("variant=outline / size=sm change classes", () => {
    render(
      <Button variant="outline" size="sm">
        X
      </Button>,
    );
    const btn = screen.getByRole("button", { name: "X" });
    expect(btn.className).toContain("border");
    expect(btn.className).toContain("h-8");
  });

  it("asChild renders the child element with button classes", () => {
    render(
      <Button asChild>
        <a href="/somewhere">Link</a>
      </Button>,
    );
    const link = screen.getByRole("link", { name: "Link" });
    expect(link.className).toContain("bg-primary");
  });

  it("forwards onClick", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

describe("components/ui — Badge", () => {
  it("default variant", () => {
    const { container } = render(<Badge>OK</Badge>);
    expect((container.firstChild as HTMLElement).className).toContain("bg-primary");
  });

  it("risk-critical variant maps to mockup --risk-critical token", () => {
    // FIX-017: assertion updated from Sprint 53.5 hex sentinel `#b71c1c` to
    // the mockup `var(--risk-critical)` token; styles-mockup.css L23 owns
    // the oklch value (≈ #B71C1C; same visual intent).
    const { container } = render(<Badge variant="risk-critical">CRITICAL</Badge>);
    expect((container.firstChild as HTMLElement).className).toContain("var(--risk-critical)");
  });
});

describe("components/ui — Card", () => {
  it("composes header/title/content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>My Card</CardTitle>
        </CardHeader>
        <CardContent>body</CardContent>
      </Card>,
    );
    expect(screen.getByText("My Card").tagName).toBe("H3");
    expect(screen.getByText("body")).toBeInTheDocument();
  });
});

describe("components/ui — EmptyState", () => {
  it("renders title + message + action", () => {
    render(
      <EmptyState
        title="No tenants"
        message="adjust filters"
        action={<Button variant="outline">Reset</Button>}
      />,
    );
    expect(screen.getByText("No tenants")).toBeInTheDocument();
    expect(screen.getByText("adjust filters")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
  });

  it("renders title only when no message/action", () => {
    render(<EmptyState title="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("components/ui — ErrorRetry", () => {
  it("shows default headline + error message + Retry button", () => {
    render(<ErrorRetry error={new Error("boom")} onRetry={vi.fn()} />);
    expect(screen.getByText("Failed to load data")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("custom message + 'Unknown error' fallback when no error", () => {
    render(<ErrorRetry message="Could not load report" onRetry={vi.fn()} />);
    expect(screen.getByText("Could not load report")).toBeInTheDocument();
    expect(screen.getByText("Unknown error")).toBeInTheDocument();
  });

  it("Retry button calls onRetry", () => {
    const onRetry = vi.fn();
    render(<ErrorRetry onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
