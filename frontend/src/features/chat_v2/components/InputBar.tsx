/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: inline styles deferred (chat-v2 batch — migrated in a follow-up sprint). */
/**
 * File: frontend/src/features/chat_v2/components/InputBar.tsx
 * Purpose: Bottom input bar — textarea + Send / Stop button + mode toggle.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 4.3)
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
 * Created: 2026-04-30 (Sprint 50.2 Day 4.3)
 * Last Modified: 2026-04-30
 *
 * Modification History:
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.3)
 *
 * Related:
 *   - ../hooks/useLoopEventStream.ts (send / cancel)
 *   - ../store/chatStore.ts (status / mode / errorMessage)
 */

import { useState, type CSSProperties, type KeyboardEvent } from "react";
import { useLoopEventStream } from "../hooks/useLoopEventStream";
import { useChatStore } from "../store/chatStore";
import type { ChatMode } from "../types";

const styles: Record<string, CSSProperties> = {
  container: {
    borderTop: "1px solid #e2e6ee",
    background: "#fff",
    padding: "0.75rem 1.5rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
  },
  topRow: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
    fontSize: 12,
    color: "#7c8696",
  },
  modeToggle: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "0.3rem",
  },
  inputRow: {
    display: "flex",
    gap: "0.6rem",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    resize: "none",
    border: "1px solid #d8dde7",
    borderRadius: 8,
    padding: "0.6rem 0.8rem",
    fontFamily: "inherit",
    fontSize: 14,
    lineHeight: 1.5,
    minHeight: 44,
    maxHeight: 160,
    outline: "none",
  },
  stopBtn: {
    padding: "0.55rem 1.1rem",
    borderRadius: 8,
    border: "none",
    background: "#c43d3d",
    color: "#fff",
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
  },
  errorBanner: {
    background: "#fff5f5",
    color: "#9d2e2e",
    border: "1px solid #f5c2c2",
    padding: "0.4rem 0.6rem",
    borderRadius: 6,
    fontSize: 12,
  },
};

const statusStyle = (color: string): CSSProperties => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  color,
  fontWeight: 500,
});

const modeButton = (active: boolean): CSSProperties => ({
  padding: "0.2rem 0.55rem",
  borderRadius: 4,
  border: "1px solid #d8dde7",
  background: active ? "#5a78c8" : "#fff",
  color: active ? "#fff" : "#5a6377",
  fontSize: 11,
  cursor: "pointer",
});

const sendBtn = (disabled: boolean): CSSProperties => ({
  padding: "0.55rem 1.1rem",
  borderRadius: 8,
  border: "none",
  background: disabled ? "#c0c8d6" : "#5a78c8",
  color: "#fff",
  fontSize: 14,
  fontWeight: 500,
  cursor: disabled ? "not-allowed" : "pointer",
});

function statusPill(status: string): { label: string; color: string } {
  switch (status) {
    case "running":
      return { label: "● running", color: "#5a78c8" };
    case "completed":
      return { label: "● completed", color: "#2f9c59" };
    case "cancelled":
      return { label: "● cancelled", color: "#a26d23" };
    case "error":
      return { label: "● error", color: "#c43d3d" };
    default:
      return { label: "○ idle", color: "#7c8696" };
  }
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

  const pill = statusPill(status);
  const modes: ChatMode[] = ["echo_demo", "real_llm"];

  return (
    <div style={styles.container}>
      {errorMessage && <div style={styles.errorBanner}>{errorMessage}</div>}
      <div style={styles.topRow}>
        <span style={statusStyle(pill.color)}>{pill.label}</span>
        <div style={styles.modeToggle}>
          <span>mode:</span>
          {modes.map((m) => (
            <button
              key={m}
              style={modeButton(mode === m)}
              onClick={() => setMode(m)}
              disabled={isRunning}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <div style={styles.inputRow}>
        <textarea
          style={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask the agent…  (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={isRunning}
        />
        {isRunning ? (
          <button style={styles.stopBtn} onClick={cancel}>
            Stop
          </button>
        ) : (
          <button
            style={sendBtn(text.trim().length === 0)}
            onClick={onSend}
            disabled={text.trim().length === 0}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
