"""
File: backend/src/adapters/azure_openai/config.py
Purpose: AzureOpenAIConfig — Pydantic Settings for Azure OpenAI adapter.
Category: Adapters / Azure OpenAI
Scope: Phase 49 / Sprint 49.4

Description:
    Loads Azure OpenAI configuration from env vars (AZURE_OPENAI_*). Distinguishes
    `deployment_name` (tenant-defined Azure resource) from `model_name` (Microsoft
    canonical model identifier — used for pricing lookup + capability detection).

    All Azure-specific connection / retry / rate-limit knobs live here. Adapter
    is otherwise pure (no env-var reads scattered).

Created: 2026-04-29 (Sprint 49.4)
Last Modified: 2026-04-29

Modification History:
    - 2026-04-29: Initial creation (Sprint 49.4)

Related:
    - adapter.py — primary consumer
    - adapters-layer.md (.claude/rules/) §Azure OpenAI 特定細節
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI adapter configuration. Loads from env (AZURE_OPENAI_*)."""

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -- connection --------------------------------------------------------

    api_key: str = Field(default="", description="Azure OpenAI API key")
    endpoint: str = Field(
        default="",
        description="Azure resource endpoint (e.g., https://<resource>.openai.azure.com/)",
    )
    api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure API version (e.g., 2024-02-15-preview)",
    )
    deployment_name: str = Field(
        default="",
        description="Tenant-defined deployment name (used in API calls)",
    )
    # Sprint 57.146: embeddings deployment (text-embedding-3-*), separate from the
    # chat deployment_name. Shares endpoint / api_key / api_version above. Env
    # AZURE_OPENAI_DEPLOYMENT_EMBEDDING (prefix + field name; matches the existing
    # AZURE_OPENAI_DEPLOYMENT_NAME convention).
    deployment_embedding: str = Field(
        default="",
        description="Azure embedding deployment name (env AZURE_OPENAI_DEPLOYMENT_EMBEDDING)",
    )

    # -- model identity (for pricing / capability) -------------------------

    model_name: str = Field(
        default="gpt-4o",
        description="Microsoft canonical model name (e.g., gpt-5.4, gpt-4o)",
    )
    model_family: Literal["gpt", "gpt-mini", "gpt-nano"] = Field(default="gpt")
    context_window: int = Field(default=128_000, description="Max input tokens")
    max_output_tokens: int = Field(default=16_384)

    # -- timeout / retry ---------------------------------------------------

    timeout_sec: float = Field(default=30.0)
    max_retries: int = Field(default=2)
    retry_backoff_factor: float = Field(default=1.5)

    # -- rate limits (informational; circuit-breaker integration in Cat 8) -

    rpm_limit: int = Field(default=60, description="Requests per minute (provider quota)")
    tpm_limit: int = Field(default=90_000, description="Tokens per minute (provider quota)")

    # -- pricing (USD per 1M tokens) ---------------------------------------

    pricing_input_per_million: float = Field(default=2.50)
    pricing_output_per_million: float = Field(default=10.00)
    pricing_cached_input_per_million: float | None = Field(default=1.25)

    # -- capability flags --------------------------------------------------

    supports_caching: bool = Field(default=True)
    supports_vision: bool = Field(default=True)
    supports_thinking: bool = Field(default=False)  # Azure GPT family ≠ Anthropic thinking
    supports_parallel_tool_calls: bool = Field(default=True)
    supports_structured_output: bool = Field(default=True)

    def is_configured(self) -> bool:
        """Returns True if minimum required env vars are present."""
        return bool(self.api_key and self.endpoint and self.deployment_name)

    def is_embedding_configured(self) -> bool:
        """Returns True if embeddings can run (shared connection + embedding deployment)."""
        return bool(self.api_key and self.endpoint and self.deployment_embedding)
