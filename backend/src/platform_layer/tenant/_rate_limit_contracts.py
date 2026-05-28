"""
File: backend/src/platform_layer/tenant/_rate_limit_contracts.py
Purpose: RateLimitCounter ABC + decision/state dataclasses — single-source rate-limit contracts.
Category: Platform layer / tenant (cross-cutting; ranges 9 governance + multi-tenancy)
Scope: Sprint 57.58 (Track A) — RateLimits RuntimeEnforcement (Phase 58.x portfolio #1)

    Note: sited under platform_layer/tenant/ (not middleware/) to break a circular
    import — the middleware package __init__ eagerly imports RateLimitMiddleware,
    which imports the counter, which imports these contracts; keeping the
    dependency-free contracts under tenant/ avoids re-entering middleware/__init__.

Description:
    Defines the abstraction both Track A (FastAPI middleware) and Track B (Cat 2
    tool layer) consume so the sliding-window enforcement engine is wired once
    (DRY). The middleware/tool layer depend only on this ABC; the concrete
    Redis-backed impl lives in platform_layer/tenant/rate_limit_counter.py.

    Two operations:
      - check_and_increment(): atomic gate — increments the counter and returns
        whether the request is allowed (used at enforcement time).
      - peek(): read-only inspection — returns the current count WITHOUT
        incrementing (used by the GET usage endpoint so admin-display polling
        does not perturb the enforcement counter).

Key Components:
    - RateLimitDecision: frozen result of check_and_increment (allowed/remaining/...)
    - RateLimitCounterState: frozen result of peek (count + reset_at)
    - RateLimitCounter: ABC implemented by RedisRateLimitCounter

Created: 2026-05-28 (Sprint 57.58)
Last Modified: 2026-05-28

Modification History (newest-first):
    - 2026-05-28: Sprint 57.58 Track A — initial creation (RateLimits RuntimeEnforcement)

Related:
    - platform_layer/tenant/rate_limit_counter.py — RedisRateLimitCounter impl
    - platform_layer/middleware/rate_limit.py — RateLimitMiddleware consumer
    - platform_layer/tenant/quota.py — DI pattern precedent (caller injects Redis)
    - sprint-57-58-plan.md §4.1 (middleware) / §4.3 (usage endpoint peek)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RateLimitDecision:
    """Outcome of an atomic check_and_increment against a sliding window.

    Attributes:
        allowed: True if the request is within the limit (counter was
            incremented); False if the limit is reached (counter unchanged).
        remaining: Requests left in the current window after this one
            (0 when blocked).
        retry_after: Seconds the caller should wait before retrying (0 when
            allowed). Surfaced as the HTTP ``Retry-After`` header on 429.
        reset_at: UNIX epoch seconds when the oldest in-window entry expires —
            i.e. when capacity frees up. Surfaced as ``X-RateLimit-Reset``.
    """

    allowed: bool
    remaining: int
    retry_after: int
    reset_at: int


@dataclass(frozen=True)
class RateLimitCounterState:
    """Read-only snapshot of a sliding window (no increment).

    Attributes:
        count: Number of entries currently inside the window.
        reset_at: UNIX epoch seconds when the oldest entry expires (the window
            "resets" as entries age out). 0 when the window is empty.
    """

    count: int
    reset_at: int


class RateLimitCounter(ABC):
    """Sliding-window rate-limit counter abstraction (Redis-backed in prod).

    Multi-tenant rule (per .claude/rules/multi-tenant-data.md): every key MUST
    embed tenant_id so counters cannot cross-tenant leak. Implementations own
    no connection lifecycle — the caller injects the backing store (mirrors
    QuotaEnforcer / RedisBudgetStore DI pattern).
    """

    @abstractmethod
    async def check_and_increment(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
        limit: int,
    ) -> RateLimitDecision:
        """Atomically test the limit and (if under) record this request."""
        raise NotImplementedError

    @abstractmethod
    async def peek(
        self,
        tenant_id: UUID,
        resource: str,
        window_seconds: int,
    ) -> RateLimitCounterState:
        """Read the current window count WITHOUT incrementing."""
        raise NotImplementedError
