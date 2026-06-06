"""
File: backend/src/platform_layer/billing/billing_outbox.py
Purpose: Transactional billing Outbox — idempotent enqueue (producer) + idempotent drain (consumer).
Category: platform_layer.billing (C-15 billing-write-atomicity leg)
Scope: Sprint 57.84 / US-1 + US-2 + US-3 + US-4

Description:
    Producer (BillingOutboxService.enqueue): the chat request observer writes a
    chargeable LLM/tool event into billing_outbox using the REQUEST's session,
    so the cost event commits atomically with the request (no best-effort
    swallow → no 漏扣). Idempotent: ON CONFLICT (tenant_id, idempotency_key)
    DO NOTHING, so a redelivered event is a no-op enqueue.

    Consumer (BillingOutboxDrainer.drain_once): a background poller claims due
    rows one-at-a-time (FOR UPDATE SKIP LOCKED), sets the row's tenant context,
    materializes cost_ledger via the EXISTING CostLedgerService (pricing
    single-source, C-11 unchanged), and marks the row `done` IN THE SAME
    transaction — exactly-once materialization, so a crash mid-row re-claims
    rather than double-charges (no 雙扣). A materialize failure rolls back the
    cost write (nothing billed) and records retry/backoff; after MAX_RETRY the
    row dead-letters (status=failed, next_retry_at=NULL → no longer claimed).

    Cross-tenant drain (US-4): the poller claims under the all-zeros system
    sentinel (the billing_outbox RLS USING escape) and SET LOCAL app.tenant_id =
    row.tenant_id before each cost_ledger insert (cost_ledger keeps its own RLS).

    LLM neutrality: payload carries only neutral record_llm_call args; no SDK
    import. Pricing resolved by the injected PricingLoader inside the drainer.

Key Components:
    - DrainStats: per-drain-cycle counters
    - BillingOutboxService: enqueue (producer)
    - BillingOutboxDrainer: drain_once (consumer poller body)
    - llm_idempotency_key / tool_idempotency_key: stable per-event keys
    - set_/get_/maybe_get_billing_outbox: enqueue-service singleton (+ reset hook)

Created: 2026-06-05 (Sprint 57.84)

Modification History:
    - 2026-06-05: Initial creation (Sprint 57.84 / US-1..US-4)

Related:
    - infrastructure/db/models/billing_outbox.py:BillingOutboxEvent — ORM
    - migrations/versions/0025_billing_outbox.py — table + RLS (sentinel escape)
    - platform_layer/billing/cost_ledger.py — drain target (pricing single-source)
    - platform_layer/billing/pricing.py — PricingLoader (injected into drainer)
    - 17-cross-category-interfaces.md — BillingOutbox enqueue/drain contract
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per cost write)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.db.models.billing_outbox import BillingOutboxEvent
from platform_layer.billing.cost_ledger import CostLedgerService
from platform_layer.billing.pricing import PricingLoader

# The all-zeros tenant sentinel matches the billing_outbox RLS USING escape
# (0025_billing_outbox.py): under this context the poller sees rows across
# tenants for the claim. A real request never runs under it (missing JWT → 401).
SYSTEM_SENTINEL_TENANT = "00000000-0000-0000-0000-000000000000"

# Retry backoff: next_retry_at = now + min(BASE * 2**(retry-1), CAP).
_BASE_BACKOFF_S = 2
_MAX_BACKOFF_S = 3600


def llm_idempotency_key(session_id: UUID, sub_type_suffix: str) -> str:
    """Stable key for an LLM cost event (loop vs _verification are distinct)."""
    return f"{session_id}:llm:{sub_type_suffix or 'loop'}"


def tool_idempotency_key(session_id: UUID, tool_name: str, seq: int) -> str:
    """Stable key for a tool cost event (per-request monotonic seq disambiguates
    repeated same-tool calls in one loop; a replay reuses the same seq → no-op)."""
    return f"{session_id}:tool:{tool_name}:{seq}"


@dataclass
class DrainStats:
    """Counters for one drain_once cycle."""

    claimed: int = 0
    materialized: int = 0
    failed: int = 0
    dead_lettered: int = 0


# === BillingOutboxService: producer (atomic, idempotent enqueue) ===
# Why: the chat observer used a best-effort try/except direct cost_ledger write
# (router.py) that swallowed failures → 漏扣. Enqueuing into billing_outbox in
# the REQUEST txn makes the cost event durable atomically with the request.
class BillingOutboxService:
    """Stateless producer; enqueue uses the caller's request session."""

    async def enqueue(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, object],
        idempotency_key: str,
        session_id: UUID | None = None,
    ) -> None:
        """Insert one outbox row in the caller's transaction; idempotent.

        ON CONFLICT (tenant_id, idempotency_key) DO NOTHING — a redelivered
        logical event is a no-op (does not raise, does not re-queue). The row
        commits with the request's own commit (atomic with session/audit).
        """
        stmt = (
            pg_insert(BillingOutboxEvent)
            .values(
                tenant_id=tenant_id,
                event_type=event_type,
                payload=payload,
                idempotency_key=idempotency_key,
                session_id=session_id,
            )
            .on_conflict_do_nothing(constraint="uq_billing_outbox_idem")
        )
        await db.execute(stmt)


