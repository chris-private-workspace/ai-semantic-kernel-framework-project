"""Sprint 57.135 drive-through cleanup: DELETE the throwaway tenant (CASCADE).

Run from backend/ with PYTHONPATH=src:  python ../docs/.../cleanup_drivethrough.py <tenant_id>
audit_log is WORM (a trigger blocks DELETE), so DISABLE TRIGGER USER on it for the cascade,
DELETE the tenant (CASCADE removes its users/sessions/messages/events/audits), re-ENABLE.
set_config app.tenant_id satisfies the FORCE'd RLS on the transcript tables for the cascade.
"""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import text

sys.path.insert(0, "src")

from infrastructure.db.session import get_session_factory  # noqa: E402

TENANT_ID = UUID(sys.argv[1])


async def main() -> None:
    factory = get_session_factory()
    async with factory() as db:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, false)"), {"t": str(TENANT_ID)}
        )
        await db.execute(text("ALTER TABLE audit_log DISABLE TRIGGER USER"))
        await db.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": str(TENANT_ID)})
        await db.execute(text("ALTER TABLE audit_log ENABLE TRIGGER USER"))
        await db.commit()
        print("CLEANED_UP")


asyncio.run(main())
