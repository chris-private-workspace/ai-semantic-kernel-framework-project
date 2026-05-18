/**
 * File: frontend/tests/unit/chat_v2/components/TurnList.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.21 TurnList role dispatcher.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 2 §2.1
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 2 §2.1)
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useAuthStore } from "@/features/auth/store/authStore";
import { TurnList } from "@/features/chat_v2/components/TurnList";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { Turn } from "@/features/chat_v2/types";

function seedAuth(): void {
  useAuthStore.setState({
    status: "authenticated",
    user: { id: "u-1", email: "jamie@acme.test", display_name: "Jamie Liu" },
    tenant: { id: "t-1", name: "Acme", code: "acme" },
    roles: ["operator"],
  });
}

const userTurn = (text: string, id = "t_u1"): Turn => ({
  role: "user",
  id,
  at: "10:42:18",
  text,
});

const agentTurn = (id = "t_a1"): Turn => ({
  role: "agent",
  id,
  at: "10:42:19",
  stopReason: "end_turn",
  durationMs: 1420,
  blocks: [{ type: "thinking", text: "Initial analysis" }],
  tokensIn: null,
  tokensOut: null,
  tokensThinking: null,
  costUsd: null,
  traceId: null,
  spanId: null,
});

const hitlTurn = (id = "t_h1"): Turn => ({
  role: "hitl",
  id,
  at: "10:46:40",
  title: "Approve write",
  severity: "risk-high",
  tool: "k8s.set_env",
  payload: "—",
  rationale: "—",
  approvalRequestId: "ap-1",
  decision: null,
  countdownSec: null,
});

describe("TurnList (Sprint 57.21 Day 2)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
    seedAuth();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("empty turns shows echo_demo hint empty-state", () => {
    render(<TurnList />);
    expect(screen.getByText(/Type a message below to start/)).toBeInTheDocument();
    expect(screen.getByText("echo hello")).toBeInTheDocument();
  });

  test("user role dispatches → UserTurn with display name + role pill + text", () => {
    useChatStore.setState({ turns: [userTurn("investigate INC-4087")] });
    render(<TurnList />);
    expect(screen.getByText("Jamie Liu")).toBeInTheDocument();
    expect(screen.getByText("operator")).toBeInTheDocument();
    expect(screen.getByText("investigate INC-4087")).toBeInTheDocument();
  });

  test("user role falls back to email when display_name null", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: { id: "u-2", email: "ops@acme.test", display_name: null },
      tenant: { id: "t-1", name: "Acme", code: "acme" },
      roles: ["operator"],
    });
    useChatStore.setState({ turns: [userTurn("test")] });
    render(<TurnList />);
    expect(screen.getByText("ops@acme.test")).toBeInTheDocument();
  });

  test("agent role dispatches → AgentTurn with turn # badge + thinking block", () => {
    useChatStore.setState({ turns: [agentTurn()] });
    render(<TurnList />);
    expect(screen.getByText("incident-responder")).toBeInTheDocument();
    expect(screen.getByText("turn a1")).toBeInTheDocument();
    expect(screen.getByText("stop: end_turn")).toBeInTheDocument();
    expect(screen.getByText("Initial analysis")).toBeInTheDocument();
  });

  test("agent role shows 'awaiting approval' when waiting=true", () => {
    useChatStore.setState({ turns: [{ ...(agentTurn() as Extract<Turn, { role: "agent" }>), waiting: true }] });
    render(<TurnList />);
    expect(screen.getByText("awaiting approval")).toBeInTheDocument();
  });

  test("hitl role dispatches → HITLTurn with severity + title + 2-action buttons + approval_id", () => {
    useChatStore.setState({ turns: [hitlTurn()] });
    render(<TurnList />);
    expect(screen.getByText("HITL approval required")).toBeInTheDocument();
    expect(screen.getByText("Approve write")).toBeInTheDocument();
    expect(screen.getByText("k8s.set_env")).toBeInTheDocument();
    // Phase-1 ships canonical 2-action subset (matches Sprint 53.5 baseline +
    // approval-card.spec.ts e2e contract). "Approve with edits" + "Escalate to L2"
    // 4-action UX deferred to Phase-2 AD-ChatV2-HITL-FourAction-Phase2.
    expect(screen.getByText("Approve & continue")).toBeInTheDocument();
    expect(screen.getByText("Reject")).toBeInTheDocument();
    expect(screen.queryByText("Approve with edits")).not.toBeInTheDocument();
    expect(screen.queryByText("Escalate to L2")).not.toBeInTheDocument();
    // approval_id visible (e2e contract approval-card.spec.ts L70).
    expect(screen.getByText(/approval_id: ap-/)).toBeInTheDocument();
  });

  test("hitl with decision shows result label + hides action buttons", () => {
    useChatStore.setState({ turns: [{ ...(hitlTurn() as Extract<Turn, { role: "hitl" }>), decision: "APPROVED" }] });
    render(<TurnList />);
    expect(screen.getByText(/Decision: APPROVED/)).toBeInTheDocument();
    // Buttons hidden when decided (e2e contract approval-card.spec.ts L152).
    expect(screen.queryByText("Approve & continue")).not.toBeInTheDocument();
    expect(screen.queryByText("Reject")).not.toBeInTheDocument();
  });

  test("mixed turns render in order user → agent → hitl", () => {
    useChatStore.setState({
      turns: [userTurn("q", "t_u1"), agentTurn("t_a1"), hitlTurn("t_h1")],
    });
    render(<TurnList />);
    expect(screen.getByText("Jamie Liu")).toBeInTheDocument();
    expect(screen.getByText("incident-responder")).toBeInTheDocument();
    expect(screen.getByText("HITL approval required")).toBeInTheDocument();
  });
});
