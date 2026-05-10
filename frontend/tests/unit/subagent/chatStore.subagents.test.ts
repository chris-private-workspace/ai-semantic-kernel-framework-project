/**
 * File: frontend/tests/unit/subagent/chatStore.subagents.test.ts
 * Purpose: Vitest tests for chatStore subagents slice — mergeEvent SSE branch + clearSubagents (Sprint 57.12 US-6).
 * Category: Frontend / tests / unit / subagent
 * Scope: Phase 57 / Sprint 57.12 Day 3 / US-6
 *
 * Description:
 *   Verifies the subagent_spawned / subagent_completed cases in mergeEvent
 *   (per AD-Cat11-SSEEvents codified by CONVENTION.md §7 3-edit checklist) +
 *   running→completed transition + dedup + defensive-create (Completed without
 *   prior Spawned) + clearSubagents reducer + rawEvents audit trail.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 3 / US-6)
 *
 * Modification History:
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 3 / US-6)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";

const spawned = (id: string, mode = "fork", parent: string | null = "chat-session-1"): LoopEvent => ({
  type: "subagent_spawned",
  data: { subagent_id: id, mode, parent_session_id: parent },
});

const completed = (id: string, summary = "done", tokens = 42): LoopEvent => ({
  type: "subagent_completed",
  data: { subagent_id: id, summary, tokens_used: tokens },
});

describe("chatStore subagents slice (Sprint 57.12 US-6)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("subagent_spawned pushes a 'running' node with mode + parentId", () => {
    useChatStore.getState().mergeEvent(spawned("sa-1", "teammate", "chat-x"));
    const { subagents, rawEvents } = useChatStore.getState();
    expect(subagents).toHaveLength(1);
    expect(subagents[0].subagentId).toBe("sa-1");
    expect(subagents[0].mode).toBe("teammate");
    expect(subagents[0].parentId).toBe("chat-x");
    expect(subagents[0].status).toBe("running");
    expect(subagents[0].summary).toBeNull();
    expect(rawEvents).toHaveLength(1); // audit trail
  });

  test("subagent_completed transitions matching node running → completed + summary + tokens", () => {
    useChatStore.getState().mergeEvent(spawned("sa-2"));
    useChatStore.getState().mergeEvent(completed("sa-2", "subagent reply", 99));
    const { subagents } = useChatStore.getState();
    expect(subagents).toHaveLength(1);
    expect(subagents[0].status).toBe("completed");
    expect(subagents[0].summary).toBe("subagent reply");
    expect(subagents[0].tokensUsed).toBe(99);
  });

  test("subagent_spawned dedups on subagent_id (no duplicate node)", () => {
    useChatStore.getState().mergeEvent(spawned("sa-3"));
    useChatStore.getState().mergeEvent(spawned("sa-3"));
    expect(useChatStore.getState().subagents).toHaveLength(1);
  });

  test("subagent_completed without prior Spawned defensively creates a 'completed' node", () => {
    useChatStore.getState().mergeEvent(completed("sa-ghost", "orphan summary", 7));
    const { subagents } = useChatStore.getState();
    expect(subagents).toHaveLength(1);
    expect(subagents[0].subagentId).toBe("sa-ghost");
    expect(subagents[0].status).toBe("completed");
    expect(subagents[0].mode).toBe("unknown");
  });

  test("clearSubagents resets the array to empty", () => {
    useChatStore.getState().mergeEvent(spawned("sa-4"));
    expect(useChatStore.getState().subagents).toHaveLength(1);
    useChatStore.getState().clearSubagents();
    expect(useChatStore.getState().subagents).toEqual([]);
  });

  test("subagent_* events with null subagent_id are recorded in rawEvents but produce no node", () => {
    useChatStore.getState().mergeEvent({
      type: "subagent_spawned",
      data: { subagent_id: null, mode: "fork", parent_session_id: null },
    });
    expect(useChatStore.getState().subagents).toHaveLength(0);
    expect(useChatStore.getState().rawEvents).toHaveLength(1);
  });
});
