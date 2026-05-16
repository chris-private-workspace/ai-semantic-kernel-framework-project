/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, SevDot, Stat, Spark */
const { useState: useLp, useMemo: useMlp, useEffect: useLpEffect } = React;

// ============ /loop-debug — TAO/ReAct visualizer ============
const LoopEvents = [
  { turn: 0, type: "user_message", text: 'Investigate payment-gateway 5xx spike', tone: "fg", at: 0 },
  { turn: 1, type: "loop.iter_start", text: "iteration_1 · stop_reason=null", tone: "primary", at: 12 },
  { turn: 1, type: "thinking.start", text: "ThinkingBlock streaming…", tone: "thinking", at: 14 },
  { turn: 1, type: "thinking.delta", text: '"User flagged P1. SLO at 1% breached…"', tone: "thinking", at: 220 },
  { turn: 1, type: "thinking.end", text: "412 tokens · 0.42s", tone: "thinking", at: 420 },
  { turn: 1, type: "tool.requested", text: "incidents.list", tone: "tool", at: 440 },
  { turn: 1, type: "hitl.policy_check", text: "policy=auto (read tool) → allow", tone: "success", at: 442 },
  { turn: 1, type: "tool.started", text: "incidents.list · timeout=30s", tone: "tool", at: 444 },
  { turn: 1, type: "tool.completed", text: "rows=8 · 82ms", tone: "tool", at: 526 },
  { turn: 1, type: "verification.run", text: "claim: prior incident exists · evidence: 1 row", tone: "success", at: 538 },
  { turn: 1, type: "loop.iter_end", text: "stop_reason=tool_use · continue", tone: "primary", at: 540 },
  { turn: 2, type: "loop.iter_start", text: "iteration_2", tone: "primary", at: 552 },
  { turn: 2, type: "subagent.spawn", text: "fork concurrent · 3 children", tone: "thinking", at: 600 },
  { turn: 2, type: "subagent.completed", text: "log-scanner · 3 turns · ok", tone: "thinking", at: 2820 },
  { turn: 2, type: "loop.iter_end", text: "stop_reason=tool_use", tone: "primary", at: 2840 },
  { turn: 3, type: "loop.iter_start", text: "iteration_3", tone: "primary", at: 2870 },
  { turn: 3, type: "memory.read", text: "scope=user.jamie · key=preferences.rca_format", tone: "memory", at: 2880 },
  { turn: 3, type: "tool.completed", text: "metrics.query · 210ms", tone: "tool", at: 3090 },
  { turn: 3, type: "verification.run", text: "claim verified · 18ms", tone: "success", at: 3110 },
  { turn: 3, type: "loop.iter_end", text: "stop_reason=tool_use", tone: "primary", at: 3140 },
  { turn: 4, type: "loop.iter_start", text: "iteration_4", tone: "primary", at: 3160 },
  { turn: 4, type: "memory.write", text: "scope=session · key=root_cause", tone: "memory", at: 3180 },
  { turn: 4, type: "hitl.policy_check", text: "tool=k8s.set_env risk=high → always_ask", tone: "warning", at: 3220 },
  { turn: 4, type: "hitl.requested", text: "approval pending · audit_id=a8f3.k2p1", tone: "warning", at: 3240 },
  { turn: 4, type: "loop.paused", text: "loop paused · awaiting approval", tone: "warning", at: 3242 },
];

