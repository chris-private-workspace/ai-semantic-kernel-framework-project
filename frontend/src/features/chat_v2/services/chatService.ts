/**
 * File: frontend/src/features/chat_v2/services/chatService.ts
 * Purpose: Browser SSE consumer — fetch + ReadableStream parser.
 * Category: Frontend / chat_v2 / services
 * Scope: Phase 50 / Sprint 50.2 (Day 3.4) → Sprint 57.8 fetchWithAuth → Sprint 57.88 resume stream
 *
 * Description:
 *   Sends POST /api/v1/chat/ and parses the `text/event-stream` response
 *   manually using `fetch + response.body.getReader()`. Browser-native
 *   `EventSource` is intentionally NOT used because it does not support
 *   POST bodies — the V2 chat endpoint requires a JSON request body.
 *
 *   Frame parser handles the SSE wire format:
 *       event: <type>\n
 *       data: <json>\n
 *       \n
 *
 *   AbortSignal support: pass the signal through fetch — when aborted,
 *   the reader rejects with AbortError and the function exits cleanly
 *   without calling onEvent again.
 *
 *   Sprint 57.8 D3: raw fetch swapped to fetchWithAuth so requests carry
 *   the Sprint 57.7 IAM JWT (Authorization: Bearer <token>) when the user
 *   is authenticated. Anonymous requests still work for backward compat
 *   while other pages lack auth gates (per AD-Frontend-AuthUX Phase 58.x).
 *
 *   Sprint 57.88 (US-5): `resumeChat` drives the durable HITL pause-resume
 *   continuation — POST /api/v1/chat/{id}/resume (no body; tenant + user from
 *   auth) opens a FRESH SSE stream of the post-approval continuation (execute
 *   the approved pending tool → continue to end_turn). Both functions share the
 *   `consumeSSEStream` reader/parser (extracted to avoid duplication).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.4)
 * Last Modified: 2026-06-14
 *
 * Modification History (newest-first):
 *   - 2026-06-16: Sprint 57.126 — +fetchSessionEvents (GET /sessions/{id}/events; history replay)
 *   - 2026-06-14: Sprint 57.115 — +force_load_skill on ChatRequestBody + fetchChatSkills (picker list)
 *   - 2026-06-12: Sprint 57.107 B3 — +listSessions (GET /sessions; real SessionList data)
 *   - 2026-06-11: Sprint 57.101 B1 — +injectMessage (POST /chat/{id}/inject; mid-run instruction)
 *   - 2026-06-08: Sprint 57.88 US-5 — +resumeChat (POST /chat/{id}/resume); extract consumeSSEStream
 *   - 2026-05-09: Sprint 57.8 D3 — swap raw fetch to fetchWithAuth (JWT injection)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.4)
 *
 * Related:
 *   - backend POST /api/v1/chat/ + POST /api/v1/chat/{id}/resume (router.py)
 *   - ../hooks/useLoopEventStream.ts (consumer — send + resume)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import { KNOWN_LOOP_EVENT_TYPES, type ChatMode, type LoopEvent } from "../types";

export type ChatRequestBody = {
  message: string;
  mode: ChatMode;
  session_id?: string;
  // Sprint 57.115 (Skills slash-command): the user-picked /skill-name. The backend
  // validates it against the tenant's registry and force-loads its instructions.
  force_load_skill?: string;
};

// === Sprint 57.115: Skills slash-command picker list =====================
// The non-admin, tenant-scoped view of the tenant's effective skills (bundled +
// overlay) — name + description ONLY (the instructions body loads on force-load).
export type ChatSkill = {
  name: string;
  description: string;
};

export type ChatSkillsResponse = {
  skills: ChatSkill[];
};

/**
 * Sprint 57.115: list the caller tenant's effective skills for the /skill-name
 * composer picker (tenant from the JWT via fetchWithAuth). A non-2xx throws so
 * the caller can surface it. Returns name + description (no instructions body).
 */
export async function fetchChatSkills(signal?: AbortSignal): Promise<ChatSkill[]> {
  const response = await fetchWithAuth("/api/v1/chat/skills", { method: "GET", signal });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  const body = (await response.json()) as ChatSkillsResponse;
  return body.skills;
}

// === Sprint 57.107 B3: session list ======================================
// Snake_case wire shape of GET /api/v1/sessions items (1:1 backend). Mapped to
// the camelCase `Session` UI type in chatStore.loadSessions.
export type SessionListApiItem = {
  id: string;
  title: string | null;
  status: string;
  agent_role: string | null;
  handoff_parent_id: string | null;
  started_at_ms: number;
  total_turns: number;
};

export type SessionListResponse = {
  sessions: SessionListApiItem[];
};

/**
 * Sprint 57.107 (B3): list the caller's chat sessions (tenant + user from the
 * auth JWT via fetchWithAuth). Returns the raw snake_case items; chatStore
 * maps them to the camelCase `Session` UI shape. A non-2xx throws so the caller
 * can surface it.
 */
