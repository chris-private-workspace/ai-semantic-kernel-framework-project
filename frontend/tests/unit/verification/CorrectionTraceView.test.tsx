/**
 * File: frontend/tests/unit/verification/CorrectionTraceView.test.tsx
 * Purpose: Vitest tests for CorrectionTraceView (Sprint 57.11 US-4 §3.2).
 * Category: Frontend / tests / unit / verification
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-4
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.2)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, test, vi } from "vitest";

import { CorrectionTraceView } from "@/features/verification/components/CorrectionTraceView";
import { verificationService } from "@/features/verification/services/verificationService";
import type { CorrectionTraceResponse } from "@/features/verification/types";

function renderView(initialPath: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/verification/timeline" element={<CorrectionTraceView />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const SAMPLE_TRACE: CorrectionTraceResponse = {
  session_id: "abc-123",
  entries: [
    {
      id: 1,
      tenant_id: "t1",
      session_id: "abc-123",
      turn_index: 0,
      verifier_name: "pii",
      verifier_type: "rules_based",
      passed: true,
      score: 0.95,
      reason: null,
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: 1000,
    },
    {
      id: 2,
      tenant_id: "t1",
      session_id: "abc-123",
      turn_index: 0,
      verifier_name: "topic",
      verifier_type: "llm_judge",
      passed: false,
      score: null,
      reason: "off topic",
      suggested_correction: "stay focused",
      correction_attempt: 1,
      created_at_ms: 2000,
    },
    {
      id: 3,
      tenant_id: "t1",
      session_id: "abc-123",
      turn_index: 1,
      verifier_name: "pii",
      verifier_type: "rules_based",
      passed: true,
      score: 0.97,
      reason: null,
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: 3000,
    },
  ],
};

describe("CorrectionTraceView (Sprint 57.11 US-4 §3.2)", () => {
  test("renders timeline grouped by turn_index when sessionId provided", async () => {
    vi.spyOn(verificationService, "fetchCorrectionTrace").mockResolvedValueOnce(SAMPLE_TRACE);

    renderView("/verification/timeline?session_id=abc-123");

    await waitFor(() => expect(screen.getByTestId("correction-trace")).toBeInTheDocument());
    expect(screen.getByTestId("turn-0")).toBeInTheDocument();
    expect(screen.getByTestId("turn-1")).toBeInTheDocument();
    expect(screen.getByTestId("entry-2")).toHaveTextContent("off topic");
    expect(screen.getByTestId("entry-2")).toHaveTextContent("Suggested: stay focused");
    expect(screen.getByTestId("entry-2")).toHaveTextContent("(correction #1)");
  });

  test("shows empty state when 404 (no entries for session)", async () => {
    vi.spyOn(verificationService, "fetchCorrectionTrace").mockRejectedValueOnce(
      new Error("No verification entries for this session."),
    );

    renderView("/verification/timeline?session_id=ghost");

    await waitFor(() => expect(screen.getByTestId("trace-empty")).toBeInTheDocument());
  });

  test("shows no-session state when session_id query param missing", () => {
    renderView("/verification/timeline");

    expect(screen.getByTestId("trace-no-session")).toBeInTheDocument();
    expect(screen.queryByTestId("correction-trace")).not.toBeInTheDocument();
  });
});
