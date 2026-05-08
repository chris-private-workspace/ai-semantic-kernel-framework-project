"""
File: backend/src/infrastructure/db/repositories/__init__.py
Purpose: ORM repository pattern — DAO layer between routers and models.
Category: Infrastructure / Repositories (Sprint 57.7 US-R1)

Description:
    Repository classes encapsulate ORM operations (INSERT/UPDATE/SELECT)
    so routers + observers don't compose SQLAlchemy queries inline. Each
    repository owns ONE root entity (Session / ToolCall) and exposes
    coarse-grained methods (create_session / create) that match observer
    event semantics 1:1.

    Sprint 57.7 US-R1 (AD-Reality-3a + 3b closure): introduces the first
    two repos for sessions + tool_calls observer wiring at chat router.

Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 2)
Last Modified: 2026-05-10
"""

from infrastructure.db.repositories.session_repository import SessionRepository
from infrastructure.db.repositories.tool_call_repository import ToolCallRepository

__all__ = ["SessionRepository", "ToolCallRepository"]
