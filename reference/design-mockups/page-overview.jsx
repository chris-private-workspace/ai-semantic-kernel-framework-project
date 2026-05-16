/* global React, Icon, Button, Badge, Card, Stat, Spark, SevDot, RiskBadge, t */

// ====================================================================
// /overview — unified operator dashboard
// ====================================================================
// Operator landing page. Cross-cuts the 12 範疇 to give a "everything I
// need at a glance" view before drilling into specific tools.
//
// Layout: 4 KPI cards → 2-col grid of widgets → quick actions strip.
// ====================================================================

const overviewStyles = {
  page: { padding: 18 },
  kpiRow: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14 },
  grid2: { display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14, marginBottom: 14 },
  grid2eq: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 },
  loopRow: {
    display: "grid",
    gridTemplateColumns: "auto 1fr auto auto auto",
    gap: 10, alignItems: "center",
    padding: "8px 10px",
    borderBottom: "1px solid var(--border)",
    fontSize: 12.5,
    cursor: "pointer",
  },
  miniBar: { height: 6, borderRadius: 3, background: "var(--bg-3)", overflow: "hidden", position: "relative" },
  miniBarFill: { position: "absolute", inset: 0, transformOrigin: "left center" },
  trafficDot: (state) => ({
    width: 8, height: 8, borderRadius: "50%",
    background: state === "green" ? "var(--success)" : state === "amber" ? "var(--warning)" : "var(--danger)",
    boxShadow: `0 0 0 3px oklch(from ${state === "green" ? "var(--success)" : state === "amber" ? "var(--warning)" : "var(--danger)"} l c h / 0.18)`,
  }),
  quickBtn: {
    flex: 1, display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-start",
    padding: 12, background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--radius)",
    cursor: "pointer", textAlign: "left",
  },
};

const ACTIVE_LOOPS = [
  { id: "s_8a2f", agent: "incident-responder", session: "sess_8a2f1", tenant: "acme-prod", turns: 6, max: 50, tokens: 18420, model: "claude-haiku-4-5", status: "running", since: "12s" },
  { id: "s_7c11", agent: "compliance-auditor", session: "sess_7c11d", tenant: "globex-eu",  turns: 12, max: 50, tokens: 31200, model: "gpt-4.1",         status: "hitl-paused", since: "4m" },
  { id: "s_6b09", agent: "patrol-runner",       session: "sess_6b09e", tenant: "acme-prod",  turns: 3, max: 50, tokens:  8400, model: "claude-haiku-4-5", status: "running", since: "1m" },
  { id: "s_5a44", agent: "chat-v2",             session: "sess_5a44a", tenant: "initech-jp", turns: 1, max: 50, tokens:  1240, model: "gpt-4.1-mini",   status: "running", since: "3s" },
  { id: "s_4f88", agent: "rca-explorer",        session: "sess_4f88c", tenant: "acme-prod",  turns: 22, max: 50, tokens: 54100, model: "claude-haiku-4-5", status: "verifying", since: "8m" },
];

const HITL_QUEUE = [
  { id: "appr_91", title: "salesforce_update — refund $4,820", risk: "high",     requester: "sess_7c11d", sla: "3h 12m" },
  { id: "appr_92", title: "email_send — refund confirmation to 14 customers", risk: "medium", requester: "sess_7c11d", sla: "3h 14m" },
  { id: "appr_88", title: "servicenow_create_ticket — P1 incident escalation",  risk: "critical", requester: "sess_4f88c", sla: "23m" },
];

const RECENT_INCIDENTS = [
  { id: "INC-2451", title: "p95 latency breach · gpt-4.1 provider",      sev: "high",     status: "open",        since: "12m" },
  { id: "INC-2447", title: "redaction rule false-positive · acme-prod",  sev: "low",      status: "investigating", since: "1h" },
  { id: "INC-2440", title: "subagent budget exceeded x4 · globex-eu",    sev: "medium",   status: "open",        since: "2h" },
  { id: "INC-2438", title: "kb_search vector index rebuild",             sev: "low",      status: "resolved",    since: "3h" },
];

