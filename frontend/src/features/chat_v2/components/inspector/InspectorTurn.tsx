/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx
 * Purpose: Right-rail Inspector "Turn" tab — populated KV pairs + block sequence from active agent turn.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.21 Day 4 §4.1 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Mockup L392-417. Picks the most-recent AgentTurn from chatStore.turns and
 *   renders Inspector metadata:
 *     - Header: "Turn N · stop_reason" (font-mono uppercase)
 *     - KV pairs: stop_reason / duration / tokens.in / tokens.out /
 *                 tokens.thinking / cost / trace_id / span_id
 *       (placeholders "—" when SSE doesn't carry the metadata; trace_id /
 *        span_id Phase-2 Cat 12 wire-up via AD-Cat12-SSE-Trace-Id-Phase2)
 *     - Block sequence: dot + colored type label + descriptive text per block
 *     - 2 action buttons: Open audit entry / Open in Loop Debug (placeholder
 *       wires; Phase-2 hooks deferred)
 *
 *   Pure read; no side effects. Empty state when no agent turn yet.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L392-417 (InspectorTurn) + L419-432 (KV + EventLine)
 *   - ../../store/chatStore.ts (turns selector)
 *   - ../../types.ts (AgentTurn + Block)
 *   - ./ChatInspector.tsx (tab consumer)
 */

import { Activity, ScrollText } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useChatStore } from "../../store/chatStore";
import type { AgentTurn, Block } from "../../types";

function KV({ k, v, mono = false }: { k: string; v: ReactNode; mono?: boolean }): JSX.Element {
  return (
    <div className="flex items-center justify-between text-[12px]">
      <span className="text-fg-muted">{k}</span>
      <span className={cn(mono && "font-mono tabular-nums text-fg")}>{v}</span>
    </div>
  );
}

const BLOCK_TONE: Record<Block["type"], { dot: string; text: string }> = {
  thinking: { dot: "bg-thinking", text: "text-thinking" },
  tool: { dot: "bg-tool", text: "text-tool" },
  verification: { dot: "bg-success", text: "text-success" },
  subagent_fork: { dot: "bg-info", text: "text-info" },
};

function describeBlock(block: Block): string {
  switch (block.type) {
    case "thinking": {
      const trimmed = block.text.trim();
      if (trimmed.length === 0) return "—";
      return trimmed.length > 36 ? `${trimmed.slice(0, 36)}…` : trimmed;
    }
    case "tool":
      return `${block.name} · ${block.status === "pending" ? "pending" : `${block.durationMs ?? 0}ms`}`;
    case "verification":
      return block.ok ? `claim verified · ${block.verifier}` : `claim failed · ${block.verifier}`;
    case "subagent_fork":
      return `spawned ${block.agents.length} subagent${block.agents.length === 1 ? "" : "s"}`;
  }
}

function EventLine({ block }: { block: Block }): JSX.Element {
  const tone = BLOCK_TONE[block.type];
  return (
    <div className="flex items-center gap-1.5 py-0.5 font-mono text-[11px]">
      <span aria-hidden="true" className={cn("inline-block h-1.5 w-1.5 rounded-full", tone.dot)} />
      <span className={cn("min-w-[78px]", tone.text)}>{block.type}</span>
      <span className="text-fg-subtle">{describeBlock(block)}</span>
    </div>
  );
}

export function InspectorTurn(): JSX.Element {
  const turns = useChatStore((s) => s.turns);
  const lastAgent = [...turns].reverse().find((t): t is AgentTurn => t.role === "agent");

  if (!lastAgent) {
    return (
      <div
        data-testid="inspector-turn-empty"
        className="px-4 py-3 text-[12px] text-fg-muted"
      >
        <div className="font-mono text-[11.5px] uppercase tracking-wider text-fg-subtle">No active turn</div>
        <p className="mt-2 leading-relaxed">Send a message to populate Inspector with turn metadata.</p>
      </div>
    );
  }

  const turnNumber = turns.filter((t) => t.role === "agent").indexOf(lastAgent) + 1;
  const durationLabel = lastAgent.durationMs != null ? `${(lastAgent.durationMs / 1000).toFixed(2)}s` : "—";
  const stopReason = lastAgent.stopReason ?? "—";

  return (
    <div data-testid="inspector-turn" className="flex flex-col gap-2 px-4 py-3">
      <div className="font-mono text-[11.5px] uppercase tracking-wider text-fg-subtle">
        Turn {turnNumber} · {stopReason}
      </div>

      <div className="flex flex-col gap-2 text-[12px]">
        <KV
          k="stop_reason"
          v={
            <Badge variant="outline" className="border-border bg-bg-2 px-1.5 py-0 text-[10px] text-fg-muted">
              {stopReason}
            </Badge>
          }
        />
        <KV k="duration" v={durationLabel} mono />
        <KV k="tokens.in" v={lastAgent.tokensIn != null ? lastAgent.tokensIn.toLocaleString() : "—"} mono />
        <KV k="tokens.out" v={lastAgent.tokensOut != null ? lastAgent.tokensOut.toLocaleString() : "—"} mono />
        <KV
          k="tokens.thinking"
          v={lastAgent.tokensThinking != null ? lastAgent.tokensThinking.toLocaleString() : "—"}
          mono
        />
        <KV k="cost" v={lastAgent.costUsd != null ? `$${lastAgent.costUsd.toFixed(4)}` : "—"} mono />
        <KV k="trace_id" v={lastAgent.traceId ?? "—"} mono />
        <KV k="span_id" v={lastAgent.spanId ?? "—"} mono />
      </div>

      <hr className="my-2 border-t border-border" />

      <div className="font-mono text-[11px] uppercase tracking-wider text-fg-subtle">Block sequence</div>
      <div className="flex flex-col gap-0.5">
        {lastAgent.blocks.length === 0 && (
          <span className="font-mono text-[11px] text-fg-subtle">no blocks yet</span>
        )}
        {lastAgent.blocks.map((b, i) => (
          <EventLine key={i} block={b} />
        ))}
      </div>

      <hr className="my-2 border-t border-border" />

      <Button variant="outline" size="sm" className="h-7 justify-start gap-1 text-xs">
        <ScrollText className="h-3 w-3" aria-hidden="true" />
        Open audit entry
      </Button>
      <Button variant="ghost" size="sm" className="h-7 justify-start gap-1 text-xs">
        <Activity className="h-3 w-3" aria-hidden="true" />
        Open in Loop Debug
      </Button>
    </div>
  );
}

export default InspectorTurn;
