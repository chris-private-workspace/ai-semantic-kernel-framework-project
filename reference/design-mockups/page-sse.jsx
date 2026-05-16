/* global React, Icon, Button, Badge, Card, Field, RiskBadge */
const { useState: useSse, useEffect: useESse, useRef: useRSse } = React;

// 22 LoopEvent types from the V2 spec
const EVENT_TYPES = [
  { name: "session.created", tone: "var(--primary)", weight: 0.5 },
  { name: "loop.iteration.start", tone: "var(--primary)", weight: 8 },
  { name: "loop.iteration.end", tone: "var(--primary)", weight: 8 },
  { name: "thinking.start", tone: "var(--thinking)", weight: 8 },
  { name: "thinking.delta", tone: "var(--thinking)", weight: 24 },
  { name: "thinking.end", tone: "var(--thinking)", weight: 8 },
  { name: "tool.requested", tone: "var(--tool)", weight: 6 },
  { name: "tool.started", tone: "var(--tool)", weight: 6 },
  { name: "tool.completed", tone: "var(--tool)", weight: 6 },
  { name: "tool.failed", tone: "var(--danger)", weight: 0.2 },
  { name: "verification.run", tone: "var(--success)", weight: 4 },
  { name: "verification.fail", tone: "var(--danger)", weight: 0.3 },
  { name: "memory.read", tone: "var(--memory)", weight: 3 },
  { name: "memory.write", tone: "var(--memory)", weight: 1.5 },
  { name: "memory.expire", tone: "var(--memory)", weight: 0.3 },
  { name: "subagent.spawned", tone: "var(--info)", weight: 0.4 },
  { name: "subagent.completed", tone: "var(--info)", weight: 0.4 },
  { name: "hitl.policy_check", tone: "var(--warning)", weight: 1 },
  { name: "hitl.requested", tone: "var(--warning)", weight: 0.2 },
  { name: "hitl.resolved", tone: "var(--warning)", weight: 0.2 },
  { name: "tripwire.fired", tone: "var(--danger)", weight: 0.05 },
  { name: "session.completed", tone: "var(--primary)", weight: 0.3 },
];

const totalWeight = EVENT_TYPES.reduce((a, b) => a + b.weight, 0);
const pickEvent = () => {
  let r = Math.random() * totalWeight;
  for (const e of EVENT_TYPES) {
    r -= e.weight;
    if (r <= 0) return e;
  }
  return EVENT_TYPES[0];
};

const detailFor = (name) => {
  if (name === "thinking.delta") return '"…confirming pgbouncer pool size from canary deployment…"';
  if (name === "tool.requested") return ["metrics.query", "log.tail", "incident_get", "audit_query_logs"][Math.floor(Math.random() * 4)];
  if (name === "tool.completed") return `${["rows=42", "ok=true", "duration=210ms", "bytes=1820"][Math.floor(Math.random() * 4)]}`;
  if (name === "memory.read") return `scope=${["user.jamie","tenant.acme-prod","session.sess_4tk2p","role.operator"][Math.floor(Math.random() * 4)]}`;
  if (name === "memory.write") return `key=evidence.${Math.random().toString(36).slice(2, 8)}`;
  if (name === "hitl.policy_check") return `risk=${["low","medium","high"][Math.floor(Math.random()*3)]} → ${["auto","ask_once","always_ask"][Math.floor(Math.random()*3)]}`;
  if (name === "verification.run") return "claim verified · evidence=2 rows";
  if (name === "loop.iteration.start") return `iteration_${Math.floor(Math.random() * 30) + 1}`;
  if (name === "loop.iteration.end") return `stop=${["tool_use", "tool_use", "end_turn"][Math.floor(Math.random()*3)]}`;
  return "—";
};

