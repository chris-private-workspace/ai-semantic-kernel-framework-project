/**
 * File: frontend/src/features/overview/components/ActiveLoopsCard.tsx
 * Purpose: /overview Active-loops card — 5-col loop rows fed by real useActiveLoops data.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:99-141`.
 *   Wraps mockup-ui <Card> with bodyClass="flush"; body renders one mockup `loopRow`
 *   per item from useActiveLoops(10). The loop row is the mockup 5-col grid:
 *     [status badge] [agent + session / tenant + model] [turn + miniBar]
 *     [tokens] [since].
 *
 *   R6 (component-logic preserved): useActiveLoops(10) hook + loading / error /
 *   empty / populated branches all unchanged. Only the visual markup is re-pointed
 *   to verbatim mockup classes + inline-style consts.
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
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point to mockup .card/loopRow classes (drop Tailwind translation)
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — extract from OverviewPage inline + D4 5-col layout
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:99-141 (loopRow canonical)
 *   - frontend/src/features/loops/hooks/useActiveLoops.ts (real data source)
 *   - frontend/src/features/loops/types.ts (Loop type + backend-gap mandate)
 *   - frontend/src/components/mockup-ui.tsx (Card / Badge primitives)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Badge, Button, Card } from "@/components/mockup-ui";
import { useAuthStore } from "@/features/auth/store/authStore";
import { useActiveLoops } from "@/features/loops/hooks/useActiveLoops";
import type { Loop } from "@/features/loops/types";

// ───────────────── verbatim inline-style consts (from page-overview.jsx:17-27) ─────────────────

const loopRow: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "auto 1fr auto auto auto",
  gap: 10,
  alignItems: "center",
  padding: "8px 10px",
  borderBottom: "1px solid var(--border)",
  fontSize: 12.5,
  cursor: "pointer",
};

const miniBar: CSSProperties = {
  height: 6,
  borderRadius: 3,
  background: "var(--bg-3)",
  overflow: "hidden",
  position: "relative",
};

const miniBarFill: CSSProperties = {
  position: "absolute",
  inset: 0,
  transformOrigin: "left center",
};

// ───────────────── component-logic layer (R6 — preserved unchanged) ─────────────────

/** max_turns is a backend gap (D-PRE-6) — hardcoded until AD-Loop-Session-Enrich-Phase58. */
const MAX_TURNS = 50;

const STATUS_TONE: Record<string, string> = {
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
    <Card
      title={t("overview.activeLoops.title")}
      subtitle={
        isLoading
          ? t("action.loading")
          : `${items.length} ${t("overview.activeLoops.subtitle")}`
      }
      actions={
        <Button
          variant="ghost"
          size="sm"
          iconRight="arrow_right"
          onClick={() => navigate("/loop-debug")}
        >
          {t("overview.activeLoops.openDebug")}
        </Button>
      }
      bodyClass="flush"
    >
      {/* loading state — subtitle already shows "Loading…" via card-sub; no body div needed */}
      {/* error state */}
      {error && (
        <div style={{ padding: "24px 16px", textAlign: "center", fontSize: 12, color: "var(--danger)" } satisfies CSSProperties} role="alert">
          {error.message}
        </div>
      )}
      {/* empty state */}
      {!error && !isLoading && items.length === 0 && (
        <div style={{ padding: "24px 16px", textAlign: "center", fontSize: 12, color: "var(--fg-muted)" } satisfies CSSProperties}>
          {t("overview.activeLoops.empty")}
        </div>
      )}
      {/* populated state — verbatim loopRow from page-overview.jsx:106-139 */}
      {!error && items.length > 0 && (
        <div>
          {items.map((loop) => {
            const pct = Math.min(100, (loop.turn_count / MAX_TURNS) * 100);
            const tone = STATUS_TONE[loop.status] ?? "muted";
            // D-PRE-6: backend Session ORM lacks agent_name / model — placeholders.
            const agentName = "agent";
            const model = "—";
            return (
              <div
                key={loop.session_id}
                style={loopRow}
                onClick={() => navigate("/loop-debug")}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") navigate("/loop-debug"); }}
              >
                <Badge tone={tone} dot>{loop.status}</Badge>
                <div className="col" style={{ gap: 2, minWidth: 0 } satisfies CSSProperties}>
                  <div className="row" style={{ gap: 6, fontSize: 12.5 } satisfies CSSProperties}>
                    <span style={{ fontWeight: 500 } satisfies CSSProperties}>{agentName}</span>
                    <span className="mono subtle" style={{ fontSize: 11 } satisfies CSSProperties}>· {loop.session_id.slice(0, 8)}</span>
                  </div>
                  <div className="row" style={{ gap: 6 } satisfies CSSProperties}>
                    <span className="mono subtle" style={{ fontSize: 10.5 } satisfies CSSProperties}>{tenant?.code ?? "—"}</span>
                    <span className="mono subtle" style={{ fontSize: 10.5 } satisfies CSSProperties}>· {model}</span>
                  </div>
                </div>
                <div className="col" style={{ gap: 3, width: 80 } satisfies CSSProperties}>
                  <span className="mono subtle" style={{ fontSize: 10.5 } satisfies CSSProperties}>turn {loop.turn_count}/{MAX_TURNS}</span>
                  <div style={miniBar}>
                    <div style={{
                      ...miniBarFill,
                      background: pct > 80 ? "var(--warning)" : "var(--primary)",
                      transform: `scaleX(${pct / 100})`,
                    }} />
                  </div>
                </div>
                <span className="mono subtle" style={{ fontSize: 11, width: 60, textAlign: "right" } satisfies CSSProperties}>
                  {loop.token_usage.toLocaleString()} tok
                </span>
                <span className="mono subtle" style={{ fontSize: 11, width: 38, textAlign: "right" } satisfies CSSProperties}>
                  {relativeSince(loop.started_at_ms)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
