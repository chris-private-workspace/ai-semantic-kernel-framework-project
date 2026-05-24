/**
 * File: frontend/src/pages/state-inspector/StateInspectorPage.tsx
 * Purpose: LoopState time-travel — port from reference/design-mockups/page-platform.jsx StateInspector.
 * Category: Frontend / pages / state-inspector
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C4; Sprint 57.37 Day 3 Domain B verbatim CSS re-point.
 *
 * Description:
 *   1:1 port of mockup `StateInspector` (page-platform.jsx:21-145):
 *     - page-head: title + subtitle (Range 7 · LoopState time-travel) + 3 .btn outline actions
 *     - .grid-stats: 4 KPI cards (Current version / Transient size / Durable bytes / Pending approvals)
 *     - inline grid 320px / 1fr: left = .card "Version chain" with 10 fixture
 *       versions (lineage tick marks + checkpoint icon); right = .card current-state
 *       (transient + durable .col KvLine lists in .grid-2) + .card diff-vs-parent
 *
 *   Backend wiring (per Sprint 57.19 US-B3, preserved Sprint 57.37):
 *     - GET /api/v1/sessions/{id}/state returns ONLY the latest snapshot for one
 *       session — there is no list-by-session version-chain endpoint yet
 *       (tracked as AD-State-VersionChain-Phase58).
 *     - When `?session_id=<uuid>` is provided in URL, this page calls the real
 *       backend and shows the live tenant_id / version / hash / reason atop the
 *       mockup-fixture chain (carryover banner shown).
 *     - When no session_id provided: render full mockup fixture (no live data).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C4)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: FIX-011 — drop production-only padding:18 on outer wrapper (mockup has no outer wrapper; .content padding sufficed; the extra 18px stacked ~46px effective vs mockup 28px)
 *   - 2026-05-24: Sprint 57.37 Day 3 — verbatim CSS re-point per page-platform.jsx:21-155 (closes Sprint 57.19 vintage HSL-translation drift; drops TONE_CLASS Record + bg-X/16/text-X Tailwind utility patterns + shadcn token classes; adopts mockup verbatim .page-head/.grid-stats/.card/.col/.spread/.mono/.subtle/.tnum + verbatim oklch alpha-tints)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C4)
 *
 * Related:
 *   - reference/design-mockups/page-platform.jsx:21-155 (verbatim mockup truth)
 *   - frontend/src/features/state/hooks/useStateSnapshot.ts (US-B3 consumer)
 *   - backend/src/api/v1/sessions.py (US-B3)
 *   - frontend/src/styles-mockup.css L416-622 (mockup class definitions)
 *   - sprint-57-37-plan.md §3.5 (Domain B re-point spec)
 */

import { Clock, Download, RefreshCw, Shield } from "lucide-react";
import type { FC, ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useStateSnapshot } from "@/features/state/hooks/useStateSnapshot";

// ───────────────── module-scope mockup-style constant refs ─────────────────
// Mockup verbatim inline-style patterns. Constant-ref objects pass the
// no-restricted-syntax eslint rule (only inline JSX object literals are flagged).
// Mockup source line references in each name.

// FIX-011 (Sprint 57.38 follow-up 2026-05-24): dropped `padding: 18` — production-only
// Sprint 57.19 vintage outer padding artifact; mockup page-platform.jsx:25-145 has NO
// outer wrapper. .content already provides 24px 28px 60px padding; the extra 18px
// stacked on top added ~46px effective left/right inset vs mockup's intended 28px.
// `gap: 14` kept to preserve vertical rhythm between page-head + grid-stats + grid-2
// children (mockup relies on per-class margins which we conservatively reinforce here).
const STATE_PAGE_WRAPPER_STYLE = { display: "flex", flexDirection: "column" as const, gap: 14 };
const STATE_GRID_320_1FR_STYLE = { display: "grid", gridTemplateColumns: "320px 1fr", gap: 14 };
const CARRYOVER_BANNER_STYLE = {
  padding: 12,
  borderRadius: 8,
  border: "1px solid oklch(from var(--warning) l c h / 0.4)",
  background: "oklch(from var(--warning) l c h / 0.08)",
  color: "var(--warning)",
  fontSize: 12,
};
const ERROR_BANNER_STYLE = {
  padding: 12,
  borderRadius: 8,
  border: "1px solid oklch(from var(--danger) l c h / 0.4)",
  background: "oklch(from var(--danger) l c h / 0.08)",
  color: "var(--danger)",
  fontSize: 12,
};
const STAT_CARD_STYLE = {
  padding: 12,
  borderRadius: 12,
  border: "1px solid var(--border)",
  background: "var(--bg-card, var(--bg-1))",
};
const STAT_LABEL_STYLE = { fontSize: 11, color: "var(--fg-muted)" };
const STAT_VALUE_STYLE = {
  marginTop: 4,
  fontFamily: "var(--font-mono)",
  fontSize: 22,
  fontWeight: 600 as const,
  fontFeatureSettings: '"tnum"',
};
const STAT_UNIT_STYLE = { marginLeft: 4, fontSize: 11, fontWeight: 400 as const, color: "var(--fg-muted)" };

