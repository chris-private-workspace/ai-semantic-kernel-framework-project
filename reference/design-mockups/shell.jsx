/* global React, Icon, Button, Badge, t */

// Aligned to repo's routes.config.ts paths + ids, but grouped with richer 6-category nav
// matching what we already iterated on (operations / business / governance / observability / resources / admin).
const ROUTES = [
  // === Operations (daily operator workflows) ===
  { id: "overview",         path: "/overview",         nameKey: "nav.overview",      icon: "dashboard",   category: "operations", active: true, proposed: true },
  { id: "chat-v2",          path: "/chat-v2",          nameKey: "nav.chatV2",        icon: "chat",        category: "operations", active: true },
  { id: "orchestrator",     path: "/orchestrator",     nameKey: "nav.orchestrator",  icon: "sparkles",    category: "operations", active: true, proposed: true },
  { id: "subagents",        path: "/subagents",        nameKey: "nav.subagents",     icon: "fork",        category: "operations", active: true, proposed: true },
  { id: "loop-debug",       path: "/loop-debug",       nameKey: "nav.loopDebug",     icon: "loop",        category: "operations", active: true },
  { id: "memory",           path: "/memory",           nameKey: "nav.memory",        icon: "memory",      category: "operations", active: true },
  { id: "state-inspector",  path: "/state-inspector",  nameKey: "nav.stateInspector", icon: "db",         category: "operations", active: true, proposed: true },
  { id: "compaction",       path: "/compaction",       nameKey: "nav.compaction",    icon: "sparkles",    category: "operations", active: true, proposed: true },
  { id: "jit-retrieval",    path: "/jit-retrieval",    nameKey: "nav.jitRetrieval",  icon: "search",      category: "operations", active: true, proposed: true },
  { id: "subagent-tree",    path: "/subagent-tree",    nameKey: "nav.subagentTree",  icon: "fork",        category: "operations", active: true, proposed: true },
  // === Business (5 IPA domains) ===
  { id: "incidents",        path: "/incidents",        nameKey: "nav.incidents",     icon: "warn",        category: "business",    active: true, proposed: true },
  // === Governance (HITL + audit + verification + redaction) ===
  { id: "governance",       path: "/governance",       nameKey: "nav.governance",    icon: "approval",    category: "governance", active: true },
  { id: "audit-log",        path: "/audit-log",        nameKey: "nav.auditLog",      icon: "audit",       category: "governance", active: false, designed: true },
  { id: "verification",     path: "/verification",     nameKey: "nav.verification",  icon: "checkcheck",  category: "governance", active: true },
  { id: "redaction",        path: "/redaction",        nameKey: "nav.redaction",     icon: "shield",      category: "governance", active: true, proposed: true },
  { id: "error-policy",     path: "/error-policy",     nameKey: "nav.errorPolicy",   icon: "warn",        category: "governance", active: true, proposed: true },
  // === Observability (Cat 12 dashboards) ===
  { id: "sla-dashboard",    path: "/sla-dashboard",    nameKey: "nav.slaDashboard",  icon: "sla",         category: "observability", active: true },
  { id: "cost-dashboard",   path: "/cost-dashboard",   nameKey: "nav.costDashboard", icon: "cost",        category: "observability", active: true },
  { id: "cache-manager",    path: "/cache-manager",    nameKey: "nav.cacheManager",  icon: "db",          category: "observability", active: true, proposed: true },
  { id: "sse",              path: "/sse",              nameKey: "nav.sseInspector",  icon: "log",         category: "observability", active: true, proposed: true },
  { id: "devui",            path: "/devui",            nameKey: "nav.devui",         icon: "code",        category: "observability", active: true, proposed: true },
  // === Resources (tools + flags) ===
  { id: "models",           path: "/models",           nameKey: "nav.models",        icon: "sparkles",    category: "resources", active: true, proposed: true },
  { id: "tools",            path: "/tools",            nameKey: "nav.tools",         icon: "tool",        category: "resources", active: true, proposed: true },
  { id: "feature-flags",    path: "/feature-flags",    nameKey: "nav.featureFlags",  icon: "toggle",      category: "resources", active: false, designed: true },
  // === Admin (tenant + identity + pricing) ===
  { id: "admin-tenants",    path: "/admin-tenants",    nameKey: "nav.tenants",       icon: "tenants",     category: "admin", active: true },
  { id: "tenant-onboarding", path: "/admin/tenant-onboarding", nameKey: "nav.tenantOnboarding", icon: "sparkles", category: "admin", active: true, proposed: true },
  { id: "tenant-settings",  path: "/tenant-settings",  nameKey: "nav.tenantSettings",icon: "settings",    category: "admin", active: true },
  { id: "pricing",          path: "/admin/pricing",    nameKey: "nav.pricing",       icon: "cost",        category: "admin", active: true, proposed: true },
  { id: "rbac",             path: "/rbac",             nameKey: "nav.rbac",          icon: "shield",      category: "admin", active: true, proposed: true },
  { id: "profile",          path: "/profile",          nameKey: "nav.userProfile",   icon: "user",        category: "admin", active: false },
  { id: "mfa",              path: "/mfa",              nameKey: "nav.mfaSettings",   icon: "keys",        category: "admin", active: false },
];

