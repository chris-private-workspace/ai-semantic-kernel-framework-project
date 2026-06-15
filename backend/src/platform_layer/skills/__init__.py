"""
platform_layer.skills — the per-tenant half of the Skills System (Sprint 57.114).

Re-exports TenantSkillService (per-tenant skill CRUD) + resolve_tenant_skill_registry
(the bundled+tenant overlay resolver, TTL-cached, fail-open) + the cache invalidation
/ reset hooks + the typed errors. See service.py for the full design.
"""

from __future__ import annotations

from platform_layer.skills.service import (
    SKILLS_MAX_INSTRUCTIONS_CHARS,
    SKILLS_MAX_PER_TENANT,
    DuplicateSkillError,
    SkillNotFoundError,
    SkillQuotaExceededError,
    TenantSkillError,
    TenantSkillService,
    invalidate_tenant_skill_registry,
    reset_skill_registry_cache,
    resolve_tenant_skill_registry,
    tenant_skill_service,
)

__all__ = [
    "SKILLS_MAX_INSTRUCTIONS_CHARS",
    "SKILLS_MAX_PER_TENANT",
    "TenantSkillError",
    "DuplicateSkillError",
    "SkillNotFoundError",
    "SkillQuotaExceededError",
    "TenantSkillService",
    "tenant_skill_service",
    "resolve_tenant_skill_registry",
    "invalidate_tenant_skill_registry",
    "reset_skill_registry_cache",
]
