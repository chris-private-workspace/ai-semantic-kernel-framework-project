/**
 * File: frontend/src/features/subagents/types.ts
 * Purpose: TypeScript contracts for Cat 11 subagents registry endpoint (GET /api/v1/subagents).
 * Category: Frontend / subagents / types
 * Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)
 *
 * Description:
 *   Mirrors backend `SubagentSpecItem` + `SubagentsResponse` Pydantic models in
 *   backend/src/api/v1/subagents.py (Sprint 57.78). The endpoint serves the
 *   tenant's AgentSpec catalog (registry view) from `agent_catalog`; usage
 *   metrics (calls_24h / p95_latency / ...) have no runtime data source and are
 *   reported in `gapped` (honest gap, not fabricated — AP-4). The prior
 *   invocations shape (`Subagent`/`SubagentsPage` with not_implemented_reason)
 *   is removed (AD-Subagent-RealList-Phase58 closed).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.78 — invocations shape → SubagentSpec/SubagentsResponse registry (AD-Subagent-RealList)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - backend/src/api/v1/subagents.py (Pydantic models)
 *   - ./services/subagentsService.ts (HTTP client)
 *   - ./hooks/useSubagents.ts (TanStack consumer)
 */

export type SubagentMode = "fork" | "as_tool" | "teammate" | "handoff";

/** One AgentSpec registry row (durable spec fields from agent_catalog). */
export interface SubagentSpec {
  key: string;
  name: string;
  model: string | null;
  allowed_modes: SubagentMode[];
  status: string;
  system_prompt: string;
  budget: Record<string, unknown> | null;
  tools: string[];
}

export interface SubagentsResponse {
  items: SubagentSpec[];
  /** Usage metrics with no runtime data source (honest gap, not fabricated). */
  gapped: string[];
}
