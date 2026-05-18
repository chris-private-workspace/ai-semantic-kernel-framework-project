/**
 * File: frontend/src/features/chat_v2/components/SessionList.tsx
 * Purpose: Sessions sidebar — fixture-driven list with status indicator + domain dot.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 3 §3.1 + §3.3 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Left rail of the 3-column chat shell (mockup L123-156). Renders the 6
 *   fixture sessions from `../fixtures/sessions.ts` (verbatim port of mockup
 *   `SESSIONS` L5-12). Active session highlight is driven by
 *   chatStore.activeSessionId; click → setActiveSessionId.
 *
 *   §3.3 AP-2 compliance — yellow demo banner sits above the sessions list to
 *   make the fixture status visible (backend wire deferred to Sprint 57.22+
 *   AD-ChatV2-SessionList-Backend; session click does NOT yet rebuild a live
 *   conversation stream, only updates the highlight state).
 *
 *   `DomainDot` (mockup L153-156) is inlined here per checklist §3.1 to keep
 *   the component count small; if a 2nd consumer appears Sprint 57.22+ it
 *   should be extracted to a shared primitive.
 *
 * Key Components:
 *   - <SessionList />: top-level export; consumes FIXTURE_SESSIONS
 *   - DomainDot: inline color mapper (incident/audit/patrol/rca)
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1 + §3.3)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L5-12 (SESSIONS) + L123-156 (SessionList) + L153-156 (DomainDot)
 *   - ../fixtures/sessions.ts (FIXTURE_SESSIONS)
 *   - ../store/chatStore.ts (activeSessionId + setActiveSessionId)
 *   - ../types.ts (Session / SessionDomain / SessionStatusUI)
 *   - frontend/STYLE.md §2 (verified tokens: bg-bg-1 / text-fg-muted / border-border / bg-warning)
 */

import { Filter, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { FIXTURE_SESSIONS } from "../fixtures/sessions";
import { useChatStore } from "../store/chatStore";
import type { Session, SessionDomain } from "../types";

const DOMAIN_COLOR: Record<SessionDomain, string> = {
  incident: "bg-danger",
  audit: "bg-memory",
  patrol: "bg-tool",
  rca: "bg-thinking",
};

function DomainDot({ domain }: { domain: SessionDomain }): JSX.Element {
  return (
    <span
      aria-hidden="true"
      className={cn("inline-block h-[7px] w-[7px] flex-shrink-0 rounded-full", DOMAIN_COLOR[domain])}
    />
  );
}

function SessionItem({ session }: { session: Session }): JSX.Element {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const setActiveSessionId = useChatStore((s) => s.setActiveSessionId);
  const { t } = useTranslation("common");
  const isActive = activeSessionId === session.id;

  return (
    <button
      type="button"
      data-active={isActive}
      data-testid={`session-item-${session.id}`}
      onClick={() => setActiveSessionId(session.id)}
      className={cn(
        "w-full cursor-pointer border-b border-border px-3 py-2.5 text-left transition-colors",
        "hover:bg-bg-hover",
        isActive && "bg-bg-2",
      )}
    >
      <div className="mb-1 flex items-center gap-1.5">
        <DomainDot domain={session.domain} />
        <span className="flex-1 truncate text-[13px] font-medium text-fg" title={session.title}>
          {session.title}
        </span>
        {session.status === "running" && (
          <span
            aria-label={t("chat.session.status.running")}
            title={t("chat.session.status.running") ?? "running"}
            className="inline-block h-2 w-2 flex-shrink-0 animate-pulse rounded-full bg-warning"
          />
        )}
        {session.status === "hitl" && (
          <Badge variant="outline" className="border-warning/40 bg-warning/16 text-[10px] text-warning">
            {t("chat.session.status.hitl")}
          </Badge>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-1 text-[11px] text-fg-muted">
        <span>{session.agent}</span>
        <span>·</span>
        <span>{t("chat.session.meta.turns", { count: session.turns })}</span>
        <span>·</span>
        <span>{session.time}</span>
      </div>
    </button>
  );
}

export function SessionList(): JSX.Element {
  const { t } = useTranslation("common");

  return (
    <div
      className="flex h-full flex-col overflow-y-auto bg-bg-1 text-fg"
      data-testid="session-list"
    >
      {/* §3.3 Demo banner — AP-2 compliance */}
      <div
        role="note"
        data-testid="session-list-demo-banner"
        className="border-b border-warning/40 bg-warning/16 px-3 py-2 text-[11px] leading-snug text-warning"
      >
        {t("chat.session.demoBanner")}
      </div>

      {/* Top action bar — New session + Filter */}
      <div className="flex items-center gap-1.5 border-b border-border px-3 py-2.5">
        <Button size="sm" className="h-7 gap-1 px-2 text-xs">
          <Plus className="h-3 w-3" aria-hidden="true" />
          {t("chat.session.newSession")}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          aria-label={t("chat.session.filter") ?? "Filter"}
          className="h-7 w-7 p-0"
        >
          <Filter className="h-3 w-3" aria-hidden="true" />
        </Button>
      </div>

      {/* Section label */}
      <div className="flex items-center justify-between px-3 py-2">
        <span className="font-mono text-[10.5px] uppercase tracking-wider text-fg-subtle">
          {t("chat.session.title")}
        </span>
        <span className="font-mono text-[10.5px] text-fg-subtle">{FIXTURE_SESSIONS.length}</span>
      </div>

      {/* Session items */}
      <div className="flex-1">
        {FIXTURE_SESSIONS.map((s) => (
          <SessionItem key={s.id} session={s} />
        ))}
      </div>
    </div>
  );
}

export default SessionList;