const PROVIDERS = [
  { name: "claude-haiku-4-5",  state: "green", p95: 1.8, calls: "12.4k" },
  { name: "gpt-4.1",           state: "amber", p95: 3.2, calls: "8.1k" },
  { name: "gpt-4.1-mini",      state: "green", p95: 1.1, calls: "4.7k" },
  { name: "embedding-3-large", state: "green", p95: 0.4, calls: "21.0k" },
];

const ERROR_24H = [3, 2, 4, 1, 0, 2, 1, 0, 0, 1, 3, 5, 8, 12, 9, 6, 4, 3, 5, 7, 4, 2, 1, 2];

const OverviewPage = ({ onNav }) => {
  return (
    <div style={overviewStyles.page}>
      {/* page head */}
      <div className="page-head">
        <div>
          <div className="page-title">{t("page.overview.title")}</div>
          <div className="page-sub">
            {t("page.overview.subtitle")}
            <span className="route-pill">/overview</span>
            <span className="mono subtle">acme-prod · operator · {new Date().toLocaleTimeString("en-US", { hour12: false })}</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="download">{t("page.overview.export")}</Button>
          <Button variant="primary" size="sm" icon="chat" onClick={() => onNav && onNav("chat-v2")}>{t("page.overview.newChat")}</Button>
        </div>
      </div>

      {/* KPI row */}
      <div style={overviewStyles.kpiRow}>
        <Stat label={t("page.overview.kpi.activeSessions")} value="14" unit="loops" delta="+3" deltaDir="up" />
        <Stat label={t("page.overview.kpi.hitlPending")}    value="3"  unit="approvals" delta="1 critical" deltaDir="down" />
        <Stat label={t("page.overview.kpi.costMtd")}         value="$2,847" delta="68% of $4,200 budget" deltaDir="up" spark={[2, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22]} />
        <Stat label={t("page.overview.kpi.slaP95")}          value="1.84s" unit="across loops" delta="-0.12s wow" deltaDir="up" spark={[2.0, 2.1, 2.0, 1.9, 1.95, 1.88, 1.84]} />
      </div>

      {/* row: active loops + HITL */}
      <div style={overviewStyles.grid2}>
        <Card
          title={t("page.overview.activeLoops.title")}
          subtitle={`${ACTIVE_LOOPS.length} live · ${t("page.overview.activeLoops.subtitle")}`}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("loop-debug")}>{t("page.overview.openLoopDebug")}</Button>}
          bodyClass="flush"
        >
          <div>
            {ACTIVE_LOOPS.map(loop => {
              const pct = Math.min(100, (loop.turns / loop.max) * 100);
              const statusTone =
                loop.status === "running" ? "success" :
                loop.status === "hitl-paused" ? "warning" :
                loop.status === "verifying" ? "thinking" : "";
              return (
                <div key={loop.id} style={overviewStyles.loopRow} onClick={() => onNav && onNav("loop-debug")}>
                  <Badge tone={statusTone} dot>{loop.status}</Badge>
                  <div className="col" style={{ gap: 2, minWidth: 0 }}>
                    <div className="row" style={{ gap: 6, fontSize: 12.5 }}>
                      <span style={{ fontWeight: 500 }}>{loop.agent}</span>
                      <span className="mono subtle" style={{ fontSize: 11 }}>· {loop.session}</span>
                    </div>
                    <div className="row" style={{ gap: 6 }}>
                      <span className="mono subtle" style={{ fontSize: 10.5 }}>{loop.tenant}</span>
                      <span className="mono subtle" style={{ fontSize: 10.5 }}>· {loop.model}</span>
                    </div>
                  </div>
                  <div className="col" style={{ gap: 3, width: 80 }}>
                    <span className="mono subtle" style={{ fontSize: 10.5 }}>turn {loop.turns}/{loop.max}</span>
                    <div style={overviewStyles.miniBar}>
                      <div style={{
                        ...overviewStyles.miniBarFill,
                        background: pct > 80 ? "var(--warning)" : "var(--primary)",
                        transform: `scaleX(${pct / 100})`,
                      }} />
                    </div>
                  </div>
                  <span className="mono subtle" style={{ fontSize: 11, width: 60, textAlign: "right" }}>{loop.tokens.toLocaleString()} tok</span>
                  <span className="mono subtle" style={{ fontSize: 11, width: 38, textAlign: "right" }}>{loop.since}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card
          title={t("page.overview.hitlQueue.title")}
          subtitle={`${HITL_QUEUE.length} pending`}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("governance")}>{t("page.overview.review")}</Button>}
          bodyClass="dense"
        >
          <div className="col" style={{ gap: 10 }}>
            {HITL_QUEUE.map(req => (
              <div key={req.id} className="col" style={{
                gap: 6, padding: 10,
                background: req.risk === "critical" ? "oklch(from var(--danger) l c h / 0.08)" : "var(--bg-1)",
                border: `1px solid ${req.risk === "critical" ? "oklch(from var(--danger) l c h / 0.4)" : "var(--border)"}`,
                borderRadius: "var(--radius-sm)",
                cursor: "pointer",
              }} onClick={() => onNav && onNav("governance")}>
                <div className="row" style={{ gap: 6, justifyContent: "space-between" }}>
                  <RiskBadge level={req.risk} />
                  <span className="mono subtle" style={{ fontSize: 10.5 }}>SLA · {req.sla}</span>
                </div>
                <div style={{ fontSize: 12.5, fontWeight: 500, lineHeight: 1.4 }}>{req.title}</div>
                <div className="mono subtle" style={{ fontSize: 10.5 }}>{req.id} · from {req.requester}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* row: cost burn + SLA traffic light */}
      <div style={overviewStyles.grid2eq}>
        <Card
          title={t("page.overview.costBurn.title")}
          subtitle={t("page.overview.costBurn.subtitle")}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("cost-dashboard")}>{t("page.overview.details")}</Button>}
        >
          <CostBurnChart />
        </Card>

        <Card
          title={t("page.overview.providers.title")}
          subtitle={`${PROVIDERS.length} providers · 24h`}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("sla-dashboard")}>{t("page.overview.details")}</Button>}
          bodyClass="dense"
        >
          <div className="col" style={{ gap: 0 }}>
            {PROVIDERS.map((p, i) => (
              <div key={p.name} className="row" style={{
                gap: 10, padding: "10px 4px",
                borderBottom: i < PROVIDERS.length - 1 ? "1px solid var(--border)" : "none",
              }}>
                <span style={overviewStyles.trafficDot(p.state)} />
                <span className="mono" style={{ fontSize: 12, flex: 1 }}>{p.name}</span>
                <span className="mono subtle" style={{ fontSize: 11 }}>p95 {p.p95}s</span>
                <span className="mono subtle" style={{ fontSize: 11, width: 60, textAlign: "right" }}>{p.calls}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* row: incidents + error trend */}
      <div style={overviewStyles.grid2eq}>
        <Card
          title={t("page.overview.incidents.title")}
          subtitle={`${RECENT_INCIDENTS.filter(i => i.status !== "resolved").length} open`}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("incidents")}>{t("page.overview.allIncidents")}</Button>}
          bodyClass="flush"
        >
          <div>
            {RECENT_INCIDENTS.map((inc, i) => (
              <div key={inc.id} className="row" style={{
                gap: 10, padding: "10px 14px",
                borderBottom: i < RECENT_INCIDENTS.length - 1 ? "1px solid var(--border)" : "none",
                fontSize: 12.5, cursor: "pointer",
              }} onClick={() => onNav && onNav("incidents")}>
                <RiskBadge level={inc.sev} />
                <span className="mono" style={{ fontSize: 11.5, width: 64 }}>{inc.id}</span>
                <span style={{ flex: 1 }}>{inc.title}</span>
                <Badge tone={inc.status === "resolved" ? "success" : inc.status === "open" ? "warning" : ""}>{inc.status}</Badge>
                <span className="mono subtle" style={{ fontSize: 11, width: 40, textAlign: "right" }}>{inc.since}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title={t("page.overview.errors.title")}
          subtitle={t("page.overview.errors.subtitle")}
          actions={<Button variant="ghost" size="sm" iconRight="arrow_right" onClick={() => onNav && onNav("error-policy")}>{t("page.overview.errorPolicy")}</Button>}
        >
          <ErrorTrendChart />
        </Card>
      </div>

      {/* quick actions strip */}
      <div className="row" style={{ gap: 12 }}>
        <button style={overviewStyles.quickBtn} onClick={() => onNav && onNav("chat-v2")}>
          <span className="row" style={{ gap: 6, alignItems: "center" }}>
            <Icon name="chat" size={14} style={{ color: "var(--primary)" }} />
            <span style={{ fontSize: 12.5, fontWeight: 500 }}>{t("page.overview.quick.newChat")}</span>
          </span>
          <span className="muted" style={{ fontSize: 11 }}>{t("page.overview.quick.newChatSub")}</span>
        </button>
        <button style={overviewStyles.quickBtn} onClick={() => onNav && onNav("governance")}>
          <span className="row" style={{ gap: 6, alignItems: "center" }}>
            <Icon name="approval" size={14} style={{ color: "var(--warning)" }} />
            <span style={{ fontSize: 12.5, fontWeight: 500 }}>{t("page.overview.quick.review")}</span>
          </span>
          <span className="muted" style={{ fontSize: 11 }}>{t("page.overview.quick.reviewSub")}</span>
        </button>
        <button style={overviewStyles.quickBtn} onClick={() => onNav && onNav("admin-tenants")}>
          <span className="row" style={{ gap: 6, alignItems: "center" }}>
            <Icon name="tenants" size={14} style={{ color: "var(--info)" }} />
            <span style={{ fontSize: 12.5, fontWeight: 500 }}>{t("page.overview.quick.tenants")}</span>
          </span>
          <span className="muted" style={{ fontSize: 11 }}>{t("page.overview.quick.tenantsSub")}</span>
        </button>
        <button style={overviewStyles.quickBtn} onClick={() => onNav && onNav("verification")}>
          <span className="row" style={{ gap: 6, alignItems: "center" }}>
            <Icon name="checkcheck" size={14} style={{ color: "var(--success)" }} />
            <span style={{ fontSize: 12.5, fontWeight: 500 }}>{t("page.overview.quick.verification")}</span>
          </span>
          <span className="muted" style={{ fontSize: 11 }}>{t("page.overview.quick.verificationSub")}</span>
        </button>
      </div>
    </div>
  );
};

// ───────────────── inner widgets ─────────────────

const CostBurnChart = () => {
  // 30-day burn vs daily budget rate
  const days = 30;
  const today = 18; // simulate "we are on day 18"
  const dailyBudget = 4200 / days; // = 140
  const spent = Array.from({ length: today }, (_, i) =>
    dailyBudget * (0.6 + (i / today) * 0.9 + Math.sin(i * 0.7) * 0.15)
  );
  const cumulative = spent.reduce((acc, v, i) => [...acc, (acc[i - 1] || 0) + v], []);
  const W = 360, H = 130, padding = { l: 30, r: 8, t: 8, b: 22 };
  const innerW = W - padding.l - padding.r;
  const innerH = H - padding.t - padding.b;
  const maxY = 4200;
  const xAt = (i) => padding.l + (i / (days - 1)) * innerW;
  const yAt = (v) => padding.t + innerH - (v / maxY) * innerH;
  const budgetLine = `M ${xAt(0)} ${yAt(0)} L ${xAt(days - 1)} ${yAt(4200)}`;
  const burnPath = cumulative.map((v, i) => `${i === 0 ? "M" : "L"} ${xAt(i)} ${yAt(v)}`).join(" ");
  const burnArea = `${burnPath} L ${xAt(today - 1)} ${yAt(0)} L ${xAt(0)} ${yAt(0)} Z`;
  return (
    <div className="col" style={{ gap: 8 }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: H }}>
        <defs>
          <linearGradient id="burnGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%"  stopColor="oklch(from var(--primary) l c h / 0.32)" />
            <stop offset="100%" stopColor="oklch(from var(--primary) l c h / 0)" />
          </linearGradient>
        </defs>
        {/* y gridlines */}
        {[0, 1050, 2100, 3150, 4200].map(v => (
          <g key={v}>
            <line x1={padding.l} x2={W - padding.r} y1={yAt(v)} y2={yAt(v)} stroke="var(--border)" strokeDasharray="2 2" />
            <text x={padding.l - 4} y={yAt(v) + 3} textAnchor="end" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>${v}</text>
          </g>
        ))}
        {/* budget line */}
        <path d={budgetLine} stroke="var(--fg-subtle)" strokeDasharray="4 3" strokeWidth="1" fill="none" />
        <text x={W - padding.r} y={yAt(4200) - 4} textAnchor="end" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>budget $4,200</text>
        {/* burn area + line */}
        <path d={burnArea} fill="url(#burnGrad)" />
        <path d={burnPath} stroke="var(--primary)" strokeWidth="1.5" fill="none" />
        <circle cx={xAt(today - 1)} cy={yAt(cumulative[today - 1])} r="3" fill="var(--primary)" />
        {/* x axis */}
        <text x={padding.l} y={H - 6} style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>day 1</text>
        <text x={xAt(today - 1)} y={H - 6} textAnchor="middle" style={{ fontSize: 9, fill: "var(--primary)", fontFamily: "var(--font-mono)" }}>today</text>
        <text x={W - padding.r} y={H - 6} textAnchor="end" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>day 30</text>
      </svg>
      <div className="row" style={{ gap: 10, fontSize: 11, color: "var(--fg-muted)" }}>
        <span><span className="mono" style={{ color: "var(--primary)" }}>${cumulative[today - 1].toFixed(0)}</span> MTD</span>
        <span style={{ flex: 1 }} />
        <span><span className="mono">${(dailyBudget * today).toFixed(0)}</span> on-pace target</span>
        <span style={{ color: cumulative[today - 1] > dailyBudget * today ? "var(--warning)" : "var(--success)" }}>
          {cumulative[today - 1] > dailyBudget * today ? "over pace" : "under pace"}
        </span>
      </div>
    </div>
  );
};

