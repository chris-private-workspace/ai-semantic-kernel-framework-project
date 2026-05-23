/**
 * File: frontend/src/features/chat_v2/components/blocks/Block.tsx
 * Purpose: Discriminated-union dispatcher for Block types within AgentTurn body.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Exhaustive switch on block.type → matching block component (thinking
 *   / tool / verification / subagent_fork). Mirrors mockup
 *   reference/design-mockups/page-chat.jsx Block component L199-267 but
 *   split across 4 separate per-type files. tsc enforces exhaustive
 *   handling via the _never path; missing future block types surface as
 *   compile errors.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 3 §D2 — no markup change (pure dispatcher); per-block re-point shipped in ThinkingBlock / ToolBlock
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 2 §2.2)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L199-267 (Block switch source)
 *   - ../../types.ts (Block discriminated union)
 *   - ./ThinkingBlock.tsx / ToolBlock.tsx / VerificationBlock.tsx / SubagentForkBlock.tsx
 */

import type { Block } from "../../types";
import { SubagentForkBlock } from "./SubagentForkBlock";
import { ThinkingBlock } from "./ThinkingBlock";
import { ToolBlock } from "./ToolBlock";
import { VerificationBlock } from "./VerificationBlock";

export function BlockRender({ block }: { block: Block }): JSX.Element | null {
  switch (block.type) {
    case "thinking":
      return <ThinkingBlock block={block} />;
    case "tool":
      return <ToolBlock block={block} />;
    case "verification":
      return <VerificationBlock block={block} />;
    case "subagent_fork":
      return <SubagentForkBlock block={block} />;
    default: {
      const _exhaustive: never = block;
      void _exhaustive;
      return null;
    }
  }
}
