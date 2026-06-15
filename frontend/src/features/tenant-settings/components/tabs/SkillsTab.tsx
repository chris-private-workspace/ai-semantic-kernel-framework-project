/**
 * File: frontend/src/features/tenant-settings/components/tabs/SkillsTab.tsx
 * Purpose: Skills tab — view + create/edit/delete the tenant's custom skills catalog.
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.114 (Per-Tenant Skills Catalog)
 *
 * Description:
 *   Read side: useTenantSkills(tenantId) → GET /admin/tenants/{id}/skills.
 *
 *   Write side: a top "+ Add skill" toggle reveals an inline create form (name +
 *   description + instructions textarea); each list row has Edit (inline form,
 *   one open at a time) + Delete (inline 2-step confirm). Create/update/delete go
 *   through useTenantSkill{Create,Update,Delete}; each invalidates the read so the
 *   list re-fetches. A tenant's custom skill overlays the bundled set per chat
 *   request — a same-name skill shadows a built-in one (e.g. a "code-review"
 *   override). The header shows the per-tenant quota (N / max) + disables Add at the
 *   cap; the instructions textarea caps at the body-size limit (both server-sourced,
 *   Sprint 57.117). Backend errors (409 duplicate / quota, 404 missing, 422 non-kebab /
 *   oversized) surface inline via the same error-banner pattern as the other tabs.
 *
 *   Admin-internal page → mockup-ui Card + grid-main + inline tokens only (no
 *   mockup-fidelity CSS); English copy. Mirrors QuotasTab's view/edit idioms.
 *
 * Created: 2026-06-13 (Sprint 57.114)
 *
 * Modification History (newest-first):
 *   - 2026-06-15: Sprint 57.119 — read-only System Skills section + Preview modal (any skill body)
 *   - 2026-06-15: Sprint 57.117 — N/max count + disable Add at quota + textarea maxLength + counter
 *   - 2026-06-13: Initial creation (Sprint 57.114)
 *
 * Related:
 *   - backend GET/POST/PUT/DELETE /admin/tenants/{id}/skills
 *   - ../../hooks/useTenantSkills.ts (read + 3 mutations)
 *   - ./QuotasTab.tsx (view/edit idiom authority)
 */

import { useEffect, useState } from "react";

import { Button, Card } from "../../../../components/mockup-ui";
import {
  useSystemSkills,
  useTenantSkillCreate,
  useTenantSkillDelete,
  useTenantSkillUpdate,
  useTenantSkills,
} from "../../hooks/useTenantSkills";
import type { Skill } from "../../types";

export interface SkillsTabProps {
  tenantId: string;
}

interface SkillDraft {
  name: string;
  description: string;
  instructions: string;
}

const EMPTY_DRAFT: SkillDraft = { name: "", description: "", instructions: "" };

/** A draft is submittable only when all 3 fields are non-blank. */
function isComplete(draft: SkillDraft): boolean {
  return (
    draft.name.trim() !== "" &&
    draft.description.trim() !== "" &&
    draft.instructions.trim() !== ""
  );
}

