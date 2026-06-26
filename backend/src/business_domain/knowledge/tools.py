"""
File: backend/src/business_domain/knowledge/tools.py
Purpose: knowledge_search ToolSpec + register_knowledge_tools — wraps the REAL LocalDocsConnector.
Category: Business domain / knowledge / tool layer (REAL — NOT mock)
Scope: Phase 57 / Sprint 57.145

Description:
    Exposes the first real external data-source connector to the agent as a
    Cat 2 tool. `knowledge_search` is read-only (LOW risk, AUTO hitl) so the
    registry-derived permission matrix auto-passes it — the agent searches the
    company docs folder freely and grounds answers in real snippets with source
    paths. Single-arity handler (no DB write → no ExecutionContext), mirroring
    the business-domain handler shape.

Key Components:
    - KNOWLEDGE_SEARCH_SPEC: the ToolSpec (mirrors MEMORY_SEARCH_SPEC shape)
    - make_knowledge_search_handler(): builds a (ToolCall) -> str handler
    - register_knowledge_tools(): registers spec + handler over a docs root

Created: 2026-06-26 (Sprint 57.145)
Last Modified: 2026-06-26

Modification History (newest-first):
    - 2026-06-26: Initial creation (Sprint 57.145) — first real connector tool
      (AD-Knowledge-Connector-First-Real-Source)

Related:
    - 01-eleven-categories-spec.md §範疇 2 (Tools)
    - agent_harness/tools/memory_tools.py (MEMORY_SEARCH_SPEC — read-only query template)
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.tools import ToolHandler, ToolRegistry

from .connector import LocalDocsConnector

KNOWLEDGE_SEARCH_SPEC: ToolSpec = ToolSpec(
    name="knowledge_search",
    description=(
        "Search the company knowledge base / internal documents folder for "
        "passages relevant to a query. Returns up to top_k snippets, each with "
        "its source file path, so the answer can cite real sources. Read-only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 1,
                "description": "Natural-language or keyword query to search the documents for.",
            },
            "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Max number of ranked document snippets to return (1-20).",
            },
        },
        "required": ["query"],
    },
    # open_world=True: this tool reaches a real external data source (the file system).
    annotations=ToolAnnotations(read_only=True, idempotent=True, open_world=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("knowledge", "read-only"),
)


def make_knowledge_search_handler(connector: LocalDocsConnector) -> ToolHandler:
    """Build a single-arity (ToolCall) -> str handler over a real docs connector."""

    async def handler(call: ToolCall) -> str:
        args = dict(call.arguments)
        query = str(args.get("query", "")).strip()
        top_k_raw = args.get("top_k", 5)
        try:
            top_k = int(top_k_raw)
        except (TypeError, ValueError):
            top_k = 5
        if not query:
            return json.dumps({"hits": [], "count": 0, "note": "empty query"})
        hits = connector.search(query, top_k=top_k)
        return json.dumps(
            {
                "hits": [
                    {"source": h.source, "snippet": h.snippet, "score": round(h.score, 3)}
                    for h in hits
                ],
                "count": len(hits),
            }
        )

    return handler


def register_knowledge_tools(
    registry: ToolRegistry,
    handlers: dict[str, ToolHandler],
    *,
    docs_root: Path | str,
) -> None:
    """Register the REAL knowledge_search tool backed by a LocalDocsConnector(docs_root).

    Mirrors the per-domain register_*_tools shape: mutates the shared (registry,
    handlers). The connector is built once here; a missing root raises clearly so
    the caller (make_default_executor opt-in) can decide to skip registration.
    """
    connector = LocalDocsConnector(docs_root)
    registry.register(KNOWLEDGE_SEARCH_SPEC)
    handlers["knowledge_search"] = make_knowledge_search_handler(connector)
