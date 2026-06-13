/**
 * File: frontend/tests/unit/tenant-settings/tabs/SkillsTab.test.tsx
 * Purpose: Vitest coverage for SkillsTab — list + Add/Edit/Delete CRUD + inline errors.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.114 (Per-Tenant Skills Catalog)
 *
 * Modification History (newest-first):
 *   - 2026-06-13: Initial creation (Sprint 57.114)
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx
 *   - ./ModelPolicyTab.test.tsx (mock structure authority)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/tenant-settings/hooks/useTenantSkills", () => ({
  useTenantSkills: vi.fn(),
  useTenantSkillCreate: vi.fn(),
  useTenantSkillUpdate: vi.fn(),
  useTenantSkillDelete: vi.fn(),
  TENANT_SKILLS_QUERY_KEY_BASE: ["tenant-settings", "skills"],
}));

import { SkillsTab } from "@/features/tenant-settings/components/tabs/SkillsTab";
import {
  useTenantSkillCreate,
  useTenantSkillDelete,
  useTenantSkillUpdate,
  useTenantSkills,
} from "@/features/tenant-settings/hooks/useTenantSkills";
import type { Skill, SkillListResponse } from "@/features/tenant-settings/types";

type MutationOverrides = Partial<{
  mutate: ReturnType<typeof vi.fn>;
  isPending: boolean;
  isSuccess: boolean;
  error: Error | null;
  reset: ReturnType<typeof vi.fn>;
}>;

function mockMutation(
  hook:
    | typeof useTenantSkillCreate
    | typeof useTenantSkillUpdate
    | typeof useTenantSkillDelete,
  overrides: MutationOverrides = {},
): void {
  vi.mocked(hook).mockReturnValue({
    mutate: overrides.mutate ?? vi.fn(),
    isPending: overrides.isPending ?? false,
    isSuccess: overrides.isSuccess ?? false,
    error: overrides.error ?? null,
    reset: overrides.reset ?? vi.fn(),
  } as unknown as ReturnType<typeof hook>);
}

function mockSkills(
  data: SkillListResponse | undefined,
  overrides: Partial<{ isLoading: boolean; error: Error | null }> = {},
): void {
  vi.mocked(useTenantSkills).mockReturnValue({
    data,
    isLoading: overrides.isLoading ?? false,
    error: overrides.error ?? null,
  } as unknown as ReturnType<typeof useTenantSkills>);
}

const SKILL_A: Skill = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "release-notes",
  description: "Turn a changelog into a release note",
  instructions: "Heading / Highlights / Upgrade notes",
  created_at: "2026-06-13T00:00:00Z",
  updated_at: "2026-06-13T00:00:00Z",
};

describe("SkillsTab (Sprint 57.114)", () => {
  beforeEach(() => {
    mockSkills({ skills: [SKILL_A] });
    mockMutation(useTenantSkillCreate);
    mockMutation(useTenantSkillUpdate);
    mockMutation(useTenantSkillDelete);
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the 'Skills' Card title", () => {
    render(<SkillsTab tenantId="t1" />);
    expect(screen.getByText("Skills")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    mockSkills(undefined, { isLoading: true });
    render(<SkillsTab tenantId="t1" />);
    expect(screen.getByText(/Loading skills/)).toBeInTheDocument();
  });

  it("renders load-error state", () => {
    mockSkills(undefined, { error: new Error("HTTP 404: tenant not found") });
    render(<SkillsTab tenantId="t1" />);
    expect(screen.getByTestId("skills-load-error")).toHaveTextContent(/tenant not found/);
  });

  it("renders the empty state when the tenant has no custom skills", () => {
    mockSkills({ skills: [] });
    render(<SkillsTab tenantId="t1" />);
    expect(screen.getByTestId("skills-empty")).toBeInTheDocument();
  });

  it("lists the tenant's skills (name + description)", () => {
    render(<SkillsTab tenantId="t1" />);
    const row = screen.getByTestId("skills-row-release-notes");
    expect(row).toHaveTextContent("release-notes");
    expect(row).toHaveTextContent("Turn a changelog into a release note");
  });

  it("Add button opens the create form (3 fields)", () => {
    render(<SkillsTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("skills-add-btn"));
    expect(screen.getByTestId("skills-add-form")).toBeInTheDocument();
    expect(screen.getByTestId("skills-add-name")).toBeInTheDocument();
    expect(screen.getByTestId("skills-add-description")).toBeInTheDocument();
    expect(screen.getByTestId("skills-add-instructions")).toBeInTheDocument();
  });

  it("Save is disabled until all 3 fields are filled, then calls create", () => {
    const mutate = vi.fn();
    mockMutation(useTenantSkillCreate, { mutate });
    render(<SkillsTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("skills-add-btn"));

    const saveBtn = screen.getByTestId("skills-add-save-btn");
    expect(saveBtn).toBeDisabled();

    fireEvent.change(screen.getByTestId("skills-add-name"), { target: { value: "deploy-notes" } });
    fireEvent.change(screen.getByTestId("skills-add-description"), { target: { value: "Deploy summary" } });
    fireEvent.change(screen.getByTestId("skills-add-instructions"), { target: { value: "Steps / Rollback" } });
    expect(saveBtn).not.toBeDisabled();

    fireEvent.click(saveBtn);
    expect(mutate).toHaveBeenCalledWith({
      name: "deploy-notes",
      description: "Deploy summary",
      instructions: "Steps / Rollback",
    });
  });

  it("surfaces a create error inline (the detail string)", () => {
    mockMutation(useTenantSkillCreate, { error: new Error("HTTP 409: skill 'release-notes' already exists") });
    render(<SkillsTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("skills-add-btn"));
    expect(screen.getByTestId("skills-add-error")).toHaveTextContent(/already exists/);
  });

  it("Edit opens a seeded form; Save calls update with the skill id + patch", () => {
    const mutate = vi.fn();
    mockMutation(useTenantSkillUpdate, { mutate });
    render(<SkillsTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("skills-edit-btn-release-notes"));

    const nameInput = screen.getByTestId("skills-edit-name") as HTMLInputElement;
    expect(nameInput.value).toBe("release-notes");
    fireEvent.change(screen.getByTestId("skills-edit-description"), {
      target: { value: "Updated description" },
    });
    fireEvent.click(screen.getByTestId("skills-edit-save-btn"));

    expect(mutate).toHaveBeenCalledWith({
      skillId: SKILL_A.id,
      patch: {
        name: "release-notes",
        description: "Updated description",
        instructions: "Heading / Highlights / Upgrade notes",
      },
    });
  });

  it("Delete is a 2-step confirm; Confirm calls delete with the skill id", () => {
    const mutate = vi.fn();
    mockMutation(useTenantSkillDelete, { mutate });
    render(<SkillsTab tenantId="t1" />);

    // First click → confirm affordance appears (no mutate yet).
    fireEvent.click(screen.getByTestId("skills-delete-btn-release-notes"));
    expect(mutate).not.toHaveBeenCalled();
    const confirmBtn = screen.getByTestId("skills-delete-confirm-release-notes");
    expect(confirmBtn).toBeInTheDocument();

    // Confirm → mutate(id, {onSuccess}).
    fireEvent.click(confirmBtn);
    expect(mutate).toHaveBeenCalledWith(SKILL_A.id, expect.objectContaining({ onSuccess: expect.any(Function) }));
  });

  it("surfaces a delete error inline", () => {
    mockMutation(useTenantSkillDelete, { error: new Error("HTTP 404: skill not found") });
    render(<SkillsTab tenantId="t1" />);
    fireEvent.click(screen.getByTestId("skills-delete-btn-release-notes"));
    expect(screen.getByTestId("skills-delete-error")).toHaveTextContent(/skill not found/);
  });
});
