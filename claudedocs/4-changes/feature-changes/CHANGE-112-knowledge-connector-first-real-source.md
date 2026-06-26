# CHANGE-112: First real external data-source connector (knowledge_search + LocalDocsConnector)

**Date**: 2026-06-26
**Sprint**: 57.145
**Scope**: Cat 2 (Tool Layer) + business_domain/knowledge (REAL connector)

## Motivation

The 2026-06-26 reality audit (`v2-reality-audit-engine-vs-grounding-20260626.md`) scored vision pillar 1 ("連接公司既有外部系統") at ~15% with **ZERO real external data-source connectors** — the 5 business domains (audit/correlation/incident/patrol/rootcause) all route to an in-process `mock_services` HTTP backend, so nothing on the platform actually reads a real external source. The audit §9 set a gate: before opening another engine-deepening sprint, move a grounding pillar from 0→1. This sprint is the minimal real-connection slice (Slice 1) for the "knowledge-base research" golden path.

## Solution

A real keyword connector over real on-disk docs, surfaced as an agent tool, wired opt-in into the chat main flow:

- **`business_domain/knowledge/connector.py`** — `LocalDocsConnector`: reads real `.md`/`.txt` under a configured root, keyword-scores (filename 1.0 > heading 0.7 > content 0.5), returns `KnowledgeHit(source, snippet, score)`. Path-safety: all reads resolved + confined to root (symlink-escape / traversal rejected). REAL connector, explicitly docstring-marked to avoid mock-as-real confusion with the 5 sibling mock domains.
- **`business_domain/knowledge/tools.py`** — `KNOWLEDGE_SEARCH_SPEC` (`read_only=True`, `open_world=True`, `risk=LOW`, `hitl=AUTO` → auto-passes any tenant policy) + single-arity `(ToolCall) -> str` handler returning compact JSON hits + `register_knowledge_tools(registry, handlers, *, docs_root)`.
- **`_register_all.py`** — `make_default_executor(knowledge_root=None)` opt-in branch (mirrors `todo_store`/`skill_registry`; None → executor byte-identical; missing root → graceful skip, never breaks the build).
- **`core/config/__init__.py`** — `knowledge_docs_root` setting (env `KNOWLEDGE_DOCS_ROOT`, default = the in-repo `agent-harness-planning/` docs — real content, zero setup, dogfooding).
- **`api/v1/chat/handler.py`** — `build_real_llm_handler` threads `get_settings().knowledge_docs_root` into `make_default_executor` (default ON in chat main flow) + `DEMO_SYSTEM_PROMPT` knowledge nudge ("for company-knowledge questions, FIRST call `knowledge_search` + cite sources" — closes the audit §5 "接了沒人用" Potemkin risk).

### Day-3 drive-through fix — tokenize + OR match (behavioral)

The drive-through (real UI + real Azure) immediately exposed a defect the unit tests missed: `search()` matched the **whole query as a single substring** (`if q in line`). A real LLM sends multi-word semantic queries (`"anti-pattern 反模式 規劃文件 定義"`), so no single line contained the exact phrase → `count: 0` → agent honestly answered "找不到". All 15 unit tests passed because each used a single-word query — the exact "gate-green ≠ usable" trap the drive-through hard-constraint exists to catch. Fix: `search()` tokenizes on whitespace; `_score_and_snippet()` matches with OR semantics (a file scores on ANY token) + a small +0.01-per-extra-distinct-token relevance bonus (single-token query keeps the exact tier → all prior tests unchanged). +2 regression tests.

## Verification

- **Gate**: mypy 0/385 · knowledge 17 passed/1 skip (incl. 2 multi-word regression tests) · `make_default_executor` opt-in 8 passed · chat keystone 11 passed · v2 lints (tool_descriptions + llm_sdk_leak) green · wire 26 / Vitest 922 / mockup 51 UNCHANGED (no new event, FE untouched).
- **Drive-through PASS** (3 rounds, real chat-v2 + real Azure gpt-5.2, dev-login dan@acme.com·admin / acme-prod): agent really CALLS `knowledge_search` (Trace span 140-234ms real exec) → real snippets from real `.md` (`04-anti-patterns.md` / `08-glossary.md` / `00-v2-vision.md`, cross-checked verbatim) → grounded answer citing 3 real source paths → `stop: end_turn` + verification passed → NO DEMO label. Sessions `f38b32e6` / `02857f31` / `0f91faa8`. Detail: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-145/progress.md` Day 3 + 3 screenshots in `artifacts/`.
- **Bonus**: per-tenant output-ESCALATE HITL verified live (acme-prod "checkpoint" escalation phrase → pause `awaiting_approval` → Approve → resume).

## Impact

- Backend-only. NO DB migration / NO new wire event / NO frontend change. Reuses Cat 2 `ToolSpec` (no new cross-category contract).
- Vision pillar 1 (connect external systems): **0 → 1** — first real connector on the chat main flow.
- Default ON in chat (`knowledge_root` threaded from settings); graceful if root absent. LLM-provider-neutral (pure file IO, no provider import).

## Carryover (Slice 2 — NOT this sprint; `AD-Knowledge-Connector-First-Real-Source`)

- Connector returns only the **first-match line per file** (usually the H1) → enumerate-style questions ("list ALL anti-patterns") can't get the full body, so the agent over-searches and can hit `max_turns=8` with no synthesized answer. Deepen the snippet (multiple match segments / section-aware) so one query yields a usable body.
- Default root recurses to ~415 files, each `search` reads all of them (fine for Slice 1 small `.md`, <1s); Slice 2 embedding/Qdrant builds an index.
- External sources (HTTP/connector framework) + per-tenant RBAC/citation (original Slice 2/3 scope).
