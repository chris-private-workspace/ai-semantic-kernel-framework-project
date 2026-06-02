"""platform_layer.handoff — Cat 11 HANDOFF control-transfer session-boot.

Sprint 57.68 (A-3b backend slice) introduces:
    - persona_registry: minimal target_agent → system_prompt stand-in
    - service: HandoffService.boot_handoff — atomic child-session boot,
      parent mark, audit (tenant-scoped, linked, persona in meta_data)

Sprint 57.69 (A-3b slice 2) introduces:
    - context_carry: cap/serialize the parent conversation + render it into the
      child's persona prompt (agent-side context carry)
"""

from platform_layer.handoff.context_carry import (
    DEFAULT_MAX_CARRY_MESSAGES,
    cap_and_serialize,
    render_carried_context_block,
)
from platform_layer.handoff.persona_registry import (
    DEFAULT_AGENTS,
    resolve_default_persona,
    resolve_persona,
)
from platform_layer.handoff.service import (
    HandoffError,
    HandoffResult,
    HandoffService,
)

__all__ = [
    # context_carry
    "DEFAULT_MAX_CARRY_MESSAGES",
    "cap_and_serialize",
    "render_carried_context_block",
    # persona_registry
    "DEFAULT_AGENTS",
    "resolve_persona",
    "resolve_default_persona",
    # service
    "HandoffError",
    "HandoffResult",
    "HandoffService",
]
