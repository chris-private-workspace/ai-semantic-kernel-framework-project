"""Sprint 57.135 drive-through seed: a throwaway tenant + backdated transcript rows.

Run from backend/:  python ../docs/.../sprint-57-135/artifacts/seed_drivethrough.py
Seeds a TRANSCRIPTRET_SCHED_* tenant (retention_days=30) + user + session + an OLD row
(now-60d) + a RECENT row (now-5d) in messages + message_events, then prints TENANT_ID.
Unlike 57.134 (manual apply endpoint), the Sprint 57.135 SCHEDULED job's startup sweep
(retention 30 → cutoff now-30d) should auto-delete the old row + keep the recent — no
manual call. Cleanup: DELETE the tenant (CASCADE) after the drive-through.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

sys.path.insert(0, "src")

from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState, User  # noqa: E402
from infrastructure.db.models.sessions import Message, MessageEvent, Session  # noqa: E402
from infrastructure.db.session import get_session_factory  # noqa: E402


async def main() -> None:
    now = datetime.now(timezone.utc)
    factory = get_session_factory()
    async with factory() as s:
        t = Tenant(
            code=f"TRANSCRIPTRET_SCHED_{uuid4().hex[:8]}",
            display_name="DT Scheduled Retention",
            state=TenantState.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
            retention_days=30,
        )
        s.add(t)
        await s.flush()
        u = User(tenant_id=t.id, email=f"dts_{uuid4().hex[:6]}@example.com")
        s.add(u)
        await s.flush()
        sess = Session(tenant_id=t.id, user_id=u.id, title="dts", status="active")
        s.add(sess)
        await s.flush()
        for seq, days in [(1, 60), (2, 5)]:
            created = now - timedelta(days=days)
            s.add(
                Message(
                    tenant_id=t.id,
                    session_id=sess.id,
                    sequence_num=seq,
                    turn_num=1,
                    role="user",
                    content_type="text",
                    content={"t": "x"},
                    created_at=created,
                )
            )
            s.add(
                MessageEvent(
                    tenant_id=t.id,
                    session_id=sess.id,
                    event_type="llm_request",
                    event_data={"n": seq},
                    sequence_num=seq,
                    timestamp_ms=0,
                    created_at=created,
                )
            )
        await s.commit()
        print(f"TENANT_ID={t.id}")


asyncio.run(main())
