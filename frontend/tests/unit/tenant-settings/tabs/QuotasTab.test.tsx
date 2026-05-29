/**
 * File: frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx
 * Purpose: Vitest coverage for QuotasTab — useQuotas/useRateLimits + Sprint 57.56/57.57 edit modes.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.49 Day 1 + Sprint 57.56 Track B + Sprint 57.57 Track B
 *
 * Modification History (newest-first):
 *   - 2026-05-29: Sprint 57.62 US-3 — +Recent alerts Card tests + existing 2 Cards scope guard
 *   - 2026-05-28: Sprint 57.58 Track D — +Live usage Card tests + Rate limits Card scope guard
 *   - 2026-05-27: Sprint 57.57 Track B — +Rate limits edit mode tests + Usage Card scope guard
 *   - 2026-05-27: Sprint 57.56 Track B — +edit-mode tests + banner copy + scope guard assertion
 *   - 2026-05-26: Sprint 57.49 — rewrite to mock useQuotas + useRateLimits hooks
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/tenant-settings/hooks/useQuotas", () => ({
  useQuotas: vi.fn(),
  QUOTAS_QUERY_KEY_BASE: ["tenant-settings", "quotas"],
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimits", () => ({
  useRateLimits: vi.fn(),
  RATE_LIMITS_QUERY_KEY_BASE: ["tenant-settings", "rate-limits"],
}));
vi.mock("@/features/tenant-settings/hooks/useQuotasSave", () => ({
  useQuotasSave: vi.fn(),
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimitsSave", () => ({
  useRateLimitsSave: vi.fn(),
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimitsUsage", () => ({
  useRateLimitsUsage: vi.fn(),
  RATE_LIMITS_USAGE_QUERY_KEY_BASE: ["tenant-settings", "rate-limits-usage"],
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimitsAlerts", () => ({
  useRateLimitsAlerts: vi.fn(),
  RATE_LIMITS_ALERTS_QUERY_KEY_BASE: ["tenant-settings", "rate-limits-alerts"],
}));

import { QuotasTab } from "@/features/tenant-settings/components/tabs/QuotasTab";
import { useQuotas } from "@/features/tenant-settings/hooks/useQuotas";
import { useQuotasSave } from "@/features/tenant-settings/hooks/useQuotasSave";
import { useRateLimits } from "@/features/tenant-settings/hooks/useRateLimits";
import { useRateLimitsAlerts } from "@/features/tenant-settings/hooks/useRateLimitsAlerts";
import { useRateLimitsSave } from "@/features/tenant-settings/hooks/useRateLimitsSave";
import { useRateLimitsUsage } from "@/features/tenant-settings/hooks/useRateLimitsUsage";

function mockSave(
  overrides: Partial<{
    mutate: ReturnType<typeof vi.fn>;
    isPending: boolean;
    isSuccess: boolean;
    error: Error | null;
    reset: ReturnType<typeof vi.fn>;
  }> = {},
): void {
  vi.mocked(useQuotasSave).mockReturnValue({
    mutate: overrides.mutate ?? vi.fn(),
    isPending: overrides.isPending ?? false,
    isSuccess: overrides.isSuccess ?? false,
    error: overrides.error ?? null,
    reset: overrides.reset ?? vi.fn(),
  } as unknown as ReturnType<typeof useQuotasSave>);
}

function mockRlSave(
  overrides: Partial<{
    mutate: ReturnType<typeof vi.fn>;
    isPending: boolean;
    isSuccess: boolean;
    error: Error | null;
    reset: ReturnType<typeof vi.fn>;
  }> = {},
): void {
  vi.mocked(useRateLimitsSave).mockReturnValue({
    mutate: overrides.mutate ?? vi.fn(),
    isPending: overrides.isPending ?? false,
    isSuccess: overrides.isSuccess ?? false,
    error: overrides.error ?? null,
    reset: overrides.reset ?? vi.fn(),
  } as unknown as ReturnType<typeof useRateLimitsSave>);
}

function mockData(quotas: unknown[], rateLimits: unknown[]): void {
  vi.mocked(useQuotas).mockReturnValue({
    data: { items: quotas, total: quotas.length, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useQuotas>);
  vi.mocked(useRateLimits).mockReturnValue({
    data: { items: rateLimits, total: rateLimits.length, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useRateLimits>);
}

/** Sprint 57.58 — control the Live usage poll hook independently. */
function mockUsage(
  usage: unknown[] | undefined,
  overrides: Partial<{ isLoading: boolean; error: Error | null }> = {},
): void {
  vi.mocked(useRateLimitsUsage).mockReturnValue({
    data: usage === undefined ? undefined : { items: usage },
    isLoading: overrides.isLoading ?? false,
    error: overrides.error ?? null,
  } as unknown as ReturnType<typeof useRateLimitsUsage>);
}

