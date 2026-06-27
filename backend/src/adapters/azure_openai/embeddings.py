"""
File: backend/src/adapters/azure_openai/embeddings.py
Purpose: AzureOpenAIEmbeddingClient — concrete EmbeddingClient over Azure text-embedding-3-*.
Category: Adapters / Azure OpenAI
Scope: Phase 57 / Sprint 57.146

Description:
    Implements the EmbeddingClient ABC using Azure OpenAI's embeddings API.
    The openai SDK import is confined to this file (+ adapter.py / error_mapper.py
    / tool_converter.py) — business_domain / agent_harness stay SDK-free per
    llm-provider-neutrality.md (check_llm_sdk_leak gate).

    Reuses AzureOpenAIConfig's shared connection fields (endpoint / api_key /
    api_version) + a dedicated deployment_embedding (env
    AZURE_OPENAI_DEPLOYMENT_EMBEDDING). is_embedding_configured() gates the
    lazy client build so an unconfigured environment raises clearly rather
    than failing deep in the SDK.

Key Components:
    - AzureOpenAIEmbeddingClient: ChatClient-style lazy client + batch embed()

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — Azure embedding adapter
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - adapters/_base/embedding_client.py — ABC owner
    - adapters/azure_openai/adapter.py — sibling ChatClient (mirrored _get_client)
    - adapters/azure_openai/config.py — AzureOpenAIConfig.is_embedding_configured()
"""

from __future__ import annotations

import asyncio
import logging

from openai import AsyncAzureOpenAI

from adapters._base.embedding_client import EmbeddingClient
from adapters.azure_openai.config import AzureOpenAIConfig
from adapters.azure_openai.error_mapper import AzureOpenAIErrorMapper

logger = logging.getLogger(__name__)


class AzureOpenAIEmbeddingClient(EmbeddingClient):
    """Azure OpenAI EmbeddingClient (text-embedding-3-small / -large)."""

    def __init__(self, config: AzureOpenAIConfig | None = None) -> None:
        self.config = config or AzureOpenAIConfig()
        self._client: AsyncAzureOpenAI | None = None

    def _get_client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            if not self.config.is_embedding_configured():
                raise ValueError(
                    "AzureOpenAIConfig missing embedding env vars: "
                    "AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / "
                    "AZURE_OPENAI_DEPLOYMENT_EMBEDDING"
                )
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                api_version=self.config.api_version,
                azure_endpoint=self.config.endpoint,
                timeout=self.config.timeout_sec,
                max_retries=self.config.max_retries,
            )
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        try:
            response = await client.embeddings.create(
                model=self.config.deployment_embedding,
                input=texts,
            )
        except asyncio.CancelledError:
            logger.info("azure_openai embed cancelled")
            raise
        except Exception as exc:  # noqa: BLE001
            raise AzureOpenAIErrorMapper.map(exc) from exc
        # response.data preserves input order; sort by .index defensively.
        ordered = sorted(response.data, key=lambda d: d.index)
        return [list(d.embedding) for d in ordered]

    def model_name(self) -> str:
        return self.config.deployment_embedding or "azure-embedding"

    async def aclose(self) -> None:
        """Release the underlying httpx pool. Idempotent."""
        if self._client is not None:
            await self._client.close()
            self._client = None