const CATEGORY_ORDER = ["operations", "business", "governance", "observability", "resources", "admin"];

const Sidebar = ({ route, onNav }) => (
  <aside className="sidebar">
    <div className="sidebar-head">
      <div className="brand-mark" />
      <div className="brand-text">
        <div className="brand-name">{t("shell.brand")}</div>
        <div className="brand-sub">{t("shell.brandSub")}</div>
      </div>
    </div>

    <div className="tenant-switcher">
      <div className="tenant-avatar">A</div>
      <div className="tenant-text grow" style={{ minWidth: 0 }}>
        <div className="tenant-name">acme-prod</div>
        <div className="tenant-meta">tenant_01h9a2 · Pro</div>
      </div>
      <Icon name="chevron_down" size={13} />
    </div>

    <nav className="nav" aria-label={t("shell.primaryNavigation")}>
      {CATEGORY_ORDER.map(category => {
        const entries = ROUTES.filter(r => r.category === category);
        if (entries.length === 0) return null;
        const proposedCount = entries.filter(r => r.proposed).length;
        return (
          <React.Fragment key={category}>
            <div className="nav-section">
              <span>{t(`nav.category.${category}`)}</span>
              {proposedCount > 0 && <span className="nav-badge" style={{ background: "oklch(from var(--thinking) l c h / 0.16)", color: "var(--thinking)", fontSize: 9 }}>{proposedCount} PROP</span>}
            </div>
            {entries.map(r => <SidebarItem key={r.id} entry={r} active={route === r.id} onNav={onNav} />)}
          </React.Fragment>
        );
      })}
    </nav>

    <div className="sidebar-foot">
      <div className="user-card">
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
          color: "white", fontSize: 11, fontWeight: 600,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>JL</div>
        <div className="grow" style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 500 }}>Jamie Liu</div>
          <div style={{ fontSize: 10.5, color: "var(--fg-subtle)", fontFamily: "var(--font-mono)" }}>operator</div>
        </div>
        <Icon name="dots" size={14} className="subtle" />
      </div>
    </div>
  </aside>
);

const SidebarItem = ({ entry, active, onNav }) => {
  // active=false in registry: NOT navigable UNLESS we have a designed page
  // designed=true: show with "DRAFT" badge, navigable (preview of designed-not-shipped route)
  if (!entry.active && !entry.designed) {
    return (
      <div
        className="nav-item"
        title={t("shell.comingSoon")}
        aria-disabled="true"
        style={{ opacity: 0.55, cursor: "not-allowed" }}
      >
        <Icon name={entry.icon} size={15} className="nav-icon" />
        <span className="nav-label">{t(entry.nameKey)}</span>
        <span className="nav-badge" style={{ fontSize: 9 }}>SOON</span>
      </div>
    );
  }
  return (
    <div
      className="nav-item"
      data-active={active}
      onClick={() => onNav(entry.id)}
      aria-current={active ? "page" : undefined}
      title={entry.designed ? "Designed · not in V2 registry yet" : undefined}
    >
      <Icon name={entry.icon} size={15} className="nav-icon" />
      <span className="nav-label">{t(entry.nameKey)}</span>
      {entry.proposed && <span className="nav-badge" style={{ background: "oklch(from var(--thinking) l c h / 0.16)", color: "var(--thinking)", fontSize: 9 }}>PROP</span>}
      {entry.designed && <span className="nav-badge" style={{ background: "oklch(from var(--warning) l c h / 0.16)", color: "var(--warning)", fontSize: 9 }}>DRAFT</span>}
    </div>
  );
};

