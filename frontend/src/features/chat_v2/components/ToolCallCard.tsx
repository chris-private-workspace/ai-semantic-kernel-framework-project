/**
 * File: frontend/src/features/chat_v2/components/ToolCallCard.tsx
 * Purpose: Renders a single tool call request + result pair (collapsible).
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 4.2)
 *
 * Description:
 *   Displays one ToolCallEntry: tool name, args (JSON pretty), status badge
 *   (running / done / error), and result body. Click header to expand /
 *   collapse. While result is undefined the badge reads "running"; once
 *   tool_call_result arrives status flips to "done" or "error".
 *
 *   Inline styles only (Tailwind retrofitted in Phase 53.4 per Day 3.6 note).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 4.2)
 * Last Modified: 2026-04-30
 *
 * Modification History:
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.2)
 *
 * Related:
 *   - ../types.ts (ToolCallEntry)
 *   - MessageList.tsx (parent renderer)
 */

import { useState, type CSSProperties } from "react";
import type { ToolCallEntry } from "../types";

type Props = {
  entry: ToolCallEntry;
};

const styles: Record<string, CSSProperties> = {
  card: {
    border: "1px solid #d8dde7",
    borderRadius: 6,
    background: "#fff",
    fontSize: 13,
    fontFamily:
      "'JetBrains Mono', Menlo, Consolas, 'Liberation Mono', monospace",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
    padding: "0.5rem 0.75rem",
    cursor: "pointer",
    background: "#f4f6fa",
    borderBottom: "1px solid #d8dde7",
    userSelect: "none",
  },
  toolIcon: { fontSize: 14 },
  toolName: { fontWeight: 600, color: "#3b4252" },
  body: { padding: "0.6rem 0.85rem" },
  label: { color: "#7c8696", fontSize: 11, marginBottom: 4 },
  pre: {
    margin: 0,
    padding: "0.4rem 0.55rem",
    background: "#f8fafc",
    border: "1px solid #ebeef4",
    borderRadius: 4,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
};

const badge = (color: string): CSSProperties => ({
  marginLeft: "auto",
  padding: "0.1rem 0.55rem",
  borderRadius: 4,
  background: color,
  color: "#fff",
  fontSize: 11,
  textTransform: "uppercase",
  letterSpacing: 0.5,
});

function statusColor(entry: ToolCallEntry): { label: string; color: string } {
  if (entry.result === undefined) return { label: "running", color: "#5a78c8" };
  if (entry.isError) return { label: "error", color: "#c43d3d" };
  return { label: "done", color: "#2f9c59" };
}

export default function ToolCallCard({ entry }: Props): JSX.Element {
  const [open, setOpen] = useState(true);
  const status = statusColor(entry);

  return (
    <div style={styles.card}>
      <div
        style={styles.header}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((v) => !v);
          }
        }}
        role="button"
        tabIndex={0}
        aria-expanded={open}
      >
        <span style={styles.toolIcon}>🔧</span>
        <span style={styles.toolName}>{entry.toolName}</span>
        {typeof entry.durationMs === "number" && (
          <span style={{ color: "#7c8696", fontSize: 11 }}>
            {entry.durationMs.toFixed(1)} ms
          </span>
        )}
        <span style={badge(status.color)}>{status.label}</span>
        <span style={{ color: "#7c8696", fontSize: 11 }}>
          {open ? "▾" : "▸"}
        </span>
      </div>
      {open && (
        <div style={styles.body}>
          <div style={styles.label}>Arguments</div>
          <pre style={styles.pre}>{JSON.stringify(entry.args, null, 2)}</pre>
          {entry.result !== undefined && (
            <>
              <div style={{ ...styles.label, marginTop: 8 }}>
                {entry.isError ? "Error" : "Result"}
              </div>
              <pre style={styles.pre}>{entry.result}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
