/**
 * File: frontend/src/features/verification/components/VerificationList.tsx
 * Purpose: Paginated verification log table with filter form (US-4 standalone admin page).
 * Category: Frontend / verification / components
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-4 §3.1
 *
 * Description:
 *   Composed UI:
 *     - Filter form: 3 fields (session_id text input / verifier_type dropdown
 *       / passed dropdown {Any / Passed / Failed}) + Apply / Reset buttons
 *     - Paginated table: 50 rows default; 6 columns (timestamp / session_id
 *       truncated / verifier_name / VerifierTypeBadge / passed badge / reason
 *       snippet 80 chars)
 *     - Click row → navigate to /verification/timeline?session_id={id}
 *     - Empty state with Reset Filters button
 *     - Loading skeleton (5-row mirror Sprint 57.9 ApprovalList pattern)
 *     - Error retry UX with retryClicked flag (Sprint 57.9 D-PRE-15 lesson)
 *     - Prev / Next pagination footer
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-card/text-muted-foreground/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-24: Sprint 57.33 Day 3 US-D1 — defensive ?? [] on items.length/map (4 sites L186/200/215/257; AD-Overview-PreExisting-Route-Crashes)
 *   - 2026-05-10: Initial creation (Sprint 57.11 Day 3 §3.1)
 *
 * Related:
 *   - ../hooks/useVerificationRecent.ts
 *   - ./VerifierTypeBadge.tsx
 *   - ../types.ts
 */

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Skeleton } from "../../../components/ui";
import { useVerificationRecent } from "../hooks/useVerificationRecent";
import type { VerificationLogFilter, VerifierType } from "../types";
import { VerifierTypeBadge } from "./VerifierTypeBadge";

const PAGE_SIZE = 50;
const REASON_SNIPPET_MAX = 80;

type FormState = {
  session_id: string;
  verifier_type: VerifierType | "";
  passed: "any" | "true" | "false";
};

const _initialForm: FormState = {
  session_id: "",
  verifier_type: "",
  passed: "any",
};

function _formToFilter(form: FormState, offset: number): VerificationLogFilter {
  const filter: VerificationLogFilter = {
    limit: PAGE_SIZE,
    offset,
  };
  if (form.session_id.trim() !== "") filter.session_id = form.session_id.trim();
  if (form.verifier_type !== "") filter.verifier_type = form.verifier_type;
  if (form.passed !== "any") filter.passed = form.passed === "true";
  return filter;
}

function _truncate(text: string | null, max: number): string {
  if (text === null) return "";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}