# === BillingOutboxDrainer: consumer (exactly-once idempotent drain) ===
# Why: decouples the (future Stripe / current cost_ledger) write from the
# request. Claim+materialize+mark-done in ONE txn = exactly-once; failures roll
# back the cost write and reschedule. Single-instance poller today; SKIP LOCKED
# keeps it multi-instance-safe.
class BillingOutboxDrainer:
    """Drains billing_outbox into cost_ledger, idempotently, with retry/backoff."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        pricing_loader: PricingLoader,
        *,
        batch: int = 50,
        max_retry: int = 8,
    ) -> None:
        self._session_factory = session_factory
        self._pricing = pricing_loader
        self._batch = batch
        self._max_retry = max_retry

    async def drain_once(self) -> DrainStats:
        """Process up to `batch` due rows, one independent transaction each."""
        stats = DrainStats()
        for _ in range(self._batch):
            outcome = await self._drain_one()
            if outcome is None:
                break  # no more due rows this cycle
            stats.claimed += 1
            if outcome == "done":
                stats.materialized += 1
            elif outcome == "dead_letter":
                stats.dead_lettered += 1
            else:  # "failed"
                stats.failed += 1
        return stats

    async def _drain_one(self) -> str | None:
        """Claim + materialize + mark one due row. Returns the outcome, or None
        when there is no due row to claim."""
        async with self._session_factory() as db:
            await self._set_tenant(db, SYSTEM_SENTINEL_TENANT)
            row = (
                (
                    await db.execute(
                        select(BillingOutboxEvent)
                        .where(
                            or_(
                                BillingOutboxEvent.status == "pending",
                                and_(
                                    BillingOutboxEvent.status == "failed",
                                    BillingOutboxEvent.next_retry_at <= func.now(),
                                ),
                            )
                        )
                        .order_by(BillingOutboxEvent.id)
                        .limit(1)
                        .with_for_update(skip_locked=True)
                    )
                )
                .scalars()
                .first()
            )
            if row is None:
                return None

            row_id = row.id
            try:
                # cost_ledger insert must run under the row's real tenant (its
                # own RLS WITH CHECK); the claim ran under the sentinel.
                await self._set_tenant(db, str(row.tenant_id))
                await self._materialize(db, row)
                row.status = "done"
                row.processed_at = _utcnow()
                row.last_error = None
                await db.commit()
                return "done"
            except Exception as exc:  # noqa: BLE001 — any materialize failure reschedules
                # The cost write (if any) + the claim are rolled back together:
                # nothing is billed, the lock releases, the session is usable.
                await db.rollback()
                return await self._record_failure(db, row_id, exc)

    async def _record_failure(self, db: AsyncSession, row_id: int, exc: Exception) -> str:
        """Bump retry/backoff (or dead-letter) in a fresh transaction."""
        await self._set_tenant(db, SYSTEM_SENTINEL_TENANT)
        row = (
            (await db.execute(select(BillingOutboxEvent).where(BillingOutboxEvent.id == row_id)))
            .scalars()
            .first()
        )
        if row is None:  # pragma: no cover — claimed row vanished (CASCADE delete)
            return "failed"
        row.retry_count += 1
        row.last_error = str(exc)[:2000]
        if row.retry_count >= self._max_retry:
            # Dead-letter: stays failed, next_retry_at NULL → no longer claimed.
            row.status = "failed"
            row.next_retry_at = None
            outcome = "dead_letter"
        else:
            row.status = "failed"
            row.next_retry_at = _utcnow() + timedelta(seconds=_backoff_seconds(row.retry_count))
            outcome = "failed"
        await db.commit()
        return outcome

    async def _materialize(self, db: AsyncSession, row: BillingOutboxEvent) -> None:
        """Write the cost_ledger entries for one outbox row via CostLedgerService."""
        cost_ledger = CostLedgerService(db=db, pricing_loader=self._pricing)
        payload = row.payload
        if row.event_type == "llm_call":
            await cost_ledger.record_llm_call(
                tenant_id=row.tenant_id,
                provider=_payload_str(payload, "provider"),
                model=_payload_str(payload, "model"),
                input_tokens=_payload_int(payload, "input_tokens"),
                output_tokens=_payload_int(payload, "output_tokens"),
                cached_input_tokens=_payload_int(payload, "cached_input_tokens", 0),
                session_id=row.session_id,
                sub_type_suffix=_payload_str(payload, "sub_type_suffix", ""),
            )
        elif row.event_type == "tool_call":
            await cost_ledger.record_tool_call(
                tenant_id=row.tenant_id,
                tool_name=_payload_str(payload, "tool_name"),
                session_id=row.session_id,
            )
        else:  # pragma: no cover — CHECK constraint blocks other values
            raise ValueError(f"unknown billing_outbox event_type: {row.event_type!r}")

    @staticmethod
    async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
        """SET LOCAL app.tenant_id for the current transaction (RLS context)."""
        # set_config(...) is the bind-param-compatible function form of SET LOCAL
        # (asyncpg rejects params on the SET utility statement). is_local=true →
        # txn-scoped, like SET LOCAL. Mirrors middleware/tenant_context.py.
        await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _backoff_seconds(retry_count: int) -> int:
    return min(_BASE_BACKOFF_S << (retry_count - 1), _MAX_BACKOFF_S)


def _payload_str(payload: dict[str, object], key: str, default: str | None = None) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"billing_outbox payload[{key!r}] expected str, got {value!r}")
    return value


def _payload_int(payload: dict[str, object], key: str, default: int | None = None) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"billing_outbox payload[{key!r}] expected int, got {value!r}")
    return value


# Module-level singleton for the enqueue producer (stateless; db passed per call).
# Reset hook per testing.md §Module-level Singleton Reset Pattern.
_service: BillingOutboxService | None = None


def get_billing_outbox() -> BillingOutboxService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "BillingOutboxService not initialised; call set_billing_outbox() at "
            "app startup or in test fixture"
        )
    return _service


def maybe_get_billing_outbox() -> BillingOutboxService | None:
    """Lenient accessor — returns None if uninitialised."""
    return _service


def set_billing_outbox(service: BillingOutboxService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


__all__ = [
    "BillingOutboxService",
    "BillingOutboxDrainer",
    "DrainStats",
    "SYSTEM_SENTINEL_TENANT",
    "llm_idempotency_key",
    "tool_idempotency_key",
    "get_billing_outbox",
    "maybe_get_billing_outbox",
    "set_billing_outbox",
]