const VERSION_CHAIN_COL_STYLE = { gap: 0, position: "relative" as const };
const VERSION_LINEAGE_TICK_STYLE = {
  position: "absolute" as const,
  left: 17,
  top: 22,
  bottom: -8,
  width: 1,
  background: "var(--border)",
};
const VERSION_KV_COL_STYLE = { gap: 6, fontSize: 12 };
const VERSION_SECTION_LABEL_STYLE = {
  fontSize: 11,
  fontFamily: "var(--font-mono)",
  textTransform: "uppercase" as const,
  letterSpacing: "0.06em",
  marginBottom: 8,
  color: "var(--fg-subtle)",
};
const VERSION_LINE_HEAD_ROW_STYLE = { gap: 5, fontSize: 11.5 };
const VERSION_BY_LINE_STYLE_BASE = { fontSize: 10.5, marginTop: 2 };
const VERSION_MSG_LINE_STYLE = { fontSize: 11, marginTop: 2, lineHeight: 1.45 };

const DIFF_PRE_STYLE = {
  margin: 0,
  padding: 12,
  background: "var(--bg-2)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  fontFamily: "var(--font-mono)",
  fontSize: 11,
  lineHeight: 1.55,
  overflowX: "auto" as const,
};

const RIGHT_COL_STYLE = { display: "flex", flexDirection: "column" as const, gap: 14 };
const CARD_TITLE_ROW_STYLE = { gap: 6 };
const CARD_TITLE_MONO_STYLE = { fontFamily: "var(--font-mono)" };
const CURRENT_BY_MONO_STYLE = { fontFamily: "var(--font-mono)" };
const GRID_2_STYLE = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 };
const KV_LABEL_STYLE = { fontSize: 11 };
const KV_VAL_STYLE = { fontSize: 11.5 };

// ───────────────── primitives ─────────────────

type VersionAuthor = "orchestrator_loop" | "reducer" | "tools" | "subagent" | "session_init";

/** Mockup author-tone map per page-platform.jsx:56-61. */
function authorColor(by: VersionAuthor): string {
  switch (by) {
    case "reducer":
      return "var(--memory)";
    case "orchestrator_loop":
      return "var(--primary)";
    case "tools":
      return "var(--tool)";
    case "subagent":
      return "var(--info)";
    case "session_init":
      return "var(--success)";
    default:
      return "var(--fg-muted)";
  }
}

const Card: FC<{
  title?: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  bodyDense?: boolean;
}> = ({ title, subtitle, children, bodyDense }) => (
  <div className="card">
    {(title || subtitle) && (
      <div className="card-head">
        {title && <div className="card-title">{title}</div>}
        {subtitle && <div className="card-sub">{subtitle}</div>}
      </div>
    )}
    <div className={bodyDense ? "card-body dense" : "card-body"}>{children}</div>
  </div>
);

