/**
 * File: frontend/tests/unit/tenant-settings/TenantSettingsEditForm.test.tsx
 * Purpose: Unit tests for TenantSettingsEditForm — submit valid + JSON validate invalid.
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-4
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TenantSettingsEditForm } from "../../../src/features/tenant-settings/components/TenantSettingsEditForm";
import * as svc from "../../../src/features/tenant-settings/services/tenantSettingsService";
import { useTenantSettingsStore } from "../../../src/features/tenant-settings/store/tenantSettingsStore";
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

describe("TenantSettingsEditForm", () => {
  afterEach(() => {
    useTenantSettingsStore.getState().reset();
    vi.restoreAllMocks();
  });

  it("submits valid display_name change → calls store.save with correct payload", async () => {
    useTenantSettingsStore.setState({ tenantId: "tenant-uuid", data: INITIAL_DATA });
    const updated = { ...INITIAL_DATA, display_name: "Renamed" };
    const updateSpy = vi.spyOn(svc, "updateTenantSettings").mockResolvedValueOnce(updated);
    const onDone = vi.fn();

    render(<TenantSettingsEditForm initialData={INITIAL_DATA} onDone={onDone} />);

    const input = screen.getByDisplayValue("Acme Corp");
    fireEvent.change(input, { target: { value: "Renamed" } });

    const saveBtn = screen.getByText("Save");
    fireEvent.click(saveBtn);

    // Wait for async save to complete.
    await vi.waitFor(() => expect(updateSpy).toHaveBeenCalled());
    expect(updateSpy).toHaveBeenCalledWith("tenant-uuid", { display_name: "Renamed" });
  });

  it("shows JSON validation error when meta_data textarea contains invalid JSON", () => {
    render(<TenantSettingsEditForm initialData={INITIAL_DATA} onDone={vi.fn()} />);

    const textarea = screen.getByDisplayValue(/region/);
    fireEvent.change(textarea, { target: { value: "{not valid json" } });
    fireEvent.blur(textarea);

    expect(screen.getByText(/Invalid JSON/)).toBeInTheDocument();
    // Save button should be disabled when JSON is invalid.
    const saveBtn = screen.getByText("Save") as HTMLButtonElement;
    expect(saveBtn.disabled).toBe(true);
  });

  it("View render via TenantSettingsEditForm initialData renders display_name + meta_data", () => {
    render(<TenantSettingsEditForm initialData={INITIAL_DATA} onDone={vi.fn()} />);

    // Display name input has the initial value populated.
    expect(screen.getByDisplayValue("Acme Corp")).toBeInTheDocument();
    // Meta data textarea contains the JSON-stringified meta_data.
    expect(screen.getByDisplayValue(/"region"/)).toBeInTheDocument();
  });
});
