/**
 * File: frontend/tests/unit/tenant-settings/TenantSettingsEditForm.test.tsx
 * Purpose: Unit tests for TenantSettingsEditForm — submit valid + JSON validate invalid (TanStack mutation).
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-4 → Sprint 57.9 US-6 Day 4 (TanStack mutation + tenantId prop)
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — wrap with QueryClientProvider; tenantId now NEW prop (was store-driven); store.setState removed (store is UI-only)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TenantSettingsEditForm } from "../../../src/features/tenant-settings/components/TenantSettingsEditForm";
import * as svc from "../../../src/features/tenant-settings/services/tenantSettingsService";
import {
  TenantPlan,
  TenantState,
  type TenantSettingsResponse,
} from "../../../src/features/tenant-settings/types";

const INITIAL_DATA: TenantSettingsResponse = {
  id: "00000000-0000-0000-0000-000000000001",
  code: "ACME",
  display_name: "Acme Corp",
  state: TenantState.ACTIVE,
  plan: TenantPlan.ENTERPRISE,
  provisioning_progress: {},
  onboarding_progress: {},
  meta_data: { region: "us-west" },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

function renderForm(props: { onDone?: () => void } = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const Wrap = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
  return render(
    <Wrap>
      <TenantSettingsEditForm
        tenantId="tenant-uuid"
        initialData={INITIAL_DATA}
        onDone={props.onDone ?? vi.fn()}
      />
    </Wrap>,
  );
}

describe("TenantSettingsEditForm (post-57.9 US-6 — TanStack mutation)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits valid display_name change → calls updateTenantSettings with correct payload", async () => {
    const updated = { ...INITIAL_DATA, display_name: "Renamed" };
    const updateSpy = vi.spyOn(svc, "updateTenantSettings").mockResolvedValueOnce(updated);
    const onDone = vi.fn();

    renderForm({ onDone });

    const input = screen.getByDisplayValue("Acme Corp");
    fireEvent.change(input, { target: { value: "Renamed" } });

    const saveBtn = screen.getByText("Save");
    fireEvent.click(saveBtn);

    await waitFor(() => expect(updateSpy).toHaveBeenCalled());
    expect(updateSpy).toHaveBeenCalledWith("tenant-uuid", { display_name: "Renamed" });
    await waitFor(() => expect(onDone).toHaveBeenCalled());
  });

  it("shows JSON validation error when meta_data textarea contains invalid JSON", () => {
    renderForm();

    const textarea = screen.getByDisplayValue(/region/);
    fireEvent.change(textarea, { target: { value: "{not valid json" } });
    fireEvent.blur(textarea);

    expect(screen.getByText(/Invalid JSON/)).toBeInTheDocument();
    const saveBtn = screen.getByText("Save") as HTMLButtonElement;
    expect(saveBtn.disabled).toBe(true);
  });

  it("renders display_name input + meta_data textarea with initial values", () => {
    renderForm();
    expect(screen.getByDisplayValue("Acme Corp")).toBeInTheDocument();
    expect(screen.getByDisplayValue(/"region"/)).toBeInTheDocument();
  });
});
