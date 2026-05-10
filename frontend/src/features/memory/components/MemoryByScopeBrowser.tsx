/**
 * File: frontend/src/features/memory/components/MemoryByScopeBrowser.tsx
 * Purpose: 5-layer card view + drill-into-scope detail panel (US-5 by-scope tab).
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.12 Day 2-3 / US-5
 *
 * Description:
 *   Two-pane browser:
 *     - Left: 5 layer cards (system / tenant / role / user / session). The 3
 *       wired layers (system / tenant / user) are clickable; role + session
 *       show "(Phase 58+)" and are disabled.
 *     - Right: detail panel. When a layer is picked:
 *         · system → directly queries /scope/system/_ (scope_id ignored by
 *           backend) and lists entries.
 *         · tenant / user → shows a scope_id input box (UUID); on submit,
 *           queries /scope/{layer}/{uuid} and lists entries. (tenant scope_id
 *           must match the JWT tenant or backend returns 404.)
 *
 *   Uses useMemoryByScope hook (enabled only when layer + scopeId are present).
 *   Error retry with retryClicked flag (StrictMode-safe; Sprint 57.9 D-PRE-15).
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2-3 / US-5)
 *
 * Related:
 *   - ../hooks/useMemoryByScope.ts
 *   - ./MemoryScopeBadge.tsx
 *   - ../types.ts
 */

import { useState } from "react";

import { Skeleton } from "../../../components/ui";
import { useMemoryByScope } from "../hooks/useMemoryByScope";
import type { MemoryLayer } from "../types";
import { MemoryScopeBadge } from "./MemoryScopeBadge";

const WIRED_LAYERS: MemoryLayer[] = ["system", "tenant", "user"];
const PHASE58_LAYERS: MemoryLayer[] = ["role", "session"];
const ALL_LAYERS: MemoryLayer[] = ["system", "tenant", "role", "user", "session"];

/** system layer ignores scope_id server-side; use a sentinel placeholder. */
const SYSTEM_SCOPE_SENTINEL = "_";

export function MemoryByScopeBrowser(): JSX.Element {
  const [selectedLayer, setSelectedLayer] = useState<MemoryLayer | null>(null);
  const [scopeInput, setScopeInput] = useState("");
  const [submittedScopeId, setSubmittedScopeId] = useState<string | null>(null);
  const [retryClicked, setRetryClicked] = useState(false);

  // For system layer, scope_id is auto-set to the sentinel on selection.
  const effectiveScopeId = selectedLayer === "system" ? SYSTEM_SCOPE_SENTINEL : submittedScopeId;
  const query = useMemoryByScope(selectedLayer, effectiveScopeId);

  function handleSelectLayer(layer: MemoryLayer) {
    setSelectedLayer(layer);
    setScopeInput("");
    setSubmittedScopeId(layer === "system" ? SYSTEM_SCOPE_SENTINEL : null);
    setRetryClicked(false);
  }

  function handleScopeSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmittedScopeId(scopeInput.trim() === "" ? null : scopeInput.trim());
    setRetryClicked(false);
  }

  function handleRetry() {
    setRetryClicked(true);
    void query.refetch();
  }

  const needsScopeInput =
    selectedLayer !== null && selectedLayer !== "system" && WIRED_LAYERS.includes(selectedLayer);

  return (
    <div className="grid gap-4 md:grid-cols-[200px_1fr]" data-testid="memory-by-scope-browser">
      {/* Layer cards */}
      <ul className="space-y-2" data-testid="layer-cards">
        {ALL_LAYERS.map((layer) => {
          const wired = WIRED_LAYERS.includes(layer);
          const active = selectedLayer === layer;
          return (
            <li key={layer}>
              <button
                type="button"
                disabled={!wired}
                onClick={() => wired && handleSelectLayer(layer)}
                className={`flex w-full items-center gap-2 rounded border p-2 text-left text-sm ${
                  active
                    ? "border-primary bg-primary/10"
                    : wired
                      ? "border-border bg-card hover:bg-muted/30"
                      : "cursor-not-allowed border-border bg-muted/20 opacity-50"
                }`}
                data-testid={`layer-card-${layer}`}
              >
                <MemoryScopeBadge layer={layer} />
                {PHASE58_LAYERS.includes(layer) && (
                  <span className="text-xs text-muted-foreground">(Phase 58+)</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Detail panel */}
      <div className="rounded border border-border bg-background p-3" data-testid="scope-detail">
        {selectedLayer === null && (
          <p className="text-sm text-muted-foreground">Select a layer card to browse entries.</p>
        )}

        {needsScopeInput && (
          <form onSubmit={handleScopeSubmit} className="mb-3 flex items-end gap-2">
            <label className="flex flex-col text-sm">
              <span className="mb-1 text-xs font-medium text-muted-foreground">
                {selectedLayer === "user" ? "User ID" : "Tenant ID"} (UUID)
              </span>
              <input
                type="text"
                value={scopeInput}
                onChange={(e) => setScopeInput(e.target.value)}
                placeholder="UUID..."
                className="rounded border border-input bg-background px-2 py-1 text-sm"
                data-testid="scope-id-input"
              />
            </label>
            <button
              type="submit"
              className="rounded bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground"
              data-testid="scope-submit"
            >
              Browse
            </button>
          </form>
        )}

        {needsScopeInput && submittedScopeId === null && (
          <p className="text-sm text-muted-foreground">
            Enter a {selectedLayer === "user" ? "user" : "tenant"} ID and click Browse.
          </p>
        )}

        {query.isLoading && (
          <div className="space-y-2" data-testid="loading-skeleton">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-8" />
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
          <p className="text-sm text-muted-foreground" data-testid="scope-empty">
            No entries for this scope.
          </p>
        )}

        {query.isSuccess && query.data.items.length > 0 && (
          <ul className="space-y-1" data-testid="scope-entries">
            {query.data.items.map((item) => (
              <li
                key={item.id}
                className="rounded bg-muted/20 p-2 text-xs"
                data-testid={`scope-entry-${item.id}`}
              >
                <div className="flex items-center gap-2">
                  <MemoryScopeBadge layer={item.layer} />
                  {item.key && <span className="font-medium">{item.key}</span>}
                  <span className="text-muted-foreground">
                    {new Date(item.created_at_ms).toLocaleDateString()}
                  </span>
                </div>
                <p className="mt-1 text-muted-foreground">{item.content}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
