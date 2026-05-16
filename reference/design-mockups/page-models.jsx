/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, Stat, Spark */
const { useState: useMd } = React;

// Backed by backend/src/adapters/{anthropic, azure_openai, maf, _base/{chat_client, circuit_breaker_wrapper, pricing}}

const PROVIDERS = [
  { id: "anthropic",    name: "Anthropic",    region: "global · api.anthropic.com", auth: "API key", status: "connected", models: 4, p95: 1240, errors24: 2,  rotateIn: "60d" },
  { id: "azure_openai", name: "Azure OpenAI", region: "eastus · acme.openai.azure.com", auth: "managed identity", status: "connected", models: 3, p95: 980,  errors24: 0,  rotateIn: "n/a" },
  { id: "openai",       name: "OpenAI",       region: "global · api.openai.com", auth: "API key", status: "connected", models: 3, p95: 1180, errors24: 1,  rotateIn: "180d" },
  { id: "bedrock",      name: "AWS Bedrock",  region: "us-east-1 · bedrock-runtime", auth: "IAM role", status: "configured", models: 0, p95: null, errors24: 0, rotateIn: "n/a" },
  { id: "vertex",       name: "Google Vertex", region: "us-central1 · aiplatform", auth: "ADC", status: "configured", models: 0, p95: null, errors24: 0, rotateIn: "n/a" },
  { id: "self_hosted",  name: "Self-hosted vLLM", region: "kube · llm.acme.internal", auth: "mTLS", status: "degraded", models: 2, p95: 420, errors24: 12, rotateIn: "n/a" },
];

const MODELS = [
  { id: "claude-haiku-4-5",  provider: "anthropic",    ctx: 200_000, maxOut: 8_192,  thinking: true,  inPrice: 0.80, outPrice: 4.00, p50: 240, p95: 1240, fallback: "claude-sonnet-4-5", status: "live", default: true, kind: "chat" },
  { id: "claude-sonnet-4-5", provider: "anthropic",    ctx: 200_000, maxOut: 8_192,  thinking: true,  inPrice: 3.00, outPrice: 15.00, p50: 320, p95: 1820, fallback: "claude-opus-4-1", status: "live", kind: "chat" },
  { id: "claude-opus-4-1",   provider: "anthropic",    ctx: 200_000, maxOut: 8_192,  thinking: true,  inPrice: 15.00, outPrice: 75.00, p50: 480, p95: 2840, fallback: null, status: "live", kind: "chat" },
  { id: "claude-haiku-3-5",  provider: "anthropic",    ctx: 200_000, maxOut: 8_192,  thinking: false, inPrice: 0.25, outPrice: 1.25, p50: 180, p95: 820, fallback: null, status: "deprecated", kind: "chat" },
  { id: "gpt-5",             provider: "openai",       ctx: 128_000, maxOut: 16_384, thinking: true,  inPrice: 2.50, outPrice: 10.00, p50: 280, p95: 1480, fallback: "gpt-4o", status: "live", kind: "chat" },
  { id: "gpt-4o",            provider: "openai",       ctx: 128_000, maxOut: 16_384, thinking: false, inPrice: 2.50, outPrice: 10.00, p50: 220, p95: 1180, fallback: null, status: "live", kind: "chat" },
  { id: "o1-mini",           provider: "openai",       ctx: 128_000, maxOut: 65_536, thinking: true,  inPrice: 3.00, outPrice: 12.00, p50: 1840, p95: 8200, fallback: "gpt-4o", status: "live", kind: "chat" },
  { id: "azure-gpt-4o",      provider: "azure_openai", ctx: 128_000, maxOut: 16_384, thinking: false, inPrice: 2.50, outPrice: 10.00, p50: 210, p95: 980, fallback: "gpt-4o", status: "live", kind: "chat" },
  { id: "azure-gpt-4o-mini", provider: "azure_openai", ctx: 128_000, maxOut: 16_384, thinking: false, inPrice: 0.15, outPrice: 0.60, p50: 160, p95: 720, fallback: null, status: "live", kind: "chat" },
  { id: "azure-o1",          provider: "azure_openai", ctx: 128_000, maxOut: 65_536, thinking: true,  inPrice: 3.00, outPrice: 12.00, p50: 1720, p95: 7800, fallback: "azure-gpt-4o", status: "live", kind: "chat" },
  { id: "voyage-3-large",    provider: "anthropic",    ctx: 32_000,  maxOut: 0,      thinking: false, inPrice: 0.18, outPrice: 0, p50: 60, p95: 180, fallback: null, status: "live", kind: "embedding" },
  { id: "llama-3.1-70b",     provider: "self_hosted",  ctx: 131_072, maxOut: 8_192,  thinking: false, inPrice: 0.04, outPrice: 0.04, p50: 90, p95: 420, fallback: null, status: "live", kind: "chat" },
  { id: "llama-3.1-8b",      provider: "self_hosted",  ctx: 131_072, maxOut: 4_096,  thinking: false, inPrice: 0.01, outPrice: 0.01, p50: 30, p95: 140, fallback: null, status: "live", kind: "chat" },
];

