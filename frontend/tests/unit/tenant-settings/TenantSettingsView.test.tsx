/**
 * File: frontend/tests/unit/tenant-settings/TenantSettingsView.test.tsx
 * Purpose: Vitest coverage for TenantSettingsView — 6-tab router integration with mocked hooks.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders TenantSettingsPageHeader when data loaded
 *   - Renders 6 tabs (General / Feature Flags / Quotas / HITL Policies / Members / Danger Zone)
 *   - Default tab "general" content visible (Identity & SSO card)
 *   - Tab switching reveals correct content
 *   - Loading state rendered when isLoading=true
 *   - Error state rendered with retry button
 *   - "No tenant in your session" fallback when tenantId empty
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Sprint 57.104 C1 — +Model Policy hook mocks + 7th-tab registration assertion
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/TenantSettingsView.tsx
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TenantSettingsView } from "@/features/tenant-settings/components/TenantSettingsView";
import {
  TenantPlan,
  TenantState,
  type TenantSettingsResponse,
} from "@/features/tenant-settings/types";

// Mock hooks before component import would normally be required, but with vi.mock these work.
vi.mock("@/features/tenant-settings/hooks/useTenantSettings", () => ({
  useTenantSettings: vi.fn(),
  TENANT_SETTINGS_QUERY_KEY_BASE: ["tenant-settings", "detail"],
}));

vi.mock("@/features/tenant-settings/hooks/useTenantSettingsSave", () => ({
  useTenantSettingsSave: vi.fn(),
}));

// Sprint 57.49 — mock 5 NEW sub-resource hooks (tabs migrated fixture → real backend)
vi.mock("@/features/tenant-settings/hooks/useTenantMembers", () => ({
  useTenantMembers: vi.fn(),
  TENANT_MEMBERS_QUERY_KEY_BASE: ["tenant-settings", "members"],
}));
vi.mock("@/features/tenant-settings/hooks/useHITLPolicies", () => ({
  useHITLPolicies: vi.fn(),
  HITL_POLICIES_QUERY_KEY_BASE: ["tenant-settings", "hitl-policies"],
}));
vi.mock("@/features/tenant-settings/hooks/useFeatureFlags", () => ({
  useFeatureFlags: vi.fn(),
  FEATURE_FLAGS_QUERY_KEY_BASE: ["tenant-settings", "feature-flags"],
}));
vi.mock("@/features/tenant-settings/hooks/useQuotas", () => ({
  useQuotas: vi.fn(),
  QUOTAS_QUERY_KEY_BASE: ["tenant-settings", "quotas"],
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimits", () => ({
  useRateLimits: vi.fn(),
  RATE_LIMITS_QUERY_KEY_BASE: ["tenant-settings", "rate-limits"],
}));
// Sprint 57.58/57.62 — Live usage + alerts poll hooks (consumed by QuotasTab)
vi.mock("@/features/tenant-settings/hooks/useRateLimitsUsage", () => ({
  useRateLimitsUsage: vi.fn(),
  RATE_LIMITS_USAGE_QUERY_KEY_BASE: ["tenant-settings", "rate-limits-usage"],
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimitsSave", () => ({
  useRateLimitsSave: vi.fn(),
}));
vi.mock("@/features/tenant-settings/hooks/useRateLimitsAlerts", () => ({
  useRateLimitsAlerts: vi.fn(),
  RATE_LIMITS_ALERTS_QUERY_KEY_BASE: ["tenant-settings", "rate-limits-alerts"],
}));
vi.mock("@/features/tenant-settings/hooks/useQuotasSave", () => ({
  useQuotasSave: vi.fn(),
}));
// Sprint 57.104 C1 — Model Policy hooks (consumed by ModelPolicyTab)
vi.mock("@/features/tenant-settings/hooks/useModelPolicy", () => ({
  useModelPolicy: vi.fn(),
  MODEL_POLICY_QUERY_KEY_BASE: ["tenant-settings", "model-policy"],
}));
vi.mock("@/features/tenant-settings/hooks/useModelPolicySave", () => ({
  useModelPolicySave: vi.fn(),
}));
// Sprint 57.50 — Identity hook (consumed by GeneralTab Identity & SSO card)
vi.mock("@/features/tenant-settings/hooks/useTenantIdentity", () => ({
  useTenantIdentity: vi.fn(),
  TENANT_IDENTITY_QUERY_KEY_BASE: ["tenant-settings", "identity"],
}));

vi.mock("@/features/auth/store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

import { useTenantSettings } from "@/features/tenant-settings/hooks/useTenantSettings";
import { useTenantSettingsSave } from "@/features/tenant-settings/hooks/useTenantSettingsSave";
import { useTenantMembers } from "@/features/tenant-settings/hooks/useTenantMembers";
import { useHITLPolicies } from "@/features/tenant-settings/hooks/useHITLPolicies";
import { useFeatureFlags } from "@/features/tenant-settings/hooks/useFeatureFlags";
import { useQuotas } from "@/features/tenant-settings/hooks/useQuotas";
import { useQuotasSave } from "@/features/tenant-settings/hooks/useQuotasSave";
import { useRateLimits } from "@/features/tenant-settings/hooks/useRateLimits";
import { useRateLimitsUsage } from "@/features/tenant-settings/hooks/useRateLimitsUsage";
import { useRateLimitsSave } from "@/features/tenant-settings/hooks/useRateLimitsSave";
import { useRateLimitsAlerts } from "@/features/tenant-settings/hooks/useRateLimitsAlerts";
import { useModelPolicy } from "@/features/tenant-settings/hooks/useModelPolicy";
import { useModelPolicySave } from "@/features/tenant-settings/hooks/useModelPolicySave";
import { useTenantIdentity } from "@/features/tenant-settings/hooks/useTenantIdentity";
import { useAuthStore } from "@/features/auth/store/authStore";

const SAMPLE: TenantSettingsResponse = {
  id: "00000000-0000-0000-0000-000000000001",
  code: "ACME",
  display_name: "Acme Corp",
  state: TenantState.ACTIVE,
  plan: TenantPlan.ENTERPRISE,
  provisioning_progress: {},
  onboarding_progress: {},
  meta_data: {},
  // Sprint 57.46 — SaaS settings extension (5 fields)
  region: "apac",
  locale: "zh-TW",
  retention_days: 365,
  sso_enabled: true,
  seats: 8,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

function setupAuth(tenantId: string): void {
  // useAuthStore is invoked with a selector: (s) => s.tenant?.id ?? ""
  vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
    const state = {
      tenant: tenantId ? { id: tenantId, name: "Acme", code: "ACME" } : null,
    };
    if (typeof selector === "function") {
      return (selector as (s: unknown) => unknown)(state);
    }
    return state;
  });
}

function setupHookLoaded(): void {
  vi.mocked(useTenantSettings).mockReturnValue({
    data: SAMPLE,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useTenantSettings>);
  vi.mocked(useTenantSettingsSave).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof useTenantSettingsSave>);
  // Sprint 57.49 — 5 sub-resource hook mocks (default empty payload; specific tests override)
  vi.mocked(useTenantMembers).mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useTenantMembers>);
  vi.mocked(useHITLPolicies).mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useHITLPolicies>);
  vi.mocked(useFeatureFlags).mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useFeatureFlags>);
  vi.mocked(useQuotas).mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useQuotas>);
  vi.mocked(useRateLimits).mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useRateLimits>);
  // Sprint 57.58/57.62 — QuotasTab Live usage + alerts + save hooks (default empty)
  vi.mocked(useRateLimitsUsage).mockReturnValue({
    data: { items: [] },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useRateLimitsUsage>);
  vi.mocked(useRateLimitsAlerts).mockReturnValue({
    data: { items: [] },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useRateLimitsAlerts>);
  vi.mocked(useRateLimitsSave).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    error: null,
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useRateLimitsSave>);
  vi.mocked(useQuotasSave).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    error: null,
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useQuotasSave>);
  // Sprint 57.104 C1 — Model Policy read + save hooks (default sparse/empty)
  vi.mocked(useModelPolicy).mockReturnValue({
    data: {
      actionDeployment: null,
      actionModel: null,
      cheapDeployment: null,
      cheapModel: null,
    },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useModelPolicy>);
  vi.mocked(useModelPolicySave).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    error: null,
    reset: vi.fn(),
  } as unknown as ReturnType<typeof useModelPolicySave>);
  // Sprint 57.50 — Identity hook (Default mock with 4 fields for GeneralTab Identity Card)
  vi.mocked(useTenantIdentity).mockReturnValue({
    data: {
      provider: "SAML 2.0 · WorkOS",
      scim_enabled: true,
      allowed_domains: ["acme.com", "acme.io"],
      mfa_required: true,
    },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useTenantIdentity>);
}

describe("TenantSettingsView (Sprint 57.44)", () => {
  beforeEach(() => {
    setupAuth("tenant-uuid-x");
    setupHookLoaded();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders TenantSettingsPageHeader with title 'Tenant Settings' when data loaded", () => {
    render(<TenantSettingsView />);
    expect(screen.getByText("Tenant Settings")).toBeInTheDocument();
  });

  it("renders all 7 tab labels", () => {
    render(<TenantSettingsView />);
    expect(screen.getByRole("tab", { name: /General/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Feature Flags/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Quotas/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Model Policy/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /HITL Policies/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Members/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Danger Zone/ })).toBeInTheDocument();
  });

  it("clicking Model Policy tab reveals Model policy card (Sprint 57.104 C1 — 7th tab)", async () => {
    const user = userEvent.setup();
    render(<TenantSettingsView />);
    await user.click(screen.getByRole("tab", { name: /Model Policy/ }));
    expect(screen.getByText("Model policy")).toBeInTheDocument();
    // Default sparse policy → all 4 fields render "System default"
    expect(screen.getByTestId("model-policy-edit-btn")).toBeInTheDocument();
  });

  it("default tab 'general' renders General + Identity & SSO cards", () => {
    render(<TenantSettingsView />);
    // "General" appears as both tab label + Card title — use getAllByText (Sprint 57.41/42/43 cohort lesson)
    const generalMatches = screen.getAllByText("General");
    expect(generalMatches.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Identity & SSO")).toBeInTheDocument();
    // Sprint 57.49 — GeneralTab now consumes real backend SaaS fields
    expect(screen.getByText("SSO Provider")).toBeInTheDocument();
  });

  it("clicking Members tab reveals Members card (Sprint 57.49 — subtitle now uses real backend total)", async () => {
    const user = userEvent.setup();
    render(<TenantSettingsView />);
    await user.click(screen.getByRole("tab", { name: /Members/ }));
    // Sprint 57.49: Members Card subtitle "${total} active · 0 invitations" — default mock total=0
    expect(screen.getByText(/0 active · 0 invitations/)).toBeInTheDocument();
  });

  it("clicking Danger Zone tab reveals Danger zone card", async () => {
    const user = userEvent.setup();
    render(<TenantSettingsView />);
    await user.click(screen.getByRole("tab", { name: /Danger Zone/ }));
    expect(screen.getByText("Danger zone")).toBeInTheDocument();
  });

  it("renders loading state when isLoading=true", () => {
    vi.mocked(useTenantSettings).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useTenantSettings>);
    render(<TenantSettingsView />);
    expect(screen.getByText(/Loading tenant settings/)).toBeInTheDocument();
  });

  it("renders error state with retry button when error present", async () => {
    const refetchSpy = vi.fn();
    vi.mocked(useTenantSettings).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("HTTP 500: server error"),
      refetch: refetchSpy,
    } as unknown as ReturnType<typeof useTenantSettings>);
    render(<TenantSettingsView />);
    expect(screen.getByText(/HTTP 500: server error/)).toBeInTheDocument();
    const retryBtn = screen.getByRole("button", { name: /retry/i });
    expect(retryBtn).toBeInTheDocument();
    const user = userEvent.setup();
    await user.click(retryBtn);
    expect(refetchSpy).toHaveBeenCalledTimes(1);
  });

  it("renders 'No tenant in your session' when tenantId empty", () => {
    setupAuth("");
    render(<TenantSettingsView />);
    expect(screen.getByText(/No tenant in your session/)).toBeInTheDocument();
  });
});
