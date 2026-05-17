"""
File: backend/src/api/v1/loops.py
Purpose: Cat 1 Orchestrator Loop REST facade for Operations Overview (Sprint 57.19 US-B1).
Category: api/v1
Scope: Phase 57 / Sprint 57.19 Day 1 / US-B1

Description:
    Single GET endpoint, gated by `Depends(get_current_tenant)` + RLS via
    `Depends(get_db_session_with_tenant)`:

    - GET /api/v1/loops?status=X&since=ISO&cursor=B64&limit=50
        Paginated list of agent loop instances (one row per session) for the
        current tenant, sorted by started_at DESC, with cursor-based pagination.

    Per Sprint 57.19 Day 0 三-prong drift D-PRE-SCHEMA-1 pivot:
    - LoopState ORM (state.py:113) is a current-version POINTER (no
      started_at/ended_at/status/turn_count/token_usage columns).
    - The columns plan claimed for the list response actually live on the
      Session ORM (sessions.py:73): started_at / ended_at / status /
      total_turns / total_tokens / total_cost_usd.
    - This endpoint queries Session (with optional alias for plan-claimed
      response field names) and uses LoopState's current_version only when
      needed (deferred; not included in v1 response).
    - Pattern follows api/v1/memory.py: direct ORM via select() without a
      repository.py layer (orchestrator_loop/repository.py does NOT exist;
      D-PRE-5).

    Cursor format: base64-url-safe JSON `{"started_at": ISO8601, "session_id": uuid}`.
    Decode + re-encode round-trip to advance pages stably.

    Multi-tenant: RLS-enforced at storage layer via SET LOCAL app.tenant_id;
    redundant `Session.tenant_id == current_tenant` filter applied at app
    layer for defence-in-depth per `.claude/rules/multi-tenant-data.md` 鐵律.

Created: 2026-05-17 (Sprint 57.19 Day 1 / US-B1)

Modification History (newest-first):
    - 2026-05-17: Initial creation (Sprint 57.19 Day 1 / US-B1) — Session ORM pivot

Related:
    - infrastructure/db/models/sessions.py:73 (Session ORM — D-PRE-SCHEMA-1 column source)
    - infrastructure/db/models/state.py:113 (LoopState ORM — current-version pointer only)
    - platform_layer/middleware/tenant_context.py (get_db_session_with_tenant — RLS)
    - platform_layer/identity/auth.py (get_current_tenant)
    - sprint-57-19-plan.md §US-B1 (Cat 1 loops list endpoint spec)
    - api/v1/memory.py (sibling 57.12 pattern reference)
    - 17-cross-category-interfaces.md §1 Cat 1 (no NEW ABC methods this sprint)
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.sessions import Session
from platform_layer.identity.auth import get_current_tenant
from platform_layer.middleware.tenant_context import get_db_session_with_tenant

router = APIRouter(prefix="/loops", tags=["loops"])

_MAX_PAGE_SIZE = 200
_DEFAULT_PAGE_SIZE = 50


class LoopItem(BaseModel):
    """One loop instance (one Session row).

    Field aliases per D-PRE-SCHEMA-2: Session ORM uses `total_turns` +
    `total_tokens`; response aliases as `turn_count` + `token_usage` for
    plan / frontend consistency.
    """

    session_id: UUID
    status: str
    started_at_ms: int
    ended_at_ms: int | None
    turn_count: int
    token_usage: int
    total_cost_usd: Decimal


class LoopsPage(BaseModel):
    items: list[LoopItem]
    next_cursor: str | None
    page_size: int


def _to_ms(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return int(dt.timestamp() * 1000)


def _session_to_item(orm: Session) -> LoopItem:
    return LoopItem(
        session_id=orm.id,
        status=orm.status,
        started_at_ms=_to_ms(orm.started_at) or 0,
        ended_at_ms=_to_ms(orm.ended_at),
        turn_count=orm.total_turns,
        token_usage=orm.total_tokens,
        total_cost_usd=orm.total_cost_usd,
    )


def _encode_cursor(started_at: datetime, session_id: UUID) -> str:
    payload = {"started_at": started_at.isoformat(), "session_id": str(session_id)}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        return datetime.fromisoformat(payload["started_at"]), UUID(payload["session_id"])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid cursor",
        ) from exc


@router.get("", response_model=LoopsPage)
async def list_loops(
    status_filter: str | None = Query(
        None, alias="status", description="Filter by Session.status (active / ended / etc.)"
    ),
    since: datetime | None = Query(None, description="Only loops started after this ISO datetime"),
    cursor: str | None = Query(
        None, description="Opaque pagination cursor from previous response.next_cursor"
    ),
    limit: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    current_tenant: UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> LoopsPage:
    """List loop instances for the current tenant, paginated by (started_at, session_id) cursor.

    Sort: started_at DESC, session_id DESC (stable tiebreaker for cursor).
    """
    base = select(Session).where(Session.tenant_id == current_tenant)

    if status_filter is not None:
        base = base.where(Session.status == status_filter)
    if since is not None:
        base = base.where(Session.started_at > since)

    if cursor is not None:
        cursor_started_at, cursor_session_id = _decode_cursor(cursor)
        # Resume from row strictly older than cursor (DESC order).
        # Tiebreak by session_id when started_at equal.
        from sqlalchemy import and_, or_

        base = base.where(
            or_(
                Session.started_at < cursor_started_at,
                and_(
                    Session.started_at == cursor_started_at,
                    Session.id < cursor_session_id,
                ),
            )
        )

    stmt = base.order_by(desc(Session.started_at), desc(Session.id)).limit(limit + 1)
    rows = (await db.execute(stmt)).scalars().all()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_session_to_item(r) for r in page_rows]

    next_cursor = None
    if has_more and page_rows:
        last = page_rows[-1]
        next_cursor = _encode_cursor(last.started_at, last.id)

    return LoopsPage(items=items, next_cursor=next_cursor, page_size=limit)