const LoopDebug = () => {
  const [filter, setFilter] = useLp({ thinking: true, tool: true, memory: true, hitl: true, verification: true, subagent: true });
  const [selected, setSelected] = useLp(22);
  const [cursor, setCursor] = useLp(LoopEvents.length); // events visible up to cursor (exclusive)
  const [playing, setPlaying] = useLp(false);
  const [speed, setSpeed] = useLp(8); // x

  React.useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setCursor(c => {
        if (c >= LoopEvents.length) { setPlaying(false); return c; }
        return c + 1;
      });
    }, 1000 / speed);
    return () => clearInterval(id);
  }, [playing, speed]);

  const visible = LoopEvents.slice(0, cursor);
  const lastEvent = visible[visible.length - 1];
  const isLive = cursor >= LoopEvents.length;

  return (
    <div className="loop-canvas">
      <div className="loop-track">
        <LoopDebugHeader
          filter={filter} onFilter={setFilter}
          cursor={cursor} total={LoopEvents.length}
          playing={playing} onPlay={() => {
            if (cursor >= LoopEvents.length) setCursor(1);
            setPlaying(p => !p);
          }}
          onReset={() => { setCursor(LoopEvents.length); setPlaying(false); }}
          onScrub={setCursor}
          speed={speed} onSpeed={setSpeed}
          lastEvent={lastEvent}
        />
        {[0,1,2,3,4].map(t => {
          const ev = visible.filter(e => e.turn === t);
          if (!ev.length) return null;
          const isLastTurn = t === 4 && isLive;
          const isCurrentTurn = lastEvent && lastEvent.turn === t && !isLive;
          return (
            <div key={t} className="loop-turn" data-status={isCurrentTurn ? "running" : isLastTurn ? "running" : "done"}>
              <div className="loop-turn-head">
                <span className="turn-no">turn {t}</span>
                {t === 0 ? <span style={{ fontWeight: 500 }}>User message</span> :
                  <span style={{ fontWeight: 500 }}>Loop iteration</span>}
                <span className="mono subtle">· {ev.length} event{ev.length !== 1 ? "s" : ""}</span>
                <span style={{ flex: 1 }} />
                {isCurrentTurn && <Badge tone="info" dot><span className="pulse">streaming</span></Badge>}
                {isLastTurn && <Badge tone="warning" dot>hitl-paused</Badge>}
                {!isCurrentTurn && !isLastTurn && t !== 0 && <Badge tone="success" dot>completed</Badge>}
                {t !== 0 && <span className="mono subtle">· {((ev.at(-1).at - ev[0].at) / 1000).toFixed(2)}s</span>}
              </div>
              <div className="loop-turn-body">
                {ev.map((e) => {
                  const idx = LoopEvents.indexOf(e);
                  const isLatest = e === lastEvent;
                  return (
                    <EventRow
                      key={idx}
                      event={e} idx={idx}
                      selected={idx === selected}
                      streaming={isLatest && !isLive}
                      onClick={() => setSelected(idx)}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
        {!isLive && (
          <div style={{ padding: "10px 12px", display: "flex", alignItems: "center", gap: 8, color: "var(--fg-subtle)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
            <span className="pulse" style={{ width: 6, height: 6, background: "var(--primary)", borderRadius: "50%" }} />
            replaying at {speed}× · {cursor}/{LoopEvents.length} events
          </div>
        )}
      </div>
      <LoopInspector event={LoopEvents[selected]} />
    </div>
  );
};

const LoopDebugHeader = ({ filter, onFilter, cursor, total, playing, onPlay, onReset, onScrub, speed, onSpeed, lastEvent }) => (
  <div className="col" style={{ marginBottom: 14, gap: 12 }}>
    <div className="row" style={{ gap: 10 }}>
      <div>
        <div className="page-title" style={{ fontSize: 18 }}>Loop Visualizer</div>
        <div className="page-sub">
          Session <span className="mono">sess_4tk2p</span>
          <span className="route-pill">/loop-debug</span>
          {cursor >= total
            ? <Badge tone="warning" dot>hitl-paused</Badge>
            : <Badge tone="info" dot><span className="pulse">replay {speed}×</span></Badge>}
        </div>
      </div>
      <div className="grow" />
      <div className="row" style={{ gap: 4 }}>
        {Object.entries({ thinking: "var(--thinking)", tool: "var(--tool)", memory: "var(--memory)", hitl: "var(--warning)", verification: "var(--success)", subagent: "var(--info)" }).map(([k, c]) => (
          <button
            key={k}
            onClick={() => onFilter({ ...filter, [k]: !filter[k] })}
            className="badge"
            style={{
              opacity: filter[k] ? 1 : 0.35,
              color: c,
              background: `oklch(from ${c} l c h / 0.14)`,
              borderColor: `oklch(from ${c} l c h / 0.32)`,
              cursor: "pointer",
              fontSize: 11,
            }}
          >
            <span style={{ width: 6, height: 6, background: c, borderRadius: "50%", display: "inline-block" }} />
            {k}
          </button>
        ))}
      </div>
    </div>

    <div className="row" style={{ gap: 8, padding: "8px 12px", background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
      <Button variant={playing ? "warning" : "primary"} size="sm" icon={playing ? "pause" : "play"} onClick={onPlay}>
        {playing ? "Pause" : cursor >= total ? "Replay" : "Resume"}
      </Button>
      <Button variant="ghost" size="sm" icon="refresh" onClick={onReset} title="Skip to live" />
      <div className="grow" style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
        <span className="mono subtle" style={{ fontSize: 11, minWidth: 70 }}>
          {String(cursor).padStart(2, "0")} / {total}
        </span>
        <input
          type="range" min={0} max={total} value={cursor}
          onChange={(e) => onScrub(Number(e.target.value))}
          style={{ flex: 1, accentColor: "var(--primary)" }}
        />
        <span className="mono subtle" style={{ fontSize: 11, minWidth: 70, textAlign: "right" }}>
          {lastEvent ? `+${lastEvent.at}ms` : "—"}
        </span>
      </div>
      <div className="btn-group">
        {[1, 4, 8, 16].map(s => (
          <button key={s} className="btn" data-size="sm"
            onClick={() => onSpeed(s)}
            style={{
              background: s === speed ? "var(--primary-soft)" : "var(--bg-1)",
              color: s === speed ? "var(--primary)" : "var(--fg-muted)",
              borderColor: s === speed ? "var(--primary-soft-2)" : "var(--border)",
            }}>{s}×</button>
        ))}
      </div>
    </div>
  </div>
);

const EventRow = ({ event, idx, selected, streaming, onClick }) => {
  const toneMap = {
    fg: "var(--fg-muted)", primary: "var(--primary)", thinking: "var(--thinking)", tool: "var(--tool)",
    memory: "var(--memory)", success: "var(--success)", warning: "var(--warning)",
  };
  const c = toneMap[event.tone] || "var(--fg-muted)";
  return (
    <div
      className="event-row"
      onClick={onClick}
      style={{
        background: selected
          ? "oklch(from var(--primary) l c h / 0.10)"
          : streaming ? `oklch(from ${c} l c h / 0.08)` : "transparent",
        border: selected ? "1px solid var(--primary-soft-2)"
              : streaming ? `1px solid oklch(from ${c} l c h / 0.4)`
              : "1px solid transparent",
        animation: streaming ? "shimmer-row 1.4s ease-in-out infinite" : "none",
      }}>
      <span className="ev-dot" style={{ background: c, boxShadow: streaming ? `0 0 0 3px oklch(from ${c} l c h / 0.25)` : "none" }} />
      <span className="ev-type" style={{ color: c }}>{event.type}</span>
      <span className="ev-detail">{event.text}</span>
      <span className="ev-timing">+{event.at}ms</span>
    </div>
  );
};

const LoopInspector = ({ event }) => (
  <div className="loop-inspector">
    <div style={{ padding: 14, borderBottom: "1px solid var(--border)" }}>
      <div style={{ fontSize: 11, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6, fontFamily: "var(--font-mono)" }}>Event</div>
      <div className="row" style={{ gap: 8, marginBottom: 4 }}>
        <span className="ev-dot" style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--warning)" }} />
        <span className="mono" style={{ fontSize: 13, fontWeight: 600 }}>{event?.type}</span>
      </div>
      <div className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{event?.text}</div>
    </div>
    <div style={{ padding: 14 }}>
      <div className="col" style={{ gap: 7, fontSize: 12 }}>
        <KvRow k="ts" v="2026-05-16 10:42:31.240" mono />
        <KvRow k="turn" v={event?.turn} mono />
        <KvRow k="audit_id" v="a8f3.k2p1" mono />
        <KvRow k="span_id" v="a04.zp2" mono />
        <KvRow k="tenant" v="tenant_01h9a2" mono />
        <KvRow k="session_id" v="sess_4tk2p" mono />
        <KvRow k="agent" v="incident-responder" mono />
      </div>
      <div className="thin-rule" />
      <div style={{ fontSize: 11, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6, fontFamily: "var(--font-mono)" }}>HITL Policy</div>
      <div className="col" style={{ gap: 7, fontSize: 12 }}>
        <KvRow k="tool" v={<span className="mono" style={{ color: "var(--tool)" }}>k8s.set_env</span>} />
        <KvRow k="risk" v={<RiskBadge level="high" />} />
        <KvRow k="policy" v={<Badge tone="warning">always_ask</Badge>} />
        <KvRow k="sandbox" v={<Badge>RESTRICTED</Badge>} />
        <KvRow k="approvers" v="@platform-l2" mono />
      </div>
      <div className="thin-rule" />
      <div style={{ fontSize: 11, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6, fontFamily: "var(--font-mono)" }}>Raw payload</div>
      <pre style={{ margin: 0, padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 10.5, lineHeight: 1.55, color: "var(--fg-muted)", overflowX: "auto" }}>{`{
  "event": "hitl.requested",
  "trace_id": "6f3a.b2k1",
  "span_id": "a04.zp2",
  "audit_id": "a8f3.k2p1",
  "tool_call": {
    "name": "k8s.set_env",
    "input_hash": "sha256:b9...",
    "input_redacted": false
  },
  "policy": {
    "name": "always_ask",
    "matched_rule": "risk_high"
  },
  "expires_at": "2026-05-16T10:46:42Z"
}`}</pre>
    </div>
  </div>
);

const KvRow = ({ k, v, mono }) => (
  <div className="spread">
    <span className="muted" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{k}</span>
    <span className={mono ? "mono tnum" : ""} style={{ fontSize: 12 }}>{v}</span>
  </div>
);

// ============ /governance/approvals — HITL queue ============
const APPROVALS = [
  { id: "apr_4tk2p", session: "sess_4tk2p", session_title: "payment-gateway 5xx spike", agent: "incident-responder", tool: "k8s.set_env", risk: "high", policy: "always_ask", since: "0m 14s", sla: "4m 12s", scope: "tenant.acme-prod", operator: "Jamie Liu", domain: "incident", queue: "active" },
  { id: "apr_91kxu", session: "sess_91kxu", session_title: "Q4 compliance audit — PCI scope", agent: "compliance-auditor", tool: "audit.export_chain", risk: "medium", policy: "ask_once", since: "8m 02s", sla: "21m 58s", scope: "tenant.acme-prod", operator: "Priya M.", domain: "audit", queue: "active" },
  { id: "apr_kp23l", session: "sess_qqx88", session_title: "Anomaly: tenant_3kp9 token spike", agent: "compliance-auditor", tool: "billing.suspend_tenant", risk: "critical", policy: "always_ask", since: "12m 41s", sla: "17m 19s", scope: "platform.admin", operator: "—", domain: "audit", queue: "active" },
  { id: "apr_88vqc", session: "sess_88vqc", session_title: "RCA: cache eviction storm", agent: "rca-bot", tool: "redis.flush_keyspace", risk: "high", policy: "always_ask", since: "21m 33s", sla: "8m 27s", scope: "tenant.acme-prod", operator: "Sam W.", domain: "rca", queue: "active" },
  { id: "apr_g922p", session: "sess_paf09", session_title: "Patrol — eu-west database checks", agent: "patrol-runner", tool: "patrol_schedule", risk: "low", policy: "ask_once", since: "2h 11m", sla: "—", scope: "tenant.acme-prod", operator: "Yui K.", domain: "patrol", queue: "active" },
  { id: "apr_77a01", session: "sess_77a01", session_title: "Change CHG-4821 — DB schema migration", agent: "change-reviewer", tool: "schema.migrate", risk: "critical", policy: "always_ask", since: "—", sla: "—", scope: "tenant.acme-prod", operator: "Dan O.", domain: "incident", queue: "active" },
  { id: "apr_3kkpw", session: "sess_kpw01", session_title: "Outage: edge-cdn cache poisoning", agent: "incident-responder", tool: "cdn.purge_all", risk: "high", policy: "always_ask", since: "—", sla: "—", scope: "tenant.acme-prod", operator: "Ben P.", domain: "incident", queue: "active" },
];

const Approvals = () => {
  const [tab, setTab] = useLp("active");
  const [selected, setSelected] = useLp(APPROVALS[0].id);
  const active = APPROVALS.find(a => a.id === selected) || APPROVALS[0];
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">HITL Approvals</div>
          <div className="page-sub">
            Central queue · Approve/reject writes before agents commit
            <span className="route-pill">/governance/approvals</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="globe">Teams sync</Button>
          <Button variant="outline" size="sm" icon="download">Export</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Active queue" value="7" delta="+2" deltaDir="down" />
        <Stat label="p50 approval time" value="2m 18s" delta="-12s" deltaDir="up" />
        <Stat label="Approved · 24h" value="184" delta="+11" deltaDir="up" />
        <Stat label="Rejected · 24h" value="6" delta="+2" deltaDir="down" />
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { id: "active", label: "Active", count: 7 },
          { id: "approved", label: "Approved", count: 184 },
          { id: "rejected", label: "Rejected", count: 6 },
          { id: "expired", label: "Expired", count: 2 },
          { id: "policies", label: "Policies" },
        ]}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 14 }}>
        <Card title="Pending approvals" subtitle="Sorted by SLA urgency" bodyClass="flush" actions={
          <div className="row">
            <Button variant="ghost" size="sm" icon="filter">Risk: all</Button>
            <Button variant="ghost" size="sm" icon="sliders">Sort: SLA</Button>
          </div>
        }>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 18 }}></th>
                <th>Session</th>
                <th>Tool</th>
                <th>Risk</th>
                <th>Policy</th>
                <th>Operator</th>
                <th style={{ textAlign: "right" }}>SLA</th>
              </tr>
            </thead>
            <tbody>
              {APPROVALS.map(a => (
                <tr key={a.id} onClick={() => setSelected(a.id)} style={{ background: selected === a.id ? "oklch(from var(--primary) l c h / 0.08)" : undefined }}>
                  <td><SevDot level={a.risk} /></td>
                  <td>
                    <div style={{ fontSize: 12.5, fontWeight: 500 }}>{a.session_title}</div>
                    <div className="mono subtle" style={{ fontSize: 10.5 }}>{a.agent} · {a.id}</div>
                  </td>
                  <td><span className="mono" style={{ color: "var(--tool)", fontSize: 11.5 }}>{a.tool}</span></td>
                  <td><RiskBadge level={a.risk} /></td>
                  <td><Badge>{a.policy}</Badge></td>
                  <td className="subtle" style={{ fontSize: 11.5 }}>{a.operator}</td>
                  <td style={{ textAlign: "right" }}>
                    <span className="mono" style={{
                      fontSize: 11,
                      color: a.sla !== "—" && parseInt(a.sla) < 10 ? "var(--warning)" : "var(--fg-muted)"
                    }}>{a.sla}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title={<span className="row" style={{ gap: 6 }}>
            <span className={`sev-dot sev-${active.risk}`} />
            {active.id}
          </span>}
          subtitle={active.session_title}
          bodyClass="dense"
          actions={<Button variant="ghost" size="sm" icon="audit">Audit</Button>}
        >
          <div className="col" style={{ gap: 6, fontSize: 12, marginBottom: 12 }}>
            <KvRow k="tool" v={<span className="mono" style={{ color: "var(--tool)" }}>{active.tool}</span>} />
            <KvRow k="risk" v={<RiskBadge level={active.risk} />} />
            <KvRow k="policy" v={<Badge tone="warning">{active.policy}</Badge>} />
            <KvRow k="scope" v={<Badge>{active.scope}</Badge>} />
            <KvRow k="operator" v={active.operator} />
            <KvRow k="age" v={active.since} mono />
            <KvRow k="SLA remaining" v={<span className="mono" style={{ color: "var(--warning)" }}>{active.sla}</span>} />
          </div>
          <Field label="Tool input payload">
            <pre style={{ margin: 0, padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.55, color: "var(--fg)", maxHeight: 160, overflowY: "auto" }}>{`{
  "namespace": "prod-payments",
  "deployment": "${active.tool.includes("set_env") ? "payment-gateway-canary" : "—"}",
  "env": { "PGBOUNCER_POOL_SIZE": "200" },
  "rolling": true
}`}</pre>
          </Field>
          <div style={{ height: 8 }} />
          <Field label="Agent rationale">
            <div style={{ padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 12, color: "var(--fg-muted)", lineHeight: 1.55 }}>
              Same failure mode as INC-4012 (27 days ago). pgbouncer pool size on canary was never bumped to match prod (200). Pool saturation observed since 10:22.
            </div>
          </Field>
          <div className="thin-rule" />
          <div className="col" style={{ gap: 8 }}>
            <Button variant="success" icon="check">Approve & continue</Button>
            <Button variant="outline" icon="sliders">Approve with edits…</Button>
            <Button variant="danger" icon="x">Reject</Button>
            <Button variant="ghost" size="sm">Escalate to L2 · @platform-l2</Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

// ============ /memory — 5 scope × 3 time scale matrix ============
const SCOPES = [
  { id: "system", name: "system", sub: "global · cross-tenant", count: 84 },
  { id: "tenant", name: "tenant", sub: "tenant_01h9a2", count: 1280 },
  { id: "role", name: "role", sub: "operator · auditor · admin", count: 312 },
  { id: "user", name: "user", sub: "u_jamie · u_priya · …", count: 4820 },
  { id: "session", name: "session", sub: "sess_4tk2p · live", count: 18 },
];
const TIME_SCALES = ["permanent", "quarter", "day"];

const MEMORY_ENTRIES = {
  "system|permanent":   [{ k: "compliance.frameworks", v: "[PCI-DSS, SOC2, ISO27001]" }, { k: "policy.tripwires", v: "12 rules" }],
  "system|quarter":     [{ k: "rate_limits.global", v: "10k req/min" }],
  "system|day":         [],
  "tenant|permanent":   [{ k: "tenant.plan", v: "Pro" }, { k: "tenant.region", v: "ap-east-1" }, { k: "hitl.risk_high", v: "always_ask" }, { k: "hitl.risk_medium", v: "ask_once" }],
  "tenant|quarter":     [{ k: "usage.tokens", v: "4.2M / 10M" }, { k: "incidents.opened", v: "27" }],
  "tenant|day":         [{ k: "anomaly.token_spike", v: "tenant_3kp9 +320%" }],
  "role|permanent":     [{ k: "operator.tools_allowed", v: "26 read · 8 write" }, { k: "auditor.tools_allowed", v: "12 read" }],
  "role|quarter":       [{ k: "operator.preferred_rca", v: "5-whys" }],
  "role|day":           [],
  "user|permanent":     [{ k: "u_jamie.tz", v: "Asia/Taipei" }, { k: "u_jamie.lang", v: "zh-TW" }, { k: "u_jamie.role", v: "operator" }],
  "user|quarter":       [{ k: "u_jamie.preferences.rca_format", v: "5-whys + timeline" }, { k: "u_jamie.shortcuts", v: "12 saved" }],
  "user|day":           [{ k: "u_jamie.last_session", v: "sess_4tk2p" }, { k: "u_jamie.notifications", v: "2 unread" }],
  "session|permanent":  [],
  "session|quarter":    [],
  "session|day":        [{ k: "sess_4tk2p.root_cause", v: "pgbouncer pool too small" }, { k: "sess_4tk2p.evidence", v: "[metrics, INC-4012]" }, { k: "sess_4tk2p.severity", v: "P1" }],
};

// Time-travel timestamps (24 hours)
const TIME_TRAVEL_MARKS = [
  { t: 0, label: "now", at: "10:42:28" },
  { t: -5, label: "5m ago", at: "10:37:00" },
  { t: -30, label: "30m ago", at: "10:12:00" },
  { t: -120, label: "2h ago", at: "08:42:00" },
  { t: -360, label: "6h ago", at: "04:42:00" },
  { t: -1440, label: "1d ago", at: "yesterday" },
];

const MEMORY_OPS_TIMELINE = [
  { t: 0, op: "WRITE", scope: "session", k: "evidence" },
  { t: -1, op: "WRITE", scope: "session", k: "root_cause" },
  { t: -2, op: "READ", scope: "tenant", k: "hitl.risk_high" },
  { t: -4, op: "READ", scope: "user", k: "preferences.rca_format" },
  { t: -7, op: "WRITE", scope: "tenant", k: "anomaly.token_spike" },
  { t: -8, op: "READ", scope: "system", k: "policy.tripwires" },
  { t: -11, op: "EXPIRE", scope: "session", k: "scratchpad.q4_audit" },
  { t: -15, op: "WRITE", scope: "user", k: "shortcuts" },
  { t: -42, op: "READ", scope: "tenant", k: "plan" },
  { t: -120, op: "WRITE", scope: "tenant", k: "usage.tokens" },
  { t: -240, op: "READ", scope: "user", k: "tz" },
  { t: -380, op: "WRITE", scope: "session", k: "severity" },
];

const MemoryPage = () => {
  const [hovered, setHovered] = useLp(null);
  const [cursor, setCursor] = useLp(0); // minutes ago; 0 = now, negative = past
  const [playing, setPlaying] = useLp(false);

  useLpEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setCursor(c => {
        if (c <= -1440) { setPlaying(false); return -1440; }
        return c - 30;
      });
    }, 200);
    return () => clearInterval(id);
  }, [playing]);

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Memory Layers</div>
          <div className="page-sub">
            Dual-axis · 5 scope × 3 time scale
            <span className="route-pill">/memory</span>
            <span className="mono subtle">· 6,514 entries</span>
            {cursor < 0 && <Badge tone="info" dot>time-travel · {Math.abs(cursor)}m ago</Badge>}
          </div>
        </div>
        <div className="page-actions">
          <Button variant={cursor < 0 ? "warning" : "outline"} size="sm" icon="clock" onClick={() => setCursor(0)}>{cursor < 0 ? "Return to now" : "Time travel"}</Button>
          <Button variant="outline" size="sm" icon="download">Export</Button>
          <Button variant="primary" size="sm" icon="plus">New entry</Button>
        </div>
      </div>

      <TimeTravelScrubber cursor={cursor} onCursor={setCursor} playing={playing} onPlay={() => { setPlaying(p => !p); }} />

      <div style={{ height: 14 }} />

      <div className="memory-matrix" style={{ opacity: cursor < 0 ? 0.95 : 1, transition: "opacity 0.2s" }}>
        <div className="mm-cell mm-header"></div>
        {TIME_SCALES.map(t => (
          <div key={t} className="mm-cell mm-header">
            <div className="row" style={{ gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: t === "permanent" ? "var(--memory)" : t === "quarter" ? "var(--info)" : "var(--tool)" }} />
              <span>{t}</span>
              <span className="subtle">·</span>
              <span className="subtle">{t === "permanent" ? "TTL ∞" : t === "quarter" ? "TTL 90d" : "TTL 24h"}</span>
            </div>
          </div>
        ))}

        {SCOPES.map(scope => (
          <React.Fragment key={scope.id}>
            <div className="mm-cell mm-scope">
              <div className="name">{scope.name}</div>
              <div className="sub">{scope.sub}</div>
              <div className="row" style={{ gap: 6, marginTop: "auto", paddingTop: 8 }}>
                <Icon name="memory" size={12} style={{ color: "var(--memory)" }} />
                <span className="mono" style={{ fontSize: 10.5, color: "var(--fg-muted)" }}>{scope.count.toLocaleString()}</span>
              </div>
            </div>
            {TIME_SCALES.map(t => {
              const key = `${scope.id}|${t}`;
              const entries = MEMORY_ENTRIES[key] || [];
              // Time-travel: hide newer entries (the more in past, the more entries are removed)
              const visible = cursor < 0 && t === "day" && scope.id === "session"
                ? (cursor > -10 ? entries.slice(0, 1) : [])
                : cursor < -120 && t === "day"
                  ? []
                  : entries;
              return (
                <div key={key} className="mm-cell" onMouseEnter={() => setHovered(key)} onMouseLeave={() => setHovered(null)}
                  style={{ background: hovered === key ? "var(--bg-2)" : undefined, transition: "background 0.12s", cursor: "pointer" }}>
                  {visible.length === 0 && <div className="subtle" style={{ fontSize: 11, fontStyle: "italic" }}>— empty</div>}
                  {visible.slice(0, 4).map((e, i) => (
                    <div key={i} className="mm-entry" style={{ animation: cursor < 0 ? "fade-up 0.25s" : "none" }}>
                      <span className="k">{e.k}</span> <span className="subtle">= {e.v}</span>
                    </div>
                  ))}
                  {visible.length > 4 && <div className="subtle mono" style={{ fontSize: 10, marginTop: 4 }}>+{visible.length - 4} more</div>}
                  <div className="count">
                    {visible.length} entry{visible.length !== 1 ? "ies" : ""}
                    {cursor < 0 && entries.length !== visible.length && <span style={{ color: "var(--warning)" }}> · {entries.length - visible.length} hidden</span>}
                  </div>
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      <div style={{ height: 16 }} />

      <div className="grid-main">
        <Card title="Recent memory ops" subtitle="Live · last 100" bodyClass="flush" actions={<Button variant="ghost" size="sm">View all</Button>}>
          <table className="table">
            <thead><tr><th>Op</th><th>Scope</th><th>Key</th><th>Value</th><th>By</th><th>When</th></tr></thead>
            <tbody>
              {[
                { op: "WRITE", scope: "session.sess_4tk2p", k: "root_cause", v: "pgbouncer pool too small", by: "incident-responder", at: "10:42:27" },
                { op: "READ", scope: "user.jamie", k: "preferences.rca_format", v: "5-whys + timeline", by: "incident-responder", at: "10:42:24" },
                { op: "READ", scope: "tenant.acme-prod", k: "hitl.risk_high", v: "always_ask", by: "incident-responder", at: "10:42:26" },
                { op: "WRITE", scope: "tenant.acme-prod", k: "anomaly.token_spike", v: "tenant_3kp9 +320%", by: "compliance-auditor", at: "10:35:11" },
                { op: "EXPIRE", scope: "session.sess_91kxu", k: "scratchpad.q4_audit", v: "—", by: "system", at: "10:31:00" },
              ].map((m, i) => (
                <tr key={i}>
                  <td><Badge tone="memory">{m.op}</Badge></td>
                  <td className="mono" style={{ fontSize: 11 }}>{m.scope}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>{m.k}</td>
                  <td className="subtle mono" style={{ fontSize: 11, maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{m.v}</td>
                  <td className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{m.by}</td>
                  <td className="subtle" style={{ fontSize: 11 }}>{m.at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="GDPR right-to-erasure">
          <div className="col" style={{ gap: 10, fontSize: 12 }}>
            <div className="subtle">Tombstone subject across all memory scopes. WORM audit retains hash chain.</div>
            <Field label="Subject id"><input className="input mono" placeholder="u_…" /></Field>
            <Field label="Reason (audited)">
              <select className="select" defaultValue="gdpr">
                <option value="gdpr">GDPR Art. 17 erasure</option>
                <option value="ccpa">CCPA opt-out</option>
                <option value="legal">Legal hold release</option>
              </select>
            </Field>
            <Button variant="danger" size="sm" icon="warn">Issue tombstone</Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

const TimeTravelScrubber = ({ cursor, onCursor, playing, onPlay }) => {
  // Maps cursor (-1440..0) to slider value (0..100)
  const sliderValue = (cursor / -1440) * 100;
  const onSliderChange = (e) => onCursor(Math.round(-1440 * (Number(e.target.value) / 100) / 5) * 5);
  return (
    <Card bodyClass="dense" className="">
      <div className="row" style={{ gap: 12 }}>
        <Button variant={playing ? "warning" : "outline"} size="sm" icon={playing ? "pause" : "play"} onClick={onPlay}>
          {playing ? "Pause" : "Replay 24h"}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onCursor(0)}>Now</Button>
        <div className="grow" style={{ position: "relative" }}>
          <div style={{ position: "relative", height: 36 }}>
            {/* Op markers behind slider */}
            <div style={{ position: "absolute", left: 0, right: 0, top: 14, height: 8 }}>
              {MEMORY_OPS_TIMELINE.map((op, i) => {
                const left = ((-op.t) / 1440) * 100;
                const color = op.op === "WRITE" ? "var(--memory)" : op.op === "READ" ? "var(--info)" : "var(--warning)";
                return (
                  <div key={i} title={`${op.op} · ${op.scope}.${op.k}`} style={{
                    position: "absolute",
                    left: `${left}%`,
                    width: 2, height: 8,
                    background: color,
                    transform: "translateX(-50%)",
                    borderRadius: 1,
                  }} />
                );
              })}
            </div>
            <input
              type="range" min={0} max={100} step={0.5}
              value={sliderValue}
              onChange={onSliderChange}
              style={{ width: "100%", accentColor: "var(--primary)", position: "absolute", inset: 0 }}
            />
            <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, display: "flex", justifyContent: "space-between", pointerEvents: "none" }}>
              {TIME_TRAVEL_MARKS.slice().reverse().map(m => (
                <span key={m.t} className="mono subtle" style={{ fontSize: 10 }}>{m.label}</span>
              ))}
            </div>
          </div>
        </div>
        <div className="col" style={{ gap: 2, minWidth: 100, textAlign: "right" }}>
          <span className="mono" style={{ fontSize: 13, fontWeight: 600, color: cursor < 0 ? "var(--warning)" : "var(--fg)" }}>
            {cursor === 0 ? "now" : `T-${Math.abs(cursor)}m`}
          </span>
          <span className="mono subtle" style={{ fontSize: 10.5 }}>
            {cursor === 0 ? "10:42:28" :
             cursor > -60 ? `~${10}:${String(42 - Math.abs(cursor)).padStart(2, "0")}` :
             cursor > -1440 ? `~${10 - Math.floor(Math.abs(cursor) / 60)}h ago` : "yesterday"}
          </span>
        </div>
      </div>
    </Card>
  );
};

// ============ /audit — WORM Merkle chain ============
const AUDIT_ENTRIES = [
  { id: "a8f3.k2p1", kind: "hitl.requested", actor: "incident-responder", target: "k8s.set_env", at: "10:42:28", risk: "high", ok: true, hash: "9a3f8c…" },
  { id: "a8f3.k2p0", kind: "memory.write", actor: "incident-responder", target: "session.sess_4tk2p", at: "10:42:27", risk: "low", ok: true, hash: "12bd2e…" },
  { id: "a8f3.k0z2", kind: "tool.completed", actor: "incident-responder", target: "metrics.query", at: "10:42:24", risk: "low", ok: true, hash: "ff041a…" },
  { id: "a8f3.j99x", kind: "verification.pass", actor: "incident-responder", target: "claim:pool_saturated", at: "10:42:24", risk: "low", ok: true, hash: "2c0e91…" },
  { id: "a8f3.j10b", kind: "subagent.completed", actor: "log-scanner", target: "tail · grep 5xx", at: "10:42:22", risk: "low", ok: true, hash: "88e4a0…" },
  { id: "a8f3.h7nm", kind: "tool.completed", actor: "incident-responder", target: "incidents.list", at: "10:42:19", risk: "low", ok: true, hash: "6f3a01…" },
  { id: "a8f3.h0pp", kind: "session.created", actor: "u_jamie", target: "sess_4tk2p", at: "10:42:18", risk: "low", ok: true, hash: "0c2189…" },
  { id: "a8f3.g8za", kind: "policy.tripwire", actor: "system", target: "tenant_3kp9 token spike", at: "10:35:11", risk: "critical", ok: false, hash: "b71c1c…" },
];

const AuditPage = () => {
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Audit Chain</div>
          <div className="page-sub">
            WORM · Merkle-verified · GDPR-tombstone aware
            <span className="route-pill">/audit</span>
            <Badge tone="success" dot>chain integrity: ok</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="check">Verify chain</Button>
          <Button variant="outline" size="sm" icon="download">Export evidence</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Entries · 24h" value="48,210" delta="+2,180" deltaDir="up" />
        <Stat label="Tripwires fired" value="3" delta="+1" deltaDir="down" />
        <Stat label="Chain depth" value="1.2M" delta="+48k" deltaDir="up" />
        <Stat label="Last verified" value="2m ago" />
      </div>

      <div className="grid-main">
        <Card title="Recent audit entries" subtitle="Append-only · sha256 linked" bodyClass="flush" actions={
          <div className="row">
            <Button variant="ghost" size="sm" icon="filter">All kinds</Button>
            <Button variant="ghost" size="sm" icon="search" />
          </div>
        }>
          <div style={{ padding: "8px 16px" }}>
            <div className="audit-chain">
              {AUDIT_ENTRIES.map(e => (
                <div key={e.id} className="audit-link">
                  <div className={`audit-node ${e.ok ? "ok" : "danger"}`}>
                    <Icon name={e.kind.startsWith("hitl") ? "shield" : e.kind.startsWith("tool") ? "tool" : e.kind.startsWith("memory") ? "memory" : e.kind.startsWith("verification") ? "check" : e.kind.startsWith("subagent") ? "fork" : e.kind.startsWith("policy") ? "warn" : "log"} size={13} />
                  </div>
                  <div>
                    <div className="row" style={{ gap: 6, marginBottom: 4 }}>
                      <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{e.kind}</span>
                      {!e.ok && <Badge tone="risk-critical">tripwire</Badge>}
                      <span className="subtle" style={{ fontSize: 11 }}>actor: <span className="mono" style={{ color: "var(--fg-muted)" }}>{e.actor}</span></span>
                      <span className="subtle" style={{ fontSize: 11 }}>→ <span className="mono">{e.target}</span></span>
                    </div>
                    <div className="audit-hash">
                      <span className="h">id: {e.id}</span>
                      <span>·</span>
                      <span className="h">prev: {e.hash.slice(0, 6)}…</span>
                      <Icon name="chain" size={11} />
                      <span className="h">sha256: {e.hash}</span>
                    </div>
                  </div>
                  <div className="row" style={{ gap: 8, alignSelf: "center" }}>
                    <RiskBadge level={e.risk} />
                    <span className="mono subtle" style={{ fontSize: 11 }}>{e.at}</span>
                    <Icon name="chevron_right" size={14} className="subtle" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <div className="col" style={{ gap: 14 }}>
          <Card title="Merkle root" subtitle="Last sealed block">
            <div className="col" style={{ gap: 8, fontSize: 12 }}>
              <KvRow k="block_height" v="481,209" mono />
              <KvRow k="sealed_at" v="10:40:00 UTC" mono />
              <KvRow k="entries_in_block" v="1,024" mono />
              <div>
                <div className="subtle" style={{ fontSize: 11, marginBottom: 4 }}>Root hash</div>
                <pre style={{ margin: 0, padding: 8, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 10.5, color: "var(--fg-muted)", wordBreak: "break-all" }}>9a3f8c12bd2eff041a2c0e9188e4a06f3a010c2189b71c1c…ed12</pre>
              </div>
              <Button variant="outline" size="sm" icon="copy">Copy root</Button>
            </div>
          </Card>
          <Card title="Tripwires" subtitle="Active monitors">
            <div className="col" style={{ gap: 8, fontSize: 12 }}>
              {[
                { name: "Cross-tenant data egress", state: "armed", risk: "critical" },
                { name: "PII in tool input", state: "armed", risk: "high" },
                { name: "Token spike > 200%", state: "fired", risk: "critical" },
                { name: "Sandbox escape attempt", state: "armed", risk: "critical" },
                { name: "Provider key exposure", state: "armed", risk: "critical" },
              ].map(t => (
                <div key={t.name} className="spread">
                  <span className="row" style={{ gap: 6 }}>
                    <SevDot level={t.risk} />
                    <span style={{ fontSize: 12 }}>{t.name}</span>
                  </span>
                  <Badge tone={t.state === "fired" ? "danger" : "success"} dot>{t.state}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { LoopDebug, Approvals, MemoryPage, AuditPage });
