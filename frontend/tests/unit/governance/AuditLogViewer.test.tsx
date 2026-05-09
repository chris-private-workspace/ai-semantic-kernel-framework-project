/**
 * File: frontend/tests/unit/governance/AuditLogViewer.test.tsx
 * Purpose: Vitest tests for AuditLogViewer (Sprint 57.9 US-4) — filter form + paginated table.
 * Category: Frontend / tests / unit / governance
 * Scope: Phase 57 / Sprint 57.9 US-4 Day 3
 *
 * Description:
 *   Renders AuditLogViewer wrapped in QueryClientProvider; spies auditService
 *   to control responses; asserts filter form fields render + empty state +
 *   one-row render path. Per D-PRE-10 lesson: use waitFor + delta assertions
 *   to tolerate TanStack v5 internal mount-time refetches.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-4)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-4)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { AuditLogViewer } from "@/features/governance/components/AuditLogViewer";
import { auditService } from "@/features/governance/services/auditService";
import type { AuditLogPage } from "@/features/governance/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const EMPTY_PAGE: AuditLogPage = {
  items: [],
  has_more: false,
  next_offset: null,
  page_size: 50,
};

const ONE_ROW_PAGE: AuditLogPage = {
  items: [
    {
      id: 7,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      user_id: "22222222-2222-4222-8222-222222222222",
      session_id: null,
      operation: "tool_executed",
      resource_type: "tool",
      resource_id: "salesforce_query",
      operation_data: {},
      operation_result: "success",
      previous_log_hash: "0000",
      current_log_hash: "abcdef1234567890",
      timestamp_ms: Date.UTC(2026, 4, 9, 10, 0, 0),
    },
  ],
  has_more: true,
  next_offset: 50,
  page_size: 50,
};

describe("AuditLogViewer (Sprint 57.9 US-4)", () => {
  test("renders the 4 filter inputs and AuditChainBadge button", async () => {
    vi.spyOn(auditService, "fetchAuditLog").mockResolvedValue(EMPTY_PAGE);

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditLogViewer />
      </Wrapper>,
    );

    expect(screen.getByText(/Audit Log$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Operation/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Resource type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/User ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/From \(timestamp\)/i)).toBeInTheDocument();
    // AuditChainBadge mounted top-right
    expect(screen.getByRole("button", { name: /Verify chain/i })).toBeInTheDocument();
  });

  test("empty state shows Reset filters button when no entries", async () => {
    vi.spyOn(auditService, "fetchAuditLog").mockResolvedValue(EMPTY_PAGE);

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditLogViewer />
      </Wrapper>,
    );

    await waitFor(() =>
      expect(screen.getByText(/No audit log entries/i)).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: /Reset filters/i })).toBeInTheDocument();
  });

  test("renders one row + pagination footer with Next enabled when has_more=true", async () => {
    vi.spyOn(auditService, "fetchAuditLog").mockResolvedValue(ONE_ROW_PAGE);

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <AuditLogViewer />
      </Wrapper>,
    );

    await waitFor(() => expect(screen.getByText("tool_executed")).toBeInTheDocument());
    expect(screen.getByText(/Showing 1.*1/i)).toBeInTheDocument();
    expect(screen.getByText(/more available/i)).toBeInTheDocument();

    const prevBtn = screen.getByRole("button", { name: /^Prev$/ });
    const nextBtn = screen.getByRole("button", { name: /^Next$/ });
    expect(prevBtn).toBeDisabled(); // offset = 0
    expect(nextBtn).not.toBeDisabled(); // has_more = true
  });
});
