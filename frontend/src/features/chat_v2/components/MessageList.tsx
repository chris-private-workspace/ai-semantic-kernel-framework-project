/**
 * File: frontend/src/features/chat_v2/components/MessageList.tsx
 * Purpose: Renders the rolling conversation — user / assistant / tool cards.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 4.1)
 *
 * Description:
 *   Subscribes to chatStore.messages and renders one row per message. Each
 *   assistant message embeds 0..N ToolCallCards inline. Auto-scrolls to the
 *   bottom whenever message count grows.
 *
 *   Status pill is rendered above the input area (in InputBar) — this
 *   component focuses on the message list only.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 4.1)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.1)
 *
 * Related:
 *   - ../store/chatStore.ts (subscribes to messages)
 *   - ToolCallCard.tsx (per-tool-call panel)
 */

import { useEffect, useRef } from "react";

import { useChatStore } from "../store/chatStore";
import type { Message } from "../types";
import { ApprovalCard } from "./ApprovalCard";
import ToolCallCard from "./ToolCallCard";

const BUBBLE_BASE =
  "whitespace-pre-wrap break-words rounded-xl px-3.5 py-2.5 text-sm leading-normal";

function MessageRow({ msg }: { msg: Message }): JSX.Element {
  if (msg.kind === "user") {
    return (
      <div className="max-w-[min(720px,90%)] self-end">
        <div className={`${BUBBLE_BASE} rounded-br bg-primary text-white`}>{msg.content}</div>
      </div>
    );
  }
  // assistant
  return (
    <div className="max-w-[min(720px,90%)] w-[min(720px,90%)] self-start">
      <div className={`${BUBBLE_BASE} rounded-bl border border-border bg-card text-foreground`}>
        {msg.thinking !== null && msg.thinking !== "" && (
          <div className="mb-1.5 text-xs italic text-muted-foreground">
            thinking: {msg.thinking}
          </div>
        )}
        {msg.content && <div>{msg.content}</div>}
        {msg.toolCalls.length > 0 && (
          <div className="mt-2.5 flex flex-col gap-2">
            {msg.toolCalls.map((tc) => (
              <ToolCallCard key={tc.toolCallId} entry={tc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function MessageList(): JSX.Element {
  const messages = useChatStore((s) => s.messages);
  const approvals = useChatStore((s) => s.approvals);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Sort approvals by receivedAt (chronological with messages).
  const approvalEntries = Object.values(approvals).sort(
    (a, b) => a.receivedAt - b.receivedAt,
  );

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, approvalEntries.length]);

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-6" ref={scrollRef}>
      {messages.length === 0 && approvalEntries.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted-foreground">
          Type a message below to start. Try <code>echo hello</code> in echo_demo
          mode.
        </div>
      ) : (
        <>
          {messages.map((m) => (
            <MessageRow key={m.id} msg={m} />
          ))}
          {approvalEntries.map((a) => (
            <ApprovalCard key={a.approvalRequestId} approvalRequestId={a.approvalRequestId} />
          ))}
        </>
      )}
    </div>
  );
}
