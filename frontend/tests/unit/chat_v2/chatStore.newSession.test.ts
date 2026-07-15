/**
 * File: frontend/tests/unit/chat_v2/chatStore.newSession.test.ts
 * Purpose: Vitest coverage for chatStore.newSession — conversation-only reset that
 *   preserves the sidebar session list (AD-Chat-New-Session-Wipes-Sidebar).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / AD-Chat-New-Session-Wipes-Sidebar
 *
 * Description:
 *   The "New session" button used to call reset(), which spreads _initial()
 *   (sessions: []) and blanked the whole sidebar until a page refresh re-fetched
 *   GET /sessions. newSession() is the fix: a conversation-only reset that clears
 *   the live conversation slices but PRESERVES `sessions` (and `mode`). These tests
 *   assert both halves — the conversation is wiped, the sidebar survives.
 *
 * Modification History:
 *   - 2026-07-15: Initial creation (AD-Chat-New-Session-Wipes-Sidebar)
 */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("@/features/chat_v2/services/chatService", () => ({
  fetchSessionEvents: vi.fn(),
  listSessions: vi.fn(),
}));

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { Session } from "@/features/chat_v2/types";

const SESSIONS: Session[] = [
  {
    id: "a",
    title: "session A",
    agent: "agent",
    turns: 3,
    status: "done",
    time: "t",
    handoffParentId: null,
    agentRole: "agent",
  },
  {
    id: "b",
    title: "session B",
    agent: "agent",
    turns: 1,
    status: "running",
    time: "t",
    handoffParentId: null,
    agentRole: "agent",
  },
];

describe("chatStore.newSession (AD-Chat-New-Session-Wipes-Sidebar)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("preserves the sessions sidebar list (the regression)", () => {
    useChatStore.setState({ sessions: SESSIONS });
    useChatStore.getState().newSession();
    expect(useChatStore.getState().sessions.map((s) => s.id)).toEqual(["a", "b"]);
  });

  test("clears the live conversation slices", () => {
    // Seed a populated conversation + inspector state (as if a chat had run).
    useChatStore.setState({
      sessions: SESSIONS,
      sessionId: "a",
      activeSessionId: "a",
      status: "running",
      totalTurns: 4,
      turns: [{ role: "user", id: "t_1", at: "now", text: "hi" }],
      rawEvents: [{ type: "loop_start" } as never],
    });

    useChatStore.getState().newSession();

    const s = useChatStore.getState();
    expect(s.turns).toEqual([]);
    expect(s.sessionId).toBeNull();
    expect(s.activeSessionId).toBeNull();
    expect(s.status).toBe("idle");
    expect(s.totalTurns).toBe(0);
    expect(s.rawEvents).toEqual([]);
    // Sidebar untouched.
    expect(s.sessions.map((x) => x.id)).toEqual(["a", "b"]);
  });

  test("preserves the chat mode (not part of _initial())", () => {
    useChatStore.setState({ sessions: SESSIONS, mode: "echo_demo" });
    useChatStore.getState().newSession();
    expect(useChatStore.getState().mode).toBe("echo_demo");
    expect(useChatStore.getState().sessions).toHaveLength(2);
  });

  test("reset() still fully wipes (including sessions) — teardown contract intact", () => {
    useChatStore.setState({ sessions: SESSIONS });
    useChatStore.getState().reset();
    expect(useChatStore.getState().sessions).toEqual([]);
  });
});
