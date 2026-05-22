/**
 * File: frontend/src/features/overview/__fixtures__/providers.ts
 * Purpose: Fixture provider traffic-light rows for ProvidersCard.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:61-66`
 *   (PROVIDERS const). The telemetry provider traffic-light API is not yet
 *   wired, so ProvidersCard ships this fixture + a visible <BackendGapBanner>
 *   per AP-2 honesty; the backend wire folds into
 *   AD-Overview-Backend-Extensions-Phase58.
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2) — lift inline PROVIDERS const to fixture
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:61-66 (PROVIDERS canonical)
 *   - frontend/src/features/overview/components/ProvidersCard.tsx (consumer)
 */

export interface Provider {
  name: string;
  state: "green" | "amber" | "red";
  p95: number;
  calls: string;
}

export const PROVIDERS: Provider[] = [
  { name: "claude-haiku-4-5", state: "green", p95: 1.8, calls: "12.4k" },
  { name: "gpt-4.1", state: "amber", p95: 3.2, calls: "8.1k" },
  { name: "gpt-4.1-mini", state: "green", p95: 1.1, calls: "4.7k" },
  { name: "embedding-3-large", state: "green", p95: 0.4, calls: "21.0k" },
];
