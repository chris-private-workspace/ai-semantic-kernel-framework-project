/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-chat.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/ChatHeader.tsx
 * Purpose: Top header of the chat center column — title + badges + streaming + actions + panel toggles.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 3 §3.2 → 57.30 Day 2 verbatim re-point
 *
 * Description:
 *   Mockup `page-chat.jsx` L93-121 — verbatim re-point of center-column header.
 *   Mockup CSS classes consumed verbatim:
 *     - .panel-toggle (styles-mockup.css L712-724) — square 26×26 toggle button
 *     - .row / .grow / .mono / .subtle (styles-mockup.css L613-620)
 *     - .live-dot (styles-mockup.css L649)
 *     - .provider-neutral (styles-mockup.css L1092)
 *
 *   Inline-style literals copied byte-for-byte from mockup L94, L98, L101, L102,
 *   L103, L107, L111, L113, L118 — these are visual-layer literals; re-expressing
 *   them as Tailwind is the drift bug Sprint 57.18-57.27 root cause investigation
 *   (claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md)
 *   identified. STYLE.md §1 escape hatch + frontend-mockup-fidelity.md.
 *
 *   Data sources (component-logic layer; preserved unchanged):
 *     - chatStore.activeSessionId → FIXTURE_SESSIONS lookup for title/agent/turns
 *     - chatStore.status === "running" → streaming indicator visibility
 *     - i18n via react-i18next ("common" namespace)
 *
 *   Mockup uses `Button variant="ghost" size="sm" icon="loop"` shadcn-foreign shape
 *   for Loop / Audit actions. Production retains shadcn `<Button>` because the
 *   mockup Button maps 1:1 onto the production primitive AND no DOM/class drift
 *   results — both render to the same `.h-7 px-2 text-xs` ghost button shape.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.2)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C2 — verbatim re-point to mockup page-chat.jsx L93-121 ChatHeader markup (.panel-toggle, inline-style literals byte-identical)
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.2)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L93-121 (ChatHeader source)
 *   - frontend/src/styles-mockup.css L712-724 (.panel-toggle) / L649 (.live-dot) / L613-620 (.row / .grow / .mono / .subtle) / L1092 (.provider-neutral)
 *   - ../fixtures/sessions.ts (FIXTURE_SESSIONS for title lookup)
 *   - ../store/chatStore.ts (activeSessionId + status)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { Activity, AlertTriangle, PanelLeft, PanelRight, ScrollText } from "lucide-react";
import { useTranslation } from "react-i18next";

import { FIXTURE_SESSIONS } from "../fixtures/sessions";
import { useChatStore } from "../store/chatStore";

type Props = {
  listOpen: boolean;
  inspOpen: boolean;
  onToggleList: () => void;
  onToggleInsp: () => void;
};

export function ChatHeader({ listOpen, inspOpen, onToggleList, onToggleInsp }: Props): JSX.Element {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const status = useChatStore((s) => s.status);
  const totalTurns = useChatStore((s) => s.totalTurns);
  const { t } = useTranslation("common");

  const active = activeSessionId
    ? FIXTURE_SESSIONS.find((s) => s.id === activeSessionId)
    : undefined;
  const titleText = active?.title ?? "New session";
  const agentText = active?.agent ?? "incident-responder";
  // Prefer live totalTurns once a real session is running; otherwise show fixture turns.
  const turnCount = totalTurns > 0 ? totalTurns : (active?.turns ?? 0);
  const isStreaming = status === "running";

  return (
    <div
      data-testid="chat-header"
      style={{
        padding: "10px 20px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: 10,
        background: "var(--bg-1)",
      }}
    >
      {/* Left panel toggle — mockup L95-97 */}
      <button
        type="button"
        className="panel-toggle"
        data-testid="chat-header-toggle-list"
        data-active={listOpen}
        aria-label={t("chat.header.toggleList") ?? "Toggle session list"}
        title={t("chat.header.toggleList") ?? undefined}
        onClick={onToggleList}
      >
        <PanelLeft size={14} aria-hidden="true" />
      </button>

      {/* Gradient warn icon — mockup L98-100 */}
      <div
        aria-hidden="true"
        style={{
          width: 26,
          height: 26,
          borderRadius: 6,
          background: "linear-gradient(135deg, var(--danger), var(--warning))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <AlertTriangle size={13} style={{ color: "white" }} />
      </div>

      {/* Title + metadata row — mockup L101-109 */}
      <div style={{ minWidth: 0, overflow: "hidden" }}>
        <div
          style={{
            fontWeight: 600,
            fontSize: 13,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
          title={titleText}
        >
          {titleText}
        </div>
        <div className="row" style={{ gap: 6, marginTop: 2, flexWrap: "wrap" }}>
          <span className="badge">{agentText}</span>
          <span className="badge thinking">claude-haiku-4-5</span>
          <span className="provider-neutral">{t("chat.header.providerNeutral")}</span>
          <span className="subtle" style={{ fontSize: 11 }}>
            · {t("chat.session.meta.turns", { count: turnCount })}
          </span>
        </div>
      </div>

      {/* Grow spacer — mockup L110 */}
      <div className="grow" />

      {/* Streaming indicator — mockup L111-114 (gated on running status) */}
      {isStreaming && (
        <span className="row" style={{ gap: 6 }} aria-live="polite">
          <span className="live-dot" />
          <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>
            {t("chat.header.streaming")}
          </span>
        </span>
      )}

      {/* Loop + Audit actions — mockup L115-116 (verbatim .btn .ghost [data-size="sm"]) */}
      <button
        type="button"
        className="btn ghost"
        data-size="sm"
        onClick={() => {
          window.location.hash = "loop-debug";
        }}
      >
        <Activity size={12} aria-hidden="true" />
        {t("chat.header.loopButton")}
      </button>
      <button type="button" className="btn ghost" data-size="sm">
        <ScrollText size={12} aria-hidden="true" />
        {t("chat.header.auditButton")}
      </button>

      {/* Right panel toggle — mockup L117-119 (icon mirrored via scaleX(-1)) */}
      <button
        type="button"
        className="panel-toggle"
        data-testid="chat-header-toggle-inspector"
        data-active={inspOpen}
        aria-label={t("chat.header.toggleInspector") ?? "Toggle inspector"}
        title={t("chat.header.toggleInspector") ?? undefined}
        onClick={onToggleInsp}
      >
        <PanelRight size={14} style={{ transform: "scaleX(-1)" }} aria-hidden="true" />
      </button>
    </div>
  );
}

export default ChatHeader;
