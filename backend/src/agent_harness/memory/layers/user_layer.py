"""
File: backend/src/agent_harness/memory/layers/user_layer.py
Purpose: Layer 4 (User) concrete MemoryLayer — PostgreSQL memory_user backed.
Category: 範疇 3 (Memory) / Layer 4 User
Scope: Phase 51 / Sprint 51.2 Day 2

Description:
    UserLayer is the core memory layer for per-user durable preferences,
    facts, and decisions. Maps onto MemoryUser ORM (49.3 schema) which has:
        - tenant_id (TenantScopedMixin) — multi-tenant isolation
        - user_id (FK users.id)
        - category, content, vector_id
        - source, source_session_id, confidence (Numeric 3,2)
        - expires_at, metadata (JSONB)

    51.2 simplified design choices:
    - read() uses ILIKE substring match for the short/long-term axes. The
      "semantic" axis returned empty (51.2 stub) until Sprint 57.155 (CARRY-026
      Slice 1): when a MemoryVectorIndex is injected (MEMORY_VECTOR_ENABLED),
      read() embeds + cosine-searches the user's rows and merges the vector hits;
      with no index it stays byte-identical (semantic-only → [], mixed → keyword).
    - 4 spec fields with no PG column live in metadata JSONB:
        verify_before_use, last_verified_at, source_tool_call_id, time_scale
    - short_term writes set expires_at = now() + 24h
    - long_term writes set expires_at = NULL (durable)

Owner: 01-eleven-categories-spec.md §範疇 3 Layer 4 User
Single-source: 17.md §2.1

Created: 2026-04-30 (Sprint 51.2 Day 2)
Last Modified: 2026-07-01

Modification History:
    - 2026-07-01: Sprint 57.155 — read() semantic branch via MemoryVectorIndex (CARRY-026 L4)
    - 2026-06-30: Sprint 57.150 — write() → idempotent upsert on dedup_key
    - 2026-06-28: Sprint 57.149 — write() additive source param → memory_user.source column
    - 2026-06-04: Sprint 57.76 — emit memory_ops on write/evict (same txn, Risk C)
    - 2026-04-30: Initial creation (Sprint 51.2 Day 2.2)

Related:
    - infrastructure/db/models/memory.py:MemoryUser (ORM)
    - 09-db-schema-design.md L453-479 (memory_user schema)
    - sprint-51-2-plan.md §2.1 (9/15 cell scope; user×long_term + user×short_term)
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent_harness._contracts import MemoryHint, TraceContext
from agent_harness.memory._abc import MemoryLayer, MemoryScope
from agent_harness.memory._ops_recorder import _record_memory_op
from agent_harness.memory.vector_index import MemoryRow, MemoryVectorIndex
from infrastructure.db.models.memory import MemoryUser

logger = logging.getLogger(__name__)

_TimeScale = Literal["short_term", "long_term", "semantic"]


def _dedup_key(content: str) -> str:
    """Normalized-content hash for write-side dedup (Sprint 57.150).

    Collapses all whitespace runs to a single space, trims, lowercases, then md5.
    MUST match the SQL backfill in migration 0032
    (md5(lower(btrim(regexp_replace(content,'\\s+',' ','g'))))) byte-for-byte so live
    writes hit the backfilled keys. md5 is a non-cryptographic dedup key here
    (usedforsecurity=False), not a security primitive.
    """
    normalized = re.sub(r"\s+", " ", content).strip().lower()
    return hashlib.md5(normalized.encode("utf-8"), usedforsecurity=False).hexdigest()


class UserLayer(MemoryLayer):
    """Layer 4 — per-user memory backed by PostgreSQL memory_user table."""

    scope = MemoryScope.USER

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        vector_index: MemoryVectorIndex | None = None,
    ) -> None:
        self._session_factory = session_factory
        # Sprint 57.155 (CARRY-026 Slice 1): when injected (MEMORY_VECTOR_ENABLED on),
        # the "semantic" time_scale returns cosine-ranked hits instead of the 51.2 []
        # stub. None → byte-identical to 57.150 (semantic-only → [], mixed → keyword only).
        self._vector_index = vector_index

    async def read(
        self,
        *,
        query: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scales: tuple[_TimeScale, ...] = ("long_term",),
        max_hints: int = 10,
        trace_context: TraceContext | None = None,
    ) -> list[MemoryHint]:
        """Search memory_user by content ILIKE; filter by tenant + user + time_scale.

        Tenant + user are required for user-layer reads (zero-trust default).
        """
        if tenant_id is None or user_id is None:
            return []

        want_keyword = any(ts in ("short_term", "long_term") for ts in time_scales)
        # Sprint 57.155: "semantic" is real only when the vector index is injected and
        # the query is non-empty (an empty query cannot embed meaningfully). Otherwise
        # the 51.2 [] stub / keyword-only behavior is preserved byte-for-byte.
        want_semantic = (
            "semantic" in time_scales and self._vector_index is not None and query.strip() != ""
        )

        keyword_hints: list[MemoryHint] = []
        if want_keyword:
            async with self._session_factory() as session:
                stmt = select(MemoryUser).where(
                    MemoryUser.tenant_id == tenant_id,
                    MemoryUser.user_id == user_id,
                    or_(
                        MemoryUser.content.ilike(f"%{query}%"),
                        MemoryUser.category.ilike(f"%{query}%"),
                    ),
                )
                # short_term filter: expires_at must be NOT NULL and in future
                if "short_term" in time_scales and "long_term" not in time_scales:
                    stmt = stmt.where(MemoryUser.expires_at.is_not(None))
                # confidence-desc ordering for stable top-k
                stmt = stmt.order_by(MemoryUser.confidence.desc().nulls_last()).limit(max_hints)
                rows = (await session.execute(stmt)).scalars().all()
            keyword_hints = [self._row_to_hint(row, query=query) for row in rows]

        semantic_hints: list[MemoryHint] = []
        if want_semantic:
            semantic_hints = await self._semantic_hints(
                query=query, tenant_id=tenant_id, user_id=user_id, max_hints=max_hints
            )

        # No semantic hits (index off / not requested / empty / fail-soft) → the keyword
        # path is returned unchanged (byte-identical to 57.150; also the semantic-only []
        # stub, since keyword_hints is [] when only "semantic" was requested).
        if not semantic_hints:
            return keyword_hints

        # Merge keyword + semantic, dedup by row id (keep the higher relevance — the
        # semantic cosine outranks the keyword 0.4/0.8 substring boost for real matches),
        # then re-rank by relevance + cap. MemoryRetrieval.search re-sorts downstream.
        by_id: dict[UUID, MemoryHint] = {}
        for hint in keyword_hints + semantic_hints:
            prev = by_id.get(hint.hint_id)
            if prev is None or hint.relevance_score > prev.relevance_score:
                by_id[hint.hint_id] = hint
        merged = sorted(by_id.values(), key=lambda h: h.relevance_score, reverse=True)
        return merged[:max_hints]

    async def _semantic_hints(
        self, *, query: str, tenant_id: UUID, user_id: UUID, max_hints: int
    ) -> list[MemoryHint]:
        """Semantic recall via the vector index (Sprint 57.155). Fail-soft to [] on any error.

        Fetches the user's rows (wildcard), embeds + cosine-searches them, and maps each
        hit back to a full MemoryHint whose relevance_score is the cosine score (the
        semantic ranking signal MemoryRetrieval.search consumes). Any embedding / Qdrant
        failure degrades to [] so recall never breaks (the keyword path still returns).
        """
        index = self._vector_index
        if index is None:
            return []
        async with self._session_factory() as session:
            stmt = select(MemoryUser).where(
                MemoryUser.tenant_id == tenant_id,
                MemoryUser.user_id == user_id,
            )
            rows = (await session.execute(stmt)).scalars().all()
        by_dedup: dict[str, MemoryUser] = {r.dedup_key: r for r in rows if r.dedup_key}
        mem_rows = [
            MemoryRow(
                dedup_key=r.dedup_key,
                content=r.content or "",
                confidence=float(r.confidence) if r.confidence is not None else 0.5,
            )
            for r in rows
            if r.dedup_key
        ]
        if not mem_rows:
            return []
        try:
            hits = await index.search(
                tenant_id=tenant_id, user_id=user_id, rows=mem_rows, query=query, top_k=max_hints
            )
        except Exception:  # noqa: BLE001 — fail-soft: any embed/Qdrant error → no semantic hits
            logger.warning("memory semantic recall failed; keyword path preserved", exc_info=True)
            return []
        out: list[MemoryHint] = []
        for hit in hits:
            row = by_dedup.get(hit.dedup_key)
            if row is None:
                continue
            out.append(replace(self._row_to_hint(row, query=query), relevance_score=hit.score))
        return out

    async def write(
        self,
        *,
        content: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scale: _TimeScale = "long_term",
        confidence: float = 0.5,
        source: str | None = None,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        """Idempotent upsert into memory_user keyed on a normalized fact hash; return id.

        Spec fields without PG columns (verify_before_use, last_verified_at,
        source_tool_call_id, time_scale) live in metadata JSONB.

        `source` is the optional provenance tag persisted into the real
        `memory_user.source` column (additive; default None = pre-57.149
        behavior). Sprint 57.149 wires the post-send `MemoryExtractor` to pass
        `source="auto_extract"` so deterministic-extraction rows are
        distinguishable from agent-driven `memory_write` rows.

        Sprint 57.150 (AD-Memory-User-Upsert-By-Key): a repeat of the same
        normalized fact UPDATEs the existing row (via the (tenant_id, user_id,
        dedup_key) unique constraint) instead of inserting a duplicate that would
        dilute profile() top-k. On conflict the FIRST writer's `source` + metadata
        are kept (a later auto_extract does not relabel a manual fact), `confidence`
        takes the greatest, `content`/`expires_at` refresh to the latest write, and
        `updated_at` is bumped. Returns the new id on insert, the existing id on
        conflict. All three writers (the 57.148 nudge `memory_write` tool, the
        57.149 auto_extract, any agent `memory_write`) dedup through this one path.
        """
        if tenant_id is None or user_id is None:
            raise ValueError("UserLayer.write requires tenant_id and user_id")

        expires_at: datetime | None = None
        if time_scale == "short_term":
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        metadata: dict[str, Any] = {
            "time_scale": time_scale,
            "verify_before_use": False,
            "last_verified_at": None,
            "source_tool_call_id": None,
        }

        key = _dedup_key(content)
        confidence_dec = Decimal(str(round(confidence, 2)))
        async with self._session_factory() as session:
            stmt = (
                pg_insert(MemoryUser)
                .values(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    category="general",
                    content=content,
                    dedup_key=key,
                    source=source,
                    confidence=confidence_dec,
                    expires_at=expires_at,
                    metadata_=metadata,
                )
                .on_conflict_do_update(
                    constraint="uq_memory_user_dedup",
                    set_={
                        # Keep first writer's source + metadata; refresh the rest.
                        "content": content,
                        "confidence": func.greatest(MemoryUser.confidence, confidence_dec),
                        "expires_at": expires_at,
                        "updated_at": func.now(),
                    },
                )
                .returning(MemoryUser.id)
            )
            row_id: UUID = (await session.execute(stmt)).scalar_one()
            # Ops-history emit (same txn — Risk C): a re-affirm is still a WRITE op.
            _record_memory_op(
                session,
                tenant_id=tenant_id,
                user_id=user_id,
                scope="user",
                key="general",
                operation="WRITE",
                time_scale=time_scale,
                value_snapshot=content,
                actor=str(user_id),
            )
            await session.commit()

        return row_id

    async def evict(
        self,
        *,
        entry_id: UUID,
        tenant_id: UUID | None = None,
        trace_context: TraceContext | None = None,
    ) -> None:
        """Delete by id, filtered by tenant_id (multi-tenant safety).

        SELECT-before-DELETE captures the old content for the ops-history
        snapshot (the DELETE itself reads nothing back). If the row is absent
        (already gone), no op row is recorded (no fabrication).
        """
        if tenant_id is None:
            return

        async with self._session_factory() as session:
            old = (
                await session.execute(
                    select(MemoryUser.content, MemoryUser.user_id).where(
                        MemoryUser.id == entry_id,
                        MemoryUser.tenant_id == tenant_id,
                    )
                )
            ).first()
            await session.execute(
                delete(MemoryUser).where(
                    MemoryUser.id == entry_id,
                    MemoryUser.tenant_id == tenant_id,
                )
            )
            if old is not None:
                old_content, old_user_id = old
                # Ops-history emit (same txn — Risk C).
                _record_memory_op(
                    session,
                    tenant_id=tenant_id,
                    user_id=old_user_id,
                    scope="user",
                    key="general",
                    operation="EVICT",
                    time_scale=None,
                    value_snapshot=old_content,
                    actor=str(old_user_id) if old_user_id is not None else None,
                )
            await session.commit()

    async def resolve(
        self,
        hint: MemoryHint,
        *,
        trace_context: TraceContext | None = None,
    ) -> str:
        """Materialize full content from a hint (lookup by hint_id)."""
        async with self._session_factory() as session:
            stmt = select(MemoryUser.content).where(MemoryUser.id == hint.hint_id)
            if hint.tenant_id is not None:
                stmt = stmt.where(MemoryUser.tenant_id == hint.tenant_id)
            result = (await session.execute(stmt)).scalar_one_or_none()
        return result if result is not None else ""

    @staticmethod
    def _row_to_hint(row: MemoryUser, *, query: str) -> MemoryHint:
        """Map MemoryUser ORM row to MemoryHint dataclass."""
        meta = row.metadata_ or {}
        time_scale = meta.get("time_scale", "long_term")
        if time_scale not in ("short_term", "long_term", "semantic"):
            time_scale = "long_term"

        last_verified_raw = meta.get("last_verified_at")
        last_verified_at: datetime | None = None
        if isinstance(last_verified_raw, str):
            try:
                last_verified_at = datetime.fromisoformat(last_verified_raw)
            except ValueError:
                last_verified_at = None

        confidence_value = float(row.confidence) if row.confidence is not None else 0.5
        # Naive relevance: substring presence boost
        relevance_score = 0.8 if query.lower() in (row.content or "").lower() else 0.4

        return MemoryHint(
            hint_id=row.id,
            layer="user",
            time_scale=time_scale,
            summary=(row.content or "")[:200],
            confidence=confidence_value,
            relevance_score=relevance_score,
            full_content_pointer=f"memory_user:{row.id}",
            timestamp=row.created_at,
            last_verified_at=last_verified_at,
            verify_before_use=bool(meta.get("verify_before_use", False)),
            source_tool_call_id=meta.get("source_tool_call_id"),
            expires_at=row.expires_at,
            tenant_id=row.tenant_id,
        )