const ErrorTrendChart = () => {
  const W = 360, H = 130, padding = { l: 30, r: 8, t: 8, b: 22 };
  const innerW = W - padding.l - padding.r;
  const innerH = H - padding.t - padding.b;
  const maxY = Math.max(...ERROR_24H, 10);
  const xAt = (i) => padding.l + (i / (ERROR_24H.length - 1)) * innerW;
  const yAt = (v) => padding.t + innerH - (v / maxY) * innerH;
  const bw = innerW / ERROR_24H.length * 0.7;
  return (
    <div className="col" style={{ gap: 8 }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: H }}>
        {/* y gridlines */}
        {[0, 4, 8, 12].map(v => (
          <g key={v}>
            <line x1={padding.l} x2={W - padding.r} y1={yAt(v)} y2={yAt(v)} stroke="var(--border)" strokeDasharray="2 2" />
            <text x={padding.l - 4} y={yAt(v) + 3} textAnchor="end" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>{v}</text>
          </g>
        ))}
        {/* bars */}
        {ERROR_24H.map((v, i) => {
          const tone = v >= 10 ? "var(--danger)" : v >= 6 ? "var(--warning)" : "var(--info)";
          return (
            <rect key={i}
              x={xAt(i) - bw / 2}
              y={yAt(v)}
              width={bw}
              height={innerH - (yAt(v) - padding.t)}
              fill={tone}
              fillOpacity={0.85}
              rx={1}
            />
          );
        })}
        {/* x axis labels */}
        <text x={padding.l} y={H - 6} style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>-24h</text>
        <text x={W / 2} y={H - 6} textAnchor="middle" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>-12h</text>
        <text x={W - padding.r} y={H - 6} textAnchor="end" style={{ fontSize: 9, fill: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>now</text>
      </svg>
      <div className="row" style={{ gap: 10, fontSize: 11, color: "var(--fg-muted)" }}>
        <span><span className="mono" style={{ color: "var(--danger)" }}>{ERROR_24H.reduce((a, b) => a + b, 0)}</span> errors · 24h</span>
        <span style={{ flex: 1 }} />
        <span><span className="mono">{Math.max(...ERROR_24H)}</span> peak / hour</span>
        <span style={{ color: ERROR_24H.slice(-3).reduce((a, b) => a + b, 0) > 10 ? "var(--warning)" : "var(--success)" }}>
          {ERROR_24H.slice(-3).reduce((a, b) => a + b, 0) > 10 ? "rising" : "stable"}
        </span>
      </div>
    </div>
  );
};

Object.assign(window, { OverviewPage });
