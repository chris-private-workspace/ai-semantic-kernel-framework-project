/**
 * File: frontend/src/features/governance/types.ts
 * Purpose: Shared types mirroring backend ApprovalSummaryDTO + AuditLogEntryDTO + ChainVerifyResult.
 * Category: Frontend / governance / types
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-4 + US-5 Day 3 (audit log + chain types)
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-4 + US-5 Day 3 — extend with audit log entry / page / filter / chain verify
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - backend/src/api/v1/governance/router.py (ApprovalSummaryDTO)
 *   - backend/src/api/v1/audit.py (AuditLogEntryDTO / AuditLogPage / ChainVerifyResult)
 *   - backend/src/agent_harness/_contracts/hitl.py (RiskLevel / DecisionType)
 */

export type RiskLevelLabel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type DecisionLabel = "approved" | "rejected" | "escalated";

export type ApprovalSummary = {
  request_id: string;
  tenant_id: string;
  session_id: string;
  requester: string;
  risk_level: RiskLevelLabel;
  payload: {
    tool_name?: string;
    tool_arguments?: Record<string, unknown>;
    reason?: string;
    summary?: string;
    [key: string]: unknown;
  };
  sla_deadline: string; // ISO 8601
  context_snapshot: Record<string, unknown>;
};

export type PendingListResponse = {
  items: ApprovalSummary[];
  count: number;
};

export type DecisionResponse = {
  request_id: string;
  decision: string;
  reviewer: string;
};

// ---------------------------------------------------------------------------
// Audit log (Sprint 57.9 US-4 + US-5 — mirrors backend audit.py DTOs)
// ---------------------------------------------------------------------------

export type AuditLogEntry = {
  id: number;
  tenant_id: string;
  user_id: string | null;
  session_id: string | null;
  operation: string;
  resource_type: string;
  resource_id: string | null;
  operation_data: Record<string, unknown>;
  operation_result: string | null;
  previous_log_hash: string;
  current_log_hash: string;
  timestamp_ms: number;
};

export type AuditLogPage = {
  items: AuditLogEntry[];
  has_more: boolean;
  next_offset: number | null;
  page_size: number;
};

/** Filter / pagination params accepted by GET /api/v1/audit/log. */
export type AuditLogFilter = {
  operation?: string;
  resource_type?: string;
  user_id?: string;
  from_ts_ms?: number;
  to_ts_ms?: number;
  offset?: number;
  page_size?: number;
};

export type ChainVerifyResult = {
  valid: boolean;
  broken_at_id: number | null;
  total_entries: number;
};
