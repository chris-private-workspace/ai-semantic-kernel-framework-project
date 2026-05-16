/* global React, Icon, Button, Badge, RiskBadge, ROUTES, t */
const { useState: useTb, useEffect: useEffTb, useRef: useRefTb } = React;

// ====================================================================
// Topbar overlays — CommandPalette (⌘K), NotificationsPanel (bell),
// UserMenu (avatar). Mounted near the root by app.jsx.
// ====================================================================

// shared backdrop hook: close on Escape / click outside
const useDismiss = (open, onClose, anchorRef) => {
  useEffTb(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    const onClick = (e) => {
      if (anchorRef && anchorRef.current && anchorRef.current.contains(e.target)) return;
      if (e.target.closest("[data-topbar-overlay]")) return;
      onClose();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open, onClose, anchorRef]);
};

// ─────────────────── Command Palette (⌘K) ───────────────────

const COMMANDS_EXTRA = [
  { type: "action", id: "act-new-chat",  icon: "chat",     label: "New chat",            hint: "Open Chat V2 and start a new session", category: "actions",  route: "chat-v2" },
  { type: "action", id: "act-review",    icon: "approval", label: "Review HITL queue",   hint: "Jump to pending approvals",            category: "actions",  route: "governance" },
  { type: "action", id: "act-onboard",   icon: "plus",     label: "Onboard tenant",      hint: "Tenant lifecycle wizard",               category: "actions",  route: "tenant-onboarding" },
  { type: "action", id: "act-incident",  icon: "warn",     label: "Declare incident",    hint: "Open incident console",                category: "actions",  route: "incidents" },
];

const TENANT_SUGGESTIONS = [
  { id: "t1", name: "acme-prod",    region: "ap-east-1",        plan: "Pro" },
  { id: "t2", name: "globex-eu",    region: "eu-west-1",        plan: "Pro" },
  { id: "t3", name: "initech-jp",   region: "ap-northeast-1",   plan: "Enterprise" },
];

const SESSION_SUGGESTIONS = [
  { id: "sess_8a2f1c3", agent: "incident-responder", tenant: "acme-prod",  status: "running" },
  { id: "sess_7c11d9e", agent: "compliance-auditor", tenant: "globex-eu",  status: "hitl-paused" },
  { id: "sess_4f88c1a", agent: "rca-explorer",       tenant: "acme-prod",  status: "verifying" },
];

