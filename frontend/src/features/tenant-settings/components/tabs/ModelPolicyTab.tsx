/**
 * File: frontend/src/features/tenant-settings/components/tabs/ModelPolicyTab.tsx
 * Purpose: Model Policy tab — view/edit the tenant's action + cheap model tier selection.
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.104 C1 (Model Policy tab)
 *
 * Description:
 *   Read side: useModelPolicy(tenantId) → GET /admin/tenants/{id}/model-policy
 *   (sparse: unset fields render "System default").
 *
 *   Write side: Edit button toggles edit mode; 4 text inputs (action deployment,
 *   action model, cheap deployment, cheap model) mutate a local draft. Save
 *   invokes useModelPolicySave → PUT (composite-replace: blank fields are cleared
 *   server-side, reverting to the system default). A 422 (`detail` string —
 *   unknown/unpriced model OR unknown field) surfaces inline via the same error
 *   banner pattern as QuotasTab. Cancel restores the loaded policy and exits.
 *
 *   Mirrors the QuotasTab Usage-quotas-Card view/edit structure (Sprint 57.56).
 *
 * Created: 2026-06-11 (Sprint 57.104 C1)
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Initial creation (Sprint 57.104 C1)
 *
 * Related:
 *   - backend GET/PUT /admin/tenants/{id}/model-policy
 *   - ../../hooks/useModelPolicy.ts + useModelPolicySave.ts (read/write)
 *   - ./QuotasTab.tsx (view/edit pattern authority)
 */

import { useEffect, useState } from "react";

import { Card } from "../../../../components/mockup-ui";
import { useModelPolicy } from "../../hooks/useModelPolicy";
import { useModelPolicySave } from "../../hooks/useModelPolicySave";
import type { ModelPolicy } from "../../types";

export interface ModelPolicyTabProps {
  tenantId: string;
}

type ModelPolicyField = keyof ModelPolicy;

/** Edit draft: same fields as ModelPolicy but never-null (text inputs need string). */
type ModelPolicyDraft = Record<ModelPolicyField, string>;

const EMPTY_DRAFT: ModelPolicyDraft = {
  actionDeployment: "",
  actionModel: "",
  cheapDeployment: "",
  cheapModel: "",
};

/** The 4 policy fields in display order — label + testid suffix + draft key. */
const POLICY_FIELDS: ReadonlyArray<{
  key: ModelPolicyField;
  label: string;
  testid: string;
}> = [
  { key: "actionDeployment", label: "Action deployment", testid: "action-deployment" },
  { key: "actionModel", label: "Action model", testid: "action-model" },
  { key: "cheapDeployment", label: "Cheap deployment", testid: "cheap-deployment" },
  { key: "cheapModel", label: "Cheap model", testid: "cheap-model" },
];

/** Seed an editable draft from the loaded policy (null → "" for inputs). */
function draftFromPolicy(policy: ModelPolicy | undefined): ModelPolicyDraft {
  if (!policy) return { ...EMPTY_DRAFT };
  return {
    actionDeployment: policy.actionDeployment ?? "",
    actionModel: policy.actionModel ?? "",
    cheapDeployment: policy.cheapDeployment ?? "",
    cheapModel: policy.cheapModel ?? "",
  };
}

export function ModelPolicyTab({ tenantId }: ModelPolicyTabProps): JSX.Element {
  const policyQuery = useModelPolicy(tenantId);
  const saveMutation = useModelPolicySave(tenantId);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<ModelPolicyDraft>({ ...EMPTY_DRAFT });

  // Reset on tenant switch
  useEffect(() => {
    setEditing(false);
    setDraft({ ...EMPTY_DRAFT });
    saveMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutation reset on tenant switch only
  }, [tenantId]);

  // Auto-exit edit mode after successful save
  useEffect(() => {
    if (saveMutation.isSuccess && editing) {
      setEditing(false);
    }
  }, [saveMutation.isSuccess, editing]);

  const policy = policyQuery.data;

  const handleEdit = (): void => {
    setDraft(draftFromPolicy(policy));
    setEditing(true);
    saveMutation.reset();
  };

  const handleCancel = (): void => {
    setDraft(draftFromPolicy(policy));
    setEditing(false);
    saveMutation.reset();
  };

  const handleSave = (): void => {
    saveMutation.mutate(draft);
  };

  const updateDraft = (field: ModelPolicyField, value: string): void => {
    setDraft((d) => ({ ...d, [field]: value }));
  };

  return (
    <div className="grid-main">
      <Card title="Model policy">
        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row flex gap */}
        <div className="row" style={{ gap: 8, marginBottom: 12, justifyContent: "flex-end" }}>
          {!editing ? (
            <button
              type="button"
              className="btn-secondary"
              onClick={handleEdit}
              disabled={policyQuery.isLoading}
              data-testid="model-policy-edit-btn"
            >
              Edit
            </button>
          ) : (
            <>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleCancel}
                disabled={saveMutation.isPending}
                data-testid="model-policy-cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending}
                data-testid="model-policy-save-btn"
              >
                {saveMutation.isPending ? "Saving…" : "Save"}
              </button>
            </>
          )}
        </div>

        {saveMutation.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12, marginBottom: 8 }} data-testid="model-policy-save-error">
            Save failed: {saveMutation.error.message}
          </p>
        ) : null}

        {policyQuery.isLoading ? (
          <p className="muted">Loading model policy…</p>
        ) : policyQuery.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }} data-testid="model-policy-load-error">
            Error loading model policy: {policyQuery.error.message}
          </p>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap
          <div className="col" style={{ gap: 14, marginTop: 8 }}>
            {POLICY_FIELDS.map((field) => {
              const currentValue = policy ? policy[field.key] : null;
              return (
                <div key={field.key} className="spread">
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fontSize */}
                  <span style={{ fontSize: 12.5 }}>{field.label}</span>
                  {editing ? (
                    <input
                      type="text"
                      value={draft[field.key]}
                      placeholder="System default"
                      onChange={(e) => updateDraft(field.key, e.target.value)}
                      // eslint-disable-next-line no-restricted-syntax -- verbatim port: input sizing
                      style={{ width: 220, fontSize: 12, padding: "2px 6px" }}
                      data-testid={`model-policy-input-${field.testid}`}
                      aria-label={`${field.label} override`}
                    />
                  ) : currentValue ? (
                    // eslint-disable-next-line no-restricted-syntax -- verbatim port: mono fontSize
                    <span className="mono" style={{ fontSize: 11.5 }} data-testid={`model-policy-value-${field.testid}`}>
                      {currentValue}
                    </span>
                  ) : (
                    <span
                      className="subtle"
                      data-testid={`model-policy-value-${field.testid}`}
                    >
                      System default
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
