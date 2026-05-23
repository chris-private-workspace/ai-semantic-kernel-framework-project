/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-chat.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/Composer.tsx
 * Purpose: Composer visual scaffolding — mockup-aligned UX with 3 disabled coming-soon affordances.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 4 §4.2 → 57.30 Day 2 verbatim re-point
 *
 * Description:
 *   Mockup `page-chat.jsx` L316-368 — verbatim re-point of composer scaffolding.
 *
 *   Mockup CSS classes consumed verbatim (styles-mockup.css):
 *     - .composer (L919-922) — outer wrapper with border-top + bg-1 + padding
 *     - .composer-inner (L924-931) — inset card with border + radius + focus-within ring
 *     - .composer-input (L932-936) — textarea reset
 *     - .composer-tools (L937) — flex bottom action row
 *     - .btn / .btn.ghost / .btn.primary / [data-size="sm"] (L426-446)
 *     - .grow / .subtle / .mono (L613-620)
 *     - .badge (L507-518)
 *     - .provider-neutral (L1092)
 *
 *   Inline-style literal copied byte-for-byte from mockup L362 (drop hint).
 *
 *   Sprint 57.21 Day 4 §4.2 scope-reduction is preserved — this ships
 *   **visual scaffolding only**; the production send path remains in
 *   `InputBar.tsx`. Composer is currently NOT consumed by chat-v2/index.tsx;
 *   carryover AD-ChatV2-Composer-Wire-Phase2 decides extract-shared-hook vs
 *   proxy-via-composition in a later sprint.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.2)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C2 — verbatim re-point to mockup page-chat.jsx L316-368 Composer markup (.composer, .composer-inner, .composer-input, .composer-tools, .btn .ghost / .primary)
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.2) — visual scaffolding; not wired to chat-v2 page
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L316-368 (Composer source)
 *   - frontend/src/styles-mockup.css L919-937 (.composer / .composer-inner / .composer-input / .composer-tools)
 *   - ./InputBar.tsx (production send path; unchanged this sprint)
 *   - sprint-57-21-checklist.md §Carryover (AD-ChatV2-Composer-Richness-Phase2 + AD-ChatV2-Composer-Wire-Phase2)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { Download, FileText, GitFork, Plus, Send } from "lucide-react";

export function Composer(): JSX.Element {
  return (
    <div className="composer" data-testid="composer">
      <div className="composer-inner">
        <textarea
          className="composer-input"
          rows={2}
          disabled
          data-testid="composer-input"
          placeholder='Ask the agent — drag files in, paste images, or type. For example, "Investigate INC-4087 and propose an action plan"'
        />
        <div className="composer-tools">
          <button
            type="button"
            disabled
            className="btn ghost"
            data-size="sm"
            data-testid="composer-attach"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
          >
            <Plus size={12} aria-hidden="true" />
            Attach
          </button>
          <button
            type="button"
            disabled
            className="btn ghost"
            data-size="sm"
            data-testid="composer-tools"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
          >
            <GitFork size={12} aria-hidden="true" />
            Tools (24)
          </button>
          <button
            type="button"
            disabled
            className="btn ghost"
            data-size="sm"
            data-testid="composer-memory-scope"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
          >
            <FileText size={12} aria-hidden="true" />
            Memory scope
          </button>

          <div className="grow" />

          <span className="badge">claude-haiku-4-5</span>
          <span className="provider-neutral">neutral</span>
          <button
            type="button"
            disabled
            className="btn primary"
            data-size="sm"
            data-testid="composer-send"
            title="Sprint 57.22+ AD-ChatV2-Composer-Wire-Phase2 — production send path remains InputBar.tsx"
          >
            Send
            <Send size={12} aria-hidden="true" />
          </button>
        </div>
      </div>
      {/* Mockup L362-365 drop hint — inline-style literal verbatim */}
      <div className="subtle" style={{ fontSize: 10.5, marginTop: 4, paddingLeft: 4 }}>
        <Download
          size={10}
          style={{ verticalAlign: "middle", marginRight: 4 }}
          aria-hidden="true"
        />
        Drop files anywhere · accepts images / pdf / txt / md / json / yaml / log / csv · max 25MB each
      </div>
    </div>
  );
}

export default Composer;
