/**
 * File: frontend/src/features/chat_v2/components/InputBar.tsx
 * Purpose: Bottom input bar — textarea + Send / Stop button + mode toggle.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 4.3) → Sprint 57.16 Tailwind migration
 *
 * Description:
 *   Two states:
 *     - idle / completed / cancelled / error: Send button enabled
 *     - running: Send button → Stop button (cancels via abort signal)
 *
 *   Mode toggle (echo_demo / real_llm) sits next to Send. real_llm requires
 *   AZURE_OPENAI_* env vars on the backend; if missing the POST returns 503
 *   and useLoopEventStream surfaces the error.
 *
 *   Keyboard:
 *     - Enter           → send
 *     - Shift+Enter     → newline
 *
 *   Sprint 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2): migrated to Tailwind
 *   utility classes. The 4-way status pill, mode-toggle active state, and
 *   send-button disabled state use finite class lookups (STATUS_PILL Record +
 *   inline `cn()` for the booleans); topRow text uses text-muted-foreground
 *   (AA-compliant; prerequisite for re-enabling color-contrast on /chat-v2).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 4.3)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes; statusPill/modeButton/sendBtn → finite class lookup (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.3)
 *
 * Related:
 *   - ../hooks/useLoopEventStream.ts (send / cancel)
 *   - ../store/chatStore.ts (status / mode / errorMessage)
 *   - frontend/STYLE.md §1 (no inline styles) + §2 (tokens)
 */

import { useState, type KeyboardEvent } from "react";

import { cn } from "../../../lib/utils";
import { useLoopEventStream } from "../hooks/useLoopEventStream";
import { useChatStore } from "../store/chatStore";
import type { ChatMode } from "../types";

// 4-way status pill (+ idle default). 57.15 vocab (`text-success` etc.) for
// visual continuity with TenantListTable / ApprovalCard; literal class strings
// so the Tailwind JIT sees them.
const STATUS_PILL: Record<string, { label: string; cls: string }> = {
  running: { label: "● running", cls: "text-primary" },
  completed: { label: "● completed", cls: "text-success" },
  cancelled: { label: "● cancelled", cls: "text-warning" },
  error: { label: "● error", cls: "text-danger" },
};

function getPill(status: string): { label: string; cls: string } {
  return STATUS_PILL[status] ?? { label: "○ idle", cls: "text-muted-foreground" };
}

export default function InputBar(): JSX.Element {
  const [text, setText] = useState("");
  const status = useChatStore((s) => s.status);
  const mode = useChatStore((s) => s.mode);
  const setMode = useChatStore((s) => s.setMode);
  const errorMessage = useChatStore((s) => s.errorMessage);
  const { send, cancel, isRunning } = useLoopEventStream();

  const onSend = (): void => {
    const trimmed = text.trim();
    if (!trimmed || isRunning) return;
    setText("");
    void send(trimmed);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const pill = getPill(status);
  const modes: ChatMode[] = ["echo_demo", "real_llm"];
  const sendDisabled = text.trim().length === 0;

  return (
    <div className="flex flex-col gap-2 border-t border-border bg-background px-6 py-3">
      {errorMessage && (
        <div className="rounded border border-danger/40 bg-danger/10 px-2.5 py-1.5 text-xs text-danger">
          {errorMessage}
        </div>
      )}
      <div className="flex items-center gap-2.5 text-xs text-muted-foreground">
        <span className={cn("inline-flex items-center gap-1 font-medium", pill.cls)}>
          {pill.label}
        </span>
        <div className="ml-auto flex items-center gap-1">
          <span>mode:</span>
          {modes.map((m) => (
            <button
              key={m}
              className={cn(
                "cursor-pointer rounded-sm border border-border px-2 py-0.5 text-[11px]",
                mode === m ? "bg-primary text-white" : "bg-background text-muted-foreground",
              )}
              onClick={() => setMode(m)}
              disabled={isRunning}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-end gap-2.5">
        <textarea
          className="max-h-40 min-h-11 flex-1 resize-none rounded-md border border-border px-3 py-2.5 text-sm leading-relaxed outline-none"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask the agent…  (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={isRunning}
        />
        {isRunning ? (
          <button
            className="cursor-pointer rounded-md border-none bg-danger px-4 py-2.5 text-sm font-medium text-white"
            onClick={cancel}
          >
            Stop
          </button>
        ) : (
          <button
            className={cn(
              "rounded-md border-none px-4 py-2.5 text-sm font-medium text-white",
              sendDisabled ? "cursor-not-allowed bg-muted-foreground" : "cursor-pointer bg-primary",
            )}
            onClick={onSend}
            disabled={sendDisabled}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
