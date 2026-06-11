/**
 * File: frontend/tests/unit/chat_v2/HITLTurn.resume.test.tsx
 * Purpose: Vitest coverage for HITLTurn's pause-resume trigger + the 57.100 verification reject-with-note.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.88 (resume) + Sprint 57.100 (verification reject UI)
 *
 * Description:
 *   HITLTurn's Approve button records the decision (governanceService.decide) and,
 *   ONLY for the deferred-pause flow (stopReason === "awaiting_approval"), drives
 *   the client resume (useLoopEventStream.resume). Sprint 57.100: a verification
 *   pause (kind === "verification") reveals a coaching-note input on Reject and
 *   ALSO resumes (the backend coaches one human-guided turn — A2); every other
 *   kind keeps terminate-on-reject (no note, no resume). Asserts:
 *     - approve + awaiting_approval → decide("approved") + resume() fired
 *     - approve + non-paused stopReason → decide() fired, resume() NOT fired
 *     - tool reject → decide("rejected") + resume() NOT fired + no note input
 *     - verification reject → reveals the note input (no immediate decide)
 *     - verification reject-with-note → decide("rejected", note) + resume() fired
 *     - verification meta row reads "verification" (kind-aware)
 *
 * Created: 2026-06-08 (Sprint 57.88 Day 3)
 *
 * Modification History:
 *   - 2026-06-10: Sprint 57.100 — +verification reject-with-note cases; decide now 3-arg (note)
 *   - 2026-06-08: Initial creation (Sprint 57.88 Day 3 / US-5)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HITLTurn } from "@/features/chat_v2/components/turns/HITLTurn";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { HITLTurn as HITLTurnType } from "@/features/chat_v2/types";

const { decideSpy, resumeSpy } = vi.hoisted(() => ({
  decideSpy: vi.fn(),
  resumeSpy: vi.fn(),
}));

vi.mock("@/features/governance/services/governanceService", () => ({
  governanceService: { decide: decideSpy },
}));

vi.mock("@/features/chat_v2/hooks/useLoopEventStream", () => ({
  useLoopEventStream: () => ({
    send: vi.fn(),
    resume: resumeSpy,
    cancel: vi.fn(),
    isRunning: false,
  }),
}));

const makeTurn = (overrides: Partial<HITLTurnType> = {}): HITLTurnType => ({
  role: "hitl",
  id: "h_1",
  at: "2026-06-08T00:00:00Z",
  title: "Approval required: HIGH",
  severity: "risk-high",
  tool: "echo_tool",
  kind: "tool",
  payload: "—",
  rationale: "—",
  approvalRequestId: "ar-1",
  decision: null,
  countdownSec: null,
  ...overrides,
});

describe("HITLTurn — durable pause-resume trigger (Sprint 57.88)", () => {
  beforeEach(() => {
    decideSpy.mockResolvedValue(undefined);
    resumeSpy.mockReset();
  });

  afterEach(() => {
    useChatStore.getState().reset();
    vi.clearAllMocks();
  });

  it("approve while deferred-paused → decide(approved) + resume() fired", async () => {
    useChatStore.setState({ stopReason: "awaiting_approval" });
    render(<HITLTurn turn={makeTurn()} />);

    await userEvent.click(screen.getByTestId("approve-btn"));

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith("ar-1", "approved", undefined));
    await waitFor(() => expect(resumeSpy).toHaveBeenCalledTimes(1));
  });

  it("approve when NOT deferred-paused → decide fired but resume() guarded off", async () => {
    useChatStore.setState({ stopReason: "end_turn" });
    render(<HITLTurn turn={makeTurn()} />);

    await userEvent.click(screen.getByTestId("approve-btn"));

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith("ar-1", "approved", undefined));
    expect(resumeSpy).not.toHaveBeenCalled();
  });

  it("tool reject → decide(rejected) + resume() NOT fired + no note input", async () => {
    useChatStore.setState({ stopReason: "awaiting_approval" });
    render(<HITLTurn turn={makeTurn()} />);

    await userEvent.click(screen.getByTestId("reject-btn"));

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith("ar-1", "rejected", undefined));
    expect(resumeSpy).not.toHaveBeenCalled();
    expect(screen.queryByTestId("reject-note")).not.toBeInTheDocument();
  });
});

describe("HITLTurn — verification reject-with-note (Sprint 57.100)", () => {
  beforeEach(() => {
    decideSpy.mockResolvedValue(undefined);
    resumeSpy.mockReset();
  });

  afterEach(() => {
    useChatStore.getState().reset();
    vi.clearAllMocks();
  });

  it("verification reject reveals a coaching-note input (no immediate decide/resume)", async () => {
    useChatStore.setState({ stopReason: "awaiting_approval" });
    render(<HITLTurn turn={makeTurn({ kind: "verification" })} />);

    expect(screen.queryByTestId("reject-note")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("reject-btn"));

    expect(screen.getByTestId("reject-note")).toBeInTheDocument();
    expect(decideSpy).not.toHaveBeenCalled();
    expect(resumeSpy).not.toHaveBeenCalled();
  });

  it("verification reject-with-note → decide(rejected, note) + resume() fired", async () => {
    useChatStore.setState({ stopReason: "awaiting_approval" });
    render(<HITLTurn turn={makeTurn({ kind: "verification" })} />);

    await userEvent.click(screen.getByTestId("reject-btn"));
    await userEvent.type(screen.getByTestId("reject-note"), "be more specific");
    await userEvent.click(screen.getByTestId("reject-confirm-btn"));

    await waitFor(() =>
      expect(decideSpy).toHaveBeenCalledWith("ar-1", "rejected", "be more specific"),
    );
    await waitFor(() => expect(resumeSpy).toHaveBeenCalledTimes(1));
  });

  it("verification meta row reads 'verification' (kind-aware, not 'tool')", () => {
    render(<HITLTurn turn={makeTurn({ kind: "verification" })} />);
    expect(screen.getByText("verification")).toBeInTheDocument();
  });
});
