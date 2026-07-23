/**
 * File: frontend/tests/unit/chat_v2/components/SessionList.test.tsx
 * Purpose: Vitest render coverage for SessionList — real-backend data (mocked store), empty state, handoff-chain badge.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 3 §3.1 → 57.107 B3 (real GET /sessions data)
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 *
 * Modification History:
 *   - 2026-07-23: Sprint 57.167 — Filter control honest-disable + tooltip (de-Potemkin 2)
 *   - 2026-06-16: Sprint 57.126 — click now calls loadSessionHistory (mock fetchSessionEvents) + new trigger test
 *   - 2026-06-12: Sprint 57.107 B3 — converted fixture assertions to mock the store (real session data + loadSessions); +empty state + chain badge + no-DEMO-banner cases
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

// Sprint 57.126: a session click now calls loadSessionHistory → fetchSessionEvents.
// Mock the service so the click/highlight assertions don't hit the network.
vi.mock("@/features/chat_v2/services/chatService", () => ({
  fetchSessionEvents: vi.fn(),
  listSessions: vi.fn(),
}));

import { SessionList } from "@/features/chat_v2/components/SessionList";
import { fetchSessionEvents } from "@/features/chat_v2/services/chatService";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { Session } from "@/features/chat_v2/types";

// Real-shaped sessions (camelCase Session UI type, as chatStore.loadSessions maps).
const SESSIONS: Session[] = [
  {
    id: "sess_root",
    title: "payment-gateway 5xx spike",
    agent: "incident-responder",
    turns: 17,
    status: "running",
    time: "2026-06-12 10:00",
    handoffParentId: null,
    agentRole: "incident-responder",
  },
  {
    id: "sess_hitl",
    title: "Q4 compliance audit",
    agent: "compliance-auditor",
    turns: 42,
    status: "hitl",
    time: "2026-06-12 09:52",
    handoffParentId: null,
    agentRole: "compliance-auditor",
  },
  {
    id: "sess_child",
    title: "RCA follow-up",
    agent: "rca-bot",
    turns: 5,
    status: "handed_off",
    time: "2026-06-12 09:00",
    handoffParentId: "sess_root",
    agentRole: "rca-bot",
  },
  {
    id: "sess_done",
    title: null,
    agent: null,
    turns: 3,
    status: "done",
    time: "2026-06-11 18:00",
    handoffParentId: null,
    agentRole: null,
  },
];

function seedSessions(sessions: Session[]): void {
  // loadSessions is called on mount; stub it to a no-op so the seeded list stays.
  useChatStore.setState({ sessions, loadSessions: vi.fn().mockResolvedValue(undefined) });
}

describe("SessionList (Sprint 57.107 B3 — real backend data)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
    // Default to an empty transcript so a click's loadSessionHistory replay is a no-op.
    vi.mocked(fetchSessionEvents).mockResolvedValue([]);
  });
  afterEach(() => {
    useChatStore.getState().reset();
    vi.restoreAllMocks();
  });

  test("renders sessions from the store with title + agent + turns", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    expect(screen.getByText("payment-gateway 5xx spike")).toBeInTheDocument();
    expect(screen.getByText("incident-responder")).toBeInTheDocument();
    expect(screen.getByText("17 turns")).toBeInTheDocument();
  });

  test("calls loadSessions on mount", () => {
    const loadSessions = vi.fn().mockResolvedValue(undefined);
    useChatStore.setState({ sessions: [], loadSessions });
    render(<SessionList />);
    expect(loadSessions).toHaveBeenCalledTimes(1);
  });

  test("empty store renders the 'No sessions yet' empty state", () => {
    useChatStore.setState({ sessions: [], loadSessions: vi.fn().mockResolvedValue(undefined) });
    render(<SessionList />);
    const empty = screen.getByTestId("session-list-empty");
    expect(empty).toBeInTheDocument();
    expect(empty.textContent).toMatch(/No sessions yet/i);
  });

  test("no DEMO banner / DEMO tag any more (real data)", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    expect(screen.queryByTestId("session-list-demo-banner")).toBeNull();
    expect(screen.queryByText("DEMO")).toBeNull();
  });

  test("null title renders the 'Untitled session' fallback", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const done = screen.getByTestId("session-item-sess_done");
    expect(done.textContent).toMatch(/Untitled session/);
  });

  test("a handoff child renders the ↳ chain badge with its agent role", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const badge = screen.getByTestId("session-chain-sess_child");
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toMatch(/↳/);
    expect(badge.textContent).toMatch(/rca-bot/);
    // A root session has NO chain badge.
    expect(screen.queryByTestId("session-chain-sess_root")).toBeNull();
  });

  test("active session is data-active=true after click; others data-active=false", async () => {
    seedSessions(SESSIONS);
    const user = userEvent.setup();
    render(<SessionList />);

    const first = screen.getByTestId("session-item-sess_root");
    const second = screen.getByTestId("session-item-sess_hitl");

    expect(first.getAttribute("data-active")).toBe("false");
    expect(second.getAttribute("data-active")).toBe("false");

    await user.click(second);
    expect(first.getAttribute("data-active")).toBe("false");
    expect(second.getAttribute("data-active")).toBe("true");
    expect(useChatStore.getState().activeSessionId).toBe("sess_hitl");
  });

  test("clicking a session triggers loadSessionHistory with its id (Sprint 57.126)", async () => {
    const loadSessionHistory = vi.fn().mockResolvedValue(undefined);
    seedSessions(SESSIONS);
    useChatStore.setState({ loadSessionHistory });
    const user = userEvent.setup();
    render(<SessionList />);

    await user.click(screen.getByTestId("session-item-sess_hitl"));
    expect(loadSessionHistory).toHaveBeenCalledWith("sess_hitl");
  });

  test("status=running shows live-dot only (no badge)", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const running = screen.getByTestId("session-item-sess_root");
    expect(running.querySelector("[aria-label='running']")).toBeTruthy();
    expect(running.textContent).not.toMatch(/HITL/);
  });

  test("status=hitl shows HITL badge (no live-dot)", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const hitl = screen.getByTestId("session-item-sess_hitl");
    expect(hitl.textContent).toMatch(/HITL/);
    expect(hitl.querySelector("[aria-label='running']")).toBeNull();
  });

  test("status=done shows neither badge nor live-dot", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const done = screen.getByTestId("session-item-sess_done");
    expect(done.textContent).not.toMatch(/HITL/);
    expect(done.querySelector("[aria-label='running']")).toBeNull();
  });

  test("session count matches store length", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);
    const counts = screen.getAllByText(String(SESSIONS.length));
    expect(counts.length).toBeGreaterThanOrEqual(1);
  });

  test("'New session' starts a fresh chat but PRESERVES the sidebar list (AD-Chat-New-Session-Wipes-Sidebar)", async () => {
    const user = userEvent.setup();
    seedSessions(SESSIONS);
    useChatStore.setState({ activeSessionId: "sess_root" });
    expect(useChatStore.getState().activeSessionId).toBe("sess_root");
    const idsBefore = useChatStore.getState().sessions.map((s) => s.id);
    expect(idsBefore.length).toBeGreaterThan(0);
    render(<SessionList />);
    await user.click(screen.getByRole("button", { name: /New session/i }));
    // Conversation reset: the active session is cleared...
    expect(useChatStore.getState().activeSessionId).toBeNull();
    // ...but the sidebar session list SURVIVES. The bug: "New session" was wired to
    // reset(), which spreads _initial() (sessions: []) → the whole list vanished
    // until a page refresh re-fetched GET /sessions.
    expect(useChatStore.getState().sessions.map((s) => s.id)).toEqual(idsBefore);
  });
});

describe("SessionList Filter control (Sprint 57.167 — de-Potemkin 2)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
    vi.mocked(fetchSessionEvents).mockResolvedValue([]);
  });
  afterEach(() => {
    useChatStore.getState().reset();
    vi.restoreAllMocks();
  });

  test("Filter is disabled and declares why, instead of silently doing nothing", () => {
    seedSessions(SESSIONS);
    render(<SessionList />);

    const filter = screen.getByRole("button", { name: /filter/i });
    expect(filter).toBeDisabled();
    // The tooltip is the honest surface: the control's inertness is declared, not hidden.
    expect(filter).toHaveAttribute("title", expect.stringMatching(/not available yet/i));
  });

  test("clicking Filter changes nothing (the AP-4 dead-control walk)", async () => {
    seedSessions(SESSIONS);
    render(<SessionList />);

    const before = useChatStore.getState().sessions;
    const filter = screen.getByRole("button", { name: /filter/i });
    // userEvent refuses to click a disabled control — that refusal IS the assertion
    // that a user cannot trigger a no-op. Verify no state moved either way.
    await userEvent.click(filter, { pointerEventsCheck: 0 });

    expect(useChatStore.getState().sessions).toBe(before);
    expect(screen.getAllByTestId(/session-item|session-list/).length).toBeGreaterThan(0);
  });
});
