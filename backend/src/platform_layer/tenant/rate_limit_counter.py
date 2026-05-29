"""
File: backend/src/platform_layer/tenant/rate_limit_counter.py
Purpose: RedisRateLimitCounter — atomic sliding-window rate limiter + {label,value} parser.
Category: Phase 58.x SaaS / platform_layer.tenant
Scope: Sprint 57.58 (Track A) — RateLimits RuntimeEnforcement (Phase 58.x portfolio #1)

Description:
    Concrete RateLimitCounter backed by a Redis sorted-set sliding window.
    Each request appends a (score=now_ms, member=now_ms:uuid) entry to a
    per-tenant per-resource ZSET; old entries are pruned by score; ZCARD gives
    the live count. The prune-add-count sequence runs inside one atomic
    MULTI/EXEC pipeline (same atomicity precedent as QuotaEnforcer 56.1 +
    RedisBudgetStore 53.2); over-limit requests roll back the just-added entry
    (reserve-then-rollback, mirroring QuotaEnforcer.check_and_reserve). Pipeline
    (not Lua) is used so fakeredis — the CI Redis double — can exercise it (it
    does not emulate EVAL / SCRIPT LOAD).

    DI pattern (mirrors quota.py:171 record_usage): the caller injects
    redis.asyncio.Redis; this module owns no connection lifecycle. App startup
    creates the client + calls set_rate_limit_counter(); tests inject a
    fakeredis-backed instance.

    Also exposes parse_rate_limit_value() — the stored config is the Sprint
    57.48/57.57 {label, value} UI-display shape (e.g. {"label": "API requests",
    "value": "100 / min"}), NOT a pre-parsed numeric shape. This helper
    converts those display strings into the (limit, window_seconds, resource)
    tuple the counter needs. Unparseable items return None and are skipped by
    callers (fail-open — a malformed admin config never blocks).

Key Components:
    - RedisRateLimitCounter: RateLimitCounter impl (MULTI/EXEC sliding window)
    - ParsedRateLimit: (resource, limit, window_seconds) for a {label, value} item
    - parse_rate_limit_value / parse_rate_limit_item: {label, value} -> numeric
    - get/set/reset/maybe_get_rate_limit_counter: singleton accessors + test hook

Created: 2026-05-28 (Sprint 57.58)
Last Modified: 2026-05-28

Modification History (newest-first):
    - 2026-05-29: Sprint 57.62 Track A — record 80%-threshold usage alert in _write_through
    - 2026-05-28: Sprint 57.59 US-3 — usage-table write-through + Redis recovery (AP-4 close)
    - 2026-05-28: Sprint 57.58 Track A — initial creation (RateLimits RuntimeEnforcement)

Related:
    - platform_layer/tenant/_rate_limit_contracts.py — RateLimitCounter ABC
    - platform_layer/tenant/quota.py — DI + singleton + reset-hook precedent
    - infrastructure/db/models/api_keys.py:RateLimit — durable usage backing table
    - api/v1/admin/tenants.py — DEFAULT_RATE_LIMITS / {label, value} stored shape
    - testing.md section Module-level Singleton Reset Pattern
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from platform_layer.tenant._rate_limit_contracts import (
    RateLimitCounter,
    RateLimitCounterState,
    RateLimitDecision,
)
from platform_layer.tenant.rate_limit_alert_store import RateLimitAlertStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    # Type alias for the optional DB session factory the counter uses for usage-
    # table write-through + Redis-restart recovery (Sprint 57.59). None disables
    # persistence (e.g. unit tests with no DB, dev without Postgres) — the Redis
    # hot-path is unaffected. get_session_factory() returns an async_sessionmaker,
    # so the factory is a zero-arg callable yielding one (call factory() to enter
    # a session: `async with self._session_factory()() as session`).
    SessionFactory = Callable[[], async_sessionmaker[AsyncSession]]

logger = logging.getLogger(__name__)


# === Sliding-window implementation strategy ============================
# Why pipeline (MULTI/EXEC) instead of a server-side Lua script:
#   - The codebase's atomic-counter precedent (QuotaEnforcer 56.1 +
#     RedisBudgetStore 53.2) uses transactional pipelines, NOT Lua. Matching
#     that keeps one mental model across the platform.
#   - fakeredis (the CI Redis double, no live Redis service) does not emulate
#     EVAL / SCRIPT LOAD — Lua would be untestable in CI.
# Atomicity: the prune + add + count run inside a single MULTI/EXEC pipeline, so
# concurrent workers cannot interleave between add and count. When the post-add
# count exceeds the limit we ROLL BACK the just-added entry (ZREM) — same
# reserve-then-rollback shape as QuotaEnforcer.check_and_reserve's decrby. The
# tiny window where an over-limit member exists before rollback only ever makes
# the limiter STRICTER (a concurrent peek may see count==limit+1 transiently),
# never more permissive, so it cannot leak capacity.
# Sorted-set sliding window (vs fixed INCR bucket) avoids the 2x-burst-at-
# bucket-boundary problem. Token bucket rejected: more state/tuning than v1 needs.


# === {label, value} parsing ============================================
# Why: the stored config (Sprint 57.48/57.57) is admin-facing display strings
# like {"label": "API requests", "value": "100 / min"}, NOT numeric. Runtime
# enforcement needs (resource, limit, window_seconds). We parse here so both
# the middleware (Track A) and the usage endpoint (Track C) share one mapping.

# Map a free-form display label to a canonical resource key. Falls back to a
# slugified label so operator-defined custom labels still get a stable key.
_LABEL_TO_RESOURCE: dict[str, str] = {
    "api requests": "api_requests",
    "tool calls": "tool_calls",
    "sse connections": "sse_connections",
}

_WINDOW_TO_SECONDS: dict[str, int] = {
    "sec": 1,
    "second": 1,
    "min": 60,
    "minute": 60,
    "hour": 3600,
    "hr": 3600,
    "day": 86400,
}

# e.g. "100 / min", "1,000 / minute", "50 / hour". Concurrency-style values
# like "50 concurrent" do NOT match (no time window) -> skipped by callers.
_VALUE_RE = re.compile(r"^\s*([\d,]+)\s*/\s*([a-zA-Z]+)\s*$")


# Canonical window length (seconds) -> table window_type label. Module-level so
# both the counter (write-through / recovery) and the usage GET endpoint (table
# fallback) map a parsed window length to the SAME rate_limits.window_type the
# config row uses, keeping the unique-key reads/writes consistent (Sprint 57.59).
_SECONDS_TO_WINDOW_TYPE: dict[int, str] = {1: "sec", 60: "min", 3600: "hour", 86400: "day"}


def window_type_for_seconds(window_seconds: int) -> str:
    """Map a window length (seconds) to the rate_limits table window_type label."""
    return _SECONDS_TO_WINDOW_TYPE.get(window_seconds, f"{window_seconds}s")


@dataclass(frozen=True)
class ParsedRateLimit:
    """A {label, value} config item parsed into enforceable numeric form."""

    resource: str
    limit: int
    window_seconds: int


def label_to_resource(label: str) -> str:
    """Canonical resource key for a display label (slug fallback for custom)."""
    key = label.strip().lower()
    if key in _LABEL_TO_RESOURCE:
        return _LABEL_TO_RESOURCE[key]
    slug = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return slug or "unknown"


def parse_rate_limit_value(value: str) -> tuple[int, int] | None:
    """Parse a "<N> / <window>" display string into (limit, window_seconds).

    Returns None for non-rate values (e.g. "50 concurrent") or malformed
    strings — callers skip these (fail-open; a bad config never blocks).
    """
    m = _VALUE_RE.match(value or "")
    if m is None:
        return None
    raw_limit, raw_window = m.group(1), m.group(2).lower()
    window_seconds = _WINDOW_TO_SECONDS.get(raw_window)
    if window_seconds is None:
        return None
    try:
        limit = int(raw_limit.replace(",", ""))
    except ValueError:
        return None
    if limit <= 0:
        return None
    return limit, window_seconds


def parse_rate_limit_item(item: object) -> ParsedRateLimit | None:
    """Parse a stored {label, value} dict into ParsedRateLimit (None if skip)."""
    if not isinstance(item, dict):
        return None
    label = str(item.get("label", ""))
    value = str(item.get("value", ""))
    if not label:
        return None
    parsed = parse_rate_limit_value(value)
    if parsed is None:
        return None
    limit, window_seconds = parsed
    return ParsedRateLimit(
        resource=label_to_resource(label),
        limit=limit,
        window_seconds=window_seconds,
    )


class RedisRateLimitCounter(RateLimitCounter):
    """Sliding-window rate-limit counter backed by a Redis sorted set.

    Sprint 57.59 (US-3): the counter optionally write-throughs each window's
    live ``used`` count to the durable ``rate_limits`` usage table and, on a
    Redis cache miss for a still-open window, recovers the count from that
    table — this is what activates the formerly-Potemkin ``rate_limits`` table
    (AP-4 close). The DB session factory is injected the same DI way Redis is
    (constructor param); ``None`` (default) disables persistence so unit tests
    + dev-without-Postgres keep the pure-Redis behaviour. Both persistence
    paths are best-effort + fail-open — the Redis hot-path decision is taken
    BEFORE any DB I/O, and any DB error logs + continues (rate limiting MUST
    NOT break the request, plan §R1/§R4).
    """

    def __init__(
        self,
        client: "Redis[bytes]",  # type: ignore[type-arg, unused-ignore]
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._client = client
        # Optional durable backing (Sprint 57.59). When None, the counter is
        # Redis-only (the Sprint 57.58 behaviour) — write-through + recovery
        # are skipped. App startup injects get_session_factory; tests that
        # exercise persistence inject the test session factory.
        self._session_factory = session_factory

    @staticmethod
    def _key(tenant_id: UUID, resource: str) -> str:
        # Multi-tenant rule: tenant_id is the first key segment so counters
        # cannot cross-tenant leak (per .claude/rules/multi-tenant-data.md).
        return f"rate_limit:{tenant_id}:{resource}"

    @staticmethod
    def _window_type_for_seconds(window_seconds: int) -> str:
        """Map a window length (seconds) to the table's window_type label.

        Delegates to the module-level window_type_for_seconds so the counter
        write-through and the usage GET endpoint's table fallback agree.
        """
        return window_type_for_seconds(window_seconds)

    @staticmethod
    def _window_bounds(now_ms: int, window_seconds: int) -> tuple[datetime, datetime]:
        """Compute (window_start, window_end) anchored to the window boundary.

        window_start = floor(now to the window_seconds boundary); window_end =
        window_start + window_seconds. Both timezone-aware UTC (the table's
        columns are timestamptz NOT NULL — Day 0 D-DAY0-G). Anchoring to the
        boundary makes the unique (tenant, resource, window_type, window_start)
        key stable across requests within the same window so write-through
        upserts the SAME row instead of inserting per request.
        """
        now_s = now_ms / 1000.0
        start_s = (int(now_s) // window_seconds) * window_seconds
        window_start = datetime.fromtimestamp(start_s, tz=timezone.utc)
        window_end = window_start + timedelta(seconds=window_seconds)
        return window_start, window_end

    async def _write_through(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
        used: int,
        limit: int,
    ) -> None:
        """Best-effort upsert of the live window's used count to rate_limits.

        Fail-open: any error (no factory, DB down, RLS) logs + returns; the
        Redis decision already happened so the request is unaffected. The row
        is keyed by the unique (tenant_id, resource_type, window_type,
        window_start) so concurrent requests in the same window converge on one
        row (used = GREATEST(existing, this count) to tolerate out-of-order
        write-through). quota is a denormalised config snapshot (plan §R9).
        """
        if self._session_factory is None:
            return
        try:
            from infrastructure.db.models.api_keys import RateLimit

            now_ms = int(time.time() * 1000)
            window_type = self._window_type_for_seconds(window_seconds)
            window_start, window_end = self._window_bounds(now_ms, window_seconds)

            factory = self._session_factory()
            async with factory() as session:
                # Multi-tenant: usage rows carry tenant_id; the RLS INSERT/UPDATE
                # policy checks it. Set the tenant context for this session so
                # the policy's current_setting('app.tenant_id') matches.
                await self._set_tenant_context(session, tenant_id)
                stmt = (
                    pg_insert(RateLimit)
                    .values(
                        tenant_id=tenant_id,
                        resource_type=resource,
                        window_type=window_type,
                        quota=limit,
                        used=used,
                        window_start=window_start,
                        window_end=window_end,
                    )
                    .on_conflict_do_update(
                        constraint="uq_rate_limits_tenant_window",
                        set_={
                            "used": func.greatest(RateLimit.used, used),
                            "quota": limit,
                            "window_end": window_end,
                        },
                    )
                )
                await session.execute(stmt)
                # Sprint 57.62: record a durable 80%-threshold usage alert at the
                # enforcement point (so breaches are captured even when no admin is
                # polling live usage). Rides this method's best-effort try/except —
                # an alert failure must NEVER break enforcement. The session already
                # carries the tenant context (set above for the rate_limits RLS
                # policies), which the rate_limit_alerts RLS policies also read.
                # Idempotent per (tenant, resource, window_type, window_start) so
                # repeated crossings in one window upsert the same row.
                await RateLimitAlertStore().maybe_record(
                    session,
                    tenant_id,
                    resource,
                    window_type,
                    used=used,
                    quota=limit,
                    window_start=window_start,
                )
                await session.commit()
        except Exception:  # noqa: BLE001 — fail-open: usage persistence never blocks
            logger.warning(
                "rate_limit_counter: usage write-through failed; failing open",
                exc_info=True,
            )

    async def _recover_from_table(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
    ) -> int | None:
        """Seed the Redis counter from the table on a cache miss (Redis restart).

        Returns the recovered ``used`` for the CURRENT still-open window
        (window_end > now), else None. Best-effort + fail-open. The recovered
        count is replayed into Redis as a single synthetic member scored at the
        window_start so subsequent check_and_increment sees the right baseline
        (approximation — exact per-request timestamps are not persisted; the
        durable backing is for "survive a restart without resetting the gate to
        zero", not perfect reconstruction).
        """
        if self._session_factory is None:
            return None
        try:
            from infrastructure.db.models.api_keys import RateLimit

            now = datetime.now(tz=timezone.utc)
            window_type = self._window_type_for_seconds(window_seconds)
            factory = self._session_factory()
            async with factory() as session:
                await self._set_tenant_context(session, tenant_id)
                result = await session.execute(
                    select(RateLimit.used, RateLimit.window_start)
                    .where(
                        RateLimit.tenant_id == tenant_id,
                        RateLimit.resource_type == resource,
                        RateLimit.window_type == window_type,
                        RateLimit.window_end > now,
                    )
                    .order_by(RateLimit.window_end.desc())
                    .limit(1)
                )
                row = result.first()
            if row is None:
                return None
            used = int(row[0])
            window_start = row[1]
            if used <= 0:
                return 0
            # Replay `used` synthetic members into the Redis window so the gate
            # resumes from the persisted baseline. Score them at window_start ms
            # so the normal sliding-window prune ages them out correctly.
            key = self._key(tenant_id, resource)
            start_ms = int(window_start.timestamp() * 1000)
            # Keys are str, values int (matches the inferred dict[str, int] of the
            # check_and_increment zadd below). Cross-platform mypy (Risk Class B,
            # code-quality.md): Linux redis stub's zadd AnyKeyT type-var rejects a
            # str|bytes union key, Windows stub wants Mapping[str|bytes, ...] and
            # rejects the narrow dict[str, int] with [arg-type] — dual ignore so both
            # platforms pass (FIX post-PR-#210).
            mapping: dict[str, int] = {
                f"recover:{i}:{uuid.uuid4().hex}": start_ms + i for i in range(used)
            }
            await self._client.zadd(key, mapping)  # type: ignore[arg-type, unused-ignore]
            await self._client.expire(key, window_seconds + 1)
            return used
        except Exception:  # noqa: BLE001 — fail-open: recovery never blocks
            logger.warning(
                "rate_limit_counter: usage recovery failed; failing open",
                exc_info=True,
            )
            return None

    @staticmethod
    async def _set_tenant_context(session: "AsyncSession", tenant_id: UUID) -> None:
        """Set app.tenant_id (txn-local) so the rate_limits RLS policy matches.

        rate_limits is an RLS table (migration 0009); the INSERT WITH CHECK +
        SELECT/UPDATE USING policies read current_setting('app.tenant_id'). The
        counter owns its own session here (not a request session) so it must set
        the context itself. Uses set_config(..., is_local=true) — the bind-param
        form (SET LOCAL cannot take $1 under asyncpg) per the correction_loop.py
        precedent; safe (no injection).
        """
        from sqlalchemy import text

        await session.execute(
            text("SELECT set_config('app.tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )

    @staticmethod
    def _oldest_score_ms(oldest: list[Any]) -> float | None:
        """Extract the oldest entry's score (ms) from a ZRANGE WITHSCORES row."""
        if not oldest:
            return None
        # ZRANGE WITHSCORES returns [(member, score)] tuples.
        first = oldest[0]
        if isinstance(first, (tuple, list)) and len(first) >= 2:
            return float(first[1])
        return None

    async def check_and_increment(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
        limit: int,
    ) -> RateLimitDecision:
        key = self._key(tenant_id, resource)
        now_ms = int(time.time() * 1000)
        cutoff = now_ms - window_seconds * 1000
        member = f"{now_ms}:{uuid.uuid4().hex}"

        # Sprint 57.59: on a Redis cache miss (empty window — e.g. fresh restart)
        # seed the counter from the durable usage table so the gate resumes from
        # the persisted baseline instead of resetting to zero. Best-effort: a
        # no-op when persistence is disabled or no open window row exists. Done
        # BEFORE the increment so the recovered members are counted below.
        pre_count = int(await self._client.zcard(key))
        if pre_count == 0 and self._session_factory is not None:
            await self._recover_from_table(tenant_id, resource, window_seconds)

        # Atomic prune + add + count in one MULTI/EXEC (see strategy note above).
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, "-inf", cutoff)
            pipe.zadd(key, {member: now_ms})
            pipe.zcard(key)
            pipe.expire(key, window_seconds + 1)
            results = await pipe.execute()
        count = int(results[2])

        oldest = await self._client.zrange(key, 0, 0, withscores=True)
        oldest_ms = self._oldest_score_ms(cast("list[Any]", oldest))

        if count <= limit:
            # Best-effort durable backing of the live window count (AP-4 close).
            await self._write_through(tenant_id, resource, window_seconds, count, limit)
            reset_at_ms = (oldest_ms if oldest_ms is not None else now_ms) + window_seconds * 1000
            return RateLimitDecision(
                allowed=True,
                remaining=max(0, limit - count),
                retry_after=0,
                reset_at=int(reset_at_ms / 1000),
            )

        # Over limit: roll back the entry we optimistically added (reserve-then-
        # rollback, mirroring QuotaEnforcer.check_and_reserve decrby).
        await self._client.zrem(key, member)
        # Persist the at-limit count (count-1 after rollback) so the table tracks
        # the saturated window too (best-effort; never blocks the 429).
        await self._write_through(tenant_id, resource, window_seconds, max(0, count - 1), limit)
        # Recompute oldest AFTER rollback so reset/retry reflect the real window.
        oldest = await self._client.zrange(key, 0, 0, withscores=True)
        oldest_ms = self._oldest_score_ms(cast("list[Any]", oldest))
        reset_at_ms = (oldest_ms if oldest_ms is not None else now_ms) + window_seconds * 1000
        retry_after = max(1, int((reset_at_ms - now_ms + 999) / 1000))
        return RateLimitDecision(
            allowed=False,
            remaining=0,
            retry_after=retry_after,
            reset_at=int(reset_at_ms / 1000),
        )

    async def peek(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
    ) -> RateLimitCounterState:
        key = self._key(tenant_id, resource)
        now_ms = int(time.time() * 1000)
        cutoff = now_ms - window_seconds * 1000

        # Prune + count atomically; read-only w.r.t. the window (no new member).
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, "-inf", cutoff)
            pipe.zcard(key)
            results = await pipe.execute()
        count = int(results[1])

        oldest = await self._client.zrange(key, 0, 0, withscores=True)
        oldest_ms = self._oldest_score_ms(cast("list[Any]", oldest))
        reset_at = int((oldest_ms + window_seconds * 1000) / 1000) if oldest_ms is not None else 0
        return RateLimitCounterState(count=count, reset_at=reset_at)


# === Singleton accessors (mirror quota.py get/set/reset/maybe_get) ===
_counter: RateLimitCounter | None = None


def get_rate_limit_counter() -> RateLimitCounter:
    """Strict accessor — raises if uninitialised (use in endpoints)."""
    if _counter is None:
        raise RuntimeError(
            "RateLimitCounter not initialised; call set_rate_limit_counter() at "
            "app startup or in a test fixture"
        )
    return _counter


def maybe_get_rate_limit_counter() -> RateLimitCounter | None:
    """Lenient accessor — returns None if uninitialised (fail-open callers).

    The middleware and tool-layer hook use this so dev / test runs without
    Redis (or before startup wiring) simply skip enforcement instead of 500.
    """
    return _counter


def set_rate_limit_counter(counter: RateLimitCounter | None) -> None:
    """Install the singleton (app startup or test fixture)."""
    global _counter
    _counter = counter


def reset_rate_limit_counter() -> None:
    """Test isolation hook (per testing.md section Module-level Singleton Reset Pattern)."""
    global _counter
    _counter = None
