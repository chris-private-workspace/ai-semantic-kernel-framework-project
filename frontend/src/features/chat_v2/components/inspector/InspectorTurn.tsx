/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx
 * Purpose: Inspector "Turn" tab — verbatim mockup re-point of page-chat.jsx L392-432.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.30 Day 4 §D3 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Mockup L392-417 (InspectorTurn) + L419-432 (KV + EventLine helpers).
 *   Picks the most-recent AgentTurn from chatStore.turns and renders:
 *     - Section header: "Turn N · stop_reason" (font-mono uppercase)
 *     - 8 KV rows: stop_reason / duration / tokens.in/out/thinking /
 *                  cost / trace_id / span_id (placeholder "—" when null)
 *     - .thin-rule divider
 *     - "Block sequence" header + 1 EventLine per block (color dot +
 *       type label + descriptive text)
 *     - .thin-rule divider
 *     - 2 action buttons: "Open audit entry" / "Open in Loop Debug"
 *
 *   Pure read; no side effects. Empty state when no agent turn yet.
 *
 *   Sprint 57.30 Day 4: re-pointed from Tailwind utility translations
 *   (flex flex-col gap-2 / text-fg-muted / border-t border-border /
 *   bg-bg-2 / variant="outline" Button etc.) to verbatim mockup `.col`,
 *   `.spread`, `.thin-rule`, `.mono`, `.tnum`, `.subtle`, `.row` classes
 *   + `.btn outline`/`.btn ghost` button system + inline-style mockup
 *   font-size/family/color literals verbatim per L394 / L405 / L420 /
 *   L427-431. KV + EventLine helpers retained (private to file) per
 *   mockup shape but emit verbatim DOM.
 *
 *   Vitest spec contract preserved (ChatInspector.test.tsx):
 *   - data-testid="inspector-turn" + "inspector-turn-empty"
 *   - Visible text: "Turn N · stop_reason" / KV values / dash "—" / block
 *     type labels ("thinking", "tool")
 *   - "metrics.query · 210ms" describeBlock output preserved
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.1)
 * Last Modified: 2026-06-15
 *
 * Modification History (newest-first):
 *   - 2026-06-15: Sprint 57.120 — +active_skill KV row (⚡ skill; reuse KV, no mockup CSS)
 *   - 2026-05-23: Sprint 57.30 Day 4 §D3 — verbatim re-point Tailwind → mockup .col/.spread/.thin-rule/.mono/.tnum + .btn outline/ghost
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L392-417 (InspectorTurn) + L419-432 (KV + EventLine)
 *   - frontend/src/styles-mockup.css L615+L617+L620+L621 (.spread/.subtle/.mono/.tnum)
 *   - frontend/src/styles-mockup.css L1119 (.thin-rule)
 *   - frontend/src/styles-mockup.css L426-460 (.btn outline/ghost)
 *   - ../../store/chatStore.ts (turns selector)
 *   - ../../types.ts (AgentTurn + Block)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L394
   (section header inline font-size/color/text-transform/font-family), L405 (Block
   sequence sub-header inline), L413+L414 (Button-shaped inline icon), L420+L427-431
   (KV + EventLine inline-style row shape with width / colors). Tokens via var(--*). */

import { Activity, ScrollText } from "lucide-react";
import type { ReactNode } from "react";

import { useChatStore } from "../../store/chatStore";
import type { AgentTurn, Block } from "../../types";

function KV({ k, v, mono = false }: { k: string; v: ReactNode; mono?: boolean }): JSX.Element {
  return (
    <div className="spread" style={{ fontSize: 12 }}>
      <span className="subtle">{k}</span>
      <span className={mono ? "mono tnum" : undefined}>{v}</span>
    </div>
  );
}

const BLOCK_TONE: Record<Block["type"], string> = {
  thinking: "var(--thinking)",
  answer: "var(--primary)",
  tool: "var(--tool)",
  verification: "var(--success)",
  subagent_fork: "var(--info)",
};

function describeBlock(block: Block): string {
  switch (block.type) {
    case "thinking": {
      const trimmed = block.text.trim();
      if (trimmed.length === 0) return "—";
      return trimmed.length > 36 ? `${trimmed.slice(0, 36)}…` : trimmed;
    }
    // Honest-surface (CHANGE-054): the agent's final text answer block.
    case "answer": {
      const trimmed = block.text.trim();
      if (trimmed.length === 0) return "—";
      return trimmed.length > 48 ? `${trimmed.slice(0, 48)}…` : trimmed;
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
    <div
      className="row"
      style={{ gap: 6, padding: "3px 0", fontFamily: "var(--font-mono)", fontSize: 11 }}
    >
      <span
        aria-hidden="true"
        style={{ width: 6, height: 6, borderRadius: "50%", background: tone, display: "inline-block" }}
      />
      <span style={{ color: tone, minWidth: 78 }}>{block.type}</span>
      <span className="subtle">{describeBlock(block)}</span>
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
        style={{ padding: "12px 16px", fontSize: 12, color: "var(--fg-muted)" }}
      >
        <div
          style={{
            fontSize: 11.5,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontFamily: "var(--font-mono)",
          }}
        >
          No active turn
        </div>
        <p style={{ marginTop: 8, lineHeight: 1.55 }}>
          Send a message to populate Inspector with turn metadata.
        </p>
      </div>
    );
  }

  const turnNumber = turns.filter((t) => t.role === "agent").indexOf(lastAgent) + 1;
  const durationLabel = lastAgent.durationMs != null ? `${(lastAgent.durationMs / 1000).toFixed(2)}s` : "—";
  const stopReason = lastAgent.stopReason ?? "—";

  return (
    <div data-testid="inspector-turn" style={{ padding: "12px 16px" }}>
      <div
        style={{
          fontSize: 11.5,
          color: "var(--fg-subtle)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 8,
          fontFamily: "var(--font-mono)",
        }}
      >
        Turn {turnNumber} · {stopReason}
      </div>

      <div className="col" style={{ gap: 8, fontSize: 12 }}>
        <KV
          k="stop_reason"
          v={<span className="badge">{stopReason}</span>}
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
        {/* Sprint 57.120: the force-loaded skill for this turn's loop (carried onto the
            AgentTurn at turn_start). ⚡ matches the 57.116 user-turn chip; "—" when no
            skill. Reuses the KV helper — no new mockup CSS / HEX / oklch. */}
        <KV k="active_skill" v={lastAgent.activeSkill ? `⚡ ${lastAgent.activeSkill}` : "—"} />
        <KV k="trace_id" v={lastAgent.traceId ?? "—"} mono />
        <KV k="span_id" v={lastAgent.spanId ?? "—"} mono />

        <div className="thin-rule" />

        <div
          style={{
            fontSize: 11,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontFamily: "var(--font-mono)",
          }}
        >
          Block sequence
        </div>
        <div className="col" style={{ gap: 3 }}>
          {lastAgent.blocks.length === 0 && (
            <span className="mono subtle" style={{ fontSize: 11 }}>
              no blocks yet
            </span>
          )}
          {lastAgent.blocks.map((b, i) => (
            <EventLine key={i} block={b} />
          ))}
        </div>

        <div className="thin-rule" />

        <button type="button" className="btn outline" data-size="sm">
          <ScrollText size={12} aria-hidden="true" />
          Open audit entry
        </button>
        <button type="button" className="btn ghost" data-size="sm">
          <Activity size={12} aria-hidden="true" />
          Open in Loop Debug
        </button>
      </div>
    </div>
  );
}

export default InspectorTurn;
