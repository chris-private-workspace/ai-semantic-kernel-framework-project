/**
 * File: frontend/tests/unit/cost-dashboard/ProviderMixCard.test.tsx
 * Purpose: Vitest spec for <ProviderMixCard> (Sprint 57.24 Day 2 US-C3).
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C3
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C3)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProviderMixCard } from "@/features/cost-dashboard/components/ProviderMixCard";

describe("<ProviderMixCard>", () => {
  it("renders all 4 fixture provider rows with BarTrack", () => {
    render(<ProviderMixCard />);
    expect(screen.getByTestId("provider-mix-card")).toBeInTheDocument();
    expect(screen.getAllByTestId("bar-track")).toHaveLength(4);
  });

  it("renders provider redacted labels (provider-A / B / C / self-hosted)", () => {
    render(<ProviderMixCard />);
    expect(screen.getByText("provider-A")).toBeInTheDocument();
    expect(screen.getByText("provider-B")).toBeInTheDocument();
    expect(screen.getByText("provider-C")).toBeInTheDocument();
    expect(screen.getByText("self-hosted")).toBeInTheDocument();
  });

  it("renders title + admin-only subtitle", () => {
    render(<ProviderMixCard />);
    expect(screen.getByText("Provider mix")).toBeInTheDocument();
    expect(screen.getByText(/Admin-only/i)).toBeInTheDocument();
  });

  it("renders LLM-neutrality redaction notice (mockup-faithful copy)", () => {
    render(<ProviderMixCard />);
    const notice = screen.getByTestId("provider-llm-neutrality-notice");
    expect(notice).toBeInTheDocument();
    expect(notice).toHaveTextContent(/redacted/i);
    expect(notice).toHaveTextContent(/LLM-neutrality/i);
  });

  it("renders BackendGapBanner declaring cross-provider API gap (AP-2 honesty)", () => {
    render(<ProviderMixCard />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/cross-provider/i);
  });
});