// Crumb / title map keyed by route id
const ID_TO_KEY = {
  "overview": "overview",
  "chat-v2": "chatV2", "loop-debug": "loopDebug", "memory": "memory",
  "state-inspector": "stateInspector", "compaction": "compaction",
  "jit-retrieval": "jitRetrieval", "cache-manager": "cacheManager",
  "workflows": "workflows", "subagent-tree": "subagentTree",
  "incidents": "incidents",
  "governance": "governance", "audit-log": "auditLog",
  "verification": "verification", "redaction": "redaction",
  "error-policy": "errorPolicy",
  "sla-dashboard": "slaDashboard", "cost-dashboard": "costDashboard",
  "sse": "sseInspector", "devui": "devui",
  "tools": "tools", "feature-flags": "featureFlags",
  "admin-tenants": "tenants", "tenant-settings": "tenantSettings",
  "tenant-onboarding": "tenantOnboarding", "pricing": "pricing",
  "rbac": "rbac", "profile": "profile", "mfa": "mfa",
  "orchestrator": "orchestrator", "subagents": "subagents",
  "models": "models",
  "domain-patrol": "domain", "domain-correlation": "domain",
  "domain-rca": "domain", "domain-audit": "domain", "domain-incident": "domain",
};
const DOMAIN_PATHS = {
  "domain-patrol": "/incidents/patrol",
  "domain-correlation": "/incidents/correlation",
  "domain-rca": "/incidents/rca",
  "domain-audit": "/incidents/audit",
  "domain-incident": "/incidents/incident",
};
const CRUMBS = {
  ...Object.fromEntries(ROUTES.map(r => [r.id, { path: r.path, titleKey: `page.${ID_TO_KEY[r.id] || r.id}.title` }])),
  ...Object.fromEntries(Object.entries(DOMAIN_PATHS).map(([id, path]) => [id, { path, titleKey: "page.domain.title" }])),
};

const Topbar = ({ route, onNav, onToggleTweaks, onOpenCmdK, onOpenNotifs, onOpenUserMenu, onToggleLocale, onToggleTheme, locale = "en", theme = "dark", notifsAnchorRef, avatarAnchorRef, unreadCount = 3 }) => {
  const c = CRUMBS[route] || {};
  return (
    <header className="topbar">
      <div className="crumb">
        <span className="here">{t(c.titleKey)}</span>
        <span className="route-pill">{c.path}</span>
      </div>
      <span className="tenant-pill"><span className="dot"></span>acme-prod · operator</span>
      <div className="topbar-spacer" />
      <div className="cmdk" role="button" tabIndex={0} onClick={onOpenCmdK} onKeyDown={(e) => { if (e.key === "Enter") onOpenCmdK(); }} style={{ cursor: "pointer" }} title="Open command palette">
        <Icon name="search" size={13} />
        <span className="grow">{t("shell.search")}</span>
        <span className="kbd">⌘K</span>
      </div>
      <button
        onClick={onToggleLocale}
        title={locale === "en" ? "切換到繁體中文" : "Switch to English"}
        aria-label={locale === "en" ? "Switch to Traditional Chinese" : "Switch to English"}
        style={{
          height: 28, minWidth: 28, padding: "0 8px",
          background: "transparent", border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm)", color: "var(--fg-muted)",
          fontSize: 11, fontWeight: 500, fontFamily: "var(--font-mono)",
          letterSpacing: "0.04em", cursor: "pointer",
          display: "inline-flex", alignItems: "center", gap: 4,
        }}>
        <Icon name="globe" size={12} />
        <span>{locale === "en" ? "EN" : "中"}</span>
      </button>
      <Button
        variant="ghost" size="sm"
        icon={theme === "dark" ? "sun" : "moon"}
        onClick={onToggleTheme}
        title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        aria-label="Toggle theme"
      />
      <span style={{ width: 1, height: 18, background: "var(--border)", margin: "0 4px", display: "inline-block" }} aria-hidden="true" />
      <span ref={notifsAnchorRef} style={{ position: "relative" }}>
        <Button variant="ghost" size="sm" icon="bell" aria-label="Notifications" onClick={onOpenNotifs}>
          {unreadCount > 0 && <span style={{
            position: "absolute", top: 3, right: 3,
            minWidth: 14, height: 14, padding: "0 3px", borderRadius: 7,
            background: "var(--warning)", color: "oklch(0.18 0.02 60)",
            fontSize: 9, fontWeight: 700, fontFamily: "var(--font-mono)",
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 0 0 2px var(--bg-1)",
          }}>{unreadCount > 9 ? "9+" : unreadCount}</span>}
        </Button>
      </span>
      <Button variant="ghost" size="sm" icon="sliders" onClick={onToggleTweaks} title="Open Tweaks" />
      <span ref={avatarAnchorRef}>
        <div className="avatar" role="button" tabIndex={0} onClick={onOpenUserMenu} onKeyDown={(e) => { if (e.key === "Enter") onOpenUserMenu(); }} style={{ cursor: "pointer" }} title="Account">JL</div>
      </span>
    </header>
  );
};

Object.assign(window, { Sidebar, Topbar, ROUTES });
