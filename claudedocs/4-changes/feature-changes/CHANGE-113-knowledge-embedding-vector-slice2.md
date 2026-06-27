# CHANGE-113: knowledge connector Slice 2 — section-aware snippets + Azure embedding + Qdrant vector search

**Date**: 2026-06-27
**Sprint**: 57.146
**Scope**: Cat 2 (Tool Layer) + Adapters (new EmbeddingClient ABC) + Infrastructure (Qdrant) — backend only, NO migration / wire / frontend

## Problem

Sprint 57.145 shipped the first real connector (keyword search over real `.md`). Its drive-through PASSed but surfaced two quality gaps the keyword path cannot fix:

1. **R2 over-search** — the snippet was the matched line ± 1 context line, so for "list/enumerate" questions the agent re-searched repeatedly into `max_turns=8` without a usable answer.
2. **Keyword brittleness** — a real LLM sends semantic phrases; when a doc uses different words than the query, OR-token keyword match misses the relevant section entirely.

## Root Cause

Retrieval was literal token overlap + one-line snippets (`connector.py:_SNIPPET_CONTEXT_LINES = 1`). No semantic path existed: `adapters/_base/` had only `ChatClient` (no embedding ABC), the Qdrant container ran but had no client wrapper (CARRY-026 stub), and `business_domain/` cannot `import openai` (約束 3 / `check_llm_sdk_leak`).

## Solution

Two coupled deliverables (opt-in; `KNOWLEDGE_VECTOR_ENABLED=False` → 57.145 byte-identical):

- **Section-aware chunking** (`chunking.py::split_sections`) — split each `.md` at `##` headings; the keyword path now returns the whole section body → **R2 over-search structurally fixed**. The same Section is the embedding unit.
- **Provider-neutral embedding path** — new `EmbeddingClient` ABC (`adapters/_base/`) + `AzureOpenAIEmbeddingClient` (`text-embedding-3-large`, openai SDK confined to `adapters/azure_openai/`) + `DeterministicEmbeddingClient` test double + `QdrantVectorStore` wrapper (`infrastructure/vector/`, `query_points` API) + `KnowledgeVectorIndex` (batched ingest + cosine search). Wired opt-in via `make_default_executor(knowledge_vector_index=...)` + a process-wide singleton (`api/v1/chat/knowledge_index.py`) + a fail-soft startup ingest (`api/main.py`). Vector-primary with a **keyword fail-soft fallback** on any embedding/Qdrant error → the tool never goes dark.

Code: see Sprint 57.146 plan §4 (17 src + 8 test files). Field `deployment_embedding` (env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`) on the existing `AzureOpenAIConfig`. New dep `qdrant-client>=1.12,<2.0`.

### Two Day-3 drive-through fixes (the payoff over gate-green)

- **Env-name rename** — the user's `.env` uses `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` (matching the existing `..._DEPLOYMENT_NAME` convention); renamed the field `embedding_deployment` → `deployment_embedding`, catching a latent `knowledge_index.py` runtime AttributeError.
- **429 batching** — embedding ALL sections in one Azure call exceeded the deployment TPM (HTTP 429). `ingest()` now embeds in `_EMBED_BATCH=16` batches. `list_files()` recursion also pulls the default planning root to 418 files / 3818 sections → the drive-through points `KNOWLEDGE_DOCS_ROOT` at a bounded real folder (`docs/rules-on-demand`, 129 sections) = the realistic production pattern.

## Verification

- Gates: mypy `src` 0/392 · run_all 11/11 (incl. `check_llm_sdk_leak`) · pytest 2980 passed / 6 skip (+33) · flake8/black/isort clean · Vitest 922 / wire 26 / mockup 51 (FE untouched).
- **Drive-through PASS** (real chat-v2 + real Azure gpt-5.2 + real `text-embedding-3-large` + real Qdrant; trace_id `f5b394db…`): a semantic query with no literal "adapter"/"neutrality" made the agent call `knowledge_search` (TOOL_EXEC span 1750ms), Qdrant returned `adapters-layer.md` + `llm-provider-neutrality.md` sections by similarity, and the agent answered citing each real source path + section name. Qdrant `knowledge_local_docs`: green, 129 points, dim 3072. Full evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-146/progress.md` Day 3.

## Impact

Backend only. The knowledge connector gains semantic retrieval; the keyword path is preserved as a fail-soft fallback (opt-in flag default OFF → 57.145 unchanged). New `EmbeddingClient` ABC + `QdrantVectorStore` unblock the long-stubbed Cat 3 memory semantic axis (CARRY-026) for a later sprint (not wired here). Closes the Slice-2 half of `AD-Knowledge-Connector-First-Real-Source`; Slice 3 (per-tenant KB isolation + RBAC + citation) carried over.
