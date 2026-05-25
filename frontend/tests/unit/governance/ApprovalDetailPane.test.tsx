/**
 * File: frontend/tests/unit/governance/ApprovalDetailPane.test.tsx
 * Purpose: Vitest coverage for ApprovalDetailPane — empty state + populated KvRows + Approve/Reject wiring.
 * Category: Frontend / Tests / governance / unit
 * Scope: Phase 57 / Sprint 57.40 Day 2 (mockup-fidelity rebuild)
 *
 * Description:
 *   - empty placeholder when approval=null
 *   - request_id mono + 7 KvRow labels rendered when approval is set
 *   - Approve & continue button → onApprove
 *   - Reject button → onReject
 *   - Approve-with-edits + Escalate buttons are AP-2 stubs (alert)
 *
 * Created: 2026-05-25 (Sprint 57.40 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.40 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApprovalDetailPane } from "@/features/governance/components/ApprovalDetailPane";
import type { ApprovalSummary } from "@/features/governance/types";

const SAMPLE_APPROVAL: ApprovalSummary = {
  request_id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  session_id: "33333333-3333-4333-8333-333333333333",
  requester: "user-a",
  risk_level: "HIGH",
  payload: {
    tool_name: "salesforce_query",
    reason: "PII access requested for incident response",
    tool_arguments: { table: "leads", columns: ["email", "phone"] },
  },
  sla_deadline: new Date(Date.now() + 5 * 60_000).toISOString(),
  context_snapshot: {},
};

describe("ApprovalDetailPane (Sprint 57.40)", () => {
  beforeEach(() => {
    // window.alert is invoked for AP-2 stub buttons; jsdom default throws
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders empty placeholder when approval is null", () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(
      <ApprovalDetailPane approval={null} onApprove={onApprove} onReject={onReject} />,
    );
    expect(
      screen.getByText(/select an approval from the list to view details/i),
    ).toBeInTheDocument();
    // No Approve / Reject buttons in empty state
    expect(screen.queryByRole("button", { name: /approve & continue/i })).toBeNull();
  });

  it("renders request_id + 7 KvRow labels + payload + rationale when approval is set", () => {
    render(
      <ApprovalDetailPane
        approval={SAMPLE_APPROVAL}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    );
    // request_id mono header
    expect(screen.getByText(SAMPLE_APPROVAL.request_id)).toBeInTheDocument();
    // 7 KvRow labels (verbatim mockup)
    expect(screen.getByText("tool")).toBeInTheDocument();
    expect(screen.getByText("risk")).toBeInTheDocument();
    expect(screen.getByText("policy")).toBeInTheDocument();
    expect(screen.getByText("scope")).toBeInTheDocument();
    expect(screen.getByText("operator")).toBeInTheDocument();
    expect(screen.getByText("age")).toBeInTheDocument();
    expect(screen.getByText("SLA remaining")).toBeInTheDocument();
    // tool name + rationale + requester text shown
    expect(screen.getByText("salesforce_query")).toBeInTheDocument();
    // payload.reason appears twice: once in Card subtitle (sessionTitle slice 80),
    // once in Agent rationale field — both surfaces are intentional per mockup
    expect(
      screen.getAllByText(/PII access requested for incident response/i).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("user-a")).toBeInTheDocument();
  });

  it("Approve & continue button invokes onApprove", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(
      <ApprovalDetailPane
        approval={SAMPLE_APPROVAL}
        onApprove={onApprove}
        onReject={onReject}
      />,
    );
    await user.click(screen.getByRole("button", { name: /approve & continue/i }));
    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(onReject).not.toHaveBeenCalled();
  });

  it("Reject button invokes onReject", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(
      <ApprovalDetailPane
        approval={SAMPLE_APPROVAL}
        onApprove={onApprove}
        onReject={onReject}
      />,
    );
    await user.click(screen.getByRole("button", { name: /^reject$/i }));
    expect(onReject).toHaveBeenCalledTimes(1);
    expect(onApprove).not.toHaveBeenCalled();
  });

  it("Approve-with-edits and Escalate buttons are AP-2 alert stubs", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(
      <ApprovalDetailPane
        approval={SAMPLE_APPROVAL}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: /approve with edits/i }));
    await user.click(screen.getByRole("button", { name: /escalate to l2/i }));
    expect(alertSpy).toHaveBeenCalledTimes(2);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[1]![0]).toMatch(/backend gap/i);
  });
});
