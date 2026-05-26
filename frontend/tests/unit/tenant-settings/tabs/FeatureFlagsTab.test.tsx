/**
 * File: frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx
 * Purpose: Vitest coverage for FeatureFlagsTab — real backend useFeatureFlags hook integration.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.49 Day 1 (fixture → real backend migration)
 *
 * Description:
 *   - Renders "Feature flags" Card title + subtitle "Tenant-scoped overrides"
 *   - Loading state visible when isLoading=true
 *   - Error state visible when error present
 *   - Empty state when items=[]
 *   - Renders flag rows from hook data; <Switch role='switch'> per row
 *   - BackendGapBanner present
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.55 Track B — +8 edit-mode tests (Save/Cancel/clear/disabled/copy)
 *   - 2026-05-26: Sprint 57.49 — rewrite to mock useFeatureFlags hook (post fixture → real migration)
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/tenant-settings/hooks/useFeatureFlags", () => ({
  useFeatureFlags: vi.fn(),
  FEATURE_FLAGS_QUERY_KEY_BASE: ["tenant-settings", "feature-flags"],
}));

vi.mock("@/features/tenant-settings/hooks/useFeatureFlagsSave", () => ({
  useFeatureFlagsSave: vi.fn(),
}));

import { FeatureFlagsTab } from "@/features/tenant-settings/components/tabs/FeatureFlagsTab";
import { useFeatureFlags } from "@/features/tenant-settings/hooks/useFeatureFlags";
import { useFeatureFlagsSave } from "@/features/tenant-settings/hooks/useFeatureFlagsSave";

function mockSave(
  overrides: Partial<{
    mutate: ReturnType<typeof vi.fn>;
    isPending: boolean;
    isSuccess: boolean;
    error: Error | null;
    reset: ReturnType<typeof vi.fn>;
  }> = {},
): void {
  vi.mocked(useFeatureFlagsSave).mockReturnValue({
    mutate: overrides.mutate ?? vi.fn(),
    isPending: overrides.isPending ?? false,
    isSuccess: overrides.isSuccess ?? false,
    error: overrides.error ?? null,
    reset: overrides.reset ?? vi.fn(),
  } as unknown as ReturnType<typeof useFeatureFlagsSave>);
}

function mockData(items: unknown[]): void {
  vi.mocked(useFeatureFlags).mockReturnValue({
    data: { items, total: items.length, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useFeatureFlags>);
}

const SAMPLE_ITEMS = [
  {
    name: "subagent.fork.enabled",
    value: true,
    default_enabled: false,
    overridden: true,
    description: "Allow concurrent fork mode",
    updated_at: "2026-05-27T00:00:00Z",
  },
  {
    name: "tool.sandbox_full",
    value: false,
    default_enabled: false,
    overridden: false,
    description: "Permit FULL_SANDBOX tool runs",
    updated_at: "2026-05-27T00:00:00Z",
  },
];

describe("FeatureFlagsTab (Sprint 57.49)", () => {
  beforeEach(() => {
    mockData([]);
    mockSave();
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders Card title 'Feature flags' + subtitle", () => {
    render(<FeatureFlagsTab tenantId="t1" />);
    expect(screen.getByText("Feature flags")).toBeInTheDocument();
    expect(screen.getByText(/Tenant-scoped overrides/)).toBeInTheDocument();
  });

  it("renders 'Loading feature flags…' when isLoading=true", () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useFeatureFlags>);
    render(<FeatureFlagsTab tenantId="t1" />);
    expect(screen.getByText(/Loading feature flags/)).toBeInTheDocument();
  });

  it("renders error message when error present", () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("HTTP 500"),
    } as unknown as ReturnType<typeof useFeatureFlags>);
    render(<FeatureFlagsTab tenantId="t1" />);
    expect(screen.getByText(/HTTP 500/)).toBeInTheDocument();
  });

  it("renders empty state when items=[]", () => {
    mockData([]);
    render(<FeatureFlagsTab tenantId="t1" />);
    expect(screen.getByText(/No feature flags registered/)).toBeInTheDocument();
  });

  it("renders flag rows with Switch when data present", () => {
    mockData([
      {
        name: "subagent.fork.enabled",
        value: true,
        default_enabled: true,
        overridden: false,
        description: "Allow concurrent fork mode",
        updated_at: "2026-05-26T00:00:00Z",
      },
      {
        name: "tool.sandbox_full",
        value: false,
        default_enabled: false,
        overridden: false,
        description: "Permit FULL_SANDBOX tool runs",
        updated_at: "2026-05-26T00:00:00Z",
      },
    ]);
    const { container } = render(<FeatureFlagsTab tenantId="t1" />);
    expect(screen.getByText("subagent.fork.enabled")).toBeInTheDocument();
    expect(screen.getByText("tool.sandbox_full")).toBeInTheDocument();
    const switches = container.querySelectorAll("[role='switch']");
    expect(switches.length).toBe(2);
  });

  it("renders AP-2 BackendGapBanner with softened Sprint 57.55 copy", () => {
    mockData([]);
    render(<FeatureFlagsTab tenantId="t1" />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/editable via Edit button/);
  });

  /* === Sprint 57.55 Track B — edit mode tests === */

  describe("edit mode (Sprint 57.55)", () => {
    it("renders Edit button when items present + disabled when empty", () => {
      mockData([]);
      const { rerender } = render(<FeatureFlagsTab tenantId="t1" />);
      expect(screen.getByTestId("ff-edit-btn")).toBeDisabled();

      mockData(SAMPLE_ITEMS);
      rerender(<FeatureFlagsTab tenantId="t1" />);
      expect(screen.getByTestId("ff-edit-btn")).not.toBeDisabled();
    });

    it("entering edit mode reveals Save/Cancel + seeds draft from overridden items", () => {
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ff-edit-btn"));

      expect(screen.getByTestId("ff-save-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ff-cancel-btn")).toBeInTheDocument();
      // Only "subagent.fork.enabled" is overridden → Clear override button visible only for it
      expect(screen.getByTestId("ff-clear-subagent.fork.enabled")).toBeInTheDocument();
      expect(screen.queryByTestId("ff-clear-tool.sandbox_full")).toBeNull();
    });

    it("toggle button updates draft state for non-overridden flag", () => {
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ff-edit-btn"));

      // tool.sandbox_full starts NOT in draft → no clear button
      expect(screen.queryByTestId("ff-clear-tool.sandbox_full")).toBeNull();
      // Toggle it → enters draft → clear button appears
      fireEvent.click(screen.getByTestId("ff-toggle-tool.sandbox_full"));
      expect(screen.getByTestId("ff-clear-tool.sandbox_full")).toBeInTheDocument();
    });

    it("Clear override button removes flag from draft", () => {
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ff-edit-btn"));

      expect(screen.getByTestId("ff-clear-subagent.fork.enabled")).toBeInTheDocument();
      fireEvent.click(screen.getByTestId("ff-clear-subagent.fork.enabled"));
      expect(screen.queryByTestId("ff-clear-subagent.fork.enabled")).toBeNull();
    });

    it("Save button calls mutation with composite payload", () => {
      const mutate = vi.fn();
      mockSave({ mutate });
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);

      fireEvent.click(screen.getByTestId("ff-edit-btn"));
      fireEvent.click(screen.getByTestId("ff-save-btn"));

      expect(mutate).toHaveBeenCalledWith({
        overrides: { "subagent.fork.enabled": true },
      });
    });

    it("Cancel button resets draft + exits edit mode", () => {
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ff-edit-btn"));
      fireEvent.click(screen.getByTestId("ff-cancel-btn"));

      expect(screen.queryByTestId("ff-save-btn")).toBeNull();
      expect(screen.queryByTestId("ff-cancel-btn")).toBeNull();
      expect(screen.getByTestId("ff-edit-btn")).toBeInTheDocument();
    });

    it("Save button disabled + 'Saving…' label while mutation isPending", () => {
      mockSave({ isPending: true });
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);
      fireEvent.click(screen.getByTestId("ff-edit-btn"));

      const saveBtn = screen.getByTestId("ff-save-btn");
      expect(saveBtn).toBeDisabled();
      expect(saveBtn).toHaveTextContent(/Saving…/);
      expect(screen.getByTestId("ff-cancel-btn")).toBeDisabled();
    });

    it("renders save error message when mutation.error present", () => {
      mockSave({ error: new Error("HTTP 422: unknown flag name") });
      mockData(SAMPLE_ITEMS);
      render(<FeatureFlagsTab tenantId="t1" />);

      const err = screen.getByTestId("ff-save-error");
      expect(err).toBeInTheDocument();
      expect(err).toHaveTextContent(/unknown flag name/);
    });
  });
});