export async function listSessions(): Promise<SessionListApiItem[]> {
  const response = await fetchWithAuth("/api/v1/sessions", { method: "GET" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  const body = (await response.json()) as SessionListResponse;
  return body.sessions;
}

// === Sprint 57.126: session history replay ===============================
// One persisted main-session SSE event (the 57.125 backend writer's row). `type`
// + `data` are byte-identical to the live SSE frame (serialize_loop_event output),
// PLUS the persist-only `user_message` row (57.126 — `data.text` is the user prompt)
// → chatStore.loadSessionHistory replays each {type, data} through the SAME
// mergeEvent reducer for a pixel-identical historical Turn stream.
export type PersistedSessionEvent = {
  type: string;
  data: Record<string, unknown>;
  sequence_num: number;
  timestamp_ms: number;
};

export type SessionEventsResponse = {
  events: PersistedSessionEvent[];
};

/**
 * Sprint 57.126: fetch a session's persisted event transcript (tenant + user from
 * the auth JWT via fetchWithAuth), ordered by sequence_num. A non-2xx throws so the
 * caller can surface it; an unknown / cross-tenant / event-less session returns
 * `{events: []}` (200) per the backend (never reveals cross-tenant existence).
 */
export async function fetchSessionEvents(
  sessionId: string,
): Promise<PersistedSessionEvent[]> {
  const response = await fetchWithAuth(`/api/v1/sessions/${sessionId}/events`, {
    method: "GET",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  const body = (await response.json()) as SessionEventsResponse;
  return body.events;
}

// Shared by streamChat + resumeChat: both consume the same SSE wire format,
// only the request (verb / URL / body) differs.
export type StreamChatOptions = {
  onEvent: (ev: LoopEvent) => void;
  onError?: (err: Error) => void;
  signal?: AbortSignal;
};

export async function streamChat(
  body: ChatRequestBody,
  opts: StreamChatOptions,
): Promise<void> {
  let response: Response;
  try {
    response = await fetchWithAuth("/api/v1/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
      signal: opts.signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    opts.onError?.(err as Error);
    return;
  }

  if (!response.ok) {
    const text = await response.text();
    opts.onError?.(new Error(`HTTP ${response.status}: ${text}`));
    return;
  }

  await consumeSSEStream(response, opts);
}

/**
 * Sprint 57.88 (US-5): resume a chat that paused on a deferred HITL approval.
 *
 * POST /api/v1/chat/{sessionId}/resume carries NO body — the backend rebuilds
 * the paused checkpoint from (session_id, tenant_id) where tenant + user come
 * from the auth context (fetchWithAuth injects the JWT). The response is a fresh
 * SSE stream of the post-approval continuation (loop_start → approval_received →
 * the approved pending tool's tool_call_result → turn_start → … → loop_end),
 * parsed identically to the initial stream. A missing / cross-tenant checkpoint
 * → HTTP 404 → onError (the caller surfaces it; it should not happen in the
 * normal approve flow). The approval decision itself is recorded out-of-band via
 * POST /governance/approvals/{id}/decide BEFORE this call.
 */
export async function resumeChat(
  sessionId: string,
  opts: StreamChatOptions,
): Promise<void> {
  let response: Response;
  try {
    response = await fetchWithAuth(`/api/v1/chat/${sessionId}/resume`, {
      method: "POST",
      headers: { Accept: "text/event-stream" },
      signal: opts.signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    opts.onError?.(err as Error);
    return;
  }

  if (!response.ok) {
    const text = await response.text();
    opts.onError?.(new Error(`HTTP ${response.status}: ${text}`));
    return;
  }

  await consumeSSEStream(response, opts);
}

/**
 * Sprint 57.101 (B1): inject a supplementary instruction into a RUNNING chat
 * session. POST /api/v1/chat/{sessionId}/inject with {message} (a plain POST, NOT
 * an SSE stream — the ALREADY-OPEN run stream delivers the resulting
 * `message_injected` event once the loop drains it at the next turn boundary). A
 * non-2xx (404 absent/cross-tenant, 409 not-running, 422 empty) throws so the
 * caller can surface it.
 */
export async function injectMessage(sessionId: string, message: string): Promise<void> {
  const response = await fetchWithAuth(`/api/v1/chat/${sessionId}/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
}

/**
 * Sprint 57.143 (AD-UserStop-Resume-Context): tell the server a running session was
 * stopped by the user. POST /api/v1/chat/sessions/{sessionId}/cancel flips the
 * session to cancelled AND records a `[Request interrupted by user]` marker in the
 * message ledger, so a follow-up "continue" send rehydrates a coherent transcript.
 * Called fire-and-forget from the Stop handler (the client also aborts the SSE for an
 * immediate stop); a non-2xx throws so the caller may choose to surface / ignore it.
 */
export async function cancelSession(sessionId: string): Promise<void> {
  const response = await fetchWithAuth(`/api/v1/chat/sessions/${sessionId}/cancel`, {
    method: "POST",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
}

/**
 * Read a `text/event-stream` Response body to completion, parsing each SSE
 * frame and dispatching valid LoopEvents to onEvent. Aborts cleanly (no further
 * onEvent) when the signal fires; other read errors route to onError. Shared by
 * streamChat + resumeChat (the response/ok handling differs; the consumption
 * does not).
 */
async function consumeSSEStream(
  response: Response,
  opts: StreamChatOptions,
): Promise<void> {
  const body_ = response.body;
  if (!body_) {
    opts.onError?.(new Error("response body is null"));
    return;
  }

  const reader = body_.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames separated by blank line "\n\n".
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const ev = parseSSEFrame(frame);
        if (ev !== null) opts.onEvent(ev);
      }
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    opts.onError?.(err as Error);
  }
}

function parseSSEFrame(frame: string): LoopEvent | null {
  let eventType = "";
  let dataLine = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event: ")) eventType = line.slice("event: ".length);
    else if (line.startsWith("data: ")) dataLine = line.slice("data: ".length);
  }
  if (!eventType || !dataLine) return null;
  if (!KNOWN_LOOP_EVENT_TYPES.has(eventType)) {
    // Defer / Unknown event from later sprints — drop frame, do not crash.
    return null;
  }
  try {
    const parsed = JSON.parse(dataLine) as Record<string, unknown>;
    // Cast is safe because KNOWN_LOOP_EVENT_TYPES gate above + backend
    // sse.py serializer guarantees the payload shape.
    return { type: eventType, data: parsed } as unknown as LoopEvent;
  } catch {
    return null;
  }
}
