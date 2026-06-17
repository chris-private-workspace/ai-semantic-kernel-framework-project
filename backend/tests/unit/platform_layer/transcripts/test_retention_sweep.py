"""
File: backend/tests/unit/platform_layer/transcripts/test_retention_sweep.py
Purpose: Unit tests for run_transcript_retention_sweep (per-tenant apply+audit+commit, fail-open).
Category: Tests / platform_layer / transcripts
Scope: Phase 57 / Sprint 57.135 (scheduled transcript-retention job)

Created: 2026-06-17
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

import platform_layer.transcripts.retention as retention_mod
from platform_layer.transcripts.retention import (
    RetentionStats,
    SweepStats,
    run_transcript_retention_sweep,
)

# NOTE: no module-level pytest.mark.asyncio — asyncio mode=AUTO auto-runs the async tests.

_CUTOFF = datetime(2026, 6, 17, tzinfo=timezone.utc)


class _FakeRows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    """Async-CM session: the read session returns enum rows; per-tenant sessions count commits."""

    def __init__(self, enum_rows: list[Any] | None) -> None:
        self._enum_rows = enum_rows
        self.commits = 0

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    async def execute(self, *a: Any, **k: Any) -> _FakeRows:
        return _FakeRows(self._enum_rows or [])

    async def commit(self) -> None:
        self.commits += 1


class _FakeFactory:
    """Call 0 → read session (enum rows); calls 1.. → per-tenant sessions (one per tenant)."""

    def __init__(self, enum_rows: list[Any]) -> None:
        self._enum_rows = enum_rows
        self.sessions: list[_FakeSession] = []

    def __call__(self) -> _FakeSession:
        is_read = len(self.sessions) == 0
        session = _FakeSession(self._enum_rows if is_read else None)
        self.sessions.append(session)
        return session


async def test_sweep_processes_all_tenants(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every tenant gets apply + a system audit + a commit; stats aggregate across tenants."""
    t1, t2 = uuid4(), uuid4()
    factory = _FakeFactory([(t1, 30), (t2, 7)])
    audits: list[dict[str, Any]] = []

    async def fake_apply(
        db: Any, tid: Any, rd: int, *, now: Any = None, dry_run: bool = False
    ) -> RetentionStats:
        return RetentionStats(
            messages=2 if tid == t1 else 1,
            events=3 if tid == t1 else 0,
            cutoff=_CUTOFF,
        )

    async def fake_audit(db: Any, **kw: Any) -> None:
        audits.append(kw)

    monkeypatch.setattr(retention_mod, "apply_transcript_retention", fake_apply)
    monkeypatch.setattr("infrastructure.db.audit_helper.append_audit", fake_audit)

    stats = await run_transcript_retention_sweep(factory)  # type: ignore[arg-type]

    assert isinstance(stats, SweepStats)
    assert stats.tenants_processed == 2
    assert stats.tenants_failed == 0
    assert stats.total_messages == 3  # 2 + 1
    assert stats.total_events == 3  # 3 + 0
    # 1 read session + 2 per-tenant sessions; each per-tenant session committed exactly once
    assert len(factory.sessions) == 3
    assert factory.sessions[1].commits == 1
    assert factory.sessions[2].commits == 1
    # audited per tenant with the scheduled operation + a system (user_id=None) actor
    assert len(audits) == 2
    assert all(a["operation"] == "tenant_transcript_retention_scheduled" for a in audits)
    assert all(a["user_id"] is None for a in audits)


async def test_sweep_fail_open_per_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    """A per-tenant exception is isolated: tenants_failed increments, the rest still process."""
    good, bad = uuid4(), uuid4()
    factory = _FakeFactory([(bad, 30), (good, 30)])

    async def fake_apply(
        db: Any, tid: Any, rd: int, *, now: Any = None, dry_run: bool = False
    ) -> RetentionStats:
        if tid == bad:
            raise RuntimeError("simulated per-tenant DB flake")
        return RetentionStats(messages=4, events=0, cutoff=_CUTOFF)

    async def fake_audit(db: Any, **kw: Any) -> None:
        return None

    monkeypatch.setattr(retention_mod, "apply_transcript_retention", fake_apply)
    monkeypatch.setattr("infrastructure.db.audit_helper.append_audit", fake_audit)

    stats = await run_transcript_retention_sweep(factory)  # type: ignore[arg-type]

    assert stats.tenants_processed == 1
    assert stats.tenants_failed == 1
    assert stats.total_messages == 4  # only the good tenant's deletion counted


async def test_sweep_no_tenants() -> None:
    """No tenants → all-zero stats; only the read session is opened."""
    factory = _FakeFactory([])
    stats = await run_transcript_retention_sweep(factory)  # type: ignore[arg-type]
    assert stats == SweepStats(0, 0, 0, 0)
    assert len(factory.sessions) == 1


async def test_sweep_passes_now_to_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    """The injected `now` is threaded to apply_transcript_retention (deterministic cutoff)."""
    tid = uuid4()
    factory = _FakeFactory([(tid, 90)])
    seen_now: list[Any] = []
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)

    async def fake_apply(
        db: Any, t: Any, rd: int, *, now: Any = None, dry_run: bool = False
    ) -> RetentionStats:
        seen_now.append(now)
        return RetentionStats(messages=0, events=0, cutoff=fixed)

    async def fake_audit(db: Any, **kw: Any) -> None:
        return None

    monkeypatch.setattr(retention_mod, "apply_transcript_retention", fake_apply)
    monkeypatch.setattr("infrastructure.db.audit_helper.append_audit", fake_audit)

    await run_transcript_retention_sweep(factory, now=fixed)  # type: ignore[arg-type]
    assert seen_now == [fixed]
