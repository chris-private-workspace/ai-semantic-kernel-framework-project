/**
 * File: frontend/src/features/chat_v2/services/chatService.ts
 * Purpose: Browser SSE consumer — fetch + ReadableStream parser.
 * Category: Frontend / chat_v2 / services
 * Scope: Phase 50 / Sprint 50.2 (Day 3.4) → Sprint 57.8 Day 3 D3 fetchWithAuth swap
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
 * Created: 2026-04-30 (Sprint 50.2 Day 3.4)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.8 D3 — swap raw fetch to fetchWithAuth (JWT injection)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.4)
 *
 * Related:
 *   - backend POST /api/v1/chat/ (router.py)
 *   - ../hooks/useLoopEventStream.ts (consumer)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import { KNOWN_LOOP_EVENT_TYPES, type ChatMode, type LoopEvent } from "../types";

export type ChatRequestBody = {
  message: string;
  mode: ChatMode;
  session_id?: string;
};

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
