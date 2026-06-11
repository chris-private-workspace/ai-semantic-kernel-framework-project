/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-chat.jsx visual-layer literals copied byte-for-byte (composer shell shape); production-only status pill + mode toggle have no mockup equivalent (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/InputBar.tsx
 * Purpose: Bottom input bar — textarea + Send / Stop button + mode toggle (production send path).
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 4.3) → Sprint 57.16 Tailwind migration → 57.30 Day 2 verbatim re-point
 *
 * Description:
 *   Mockup `page-chat.jsx` ships only the **visual** Composer scaffolding (no
 *   wired send / mode toggle / status pill). InputBar.tsx is the **production
 *   send path** — preserves Sprint 50.2 → 57.16 logic:
 *     - idle / completed / cancelled / error: Send button enabled
 *     - running: Send button → Stop button (cancels via abort signal)
 *     - Mode toggle (echo_demo / real_llm) sits next to Send
 *     - Keyboard: Enter → send, Shift+Enter → newline
 *
 *   Sprint 57.30 Day 2 verbatim re-point — the **shell + button visuals** are
 *   re-pointed to mockup `.composer` / `.composer-inner` / `.composer-input` /
 *   `.btn` classes from styles-mockup.css L919-937 + L426-446 (matching the
 *   sibling Composer.tsx scaffolding). The **production-only widgets** (status
 *   pill, mode toggle, error banner) have no mockup equivalent — they use
 *   inline-style literals consistent with mockup token vocabulary (var(--*)).
 *
 *   STYLE.md §1 escape hatch applies — inline styles here are verbatim mockup
 *   literals OR production-only widgets with no mockup counterpart; re-expressing
 *   them as Tailwind risks re-introducing the drift bug Sprint 57.18-57.27 root
 *   cause investigation identified.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 4.3)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Sprint 57.101 B1 — composer usable mid-run (real_llm) → Inject button routes to inject()
 *   - 2026-06-06: chat-v2 honest surface — mode-button tooltips + echo_demo "echoes input" note; +useTranslation (CHANGE-054)
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C2 — verbatim re-point to mockup composer shell (.composer / .composer-inner / .composer-input / .btn primary / .btn danger / .btn ghost)
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration text-muted-foreground→text-fg-muted; bg-muted-foreground→bg-fg-muted (disabled Send) for new shell mockup consistency
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes; statusPill/modeButton/sendBtn → finite class lookup (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.3)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L316-368 (Composer visual reference)
 *   - frontend/src/styles-mockup.css L919-937 (.composer / .composer-inner / .composer-input / .composer-tools) / L426-446 (.btn variants)
 *   - ../hooks/useLoopEventStream.ts (send / cancel)
 *   - ../store/chatStore.ts (status / mode / errorMessage)
 *   - ./Composer.tsx (sibling visual scaffolding; non-wired)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { useState, type CSSProperties, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";

import { useLoopEventStream } from "../hooks/useLoopEventStream";
import { useChatStore } from "../store/chatStore";
import type { ChatMode } from "../types";

// 4-way status pill (production-only; no mockup equivalent). Each entry maps to
// a mockup CSS-var color so visual continuity with .badge / Cat 9 risk palette holds.
const STATUS_PILL: Record<string, { label: string; color: string }> = {
  running: { label: "● running", color: "var(--primary)" },
  completed: { label: "● completed", color: "var(--success)" },
  cancelled: { label: "● cancelled", color: "var(--warning)" },
  error: { label: "● error", color: "var(--danger)" },
};

function getPill(status: string): { label: string; color: string } {
  return STATUS_PILL[status] ?? { label: "○ idle", color: "var(--fg-muted)" };
}

export default function InputBar(): JSX.Element {
  const { t } = useTranslation("common");
  const [text, setText] = useState("");
  const status = useChatStore((s) => s.status);
  const mode = useChatStore((s) => s.mode);
  const setMode = useChatStore((s) => s.setMode);
  const errorMessage = useChatStore((s) => s.errorMessage);
  const { send, cancel, inject, isRunning } = useLoopEventStream();
  // Sprint 57.101 (B1): mid-run injection is a real_llm capability — the echo_demo
  // mock is scripted + completes in ms, so it cannot act on a mid-run note (gating
  // it here avoids a dead control in echo mode per the Drive-Through rule).
  const canInject = isRunning && mode === "real_llm";

  const onSend = (): void => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (isRunning) {
      if (!canInject) return; // echo_demo running: textarea is disabled anyway
      setText("");
      void inject(trimmed); // mid-run: send a supplementary instruction (next turn)
      return;
    }
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

  // Production-only widget styles (no mockup equivalent) — kept as inline-style
  // literals using mockup CSS-var token vocabulary for visual continuity.
  const errorBoxStyle: CSSProperties = {
    border: "1px solid oklch(from var(--danger) l c h / 0.4)",
    background: "oklch(from var(--danger) l c h / 0.1)",
    color: "var(--danger)",
    padding: "6px 10px",
    borderRadius: 4,
    fontSize: 12,
  };

  const topRowStyle: CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: 10,
    fontSize: 12,
    color: "var(--fg-muted)",
    marginBottom: 6,
  };

  const modeButtonStyle = (active: boolean): CSSProperties => ({
    cursor: isRunning ? "not-allowed" : "pointer",
    border: "1px solid var(--border)",
    background: active ? "var(--primary)" : "var(--bg)",
    color: active ? "white" : "var(--fg-muted)",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    fontFamily: "var(--font-mono)",
  });

  return (
    <div className="composer" data-testid="input-bar">
      {errorMessage && <div style={errorBoxStyle}>{errorMessage}</div>}

      <div style={topRowStyle}>
        <span style={{ color: pill.color, fontWeight: 500 }}>{pill.label}</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 4 }}>
          <span>mode:</span>
          {modes.map((m) => (
            <button
              key={m}
              type="button"
              style={modeButtonStyle(mode === m)}
              onClick={() => setMode(m)}
              disabled={isRunning}
              title={
                m === "echo_demo"
                  ? t("chat.composer.echoModeTitle")
                  : t("chat.composer.realModeTitle")
              }
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Honest-surface: echo_demo mirrors the input (offline mock) — make that
          explicit so a tester doesn't mistake the echo for a real LLM answer. */}
      {mode === "echo_demo" && (
        <div style={{ fontSize: 11, color: "var(--warning)", marginBottom: 6 }}>
          {t("chat.composer.echoModeNote")}
        </div>
      )}

      <div className="composer-inner">
        <textarea
          className="composer-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
          placeholder={
            canInject
              ? "Add an instruction for the running agent…  (it picks it up next turn)"
              : "Ask the agent…  (Enter to send, Shift+Enter for newline)"
          }
          rows={2}
          disabled={isRunning && !canInject}
        />
        <div className="composer-tools">
          <div className="grow" />
          {isRunning ? (
            <>
              {canInject && (
                <button
                  type="button"
                  className="btn primary"
                  data-size="sm"
                  data-testid="inject-send"
                  onClick={onSend}
                  disabled={sendDisabled}
                  style={sendDisabled ? { opacity: 0.5, cursor: "not-allowed" } : undefined}
                  title="Send a supplementary instruction to the running agent (it acts on it next turn)"
                >
                  Inject
                </button>
              )}
              <button type="button" className="btn danger" data-size="sm" onClick={cancel}>
                Stop
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn primary"
              data-size="sm"
              onClick={onSend}
              disabled={sendDisabled}
              style={sendDisabled ? { opacity: 0.5, cursor: "not-allowed" } : undefined}
            >
              Send
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
