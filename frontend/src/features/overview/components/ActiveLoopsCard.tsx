/**
 * File: frontend/src/features/overview/components/ActiveLoopsCard.tsx
 * Purpose: /overview Active-loops card — 5-col loop rows fed by real useActiveLoops data.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:99-141`.
 *   Wraps the shared <CardShell>; body renders one mockup `loopRow` per item
 *   from useActiveLoops(10). The loop row is the mockup 5-col grid:
 *     [status badge] [agent + session / tenant + model] [turn + miniBar]
 *     [tokens] [since].
 *
 *   This is the ONE real-data widget on /overview, so it carries NO
 *   <BackendGapBanner>. Loading / error / empty states are preserved from
 *   the prior inline OverviewPage.ActiveLoopsCard implementation.
 *
 *   Backend gap (D-PRE-6 / AD-Loop-Session-Enrich-Phase58): the Loop type has
 *   no agent_name / model / max_turns. agent_name + model render as placeholder
 *   strings and max_turns is hardcoded 50, per the features/loops/types.ts
 *   header mandate. The 5-col layout is closed; agent/model enrichment pends
 *   Phase 58.
 *
 * Key Components:
 *   - ActiveLoopsCard: card + loop rows
 *   - relativeSince(): started_at_ms → "12s" / "4m" / "8m" relative label
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — extract from OverviewPage inline + D4 5-col layout
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:99-141 (loopRow canonical)
 *   - frontend/src/features/loops/hooks/useActiveLoops.ts (real data source)
 *   - frontend/src/features/loops/types.ts (Loop type + backend-gap mandate)
 *   - frontend/src/components/ui/CardShell.tsx (shared wrapper)
 */

import { ArrowRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { CardShell } from "@/components/ui/CardShell";
import { useAuthStore } from "@/features/auth/store/authStore";
import { useActiveLoops } from "@/features/loops/hooks/useActiveLoops";
import type { Loop } from "@/features/loops/types";

import { Badge, type Tone } from "./_primitives";

/** max_turns is a backend gap (D-PRE-6) — hardcoded until AD-Loop-Session-Enrich-Phase58. */
const MAX_TURNS = 50;

const STATUS_TONE: Record<string, Tone> = {
  running: "success",
  "hitl-paused": "warning",
  verifying: "thinking",
  error: "danger",
  ended: "muted",
};

/**
 * Compact relative-age label from an epoch-ms timestamp, matching the mockup
 * `since` column ("12s" / "4m" / "8m"). Falls back to "—" for invalid input.
 */
function relativeSince(startedAtMs: number): string {
  const deltaMs = Date.now() - startedAtMs;
  if (!Number.isFinite(deltaMs) || deltaMs < 0) return "—";
  const seconds = Math.floor(deltaMs / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  return `${Math.floor(minutes / 60)}h`;
}

export const ActiveLoopsCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const tenant = useAuthStore((s) => s.tenant);
  const { data, isLoading, error } = useActiveLoops(10);
  const items: Loop[] = data?.items ?? [];

  return (
    <CardShell
      title={t("overview.activeLoops.title")}
      subtitle={
        isLoading
          ? t("action.loading")
          : `${items.length} ${t("overview.activeLoops.subtitle")}`
      }
      actions={
        <button
          type="button"
          onClick={() => navigate("/loop-debug")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.activeLoops.openDebug")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClass=""
    >
      {error && (
        <div className="px-4 py-6 text-center text-[12px] text-danger" role="alert">
          {error.message}
        </div>
      )}
      {!error && !isLoading && items.length === 0 && (
        <div className="px-4 py-6 text-center text-[12px] text-fg-muted">
          {t("overview.activeLoops.empty")}
        </div>
      )}
      {!error && items.length > 0 && (
        <div>
          {items.map((loop) => {
            const pct = Math.min(100, (loop.turn_count / MAX_TURNS) * 100);
            const tone = STATUS_TONE[loop.status] ?? "muted";
            // D-PRE-6: backend Session ORM lacks agent_name / model — placeholders.
            const agentName = "agent";
            const model = "—";
            return (
              <button
                key={loop.session_id}
                type="button"
                onClick={() => navigate("/loop-debug")}
                className="grid w-full cursor-pointer grid-cols-[auto_1fr_auto_auto_auto] items-center gap-[10px] border-b border-border px-[10px] py-2 text-left text-[12.5px] last:border-0 hover:bg-bg-hover"
              >
                <Badge tone={tone} dot>
                  {loop.status}
                </Badge>
                <div className="flex min-w-0 flex-col gap-[2px]">
                  <div className="flex items-center gap-[6px] text-[12.5px]">
                    <span className="font-medium">{agentName}</span>
                    <span className="font-mono text-[11px] text-fg-subtle">
                      · {loop.session_id.slice(0, 8)}
                    </span>
                  </div>
                  <div className="flex items-center gap-[6px]">
                    <span className="font-mono text-[10.5px] text-fg-subtle">
                      {tenant?.code ?? "—"}
                    </span>
                    <span className="font-mono text-[10.5px] text-fg-subtle">
                      · {model}
                    </span>
                  </div>
                </div>
                <div className="flex w-20 flex-col gap-[3px]">
                  <span className="font-mono text-[10.5px] text-fg-subtle">
                    turn {loop.turn_count}/{MAX_TURNS}
                  </span>
                  <div className="relative h-1.5 overflow-hidden rounded-[3px] bg-bg-3">
                    <div
                      className={`absolute inset-0 origin-left ${pct > 80 ? "bg-warning" : "bg-primary"}`}
                      // eslint-disable-next-line no-restricted-syntax -- dynamic per-row progress fill per mockup parity (STYLE.md §1 escape hatch)
                      style={{ transform: `scaleX(${pct / 100})` }}
                    />
                  </div>
                </div>
                <span className="w-[60px] text-right font-mono text-[11px] text-fg-subtle">
                  {loop.token_usage.toLocaleString()} tok
                </span>
                <span className="w-9 text-right font-mono text-[11px] text-fg-subtle">
                  {relativeSince(loop.started_at_ms)}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </CardShell>
  );
};
