"""
File: backend/src/business_domain/knowledge/__init__.py
Purpose: Public exports for the REAL knowledge connector domain (first real external data source).
Category: Business domain / knowledge (REAL — NOT mock)
Scope: Phase 57 / Sprint 57.145
"""

from .connector import KnowledgeHit, LocalDocsConnector
from .tools import (
    KNOWLEDGE_SEARCH_SPEC,
    make_knowledge_search_handler,
    register_knowledge_tools,
)

__all__ = [
    "KnowledgeHit",
    "LocalDocsConnector",
    "KNOWLEDGE_SEARCH_SPEC",
    "make_knowledge_search_handler",
    "register_knowledge_tools",
]
