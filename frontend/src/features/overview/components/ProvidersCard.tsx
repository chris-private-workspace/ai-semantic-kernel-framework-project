/**
 * File: frontend/src/features/overview/components/ProvidersCard.tsx
 * Purpose: /overview providers traffic-light card — 4 provider rows with state dots.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:180-199`.
 *   Wraps the shared <CardShell> (dense body); body renders one provider row per
 *   PROVIDERS fixture entry. Each row: coloured traffic-dot (8px circle with
 *   oklch-glow ring via inline style STYLE.md §1 escape hatch), mono name,
 *   p95 label, call count right-aligned.
 *
 *   The telemetry provider traffic-light API is not yet wired; a visible
 *   <BackendGapBanner> declares fixture data per AP-2 honesty.
 *
 * Key Components:
 *   - ProvidersCard: card + 4 provider rows + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C2) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:180-199 (ProvidersCard canonical)
 *   - frontend/src/features/overview/__fixtures__/providers.ts (fixture data)
 *   - frontend/src/components/ui/CardShell.tsx + BackendGapBanner.tsx (shared)
 */

import { ArrowRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { CardShell } from "@/components/ui/CardShell";

import { PROVIDERS } from "../__fixtures__/providers";

const STATE_COLOR: Record<string, string> = {
  green: "var(--success)",
  amber: "var(--warning)",
  red: "var(--danger)",
};

const STATE_DOT_CLASS: Record<string, string> = {
  green: "bg-success",
  amber: "bg-warning",
  red: "bg-danger",
};

export const ProvidersCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <CardShell
      title={t("overview.providers.title")}
      subtitle={`${PROVIDERS.length} providers · 24h`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/sla-dashboard")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.providers.details")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClass="p-2.5"
    >
      <div className="flex flex-col">
        {PROVIDERS.map((p, i) => (
          <div
            key={p.name}
            className={`flex items-center gap-[10px] px-1 py-[10px] ${
              i < PROVIDERS.length - 1 ? "border-b border-border" : ""
            }`}
          >
            <span
              data-testid={`traffic-dot-${p.state}`}
              className={`h-2 w-2 rounded-full ${STATE_DOT_CLASS[p.state] ?? "bg-fg-muted"}`}
              // eslint-disable-next-line no-restricted-syntax -- per-state oklch glow ring per mockup parity (STYLE.md §1 escape hatch)
              style={{
                boxShadow: `0 0 0 3px color-mix(in oklch, ${STATE_COLOR[p.state] ?? "var(--fg-muted)"} 18%, transparent)`,
              }}
            />
            <span className="flex-1 font-mono text-[12px]">{p.name}</span>
            <span className="font-mono text-[11px] text-fg-muted">p95 {p.p95}s</span>
            <span className="w-[60px] text-right font-mono text-[11px] text-fg-muted">
              {p.calls}
            </span>
          </div>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.providers.backendGap")} />
    </CardShell>
  );
};
