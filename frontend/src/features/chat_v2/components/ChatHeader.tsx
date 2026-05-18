/**
 * File: frontend/src/features/chat_v2/components/ChatHeader.tsx
 * Purpose: Top header of the chat center column — title + badges + streaming + actions + panel toggles.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 3 §3.2 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Mockup L93-121 — center column header. Renders:
 *     - Left panel toggle button (collapse / expand sessions sidebar)
 *     - Gradient warn icon (danger → warning) per mockup
 *     - Session title + agent / model / provider / turns metadata row
 *     - Streaming indicator (live-dot + "streaming" mono text) when active
 *     - Loop button (link to /loop-debug) + Audit button
 *     - Right panel toggle (collapse / expand inspector sidebar)
 *
 *   Data sources:
 *     - chatStore.activeSessionId → FIXTURE_SESSIONS lookup for title/agent/turns
 *     - chatStore.status === "running" → streaming indicator visibility
 *
 *   Token migration note: this is Day 3 NEW work, uses Sprint 57.18+ mockup
 *   token vocabulary directly (bg-bg-1 / text-fg / text-fg-muted / etc.) per
 *   STYLE.md §2.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.2)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L93-121 (ChatHeader source)
 *   - ../fixtures/sessions.ts (FIXTURE_SESSIONS for title lookup)
 *   - ../store/chatStore.ts (activeSessionId + status)
 *   - frontend/STYLE.md §2
 */

import { Activity, AlertTriangle, PanelLeft, PanelRight, ScrollText } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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
    <header
      data-testid="chat-header"
      className="flex items-center gap-2.5 border-b border-border bg-bg-1 px-5 py-2.5"
    >
      {/* Left panel toggle */}
      <button
        type="button"
        data-testid="chat-header-toggle-list"
        data-active={listOpen}
        aria-label={t("chat.header.toggleList") ?? "Toggle session list"}
        title={t("chat.header.toggleList") ?? undefined}
        onClick={onToggleList}
        className={cn(
          "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border text-fg-muted",
          "hover:bg-bg-hover hover:text-fg",
          listOpen && "bg-bg-2 text-fg",
        )}
      >
        <PanelLeft className="h-3.5 w-3.5" aria-hidden="true" />
      </button>

      {/* Gradient warn icon */}
      <div
        aria-hidden="true"
        className="flex h-[26px] w-[26px] flex-shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-danger to-warning"
      >
        <AlertTriangle className="h-3 w-3 text-white" />
      </div>

      {/* Title + metadata row */}
      <div className="min-w-0 flex-1 overflow-hidden">
        <h2 className="m-0 truncate text-[13px] font-semibold text-fg" title={titleText}>
          {titleText}
        </h2>
        <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[11px]">
          <Badge variant="outline" className="border-border bg-bg-2 px-1.5 py-0 text-[10px] text-fg-muted">
            {agentText}
          </Badge>
          <Badge variant="outline" className="border-thinking/40 bg-thinking/16 px-1.5 py-0 text-[10px] text-thinking">
            claude-haiku-4-5
          </Badge>
          <span className="font-mono text-[10px] text-fg-subtle">{t("chat.header.providerNeutral")}</span>
          <span className="text-[11px] text-fg-subtle">· {t("chat.session.meta.turns", { count: turnCount })}</span>
        </div>
      </div>

      {/* Streaming indicator */}
      {isStreaming && (
        <span className="flex items-center gap-1.5" aria-live="polite">
          <span aria-hidden="true" className="inline-block h-2 w-2 animate-pulse rounded-full bg-warning" />
          <span className="font-mono text-[11px] text-fg-muted">{t("chat.header.streaming")}</span>
        </span>
      )}

      {/* Loop + Audit actions */}
      <Button
        size="sm"
        variant="ghost"
        className="h-7 gap-1 px-2 text-xs"
        onClick={() => {
          window.location.hash = "loop-debug";
        }}
      >
        <Activity className="h-3 w-3" aria-hidden="true" />
        {t("chat.header.loopButton")}
      </Button>
      <Button size="sm" variant="ghost" className="h-7 gap-1 px-2 text-xs">
        <ScrollText className="h-3 w-3" aria-hidden="true" />
        {t("chat.header.auditButton")}
      </Button>

      {/* Right panel toggle */}
      <button
        type="button"
        data-testid="chat-header-toggle-inspector"
        data-active={inspOpen}
        aria-label={t("chat.header.toggleInspector") ?? "Toggle inspector"}
        title={t("chat.header.toggleInspector") ?? undefined}
        onClick={onToggleInsp}
        className={cn(
          "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border text-fg-muted",
          "hover:bg-bg-hover hover:text-fg",
          inspOpen && "bg-bg-2 text-fg",
        )}
      >
        <PanelRight className="h-3.5 w-3.5" aria-hidden="true" />
      </button>
    </header>
  );
}

export default ChatHeader;
