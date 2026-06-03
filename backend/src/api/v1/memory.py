"""
File: backend/src/api/v1/memory.py
Purpose: Read-only Cat 3 Memory REST facade for MemoryViewer UI (Sprint 57.12 US-2).
Category: api/v1
Scope: Phase 57 / Sprint 57.12 Day 1 / US-2

Description:
    Three GET endpoints, all gated by `Depends(require_audit_role)` (auditor /
    admin / compliance) and `Depends(get_current_tenant)`:

    - GET /api/v1/memory/recent?layer=X&limit=50&offset=0
        Paginated list of memory entries within a single layer, sorted by
        created_at DESC. Tenant-scoped layers (tenant / user) auto-filter by
        JWT tenant via RLS SET LOCAL. System layer is cross-tenant (auditor
        only). Role / session layers return 501 (Phase 58+ scope per
        AD-Memory-Role-Session-Phase58 carryover).

    - GET /api/v1/memory/scope/{layer}/{scope_id}?limit=50&offset=0
        Entries scoped to a specific layer + scope_id (e.g. /scope/user/<uuid>
        lists memory for that user). Cross-tenant denied via RLS for tenant /
        user layers; auditor-only for system layer; 501 for role / session.

    - GET /api/v1/memory/by-time/{layer}/{time_scale}?limit=50&offset=0
        Time-scale filter on `expires_at` column. Currently only meaningful
        for `memory_user` (only layer with expires_at column per Day 1
        D1-008 ORM探勘); other layers return 400.

    - GET /api/v1/memory/matrix
        Aggregate (layer × time_scale) counts via GROUP BY / count() (no row
        materialisation). system + tenant collapse to one PERMANENT bucket
        (no expires_at); user buckets into PERMANENT / QUARTERLY / DAILY via
        the same expires_at predicate as /by-time. role + session are reported
        in `gapped_layers` (junction tables, no RLS path) but NOT queried.

    Per Day 1 D1-007 + D1-008 drift catalog:
    - MemoryStore ABC has no list_* methods → bypass ABC, read ORM directly
      (Option B per user 2026-05-10 decision).
    - 5-layer ORM tables have non-uniform schemas → ship MemoryEntryItem as a
      discriminated response shape with nullable layer-specific fields.
    - Phase 57.12 ships full functionality for tenant + user + system layers;
      role + session return 501 (Phase 58+).

    All requests outside the JWT tenant → empty / 404 (per multi-tenant-data.md
    鐵律 — never reveal cross-tenant existence). RLS enforces at storage layer
    via `get_db_session_with_tenant` SET LOCAL app.tenant_id for layers with
    TenantScopedMixin.

Created: 2026-05-10 (Sprint 57.12 Day 1 / US-2)

Modification History (newest-first):
    - 2026-06-03: Sprint 57.73 Track B — add GET /matrix layer×time_scale count aggregate
    - 2026-05-17: Sprint 57.19 US-B2 — extend /recent w/ optional scope_id + time_scale params
    - 2026-05-10: Initial creation (Sprint 57.12 Day 1 / US-2) — 3 endpoints
      ORM-direct read facade; tenant + user + system layers fully wired

Related:
    - infrastructure/db/models/memory.py (5-layer ORM)
    - platform_layer/middleware/tenant_context.py (get_db_session_with_tenant — RLS)
    - platform_layer/identity/auth.py (get_current_tenant + require_audit_role)
    - sprint-57-12-plan.md §US-2 (REST endpoint spec + Day 1 drift D1-007/008/009/010)
    - api/v1/verification.py (sibling 57.11 pattern reference for inline schemas)
    - 17-cross-category-interfaces.md §3 Cat 3 (no NEW ABC methods this sprint)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.memory import (
    MemorySystem,
    MemoryTenant,
    MemoryUser,
)
from platform_layer.identity.auth import get_current_tenant, require_audit_role
from platform_layer.middleware.tenant_context import get_db_session_with_tenant

router = APIRouter(prefix="/memory", tags=["memory"])

# Hard cap on page size; mirrors verification.py 57.11 _MAX_PAGE_SIZE pattern.
_MAX_PAGE_SIZE = 200


class MemoryLayer(str, Enum):
    SYSTEM = "system"
    TENANT = "tenant"
    ROLE = "role"
    USER = "user"
    SESSION = "session"


class MemoryTimeScale(str, Enum):
    PERMANENT = "permanent"  # expires_at IS NULL
    QUARTERLY = "quarterly"  # expires_at > NOW() + 30d (long-lived)
    DAILY = "daily"  # expires_at <= NOW() + 30d (short-lived)


class MemoryEntryItem(BaseModel):
    """Discriminated by `layer`; layer-specific fields nullable.

    Per Day 1 D1-008: 5-layer ORM tables have non-uniform schemas
    (MemorySystem has no tenant_id; MemoryRole has no expires_at; etc.).
    Frontend MemoryViewer renders fields conditionally based on `layer`.
    """

    id: UUID
    layer: MemoryLayer
    scope_id: str | None = None  # tenant_id / role_id / user_id / session_id
    key: str | None = None  # None for session (use summary as identifier)
    content: str  # entry content; for session = summary
    category: str | None = None
    expires_at_ms: int | None = None  # only memory_user has this
    created_at_ms: int
    updated_at_ms: int | None = None  # role + session don't have this
    tenant_id: UUID | None = None  # only tenant + user (via TenantScopedMixin)


class MemoryEntryPage(BaseModel):
    items: list[MemoryEntryItem]
    total: int
    has_more: bool
    next_offset: int | None
    page_size: int


class MemoryMatrixCell(BaseModel):
    """Single (layer × time_scale) count cell of the Memory 5×3 matrix.

    Sprint 57.73 Track B: aggregate read for the MemoryViewer matrix widget.
    Only cells with count > 0 are emitted (FE default-0 for absent cells);
    see GET /matrix docstring for the time-scale reality per layer.
    """

    layer: MemoryLayer
    time_scale: MemoryTimeScale
    count: int


class MemoryMatrixResponse(BaseModel):
    cells: list[MemoryMatrixCell]
    total: int
    gapped_layers: list[MemoryLayer]


def _to_ms(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return int(dt.timestamp() * 1000)


def _system_to_item(orm: MemorySystem) -> MemoryEntryItem:
    return MemoryEntryItem(
        id=orm.id,
        layer=MemoryLayer.SYSTEM,
        scope_id=None,
        key=orm.key,
        content=orm.content,
        category=orm.category,
        expires_at_ms=None,
        created_at_ms=_to_ms(orm.created_at) or 0,
        updated_at_ms=_to_ms(orm.updated_at),
        tenant_id=None,
    )


def _tenant_to_item(orm: MemoryTenant) -> MemoryEntryItem:
    return MemoryEntryItem(
        id=orm.id,
        layer=MemoryLayer.TENANT,
        scope_id=str(orm.tenant_id) if orm.tenant_id else None,
        key=orm.key,
        content=orm.content,
        category=orm.category,
        expires_at_ms=None,
        created_at_ms=_to_ms(orm.created_at) or 0,
        updated_at_ms=_to_ms(orm.updated_at),
        tenant_id=orm.tenant_id,
    )


def _user_to_item(orm: MemoryUser) -> MemoryEntryItem:
    return MemoryEntryItem(
        id=orm.id,
        layer=MemoryLayer.USER,
        scope_id=str(orm.user_id),
        key=None,  # MemoryUser ORM has no key column (per D1-008)
        content=orm.content,
        category=orm.category,
        expires_at_ms=_to_ms(orm.expires_at),
        created_at_ms=_to_ms(orm.created_at) or 0,
        updated_at_ms=_to_ms(orm.updated_at),
        tenant_id=orm.tenant_id,
    )


def _validate_page_size(limit: int) -> int:
    if limit > _MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"limit exceeds {_MAX_PAGE_SIZE}",
        )
    return limit


async def _list_system(
    db: AsyncSession, offset: int, limit: int
) -> tuple[list[MemoryEntryItem], int]:
    sel = select(MemorySystem).order_by(desc(MemorySystem.created_at))
    items_orm = (await db.execute(sel.offset(offset).limit(limit))).scalars().all()
    total = len((await db.execute(select(MemorySystem))).scalars().all())
    return [_system_to_item(o) for o in items_orm], total


async def _list_tenant(
    db: AsyncSession, current_tenant: UUID, offset: int, limit: int
) -> tuple[list[MemoryEntryItem], int]:
    base = select(MemoryTenant).where(MemoryTenant.tenant_id == current_tenant)
    sel = base.order_by(desc(MemoryTenant.created_at))
    items_orm = (await db.execute(sel.offset(offset).limit(limit))).scalars().all()
    total = len((await db.execute(base)).scalars().all())
    return [_tenant_to_item(o) for o in items_orm], total


async def _list_user(
    db: AsyncSession,
    current_tenant: UUID,
    offset: int,
    limit: int,
    user_id: UUID | None = None,
    time_scale: MemoryTimeScale | None = None,
) -> tuple[list[MemoryEntryItem], int]:
    base = select(MemoryUser).where(MemoryUser.tenant_id == current_tenant)
    if user_id is not None:
        base = base.where(MemoryUser.user_id == user_id)
    if time_scale is not None:
        now = datetime.now(UTC)
        if time_scale == MemoryTimeScale.PERMANENT:
            base = base.where(MemoryUser.expires_at.is_(None))
        elif time_scale == MemoryTimeScale.QUARTERLY:
            base = base.where(MemoryUser.expires_at > now + timedelta(days=30))
        elif time_scale == MemoryTimeScale.DAILY:
            base = base.where(MemoryUser.expires_at.is_not(None))
            base = base.where(MemoryUser.expires_at <= now + timedelta(days=30))
    sel = base.order_by(desc(MemoryUser.created_at))
    items_orm = (await db.execute(sel.offset(offset).limit(limit))).scalars().all()
    total = len((await db.execute(base)).scalars().all())
    return [_user_to_item(o) for o in items_orm], total


def _build_page(
    items: list[MemoryEntryItem], total: int, offset: int, page_size: int
) -> MemoryEntryPage:
    has_more = offset + len(items) < total
    next_offset = offset + len(items) if has_more else None
    return MemoryEntryPage(
        items=items,
        total=total,
        has_more=has_more,
        next_offset=next_offset,
        page_size=page_size,
    )


@router.get("/recent", response_model=MemoryEntryPage)
async def list_recent(
    layer: MemoryLayer = Query(..., description="Layer to query (single layer per request)"),
    limit: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    scope_id: UUID | None = Query(
        None,
        description=(
            "Optional scope_id (Sprint 57.19 US-B2). For layer=user this is user_id; "
            "for layer=tenant it must match current_tenant (else 404); ignored otherwise."
        ),
    ),
    time_scale: MemoryTimeScale | None = Query(
        None,
        description="Optional time-scale filter (Sprint 57.19 US-B2). Only applies to layer=user; "
        "ignored for other layers (only memory_user has expires_at column per D1-008).",
    ),
    current_tenant: UUID = Depends(get_current_tenant),
    _audit: UUID = Depends(require_audit_role),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> MemoryEntryPage:
    """Paginated recent entries from a single layer, sorted by created_at DESC.

    Tenant + user layers: filtered by JWT tenant_id via RLS.
    System layer: cross-tenant (auditor only).
    Role + session layers: 501 Not Implemented (AD-Memory-Role-Session-Phase58).

    Sprint 57.19 US-B2 extension:
    - scope_id: filter within layer (user_id for user; tenant cross-check for tenant)
    - time_scale: only for layer=user (the only layer with expires_at column)
    """
    _validate_page_size(limit)
    if layer == MemoryLayer.SYSTEM:
        items, total = await _list_system(db, offset, limit)
    elif layer == MemoryLayer.TENANT:
        # scope_id (if present) must match current_tenant for tenant layer.
        if scope_id is not None and scope_id != current_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="scope_id does not match current tenant",
            )
        items, total = await _list_tenant(db, current_tenant, offset, limit)
    elif layer == MemoryLayer.USER:
        items, total = await _list_user(
            db, current_tenant, offset, limit, user_id=scope_id, time_scale=time_scale
        )
    else:
        # role / session — Phase 58+ scope per AD-Memory-Role-Session-Phase58.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"layer={layer.value} not yet supported (Phase 58+ scope)",
        )
    return _build_page(items, total, offset, limit)


@router.get("/scope/{layer}/{scope_id}", response_model=MemoryEntryPage)
async def list_by_scope(
    layer: MemoryLayer,
    scope_id: str,
    limit: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    current_tenant: UUID = Depends(get_current_tenant),
    _audit: UUID = Depends(require_audit_role),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> MemoryEntryPage:
    """Entries scoped to a specific scope_id within a layer.

    For tenant layer: scope_id must match current_tenant (cross-tenant rejected
    via RLS at DB layer). For user layer: scope_id is user_id; tenant filter
    enforced. System layer: scope_id ignored (returns all). Role / session: 501.
    """
    _validate_page_size(limit)
    if layer == MemoryLayer.USER:
        try:
            user_uuid = UUID(scope_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scope_id must be a valid UUID for user layer",
            ) from exc
        items, total = await _list_user(db, current_tenant, offset, limit, user_id=user_uuid)
    elif layer == MemoryLayer.TENANT:
        try:
            scope_uuid = UUID(scope_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scope_id must be a valid UUID for tenant layer",
            ) from exc
        # Multi-tenant rule: scope_id MUST match current_tenant (no peeking
        # into other tenants' memory regardless of role).
        if scope_uuid != current_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="scope_id does not match current tenant",
            )
        items, total = await _list_tenant(db, current_tenant, offset, limit)
    elif layer == MemoryLayer.SYSTEM:
        # System layer: scope_id has no semantic meaning; return all (auditor-only).
        items, total = await _list_system(db, offset, limit)
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"layer={layer.value} not yet supported (Phase 58+ scope)",
        )
    return _build_page(items, total, offset, limit)


@router.get("/by-time/{layer}/{time_scale}", response_model=MemoryEntryPage)
async def list_by_time(
    layer: MemoryLayer,
    time_scale: MemoryTimeScale,
    limit: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    current_tenant: UUID = Depends(get_current_tenant),
    _audit: UUID = Depends(require_audit_role),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> MemoryEntryPage:
    """Time-scale filter on expires_at column. Only memory_user has expires_at
    in current ORM (per D1-008); other layers return 400 with explanation.
    """
    _validate_page_size(limit)
    if layer != MemoryLayer.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"layer={layer.value} has no expires_at column; "
                "by-time only supports layer=user (per D1-008)"
            ),
        )

    base = select(MemoryUser).where(MemoryUser.tenant_id == current_tenant)
    now = datetime.now(UTC)
    if time_scale == MemoryTimeScale.PERMANENT:
        base = base.where(MemoryUser.expires_at.is_(None))
    elif time_scale == MemoryTimeScale.QUARTERLY:
        base = base.where(MemoryUser.expires_at > now + timedelta(days=30))
    elif time_scale == MemoryTimeScale.DAILY:
        base = base.where(MemoryUser.expires_at.is_not(None))
        base = base.where(MemoryUser.expires_at <= now + timedelta(days=30))

    stmt = base.order_by(desc(MemoryUser.created_at)).offset(offset).limit(limit)
    items_orm = (await db.execute(stmt)).scalars().all()
    total = len((await db.execute(base)).scalars().all())
    items = [_user_to_item(o) for o in items_orm]
    return _build_page(items, total, offset, limit)


@router.get("/matrix", response_model=MemoryMatrixResponse)
async def get_matrix(
    current_tenant: UUID = Depends(get_current_tenant),
    _audit: UUID = Depends(require_audit_role),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> MemoryMatrixResponse:
    """Aggregate (layer × time_scale) counts for the MemoryViewer matrix.

    Returns one cell per non-empty (layer, time_scale) pair using GROUP BY /
    count() aggregates (no row materialisation). Time-scale-per-layer reality
    (per Day 1 D1-008 ORM探勘):

    - system: global (NO tenant filter, NO expires_at) → 1 bucket (PERMANENT).
    - tenant: tenant-scoped (RLS), NO expires_at → 1 bucket (PERMANENT).
    - user:   tenant-scoped (RLS), HAS expires_at → up to 3 buckets
              (PERMANENT = expires_at IS NULL; QUARTERLY = expires_at > now+30d;
              DAILY = expires_at <= now+30d). Same predicate as /by-time.

    Cells with count 0 are OMITTED (the frontend defaults absent cells to 0).

    Layer gap (per AD-Memory-Role-Session-Phase58): role + session are junction
    tables with no RLS path (501 elsewhere); they are REPORTED in
    `gapped_layers` but NOT queried. `total` = sum of emitted cell counts.
    """
    cells: list[MemoryMatrixCell] = []

    # system — global, no tenant filter, no expires_at → all PERMANENT.
    system_count = (await db.execute(select(func.count()).select_from(MemorySystem))).scalar_one()
    if system_count:
        cells.append(
            MemoryMatrixCell(
                layer=MemoryLayer.SYSTEM,
                time_scale=MemoryTimeScale.PERMANENT,
                count=system_count,
            )
        )

    # tenant — RLS-scoped to current tenant; no expires_at → all PERMANENT.
    tenant_count = (
        await db.execute(
            select(func.count())
            .select_from(MemoryTenant)
            .where(MemoryTenant.tenant_id == current_tenant)
        )
    ).scalar_one()
    if tenant_count:
        cells.append(
            MemoryMatrixCell(
                layer=MemoryLayer.TENANT,
                time_scale=MemoryTimeScale.PERMANENT,
                count=tenant_count,
            )
        )

    # user — RLS-scoped; bucket by expires_at via the SAME predicate as /by-time.
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=30)
    time_scale_bucket = case(
        (MemoryUser.expires_at.is_(None), MemoryTimeScale.PERMANENT.value),
        (MemoryUser.expires_at > cutoff, MemoryTimeScale.QUARTERLY.value),
        else_=MemoryTimeScale.DAILY.value,
    )
    user_rows = (
        await db.execute(
            select(time_scale_bucket.label("bucket"), func.count().label("n"))
            .where(MemoryUser.tenant_id == current_tenant)
            .group_by(time_scale_bucket)
        )
    ).all()
    for bucket, n in user_rows:
        cells.append(
            MemoryMatrixCell(
                layer=MemoryLayer.USER,
                time_scale=MemoryTimeScale(bucket),
                count=n,
            )
        )

    total = sum(cell.count for cell in cells)
    return MemoryMatrixResponse(
        cells=cells,
        total=total,
        gapped_layers=[MemoryLayer.ROLE, MemoryLayer.SESSION],
    )
