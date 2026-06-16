/**
 * File: frontend/tests/unit/chat_v2/chatStore.historyReplay.test.ts
 * Purpose: Vitest coverage for loadSessionHistory — fetch /events → replay through mergeEvent.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.126 (US-4/5)
 *
 * Description:
 *   loadSessionHistory fetches a session's persisted transcript and replays each
 *   {type, data} through the SAME mergeEvent reducer (incl. the NEW user_message
 *   case → UserTurn) onto a conversation-only reset. Asserts: a complete
 *   user→agent replay; defensive sort; the live guard (don't reload a running
 *   session); the race guard (latest-clicked-wins); the reset preserves `sessions`.
 *
 * Modification History:
 *   - 2026-06-16: Initial creation (Sprint 57.126)
 */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("@/features/chat_v2/services/chatService", () => ({
  fetchSessionEvents: vi.fn(),
  listSessions: vi.fn(),
}));

import { fetchSessionEvents } from "@/features/chat_v2/services/chatService";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { PersistedSessionEvent } from "@/features/chat_v2/services/chatService";
import type { AgentTurn, Session, UserTurn } from "@/features/chat_v2/types";

const mockFetch = vi.mocked(fetchSessionEvents);

// A full single-send transcript: user prompt + the agent's reply turn.
const TRANSCRIPT: PersistedSessionEvent[] = [
  { type: "user_message", data: { text: "what is 2+2?" }, sequence_num: 1, timestamp_ms: 1000 },
  {
    type: "loop_start",
    data: { session_id: "s1", request_id: "r1", active_skill: null },
    sequence_num: 2,
    timestamp_ms: 1001,
  },
  { type: "turn_start", data: { turn_num: 1 }, sequence_num: 3, timestamp_ms: 1002 },
  {
    type: "llm_response",
    data: { content: "4", tool_calls: [], thinking: "" },
    sequence_num: 4,
    timestamp_ms: 1003,
  },
  {
    type: "loop_end",
    data: { stop_reason: "end_turn", total_turns: 1 },
    sequence_num: 5,
    timestamp_ms: 1004,
  },
];

describe("chatStore.loadSessionHistory (Sprint 57.126)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
    // Clear cumulative call history + implementation between tests (the module mock
    // persists across tests; restoreAllMocks doesn't reset a vi.mock factory fn).
    mockFetch.mockReset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
    vi.restoreAllMocks();
  });

  test("replays a transcript into user + agent turns + sets the active session", async () => {
    mockFetch.mockResolvedValue(TRANSCRIPT);

    await useChatStore.getState().loadSessionHistory("s1");

    const { turns, sessionId, activeSessionId, status } = useChatStore.getState();
    expect(turns).toHaveLength(2);
    expect(turns[0].role).toBe("user");
    expect((turns[0] as UserTurn).text).toBe("what is 2+2?");
    expect(turns[1].role).toBe("agent");
    expect((turns[1] as AgentTurn).blocks.length).toBeGreaterThan(0);
    // loop_end ran → completed (composer re-enabled for continuation).
    expect(status).toBe("completed");
    // The loaded session is active so a follow-up continues it.
    expect(sessionId).toBe("s1");
    expect(activeSessionId).toBe("s1");
  });

  test("sorts out-of-order events by sequence_num before replay (faithful order)", async () => {
    const shuffled = [TRANSCRIPT[4], TRANSCRIPT[1], TRANSCRIPT[3], TRANSCRIPT[0], TRANSCRIPT[2]];
    mockFetch.mockResolvedValue(shuffled);

    await useChatStore.getState().loadSessionHistory("s1");

    const { turns } = useChatStore.getState();
    expect(turns.map((t) => t.role)).toEqual(["user", "agent"]);
    expect((turns[0] as UserTurn).text).toBe("what is 2+2?");
  });

  test("live guard: clicking the currently-running session does NOT reload", async () => {
    useChatStore.setState({ sessionId: "s1", status: "running", turns: [] });

    await useChatStore.getState().loadSessionHistory("s1");

    expect(mockFetch).not.toHaveBeenCalled();
    expect(useChatStore.getState().status).toBe("running");
  });

  test("race guard: a stale fetch resolved after a newer click is dropped", async () => {
    let resolveFetch: (v: PersistedSessionEvent[]) => void = () => {};
    mockFetch.mockReturnValue(
      new Promise<PersistedSessionEvent[]>((r) => {
        resolveFetch = r;
      }),
    );

    // Click session s1 (sets activeSessionId=s1, awaits the fetch)...
    const pending = useChatStore.getState().loadSessionHistory("s1");
    // ...then a newer click re-points to s2 before s1's fetch resolves.
    useChatStore.setState({ activeSessionId: "s2" });
    resolveFetch(TRANSCRIPT);
    await pending;

    // The stale s1 transcript must NOT be replayed onto the s2 selection.
    expect(useChatStore.getState().turns).toEqual([]);
  });

  test("conversation-only reset preserves the sidebar `sessions` list", async () => {
    const sessions: Session[] = [
      {
        id: "s1",
        title: "prior chat",
        agent: "a",
        turns: 2,
        status: "done",
        time: "t",
        handoffParentId: null,
        agentRole: "a",
      },
    ];
    useChatStore.setState({ sessions });
    mockFetch.mockResolvedValue([]);

    await useChatStore.getState().loadSessionHistory("s1");

    expect(useChatStore.getState().sessions).toEqual(sessions);
  });

  test("a fetch error surfaces as errorMessage without crashing", async () => {
    mockFetch.mockRejectedValue(new Error("HTTP 500: boom"));

    await useChatStore.getState().loadSessionHistory("s1");

    expect(useChatStore.getState().errorMessage).toMatch(/HTTP 500/);
    expect(useChatStore.getState().turns).toEqual([]);
  });
});
