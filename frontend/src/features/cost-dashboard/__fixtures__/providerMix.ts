/**
 * File: frontend/src/features/cost-dashboard/__fixtures__/providerMix.ts
 * Purpose: 4-provider mix fixture for /cost-dashboard ProviderMixCard (Sprint 57.24 US-C3).
 * Category: Frontend / cost-dashboard / fixtures
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C3
 *
 * Description:
 *   Mirrors mockup reference/design-mockups/page-admin.jsx:297-301 inline
 *   array. Provider identity is REDACTED in operator views per LLM-neutrality
 *   constraint (V2 §約束 3: LLM Provider Neutrality — adapter layer hides
 *   provider-specific identity from agent_harness + operator UI).
 *
 *   Cross-provider aggregation backend API pending Phase 58+
 *   AD-Cost-Dashboard-Backend-Extensions.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C3)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C3)
 */

export interface ProviderMixRow {
  label: string; // redacted alias e.g. "provider-A"
  tokens: string; // "8.1M" pre-formatted
  cost: number; // dollars
  pct: number; // 0-100
  toneColor: string; // raw CSS for BarTrack tone
  toneClass: string; // Tailwind class for label dot
}

export const PROVIDER_MIX_FIXTURE: ProviderMixRow[] = [
  { label: "provider-A", tokens: "8.1M", cost: 1620, pct: 57, toneColor: "var(--primary)", toneClass: "bg-primary" },
  { label: "provider-B", tokens: "4.4M", cost: 884, pct: 31, toneColor: "var(--thinking)", toneClass: "bg-thinking" },
  { label: "provider-C", tokens: "1.3M", cost: 260, pct: 9, toneColor: "var(--tool)", toneClass: "bg-tool" },
  { label: "self-hosted", tokens: "0.4M", cost: 83, pct: 3, toneColor: "var(--memory)", toneClass: "bg-memory" },
];