const CommandPalette = ({ open, onClose, onNav }) => {
  const [q, setQ] = useTb("");
  const [activeIdx, setActiveIdx] = useTb(0);
  const inputRef = useRefTb(null);

  useEffTb(() => {
    if (open) {
      setQ(""); setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffTb(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  // build groups
  const lower = q.trim().toLowerCase();
  const match = (s) => !lower || s.toLowerCase().includes(lower);
  const pages = ROUTES
    .filter(r => match(r.id) || match(t(r.nameKey)) || match(r.path))
    .slice(0, 8)
    .map(r => ({ type: "page", id: `pg-${r.id}`, icon: r.icon, label: t(r.nameKey), hint: r.path, route: r.id }));
  const actions = COMMANDS_EXTRA.filter(c => match(c.label) || match(c.hint));
  const tenants = lower
    ? TENANT_SUGGESTIONS.filter(t => match(t.name)).map(t => ({
        type: "tenant", id: `tn-${t.id}`, icon: "tenants", label: t.name, hint: `${t.region} · ${t.plan}`, route: "admin-tenants",
      }))
    : [];
  const sessions = lower && /^(sess|s_|[a-f0-9]{2,})/i.test(lower)
    ? SESSION_SUGGESTIONS.filter(s => s.id.toLowerCase().includes(lower)).map(s => ({
        type: "session", id: `ss-${s.id}`, icon: "loop", label: s.id, hint: `${s.agent} · ${s.tenant} · ${s.status}`, route: "loop-debug",
      }))
    : [];

  const groups = [
    { label: t("cmdk.group.actions"),  items: actions },
    { label: t("cmdk.group.pages"),    items: pages },
    { label: t("cmdk.group.tenants"),  items: tenants },
    { label: t("cmdk.group.sessions"), items: sessions },
  ].filter(g => g.items.length > 0);
  const flat = groups.flatMap(g => g.items);

  const goItem = (item) => {
    if (item.route) onNav(item.route);
    onClose();
  };

  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx(i => Math.min(flat.length - 1, i + 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx(i => Math.max(0, i - 1)); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (flat[activeIdx]) goItem(flat[activeIdx]);
    }
  };

  return (
    <div
      data-topbar-overlay
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: "fixed", inset: 0, zIndex: 1000,
        background: "oklch(from var(--bg) l c h / 0.6)",
        backdropFilter: "blur(4px)",
        display: "flex", alignItems: "flex-start", justifyContent: "center",
        paddingTop: "12vh",
      }}>
      <div style={{
        width: 560, maxHeight: "70vh", display: "flex", flexDirection: "column",
        background: "var(--bg-1)", border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius-lg)", boxShadow: "0 24px 60px oklch(0 0 0 / 0.5)",
        overflow: "hidden",
      }}>
        {/* input */}
        <div className="row" style={{ gap: 10, padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
          <Icon name="search" size={15} className="subtle" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => { setQ(e.target.value); setActiveIdx(0); }}
            onKeyDown={onKey}
            placeholder={t("cmdk.placeholder")}
            style={{
              flex: 1, background: "transparent", border: "none", outline: "none",
              color: "var(--fg)", fontSize: 14, fontFamily: "var(--font-sans)",
            }}
          />
          <span className="kbd" style={{ fontSize: 10 }}>ESC</span>
        </div>

        {/* results */}
        <div style={{ overflowY: "auto", padding: 4 }}>
          {flat.length === 0 ? (
            <div className="col" style={{ gap: 6, alignItems: "center", padding: "32px 0", color: "var(--fg-subtle)" }}>
              <Icon name="search" size={20} />
              <div style={{ fontSize: 12.5 }}>{t("cmdk.noResults")}</div>
            </div>
          ) : (
            groups.map(g => (
              <div key={g.label}>
                <div style={{
                  padding: "8px 12px 4px",
                  fontSize: 10, color: "var(--fg-subtle)", textTransform: "uppercase",
                  letterSpacing: "0.06em", fontFamily: "var(--font-mono)",
                }}>{g.label}</div>
                {g.items.map(item => {
                  const idx = flat.indexOf(item);
                  const active = idx === activeIdx;
                  return (
                    <div
                      key={item.id}
                      onMouseEnter={() => setActiveIdx(idx)}
                      onClick={() => goItem(item)}
                      className="row"
                      style={{
                        gap: 10, padding: "8px 12px", borderRadius: 6,
                        background: active ? "var(--bg-hover)" : "transparent",
                        cursor: "pointer", fontSize: 13,
                      }}>
                      <Icon name={item.icon} size={14} className="subtle" />
                      <span style={{ flex: 1 }}>{item.label}</span>
                      <span className="mono subtle" style={{ fontSize: 11 }}>{item.hint}</span>
                      {active && <Icon name="arrow_right" size={11} className="subtle" />}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* footer */}
        <div className="row" style={{
          gap: 14, padding: "8px 14px", borderTop: "1px solid var(--border)",
          fontSize: 10.5, color: "var(--fg-subtle)", fontFamily: "var(--font-mono)",
        }}>
          <span><span className="kbd" style={{ fontSize: 9 }}>↑↓</span> navigate</span>
          <span><span className="kbd" style={{ fontSize: 9 }}>↵</span> open</span>
          <span><span className="kbd" style={{ fontSize: 9 }}>ESC</span> close</span>
          <span style={{ flex: 1 }} />
          <span>{flat.length} results</span>
        </div>
      </div>
    </div>
  );
};

// ─────────────────── Notifications popover ───────────────────

const NOTIFS_SEED = [
  { id: "n1", kind: "hitl",       severity: "critical", title: "P1 escalation awaiting approval",      body: "servicenow_create_ticket from sess_4f88c1a", time: "23m", unread: true,  route: "governance" },
  { id: "n2", kind: "incident",   severity: "high",     title: "p95 latency breach on gpt-4.1",         body: "INC-2451 · 3.2s / 2s threshold for 12m",    time: "1h",  unread: true,  route: "incidents" },
  { id: "n3", kind: "verify",     severity: "medium",   title: "Verification failed twice",             body: "compliance-auditor · LLM-judge rejected",   time: "2h",  unread: true,  route: "verification" },
  { id: "n4", kind: "tripwire",   severity: "high",     title: "PII redaction triggered",               body: "salesforce_query returned 3 redacted records", time: "3h", unread: false, route: "redaction" },
  { id: "n5", kind: "system",     severity: "low",      title: "Cost MTD reached 68% of budget",        body: "$2,847 / $4,200 · projected $3,920",        time: "5h",  unread: false, route: "cost-dashboard" },
  { id: "n6", kind: "system",     severity: "low",      title: "Cache rebuild completed",                body: "tenant_acme kb_search vector index",        time: "8h",  unread: false, route: "cache-manager" },
];

const NOTIF_ICON = {
  hitl: "approval", incident: "warn", verify: "checkcheck", tripwire: "shield", system: "info",
};

const NotificationsPanel = ({ open, onClose, onNav, anchorRef }) => {
  const [filter, setFilter] = useTb("all");
  const [items, setItems] = useTb(NOTIFS_SEED);
  useDismiss(open, onClose, anchorRef);
  if (!open) return null;

  const filtered = filter === "unread" ? items.filter(n => n.unread) : items;
  const unreadCount = items.filter(n => n.unread).length;
  const markAll = () => setItems(items.map(n => ({ ...n, unread: false })));
  const markOne = (id) => setItems(items.map(n => n.id === id ? { ...n, unread: false } : n));

  return (
    <div
      data-topbar-overlay
      style={{
        position: "absolute", top: 50, right: 88, width: 400, maxHeight: "75vh",
        background: "var(--bg-1)", border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius)", boxShadow: "0 12px 32px oklch(0 0 0 / 0.5)",
        display: "flex", flexDirection: "column", zIndex: 999,
      }}>
      {/* head */}
      <div className="row" style={{ gap: 8, padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
        <span style={{ fontSize: 13.5, fontWeight: 600 }}>{t("notif.title")}</span>
        {unreadCount > 0 && <Badge tone="warning">{unreadCount} {t("notif.new")}</Badge>}
        <div className="grow" />
        <button className="btn-ghost-sm" style={{
          fontSize: 11, color: "var(--fg-subtle)", border: "none", background: "transparent", cursor: "pointer",
        }} onClick={markAll}>{t("notif.markAll")}</button>
      </div>

      {/* tabs */}
      <div className="row" style={{ gap: 4, padding: "6px 10px", borderBottom: "1px solid var(--border)" }}>
        {[
          { k: "all",    label: t("notif.tab.all"),    count: items.length },
          { k: "unread", label: t("notif.tab.unread"), count: unreadCount },
        ].map(tab => (
          <button key={tab.k}
            onClick={() => setFilter(tab.k)}
            style={{
              padding: "5px 10px", borderRadius: 5,
              background: filter === tab.k ? "var(--bg-2)" : "transparent",
              border: "none", cursor: "pointer", color: filter === tab.k ? "var(--fg)" : "var(--fg-subtle)",
              fontSize: 11.5, fontWeight: filter === tab.k ? 500 : 400,
            }}>
            {tab.label} <span className="mono subtle" style={{ marginLeft: 4 }}>{tab.count}</span>
          </button>
        ))}
      </div>

      {/* list */}
      <div style={{ overflowY: "auto", flex: 1 }}>
        {filtered.length === 0 ? (
          <div className="col" style={{ gap: 6, alignItems: "center", padding: "32px 0", color: "var(--fg-subtle)" }}>
            <Icon name="checkcheck" size={20} />
            <div style={{ fontSize: 12 }}>{t("notif.empty")}</div>
          </div>
        ) : (
          filtered.map((n, i) => (
            <div key={n.id}
              onClick={() => { markOne(n.id); if (n.route) onNav(n.route); onClose(); }}
              style={{
                position: "relative",
                display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 10,
                padding: "12px 14px",
                borderBottom: i < filtered.length - 1 ? "1px solid var(--border)" : "none",
                background: n.unread ? "oklch(from var(--primary) l c h / 0.04)" : "transparent",
                cursor: "pointer",
              }}>
              {n.unread && <span style={{
                position: "absolute", left: 4, top: "50%", transform: "translateY(-50%)",
                width: 6, height: 6, borderRadius: "50%", background: "var(--primary)",
              }} />}
              <span style={{
                width: 28, height: 28, borderRadius: 6,
                background: `oklch(from var(${n.severity === "critical" ? "--danger" : n.severity === "high" ? "--warning" : n.severity === "medium" ? "--info" : "--success"}) l c h / 0.14)`,
                color: `var(${n.severity === "critical" ? "--danger" : n.severity === "high" ? "--warning" : n.severity === "medium" ? "--info" : "--success"})`,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <Icon name={NOTIF_ICON[n.kind]} size={14} />
              </span>
              <div className="col" style={{ gap: 3, minWidth: 0 }}>
                <div style={{ fontSize: 12.5, fontWeight: n.unread ? 500 : 400, lineHeight: 1.4 }}>{n.title}</div>
                <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.4 }}>{n.body}</div>
              </div>
              <span className="mono subtle" style={{ fontSize: 10.5, whiteSpace: "nowrap" }}>{n.time}</span>
            </div>
          ))
        )}
      </div>

      {/* foot */}
      <div className="row" style={{
        gap: 8, padding: "8px 14px", borderTop: "1px solid var(--border)",
      }}>
        <button style={{
          flex: 1, fontSize: 11.5, padding: 6,
          background: "transparent", border: "1px solid var(--border)", borderRadius: 5,
          color: "var(--fg-muted)", cursor: "pointer",
        }} onClick={() => { onNav("audit-log"); onClose(); }}>
          {t("notif.viewAll")}
        </button>
        <button style={{
          fontSize: 11.5, padding: "6px 10px",
          background: "transparent", border: "1px solid var(--border)", borderRadius: 5,
          color: "var(--fg-muted)", cursor: "pointer",
        }} onClick={() => { onNav("tenant-settings"); onClose(); }}>
          <Icon name="settings" size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
          {t("notif.prefs")}
        </button>
      </div>
    </div>
  );
};

// ─────────────────── User menu (avatar) ───────────────────

const UserMenu = ({ open, onClose, onNav, anchorRef }) => {
  useDismiss(open, onClose, anchorRef);
  if (!open) return null;

  return (
    <div
      data-topbar-overlay
      style={{
        position: "absolute", top: 50, right: 12, width: 260,
        background: "var(--bg-1)", border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius)", boxShadow: "0 12px 32px oklch(0 0 0 / 0.5)",
        zIndex: 999, padding: 4,
      }}>
      {/* identity card */}
      <div className="row" style={{
        gap: 10, padding: "10px 12px", borderRadius: 5,
        background: "var(--bg-2)", marginBottom: 4,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
          color: "white", fontSize: 13, fontWeight: 600,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>JL</div>
        <div className="col grow" style={{ gap: 2, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Jamie Liu</div>
          <div className="mono subtle" style={{ fontSize: 10.5 }}>jamie@acme.com</div>
        </div>
      </div>

      {/* tenant switch */}
      <div style={{ padding: "6px 12px 4px", fontSize: 10, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: "var(--font-mono)" }}>
        {t("usermenu.switchTenant")}
      </div>
      {[
        { id: "t1", name: "acme-prod",  region: "ap-east-1",      active: true },
        { id: "t2", name: "globex-eu",  region: "eu-west-1",      active: false },
        { id: "t3", name: "initech-jp", region: "ap-northeast-1", active: false },
      ].map(tn => (
        <div key={tn.id} className="row" style={{
          gap: 8, padding: "7px 10px", borderRadius: 5, cursor: "pointer",
          background: tn.active ? "oklch(from var(--primary) l c h / 0.10)" : "transparent",
        }} onClick={onClose}>
          <div style={{
            width: 22, height: 22, borderRadius: 4,
            background: tn.active ? "var(--primary)" : "var(--bg-3)",
            color: tn.active ? "white" : "var(--fg-muted)",
            fontSize: 10, fontWeight: 600,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>{tn.name[0].toUpperCase()}</div>
          <div className="col grow" style={{ gap: 1 }}>
            <span style={{ fontSize: 12 }}>{tn.name}</span>
            <span className="mono subtle" style={{ fontSize: 10 }}>{tn.region}</span>
          </div>
          {tn.active && <Icon name="check" size={11} style={{ color: "var(--primary)" }} />}
        </div>
      ))}

      <div className="hr" style={{ margin: "4px 0" }} />

      {/* nav items */}
      {[
        { icon: "user",     label: t("usermenu.profile"),     route: "profile" },
        { icon: "keys",     label: t("usermenu.mfa"),         route: "mfa" },
        { icon: "settings", label: t("usermenu.preferences"), route: "tenant-settings" },
        { icon: "help",     label: t("usermenu.help"),        route: "devui",     external: true },
      ].map(it => (
        <div key={it.label} className="row" style={{
          gap: 10, padding: "7px 10px", borderRadius: 5, cursor: "pointer",
          fontSize: 12.5,
        }}
          onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-hover)"}
          onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          onClick={() => { onNav(it.route); onClose(); }}>
          <Icon name={it.icon} size={13} className="subtle" />
          <span style={{ flex: 1 }}>{it.label}</span>
          {it.external && <Icon name="arrow_right" size={10} className="subtle" />}
        </div>
      ))}

      <div className="hr" style={{ margin: "4px 0" }} />

      {/* role / shortcuts */}
      <div className="row" style={{ padding: "6px 12px", gap: 6, justifyContent: "space-between", fontSize: 11 }}>
        <span className="muted">{t("usermenu.role")}</span>
        <Badge tone="primary">operator</Badge>
      </div>
      <div className="row" style={{ padding: "6px 12px", gap: 6, justifyContent: "space-between", fontSize: 11 }}>
        <span className="muted">{t("usermenu.region")}</span>
        <span className="mono subtle">ap-east-1</span>
      </div>

      <div className="hr" style={{ margin: "4px 0" }} />

      {/* logout */}
      <div className="row" style={{
        gap: 10, padding: "8px 10px", borderRadius: 5, cursor: "pointer",
        color: "var(--danger)", fontSize: 12.5,
      }}
        onMouseEnter={(e) => e.currentTarget.style.background = "oklch(from var(--danger) l c h / 0.08)"}
        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
        onClick={() => { location.hash = "auth-login"; onClose(); }}>
        <Icon name="x" size={13} />
        <span style={{ flex: 1 }}>{t("usermenu.logout")}</span>
        <span className="mono subtle" style={{ fontSize: 10, color: "var(--fg-subtle)" }}>⇧⌘Q</span>
      </div>
    </div>
  );
};

Object.assign(window, { CommandPalette, NotificationsPanel, UserMenu });
