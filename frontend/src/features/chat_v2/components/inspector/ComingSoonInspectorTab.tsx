/**
 * File: frontend/src/features/chat_v2/components/inspector/ComingSoonInspectorTab.tsx
 * Purpose: Empty-state placeholder for Inspector tabs deferred to Sprint 57.22+ Phase-2 ADs.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.21 Day 4 §4.1 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Trace / Memory / Tree tabs render this placeholder until their respective
 *   backend feeds land in Sprint 57.22+. Each instance names the carryover AD
 *   so the operator + reviewer can locate the work item:
 *     - AD-ChatV2-Inspector-Trace-Phase2     (Cat 12 OTel spans waterfall)
 *     - AD-ChatV2-Inspector-Memory-Phase2    (Cat 3 memory ops feed)
 *     - AD-ChatV2-Inspector-SubagentTree-Phase2 (Cat 11 live tree)
 *
 *   Visual: mockup file hint + 1-2 line description + carryover AD link copy.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L434-466 (Trace), L468-487 (Memory), L489-531 (Tree)
 *   - ./ChatInspector.tsx (tab dispatcher)
 *   - sprint-57-21-checklist.md §4.1 + §Carryover
 */

type Props = {
  name: "Trace" | "Memory" | "Tree";
  mockupSection: string;
  carryoverAd: string;
  hint: string;
};

export function ComingSoonInspectorTab({ name, mockupSection, carryoverAd, hint }: Props): JSX.Element {
  return (
    <div
      data-testid={`inspector-tab-coming-soon-${name.toLowerCase()}`}
      className="flex flex-col gap-2 px-4 py-3 text-[12px] text-fg-muted"
    >
      <div className="font-mono text-[11.5px] uppercase tracking-wider text-fg-subtle">
        {name} · coming soon
      </div>
      <p className="leading-relaxed">{hint}</p>
      <div className="rounded border border-border bg-bg-2 p-2.5 text-[11px] leading-snug">
        <div>
          Mockup design: <span className="font-mono text-fg-muted">page-chat.jsx {mockupSection}</span>
        </div>
        <div className="mt-1">
          Backend wire: <span className="font-mono text-fg">{carryoverAd}</span> (Sprint 57.22+)
        </div>
      </div>
    </div>
  );
}

export default ComingSoonInspectorTab;
