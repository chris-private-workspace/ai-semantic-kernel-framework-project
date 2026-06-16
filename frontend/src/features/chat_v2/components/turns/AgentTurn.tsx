/**
 * File: frontend/src/features/chat_v2/components/turns/AgentTurn.tsx
 * Purpose: Renders agent-role Turn — verbatim mockup re-point of L178-197.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with timeline rail + primary-tinted marker + head row
 *   (agent name + turn # badge + stop_reason badge + duration + at +
 *   optional "awaiting approval" indicator when waiting=true) + body
 *   renders Block sequence via BlockRender dispatcher. Source: mockup
 *   reference/design-mockups/page-chat.jsx L178-197; styles
 *   styles-mockup.css L742-771 (.turn / .turn-rail / .turn-marker
 *   primary-variant / .turn-head / .turn-body) + L507-535 (.badge,
 *   .badge.primary) + L649 (.live-dot).
 *
 *   Sprint 57.30 Day 3: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.turn[data-role="agent"]` (CSS owns marker primary
 *   tint) / `.turn-head` / `.badge`+`.badge.primary` / `.turn-body` classes.
 *   The "awaiting approval" indicator + flex wrappers use the same row +
 *   inline-style approach as the mockup (page-chat.jsx L188-191) so the
 *   warning live-dot pulsing matches.
 *
 *   Honest-surface (2026-06-06): the role label shows a neutral "agent" rather
 *   than the misleading fixture persona "incident-responder" (which rendered on
 *   every real run regardless of the actual model). A real per-session agent name
 *   will derive from active session metadata when /api/v1/sessions ships
 *   (AD-ChatV2-SessionList-Backend).
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-06-16: Sprint 57.130 — head renders terminated danger badge (LoopTerminated surface)
 *   - 2026-06-06: chat-v2 honest surface — role label "incident-responder"→"agent" (drop misleading fixture persona on real runs) (CHANGE-054)
 *   - 2026-05-23: Sprint 57.30 Day 3 §D1 — verbatim re-point Tailwind → mockup .turn/.turn-head/.badge/.badge.primary/.turn-body + .row inline-style for awaiting-approval
 *   - 2026-05-17: Initial extract from mockup L178-197 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L178-197 (source JSX)
 *   - frontend/src/styles-mockup.css L742-771 (.turn / .turn-rail / .turn-marker / .turn-head / .turn-body)
 *   - frontend/src/styles-mockup.css L507-535 (.badge + .badge.primary)
 *   - frontend/src/styles-mockup.css L649 (.live-dot pulsing)
 *   - ../../types.ts (AgentTurn type)
 *   - ../blocks/Block.tsx (BlockRender dispatcher — Day 2 §2.2)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L188-191
   uses inline-style on .row + live-dot warning override + warning-tinted mono label. */

import type { AgentTurn as AgentTurnType } from "../../types";
import { BlockRender } from "../blocks/Block";

export function AgentTurn({ turn }: { turn: AgentTurnType }): JSX.Element {
  const turnNum = turn.id.replace(/^t_?/, "");
  return (
    <div className="turn" data-role="agent">
      <div className="turn-rail" />
      <div className="turn-marker" />
      <div className="turn-head">
        <span className="role">agent</span>
        <span className="badge primary">turn {turnNum}</span>
        {turn.stopReason && <span className="badge">stop: {turn.stopReason}</span>}
        {turn.durationMs !== null && (
          <span className="mono subtle">· {(turn.durationMs / 1000).toFixed(2)}s</span>
        )}
        <span className="mono subtle">· {turn.at}</span>
        {turn.waiting && (
          <span className="row" style={{ gap: 5, marginLeft: 6 }}>
            <span className="live-dot" style={{ background: "var(--warning)" }} />
            <span className="mono" style={{ fontSize: 11, color: "var(--warning)" }}>
              awaiting approval
            </span>
          </span>
        )}
        {turn.terminated && (
          <span className="badge danger">terminated · {turn.terminated.reason}</span>
        )}
      </div>
      <div className="turn-body">
        {turn.blocks.map((b, i) => (
          <BlockRender key={i} block={b} />
        ))}
      </div>
    </div>
  );
}
