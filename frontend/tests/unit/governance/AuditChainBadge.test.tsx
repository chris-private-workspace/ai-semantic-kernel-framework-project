/**
 * File: frontend/tests/unit/governance/AuditChainBadge.test.tsx
 * Purpose: Vitest tests for AuditChainBadge (Sprint 57.9 US-5) — manual verify trigger + 3 result states.
 * Category: Frontend / tests / unit / governance
 * Scope: Phase 57 / Sprint 57.9 US-5 Day 3
 *
 * Description:
 *   Asserts: idle render (no result yet), valid state (✓ + total entries),
 *   broken state (✗ + broken_at_id), and error surfacing. Per D-PRE-10:
 *   delta-tolerant assertions where applicable.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-5)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-5)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { AuditChainBadge } from "@/features/governance/components/AuditChainBadge";
import { auditService } from "@/features/governance/services/auditService";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("AuditChainBadge (Sprint 57.9 US-5)", () => {
  test("idle render shows Verify chain button + no result badge", () => {
    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditChainBadge />
      </Wrapper>,
    );

    expect(screen.getByRole("button", { name: /Verify chain/i })).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  test("click triggers verifyChain + shows valid badge on success", async () => {
    vi.spyOn(auditService, "verifyChain").mockResolvedValueOnce({
      valid: true,
      broken_at_id: null,
      total_entries: 1234,
    });

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditChainBadge />
      </Wrapper>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Verify chain/i }));
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.getByRole("status")).toHaveTextContent(/Valid/i);
    expect(screen.getByRole("status")).toHaveTextContent(/1234 entries/);
  });

  test("broken chain renders ✗ + broken_at_id", async () => {
    vi.spyOn(auditService, "verifyChain").mockResolvedValueOnce({
      valid: false,
      broken_at_id: 87,
      total_entries: 200,
    });

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditChainBadge />
      </Wrapper>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Verify chain/i }));
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.getByRole("status")).toHaveTextContent(/Broken at id=87/i);
    expect(screen.getByRole("status")).toHaveTextContent(/200 entries/);
  });

  test("error from service surfaces in alert role with HTTP detail", async () => {
    vi.spyOn(auditService, "verifyChain").mockRejectedValueOnce(
      new Error("HTTP 500: chain walker crashed"),
    );

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditChainBadge />
      </Wrapper>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Verify chain/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent(/Verify failed/i);
    expect(screen.getByRole("alert")).toHaveTextContent(/chain walker crashed/i);
  });
});
