/**
 * File: frontend/src/features/chat_v2/hooks/useLoopEventStream.ts
 * Purpose: React hook wrapping streamChat + Zustand store integration.
 * Category: Frontend / chat_v2 / hooks
 * Scope: Phase 50 / Sprint 50.2 (Day 3.5)
 *
 * Description:
 *   Provides a `send(message)` function that:
 *     1. Pushes the user message into the store
 *     2. Calls streamChat() with onEvent → store.mergeEvent
 *     3. Routes errors to store.setError + status="error"
 *     4. Owns an AbortController for cancellation via `cancel()`
 *
 *   Sprint 57.88 (US-5): also provides `resume()` for the durable HITL
 *   pause-resume continuation. After a deferred pause (loop_end with
 *   stop_reason="awaiting_approval") and the human's decide() call, `resume()`
 *   opens a fresh SSE stream via resumeChat() that merges the continuation
 *   events into the SAME store (the resumed tool_call_result updates the
 *   still-pending escalated ToolBlock by tool_call_id; turn_start pushes the
 *   continuation as a new agent turn). No user message is pushed.
 *
 *   Reuses the same Zustand chatStore — components subscribe directly to
 *   store fields rather than receiving them through hook return value.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.5)
 * Last Modified: 2026-06-14
 *
 * Modification History:
 *   - 2026-06-14: Sprint 57.115 — send() takes opts.forceLoadSkill → force_load_skill request field
 *   - 2026-06-11: Sprint 57.101 B1 — +inject() for mid-run message injection (POST /inject)
 *   - 2026-06-08: Sprint 57.88 US-5 — +resume() for durable HITL pause-resume continuation
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.5)
 *
 * Related:
 *   - ../services/chatService.ts (streamChat + resumeChat)
 *   - ../store/chatStore.ts (mergeEvent + status)
 *   - ../components/turns/HITLTurn.tsx (calls resume() after an approve decision)
 */

import { useCallback, useRef } from "react";
import { cancelSession, injectMessage, resumeChat, streamChat } from "../services/chatService";
import { useChatStore } from "../store/chatStore";

export type UseLoopEventStream = {
  // Sprint 57.115: opts.forceLoadSkill carries the user-picked /skill-name (the
  // InputBar parses the leading token) → the chat POST's force_load_skill field.
  send: (message: string, opts?: { forceLoadSkill?: string }) => Promise<void>;
  resume: () => Promise<void>;
  inject: (message: string) => Promise<void>;
  cancel: () => void;
  isRunning: boolean;
};

export function useLoopEventStream(): UseLoopEventStream {
  const status = useChatStore((s) => s.status);
  const mode = useChatStore((s) => s.mode);
  const sessionId = useChatStore((s) => s.sessionId);
  const pushUserMessage = useChatStore((s) => s.pushUserMessage);
  const mergeEvent = useChatStore((s) => s.mergeEvent);
  const setStatus = useChatStore((s) => s.setStatus);
  const setError = useChatStore((s) => s.setError);

  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (message: string, opts?: { forceLoadSkill?: string }) => {
      if (status === "running") return;
      pushUserMessage(message);
      setStatus("running");
      setError(null);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      await streamChat(
        {
          message,
          mode,
          ...(sessionId ? { session_id: sessionId } : {}),
          // Sprint 57.115: the user-picked /skill-name → deterministic force-load.
          ...(opts?.forceLoadSkill ? { force_load_skill: opts.forceLoadSkill } : {}),
        },
        {
          onEvent: mergeEvent,
          onError: (err) => {
            setError(err.message);
            setStatus("error");
          },
          signal: ctrl.signal,
        },
      );

      // If the loop did NOT emit loop_end (network drop / abort), state may
      // still be "running" — drop to "completed" so the UI re-enables input.
      const finalStatus = useChatStore.getState().status;
      if (finalStatus === "running") setStatus("completed");
    },
    [status, mode, sessionId, pushUserMessage, mergeEvent, setStatus, setError],
  );

  // Sprint 57.88 (US-5): resume a deferred-paused chat after a human approval.
  // Reads sessionId/status from the live store (not closure) to avoid a stale
  // capture when invoked deep in the turn tree (HITLTurn). Pushes no user
  // message — the continuation flows into the existing turns.
  const resume = useCallback(async () => {
    const { sessionId: sid, status: st } = useChatStore.getState();
    if (st === "running" || sid === null) return;
    setStatus("running");
    setError(null);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    await resumeChat(sid, {
      onEvent: mergeEvent,
      onError: (err) => {
        setError(err.message);
        setStatus("error");
      },
      signal: ctrl.signal,
    });

    // Mirror send(): if the resumed loop did NOT emit loop_end (drop / abort),
    // settle status so the UI re-enables.
    const finalStatus = useChatStore.getState().status;
    if (finalStatus === "running") setStatus("completed");
  }, [mergeEvent, setStatus, setError]);

  // Sprint 57.101 (B1): inject a supplementary instruction MID-RUN. Only valid
  // while a run is live (status="running" + a sessionId); the loop drains it at
  // the next turn boundary and the ALREADY-OPEN run stream (held by send()) merges
  // the resulting message_injected event. Reads sessionId/status from the live
  // store (not closure) to avoid a stale capture. An inject failure (e.g. 409 if
  // the run just ended) surfaces via setError but does NOT change status — the run
  // is unaffected, the injection simply did not land.
  const inject = useCallback(
    async (message: string) => {
      const { sessionId: sid, status: st } = useChatStore.getState();
      if (sid === null || st !== "running") return;
      try {
        await injectMessage(sid, message);
      } catch (err) {
        setError((err as Error).message);
      }
    },
    [setError],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setStatus("cancelled");
    // Sprint 57.143 (AD-UserStop-Resume-Context): also tell the server so it records
    // a `[Request interrupted by user]` marker (the abort alone only closes the SSE;
    // the marker makes a later "continue" send coherent). Fire-and-forget — a cancel
    // API failure must NOT change the UI cancelled state.
    const { sessionId: sid } = useChatStore.getState();
    if (sid) void cancelSession(sid).catch(() => {});
  }, [setStatus]);

  return { send, resume, inject, cancel, isRunning: status === "running" };
}
