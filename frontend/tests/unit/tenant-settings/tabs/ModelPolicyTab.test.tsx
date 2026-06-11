/**
 * File: frontend/tests/unit/tenant-settings/tabs/ModelPolicyTab.test.tsx
 * Purpose: Vitest coverage for ModelPolicyTab — view/edit + Save PUT + 422 inline error.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.104 C1 (Model Policy tab)
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Initial creation (Sprint 57.104 C1)
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/ModelPolicyTab.tsx
 *   - ./QuotasTab.test.tsx (mock structure authority)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/tenant-settings/hooks/useModelPolicy", () => ({
  useModelPolicy: vi.fn(),
  MODEL_POLICY_QUERY_KEY_BASE: ["tenant-settings", "model-policy"],
}));
vi.mock("@/features/tenant-settings/hooks/useModelPolicySave", () => ({
  useModelPolicySave: vi.fn(),
}));

import { ModelPolicyTab } from "@/features/tenant-settings/components/tabs/ModelPolicyTab";
import { useModelPolicy } from "@/features/tenant-settings/hooks/useModelPolicy";
import { useModelPolicySave } from "@/features/tenant-settings/hooks/useModelPolicySave";
import type { ModelPolicy } from "@/features/tenant-settings/types";

function mockSave(
  overrides: Partial<{
    mutate: ReturnType<typeof vi.fn>;
    isPending: boolean;
    isSuccess: boolean;
    error: Error | null;
    reset: ReturnType<typeof vi.fn>;
  }> = {},
): void {
  vi.mocked(useModelPolicySave).mockReturnValue({
    mutate: overrides.mutate ?? vi.fn(),
    isPending: overrides.isPending ?? false,
    isSuccess: overrides.isSuccess ?? false,
    error: overrides.error ?? null,
    reset: overrides.reset ?? vi.fn(),
  } as unknown as ReturnType<typeof useModelPolicySave>);
}

function mockPolicy(
  policy: ModelPolicy | undefined,
  overrides: Partial<{ isLoading: boolean; error: Error | null }> = {},
): void {
  vi.mocked(useModelPolicy).mockReturnValue({
    data: policy,
    isLoading: overrides.isLoading ?? false,
    error: overrides.error ?? null,
  } as unknown as ReturnType<typeof useModelPolicy>);
}

const SPARSE_POLICY: ModelPolicy = {
  actionDeployment: null,
  actionModel: null,
  cheapDeployment: null,
  cheapModel: null,
};

const FULL_POLICY: ModelPolicy = {
  actionDeployment: "gpt-5.2-prod",
  actionModel: "gpt-5.2",
  cheapDeployment: "gpt-5.2-mini-prod",
  cheapModel: "gpt-5.2-mini",
};

describe("ModelPolicyTab (Sprint 57.104 C1)", () => {
  beforeEach(() => {
    mockPolicy(SPARSE_POLICY);
    mockSave();
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the 'Model policy' Card title", () => {
    render(<ModelPolicyTab tenantId="t1" />);
    expect(screen.getByText("Model policy")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    mockPolicy(undefined, { isLoading: true });
    render(<ModelPolicyTab tenantId="t1" />);
    expect(screen.getByText(/Loading model policy/)).toBeInTheDocument();
  });

  it("renders load-error state", () => {
    mockPolicy(undefined, { error: new Error("HTTP 404: tenant not found") });
    render(<ModelPolicyTab tenantId="t1" />);
    const err = screen.getByTestId("model-policy-load-error");
    expect(err).toBeInTheDocument();
    expect(err).toHaveTextContent(/tenant not found/);
  });

  it("view mode: sparse policy renders 'System default' for unset fields", () => {
    mockPolicy(SPARSE_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    const values = screen.getAllByText("System default");
    expect(values.length).toBe(4);
    expect(screen.getByTestId("model-policy-value-action-deployment")).toHaveTextContent(
      "System default",
    );
  });

  it("view mode: set fields render their current value", () => {
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    expect(screen.getByTestId("model-policy-value-action-deployment")).toHaveTextContent(
      "gpt-5.2-prod",
    );
    expect(screen.getByTestId("model-policy-value-action-model")).toHaveTextContent("gpt-5.2");
    expect(screen.getByTestId("model-policy-value-cheap-deployment")).toHaveTextContent(
      "gpt-5.2-mini-prod",
    );
    expect(screen.getByTestId("model-policy-value-cheap-model")).toHaveTextContent(
      "gpt-5.2-mini",
    );
  });

  it("Edit button disabled while loading, enabled once loaded", () => {
    mockPolicy(undefined, { isLoading: true });
    const { rerender } = render(<ModelPolicyTab tenantId="t1" />);
    // Header Edit button still mounts during load (the loading guard only hides
    // the field list), but is disabled by policyQuery.isLoading.
    expect(screen.getByTestId("model-policy-edit-btn")).toBeDisabled();

    mockPolicy(FULL_POLICY);
    rerender(<ModelPolicyTab tenantId="t1" />);
    expect(screen.getByTestId("model-policy-edit-btn")).not.toBeDisabled();
  });

  it("entering edit mode reveals Save/Cancel + 4 text inputs seeded from current policy", () => {
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));

    expect(screen.getByTestId("model-policy-save-btn")).toBeInTheDocument();
    expect(screen.getByTestId("model-policy-cancel-btn")).toBeInTheDocument();

    const actionDep = screen.getByTestId("model-policy-input-action-deployment") as HTMLInputElement;
    const actionModel = screen.getByTestId("model-policy-input-action-model") as HTMLInputElement;
    const cheapDep = screen.getByTestId("model-policy-input-cheap-deployment") as HTMLInputElement;
    const cheapModel = screen.getByTestId("model-policy-input-cheap-model") as HTMLInputElement;
    expect(actionDep.value).toBe("gpt-5.2-prod");
    expect(actionModel.value).toBe("gpt-5.2");
    expect(cheapDep.value).toBe("gpt-5.2-mini-prod");
    expect(cheapModel.value).toBe("gpt-5.2-mini");
  });

  it("edit mode seeds blank inputs from a sparse policy (null → '')", () => {
    mockPolicy(SPARSE_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));
    const actionDep = screen.getByTestId("model-policy-input-action-deployment") as HTMLInputElement;
    expect(actionDep.value).toBe("");
  });

  it("changing an input updates the draft for that field", () => {
    mockPolicy(SPARSE_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));
    const actionDep = screen.getByTestId("model-policy-input-action-deployment") as HTMLInputElement;
    fireEvent.change(actionDep, { target: { value: "gpt-5.2-prod" } });
    expect(actionDep.value).toBe("gpt-5.2-prod");
  });

  it("Save button calls putModelPolicy mutation with the current draft", () => {
    const mutate = vi.fn();
    mockSave({ mutate });
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);

    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));
    fireEvent.click(screen.getByTestId("model-policy-save-btn"));

    expect(mutate).toHaveBeenCalledWith({
      actionDeployment: "gpt-5.2-prod",
      actionModel: "gpt-5.2",
      cheapDeployment: "gpt-5.2-mini-prod",
      cheapModel: "gpt-5.2-mini",
    });
  });

  it("Cancel button resets the draft + exits edit mode", () => {
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));
    fireEvent.click(screen.getByTestId("model-policy-cancel-btn"));

    expect(screen.queryByTestId("model-policy-save-btn")).toBeNull();
    expect(screen.queryByTestId("model-policy-cancel-btn")).toBeNull();
    expect(screen.getByTestId("model-policy-edit-btn")).toBeInTheDocument();
  });

  it("Save button disabled + 'Saving…' label while mutation isPending", () => {
    mockSave({ isPending: true });
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));

    const saveBtn = screen.getByTestId("model-policy-save-btn");
    expect(saveBtn).toBeDisabled();
    expect(saveBtn).toHaveTextContent(/Saving…/);
    expect(screen.getByTestId("model-policy-cancel-btn")).toBeDisabled();
  });

  it("surfaces a 422 save error inline (the detail string)", () => {
    mockSave({ error: new Error("HTTP 422: unknown model 'gpt-99'") });
    mockPolicy(FULL_POLICY);
    render(<ModelPolicyTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("model-policy-edit-btn"));

    const err = screen.getByTestId("model-policy-save-error");
    expect(err).toBeInTheDocument();
    expect(err).toHaveTextContent(/unknown model/);
  });
});
