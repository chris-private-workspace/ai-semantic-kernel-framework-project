/**
 * File: frontend/tests/unit/verification/VerificationPanel.test.tsx
 * Purpose: Vitest tests for chat-v2 inline VerificationPanel (Sprint 57.11 US-5 §3.5).
 * Category: Frontend / tests / unit / verification
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-5
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.5)
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import { VerificationPanel } from "@/features/verification/components/VerificationPanel";
import type { VerificationEvent } from "@/features/verification/types";

describe("VerificationPanel (Sprint 57.11 US-5)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });

  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("hidden when verifications array empty (returns null)", () => {
    const { container } = render(<VerificationPanel />);
    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId("verification-panel")).not.toBeInTheDocument();
  });

  test("renders 2 entries (1 passed + 1 failed) with VerifierTypeBadge integration", () => {
    const ev1: VerificationEvent = {
      type: "verification_passed",
      data: { verifier: "pii_redaction", verifier_type: "rules_based", score: 0.95 },
    };
    const ev2: VerificationEvent = {
      type: "verification_failed",
      data: {
        verifier: "off_topic_detector",
        verifier_type: "llm_judge",
        reason: "user prompt drifted",
        suggested_correction: "redirect to original topic",
      },
    };
    useChatStore.getState().appendVerification(ev1);
    useChatStore.getState().appendVerification(ev2);

    render(<VerificationPanel />);

    expect(screen.getByTestId("verification-panel")).toBeInTheDocument();
    expect(screen.getByText("Verification (2)")).toBeInTheDocument();
    expect(screen.getByText("pii_redaction")).toBeInTheDocument();
    expect(screen.getByText("off_topic_detector")).toBeInTheDocument();
    expect(screen.getByText("user prompt drifted")).toBeInTheDocument();
    expect(screen.getByText("Suggested: redirect to original topic")).toBeInTheDocument();
    // VerifierTypeBadge rendered for both types
    expect(screen.getByTestId("verifier-type-badge-rules_based")).toBeInTheDocument();
    expect(screen.getByTestId("verifier-type-badge-llm_judge")).toBeInTheDocument();
  });

  test("passed entry shows score when present", () => {
    useChatStore.getState().appendVerification({
      type: "verification_passed",
      data: { verifier: "v1", verifier_type: "external", score: 0.87 },
    });

    render(<VerificationPanel />);
    expect(screen.getByText("Score: 0.87")).toBeInTheDocument();
  });
});
