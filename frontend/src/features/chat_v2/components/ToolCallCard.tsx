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
 * Created: 2026-04-30 (Sprint 50.2 Day 4.2)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration bg-card→bg-bg-1; bg-muted→bg-bg-2; text-muted-foreground→text-fg-muted for new shell mockup consistency
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 4.2)
 *
 * Related:
 *   - ../types.ts (ToolCallEntry)
 *   - MessageList.tsx (parent renderer)
 *   - frontend/STYLE.md §4 Code / JSON display
 */

import { useState } from "react";

import { cn } from "../../../lib/utils";
import type { ToolCallEntry } from "../types";

type Props = {
  entry: ToolCallEntry;
};

function statusBadge(entry: ToolCallEntry): { label: string; cls: string } {
  if (entry.result === undefined) return { label: "running", cls: "bg-primary" };
  if (entry.isError) return { label: "error", cls: "bg-danger" };
  return { label: "done", cls: "bg-success" };
}

export default function ToolCallCard({ entry }: Props): JSX.Element {
  const [open, setOpen] = useState(true);
  const status = statusBadge(entry);

  return (
    <div className="overflow-hidden rounded-md border border-border bg-bg-1 font-mono text-[13px]">
      <div
        className="flex cursor-pointer select-none items-center gap-2.5 border-b border-border bg-bg-2 px-3 py-2"
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
        <span className="text-sm">🔧</span>
        <span className="font-semibold text-foreground">{entry.toolName}</span>
        {typeof entry.durationMs === "number" && (
          <span className="text-[11px] text-fg-muted">
            {entry.durationMs.toFixed(1)} ms
          </span>
        )}
        <span
          className={cn(
            "ml-auto rounded px-2 py-0.5 text-[11px] uppercase tracking-wide text-white",
            status.cls,
          )}
        >
          {status.label}
        </span>
        <span className="text-[11px] text-fg-muted">{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div className="px-3.5 py-2.5">
          <div className="mb-1 text-[11px] text-fg-muted">Arguments</div>
          <pre className="m-0 whitespace-pre-wrap break-words rounded border border-border bg-bg-2 px-2 py-1.5">
            {JSON.stringify(entry.args, null, 2)}
          </pre>
          {entry.result !== undefined && (
            <>
              <div className="mb-1 mt-2 text-[11px] text-fg-muted">
                {entry.isError ? "Error" : "Result"}
              </div>
              <pre className="m-0 whitespace-pre-wrap break-words rounded border border-border bg-bg-2 px-2 py-1.5">
                {entry.result}
              </pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
