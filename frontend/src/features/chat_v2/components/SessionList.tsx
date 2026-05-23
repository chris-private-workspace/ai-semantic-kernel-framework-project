/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-chat.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/SessionList.tsx
 * Purpose: Sessions sidebar — fixture-driven list with status indicator + domain dot.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 3 §3.1 + §3.3 → 57.30 Day 2 verbatim re-point
 *
 * Description:
 *   Mockup `page-chat.jsx` L123-156 — verbatim re-point of left rail.
 *
 *   Mockup CSS classes consumed verbatim (styles-mockup.css):
 *     - .chat-list (L693-697) — left rail wrapper with border + bg + overflow
 *     - .session-item (L726-737) — session row card; data-active drives highlight
 *     - .session-title (L738) — session title typography
 *     - .session-meta (L739) — metadata row typography
 *     - .row / .grow / .mono / .subtle (L613-620)
 *     - .live-dot (L649)
 *     - .badge / .badge.warning (L507-525)
 *
 *   Inline-style literals copied byte-for-byte from mockup L125, L129-131, L135,
 *   L155 (DomainDot). These are visual-layer literals per the verbatim re-point
 *   method.
 *
 *   §3.3 AP-2 demo banner above the sessions list is preserved (no mockup
 *   equivalent — production-only honesty); uses inline-style for the
 *   warning-tinted block matching the .badge.warning color shape.
 *
 *   `DomainDot` (mockup L153-156) is inlined here — color mapping uses mockup
 *   CSS vars (--danger / --memory / --tool / --thinking) directly.
 *
 * Key Components:
 *   - <SessionList />: top-level export; consumes FIXTURE_SESSIONS
 *   - DomainDot: inline color mapper (incident/audit/patrol/rca)
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C2 — verbatim re-point to mockup page-chat.jsx L123-156 SessionList markup (.chat-list, .session-item, .session-title, .session-meta, .live-dot, .badge)
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1 + §3.3)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L5-12 (SESSIONS) + L123-156 (SessionList) + L153-156 (DomainDot)
 *   - frontend/src/styles-mockup.css L693-739 (.chat-list / .session-item / .session-title / .session-meta) / L649 (.live-dot) / L507-525 (.badge / .badge.warning)
 *   - ../fixtures/sessions.ts (FIXTURE_SESSIONS)
 *   - ../store/chatStore.ts (activeSessionId + setActiveSessionId)
 *   - ../types.ts (Session / SessionDomain / SessionStatusUI)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { Filter, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";

import { FIXTURE_SESSIONS } from "../fixtures/sessions";
import { useChatStore } from "../store/chatStore";
import type { Session, SessionDomain } from "../types";

// Mockup L154 verbatim — DomainDot CSS-var color map.
const DOMAIN_COLOR: Record<SessionDomain, string> = {
  incident: "var(--danger)",
  audit: "var(--memory)",
  patrol: "var(--tool)",
  rca: "var(--thinking)",
};

function DomainDot({ domain }: { domain: SessionDomain }): JSX.Element {
  // Mockup L155 inline-style literal verbatim.
  return (
    <span
      aria-hidden="true"
      style={{
        width: 7,
        height: 7,
        borderRadius: 50,
        background: DOMAIN_COLOR[domain],
        flexShrink: 0,
      }}
    />
  );
}

function SessionItem({ session }: { session: Session }): JSX.Element {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const setActiveSessionId = useChatStore((s) => s.setActiveSessionId);
  const { t } = useTranslation("common");
  const isActive = activeSessionId === session.id;

  return (
    <div
      className="session-item"
      data-active={isActive}
      data-testid={`session-item-${session.id}`}
      onClick={() => setActiveSessionId(session.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setActiveSessionId(session.id);
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="row" style={{ gap: 6, marginBottom: 4 }}>
        <DomainDot domain={session.domain} />
        <span className="session-title grow" title={session.title}>
          {session.title}
        </span>
        {session.status === "running" && (
          <span
            className="live-dot"
            aria-label={t("chat.session.status.running") ?? "running"}
            title={t("chat.session.status.running") ?? "running"}
          />
        )}
        {session.status === "hitl" && (
          <span className="badge warning">{t("chat.session.status.hitl")}</span>
        )}
      </div>
      <div className="session-meta">
        <span>{session.agent}</span>
        <span>·</span>
        <span>{t("chat.session.meta.turns", { count: session.turns })}</span>
        <span>·</span>
        <span>{session.time}</span>
      </div>
    </div>
  );
}

export function SessionList(): JSX.Element {
  const { t } = useTranslation("common");

  return (
    <div className="chat-list" data-testid="session-list">
      {/* §3.3 Demo banner — AP-2 compliance; production-only (no mockup equivalent).
          Inline-style mirrors .badge.warning color shape for visual continuity. */}
      <div
        role="note"
        data-testid="session-list-demo-banner"
        style={{
          borderBottom: "1px solid oklch(from var(--warning) l c h / 0.32)",
          background: "oklch(from var(--warning) l c h / 0.14)",
          color: "var(--warning)",
          padding: "8px 12px",
          fontSize: 11,
          lineHeight: 1.4,
        }}
      >
        {t("chat.session.demoBanner")}
      </div>

      {/* Top action bar — mockup L125-128 verbatim (.btn .ghost / .btn .primary) */}
      <div
        style={{
          padding: "10px 12px 8px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        <button type="button" className="btn primary" data-size="sm">
          <Plus size={12} aria-hidden="true" />
          {t("chat.session.newSession")}
        </button>
        <button
          type="button"
          className="btn ghost"
          data-size="sm"
          aria-label={t("chat.session.filter") ?? "Filter"}
        >
          <Filter size={12} aria-hidden="true" />
        </button>
      </div>

      {/* Section label — mockup L129-132 verbatim */}
      <div
        style={{
          padding: "8px 12px 6px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          className="mono"
          style={{
            fontSize: 10.5,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          {t("chat.session.title")}
        </span>
        <span className="mono" style={{ fontSize: 10.5, color: "var(--fg-subtle)" }}>
          {FIXTURE_SESSIONS.length}
        </span>
      </div>

      {/* Session items — mockup L133-149 verbatim */}
      {FIXTURE_SESSIONS.map((s) => (
        <SessionItem key={s.id} session={s} />
      ))}
    </div>
  );
}

export default SessionList;