const FALLBACK_CHAINS = [
  { name: "orchestrator-main",    chain: ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-1"], policy: "on circuit-breaker open · on TRANSIENT × 3" },
  { name: "compliance-auditor",   chain: ["claude-opus-4-1", "azure-o1"], policy: "on circuit-breaker open" },
  { name: "metrics-pull",         chain: ["azure-gpt-4o-mini", "claude-haiku-4-5"], policy: "on TRANSIENT × 3" },
  { name: "summarizer (compaction)", chain: ["claude-haiku-4-5", "azure-gpt-4o-mini", "llama-3.1-70b"], policy: "cost-first · max p95 1s" },
];

// Where models bind into runtime flows
const FLOW_BINDINGS = [
  { flow: "orchestrator-main",          role: "Primary loop", model: "claude-haiku-4-5",  page: "orchestrator", required: true },
  { flow: "orchestrator-main",          role: "Fallback ×2",  model: "claude-sonnet-4-5 + claude-opus-4-1", page: "orchestrator", required: false },
  { flow: "subagent · log-scanner",     role: "AsTool / Fork", model: "claude-haiku-4-5",  page: "subagents", required: true },
  { flow: "subagent · compliance-auditor", role: "Handoff / Teammate", model: "claude-opus-4-1", page: "subagents", required: true },
  { flow: "subagent · summarizer",      role: "AsTool",       model: "claude-haiku-4-5",  page: "subagents", required: true },
  { flow: "compaction (semantic)",      role: "Summarizer",   model: "claude-haiku-4-5",  page: "compaction", required: true },
  { flow: "memory · jit-retrieval",     role: "Re-ranker",    model: "azure-gpt-4o-mini", page: "jit-retrieval", required: false },
  { flow: "memory · embeddings",        role: "Vector encode", model: "voyage-3-large",  page: "memory", required: true },
  { flow: "verification",               role: "Claim checker", model: "azure-gpt-4o-mini", page: "verification", required: true },
  { flow: "redaction · classifier",     role: "PII classifier", model: "claude-haiku-4-5", page: "redaction", required: false },
];

const ModelsPage = () => {
  const [tab, setTab] = useMd("models");
  const [selected, setSelected] = useMd(null);
  const active = selected ? MODELS.find(m => m.id === selected) : null;
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">LLM Models</div>
          <div className="page-sub">
            Range 6 · Provider-neutral adapters · 13 models across 6 providers
            <span className="route-pill">/models</span>
            <Badge tone="warning">platform admin</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">Sync from adapters/</Button>
          <Button variant="primary" size="sm" icon="plus" onClick={() => setTab("new")}>Register model</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Active providers" value={String(PROVIDERS.filter(p => p.status === "connected").length)} unit={`/${PROVIDERS.length}`} />
        <Stat label="Registered models" value={String(MODELS.filter(m => m.status === "live").length)} delta="+2" deltaDir="up" />
        <Stat label="Avg cost / 1M tok" value="$1.84" delta="-$0.12" deltaDir="up" />
        <Stat label="Spend · MTD" value="$2,847" delta="+8.4%" deltaDir="down" />
      </div>

      <Tabs value={tab} onChange={(v) => { setTab(v); if (v !== "models") setSelected(null); }}
        items={[
          { id: "models",    label: "Models",    count: MODELS.length },
          { id: "providers", label: "Providers", count: PROVIDERS.length },
          { id: "fallback",  label: "Fallback chains" },
          { id: "bindings",  label: "Flow bindings", count: FLOW_BINDINGS.length },
          { id: "allowlist", label: "Per-tenant allowlist" },
          { id: "new",       label: "+ New model" },
        ]}
      />

      {tab === "models" && (
        active
          ? <ModelDetailSplit model={active} onClose={() => setSelected(null)} />
          : <ModelsTable onSelect={setSelected} />
      )}
      {tab === "providers" && <ProvidersTab />}
      {tab === "fallback" && <FallbackTab />}
      {tab === "bindings" && <BindingsTab />}
      {tab === "allowlist" && <AllowlistTab />}
      {tab === "new" && <NewModelWizard onCancel={() => setTab("models")} />}
    </div>
  );
};

