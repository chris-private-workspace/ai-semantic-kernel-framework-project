"""
File: backend/src/platform_layer/handoff/service.py
Purpose: HandoffService — boots a child session for a Cat 11 HANDOFF control transfer.
Category: platform_layer (Cat 11 HANDOFF session-boot; crosses sessions DB + audit + persona)
Scope: Phase 57 / Sprint 57.68 (A-3b backend slice, Stage 1)

Description:
    When the agent loop ends with stop_reason="handoff" (carrying target_agent
    + reason), the platform boots a NEW persisted child session for the target
    agent so the handover is durable + auditable. This service owns that boot;
    server-side-first layering keeps DB / session knowledge out of the loop.

    boot_handoff() runs as ONE DB transaction (atomic — child create + parent
    mark + audit all commit together or roll back together):
        1. resolve target_agent → persona system_prompt (unknown → typed error,
           no session booted).
        2. verify the parent session belongs to the caller's tenant
           (multi-tenant 鐵律 — a cross-tenant / missing parent is rejected;
           the child MUST use the parent's tenant_id).
        3. create the child session (parent's tenant_id, handoff_parent_id =
           parent, meta_data["agent_role"] = target_agent).
        4. mark the parent session status="handed_off".
        5. append a hash-chained "session.handoff" audit row.

    LLM-provider-neutral: no SDK import; persona resolution is a string lookup.
    The router (Stage 2) calls this from its post-loop hook and then emits the
    AgentHandoff SSE event carrying new_session_id.

Key Components:
    - HandoffResult: value object carrying new_session_id + target_agent
    - HandoffError: typed error (unknown target / foreign parent)
    - HandoffService.boot_handoff(): the atomic session-boot

Created: 2026-06-02 (Sprint 57.68 A-3b)
Last Modified: 2026-06-12

Modification History (newest-first):
    - 2026-06-12: Sprint 57.107 (B3) — boot_handoff allowed_targets tenant allowlist enforcement
    - 2026-06-02: Sprint 57.70 Stage-1a — await async per-tenant resolve_persona
    - 2026-06-02: Sprint 57.69 A-3b — boot_handoff carries parent_context into child meta_data
    - 2026-06-02: Initial creation (Sprint 57.68 A-3b) — atomic handoff session-boot

Related:
    - platform_layer/handoff/context_carry.py — cap_and_serialize (Sprint 57.69)
    - platform_layer/handoff/persona_registry.py — resolve_persona (US-3)
    - infrastructure/db/repositories/session_repository.py — create/get/mark
    - infrastructure/db/audit_helper.py — append_audit (hash-chained)
    - .claude/rules/multi-tenant-data.md 鐵律 — child uses parent's tenant_id
    - sprint-57-68-plan.md §3.2 — platform handoff service (US-2)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts.chat import Message
from infrastructure.db.audit_helper import append_audit
from infrastructure.db.repositories.session_repository import SessionRepository
from platform_layer.handoff.context_carry import cap_and_serialize
from platform_layer.handoff.persona_registry import resolve_persona


class HandoffError(Exception):
    """Raised when a handoff cannot be booted (unknown target / foreign parent).

    No child session is created when this is raised; the caller treats it as a
    failed handover (the parent stays in its prior status).
    """


@dataclass(frozen=True)
class HandoffResult:
    """Outcome of a successful handoff session-boot."""

    new_session_id: UUID
    parent_session_id: UUID
    target_agent: str


class HandoffService:
    """Boots a tenant-scoped child session for a Cat 11 HANDOFF control transfer."""

    # === boot_handoff: atomic child-create + parent-mark + audit ===========
    # Why: a HANDOFF is durable only if the child session, the parent mark, and
    # the audit row commit together — a partial boot (child exists but parent
    # not marked / no audit) leaves the chain inconsistent. The whole body runs
    # under one transaction; any failure rolls all of it back. Multi-tenant
    # 鐵律: the child inherits the parent's tenant_id and a cross-tenant /
    # missing parent is rejected BEFORE anything is written.
    async def boot_handoff(
        self,
        *,
        parent_session_id: UUID,
        target_agent: str,
        reason: str,
        tenant_id: UUID,
        user_id: UUID,
        db: AsyncSession,
        parent_context: list[Message] | None = None,
        allowed_targets: Sequence[str] | None = None,
    ) -> HandoffResult:
        """Boot a child session for `target_agent`, mark parent handed-off, audit.

        Args:
            parent_session_id: the session that emitted the HANDOFF.
            target_agent: handoff target identifier (resolved via the persona
                registry; unknown → HandoffError, no boot).
            reason: free-text handoff reason (audited; carried to the event).
            tenant_id: the caller's tenant (the parent's tenant; the child uses
                this same tenant_id — multi-tenant 鐵律).
            user_id: the acting user (audited as the actor + child owner).
            db: AsyncSession; this method owns the transaction (begin/commit or
                rollback). Use a nested transaction if the caller already has
                one open.
            parent_context: the parent's in-memory conversation snapshot at
                HANDOFF (Sprint 57.69 A-3b slice 2). When provided, it is
                capped + serialized into the child's
                meta_data["carried_context"] so the child agent sees the prior
                conversation. None / empty → no carried_context key (backward
                compatible with the 57.68 boot).
            allowed_targets: the tenant's handoff_target_allowlist (Sprint
                57.107 B3 governance). None = no restriction (all registered
                personas); values = only those targets boot. Enforced here
                (defense in depth — the LLM may name any target regardless of
                the spec description).

        Returns:
            HandoffResult with the new child session_id.

        Raises:
            HandoffError: target_agent unknown (no persona) OR not in the
                tenant's allowlist OR parent_session_id does not exist in this
                tenant (foreign / missing parent).
        """
        # 1. Resolve persona FIRST — reject unknown target before any write.
        #    Per-tenant DB catalog → hardcoded defaults → None (Sprint 57.70).
        #    Resolved BEFORE the transaction (db + tenant_id are in scope).
        persona = await resolve_persona(db, tenant_id, target_agent)
        if persona is None:
            raise HandoffError(f"unknown handoff target_agent: {target_agent!r}")

        # 1b. Tenant allowlist (Sprint 57.107 B3): an off-list target is rejected
        #     BEFORE any write — the router's existing fail-soft path logs it and
        #     the run ends without a child (no orphan boot).
        if allowed_targets is not None and target_agent not in allowed_targets:
            raise HandoffError(
                f"handoff target_agent not allowed by tenant policy: {target_agent!r}"
            )

        repo = SessionRepository(db)

        # Use a nested transaction when the caller already opened one (tests /
        # request scope); otherwise begin a fresh transaction. Either way the
        # block below is atomic.
        transaction = db.begin_nested() if db.in_transaction() else db.begin()
        async with transaction:
            # 2. Multi-tenant 鐵律: the parent must belong to this tenant. A
            #    cross-tenant or missing parent → reject (no orphan child).
            parent = await repo.get_session(session_id=parent_session_id, tenant_id=tenant_id)
            if parent is None:
                raise HandoffError(
                    f"parent session {parent_session_id} not found in tenant {tenant_id}"
                )

            # 3. Create the child session under the PARENT's tenant_id, linked
            #    + carrying the target persona role in meta_data. When a parent
            #    conversation snapshot is supplied, cap + serialize it into
            #    meta_data["carried_context"] (Sprint 57.69) so the child agent
            #    sees the prior context; absent/empty → no carried_context key
            #    (57.68 backward-compat).
            carried = cap_and_serialize(parent_context)
            meta_data: dict[str, Any] = {"agent_role": target_agent}
            if carried:
                meta_data["carried_context"] = carried
            new_session_id = uuid4()
            await repo.create_session(
                session_id=new_session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                title=f"Handoff → {target_agent}",
                handoff_parent_id=parent_session_id,
                meta_data=meta_data,
            )

            # 4. Mark the parent handed-off (tenant-scoped UPDATE).
            await repo.mark_handed_off(session_id=parent_session_id, tenant_id=tenant_id)

            # 5. Hash-chained audit row for the handover.
            await append_audit(
                db,
                tenant_id=tenant_id,
                operation="session.handoff",
                resource_type="session",
                resource_id=str(parent_session_id),
                operation_data={
                    "target_agent": target_agent,
                    "new_session_id": str(new_session_id),
                    "reason": reason,
                },
                user_id=user_id,
                session_id=parent_session_id,
                operation_result="success",
            )

        return HandoffResult(
            new_session_id=new_session_id,
            parent_session_id=parent_session_id,
            target_agent=target_agent,
        )


__all__ = ["HandoffError", "HandoffResult", "HandoffService"]
