/**
 * File: frontend/tests/unit/chat_v2/components/SessionList.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.21 SessionList sidebar (Day 3 §3.1).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 3 §3.1
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { FIXTURE_SESSIONS } from "@/features/chat_v2/fixtures/sessions";
import { SessionList } from "@/features/chat_v2/components/SessionList";
import { useChatStore } from "@/features/chat_v2/store/chatStore";

describe("SessionList (Sprint 57.21 Day 3 §3.1)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("renders all 6 fixture sessions with title + agent + turns", () => {
    render(<SessionList />);
    for (const s of FIXTURE_SESSIONS) {
      expect(screen.getByText(s.title)).toBeInTheDocument();
    }
    // First session metadata sample assertion
    expect(screen.getByText("incident-responder")).toBeInTheDocument();
    expect(screen.getByText("17 turns")).toBeInTheDocument();
  });

  test("renders demo banner with backend-deferred copy (AP-2 compliance)", () => {
    render(<SessionList />);
    const banner = screen.getByTestId("session-list-demo-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/Demo data/i);
    expect(banner.textContent).toMatch(/AD-ChatV2-SessionList-Backend/);
  });

  test("active session is data-active=true after click; others data-active=false", async () => {
    const user = userEvent.setup();
    render(<SessionList />);

    const first = screen.getByTestId("session-item-sess_4tk2p");
    const second = screen.getByTestId("session-item-sess_91kxu");

    // Initially no active session — both data-active=false.
    expect(first.getAttribute("data-active")).toBe("false");
    expect(second.getAttribute("data-active")).toBe("false");

    await user.click(second);
    expect(first.getAttribute("data-active")).toBe("false");
    expect(second.getAttribute("data-active")).toBe("true");
    expect(useChatStore.getState().activeSessionId).toBe("sess_91kxu");
  });

  test("status=running shows live-dot only (no badge)", () => {
    render(<SessionList />);
    const running = screen.getByTestId("session-item-sess_4tk2p");
    // live-dot element has aria-label "running"
    expect(running.querySelector("[aria-label='running']")).toBeTruthy();
    // No HITL badge
    expect(running.textContent).not.toMatch(/HITL/);
  });

  test("status=hitl shows HITL badge (no live-dot)", () => {
    render(<SessionList />);
    const hitl = screen.getByTestId("session-item-sess_91kxu");
    expect(hitl.textContent).toMatch(/HITL/);
    expect(hitl.querySelector("[aria-label='running']")).toBeNull();
  });

  test("status=done shows neither badge nor live-dot", () => {
    render(<SessionList />);
    const done = screen.getByTestId("session-item-sess_88vqc");
    expect(done.textContent).not.toMatch(/HITL/);
    expect(done.querySelector("[aria-label='running']")).toBeNull();
  });

  test("session count badge matches fixture length", () => {
    render(<SessionList />);
    const counts = screen.getAllByText(String(FIXTURE_SESSIONS.length));
    expect(counts.length).toBeGreaterThanOrEqual(1);
  });
});
