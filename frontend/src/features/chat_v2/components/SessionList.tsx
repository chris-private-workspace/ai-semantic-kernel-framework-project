/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-chat.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/SessionList.tsx
 * Purpose: Sessions sidebar — real backend session list with status indicator + handoff-chain badge.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 3 §3.1 + §3.3 → 57.30 Day 2 verbatim re-point → 57.107 B3 real-backend wiring
 *
 * Description:
 *   Mockup `page-chat.jsx` L123-156 — verbatim re-point of left rail.
 *
 *   Sprint 57.107 B3: replaced the FIXTURE_SESSIONS demo source with the real
 *   GET /api/v1/sessions list (chatStore.loadSessions, fetched on mount). The
 *   §3.3 DEMO banner + DEMO tag are removed (the data is real now). A session
 *   whose `handoffParentId` is non-null renders a small `.route-pill` chain
 *   badge (`↳ {agentRole}`). Empty list → a plain "No sessions yet" line.
 *
 *   Mockup CSS classes consumed verbatim (styles-mockup.css):
 *     - .chat-list (L693-697) — left rail wrapper with border + bg + overflow
 *     - .session-item (L726-737) — session row card; data-active drives highlight
 *     - .session-title (L738) — session title typography
 *     - .session-meta (L739) — metadata row typography
 *     - .row / .grow / .mono / .subtle (L613-620)
 *     - .live-dot (L649)
 *     - .badge / .badge.warning (L507-525)
 *     - .route-pill (L1101) — handoff-chain badge (reused from Sprint 57.101)
 *
 *   Inline-style literals copied byte-for-byte from mockup L125, L129-131, L135.
 *   These are visual-layer literals per the verbatim re-point method.
 *
 * Key Components:
 *   - <SessionList />: top-level export; consumes chatStore.sessions (real data)
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 * Last Modified: 2026-06-12
 *
 * Modification History:
 *   - 2026-07-15: "New session" → newSession() (was reset()) — keep sidebar list (AD-Chat-New-Session-Wipes-Sidebar)
 *   - 2026-06-16: Sprint 57.126 — session click → loadSessionHistory (replay) replaces setActiveSessionId
 *   - 2026-06-12: Sprint 57.107 B3 — real GET /sessions via loadSessions; drop fixture + DEMO banner; +handoff-chain badge + empty state
 *   - 2026-06-06: chat-v2 honest surface — wire "New session" → store.reset() (was a no-op button) + DEMO badge on section header (fixture list honesty) (CHANGE-054)
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C2 — verbatim re-point to mockup page-chat.jsx L123-156 SessionList markup (.chat-list, .session-item, .session-title, .session-meta, .live-dot, .badge)
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1 + §3.3)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L5-12 (SESSIONS) + L123-156 (SessionList)
 *   - frontend/src/styles-mockup.css L693-739 (.chat-list / .session-item / .session-title / .session-meta) / L649 (.live-dot) / L507-525 (.badge / .badge.warning) / L1101 (.route-pill)
 *   - ../store/chatStore.ts (sessions + loadSessions + activeSessionId + setActiveSessionId)
 *   - ../services/chatService.ts (listSessions)
 *   - ../types.ts (Session / SessionStatusUI)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { useEffect } from "react";
import { Filter, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useChatStore } from "../store/chatStore";
import type { Session } from "../types";

function SessionItem({ session }: { session: Session }): JSX.Element {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  // Sprint 57.126: clicking a session now LOADS + replays its conversation (was
  // setActiveSessionId — highlight-only, a soft Potemkin). loadSessionHistory sets
  // activeSessionId itself, so the highlight still works.
  const loadSessionHistory = useChatStore((s) => s.loadSessionHistory);
  const { t } = useTranslation("common");
  const isActive = activeSessionId === session.id;
  const title = session.title ?? t("chat.session.titleFallback");

  return (
    <div
      className="session-item"
      data-active={isActive}
      data-testid={`session-item-${session.id}`}
      onClick={() => void loadSessionHistory(session.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          void loadSessionHistory(session.id);
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="row" style={{ gap: 6, marginBottom: 4 }}>
        <span className="session-title grow" title={title}>
          {title}
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
        {session.agent && (
          <>
            <span>{session.agent}</span>
            <span>·</span>
          </>
        )}
        <span>{t("chat.session.meta.turns", { count: session.turns })}</span>
        <span>·</span>
        <span>{session.time}</span>
      </div>
      {session.handoffParentId && (
        <div className="row" style={{ gap: 6, marginTop: 4 }}>
          <span className="route-pill" data-testid={`session-chain-${session.id}`}>
            {t("chat.session.chainBadge", { role: session.agentRole ?? "handoff" })}
          </span>
        </div>
      )}
    </div>
  );
}

export function SessionList(): JSX.Element {
  const { t } = useTranslation("common");
  // Honest-surface: "New session" was a visual-only button (no onClick). Wire it
  // to newSession() — a conversation-only reset that starts a fresh conversation
  // (clears turns / session id / inspector slices) while PRESERVING the sidebar
  // session list (AD-Chat-New-Session-Wipes-Sidebar: reset() blanked the list until
  // a page refresh re-fetched GET /sessions).
  const newSession = useChatStore((s) => s.newSession);
  const sessions = useChatStore((s) => s.sessions);
  const loadSessions = useChatStore((s) => s.loadSessions);

  // Sprint 57.107 B3: load the real session list on mount.
  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  return (
    <div className="chat-list" data-testid="session-list">
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
        <button
          type="button"
          className="btn primary"
          data-size="sm"
          onClick={() => newSession()}
        >
          <Plus size={12} aria-hidden="true" />
          {t("chat.session.newSession")}
        </button>
        {/* Honest-surface (Sprint 57.167, de-Potemkin 2): this button had no
            onClick — a dead control on the 主流量 (reality audit 2026-06-26,
            still unfixed at the 2026-07-15 re-scan). It is DISABLED rather than
            wired because the mockup it was ported from (page-chat.jsx:127,
            `<Button variant="ghost" size="sm" icon="filter" />`) defines no
            filter behaviour at all — inventing a filter UI here would breach the
            mockup-fidelity 禁止項「自創 widget」. The widget stays (deleting a
            mockup widget is also forbidden); only its inertness is now declared.
            Real filtering needs a mockup spec first → AD-SessionList-Filter-Real-Implementation. */}
        <button
          type="button"
          className="btn ghost"
          data-size="sm"
          disabled
          aria-label={t("chat.session.filter") ?? "Filter"}
          title={t("chat.session.filterUnavailable") ?? "Session filtering is not available yet"}
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
          {sessions.length}
        </span>
      </div>

      {/* Session items — mockup L133-149 verbatim */}
      {sessions.length === 0 ? (
        <div
          className="subtle"
          data-testid="session-list-empty"
          style={{ padding: "12px", fontSize: 12 }}
        >
          {t("chat.session.emptyState")}
        </div>
      ) : (
        sessions.map((s) => <SessionItem key={s.id} session={s} />)
      )}
    </div>
  );
}

export default SessionList;
