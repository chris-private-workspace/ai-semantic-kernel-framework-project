/**
 * File: frontend/tests/unit/verification/VerificationList.test.tsx
 * Purpose: Vitest tests for VerificationList (Sprint 57.11 US-4 §3.1).
 * Category: Frontend / tests / unit / verification
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-4
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.1)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, test, vi } from "vitest";

import { VerificationList } from "@/features/verification/components/VerificationList";
import { verificationService } from "@/features/verification/services/verificationService";
import type { VerificationLogPage } from "@/features/verification/types";

function renderList() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/verification/recent"]}>
        <Routes>
          <Route path="/verification/recent" element={<VerificationList />} />
          <Route
            path="/verification/timeline"
            element={<div data-testid="timeline-page">timeline</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const SAMPLE_PAGE: VerificationLogPage = {
  items: [
    {
      id: 7,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      session_id: "22222222-2222-4222-8222-222222222222",
      turn_index: 0,
      verifier_name: "pii_redaction",
      verifier_type: "rules_based",
      passed: true,
      score: 0.99,
      reason: null,
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: Date.UTC(2026, 4, 10, 8, 0, 0),
    },
    {
      id: 8,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      session_id: "33333333-3333-4333-8333-333333333333",
      turn_index: 0,
      verifier_name: "off_topic",
      verifier_type: "llm_judge",
      passed: false,
      score: null,
      reason: "drifted from original topic",
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: Date.UTC(2026, 4, 10, 8, 5, 0),
    },
  ],
  total: 2,
  has_more: false,
  next_offset: null,
  page_size: 50,
};

describe("VerificationList (Sprint 57.11 US-4 §3.1)", () => {
  test("renders filter form + table on success", async () => {
    vi.spyOn(verificationService, "fetchVerificationRecent").mockResolvedValueOnce(SAMPLE_PAGE);

    renderList();

    await waitFor(() => expect(screen.getByTestId("verification-table")).toBeInTheDocument());
    expect(screen.getByTestId("filter-session-id")).toBeInTheDocument();
    expect(screen.getByTestId("filter-verifier-type")).toBeInTheDocument();
    expect(screen.getByTestId("filter-passed")).toBeInTheDocument();
    expect(screen.getByText("pii_redaction")).toBeInTheDocument();
    expect(screen.getByText("off_topic")).toBeInTheDocument();
    expect(screen.getByText("drifted from original topic")).toBeInTheDocument();
  });

  test("empty state shows Reset button when no items", async () => {
    vi.spyOn(verificationService, "fetchVerificationRecent").mockResolvedValueOnce({
      ...SAMPLE_PAGE,
      items: [],
      total: 0,
    });

    renderList();

    await waitFor(() =>
      expect(screen.getByText("No verification entries match the filters.")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("empty-reset")).toBeInTheDocument();
  });

  test("clicking row navigates to /verification/timeline?session_id=...", async () => {
    vi.spyOn(verificationService, "fetchVerificationRecent").mockResolvedValueOnce(SAMPLE_PAGE);

    renderList();

    await waitFor(() => expect(screen.getByTestId("row-7")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("row-7"));

    await waitFor(() => expect(screen.getByTestId("timeline-page")).toBeInTheDocument());
  });
});
