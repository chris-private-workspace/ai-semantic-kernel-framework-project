/**
 * File: frontend/src/features/subagents/types.ts
 * Purpose: TypeScript contracts for Cat 11 subagents endpoint (GET /api/v1/subagents).
 * Category: Frontend / subagents / types
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C3
 *
 * Description:
 *   Mirrors backend `SubagentItem` + `SubagentsPage` Pydantic models in
 *   backend/src/api/v1/subagents.py (Sprint 57.19 US-B4).
 *
 *   IMPORTANT: US-B4 backend currently returns empty list + populated
 *   `not_implemented_reason` (subagent invocations not persisted yet —
 *   tracked as AD-Subagent-RealList-Phase58). Frontend renders the
 *   carryover banner from this field when items is empty.
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - backend/src/api/v1/subagents.py (Pydantic models)
 *   - ./services/subagentsService.ts (HTTP client)
 *   - ./hooks/useSubagents.ts (TanStack consumer)
 */

export type SubagentMode = "fork" | "as_tool" | "teammate" | "handoff";

export interface Subagent {
  invocation_id: string;
  mode: SubagentMode;
  parent_session_id: string;
  status: string;
  total_tokens: number;
  started_at_ms: number;
  ended_at_ms: number | null;
}

export interface SubagentsPage {
  items: Subagent[];
  next_cursor: string | null;
  page_size: number;
  not_implemented_reason: string | null;
}
