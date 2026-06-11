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
Last Modified: 2026-04-30

Modification History (newest-first):
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


class InjectRequestBody(BaseModel):
    """Inbound POST /api/v1/chat/{session_id}/inject body (Sprint 57.101 B1).

    A supplementary instruction the running loop drains at the next turn boundary.
    """

    message: str = Field(..., min_length=1, max_length=4096)


SessionStatus = Literal["running", "completed", "cancelled"]


class ChatSessionResponse(BaseModel):
    """Outbound GET /api/v1/chat/sessions/{id} body."""

    session_id: UUID
    status: SessionStatus
    started_at: datetime