const ModelsTable = ({ onSelect }) => (
  <Card title="Model registry" subtitle="Click a row to inspect / edit" bodyClass="flush">
    <table className="table">
      <thead><tr>
        <th>Model</th><th>Provider</th><th>Kind</th><th style={{ textAlign: "right" }}>Context</th>
        <th>Thinking</th>
        <th style={{ textAlign: "right" }}>$ in / 1M</th><th style={{ textAlign: "right" }}>$ out / 1M</th>
        <th style={{ textAlign: "right" }}>p95</th><th>Fallback</th><th>Status</th>
      </tr></thead>
      <tbody>
        {MODELS.map(m => (
          <tr key={m.id} onClick={() => onSelect(m.id)}>
            <td>
              <div className="row" style={{ gap: 6 }}>
                <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{m.id}</span>
                {m.default && <Badge tone="primary">default</Badge>}
              </div>
            </td>
            <td className="mono subtle" style={{ fontSize: 11 }}>{m.provider}</td>
            <td><Badge tone={m.kind === "embedding" ? "memory" : "info"}>{m.kind}</Badge></td>
            <td className="mono tnum subtle" style={{ textAlign: "right" }}>{(m.ctx / 1000).toFixed(0)}K</td>
            <td>{m.thinking ? <Badge tone="thinking">✓</Badge> : <span className="subtle">—</span>}</td>
            <td className="mono tnum" style={{ textAlign: "right" }}>${m.inPrice.toFixed(2)}</td>
            <td className="mono tnum" style={{ textAlign: "right" }}>${m.outPrice.toFixed(2)}</td>
            <td className="mono tnum" style={{ textAlign: "right" }}>{m.p95}ms</td>
            <td>{m.fallback ? <span className="mono subtle" style={{ fontSize: 11 }}>→ {m.fallback}</span> : <span className="subtle">—</span>}</td>
            <td><Badge tone={m.status === "live" ? "success" : "warning"} dot>{m.status}</Badge></td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

// ============ Model detail (split view) ============
const ModelDetailSplit = ({ model, onClose }) => {
  const bindings = FLOW_BINDINGS.filter(b => b.model.includes(model.id));
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
      <Card
        title={<span className="row" style={{ gap: 8 }}>
          <span className="mono">{model.id}</span>
          {model.default && <Badge tone="primary">default</Badge>}
          <Badge tone={model.status === "live" ? "success" : "warning"} dot>{model.status}</Badge>
        </span>}
        subtitle={`${model.provider} · ${model.kind} · ${(model.ctx / 1000).toFixed(0)}K context`}
        actions={<div className="row"><Button variant="ghost" size="sm" icon="play">Test</Button><Button variant="ghost" size="sm" onClick={onClose}><Icon name="x" size={14} /></Button></div>}
      >
        <div className="col" style={{ gap: 12 }}>
          <Field label="Model id (immutable)"><input className="input mono" readOnly defaultValue={model.id} /></Field>
          <Field label="Display alias"><input className="input" defaultValue={model.id.replace(/[-_]/g, " ")} /></Field>
          <Field label="Provider"><select className="select" defaultValue={model.provider}>{PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
          <div className="grid-2">
            <Field label="Context window (tokens)"><input className="input mono" defaultValue={model.ctx} /></Field>
            <Field label="Max output (tokens)"><input className="input mono" defaultValue={model.maxOut} /></Field>
          </div>
          <Field label="Capabilities">
            <div className="kbar">
              <Badge tone={model.kind === "chat" ? "success" : ""}>chat</Badge>
              <Badge tone={model.thinking ? "thinking" : ""}>thinking</Badge>
              <Badge tone={model.kind === "chat" ? "tool" : ""}>tool calls</Badge>
              <Badge tone={model.kind === "chat" ? "info" : ""}>streaming</Badge>
              <Badge tone={model.kind === "embedding" ? "memory" : ""}>embedding</Badge>
            </div>
          </Field>
          <div className="grid-2">
            <Field label="Input cost / 1M tokens" help="USD"><input className="input mono" defaultValue={`$${model.inPrice.toFixed(2)}`} /></Field>
            <Field label="Output cost / 1M tokens" help="USD"><input className="input mono" defaultValue={`$${model.outPrice.toFixed(2)}`} /></Field>
          </div>
          <Field label="Fallback target" help="On circuit-breaker open or TRANSIENT × 3">
            <select className="select" defaultValue={model.fallback || ""}>
              <option value="">(none)</option>
              {MODELS.filter(m => m.id !== model.id && m.kind === model.kind).map(m => <option key={m.id} value={m.id}>{m.id}</option>)}
            </select>
          </Field>
          <div className="thin-rule" />
          <div className="row" style={{ gap: 6 }}>
            <Button variant="primary" size="sm" icon="check">Save</Button>
            <Button variant="ghost" size="sm">Discard</Button>
            <div className="grow" />
            <Button variant="danger" size="sm" icon="x">Deprecate</Button>
          </div>
        </div>
      </Card>

      <div className="col" style={{ gap: 14 }}>
        <Card title={<span className="row" style={{ gap: 6 }}><Icon name="branch" size={13} />Used by</span>} subtitle={`${bindings.length} active binding${bindings.length === 1 ? "" : "s"} · click to edit at source`} bodyClass="dense">
          {bindings.length === 0 && <div className="empty" style={{ padding: 18 }}>Not bound to any flow yet. <a style={{ color: "var(--primary)" }} onClick={() => location.hash = "orchestrator"}>Bind →</a></div>}
          {bindings.map((b, i) => (
            <div key={i} onClick={() => location.hash = b.page} style={{ padding: "10px 6px", borderBottom: i < bindings.length - 1 ? "1px solid var(--border)" : "none", cursor: "pointer" }}>
              <div className="row" style={{ gap: 6 }}>
                <Icon name="arrow_right" size={11} className="subtle" />
                <span className="mono" style={{ fontSize: 12, fontWeight: 500, color: "var(--primary)" }}>{b.flow}</span>
                {b.required && <Badge tone="warning">required</Badge>}
              </div>
              <div className="subtle mono" style={{ fontSize: 11, marginTop: 2, paddingLeft: 17 }}>role: {b.role}</div>
            </div>
          ))}
        </Card>

        <Card title="Live metrics · last 1h" bodyClass="dense">
          <div className="col" style={{ gap: 7, fontSize: 12 }}>
            <div className="spread"><span className="muted">Calls</span><span className="mono">2,840</span></div>
            <div className="spread"><span className="muted">p50</span><span className="mono">{model.p50}ms</span></div>
            <div className="spread"><span className="muted">p95</span><span className="mono">{model.p95}ms</span></div>
            <div className="spread"><span className="muted">Errors</span><span className="mono">2 (0.07%)</span></div>
            <div className="spread"><span className="muted">Cache hit rate</span><span className="mono">38%</span></div>
            <div className="spread"><span className="muted">Spend · 1h</span><span className="mono">$12.84</span></div>
          </div>
          <div className="hr" />
          <Spark points={[model.p95 * 0.9, model.p95, model.p95 * 1.1, model.p95 * 0.95, model.p95 * 1.05, model.p95]} width={240} height={32} />
        </Card>
      </div>
    </div>
  );
};

// ============ Flow bindings tab ============
const BindingsTab = () => {
  // Group bindings by flow
  const flows = {};
  FLOW_BINDINGS.forEach(b => { (flows[b.flow] = flows[b.flow] || []).push(b); });
  return (
    <Card title="Where models bind into runtime flows" subtitle="Each consumer + which model it currently uses · click flow name to jump" bodyClass="flush">
      <table className="table">
        <thead><tr><th>Flow / consumer</th><th>Role</th><th>Bound model</th><th>Required</th><th></th></tr></thead>
        <tbody>
          {FLOW_BINDINGS.map((b, i) => {
            const isMulti = b.model.includes("+");
            return (
              <tr key={i} onClick={() => location.hash = b.page}>
                <td className="mono" style={{ fontSize: 12, fontWeight: 500, color: "var(--primary)" }}>{b.flow}</td>
                <td className="subtle" style={{ fontSize: 12 }}>{b.role}</td>
                <td>
                  <div className="row" style={{ gap: 4, flexWrap: "wrap" }}>
                    {b.model.split(" + ").map(m => (
                      <span key={m} className="mono" style={{
                        padding: "2px 7px", fontSize: 11,
                        background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 4,
                      }}>{m.trim()}</span>
                    ))}
                  </div>
                </td>
                <td>{b.required ? <Badge tone="warning">required</Badge> : <Badge>optional</Badge>}</td>
                <td><Icon name="chevron_right" size={14} className="subtle" /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)" }}>
        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>
          Bindings are the contract between <span className="mono">/models</span> and runtime consumers. When you change a model's id or deprecate it, every flow listed here must be re-bound. The same model can be bound to multiple flows (e.g. <span className="mono">claude-haiku-4-5</span> drives both orchestrator and compaction summarizer).
        </div>
      </div>
    </Card>
  );
};

// ============ New model wizard ============
const NEW_MODEL_STEPS = [
  { id: "basic",     title: "Identity",    desc: "Id, alias, kind" },
  { id: "provider",  title: "Provider",    desc: "Connection + auth" },
  { id: "capacity",  title: "Capacity",    desc: "Context + limits" },
  { id: "pricing",   title: "Pricing",     desc: "Input + output rates" },
  { id: "bindings",  title: "Bindings",    desc: "Where to use" },
  { id: "test",      title: "Test & ship", desc: "Smoke + activate" },
];

const NewModelWizard = ({ onCancel }) => {
  const [step, setStep] = useMd(0);
  const next = () => setStep(s => Math.min(s + 1, NEW_MODEL_STEPS.length - 1));
  const back = () => setStep(s => Math.max(s - 1, 0));
  const isLast = step === NEW_MODEL_STEPS.length - 1;
  return (
    <div style={{ maxWidth: 760, margin: "0 auto" }}>
      {/* Stepper */}
      <div style={{ position: "relative", marginBottom: 22 }}>
        <div style={{ position: "absolute", left: 14, right: 14, top: 12, height: 2, background: "var(--border)", borderRadius: 1 }} />
        <div style={{ position: "absolute", left: 14, top: 12, height: 2, background: "var(--primary)",
          width: `calc(${(step / (NEW_MODEL_STEPS.length - 1)) * 100}% - 14px)`,
          borderRadius: 1, transition: "width 0.25s" }} />
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${NEW_MODEL_STEPS.length}, 1fr)`, position: "relative" }}>
          {NEW_MODEL_STEPS.map((s, i) => {
            const done = i < step, current = i === step;
            return (
              <div key={s.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, cursor: "pointer" }} onClick={() => setStep(i)}>
                <div style={{
                  width: 26, height: 26, borderRadius: "50%",
                  background: done ? "var(--primary)" : current ? "var(--bg-1)" : "var(--bg-2)",
                  border: `1.5px solid ${done || current ? "var(--primary)" : "var(--border)"}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: done ? "var(--primary-fg)" : current ? "var(--primary)" : "var(--fg-muted)",
                  fontWeight: 600, fontSize: 11.5, fontFamily: "var(--font-mono)", zIndex: 1,
                }}>
                  {done ? <Icon name="check" size={12} /> : i + 1}
                </div>
                <div style={{ fontSize: 11.5, fontWeight: current ? 600 : 400, color: current ? "var(--fg)" : "var(--fg-muted)", textAlign: "center" }}>{s.title}</div>
                <div className="subtle" style={{ fontSize: 10.5, textAlign: "center" }}>{s.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      <Card title={NEW_MODEL_STEPS[step].title} subtitle={NEW_MODEL_STEPS[step].desc}>
        {step === 0 && (
          <div className="col" style={{ gap: 12 }}>
            <Field label="Model id" help="Immutable · used by adapter routing"><input className="input mono" defaultValue="claude-sonnet-4-7" placeholder="e.g. claude-sonnet-4-7" /></Field>
            <Field label="Display alias"><input className="input" defaultValue="Claude Sonnet 4.7" /></Field>
            <Field label="Kind">
              <div className="row" style={{ gap: 6 }}>
                {["chat", "embedding", "reranker"].map((k, i) => (
                  <button key={k} className="badge" style={{ cursor: "pointer", padding: "5px 12px", fontSize: 11.5, background: i === 0 ? "var(--primary-soft)" : "var(--bg-2)", color: i === 0 ? "var(--primary)" : "var(--fg-muted)", border: i === 0 ? "1px solid var(--primary)" : "1px solid var(--border)" }}>{k}</button>
                ))}
              </div>
            </Field>
          </div>
        )}
        {step === 1 && (
          <div className="col" style={{ gap: 12 }}>
            <Field label="Provider">
              <select className="select" defaultValue="anthropic">
                {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.name}{p.status === "configured" ? " · need API key" : ""}</option>)}
              </select>
            </Field>
            <Field label="Auth method">
              <div className="row" style={{ gap: 6 }}>
                {["API key", "managed identity", "IAM role", "mTLS"].map((a, i) => (
                  <Badge key={a} tone={i === 0 ? "primary" : ""}>{a}</Badge>
                ))}
              </div>
            </Field>
            <Field label="API key reference" help="Pulled from Key Vault; never inlined"><input className="input mono" defaultValue="kv://acme-prod/anthropic-api-key" /></Field>
            <Field label="Connection health">
              <div className="row" style={{ gap: 8 }}>
                <Badge tone="success" dot>OK · 188ms</Badge>
                <Button variant="outline" size="sm" icon="refresh">Re-test</Button>
              </div>
            </Field>
          </div>
        )}
        {step === 2 && (
          <div className="col" style={{ gap: 12 }}>
            <div className="grid-2">
              <Field label="Context window (tokens)"><input className="input mono" defaultValue="200000" /></Field>
              <Field label="Max output (tokens)"><input className="input mono" defaultValue="16384" /></Field>
            </div>
            <Field label="Max thinking tokens / turn"><input className="input mono" defaultValue="4096" /></Field>
            <Field label="Streaming">
              <div className="row"><Switch on={true} /><span className="muted">SSE supported</span></div>
            </Field>
            <Field label="Tool calls">
              <div className="row"><Switch on={true} /><span className="muted">Native tool_calls schema (LLM-neutral)</span></div>
            </Field>
          </div>
        )}
        {step === 3 && (
          <div className="col" style={{ gap: 12 }}>
            <div className="grid-2">
              <Field label="Input cost / 1M tokens (USD)"><input className="input mono" defaultValue="3.00" /></Field>
              <Field label="Output cost / 1M tokens (USD)"><input className="input mono" defaultValue="15.00" /></Field>
            </div>
            <Field label="Thinking cost / 1M tokens (USD)" help="If different from output"><input className="input mono" defaultValue="3.00" /></Field>
            <Field label="Cache discount">
              <div className="row" style={{ gap: 8 }}>
                <input className="input mono" defaultValue="0.10" style={{ maxWidth: 100 }} />
                <span className="muted">× input rate for cached prompts</span>
              </div>
            </Field>
          </div>
        )}
        {step === 4 && (
          <div className="col" style={{ gap: 12 }}>
            <div className="muted" style={{ fontSize: 12.5, marginBottom: 6 }}>Pick which runtime flows should use this model when it ships. You can wire more later from each flow page.</div>
            {[
              { flow: "orchestrator-main · primary", page: "orchestrator", checked: false },
              { flow: "orchestrator-main · fallback ×2", page: "orchestrator", checked: true },
              { flow: "subagent · compliance-auditor", page: "subagents", checked: true },
              { flow: "subagent · postmortem-writer", page: "subagents", checked: true },
              { flow: "compaction (semantic)", page: "compaction", checked: false },
              { flow: "verification claim-checker", page: "verification", checked: false },
            ].map((b, i) => (
              <div key={i} className="row" style={{ gap: 8, padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: b.checked ? "var(--primary-soft)" : "var(--bg-1)" }}>
                <input type="checkbox" defaultChecked={b.checked} style={{ accentColor: "var(--primary)" }} />
                <span className="mono" style={{ fontSize: 12.5, color: b.checked ? "var(--primary)" : "var(--fg)" }}>{b.flow}</span>
                <span className="subtle" style={{ marginLeft: "auto", fontSize: 11 }}>→ /{b.page}</span>
              </div>
            ))}
            <div className="muted" style={{ fontSize: 11.5, padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6 }}>
              Bindings are 2-way: the consumer page (e.g. <span className="mono">/orchestrator</span>) also shows this model as an option once registered. WORM audit logs every binding change.
            </div>
          </div>
        )}
        {step === 5 && (
          <div className="col" style={{ gap: 12 }}>
            <Field label="Smoke test prompt"><textarea className="textarea" rows="3" defaultValue="Hello! Reply with the model id and 3-word summary." /></Field>
            <Card bodyClass="dense" className="">
              <div className="col" style={{ gap: 6, fontSize: 12 }}>
                <div className="spread"><span className="muted">Endpoint</span><span className="mono">connect ✓ · 188ms</span></div>
                <div className="spread"><span className="muted">Auth</span><span className="mono">200 OK</span></div>
                <div className="spread"><span className="muted">Streaming</span><span className="mono">SSE OK · first token 240ms</span></div>
                <div className="spread"><span className="muted">Tool call schema</span><span className="mono">native tool_calls ✓</span></div>
                <div className="spread"><span className="muted">Cost estimate</span><span className="mono">$0.0042 / smoke run</span></div>
                <div className="spread"><span className="muted">Status</span><Badge tone="success" dot>ready to register</Badge></div>
              </div>
            </Card>
            <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>
              On <span className="mono">Register</span>, the model becomes available in the registry, fallback chains and per-tenant allowlist. Selected bindings are applied atomically.
            </div>
          </div>
        )}
      </Card>

      <div className="row" style={{ marginTop: 14, gap: 8 }}>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button variant="outline" onClick={back} disabled={step === 0}>Back</Button>
        <div className="grow" />
        <Button variant="primary" icon={isLast ? "bolt" : undefined} iconRight={!isLast ? "arrow_right" : undefined} onClick={isLast ? onCancel : next}>
          {isLast ? "Register model" : "Continue"}
        </Button>
      </div>
    </div>
  );
};

// ============ Providers tab (unchanged) ============
const ProvidersTab = () => (
  <div className="grid-3">
    {PROVIDERS.map(p => (
      <div key={p.id} className="card" style={{ borderLeft: `3px solid ${p.status === "connected" ? "var(--success)" : p.status === "degraded" ? "var(--warning)" : "var(--fg-subtle)"}` }}>
        <div className="card-body">
          <div className="row" style={{ gap: 8, marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{p.name}</span>
            <Badge tone={p.status === "connected" ? "success" : p.status === "degraded" ? "warning" : ""} dot>{p.status}</Badge>
            <Icon name="dots" size={14} className="subtle" style={{ marginLeft: "auto" }} />
          </div>
          <div className="col" style={{ gap: 6, fontSize: 12 }}>
            <div className="spread"><span className="muted">Region</span><span className="mono" style={{ fontSize: 11 }}>{p.region}</span></div>
            <div className="spread"><span className="muted">Auth</span><span className="mono" style={{ fontSize: 11 }}>{p.auth}</span></div>
            <div className="spread"><span className="muted">Models</span><span className="mono">{p.models}</span></div>
            <div className="spread"><span className="muted">p95 latency</span><span className="mono">{p.p95 != null ? `${p.p95}ms` : "—"}</span></div>
            <div className="spread"><span className="muted">Errors · 24h</span><span className="mono" style={{ color: p.errors24 > 5 ? "var(--warning)" : "var(--fg)" }}>{p.errors24}</span></div>
            <div className="spread"><span className="muted">Key rotation</span><span className="mono">{p.rotateIn}</span></div>
          </div>
          <div className="hr" />
          <div className="row" style={{ gap: 6 }}>
            <Button variant="outline" size="sm" icon="refresh">Test</Button>
            <Button variant="ghost" size="sm" icon="keys">Rotate key</Button>
          </div>
        </div>
      </div>
    ))}
    <div className="card" style={{ borderStyle: "dashed", display: "flex", alignItems: "center", justifyContent: "center", minHeight: 200, cursor: "pointer" }}>
      <div className="col" style={{ alignItems: "center", gap: 6, color: "var(--fg-muted)" }}>
        <Icon name="plus" size={20} />
        <span style={{ fontSize: 13 }}>Add provider</span>
      </div>
    </div>
  </div>
);

const FallbackTab = () => (
  <Card title="Fallback chains" subtitle="When primary fails (circuit-breaker open or TRANSIENT × 3)" bodyClass="">
    <div className="col" style={{ gap: 18 }}>
      {FALLBACK_CHAINS.map(c => (
        <div key={c.name}>
          <div className="row" style={{ gap: 8, marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</span>
            <span className="subtle mono" style={{ fontSize: 11 }}>{c.policy}</span>
          </div>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {c.chain.map((m, i) => (
              <React.Fragment key={i}>
                <div style={{ padding: "6px 10px", border: `1px solid ${i === 0 ? "var(--primary)" : "var(--border)"}`, borderRadius: 4, background: i === 0 ? "var(--primary-soft)" : "var(--bg-2)", display: "flex", alignItems: "center", gap: 6 }}>
                  {i === 0 && <span className="mono" style={{ fontSize: 9, padding: "1px 4px", background: "var(--primary)", color: "white", borderRadius: 2 }}>1°</span>}
                  <span className="mono" style={{ fontSize: 11.5, color: i === 0 ? "var(--primary)" : "var(--fg)" }}>{m}</span>
                </div>
                {i < c.chain.length - 1 && <Icon name="arrow_right" size={13} className="subtle" />}
              </React.Fragment>
            ))}
            <Button variant="ghost" size="sm" icon="plus">Add</Button>
          </div>
        </div>
      ))}
    </div>
  </Card>
);

const AllowlistTab = () => {
  const tenants = [
    { name: "acme-prod", plan: "Pro", allowed: ["claude-haiku-4-5", "claude-sonnet-4-5", "azure-gpt-4o", "voyage-3-large"] },
    { name: "globex-eu", plan: "Pro", allowed: ["claude-haiku-4-5", "azure-gpt-4o", "azure-gpt-4o-mini"] },
    { name: "initech-jp", plan: "Enterprise", allowed: ["claude-opus-4-1", "claude-sonnet-4-5", "claude-haiku-4-5", "azure-o1", "voyage-3-large"] },
    { name: "wonka-apac", plan: "Starter", allowed: ["claude-haiku-4-5", "azure-gpt-4o-mini"] },
  ];
  const chatModels = MODELS.filter(m => m.kind !== "embedding");
  return (
    <Card title="Per-tenant model allowlist" subtitle="Which models can each tenant use · click to toggle" bodyClass="flush">
      <table className="table">
        <thead>
          <tr>
            <th style={{ minWidth: 160 }}>Tenant</th>
            <th>Plan</th>
            {chatModels.map(m => <th key={m.id} style={{ textAlign: "center" }}>
              <span className="mono" style={{ fontSize: 9.5, writingMode: "vertical-rl", transform: "rotate(180deg)", display: "inline-block", whiteSpace: "nowrap" }}>{m.id}</span>
            </th>)}
          </tr>
        </thead>
        <tbody>
          {tenants.map(t => (
            <tr key={t.name}>
              <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{t.name}</td>
              <td><Badge tone={t.plan === "Enterprise" ? "primary" : t.plan === "Pro" ? "info" : ""}>{t.plan}</Badge></td>
              {chatModels.map(m => (
                <td key={m.id} style={{ textAlign: "center" }}>
                  {t.allowed.includes(m.id)
                    ? <span style={{ display: "inline-flex", width: 20, height: 20, borderRadius: 4, background: "oklch(from var(--success) l c h / 0.18)", color: "var(--success)", alignItems: "center", justifyContent: "center" }}><Icon name="check" size={11} /></span>
                    : <span className="subtle mono" style={{ fontSize: 10 }}>—</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
};

Object.assign(window, { ModelsPage });
