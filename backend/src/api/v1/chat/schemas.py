"""
File: backend/src/api/v1/chat/schemas.py
Purpose: Pydantic request/response schemas for /api/v1/chat endpoints.
Category: api/v1/chat
Scope: Phase 50 / Sprint 50.2 (Day 1.1)

Description:
    Inbound `ChatRequest` (POST body) + outbound `ChatSessionResponse`
    (GET /sessions/{id}). Both are LLM-neutral — they describe the
    HTTP-level contract, NOT the LLM-provider neutral types in
    `agent_harness/_contracts/chat.py` (those flow inside the loop).

    `mode` field selects which `ChatClient` the handler factory wires:
    - `echo_demo`: MockChatClient pre-scripted to call echo_tool once
    - `real_llm`: AzureOpenAIAdapter; requires AZURE_OPENAI_* env vars

Created: 2026-04-30 (Sprint 50.2 Day 1.1)
Last Modified: 2026-06-14

Modification History (newest-first):
    - 2026-06-14: Sprint 57.115 — ChatRequest.force_load_skill + ChatSkill list schemas
    - 2026-04-30: Initial creation (Sprint 50.2 Day 1.1) — minimal request +
        session response schemas for echo_demo / real_llm modes.

Related:
    - .router (consumes ChatRequest, returns ChatSessionResponse)
    - .handler (selects ChatClient impl by mode)
    - 02-architecture-design.md §API v1 endpoints
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ChatMode = Literal["echo_demo", "real_llm"]


class ChatRequest(BaseModel):
    """Inbound POST /api/v1/chat body."""

    message: str = Field(..., min_length=1, max_length=10_000)
    session_id: UUID | None = None
    mode: ChatMode = "echo_demo"
    # Sprint 57.115 (Skills slash-command): the user-picked skill name from the
    # /skill-name composer command. The router validates it against the resolved
    # per-tenant registry (unknown → graceful no-op) and threads it to
    # build_handler for deterministic force-load. Kebab name; absent → no force.
    force_load_skill: str | None = Field(default=None, max_length=128, pattern=r"^[a-z0-9-]+$")


class InjectRequestBody(BaseModel):
    """Inbound POST /api/v1/chat/{session_id}/inject body (Sprint 57.101 B1).

    A supplementary instruction the running loop drains at the next turn boundary.
    """

    message: str = Field(..., min_length=1, max_length=4096)


class ChatSkillItem(BaseModel):
    """One skill in GET /api/v1/chat/skills — name + description ONLY.

    Sprint 57.115: the slash-command picker needs the discovery pair, NOT the
    full instructions body (that loads on force-load / read_skill). Deliberately
    omits `instructions` so the non-admin list endpoint never leaks skill bodies.
    """

    name: str
    description: str


class ChatSkillsResponse(BaseModel):
    """Outbound GET /api/v1/chat/skills body — the caller tenant's effective skills."""

    skills: list[ChatSkillItem]


SessionStatus = Literal["running", "completed", "cancelled"]


class ChatSessionResponse(BaseModel):
    """Outbound GET /api/v1/chat/sessions/{id} body."""

    session_id: UUID
    status: SessionStatus
    started_at: datetime