const Stat: FC<{ label: string; value: string; unit?: string }> = ({ label, value, unit }) => (
  // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx Stat verbatim layout (constant ref); mockup-fidelity
  <div style={STAT_CARD_STYLE}>
    {/* eslint-disable-next-line no-restricted-syntax -- mockup Stat label (constant ref); mockup-fidelity */}
    <div style={STAT_LABEL_STYLE}>{label}</div>
    {/* eslint-disable-next-line no-restricted-syntax -- mockup Stat value typography (constant ref); mockup-fidelity */}
    <div style={STAT_VALUE_STYLE}>
      {value}
      {/* eslint-disable-next-line no-restricted-syntax -- mockup Stat unit (constant ref); mockup-fidelity */}
      {unit && <span style={STAT_UNIT_STYLE}>{unit}</span>}
    </div>
  </div>
);

const KvLine: FC<{ k: string; v: ReactNode; mono?: boolean }> = ({ k, v, mono }) => (
  <div className="spread">
    {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:149 KvLine label (constant ref); mockup-fidelity */}
    <span className="muted mono" style={KV_LABEL_STYLE}>
      {k}
    </span>
    {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:150 KvLine value (constant ref); mockup-fidelity */}
    <span className={mono ? "mono tnum" : ""} style={KV_VAL_STYLE}>
      {v}
    </span>
  </div>
);

// ───────────────── fixture: 10 mockup versions ─────────────────

interface VersionRow {
  v: number;
  parent: number | null;
  at: string;
  by: VersionAuthor;
  msg: string;
  checkpoint: boolean;
}

const STATE_VERSIONS: VersionRow[] = [
  { v: 18, parent: 17, at: "10:42:28.420", by: "orchestrator_loop", msg: "loop.iteration_4 end · stop_reason=hitl", checkpoint: false },
  { v: 17, parent: 16, at: "10:42:28.180", by: "reducer", msg: "WRITE durable: pending_approval[a8f3.k2p1]", checkpoint: true },
  { v: 16, parent: 15, at: "10:42:27.480", by: "tools", msg: "tool_result · metrics.query · 1.8KB", checkpoint: false },
  { v: 15, parent: 14, at: "10:42:25.220", by: "reducer", msg: "WRITE durable: conversation_summary", checkpoint: true },
  { v: 14, parent: 13, at: "10:42:24.020", by: "subagent", msg: "subagent.completed · log-scanner", checkpoint: false },
  { v: 13, parent: 12, at: "10:42:22.840", by: "tools", msg: "tool_result · incidents.list · 8 rows", checkpoint: false },
  { v: 12, parent: 11, at: "10:42:20.120", by: "orchestrator_loop", msg: "loop.iteration_2 end · spawn 3 subagents", checkpoint: false },
  { v: 11, parent: 10, at: "10:42:19.620", by: "reducer", msg: "compaction: hybrid · -2,140 tokens", checkpoint: true },
  { v: 10, parent: 9, at: "10:42:18.840", by: "orchestrator_loop", msg: "loop.iteration_1 end · stop_reason=tool_use", checkpoint: false },
  { v: 9, parent: 8, at: "10:42:18.020", by: "session_init", msg: "session_id=sess_4tk2p · tenant=acme-prod", checkpoint: true },
];

const DIFF_TEXT = `  durable.pending_approval_ids:
- []
+ ["a8f3.k2p1"]

  transient.pending_tool_calls:
- []
+ [{ name: "k8s.set_env", tool_call_id: "tc_8a02p" }]

  transient.token_usage_so_far:
- 18,200
+ 18,420  (+220)`;

// ───────────────── page ─────────────────