/** Sprint 57.62 — control the Recent alerts poll hook independently. */
function mockAlerts(
  alerts: unknown[] | undefined,
  overrides: Partial<{ isLoading: boolean; error: Error | null }> = {},
): void {
  vi.mocked(useRateLimitsAlerts).mockReturnValue({
    data: alerts === undefined ? undefined : { items: alerts },
    isLoading: overrides.isLoading ?? false,
    error: overrides.error ?? null,
  } as unknown as ReturnType<typeof useRateLimitsAlerts>);
}

const SAMPLE_QUOTAS = [
  { resource: "tokens_per_day", limit: 10_000_000, unit: "tokens", period: "day", current_usage: null },
  { resource: "cost_usd_per_day", limit: 100, unit: "usd", period: "day", current_usage: null },
];

describe("QuotasTab (Sprint 57.49)", () => {
  beforeEach(() => {
    mockData([], []);
    mockSave();
    mockRlSave();
    mockUsage([]);
    mockAlerts([]);
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'Usage quotas' + 'Rate limits' Card titles", () => {
    render(<QuotasTab tenantId="t1" />);
    expect(screen.getByText("Usage quotas")).toBeInTheDocument();
    expect(screen.getByText("Rate limits")).toBeInTheDocument();
  });

  it("Usage quotas Card renders loading state", () => {
    vi.mocked(useQuotas).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useQuotas>);
    vi.mocked(useRateLimits).mockReturnValue({
      data: { items: [], total: 0, limit: 50, offset: 0 },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useRateLimits>);
    render(<QuotasTab tenantId="t1" />);
    expect(screen.getByText(/Loading quotas/)).toBeInTheDocument();
  });

  it("renders quota rows when data present + null current_usage renders 0% bar-track", () => {
    mockData(SAMPLE_QUOTAS, []);
    const { container } = render(<QuotasTab tenantId="t1" />);
    expect(screen.getByText("tokens_per_day")).toBeInTheDocument();
    expect(screen.getByText("cost_usd_per_day")).toBeInTheDocument();
    const bars = container.querySelectorAll(".bar-track");
    expect(bars.length).toBe(2);
  });

  it("renders rate-limit rows from useRateLimits data", () => {
    mockData(
      [],
      [
        { label: "API requests", value: "100 / min" },
        { label: "Tool calls", value: "1,000 / min" },
      ],
    );
    render(<QuotasTab tenantId="t1" />);
    expect(screen.getByText("API requests")).toBeInTheDocument();
    expect(screen.getByText("100 / min")).toBeInTheDocument();
    expect(screen.getByText("Tool calls")).toBeInTheDocument();
  });

  it("renders AP-2 BackendGapBanner with Sprint 57.56 softened copy", () => {
    mockData(SAMPLE_QUOTAS, []);
    render(<QuotasTab tenantId="t1" />);
    // Sprint 57.57: 2 banners now (Usage Card + Rate limits Card). Usage Card banner = banners[0].
    const banners = screen.getAllByTestId("backend-gap-banner");
    expect(banners.length).toBeGreaterThanOrEqual(1);
    const usageBanner = banners[0];
    expect(usageBanner).toHaveTextContent(/Phase 58\+/);
    expect(usageBanner).toHaveTextContent(/Redis counter exposure/);
    expect(usageBanner).toHaveTextContent(/editable via Edit button/);
  });

  /* === Sprint 57.56 Track B — edit mode tests === */

  describe("edit mode (Sprint 57.56)", () => {
    it("renders Edit button when items present + disabled when empty", () => {
      mockData([], []);
      const { rerender } = render(<QuotasTab tenantId="t1" />);
      expect(screen.getByTestId("quotas-edit-btn")).toBeDisabled();

      mockData(SAMPLE_QUOTAS, []);
      rerender(<QuotasTab tenantId="t1" />);
      expect(screen.getByTestId("quotas-edit-btn")).not.toBeDisabled();
    });

    it("entering edit mode reveals Save/Cancel + numeric inputs (form mode)", () => {
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));

      expect(screen.getByTestId("quotas-save-btn")).toBeInTheDocument();
      expect(screen.getByTestId("quotas-cancel-btn")).toBeInTheDocument();
      // Numeric inputs visible for each resource
      expect(screen.getByTestId("quotas-input-tokens_per_day")).toBeInTheDocument();
      expect(screen.getByTestId("quotas-input-cost_usd_per_day")).toBeInTheDocument();
    });

    it("seeds draft from current items[].limit on entering edit mode", () => {
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));

      const tokensInput = screen.getByTestId("quotas-input-tokens_per_day") as HTMLInputElement;
      const costInput = screen.getByTestId("quotas-input-cost_usd_per_day") as HTMLInputElement;
      // Draft seeded from items[].limit → input.value reflects it
      expect(tokensInput.value).toBe("10000000");
      expect(costInput.value).toBe("100");
      // Clear override buttons visible (all rows in draft post-Edit)
      expect(screen.getByTestId("quotas-clear-tokens_per_day")).toBeInTheDocument();
      expect(screen.getByTestId("quotas-clear-cost_usd_per_day")).toBeInTheDocument();
    });

    it("changing input updates draft for that resource", () => {
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));

      const tokensInput = screen.getByTestId("quotas-input-tokens_per_day") as HTMLInputElement;
      fireEvent.change(tokensInput, { target: { value: "25000000" } });
      expect(tokensInput.value).toBe("25000000");
    });

    it("Clear override button removes resource from draft", () => {
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));

      expect(screen.getByTestId("quotas-clear-tokens_per_day")).toBeInTheDocument();
      fireEvent.click(screen.getByTestId("quotas-clear-tokens_per_day"));
      expect(screen.queryByTestId("quotas-clear-tokens_per_day")).toBeNull();
    });

    it("Save button calls mutation with current draft as overrides payload", () => {
      const mutate = vi.fn();
      mockSave({ mutate });
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);

      fireEvent.click(screen.getByTestId("quotas-edit-btn"));
      fireEvent.click(screen.getByTestId("quotas-save-btn"));

      expect(mutate).toHaveBeenCalledWith({
        overrides: { tokens_per_day: 10_000_000, cost_usd_per_day: 100 },
      });
    });

    it("Cancel button resets draft + exits edit mode", () => {
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));
      fireEvent.click(screen.getByTestId("quotas-cancel-btn"));

      expect(screen.queryByTestId("quotas-save-btn")).toBeNull();
      expect(screen.queryByTestId("quotas-cancel-btn")).toBeNull();
      expect(screen.getByTestId("quotas-edit-btn")).toBeInTheDocument();
    });

    it("Save button disabled + 'Saving…' label while mutation isPending", () => {
      mockSave({ isPending: true });
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));

      const saveBtn = screen.getByTestId("quotas-save-btn");
      expect(saveBtn).toBeDisabled();
      expect(saveBtn).toHaveTextContent(/Saving…/);
      expect(screen.getByTestId("quotas-cancel-btn")).toBeDisabled();
    });

    it("renders save error message when mutation.error present", () => {
      mockSave({ error: new Error("HTTP 422: unknown resource") });
      mockData(SAMPLE_QUOTAS, []);
      render(<QuotasTab tenantId="t1" />);

      const err = screen.getByTestId("quotas-save-error");
      expect(err).toBeInTheDocument();
      expect(err).toHaveTextContent(/unknown resource/);
    });

    it("scope guard: Rate limits Card still renders rate-limit items independently of Usage quotas edit mode", () => {
      mockData(SAMPLE_QUOTAS, [
        { label: "API requests", value: "100 / min" },
      ]);
      render(<QuotasTab tenantId="t1" />);

      // Enter edit mode for Usage quotas → Rate limits unaffected
      fireEvent.click(screen.getByTestId("quotas-edit-btn"));
      expect(screen.getByText("Rate limits")).toBeInTheDocument();
      expect(screen.getByText("API requests")).toBeInTheDocument();
      expect(screen.getByText("100 / min")).toBeInTheDocument();
      // Rate limits Card has its own Edit button (Sprint 57.57)
      expect(screen.getByTestId("ratelimits-edit-btn")).toBeInTheDocument();
    });
  });

  /* === Sprint 57.57 Track B — Rate limits Card edit mode tests === */

  const SAMPLE_RATE_LIMITS = [
    { label: "API requests", value: "100/min" },
    { label: "Agent runs", value: "20/min" },
  ];

  describe("Rate limits edit mode (Sprint 57.57)", () => {
    it("renders Rate limits Edit button when data loaded", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      expect(screen.getByTestId("ratelimits-edit-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-edit-btn")).not.toBeDisabled();
    });

    it("entering edit mode reveals Save/Cancel + per-row label+value inputs + Add row button", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      expect(screen.getByTestId("ratelimits-save-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-cancel-btn")).toBeInTheDocument();
      // Two rows × two inputs each
      expect(screen.getByTestId("ratelimits-label-input-0")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-value-input-0")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-label-input-1")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-value-input-1")).toBeInTheDocument();
      // Per-row remove buttons
      expect(screen.getByTestId("ratelimits-remove-0")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-remove-1")).toBeInTheDocument();
      // Add row button
      expect(screen.getByTestId("ratelimits-add-row-btn")).toBeInTheDocument();
    });

    it("seeds rlDraft from current items on entering edit mode", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      const lbl0 = screen.getByTestId("ratelimits-label-input-0") as HTMLInputElement;
      const val0 = screen.getByTestId("ratelimits-value-input-0") as HTMLInputElement;
      const lbl1 = screen.getByTestId("ratelimits-label-input-1") as HTMLInputElement;
      const val1 = screen.getByTestId("ratelimits-value-input-1") as HTMLInputElement;
      expect(lbl0.value).toBe("API requests");
      expect(val0.value).toBe("100/min");
      expect(lbl1.value).toBe("Agent runs");
      expect(val1.value).toBe("20/min");
    });

    it("changing label input updates rlDraft[index].label", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      const lbl0 = screen.getByTestId("ratelimits-label-input-0") as HTMLInputElement;
      fireEvent.change(lbl0, { target: { value: "API calls" } });
      expect(lbl0.value).toBe("API calls");
    });

    it("changing value input updates rlDraft[index].value", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      const val0 = screen.getByTestId("ratelimits-value-input-0") as HTMLInputElement;
      fireEvent.change(val0, { target: { value: "200/min" } });
      expect(val0.value).toBe("200/min");
    });

    it("Add row button appends empty row to rlDraft", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      expect(screen.queryByTestId("ratelimits-label-input-2")).toBeNull();
      fireEvent.click(screen.getByTestId("ratelimits-add-row-btn"));
      const newLbl = screen.getByTestId("ratelimits-label-input-2") as HTMLInputElement;
      const newVal = screen.getByTestId("ratelimits-value-input-2") as HTMLInputElement;
      expect(newLbl.value).toBe("");
      expect(newVal.value).toBe("");
    });

    it("Remove (×) button drops that row from rlDraft", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      expect(screen.getByTestId("ratelimits-label-input-1")).toBeInTheDocument();
      fireEvent.click(screen.getByTestId("ratelimits-remove-0"));
      // After removal, row index 0 now shows what was index 1
      const lbl0 = screen.getByTestId("ratelimits-label-input-0") as HTMLInputElement;
      expect(lbl0.value).toBe("Agent runs");
      // Original index-1 no longer present (only 1 row remains)
      expect(screen.queryByTestId("ratelimits-label-input-1")).toBeNull();
    });

    it("Save button calls rlMutation with current rlDraft as items payload", () => {
      const mutate = vi.fn();
      mockRlSave({ mutate });
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);

      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));
      fireEvent.click(screen.getByTestId("ratelimits-save-btn"));

      expect(mutate).toHaveBeenCalledWith({
        items: [
          { label: "API requests", value: "100/min" },
          { label: "Agent runs", value: "20/min" },
        ],
      });
    });

    it("empty list save allowed (composite-clear → backend falls back to defaults)", () => {
      const mutate = vi.fn();
      mockRlSave({ mutate });
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);

      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));
      fireEvent.click(screen.getByTestId("ratelimits-remove-0"));
      fireEvent.click(screen.getByTestId("ratelimits-remove-0"));
      // All rows removed — empty-draft hint visible
      expect(screen.getByTestId("ratelimits-empty-draft")).toBeInTheDocument();

      fireEvent.click(screen.getByTestId("ratelimits-save-btn"));
      expect(mutate).toHaveBeenCalledWith({ items: [] });
    });

    it("Cancel button resets rlDraft + exits edit mode", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));
      fireEvent.click(screen.getByTestId("ratelimits-cancel-btn"));

      expect(screen.queryByTestId("ratelimits-save-btn")).toBeNull();
      expect(screen.queryByTestId("ratelimits-cancel-btn")).toBeNull();
      expect(screen.getByTestId("ratelimits-edit-btn")).toBeInTheDocument();
    });

    it("Save button disabled + 'Saving…' label while rlMutation isPending", () => {
      mockRlSave({ isPending: true });
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));

      const saveBtn = screen.getByTestId("ratelimits-save-btn");
      expect(saveBtn).toBeDisabled();
      expect(saveBtn).toHaveTextContent(/Saving…/);
      expect(screen.getByTestId("ratelimits-cancel-btn")).toBeDisabled();
    });

    it("renders save error message when rlMutation.error present", () => {
      mockRlSave({ error: new Error("HTTP 422: items[].label required") });
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);

      const err = screen.getByTestId("ratelimits-save-error");
      expect(err).toBeInTheDocument();
      expect(err).toHaveTextContent(/label required/);
    });

    it("renders Rate limits BackendGapBanner with Sprint 57.57 softened copy", () => {
      mockData([], SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);
      // 2 BackendGapBanner instances now (Usage Card + Rate limits Card)
      const banners = screen.getAllByTestId("backend-gap-banner");
      expect(banners.length).toBe(2);
      // Rate limits banner content
      const rlBanner = banners[1];
      expect(rlBanner).toHaveTextContent(/syntax validation/);
      expect(rlBanner).toHaveTextContent(/editable via Edit button/);
    });

    it("scope guard: Usage quotas Card edit mode (Sprint 57.56) UNCHANGED when Rate limits editing", () => {
      mockData(SAMPLE_QUOTAS, SAMPLE_RATE_LIMITS);
      render(<QuotasTab tenantId="t1" />);

      // Enter Rate limits edit mode → Usage quotas Card unaffected
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));
      // Sprint 57.56 Usage quotas Edit button still present + functional
      expect(screen.getByTestId("quotas-edit-btn")).toBeInTheDocument();
      expect(screen.getByTestId("quotas-edit-btn")).not.toBeDisabled();
      // Usage quotas rows still rendered in read-only display
      expect(screen.getByText("tokens_per_day")).toBeInTheDocument();
      expect(screen.getByText("cost_usd_per_day")).toBeInTheDocument();
      // Usage quotas edit-mode controls NOT present (we're editing Rate limits, not Usage)
      expect(screen.queryByTestId("quotas-save-btn")).toBeNull();
      expect(screen.queryByTestId("quotas-cancel-btn")).toBeNull();
    });
  });

  /* === Sprint 57.58 Track D — Live usage Card tests === */

  const SAMPLE_USAGE = [
    // green: 30/100 = 30%
    { resource: "api_requests", window: 60, limit: 100, current: 30, reset_at: 1_900_000_060 },
    // yellow: 16/20 = 80%
    { resource: "agent_runs", window: 60, limit: 20, current: 16, reset_at: 1_900_000_055 },
    // red: 95/100 = 95%
    { resource: "tool_calls", window: 60, limit: 100, current: 95, reset_at: 1_900_000_058 },
  ];

  describe("Live usage Card (Sprint 57.58)", () => {
    it("renders 'Live usage' Card title + per-resource rows when usage present", () => {
      mockData([], []);
      mockUsage(SAMPLE_USAGE);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByText("Live usage")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-list")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-row-api_requests")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-row-agent_runs")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-row-tool_calls")).toBeInTheDocument();
    });

    it("renders per-resource progress (current / limit / pct) with a bar-track", () => {
      mockData([], []);
      mockUsage(SAMPLE_USAGE);
      const { container } = render(<QuotasTab tenantId="t1" />);

      // Count text reflects current value
      expect(screen.getByTestId("ratelimits-usage-count-api_requests")).toHaveTextContent("30");
      // pct text present (30%)
      expect(screen.getByText(/\(30%\)/)).toBeInTheDocument();
      // Live usage Card bars use the same .bar-track primitive (3 usage rows;
      // SAMPLE_QUOTAS not loaded here so all bar-tracks belong to Live usage)
      const bars = container.querySelectorAll(".bar-track");
      expect(bars.length).toBe(3);
    });

    it("color-codes severity by threshold (green<70 / yellow70-90 / red>90)", () => {
      mockData([], []);
      mockUsage(SAMPLE_USAGE);
      const { container } = render(<QuotasTab tenantId="t1" />);

      const ok = container.querySelector(
        '[data-testid="ratelimits-usage-row-api_requests"] .bar-track',
      );
      const warn = container.querySelector(
        '[data-testid="ratelimits-usage-row-agent_runs"] .bar-track',
      );
      const crit = container.querySelector(
        '[data-testid="ratelimits-usage-row-tool_calls"] .bar-track',
      );
      // 30% → ok (green), 80% → warn (yellow), 95% → crit (red)
      expect(ok).toHaveAttribute("data-severity", "ok");
      expect(warn).toHaveAttribute("data-severity", "warn");
      expect(crit).toHaveAttribute("data-severity", "crit");
    });

    it("renders a human-readable reset countdown per resource", () => {
      // Freeze Date.now so reset_at - now is deterministic.
      // reset_at 1_900_000_060 → 60s after the frozen now (1_900_000_000_000 ms).
      const nowSpy = vi.spyOn(Date, "now").mockReturnValue(1_900_000_000_000);
      mockData([], []);
      mockUsage(SAMPLE_USAGE);
      render(<QuotasTab tenantId="t1" />);

      // api_requests reset_at is 60s out → "1m"
      expect(screen.getByTestId("ratelimits-usage-reset-api_requests")).toHaveTextContent("1m");
      // agent_runs reset_at is 55s out → "55s"
      expect(screen.getByTestId("ratelimits-usage-reset-agent_runs")).toHaveTextContent("55s");
      nowSpy.mockRestore();
    });

    it("renders empty state when no rate limits configured", () => {
      mockData([], []);
      mockUsage([]);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByTestId("ratelimits-usage-empty")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-empty")).toHaveTextContent(
        /No rate limits configured/,
      );
      expect(screen.queryByTestId("ratelimits-usage-list")).toBeNull();
    });

    it("renders loading + error states from the poll hook", () => {
      mockData([], []);
      mockUsage(undefined, { isLoading: true });
      const { rerender } = render(<QuotasTab tenantId="t1" />);
      expect(screen.getByTestId("ratelimits-usage-loading")).toBeInTheDocument();

      mockUsage(undefined, { error: new Error("HTTP 404: tenant not found") });
      rerender(<QuotasTab tenantId="t1" />);
      const err = screen.getByTestId("ratelimits-usage-error");
      expect(err).toBeInTheDocument();
      expect(err).toHaveTextContent(/tenant not found/);
    });

    it("scope guard: Rate limits Card (Sprint 57.57) UNCHANGED when Live usage present", () => {
      const SAMPLE_RATE_LIMITS = [{ label: "API requests", value: "100/min" }];
      mockData([], SAMPLE_RATE_LIMITS);
      mockUsage(SAMPLE_USAGE);
      render(<QuotasTab tenantId="t1" />);

      // Rate limits Card retains its read-only items + Edit button untouched
      expect(screen.getByText("Rate limits")).toBeInTheDocument();
      expect(screen.getByText("API requests")).toBeInTheDocument();
      expect(screen.getByText("100/min")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-edit-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-edit-btn")).not.toBeDisabled();
      // Entering Rate limits edit mode still works (independent of Live usage Card)
      fireEvent.click(screen.getByTestId("ratelimits-edit-btn"));
      expect(screen.getByTestId("ratelimits-save-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-cancel-btn")).toBeInTheDocument();
      // Live usage Card still rendered alongside
      expect(screen.getByText("Live usage")).toBeInTheDocument();
    });
  });

  /* === Sprint 57.62 US-3 — Recent alerts Card tests === */

  const SAMPLE_ALERTS = [
    {
      resource: "api_requests",
      window: "min",
      threshold_pct: 80,
      actual_pct: 92,
      used: 92,
      quota: 100,
      severity: "warning",
      window_start: "2026-05-29T10:00:00Z",
      triggered_at: "2026-05-29T10:00:05Z",
    },
    {
      resource: "tool_calls",
      window: "min",
      threshold_pct: 80,
      actual_pct: 100,
      used: 100,
      quota: 100,
      severity: "critical",
      window_start: "2026-05-29T09:59:00Z",
      triggered_at: "2026-05-29T09:59:30Z",
    },
  ];

  describe("Recent alerts Card (Sprint 57.62)", () => {
    it("renders 'Recent alerts' Card title + per-alert rows when alerts present", () => {
      mockData([], []);
      mockAlerts(SAMPLE_ALERTS);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByText("Recent alerts")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-alerts-list")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-alert-row-api_requests")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-alert-row-tool_calls")).toBeInTheDocument();
    });

    it("renders peak pct + severity per alert row", () => {
      mockData([], []);
      mockAlerts(SAMPLE_ALERTS);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByTestId("ratelimits-alert-pct-api_requests")).toHaveTextContent("92%");
      expect(screen.getByTestId("ratelimits-alert-pct-tool_calls")).toHaveTextContent("100%");
      expect(screen.getByTestId("ratelimits-alert-badge-api_requests")).toHaveTextContent("warning");
      expect(screen.getByTestId("ratelimits-alert-badge-tool_calls")).toHaveTextContent("critical");
    });

    it("maps severity → existing token badge modifier (warning → .badge.warning, critical → .badge.danger)", () => {
      mockData([], []);
      mockAlerts(SAMPLE_ALERTS);
      render(<QuotasTab tenantId="t1" />);

      const warnBadge = screen.getByTestId("ratelimits-alert-badge-api_requests");
      const critBadge = screen.getByTestId("ratelimits-alert-badge-tool_calls");
      // severity → existing styles-mockup.css badge modifier (refs --warning / --danger; no new oklch)
      expect(warnBadge).toHaveClass("badge", "warning");
      expect(warnBadge).toHaveAttribute("data-severity", "warning");
      expect(critBadge).toHaveClass("badge", "danger");
      expect(critBadge).toHaveAttribute("data-severity", "critical");
    });

    it("renders a relative-time label per alert", () => {
      // Freeze Date.now so triggered_at - now is deterministic.
      // triggered_at 2026-05-29T10:00:05Z; now = +65s → "1m ago".
      const nowSpy = vi
        .spyOn(Date, "now")
        .mockReturnValue(Date.parse("2026-05-29T10:01:10Z"));
      mockData([], []);
      mockAlerts(SAMPLE_ALERTS);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByTestId("ratelimits-alert-time-api_requests")).toHaveTextContent("1m ago");
      nowSpy.mockRestore();
    });

    it("renders empty state when no alerts recorded", () => {
      mockData([], []);
      mockAlerts([]);
      render(<QuotasTab tenantId="t1" />);

      expect(screen.getByTestId("ratelimits-alerts-empty")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-alerts-empty")).toHaveTextContent(/No recent alerts/);
      expect(screen.queryByTestId("ratelimits-alerts-list")).toBeNull();
    });

    it("renders loading + error states from the alerts poll hook", () => {
      mockData([], []);
      mockAlerts(undefined, { isLoading: true });
      const { rerender } = render(<QuotasTab tenantId="t1" />);
      expect(screen.getByTestId("ratelimits-alerts-loading")).toBeInTheDocument();

      mockAlerts(undefined, { error: new Error("HTTP 404: tenant not found") });
      rerender(<QuotasTab tenantId="t1" />);
      const err = screen.getByTestId("ratelimits-alerts-error");
      expect(err).toBeInTheDocument();
      expect(err).toHaveTextContent(/tenant not found/);
    });

    it("scope guard: existing Rate limits + Live usage Cards UNCHANGED when alerts present", () => {
      const SAMPLE_RATE_LIMITS = [{ label: "API requests", value: "100/min" }];
      mockData([], SAMPLE_RATE_LIMITS);
      mockUsage(SAMPLE_USAGE);
      mockAlerts(SAMPLE_ALERTS);
      render(<QuotasTab tenantId="t1" />);

      // Rate limits Card (Sprint 57.57) intact — read-only items + Edit button
      expect(screen.getByText("Rate limits")).toBeInTheDocument();
      expect(screen.getByText("API requests")).toBeInTheDocument();
      expect(screen.getByText("100/min")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-edit-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-edit-btn")).not.toBeDisabled();

      // Live usage Card (Sprint 57.58) intact — list + rows
      expect(screen.getByText("Live usage")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-list")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-usage-row-api_requests")).toBeInTheDocument();

      // Recent alerts Card rendered alongside
      expect(screen.getByText("Recent alerts")).toBeInTheDocument();
      expect(screen.getByTestId("ratelimits-alerts-list")).toBeInTheDocument();
    });
  });
});
