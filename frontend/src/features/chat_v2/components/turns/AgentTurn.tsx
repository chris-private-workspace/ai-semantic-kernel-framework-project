/**
 * File: frontend/src/features/chat_v2/components/turns/AgentTurn.tsx
 * Purpose: Renders agent-role Turn — Tailwind translation of mockup L178-197.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with timeline rail + primary-tinted marker + head row
 *   (agent name + turn # badge + stop_reason badge + duration + at +
 *   optional "awaiting approval" indicator when waiting=true) + body
 *   renders Block sequence via BlockRender dispatcher. Source: mockup
 *   reference/design-mockups/page-chat.jsx L178-197; styles
 *   reference/design-mockups/styles.css L742-771 + L773-777.
 *
 *   Agent name "incident-responder" is currently a fixture label per
 *   mockup; Sprint 57.22+ AD-ChatV2-SessionList-Backend will derive from
 *   active session metadata when /api/v1/sessions list ships.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L178-197 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L178-197 (source JSX)
 *   - reference/design-mockups/styles.css L742-771 (turn-rail / turn-marker / turn-head)
 *   - ../../types.ts (AgentTurn type)
 *   - ../blocks/Block.tsx (BlockRender dispatcher — Day 2 §2.2)
 */

import type { AgentTurn as AgentTurnType } from "../../types";
import { BlockRender } from "../blocks/Block";

export function AgentTurn({ turn }: { turn: AgentTurnType }): JSX.Element {
  const turnNum = turn.id.replace(/^t_?/, "");
  return (
    <div className="relative border-b border-border bg-bg px-6 py-3.5" data-role="agent">
      <div className="absolute bottom-0 left-[10px] top-0 w-px bg-border" />
      <div className="absolute left-[6px] top-[18px] h-[9px] w-[9px] rounded-full border-2 border-primary bg-primary" />
      <div className="mb-2 flex flex-wrap items-center gap-2 pl-[22px] text-[11px] text-fg-muted">
        <span className="text-xs font-semibold text-fg">incident-responder</span>
        <span className="rounded border border-primary/20 bg-primary/10 px-1.5 py-px font-mono text-[10.5px] text-primary">
          turn {turnNum}
        </span>
        {turn.stopReason && (
          <span className="rounded border border-border bg-bg-2 px-1.5 py-px font-mono text-[10.5px] text-fg-muted">
            stop: {turn.stopReason}
          </span>
        )}
        {turn.durationMs !== null && (
          <span className="font-mono text-fg-subtle">· {(turn.durationMs / 1000).toFixed(2)}s</span>
        )}
        <span className="font-mono text-fg-subtle">· {turn.at}</span>
        {turn.waiting && (
          <span className="ml-1.5 flex items-center gap-1.5">
            <span className="h-[7px] w-[7px] animate-pulse rounded-full bg-warning" />
            <span className="font-mono text-[11px] text-warning">awaiting approval</span>
          </span>
        )}
      </div>
      <div className="flex flex-col gap-1.5 pl-[22px]">
        {turn.blocks.map((b, i) => (
          <BlockRender key={i} block={b} />
        ))}
      </div>
    </div>
  );
}