function StateInspectorPageInner(): JSX.Element {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [selected, setSelected] = useState(18);

  const current = STATE_VERSIONS.find((s) => s.v === selected) ?? STATE_VERSIONS[0];
  const parent = STATE_VERSIONS.find((s) => s.v === current.parent);

  const { data: liveSnapshot, error: liveError } = useStateSnapshot(sessionId);
  const hasLive = liveSnapshot != null;

  return (
    // eslint-disable-next-line no-restricted-syntax -- page-wrapper layout (constant ref); preserves Sprint 57.19 outer padding inside verbatim mockup
    <div style={STATE_PAGE_WRAPPER_STYLE}>
      {/* === Mockup page-head === */}
      <div className="page-head">
        <div>
          <div className="page-title">State Inspector</div>
          <div className="page-sub">
            {t("stateInspector.subtitle")}
            <span className="route-pill">/state-inspector</span>
            <span className="mono subtle">
              · {STATE_VERSIONS.length} {t("stateInspector.versions")} · 3 {t("stateInspector.checkpoints")}
            </span>
          </div>
        </div>
        <div className="page-actions">
          <button type="button" className="btn outline" data-size="sm">
            <Clock className="ico" /> {t("stateInspector.diffVsParent")}
          </button>
          <button type="button" className="btn outline" data-size="sm">
            <RefreshCw className="ico" /> {t("stateInspector.restore")}
          </button>
          <button type="button" className="btn outline" data-size="sm">
            <Download className="ico" /> {t("stateInspector.exportCheckpoint")}
          </button>
        </div>
      </div>

      {/* === Carryover banner — backend gap === */}
      {/* eslint-disable-next-line no-restricted-syntax -- carryover banner verbatim tint (constant ref); mockup-token vocabulary */}
      <div role="status" style={CARRYOVER_BANNER_STYLE}>
        <strong>{t("stateInspector.carryoverHeading")}</strong>: {t("stateInspector.carryoverBody")}
      </div>

      {/* === Live error if backend fetch failed === */}
      {liveError && (
        // eslint-disable-next-line no-restricted-syntax -- error banner verbatim tint (constant ref); mockup-token vocabulary
        <div role="alert" style={ERROR_BANNER_STYLE}>
          {t("stateInspector.liveFetchError")}: {liveError.message}
        </div>
      )}

      {/* === KPI row (mockup .grid-stats) === */}
      <div className="grid-stats">
        <Stat
          label={t("stateInspector.kpi.currentVersion")}
          value={`v${hasLive ? liveSnapshot.version : selected}`}
        />
        <Stat label={t("stateInspector.kpi.transientSize")} value="12" unit=" msg" />
        <Stat label={t("stateInspector.kpi.durableBytes")} value="4.2" unit=" kB" />
        <Stat label={t("stateInspector.kpi.pendingApprovals")} value="1" />
      </div>

      {/* === 320px / 1fr grid: version chain + state pane === */}
      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:50 verbatim inline grid (constant ref); mockup-fidelity */}
      <div style={STATE_GRID_320_1FR_STYLE}>
        <Card
          title={t("stateInspector.chain.title")}
          subtitle={t("stateInspector.chain.subtitle")}
          bodyDense
        >
          {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:52 col with position relative (constant ref); mockup-fidelity */}
          <div className="col" style={VERSION_CHAIN_COL_STYLE}>
            {STATE_VERSIONS.map((sv, i) => {
              const isSel = sv.v === selected;
              const isLast = i === STATE_VERSIONS.length - 1;
              const cat = authorColor(sv.by);
              return (
                <div
                  key={sv.v}
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelected(sv.v)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelected(sv.v);
                    }
                  }}
                  // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:64-71 verbatim version-row layout (dynamic selected highlight); mockup-fidelity pattern
                  style={{
                    position: "relative",
                    display: "grid",
                    gridTemplateColumns: "28px 1fr",
                    gap: 10,
                    padding: "7px 4px",
                    cursor: "pointer",
                    background: isSel ? "oklch(from var(--primary) l c h / 0.10)" : undefined,
                    borderRadius: 4,
                    borderLeft: isSel ? "2px solid var(--primary)" : "2px solid transparent",
                  }}
                >
                  {!isLast && (
                    // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:72 verbatim lineage tick (constant ref); mockup-fidelity
                    <span style={VERSION_LINEAGE_TICK_STYLE} />
                  )}
                  <span
                    // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:73-80 verbatim checkpoint icon (dynamic per cat + checkpoint); mockup-fidelity
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: sv.checkpoint ? 4 : "50%",
                      background: sv.checkpoint
                        ? `oklch(from ${cat} l c h / 0.2)`
                        : "var(--bg-1)",
                      border: `1.5px solid ${cat}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: cat,
                      fontSize: 9,
                      fontFamily: "var(--font-mono)",
                      fontWeight: 600,
                      marginTop: 4,
                    }}
                  >
                    {sv.checkpoint ? <Shield size={10} /> : null}
                  </span>
                  <div>
                    {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:82 row head (constant ref); mockup-fidelity */}
                    <div className="row" style={VERSION_LINE_HEAD_ROW_STYLE}>
                      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:83 mono fontWeight (constant ref); mockup-fidelity */}
                      <span className="mono" style={{ fontWeight: 600 }}>
                        v{sv.v}
                      </span>
                      {sv.checkpoint && <span className="badge memory">checkpoint</span>}
                      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:85 timestamp right-align (constant ref); mockup-fidelity */}
                      <span className="mono subtle" style={{ marginLeft: "auto", fontSize: 10 }}>
                        {sv.at.slice(-6)}
                      </span>
                    </div>
                    <div
                      className="mono"
                      // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:87 by-line color (dynamic per cat); mockup-fidelity
                      style={{ ...VERSION_BY_LINE_STYLE_BASE, color: cat }}
                    >
                      {sv.by}
                    </div>
                    {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:88 msg line (constant ref); mockup-fidelity */}
                    <div className="subtle" style={VERSION_MSG_LINE_STYLE}>
                      {sv.msg}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:96 right col gap (constant ref); mockup-fidelity */}
        <div style={RIGHT_COL_STYLE}>
          <Card
            title={
              // eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:97 title row (constant ref); mockup-fidelity
              <span className="row" style={CARD_TITLE_ROW_STYLE}>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:98 mono span (constant ref); mockup-fidelity */}
                <span style={CARD_TITLE_MONO_STYLE}>v{selected}</span>
                <span className="subtle">by</span>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:100 current-by-mono dynamic color; mockup-fidelity */}
                <span className="mono" style={{ ...CURRENT_BY_MONO_STYLE, color: authorColor(current.by) }}>
                  {current.by}
                </span>
              </span>
            }
            subtitle={current.msg}
            bodyDense
          >
            {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:102 grid-2 (constant ref); mockup-fidelity */}
            <div style={GRID_2_STYLE}>
              <div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:104 section label (constant ref); mockup-fidelity */}
                <div className="subtle" style={VERSION_SECTION_LABEL_STYLE}>
                  {t("stateInspector.transient.heading")}
                </div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:105 col KvLines (constant ref); mockup-fidelity */}
                <div className="col" style={VERSION_KV_COL_STYLE}>
                  <KvLine k="messages" v="12 items" mono />
                  <KvLine k="pending_tool_calls" v="1" mono />
                  <KvLine k="current_turn" v="4" mono />
                  <KvLine k="elapsed_ms" v="4,210" mono />
                  <KvLine k="token_usage_so_far" v="18,420" mono />
                </div>
              </div>
              <div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:114 section label (constant ref); mockup-fidelity */}
                <div className="subtle" style={VERSION_SECTION_LABEL_STYLE}>
                  {t("stateInspector.durable.heading")}
                </div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:115 col KvLines (constant ref); mockup-fidelity */}
                <div className="col" style={VERSION_KV_COL_STYLE}>
                  <KvLine
                    k="session_id"
                    v={hasLive ? liveSnapshot.session_id.slice(0, 12) + "…" : "sess_4tk2p"}
                    mono
                  />
                  <KvLine
                    k="tenant_id"
                    v={hasLive ? liveSnapshot.tenant_id.slice(0, 12) + "…" : "tenant_01h9a2"}
                    mono
                  />
                  <KvLine k="user_id" v="u_jamie" mono />
                  <KvLine k="pending_approval_ids" v="[a8f3.k2p1]" mono />
                  <KvLine
                    k="last_checkpoint_version"
                    v={String(hasLive ? liveSnapshot.version : 17)}
                    mono
                  />
                  <KvLine k="conversation_summary" v={<span className="subtle">— 124 chars —</span>} />
                </div>
              </div>
            </div>
          </Card>

          <Card
            title={t("stateInspector.diff.title")}
            subtitle={parent ? `v${parent.v} → v${current.v}` : t("stateInspector.diff.noParent")}
            bodyDense
          >
            {/* eslint-disable-next-line no-restricted-syntax -- mockup page-platform.jsx:128 diff pre verbatim (constant ref); mockup-fidelity */}
            <pre style={DIFF_PRE_STYLE}>{DIFF_TEXT}</pre>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function StateInspectorPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <RequireAuth>
      <AppShellV2 pageTitle={t("stateInspector.title")}>
        <StateInspectorPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default StateInspectorPage;
