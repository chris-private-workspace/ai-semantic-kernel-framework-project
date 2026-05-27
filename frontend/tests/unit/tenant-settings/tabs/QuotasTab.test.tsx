/**
 * File: frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx
 * Purpose: Vitest coverage for QuotasTab — useQuotas/useRateLimits + Sprint 57.56 edit mode.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.49 Day 1 + Sprint 57.56 Track B
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.56 Track B — +edit-mode tests + banner copy + scope guard assertion
 *   - 2026-05-26: Sprint 57.49 — rewrite to mock useQuotas + useRateLimits hooks
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

import { QuotasTab } from "@/features/tenant-settings/components/tabs/QuotasTab";
import { useQuotas } from "@/features/tenant-settings/hooks/useQuotas";
import { useQuotasSave } from "@/features/tenant-settings/hooks/useQuotasSave";
import { useRateLimits } from "@/features/tenant-settings/hooks/useRateLimits";

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

const SAMPLE_QUOTAS = [
  { resource: "tokens_per_day", limit: 10_000_000, unit: "tokens", period: "day", current_usage: null },
  { resource: "cost_usd_per_day", limit: 100, unit: "usd", period: "day", current_usage: null },
];

describe("QuotasTab (Sprint 57.49)", () => {
  beforeEach(() => {
    mockData([], []);
    mockSave();
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

  it("Request increase button fires window.alert with backend gap message", async () => {
    mockData([], [{ label: "x", value: "y" }]);
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    const user = userEvent.setup();
    render(<QuotasTab tenantId="t1" />);
    await user.click(screen.getByRole("button", { name: /request increase/i }));
    expect(alertSpy).toHaveBeenCalledWith(expect.stringMatching(/backend gap/i));
    alertSpy.mockRestore();
  });

  it("renders AP-2 BackendGapBanner with Sprint 57.56 softened copy", () => {
    mockData(SAMPLE_QUOTAS, []);
    render(<QuotasTab tenantId="t1" />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/Redis counter exposure/);
    expect(banner).toHaveTextContent(/editable via Edit button/);
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
      // Request increase button still present (Rate limits Card unchanged)
      expect(screen.getByRole("button", { name: /request increase/i })).toBeInTheDocument();
    });
  });
});