export function SkillsTab({ tenantId }: SkillsTabProps): JSX.Element {
  const skills = useTenantSkills(tenantId);
  const createMutation = useTenantSkillCreate(tenantId);
  const updateMutation = useTenantSkillUpdate(tenantId);
  const deleteMutation = useTenantSkillDelete(tenantId);
  // Sprint 57.119: the read-only system-bundled catalog (the base this tenant's skills overlay).
  const systemSkills = useSystemSkills(tenantId);

  const [adding, setAdding] = useState(false);
  const [addDraft, setAddDraft] = useState<SkillDraft>({ ...EMPTY_DRAFT });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<SkillDraft>({ ...EMPTY_DRAFT });

  const [deletingId, setDeletingId] = useState<string | null>(null);
  // Sprint 57.119: the skill whose full instructions the Preview modal renders (null = closed).
  const [previewSkill, setPreviewSkill] = useState<{ name: string; instructions: string } | null>(
    null,
  );

  // Reset all transient UI state on tenant switch.
  useEffect(() => {
    setAdding(false);
    setAddDraft({ ...EMPTY_DRAFT });
    setEditingId(null);
    setEditDraft({ ...EMPTY_DRAFT });
    setDeletingId(null);
    setPreviewSkill(null);
    createMutation.reset();
    updateMutation.reset();
    deleteMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reset on tenant switch only
  }, [tenantId]);

  // Auto-close the add form after a successful create.
  useEffect(() => {
    if (createMutation.isSuccess && adding) {
      setAdding(false);
      setAddDraft({ ...EMPTY_DRAFT });
    }
  }, [createMutation.isSuccess, adding]);

  // Auto-close the edit form after a successful update.
  useEffect(() => {
    if (updateMutation.isSuccess && editingId) {
      setEditingId(null);
      setEditDraft({ ...EMPTY_DRAFT });
    }
  }, [updateMutation.isSuccess, editingId]);

  // Sprint 57.119: close the Preview modal on Escape (the codebase drawer/dialog convention).
  useEffect(() => {
    if (previewSkill === null) return;
    const handler = (e: KeyboardEvent): void => {
      if (e.key === "Escape") setPreviewSkill(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [previewSkill]);

  const items = skills.data?.skills ?? [];
  // Sprint 57.117: the effective per-tenant limits (server-sourced via the list response).
  // Fall back to no cap (Infinity) when absent so an older/cached response never falsely
  // disables Add or caps the textarea.
  const maxSkills = skills.data?.max_skills ?? Infinity;
  const maxInstructionsChars = skills.data?.max_instructions_chars ?? Infinity;
  const atLimit = items.length >= maxSkills;

  const handleAddOpen = (): void => {
    setAddDraft({ ...EMPTY_DRAFT });
    setAdding(true);
    setEditingId(null);
    setDeletingId(null);
    createMutation.reset();
  };

  const handleAddCancel = (): void => {
    setAdding(false);
    setAddDraft({ ...EMPTY_DRAFT });
    createMutation.reset();
  };

  const handleAddSave = (): void => {
    createMutation.mutate({
      name: addDraft.name.trim(),
      description: addDraft.description.trim(),
      instructions: addDraft.instructions.trim(),
    });
  };

  const handleEditOpen = (skill: Skill): void => {
    setEditingId(skill.id);
    setEditDraft({
      name: skill.name,
      description: skill.description,
      instructions: skill.instructions,
    });
    setAdding(false);
    setDeletingId(null);
    updateMutation.reset();
  };

  const handleEditCancel = (): void => {
    setEditingId(null);
    setEditDraft({ ...EMPTY_DRAFT });
    updateMutation.reset();
  };

  const handleEditSave = (skillId: string): void => {
    updateMutation.mutate({
      skillId,
      patch: {
        name: editDraft.name.trim(),
        description: editDraft.description.trim(),
        instructions: editDraft.instructions.trim(),
      },
    });
  };

  const handleDeleteRequest = (skillId: string): void => {
    setDeletingId(skillId);
    deleteMutation.reset();
  };

  const handleDeleteConfirm = (skillId: string): void => {
    deleteMutation.mutate(skillId, {
      onSuccess: () => setDeletingId(null),
    });
  };

  // Shared field editor (used by both the add form and the per-row edit form).
  const renderDraftFields = (
    draft: SkillDraft,
    setDraft: (next: SkillDraft) => void,
    idPrefix: string,
  ): JSX.Element => (
    // eslint-disable-next-line no-restricted-syntax -- inline-style: form column gap
    <div className="col" style={{ gap: 8, marginTop: 8 }}>
      <input
        type="text"
        value={draft.name}
        placeholder="kebab-name (e.g. release-notes)"
        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        // eslint-disable-next-line no-restricted-syntax -- inline-style: input sizing
        style={{ fontSize: 12, padding: "4px 8px" }}
        data-testid={`${idPrefix}-name`}
        aria-label="Skill name"
      />
      <input
        type="text"
        value={draft.description}
        placeholder="One-line description"
        onChange={(e) => setDraft({ ...draft, description: e.target.value })}
        // eslint-disable-next-line no-restricted-syntax -- inline-style: input sizing
        style={{ fontSize: 12, padding: "4px 8px" }}
        data-testid={`${idPrefix}-description`}
        aria-label="Skill description"
      />
      <textarea
        value={draft.instructions}
        placeholder="Full instructions (read_skill returns this verbatim)"
        onChange={(e) => setDraft({ ...draft, instructions: e.target.value })}
        rows={5}
        maxLength={Number.isFinite(maxInstructionsChars) ? maxInstructionsChars : undefined}
        // eslint-disable-next-line no-restricted-syntax -- inline-style: textarea sizing
        style={{ fontSize: 12, padding: "4px 8px", fontFamily: "inherit" }}
        data-testid={`${idPrefix}-instructions`}
        aria-label="Skill instructions"
      />
      {Number.isFinite(maxInstructionsChars) ? (
        <span
          className="subtle"
          // eslint-disable-next-line no-restricted-syntax -- inline-style: char counter
          style={{ fontSize: 10.5, alignSelf: "flex-end" }}
          data-testid={`${idPrefix}-instructions-counter`}
        >
          {draft.instructions.length} / {maxInstructionsChars}
        </span>
      ) : null}
    </div>
  );

  return (
    <div className="grid-main">
      <Card title="Skills">
        {/* eslint-disable-next-line no-restricted-syntax -- inline-style: hint copy */}
        <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
          Custom skills overlay the built-in set for this tenant. A skill whose
          name matches a built-in one (e.g. <span className="mono">code-review</span>)
          replaces it; others are added. Changes apply on the next chat request.
        </p>

        {/* eslint-disable-next-line no-restricted-syntax -- inline-style: count+action row */}
        <div className="row" style={{ gap: 8, marginBottom: 12, justifyContent: "space-between", alignItems: "center" }}>
          {/* eslint-disable-next-line no-restricted-syntax -- inline-style: count label */}
          <span className="subtle" style={{ fontSize: 11.5 }} data-testid="skills-count">
            {items.length}
            {Number.isFinite(maxSkills) ? ` / ${maxSkills}` : ""} skills
          </span>
          {/* eslint-disable-next-line no-restricted-syntax -- inline-style: right action group */}
          <span className="row" style={{ gap: 8, alignItems: "center" }}>
            {atLimit && !adding ? (
              <span
                className="subtle"
                // eslint-disable-next-line no-restricted-syntax -- inline-style: limit hint colour
                style={{ fontSize: 11.5, color: "var(--danger)" }}
                data-testid="skills-limit-hint"
              >
                Skill limit reached
              </span>
            ) : null}
            {!adding ? (
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddOpen}
                disabled={skills.isLoading || atLimit}
                data-testid="skills-add-btn"
              >
                + Add skill
              </Button>
            ) : null}
          </span>
        </div>

        {adding ? (
          <div
            // eslint-disable-next-line no-restricted-syntax -- inline-style: add-form panel
            style={{
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: 12,
              marginBottom: 14,
            }}
            data-testid="skills-add-form"
          >
            {/* eslint-disable-next-line no-restricted-syntax -- inline-style: form heading */}
            <div style={{ fontSize: 12.5, fontWeight: 600 }}>New skill</div>
            {renderDraftFields(addDraft, setAddDraft, "skills-add")}

            {createMutation.error ? (
              // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
              <p style={{ color: "var(--danger)", fontSize: 12, marginTop: 8 }} data-testid="skills-add-error">
                Create failed: {createMutation.error.message}
              </p>
            ) : null}

            {/* eslint-disable-next-line no-restricted-syntax -- inline-style: action row */}
            <div className="row" style={{ gap: 8, marginTop: 10, justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleAddCancel}
                disabled={createMutation.isPending}
                data-testid="skills-add-cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleAddSave}
                disabled={createMutation.isPending || !isComplete(addDraft)}
                data-testid="skills-add-save-btn"
              >
                {createMutation.isPending ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        ) : null}

        {skills.isLoading ? (
          <p className="muted">Loading skills…</p>
        ) : skills.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }} data-testid="skills-load-error">
            Error loading skills: {skills.error.message}
          </p>
        ) : items.length === 0 ? (
          <p className="muted" data-testid="skills-empty">
            No custom skills — this tenant uses the built-in set only.
          </p>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- inline-style: list column gap
          <div className="col" style={{ gap: 12, marginTop: 8 }} data-testid="skills-list">
            {items.map((skill) =>
              editingId === skill.id ? (
                <div
                  key={skill.id}
                  // eslint-disable-next-line no-restricted-syntax -- inline-style: edit-form panel
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius)",
                    padding: 12,
                  }}
                  data-testid={`skills-edit-form-${skill.name}`}
                >
                  {/* eslint-disable-next-line no-restricted-syntax -- inline-style: form heading */}
                  <div style={{ fontSize: 12.5, fontWeight: 600 }}>Edit skill</div>
                  {renderDraftFields(editDraft, setEditDraft, "skills-edit")}

                  {updateMutation.error ? (
                    // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
                    <p style={{ color: "var(--danger)", fontSize: 12, marginTop: 8 }} data-testid="skills-edit-error">
                      Update failed: {updateMutation.error.message}
                    </p>
                  ) : null}

                  {/* eslint-disable-next-line no-restricted-syntax -- inline-style: action row */}
                  <div className="row" style={{ gap: 8, marginTop: 10, justifyContent: "flex-end" }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={handleEditCancel}
                      disabled={updateMutation.isPending}
                      data-testid="skills-edit-cancel-btn"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => handleEditSave(skill.id)}
                      disabled={updateMutation.isPending || !isComplete(editDraft)}
                      data-testid="skills-edit-save-btn"
                    >
                      {updateMutation.isPending ? "Saving…" : "Save"}
                    </button>
                  </div>
                </div>
              ) : (
                <div key={skill.id} className="spread" data-testid={`skills-row-${skill.name}`}>
                  {/* eslint-disable-next-line no-restricted-syntax -- inline-style: name+desc column */}
                  <div className="col" style={{ gap: 2 }}>
                    {/* eslint-disable-next-line no-restricted-syntax -- inline-style: name fontSize */}
                    <span className="mono" style={{ fontSize: 12.5 }}>{skill.name}</span>
                    {/* eslint-disable-next-line no-restricted-syntax -- inline-style: desc fontSize */}
                    <span className="subtle" style={{ fontSize: 11.5 }}>{skill.description}</span>
                  </div>
                  {deletingId === skill.id ? (
                    // eslint-disable-next-line no-restricted-syntax -- inline-style: confirm row
                    <span className="row" style={{ gap: 6, alignItems: "center" }}>
                      {deleteMutation.error ? (
                        // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
                        <span style={{ color: "var(--danger)", fontSize: 11.5 }} data-testid="skills-delete-error">
                          {deleteMutation.error.message}
                        </span>
                      ) : (
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: confirm prompt
                        <span className="subtle" style={{ fontSize: 11.5 }}>Delete?</span>
                      )}
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => setDeletingId(null)}
                        disabled={deleteMutation.isPending}
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        data-testid={`skills-delete-cancel-${skill.name}`}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() => handleDeleteConfirm(skill.id)}
                        disabled={deleteMutation.isPending}
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        data-testid={`skills-delete-confirm-${skill.name}`}
                      >
                        {deleteMutation.isPending ? "Deleting…" : "Confirm"}
                      </button>
                    </span>
                  ) : (
                    // eslint-disable-next-line no-restricted-syntax -- inline-style: action row
                    <span className="row" style={{ gap: 6, alignItems: "center" }}>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() =>
                          setPreviewSkill({ name: skill.name, instructions: skill.instructions })
                        }
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        data-testid={`skills-preview-btn-${skill.name}`}
                      >
                        Preview
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => handleEditOpen(skill)}
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        data-testid={`skills-edit-btn-${skill.name}`}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => handleDeleteRequest(skill.id)}
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        data-testid={`skills-delete-btn-${skill.name}`}
                      >
                        Delete
                      </button>
                    </span>
                  )}
                </div>
              ),
            )}
          </div>
        )}
      </Card>

      <Card title="System Skills">
        {/* eslint-disable-next-line no-restricted-syntax -- inline-style: hint copy */}
        <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
          Built-in skills available to every tenant. Your custom skills above overlay
          these by name; a <span className="mono">🔧 script</span> skill ships an
          executable the agent can run.
        </p>

        {systemSkills.isLoading ? (
          <p className="muted">Loading system skills…</p>
        ) : systemSkills.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }} data-testid="system-skills-load-error">
            Error loading system skills: {systemSkills.error.message}
          </p>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- inline-style: list column gap
          <div className="col" style={{ gap: 12, marginTop: 4 }} data-testid="system-skills-section">
            {(systemSkills.data?.skills ?? []).map((sys) => (
              <div key={sys.name} className="spread" data-testid={`system-skills-row-${sys.name}`}>
                {/* eslint-disable-next-line no-restricted-syntax -- inline-style: name+desc column */}
                <div className="col" style={{ gap: 2 }}>
                  {/* eslint-disable-next-line no-restricted-syntax -- inline-style: name+badges row */}
                  <span className="row" style={{ gap: 6, alignItems: "center" }}>
                    {/* eslint-disable-next-line no-restricted-syntax -- inline-style: name fontSize */}
                    <span className="mono" style={{ fontSize: 12.5 }}>{sys.name}</span>
                    {sys.has_script ? (
                      <span
                        className="subtle"
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: script badge pill
                        style={{
                          fontSize: 10,
                          padding: "1px 6px",
                          border: "1px solid var(--border)",
                          borderRadius: 4,
                        }}
                        data-testid={`system-skill-script-badge-${sys.name}`}
                      >
                        🔧 script
                      </span>
                    ) : null}
                    {sys.overridden ? (
                      <span
                        className="subtle"
                        // eslint-disable-next-line no-restricted-syntax -- inline-style: shadowed tag
                        style={{ fontSize: 10 }}
                        data-testid={`system-skill-shadowed-${sys.name}`}
                      >
                        shadowed by your skill
                      </span>
                    ) : null}
                  </span>
                  {/* eslint-disable-next-line no-restricted-syntax -- inline-style: desc fontSize */}
                  <span className="subtle" style={{ fontSize: 11.5 }}>{sys.description}</span>
                </div>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() =>
                    setPreviewSkill({ name: sys.name, instructions: sys.instructions })
                  }
                  // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                  style={{ fontSize: 11, padding: "2px 8px" }}
                  data-testid={`system-skill-preview-btn-${sys.name}`}
                >
                  Preview
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {previewSkill ? (
        // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions -- backdrop overlay; Escape-key handler attached via the window listener above; the Close button + Escape are the keyboard paths
        <div
          // eslint-disable-next-line no-restricted-syntax -- inline-style: modal backdrop (no Modal primitive)
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            zIndex: 50,
          }}
          onClick={() => setPreviewSkill(null)}
          data-testid="skill-preview-modal"
        >
          {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions -- stop-propagation div; role=dialog provides the accessible name; the inner Close button is keyboard-accessible */}
          <div
            // eslint-disable-next-line no-restricted-syntax -- inline-style: modal panel
            style={{
              background: "var(--bg)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              boxShadow: "var(--shadow)",
              width: "100%",
              maxWidth: 640,
              maxHeight: "80vh",
              display: "flex",
              flexDirection: "column",
              padding: 16,
            }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Skill preview"
          >
            {/* eslint-disable-next-line no-restricted-syntax -- inline-style: modal header row */}
            <div className="spread" style={{ marginBottom: 10, alignItems: "center" }}>
              {/* eslint-disable-next-line no-restricted-syntax -- inline-style: modal title */}
              <span className="mono" style={{ fontSize: 13, fontWeight: 600 }}>
                {previewSkill.name}
              </span>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setPreviewSkill(null)}
                // eslint-disable-next-line no-restricted-syntax -- inline-style: btn sizing
                style={{ fontSize: 11, padding: "2px 8px" }}
                data-testid="skill-preview-close-btn"
              >
                Close
              </button>
            </div>
            <pre
              className="mono"
              // eslint-disable-next-line no-restricted-syntax -- inline-style: preview body
              style={{
                margin: 0,
                fontSize: 12,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                overflowY: "auto",
                maxHeight: "64vh",
              }}
              data-testid="skill-preview-body"
            >
              {previewSkill.instructions}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
