"""Sprint 57.135 drive-through verifier: a tenant's remaining messages + scheduled-retention audits.

Run from backend/ with PYTHONPATH=src:
    python ../docs/.../sprint-57-135/artifacts/verify_sweep.py <tenant_id>
Prints MESSAGES (remaining message rows) + SCHEDULED_AUDITS (count of
tenant_transcript_retention_scheduled audit rows) for the tenant. After the scheduled job's
startup sweep, a throwaway tenant seeded with old(now-60d)+recent(now-5d) at retention 30 should
show MESSAGES=1 (recent survived) + SCHEDULED_AUDITS>=1.
"""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import func, select, text

sys.path.insert(0, "src")

from infrastructure.db.models.audit import AuditLog  # noqa: E402
from infrastructure.db.models.sessions import Message  # noqa: E402
from infrastructure.db.session import get_session_factory  # noqa: E402

TENANT_ID = UUID(sys.argv[1])


async def main() -> None:
    factory = get_session_factory()
    async with factory() as db:
        # FORCE RLS on messages / audit_log → set the tenant context for this read txn.
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, false)"), {"t": str(TENANT_ID)}
        )
        msgs = (
            await db.execute(
                select(func.count()).select_from(Message).where(Message.tenant_id == TENANT_ID)
            )
        ).scalar_one()
        audits = (
            await db.execute(
                select(func.count())
                .select_from(AuditLog)
                .where(
                    AuditLog.tenant_id == TENANT_ID,
                    AuditLog.operation == "tenant_transcript_retention_scheduled",
                )
            )
        ).scalar_one()
        print(f"MESSAGES={msgs} SCHEDULED_AUDITS={audits}")


asyncio.run(main())