export function VerificationList(): JSX.Element {
  const [appliedForm, setAppliedForm] = useState<FormState>(_initialForm);
  const [draftForm, setDraftForm] = useState<FormState>(_initialForm);
  const [offset, setOffset] = useState(0);
  const [retryClicked, setRetryClicked] = useState(false);
  const navigate = useNavigate();

  const filter = useMemo(() => _formToFilter(appliedForm, offset), [appliedForm, offset]);
  const query = useVerificationRecent(filter);

  function handleApply(e: React.FormEvent) {
    e.preventDefault();
    setAppliedForm(draftForm);
    setOffset(0);
    setRetryClicked(false);
  }

  function handleReset() {
    setDraftForm(_initialForm);
    setAppliedForm(_initialForm);
    setOffset(0);
    setRetryClicked(false);
  }

  function handleRetry() {
    setRetryClicked(true);
    void query.refetch();
  }

  return (
    <div className="space-y-4" data-testid="verification-list">
      {/* Filter form */}
      <form
        onSubmit={handleApply}
        className="card flex flex-wrap items-end gap-3"
        style={{ padding: 12 }}
      >
        <label className="field">
          <span className="field-label">Session ID</span>
          <input
            type="text"
            value={draftForm.session_id}
            onChange={(e) => setDraftForm({ ...draftForm, session_id: e.target.value })}
            placeholder="UUID..."
            className="input"
            data-testid="filter-session-id"
          />
        </label>
        <label className="field">
          <span className="field-label">Verifier Type</span>
          <select
            value={draftForm.verifier_type}
            onChange={(e) =>
              setDraftForm({ ...draftForm, verifier_type: e.target.value as VerifierType | "" })
            }
            className="select"
            data-testid="filter-verifier-type"
          >
            <option value="">Any</option>
            <option value="rules_based">Rules</option>
            <option value="llm_judge">LLM Judge</option>
            <option value="external">External</option>
          </select>
        </label>
        <label className="field">
          <span className="field-label">Passed</span>
          <select
            value={draftForm.passed}
            onChange={(e) =>
              setDraftForm({ ...draftForm, passed: e.target.value as FormState["passed"] })
            }
            className="select"
            data-testid="filter-passed"
          >
            <option value="any">Any</option>
            <option value="true">Passed</option>
            <option value="false">Failed</option>
          </select>
        </label>
        <button type="submit" className="btn primary" data-testid="filter-apply">
          Apply
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="btn outline"
          data-testid="filter-reset"
        >
          Reset
        </button>
      </form>

      {/* Result region */}
      {query.isLoading && (
        <div className="space-y-2" data-testid="loading-skeleton">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      )}

      {query.isError && (
        <div
          className="card"
          style={{
            padding: 12,
            borderColor: "oklch(from var(--danger) l c h / 0.4)",
            background: "oklch(from var(--danger) l c h / 0.08)",
            color: "var(--danger)",
            fontSize: 13,
          }}
        >
          <p>Error: {query.error.message}</p>
          <button
            type="button"
            onClick={handleRetry}
            className="btn danger mt-2"
            data-testid="error-retry"
          >
            Retry{retryClicked ? "ing..." : ""}
          </button>
        </div>
      )}

      {query.isSuccess && (query.data.items ?? []).length === 0 && (
        <div className="card" style={{ padding: 24, textAlign: "center" }}>
          <p className="subtle text-sm">No verification entries match the filters.</p>
          <button
            type="button"
            onClick={handleReset}
            className="btn outline mt-2"
            data-testid="empty-reset"
          >
            Reset Filters
          </button>
        </div>
      )}

      {query.isSuccess && (query.data.items ?? []).length > 0 && (
        <>
          <div className="card" style={{ padding: 0, overflowX: "auto" }}>
            <table className="table" data-testid="verification-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Session</th>
                  <th>Verifier</th>
                  <th>Type</th>
                  <th>Outcome</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {(query.data.items ?? []).map((item) => (
                  <tr
                    key={item.id}
                    onClick={() =>
                      navigate(`/verification/timeline?session_id=${item.session_id}`)
                    }
                    data-testid={`row-${item.id}`}
                  >
                    <td className="subtle" style={{ fontSize: 11 }}>
                      {new Date(item.created_at_ms).toLocaleString()}
                    </td>
                    <td className="mono" style={{ fontSize: 11 }}>
                      {item.session_id.slice(0, 8)}…
                    </td>
                    <td>{item.verifier_name}</td>
                    <td>
                      <VerifierTypeBadge type={item.verifier_type} />
                    </td>
                    <td>
                      <span className={`badge ${item.passed ? "success" : "danger"}`}>
                        {item.passed ? "Passed" : "Failed"}
                      </span>
                    </td>
                    <td className="subtle" style={{ fontSize: 11 }}>
                      {_truncate(item.reason, REASON_SNIPPET_MAX)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination footer */}
          <div className="spread" style={{ fontSize: 13 }}>
            <span className="subtle">
              Showing {offset + 1}–{offset + (query.data.items ?? []).length} of {query.data.total}
            </span>
            <div className="row" style={{ gap: 8 }}>
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="btn outline"
                data-testid="pagination-prev"
              >
                Prev
              </button>
              <button
                type="button"
                disabled={!query.data.has_more}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="btn outline"
                data-testid="pagination-next"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
