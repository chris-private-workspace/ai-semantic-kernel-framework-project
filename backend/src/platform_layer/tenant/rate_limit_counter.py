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
    - 2026-05-28: Sprint 57.58 Track A — initial creation (RateLimits RuntimeEnforcement)

Related:
    - platform_layer/tenant/_rate_limit_contracts.py — RateLimitCounter ABC
    - platform_layer/tenant/quota.py — DI + singleton + reset-hook precedent
    - api/v1/admin/tenants.py — DEFAULT_RATE_LIMITS / {label, value} stored shape
    - testing.md section Module-level Singleton Reset Pattern
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from platform_layer.tenant._rate_limit_contracts import (
    RateLimitCounter,
    RateLimitCounterState,
    RateLimitDecision,
)

if TYPE_CHECKING:
    from redis.asyncio import Redis

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
    """Sliding-window rate-limit counter backed by a Redis sorted set."""

    def __init__(self, client: "Redis[bytes]") -> None:  # type: ignore[type-arg, unused-ignore]
        self._client = client

    @staticmethod
    def _key(tenant_id: UUID, resource: str) -> str:
        # Multi-tenant rule: tenant_id is the first key segment so counters
        # cannot cross-tenant leak (per .claude/rules/multi-tenant-data.md).
        return f"rate_limit:{tenant_id}:{resource}"

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
