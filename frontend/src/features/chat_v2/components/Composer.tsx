/**
 * File: frontend/src/features/chat_v2/components/Composer.tsx
 * Purpose: Composer visual scaffolding — mockup-aligned UX with 3 disabled coming-soon affordances.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 Day 4 §4.2 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Mockup L316-368 — composer with rich attachment + tool-picker + memory-scope
 *   affordances. This Sprint 57.21 Day 4 ships **visual scaffolding only**:
 *
 *     1. Textarea with mockup placeholder copy
 *     2. 3 disabled coming-soon buttons: Attach / Tools (24) / Memory scope
 *        (each with tooltip pointing to Sprint 57.22+ AD-ChatV2-Composer-
 *        Richness-Phase2)
 *     3. Right-aligned model badge (claude-haiku-4-5) + provider neutral chip
 *     4. Primary Send button (placeholder; not wired)
 *
 *   The chat-v2 page (pages/chat-v2/index.tsx) continues to use `InputBar.tsx`
 *   for production sends — InputBar.tsx ships the proven 5-state pill + send /
 *   cancel + mode toggle + 14 SSE event handling. Composer.tsx is intentionally
 *   **not** consumed by chat-v2/index.tsx this sprint to preserve InputBar's
 *   battle-tested wire (carryover: AD-ChatV2-Composer-Wire-Phase2 — pick
 *   between extract-shared-hook vs proxy-via-composition after the rich
 *   affordances are themselves wired in Sprint 57.22+).
 *
 *   This is an explicit Sprint 57.21 scope-reduction per Day 4 §4.2 plan
 *   "lower-risk option" footer — ship the visual demonstration without
 *   regressing the production send path.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.2) — visual scaffolding; not wired to chat-v2 page
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L316-368 (Composer source)
 *   - ./InputBar.tsx (production send path; unchanged this sprint)
 *   - sprint-57-21-checklist.md §Carryover (AD-ChatV2-Composer-Richness-Phase2 + AD-ChatV2-Composer-Wire-Phase2)
 */

import { Download, FileText, GitFork, Plus, Send } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function Composer(): JSX.Element {
  return (
    <div
      data-testid="composer"
      className="border-t border-border bg-bg-1 px-4 py-3"
    >
      <div className="flex flex-col gap-2 rounded-md border border-border bg-bg-2 p-2.5">
        <textarea
          rows={2}
          disabled
          data-testid="composer-input"
          placeholder='Ask the agent — drag files in, paste images, or type. For example, "Investigate INC-4087 and propose an action plan"'
          className="w-full resize-none rounded border border-transparent bg-transparent px-2 py-1.5 text-[13px] text-fg placeholder:text-fg-subtle focus:border-border focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
        />
        <div className="flex flex-wrap items-center gap-1.5">
          <Button
            disabled
            variant="ghost"
            size="sm"
            data-testid="composer-attach"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
            className="h-7 gap-1 px-2 text-xs"
          >
            <Plus className="h-3 w-3" aria-hidden="true" />
            Attach
          </Button>
          <Button
            disabled
            variant="ghost"
            size="sm"
            data-testid="composer-tools"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
            className="h-7 gap-1 px-2 text-xs"
          >
            <GitFork className="h-3 w-3" aria-hidden="true" />
            Tools (24)
          </Button>
          <Button
            disabled
            variant="ghost"
            size="sm"
            data-testid="composer-memory-scope"
            title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"
            className="h-7 gap-1 px-2 text-xs"
          >
            <FileText className="h-3 w-3" aria-hidden="true" />
            Memory scope
          </Button>

          <div className="flex-1" />

          <Badge variant="outline" className="border-border bg-bg-1 px-1.5 py-0 text-[10px] text-fg-muted">
            claude-haiku-4-5
          </Badge>
          <span className="font-mono text-[10px] text-fg-subtle">neutral</span>
          <Button
            disabled
            size="sm"
            data-testid="composer-send"
            title="Sprint 57.22+ AD-ChatV2-Composer-Wire-Phase2 — production send path remains InputBar.tsx"
            className="h-7 gap-1 px-2 text-xs"
          >
            Send
            <Send className="h-3 w-3" aria-hidden="true" />
          </Button>
        </div>
      </div>
      <div className="mt-1 flex items-center gap-1 pl-1 text-[10.5px] text-fg-subtle">
        <Download className="h-2.5 w-2.5" aria-hidden="true" />
        Drop files anywhere · accepts images / pdf / txt / md / json / yaml / log / csv · max 25MB each
      </div>
    </div>
  );
}

export default Composer;
