/**
 * File: frontend/src/components/mockup-ui.tsx
 * Purpose: Verbatim-TSX port of the mockup `ui.jsx` primitives — emit mockup CSS class strings directly.
 * Category: Frontend / components
 * Scope: Phase 57 / Sprint 57.29 US-B1 (verbatim re-point — shared primitive set)
 *
 * Description:
 *   1:1 port of `reference/design-mockups/ui.jsx` primitives into typed ESM TSX.
 *   These primitives deliberately consume the mockup CSS class names from
 *   `styles-mockup.css` verbatim (`btn`, `badge`, `card`, `stat`, `sev-dot`, …) —
 *   NO Tailwind utility re-translation, NO shadcn primitives. They are the shared
 *   verbatim primitive set consumed by the re-pointed shell, the topbar overlays,
 *   and the `/overview` page (Sprint 57.29 Phase-2 per-page re-point epic).
 *
 *   The visual layer (class names + inline-style literals) is copied verbatim from
 *   the mockup; the component-logic layer (UMD `window` globals) is rewritten to
 *   typed ESM props. Reference worked example: the PoC `pages/overview-poc/components.tsx`.
 *
 * Key Components:
 *   - Icon: inline-SVG icon set ported from mockup `ui.jsx` `Icon`
 *   - Button: `btn ${variant}` + `data-size` + `.ico`
 *   - Badge: `badge ${tone} ${dot ? "dot" : ""} ${pill ? "pill" : ""}`
 *   - Card: `card` → `card-head` / `card-title` / `card-sub` / `card-body ${bodyClass}` / `card-foot`
 *   - Stat: `stat` / `stat-label` / `stat-value tnum` / `stat-delta` / `stat-spark`
 *   - Spark: inline-SVG sparkline (`<path>` polyline) ported from mockup `ui.jsx` `Spark`
 *   - SevDot: `sev-dot sev-${level}`
 *   - RiskBadge: `Badge tone="risk-${level}"` + inline `sev-dot`
 *
 * Created: 2026-05-22 (Sprint 57.29 Day 1 US-B1)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 Day 3 — add Spark SVG primitive (Day-1 port omitted it)
 *   - 2026-05-22: Initial creation (Sprint 57.29 Day 1) — verbatim port of ui.jsx primitives
 *
 * Related:
 *   - reference/design-mockups/ui.jsx (authoritative visual source)
 *   - frontend/src/styles-mockup.css (Layer 2 — byte-identical mockup stylesheet, globally imported)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim-CSS method)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup ui.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, ReactNode } from "react";

// ───────────────── Icon ─────────────────

export type IconName =
  | "dashboard"
  | "chat"
  | "loop"
  | "memory"
  | "approval"
  | "audit"
  | "cost"
  | "sla"
  | "tenants"
  | "settings"
  | "search"
  | "chevron_right"
  | "chevron_down"
  | "chevron_up"
  | "plus"
  | "filter"
  | "bell"
  | "help"
  | "arrow_up"
  | "arrow_down"
  | "arrow_right"
  | "dots"
  | "copy"
  | "check"
  | "x"
  | "bolt"
  | "git"
  | "refresh"
  | "code"
  | "db"
  | "globe"
  | "clock"
  | "eye"
  | "play"
  | "pause"
  | "stop"
  | "send"
  | "sliders"
  | "thinking"
  | "tool"
  | "branch"
  | "shield"
  | "warn"
  | "fork"
  | "log"
  | "chain"
  | "sparkles"
  | "download"
  | "moon"
  | "sun"
  | "panel"
  | "user"
  | "toggle"
  | "checkcheck"
  | "keys"
  | "info";

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}

// Verbatim copy of the mockup `ui.jsx` icon path set.
const ICON_PATHS: Record<IconName, ReactNode> = {
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </>
  ),
  chat: (
    <path d="M21 11.5a8.4 8.4 0 0 1-1 4 8.5 8.5 0 0 1-7.5 4.5 8.4 8.4 0 0 1-4-1L3 21l2-5.5a8.4 8.4 0 0 1-1-4A8.5 8.5 0 0 1 21 11.5Z" />
  ),
  loop: (
    <>
      <path d="M21 12a9 9 0 1 1-3-6.7" />
      <polyline points="21 4 21 9 16 9" />
    </>
  ),
  memory: (
    <path d="M12 3a4 4 0 0 1 4 4v1h-2a3 3 0 0 0 0 6h2v3a4 4 0 0 1-4 4 4 4 0 0 1-4-4v-3h2a3 3 0 0 0 0-6H8V7a4 4 0 0 1 4-4Z" />
  ),
  approval: (
    <>
      <path d="M9 11.5 11 13.5 15 9" />
      <path d="M12 3 4 7v6c0 5 4 8 8 9 4-1 8-4 8-9V7l-8-4Z" />
    </>
  ),
  audit: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
      <path d="m17 17 1 1 2-2" stroke="var(--success)" />
    </>
  ),
  cost: <path d="M12 3v18M17 7H9.5a3 3 0 0 0 0 6H14a3 3 0 0 1 0 6H6" />,
  sla: (
    <>
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 6 12 12 16 14" />
    </>
  ),
  tenants: (
    <>
      <path d="M3 21h18" />
      <path d="M6 21V8l6-4 6 4v13" />
      <path d="M9 21v-6h6v6" />
      <rect x="8" y="9" width="2" height="2" />
      <rect x="14" y="9" width="2" height="2" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.7l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.7-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.7.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.7 1.6 1.6 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.7.3h.1a1.6 1.6 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.7-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.7v.1a1.6 1.6 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  chevron_right: <polyline points="9 6 15 12 9 18" />,
  chevron_down: <polyline points="6 9 12 15 18 9" />,
  chevron_up: <polyline points="6 15 12 9 18 15" />,
  plus: <path d="M12 5v14M5 12h14" />,
  filter: <path d="M4 5h16l-6 7v7l-4-2v-5L4 5Z" />,
  bell: (
    <>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9Z" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </>
  ),
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9a2.5 2.5 0 1 1 4 2c-.8.5-1.5 1-1.5 2" />
      <circle cx="12" cy="17" r=".5" fill="currentColor" />
    </>
  ),
  arrow_up: <path d="M12 19V5M5 12l7-7 7 7" />,
  arrow_down: <path d="M12 5v14M19 12l-7 7-7-7" />,
  arrow_right: <path d="M5 12h14M13 5l7 7-7 7" />,
  dots: (
    <>
      <circle cx="5" cy="12" r="1.4" fill="currentColor" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" />
      <circle cx="19" cy="12" r="1.4" fill="currentColor" />
    </>
  ),
  copy: (
    <>
      <rect x="9" y="9" width="11" height="11" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
    </>
  ),
  check: <polyline points="4 12 10 18 20 6" />,
  x: <path d="M6 6l12 12M18 6 6 18" />,
  bolt: <polygon points="13 2 4 14 11 14 11 22 20 10 13 10 13 2" />,
  git: (
    <>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="18" r="2.5" />
      <circle cx="6" cy="18" r="2.5" />
      <path d="M6 8.5v7" />
      <path d="M8.5 6h6a3 3 0 0 1 3 3v6.5" />
    </>
  ),
  refresh: (
    <>
      <polyline points="3 12 3 6 9 6" />
      <path d="M3.5 6.5A9 9 0 1 1 3 12" />
    </>
  ),
  code: (
    <>
      <polyline points="8 7 3 12 8 17" />
      <polyline points="16 7 21 12 16 17" />
      <line x1="14" y1="5" x2="10" y2="19" />
    </>
  ),
  db: (
    <>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
      <path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c2.5 3 4 6.5 4 9s-1.5 6-4 9c-2.5-3-4-6.5-4-9s1.5-6 4-9Z" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 15 14" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  play: <polygon points="6 4 20 12 6 20" />,
  pause: (
    <>
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </>
  ),
  stop: <rect x="5" y="5" width="14" height="14" rx="2" />,
  send: <path d="M3 11 21 3l-8 18-2-8-8-2Z" />,
  sliders: (
    <>
      <line x1="4" y1="6" x2="12" y2="6" />
      <line x1="16" y1="6" x2="20" y2="6" />
      <line x1="4" y1="12" x2="8" y2="12" />
      <line x1="12" y1="12" x2="20" y2="12" />
      <line x1="4" y1="18" x2="16" y2="18" />
      <circle cx="14" cy="6" r="2" />
      <circle cx="10" cy="12" r="2" />
      <circle cx="18" cy="18" r="2" />
    </>
  ),
  thinking: (
    <>
      <path d="M12 4a5 5 0 0 0-5 5c0 1.6 1 3 2 4l.5 2h5l.5-2c1-1 2-2.4 2-4a5 5 0 0 0-5-5Z" />
      <path d="M10 19h4M11 22h2" />
    </>
  ),
  tool: (
    <path d="m14.7 6.3-2.4 2.4 1.4 1.4 2.4-2.4a3 3 0 1 1-4.2 4.2L4 18.5a2 2 0 0 0 0 2.8 2 2 0 0 0 2.8 0L13.7 14a3 3 0 1 1 4.2-4.2l-3.2-3.5Z" />
  ),
  branch: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="6" cy="19" r="2" />
      <circle cx="18" cy="12" r="2" />
      <path d="M6 7v10" />
      <path d="M6 9a6 6 0 0 0 6 6 6 6 0 0 1 4-3" />
    </>
  ),
  shield: <path d="M12 3 4 7v6c0 5 4 8 8 9 4-1 8-4 8-9V7l-8-4Z" />,
  warn: (
    <>
      <path d="M12 4 2 21h20L12 4Z" />
      <line x1="12" y1="10" x2="12" y2="15" />
      <circle cx="12" cy="18" r=".7" fill="currentColor" />
    </>
  ),
  fork: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="18" cy="5" r="2" />
      <circle cx="12" cy="19" r="2" />
      <path d="M6 7v3a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7" />
      <path d="M12 12v5" />
    </>
  ),
  log: (
    <>
      <path d="M5 4h11l3 3v13H5z" />
      <line x1="8" y1="10" x2="16" y2="10" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="16" x2="13" y2="16" />
    </>
  ),
  chain: (
    <>
      <path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
      <path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
    </>
  ),
  sparkles: (
    <path d="M9 3v4M7 5h4M17 13v4M15 15h4M14 4l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3Z" />
  ),
  download: (
    <>
      <path d="M12 3v12M6 11l6 6 6-6" />
      <path d="M5 21h14" />
    </>
  ),
  moon: <path d="M20 14a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="4" />
      <line x1="12" y1="20" x2="12" y2="22" />
      <line x1="4" y1="12" x2="2" y2="12" />
      <line x1="22" y1="12" x2="20" y2="12" />
      <line x1="5" y1="5" x2="6.5" y2="6.5" />
      <line x1="17.5" y1="17.5" x2="19" y2="19" />
      <line x1="5" y1="19" x2="6.5" y2="17.5" />
      <line x1="17.5" y1="6.5" x2="19" y2="5" />
    </>
  ),
  panel: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <line x1="9" y1="4" x2="9" y2="20" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-7 8-7s8 3 8 7" />
    </>
  ),
  toggle: (
    <>
      <rect x="2" y="7" width="20" height="10" rx="5" />
      <circle cx="8" cy="12" r="3" fill="currentColor" />
    </>
  ),
  checkcheck: (
    <>
      <polyline points="3 12 7 16 13 10" />
      <polyline points="11 16 15 20 21 12" />
    </>
  ),
  keys: (
    <>
      <circle cx="8" cy="15" r="4" />
      <path d="m10.85 12.15 7.85-7.85" />
      <path d="m18 7-3 3" />
      <path d="m15 4 3 3" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <line x1="12" y1="11" x2="12" y2="16" />
      <circle cx="12" cy="8" r=".7" fill="currentColor" />
    </>
  ),
};

export function Icon({ name, size = 16, className = "", style }: IconProps): JSX.Element {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
    >
      {ICON_PATHS[name] ?? <circle cx="12" cy="12" r="3" />}
    </svg>
  );
}

// ───────────────── Button ─────────────────

type ButtonVariant = "outline" | "primary" | "ghost";

interface ButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  variant?: ButtonVariant;
  size?: "sm";
  icon?: IconName;
  iconRight?: IconName;
  children?: ReactNode;
}

export function Button({
  variant = "outline",
  size,
  icon,
  iconRight,
  children,
  ...rest
}: ButtonProps): JSX.Element {
  return (
    <button className={`btn ${variant}`} data-size={size} {...rest}>
      {icon && <Icon name={icon} size={14} className="ico" />}
      {children}
      {iconRight && <Icon name={iconRight} size={14} className="ico" />}
    </button>
  );
}

// ───────────────── Badge ─────────────────

interface BadgeProps {
  tone?: string;
  dot?: boolean;
  pill?: boolean;
  children: ReactNode;
}

export function Badge({ tone = "", dot, pill, children }: BadgeProps): JSX.Element {
  return (
    <span className={`badge ${tone} ${dot ? "dot" : ""} ${pill ? "pill" : ""}`}>
      {children}
    </span>
  );
}

// ───────────────── Card ─────────────────

interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  foot?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClass?: string;
}

export function Card({
  title,
  subtitle,
  actions,
  foot,
  children,
  className = "",
  bodyClass = "",
}: CardProps): JSX.Element {
  return (
    <div className={`card ${className}`}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <div className="card-title">{title}</div>}
            {subtitle && <div className="card-sub">{subtitle}</div>}
          </div>
          {actions}
        </div>
      )}
      <div className={`card-body ${bodyClass}`}>{children}</div>
      {foot && <div className="card-foot">{foot}</div>}
    </div>
  );
}

// ───────────────── Stat ─────────────────

interface StatProps {
  label: ReactNode;
  value: ReactNode;
  unit?: ReactNode;
  delta?: ReactNode;
  deltaDir?: "up" | "down";
  spark?: ReactNode;
}

export function Stat({
  label,
  value,
  unit,
  delta,
  deltaDir = "up",
  spark,
}: StatProps): JSX.Element {
  return (
    <div className="stat">
      <div className="stat-label">
        <span>{label}</span>
        {delta && (
          <span className={`stat-delta ${deltaDir}`}>
            <Icon name={deltaDir === "up" ? "arrow_up" : "arrow_down"} size={10} />
            {delta}
          </span>
        )}
      </div>
      <div className="stat-value tnum">
        {value}
        {unit && <span className="unit">{unit}</span>}
      </div>
      {spark && <div className="stat-spark">{spark}</div>}
    </div>
  );
}

// ───────────────── Spark ─────────────────

interface SparkProps {
  points: number[];
  width?: number;
  height?: number;
  tone?: string;
}

/** Inline-SVG sparkline — verbatim port of mockup `ui.jsx` `Spark`. */
export function Spark({
  points,
  width = 90,
  height = 26,
  tone = "var(--primary)",
}: SparkProps): JSX.Element {
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);
  const d = points
    .map((v, i) => {
      const x = (i * step).toFixed(1);
      const y = (height - ((v - min) / range) * height).toFixed(1);
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={width} height={height}>
      <path d={d} fill="none" stroke={tone} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// ───────────────── Severity primitives ─────────────────

export type RiskLevel = "low" | "medium" | "high" | "critical";

/** Severity dot — `sev-dot sev-${level}`. */
export function SevDot({ level }: { level: RiskLevel }): JSX.Element {
  return <span className={`sev-dot sev-${level}`} title={level} />;
}

/** Risk badge — `Badge tone="risk-${level}"` + inline `sev-dot`. */
export function RiskBadge({ level }: { level: RiskLevel }): JSX.Element {
  return (
    <Badge tone={`risk-${level}`}>
      <span className={`sev-dot sev-${level}`} style={{ width: 5, height: 5 }} />
      {level}
    </Badge>
  );
}