// ============ SSE Inspector — protocol simulator ============
const SSEInspector = () => {
  const [connected, setConnected] = useSse(true);
  const [paused, setPaused] = useSse(false);
  const [rate, setRate] = useSse(8); // events/sec
  const [events, setEvents] = useSse([]);
  const [filter, setFilter] = useSse(new Set());
  const [lastEventId, setLastEventId] = useSse(0);
  const [reconnectIn, setReconnectIn] = useSse(0);
  const [stats, setStats] = useSse({ total: 0, retries: 0, bytes: 0, errors: 0 });

  // Synthetic event generation
  useESse(() => {
    if (!connected || paused) return;
    const interval = 1000 / rate;
    const id = setInterval(() => {
      const t = pickEvent();
      const detail = detailFor(t.name);
      const ev = {
        ts: Date.now(),
        type: t.name,
        tone: t.tone,
        detail,
        bytes: 80 + Math.floor(Math.random() * 240),
      };
      setLastEventId(prev => prev + 1);
      setEvents(evs => [{ ...ev, id: (evs[0]?.id || 0) + 1, turn: Math.floor(((evs[0]?.id || 0) + 1) / 8) }, ...evs].slice(0, 200));
      setStats(s => ({ ...s, total: s.total + 1, bytes: s.bytes + ev.bytes, errors: s.errors + (t.name.endsWith(".failed") || t.name === "tripwire.fired" ? 1 : 0) }));
      if (Math.random() < 0.003) setConnected(false);
    }, interval);
    return () => clearInterval(id);
  }, [connected, paused, rate]);

  // Reconnect countdown
  useESse(() => {
    if (connected) return;
    setReconnectIn(3);
    const id = setInterval(() => {
      setReconnectIn(c => {
        if (c <= 1) {
          setConnected(true);
          setStats(s => ({ ...s, retries: s.retries + 1 }));
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [connected]);

  const visible = events.filter(e => filter.size === 0 || filter.has(e.type));

  const toggleFilter = (name) => {
    setFilter(f => {
      const next = new Set(f);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  };

  const eventCounts = EVENT_TYPES.map(t => ({ ...t, count: events.filter(e => e.type === t.name).length }));

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">SSE Inspector</div>
          <div className="page-sub">
            22 LoopEvent types · Range 4 Streaming · simulated protocol contract
            <span className="route-pill">/devui/sse</span>
            <Badge tone="warning">platform scope</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" size="sm" icon="download">.har</Button>
          <Button variant={paused ? "primary" : "outline"} size="sm" icon={paused ? "play" : "pause"} onClick={() => setPaused(p => !p)}>
            {paused ? "Resume" : "Pause"}
          </Button>
          <Button variant="outline" size="sm" icon="refresh" onClick={() => setConnected(false)}>Force reconnect</Button>
        </div>
      </div>

      {/* Connection bar */}
      <div style={{ marginBottom: 12 }}>
        <Card bodyClass="dense">
          <div className="row" style={{ gap: 16, flexWrap: "wrap" }}>
            <div className="row" style={{ gap: 8 }}>
              {connected
                ? <><span className="live-dot" /><span style={{ fontSize: 13, fontWeight: 500, color: "var(--success)" }}>Connected</span></>
                : <><span className="live-dot" style={{ background: "var(--danger)" }} /><span style={{ fontSize: 13, fontWeight: 500, color: "var(--danger)" }}>Reconnecting in {reconnectIn}s</span></>}
            </div>
            <KvInline k="endpoint" v="GET /v1/sessions/sess_4tk2p/events" />
            <KvInline k="content-type" v="text/event-stream" />
            <KvInline k="last-event-id" v={String(lastEventId).padStart(6, "0")} mono />
            <div className="grow" />
            <KvInline k="rate" v={`${rate}/s`} />
            <KvInline k="total" v={stats.total.toLocaleString()} />
            <KvInline k="retries" v={stats.retries} />
            <KvInline k="bytes" v={`${(stats.bytes / 1024).toFixed(1)} kB`} />
          </div>
        </Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 12 }}>
        {/* Event stream */}
        <Card
          title={<span className="row" style={{ gap: 8 }}>
            <Icon name="log" size={13} />
            Event stream
            {filter.size > 0 && <Badge tone="primary">filter: {filter.size}</Badge>}
          </span>}
          subtitle={`${visible.length} of ${events.length} events · auto-scrolling`}
          bodyClass="flush"
          actions={<Button variant="ghost" size="sm" icon="x" onClick={() => setFilter(new Set())}>Clear filter</Button>}
        >
          <div style={{ maxHeight: 540, overflowY: "auto", fontFamily: "var(--font-mono)", fontSize: 11.5 }}>
            {visible.length === 0 && (
              <div className="empty">
                <Icon name="log" size={24} />
                <span>Waiting for events…</span>
              </div>
            )}
            {visible.map((e, i) => (
              <div key={e.id} style={{
                display: "grid",
                gridTemplateColumns: "60px 130px 90px 1fr 60px",
                gap: 10,
                padding: "5px 14px",
                borderBottom: "1px solid var(--border)",
                animation: i === 0 ? "fade-up 0.25s ease-out" : "none",
                background: i === 0 ? `oklch(from ${e.tone} l c h / 0.06)` : "transparent",
              }}>
                <span style={{ color: "var(--fg-subtle)" }}>#{String(e.id).padStart(5, "0")}</span>
                <span style={{ color: "var(--fg-muted)" }}>{new Date(e.ts).toLocaleTimeString("en-US", { hour12: false })}</span>
                <span style={{ color: e.tone, fontWeight: 500 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: e.tone, display: "inline-block", marginRight: 5 }} />
                  t{e.turn}
                </span>
                <span style={{ color: "var(--fg)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  <span style={{ color: e.tone }}>{e.type}</span>{" "}
                  <span style={{ color: "var(--fg-subtle)" }}>{e.detail}</span>
                </span>
                <span style={{ color: "var(--fg-subtle)", textAlign: "right" }}>{e.bytes}b</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Right panel: event types + controls */}
        <div className="col" style={{ gap: 12 }}>
          <Card title="Rate" bodyClass="dense">
            <div className="col" style={{ gap: 8 }}>
              <input type="range" min={1} max={40} value={rate} onChange={e => setRate(Number(e.target.value))}
                style={{ width: "100%", accentColor: "var(--primary)" }} />
              <div className="spread">
                <span className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>1/s</span>
                <span className="mono" style={{ fontSize: 13, fontWeight: 600 }}>{rate}/s</span>
                <span className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>40/s</span>
              </div>
            </div>
          </Card>

          <Card title="Event types" subtitle={`22 LoopEvent kinds · click to filter`} bodyClass="dense">
            <div className="col" style={{ gap: 3, maxHeight: 360, overflowY: "auto" }}>
              {eventCounts.map(t => {
                const isActive = filter.has(t.name);
                return (
                  <button
                    key={t.name}
                    onClick={() => toggleFilter(t.name)}
                    style={{
                      display: "grid", gridTemplateColumns: "10px 1fr auto",
                      gap: 6, alignItems: "center",
                      padding: "3px 6px",
                      border: isActive ? `1px solid ${t.tone}` : "1px solid transparent",
                      background: isActive ? `oklch(from ${t.tone} l c h / 0.12)` : (filter.size && !isActive) ? "transparent" : "var(--bg-2)",
                      borderRadius: 4,
                      cursor: "pointer",
                      fontFamily: "var(--font-mono)",
                      fontSize: 10.5,
                      color: "var(--fg-muted)",
                      opacity: filter.size && !isActive ? 0.5 : 1,
                    }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: t.tone }} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", textAlign: "left", color: isActive ? t.tone : "var(--fg-muted)" }}>{t.name}</span>
                    <span className="tnum" style={{ color: "var(--fg-subtle)" }}>{t.count}</span>
                  </button>
                );
              })}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

const KvInline = ({ k, v, mono }) => (
  <span className="row" style={{ gap: 5, fontSize: 11.5 }}>
    <span className="mono subtle">{k}:</span>
    <span className={mono ? "mono" : ""} style={{ color: "var(--fg)" }}>{v}</span>
  </span>
);

Object.assign(window, { SSEInspector });
