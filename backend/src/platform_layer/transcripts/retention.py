"""
File: backend/src/platform_layer/transcripts/retention.py
Purpose: apply_transcript_retention — delete (or dry-run count) transcript rows past retention.
Category: Phase 57 platform_layer.transcripts (data lifecycle)
Scope: Sprint 57.134 (transcript retention — apply/preview on the canonical tenants.retention_days)

Description:
    Enforces a tenant's transcript retention window by deleting messages + message_events
    older than (now - retention_days). The retention window is the CANONICAL
    tenants.retention_days SaaS-settings column (Sprint 57.46; settable via the admin
    PATCH /tenants/{id}) — this module does NOT introduce a parallel config (Day-0 pivot,
    Sprint 57.134: avoids the AP-6 parallel-config anti-pattern; the column already exists).

    apply_transcript_retention supports a dry_run mode that COUNTS the rows that would be
    deleted (no mutation) — backs the admin "preview" GET so an operator can see the impact
    before running the destructive apply POST.

    Provider-neutral; no SDK / agent_harness import.

    RLS: messages / message_events / audit_log are FORCE ROW LEVEL SECURITY (migration 0009),
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid). The admin path uses a
    plain (non-tenant) session, so this sets app.tenant_id for the txn (set_config local)
    before the DELETE / COUNT so the cross-tenant admin operation satisfies the USING policy;
    the explicit WHERE tenant_id filter is the real scope (correct even if the app role owns
    the schema and bypasses FORCE in dev/test).

Key Components:
    - RetentionStats — (messages, events, cutoff); apply=deleted, dry_run=matched counts
    - apply_transcript_retention(db, tenant_id, retention_days, *, now, dry_run) -> RetentionStats
    - SweepStats — (tenants_processed, tenants_failed, total_messages, total_events)
    - run_transcript_retention_sweep(session_factory, *, now) -> SweepStats (all-tenant sweep)

Created: 2026-06-17 (Sprint 57.134)
Last Modified: 2026-06-17

Modification History (newest-first):
    - 2026-06-17: Sprint 57.135 — add run_transcript_retention_sweep + SweepStats (scheduled job)
    - 2026-06-17: Initial creation (Sprint 57.134) — apply/preview on tenants.retention_days

Related:
    - infrastructure/db/models/identity.py — Tenant.retention_days (canonical SaaS col, 57.46)
    - infrastructure/db/models/sessions.py — Message + MessageEvent (tenant_id, created_at)
    - migrations/versions/0009_rls_policies.py — FORCE RLS on the transcript tables (SET LOCAL)
    - api/v1/admin/tenants.py — the apply POST + preview GET endpoints that consume this module
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import delete, func, select, text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetentionStats:
    """Outcome of one retention run. apply -> deleted counts; dry_run -> would-delete counts."""

    messages: int
    events: int
    cutoff: datetime


async def apply_transcript_retention(
    db: AsyncSession,
    tenant_id: UUID,
    retention_days: int,
    *,
    now: datetime | None = None,
    dry_run: bool = False,
) -> RetentionStats:
    """Delete (or, when dry_run, COUNT) messages + message_events older than the retention window.

    retention_days is the tenant's canonical tenants.retention_days (NOT NULL, >= 1). cutoff =
    now - retention_days. `now` is injectable for deterministic tests; defaults to UTC now.
    Strictly tenant-scoped (explicit WHERE + a SET LOCAL app.tenant_id for the FORCE'd RLS on
    messages/message_events). Runs inside the caller's transaction (the apply endpoint commits
    after auditing; the preview endpoint does not mutate, so it never commits).
    """
    resolved_now = now if now is not None else datetime.now(timezone.utc)
    cutoff = resolved_now - timedelta(days=retention_days)

    # RLS context for this txn (messages / message_events are FORCE ROW LEVEL SECURITY).
    await db.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
    )

    from infrastructure.db.models.sessions import Message, MessageEvent

    if dry_run:
        msg_n = await _count_older(db, Message, tenant_id, cutoff)
        evt_n = await _count_older(db, MessageEvent, tenant_id, cutoff)
        return RetentionStats(messages=msg_n, events=evt_n, cutoff=cutoff)

    msg_result = await db.execute(
        delete(Message)
        .where(Message.tenant_id == tenant_id, Message.created_at < cutoff)
        .execution_options(synchronize_session=False)
    )
    evt_result = await db.execute(
        delete(MessageEvent)
        .where(MessageEvent.tenant_id == tenant_id, MessageEvent.created_at < cutoff)
        .execution_options(synchronize_session=False)
    )
    return RetentionStats(
        messages=int(getattr(msg_result, "rowcount", 0) or 0),
        events=int(getattr(evt_result, "rowcount", 0) or 0),
        cutoff=cutoff,
    )


async def _count_older(db: AsyncSession, model: Any, tenant_id: UUID, cutoff: datetime) -> int:
    """COUNT rows of `model` for the tenant older than cutoff (dry-run helper)."""
    result = await db.execute(
        select(func.count())
        .select_from(model)
        .where(model.tenant_id == tenant_id, model.created_at < cutoff)
    )
    return int(result.scalar_one() or 0)


@dataclass(frozen=True)
class SweepStats:
    """Outcome of one scheduled retention sweep across all tenants (the job's drain_once analog)."""

    tenants_processed: int
    tenants_failed: int
    total_messages: int
    total_events: int


# === run_transcript_retention_sweep: the scheduled job's per-cycle unit of work ===
# Why: Sprint 57.134 shipped a MANUAL per-tenant apply (admin POST). The scheduled job
# (Sprint 57.135) needs a sweep that enforces retention across ALL tenants automatically.
# This is the testable analog of BillingOutboxDrainer.drain_once() — one sweep cycle.
# Each tenant runs in its OWN transaction (apply → audit → commit) and is fail-open
# (a flake on one tenant must not abort the rest). Reuses apply_transcript_retention
# (the delete primitive) + append_audit (system user_id=None).
async def run_transcript_retention_sweep(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: datetime | None = None,
) -> SweepStats:
    """Enforce per-tenant transcript retention across ALL tenants (one sweep cycle).

    Enumerates every tenant's (id, retention_days) and, for each, opens a fresh session,
    deletes its expired transcripts (apply_transcript_retention), writes a system audit row
    (tenant_transcript_retention_scheduled, user_id=None), and commits — per-tenant txn so a
    SET LOCAL app.tenant_id + delete + audit is isolated. Fail-open per tenant: a per-tenant
    exception is logged and the sweep continues (tenants_failed += 1). `now` is injectable for
    deterministic tests. Returns aggregate SweepStats.
    """
    # Local imports keep this module import-light + avoid an import cycle (audit_helper /
    # identity both sit above platform_layer in the import graph at module load).
    from infrastructure.db.audit_helper import append_audit
    from infrastructure.db.models.identity import Tenant

    # Enumerate all tenants in a short read session. The `tenants` registry is NOT
    # tenant-RLS'd (it IS the tenant list), so a plain (non-tenant) session reads it.
    async with session_factory() as read_db:
        rows = (await read_db.execute(select(Tenant.id, Tenant.retention_days))).all()

    processed = failed = total_messages = total_events = 0
    for tenant_id, retention_days in rows:
        try:
            async with session_factory() as db:
                stats = await apply_transcript_retention(db, tenant_id, retention_days, now=now)
                await append_audit(
                    db,
                    tenant_id=tenant_id,
                    operation="tenant_transcript_retention_scheduled",
                    resource_type="tenant",
                    resource_id=str(tenant_id),
                    operation_data={
                        "retention_days": retention_days,
                        "cutoff": stats.cutoff.isoformat(),
                        "deleted_messages": stats.messages,
                        "deleted_events": stats.events,
                    },
                    user_id=None,
                    operation_result="success",
                )
                await db.commit()
            processed += 1
            total_messages += stats.messages
            total_events += stats.events
        except Exception:  # noqa: BLE001 — fail-open per tenant: one flake must not abort the sweep
            logger.exception("transcript retention sweep failed for tenant %s", tenant_id)
            failed += 1
    return SweepStats(
        tenants_processed=processed,
        tenants_failed=failed,
        total_messages=total_messages,
        total_events=total_events,
    )
