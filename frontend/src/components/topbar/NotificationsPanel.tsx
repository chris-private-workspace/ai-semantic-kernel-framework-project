/**
 * File: frontend/src/components/topbar/NotificationsPanel.tsx
 * Purpose: Bell-icon dropdown panel — 6 fixture notifications (HITL/incident/verify/tripwire/system) + tabs + mark-read.
 * Category: Frontend / components / topbar (Cat 12 cross-cutting UX surface)
 * Scope: Phase 57 / Sprint 57.19 Day 5 / US-D2
 *
 * Description:
 *   Verbatim re-point of `reference/design-mockups/topbar-overlays.jsx` NotificationsPanel.
 *   Panel shell, header row, tab buttons, notification rows, and footer buttons now use
 *   verbatim inline-style literals from the mockup. Component-logic layer unchanged:
 *   all props/signatures, mark-read logic, navigate(), role="dialog", role="tablist",
 *   role="tab", role="button", tabIndex, onKeyDown Enter/Space on rows, data-testid.
 *
 *   Backend wiring: deferred to Sprint 57.20+ (Cat 12 notifications feed via SSE / poll endpoint).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 5 / US-D2)
 * Last Modified: 2026-05-22
 *
 * Modification History:
 *   - 2026-05-22: Sprint 57.29 US-B4 — verbatim re-point panel shell to mockup topbar-overlays.jsx literals
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 5 / US-D2) — mockup port with 6 fixture items
 *
 * Related:
 *   - reference/design-mockups/topbar-overlays.jsx §NotificationsPanel (canonical visual source)
 *   - reference/design-mockups/styles.css / frontend/src/styles-mockup.css
 *   - frontend/src/components/AppShellV2.tsx (bell button trigger + anchored panel)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup topbar-overlays.jsx visual-layer literals (panel shell, head/tab/item/foot rows, icon badge, unread dot) copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import { type CSSProperties, type FC, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Icon } from "@/components/mockup-ui";

// ─── Verbatim mockup topbar-overlays.jsx inline-style literals ───────────────

// Panel container
const PANEL_STYLE: CSSProperties = {
  position: "absolute", top: 50, right: 88, width: 400, maxHeight: "75vh",
  background: "var(--bg-1)", border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius)", boxShadow: "0 12px 32px oklch(0 0 0 / 0.5)",
  display: "flex", flexDirection: "column", zIndex: 999,
};

// Head row
const HEAD_ROW_STYLE: CSSProperties = {
  gap: 8, padding: "12px 14px", borderBottom: "1px solid var(--border)",
};

const HEAD_TITLE_STYLE: CSSProperties = { fontSize: 13.5, fontWeight: 600 };

const MARK_ALL_BTN_STYLE: CSSProperties = {
  fontSize: 11, color: "var(--fg-subtle)", border: "none", background: "transparent", cursor: "pointer",
};

// Tabs row
const TABS_ROW_STYLE: CSSProperties = {
  gap: 4, padding: "6px 10px", borderBottom: "1px solid var(--border)",
};

const tabBtnStyle = (active: boolean): CSSProperties => ({
  padding: "5px 10px", borderRadius: 5,
  background: active ? "var(--bg-2)" : "transparent",
  border: "none", cursor: "pointer",
  color: active ? "var(--fg)" : "var(--fg-subtle)",
  fontSize: 11.5, fontWeight: active ? 500 : 400,
});

// List scroll area
const LIST_STYLE: CSSProperties = { overflowY: "auto", flex: 1 };

// Empty state
const EMPTY_STYLE: CSSProperties = {
  gap: 6, alignItems: "center", padding: "32px 0", color: "var(--fg-subtle)",
};

// Notification row
const notifRowStyle = (unread: boolean, isLast: boolean): CSSProperties => ({
  position: "relative",
  display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 10,
  padding: "12px 14px",
  borderBottom: isLast ? "none" : "1px solid var(--border)",
  background: unread ? "oklch(from var(--primary) l c h / 0.04)" : "transparent",
  cursor: "pointer",
});

// Unread dot
const UNREAD_DOT_STYLE: CSSProperties = {
  position: "absolute", left: 4, top: "50%", transform: "translateY(-50%)",
  width: 6, height: 6, borderRadius: "50%", background: "var(--primary)",
};

// Severity icon badge
type Severity = "critical" | "high" | "medium" | "low";
const sevIconStyle = (sev: Severity): CSSProperties => ({
  width: 28, height: 28, borderRadius: 6,
  background: `oklch(from var(${sev === "critical" ? "--danger" : sev === "high" ? "--warning" : sev === "medium" ? "--info" : "--success"}) l c h / 0.14)`,
  color: `var(${sev === "critical" ? "--danger" : sev === "high" ? "--warning" : sev === "medium" ? "--info" : "--success"})`,
  display: "flex", alignItems: "center", justifyContent: "center",
});

// Col text wrapper
const TEXT_COL_STYLE: CSSProperties = { gap: 3, minWidth: 0 };

const titleStyle = (unread: boolean): CSSProperties => ({
  fontSize: 12.5, fontWeight: unread ? 500 : 400, lineHeight: 1.4,
});

const BODY_STYLE: CSSProperties = { fontSize: 11.5, lineHeight: 1.4 };

// Time label
const TIME_STYLE: CSSProperties = { fontSize: 10.5, whiteSpace: "nowrap" };

// Footer
const FOOT_STYLE: CSSProperties = {
  gap: 8, padding: "8px 14px", borderTop: "1px solid var(--border)",
};

const VIEW_ALL_BTN_STYLE: CSSProperties = {
  flex: 1, fontSize: 11.5, padding: 6,
  background: "transparent", border: "1px solid var(--border)", borderRadius: 5,
  color: "var(--fg-muted)", cursor: "pointer",
};

const PREFS_BTN_STYLE: CSSProperties = {
  fontSize: 11.5, padding: "6px 10px",
  background: "transparent", border: "1px solid var(--border)", borderRadius: 5,
  color: "var(--fg-muted)", cursor: "pointer",
};

// ─────────────────────────────────────────────────────────────────────────────

type NotificationKind = "hitl" | "incident" | "verify" | "tripwire" | "system";

const KIND_ICON: Record<NotificationKind, string> = {
  hitl: "approval", incident: "warn", verify: "checkcheck", tripwire: "shield", system: "info",
};

interface NotificationItem {
  id: string;
  kind: NotificationKind;
  severity: Severity;
  titleKey: string;
  bodyKey: string;
  time: string;
  unread: boolean;
  routePath?: string;
}

const NOTIFICATIONS_SEED: NotificationItem[] = [
  { id: "n1", kind: "hitl",     severity: "critical", titleKey: "topbar.notifications.items.n1Title", bodyKey: "topbar.notifications.items.n1Body", time: "23m", unread: true,  routePath: "/governance" },
  { id: "n2", kind: "incident", severity: "high",     titleKey: "topbar.notifications.items.n2Title", bodyKey: "topbar.notifications.items.n2Body", time: "1h",  unread: true,  routePath: "/incidents" },
  { id: "n3", kind: "verify",   severity: "medium",   titleKey: "topbar.notifications.items.n3Title", bodyKey: "topbar.notifications.items.n3Body", time: "2h",  unread: true,  routePath: "/verification" },
  { id: "n4", kind: "tripwire", severity: "high",     titleKey: "topbar.notifications.items.n4Title", bodyKey: "topbar.notifications.items.n4Body", time: "3h",  unread: false, routePath: "/redaction" },
  { id: "n5", kind: "system",   severity: "low",      titleKey: "topbar.notifications.items.n5Title", bodyKey: "topbar.notifications.items.n5Body", time: "5h",  unread: false, routePath: "/cost-dashboard" },
  { id: "n6", kind: "system",   severity: "low",      titleKey: "topbar.notifications.items.n6Title", bodyKey: "topbar.notifications.items.n6Body", time: "8h",  unread: false, routePath: "/cache-manager" },
];

interface NotificationsPanelProps {
  open: boolean;
  onClose: () => void;
}

export const NotificationsPanel: FC<NotificationsPanelProps> = ({ open, onClose }) => {
  const { t } = useTranslation("common");
  const navigate = useNavigate();
  const [items, setItems] = useState(NOTIFICATIONS_SEED);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  if (!open) return null;

  const visibleItems = filter === "unread" ? items.filter((n) => n.unread) : items;
  const unreadCount = items.filter((n) => n.unread).length;

  const markAll = (): void => setItems(items.map((n) => ({ ...n, unread: false })));
  const markOne = (id: string): void => setItems(items.map((n) => (n.id === id ? { ...n, unread: false } : n)));
  const onItemClick = (n: NotificationItem): void => {
    markOne(n.id);
    if (n.routePath) navigate(n.routePath);
    onClose();
  };

  return (
    <div
      data-testid="notifications-panel"
      data-topbar-overlay
      style={PANEL_STYLE}
      role="dialog"
      aria-label={t("topbar.notifications.title")}
    >
      {/* Head */}
      <div className="row" style={HEAD_ROW_STYLE}>
        <span style={HEAD_TITLE_STYLE}>{t("topbar.notifications.title")}</span>
        {unreadCount > 0 && (
          <span className="badge warning pill">
            {unreadCount} {t("topbar.notifications.new")}
          </span>
        )}
        <div className="grow" />
        <button
          type="button"
          style={MARK_ALL_BTN_STYLE}
          onClick={markAll}
        >
          {t("topbar.notifications.markAll")}
        </button>
      </div>

      {/* Tabs */}
      <div className="row" style={TABS_ROW_STYLE} role="tablist">
        {(["all", "unread"] as const).map((k) => (
          <button
            key={k}
            type="button"
            role="tab"
            aria-selected={filter === k}
            onClick={() => setFilter(k)}
            style={tabBtnStyle(filter === k)}
          >
            {t(`topbar.notifications.tab.${k}`)}{" "}
            <span className="mono subtle" style={{ marginLeft: 4 }}>
              {k === "all" ? items.length : unreadCount}
            </span>
          </button>
        ))}
      </div>

      {/* List */}
      <div style={LIST_STYLE}>
        {visibleItems.length === 0 ? (
          <div className="col" style={EMPTY_STYLE}>
            <Icon name="checkcheck" size={20} />
            <div style={{ fontSize: 12 }}>{t("topbar.notifications.empty")}</div>
          </div>
        ) : (
          visibleItems.map((n, i) => (
            <div
              key={n.id}
              onClick={() => onItemClick(n)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onItemClick(n);
                }
              }}
              style={notifRowStyle(n.unread, i === visibleItems.length - 1)}
            >
              {n.unread && <span style={UNREAD_DOT_STYLE} />}
              <span style={sevIconStyle(n.severity)}>
                <Icon name={KIND_ICON[n.kind] as Parameters<typeof Icon>[0]["name"]} size={14} />
              </span>
              <div className="col" style={TEXT_COL_STYLE}>
                <div style={titleStyle(n.unread)}>{t(n.titleKey)}</div>
                <div className="muted" style={BODY_STYLE}>{t(n.bodyKey)}</div>
              </div>
              <span className="mono subtle" style={TIME_STYLE}>{n.time}</span>
            </div>
          ))
        )}
      </div>

      {/* Foot */}
      <div className="row" style={FOOT_STYLE}>
        <button
          type="button"
          style={VIEW_ALL_BTN_STYLE}
          onClick={() => { navigate("/audit-log"); onClose(); }}
        >
          {t("topbar.notifications.viewAll")}
        </button>
        <button
          type="button"
          style={PREFS_BTN_STYLE}
          onClick={() => { navigate("/tenant-settings"); onClose(); }}
        >
          <Icon name="settings" size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
          {t("topbar.notifications.prefs")}
        </button>
      </div>
    </div>
  );
};
