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
        className="flex flex-wrap items-end gap-3 rounded border border-border bg-card p-3"
      >
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-xs font-medium text-muted-foreground">Session ID</span>
          <input
            type="text"
            value={draftForm.session_id}
            onChange={(e) => setDraftForm({ ...draftForm, session_id: e.target.value })}
            placeholder="UUID..."
            className="rounded border border-input bg-background px-2 py-1 text-sm"
            data-testid="filter-session-id"
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-xs font-medium text-muted-foreground">Verifier Type</span>
          <select
            value={draftForm.verifier_type}
            onChange={(e) =>
              setDraftForm({ ...draftForm, verifier_type: e.target.value as VerifierType | "" })
            }
            className="rounded border border-input bg-background px-2 py-1 text-sm"
            data-testid="filter-verifier-type"
          >
            <option value="">Any</option>
            <option value="rules_based">Rules</option>
            <option value="llm_judge">LLM Judge</option>
            <option value="external">External</option>
          </select>
        </label>
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-xs font-medium text-muted-foreground">Passed</span>
          <select
            value={draftForm.passed}
            onChange={(e) =>
              setDraftForm({ ...draftForm, passed: e.target.value as FormState["passed"] })
            }
            className="rounded border border-input bg-background px-2 py-1 text-sm"
            data-testid="filter-passed"
          >
            <option value="any">Any</option>
            <option value="true">Passed</option>
            <option value="false">Failed</option>
          </select>
        </label>
        <button
          type="submit"
          className="rounded bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground"
          data-testid="filter-apply"
        >
          Apply
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="rounded border border-input bg-background px-3 py-1.5 text-sm"
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
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          <p>Error: {query.error.message}</p>
          <button
            type="button"
            onClick={handleRetry}
            className="mt-2 rounded bg-red-600 px-2 py-1 text-xs font-medium text-white"
            data-testid="error-retry"
          >
            Retry{retryClicked ? "ing..." : ""}
          </button>
        </div>
      )}

      {query.isSuccess && query.data.items.length === 0 && (
        <div className="rounded border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">No verification entries match the filters.</p>
          <button
            type="button"
            onClick={handleReset}
            className="mt-2 rounded border border-input bg-background px-3 py-1 text-xs"
            data-testid="empty-reset"
          >
            Reset Filters
          </button>
        </div>
      )}

      {query.isSuccess && query.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded border border-border">
            <table className="min-w-full text-sm" data-testid="verification-table">
              <thead className="bg-muted text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">Timestamp</th>
                  <th className="px-3 py-2">Session</th>
                  <th className="px-3 py-2">Verifier</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Outcome</th>
                  <th className="px-3 py-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() =>
                      navigate(`/verification/timeline?session_id=${item.session_id}`)
                    }
                    className="cursor-pointer border-t border-border hover:bg-muted/30"
                    data-testid={`row-${item.id}`}
                  >
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {new Date(item.created_at_ms).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {item.session_id.slice(0, 8)}…
                    </td>
                    <td className="px-3 py-2">{item.verifier_name}</td>
                    <td className="px-3 py-2">
                      <VerifierTypeBadge type={item.verifier_type} />
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${
                          item.passed
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {item.passed ? "Passed" : "Failed"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {_truncate(item.reason, REASON_SNIPPET_MAX)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination footer */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Showing {offset + 1}–{offset + query.data.items.length} of {query.data.total}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded border border-input bg-background px-3 py-1 text-xs disabled:opacity-50"
                data-testid="pagination-prev"
              >
                Prev
              </button>
              <button
                type="button"
                disabled={!query.data.has_more}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded border border-input bg-background px-3 py-1 text-xs disabled:opacity-50"
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
