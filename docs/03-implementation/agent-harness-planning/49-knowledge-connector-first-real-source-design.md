# 49 — Knowledge Connector: First Real External Data-Source (Slice 1) design note

**Purpose**: Spike-extract design note from Sprint 57.145; documents the verified runtime invariants for the platform's FIRST real external data-source connector — `knowledge_search` over a real local-docs source — extracted from real implementation + a 3-round real-Azure drive-through.
**Category / Scope**: Cat 2 (Tool Layer) + `business_domain/knowledge` (REAL connector) / Phase 57 / Sprint 57.145
**Created**: 2026-06-26
**Last Modified**: 2026-06-26
**Status**: Active
**Slice**: `AD-Knowledge-Connector-First-Real-Source`

> **Modification History**
> - 2026-06-26: Initial creation (Sprint 57.145) — spike-extract from first-real-connector implementation + drive-through

---

## 1. Spike Summary (US-1..US-4)

**Spike question**: Can the platform expose its FIRST real external data-source connector — one that reads a REAL source (not the in-process `mock_services` HTTP backend the 5 business domains use) and returns real grounded content — wired into the chat main flow, drive-through-proven on real UI + real Azure?

**Answer: yes.** A keyword connector over real on-disk `.md`/`.txt`, surfaced as a `knowledge_search` Cat-2 tool, opt-in into `make_default_executor`, default-ON in chat via the handler. Drive-through PASS: the agent really calls the tool, really reads real project docs, and grounds its answer in + cites 3 real source paths. Vision pillar 1 (connect external systems): **0 → 1**.

**Why this source first**: the in-repo `agent-harness-planning/` docs (~415 real `.md`/`.txt`) — real, rich content, zero external dependency, dogfooding (the agent answers questions about its own platform from its own planning docs).

---

## 2. Decision Matrix — what counts as the "first real connector"

| Option | Real vs mock | Setup cost | Dependency | Drive-through-able now | Decision |
|--------|--------------|-----------|------------|------------------------|----------|
| **A. Local-folder keyword (CHOSEN, Slice 1)** | REAL (reads real `.md` off disk) | ~0 (in-repo docs) | none | ✅ yes | **CHOSEN** — minimal real connection; proves the pillar 0→1 with zero infra |
| B. Wire to the existing `mock_services` KB mock | mock (HTTP echo) | low | mock service running | ✅ but proves nothing real | ❌ rejected — still a mock; audit §5 says this is the gap, not the fix |
| C. External API (e.g. Confluence/SharePoint) | REAL | high (auth, network, secrets) | external account + creds | ❌ not in a thin spike | ❌ deferred to Slice 2/3 — too heavy for a 0→1 proof |
| D. Embedding + Qdrant index | REAL + better retrieval | medium (index build, vector store) | Qdrant | ⚠️ over-scoped for Slice 1 | ❌ deferred to Slice 2 — keyword is enough to prove the connection |

**Rationale**: the audit gate was "move a grounding pillar 0→1", not "build the best retriever". Keyword over real in-repo docs is the smallest change that is genuinely real (not mock) and fully drive-through-able with zero infra. Retrieval quality (embedding) and external sources are Slice 2/3.

**Retrieval-match decision (Day-3, drive-through-forced)**: whole-phrase substring vs **tokenized OR match**. A real LLM sends multi-word semantic queries; whole-phrase substring returned 0 hits on every real query. Tokenized OR match (any token scores) + a multi-token relevance bonus was the minimal fix. See §3 invariant 5.

---

## 3. Verified Invariants (file:line — runtime-proven)

1. **Real file read, path-confined** — `LocalDocsConnector.__init__` resolves + validates the root (`business_domain/knowledge/connector.py:67-73`); `list_files()` recursively collects `.md`/`.txt` and rejects symlink-escape/traversal via `resolved.is_relative_to(self._root)` (`connector.py:79-93`). Verified: `test_symlink_escape_rejected`, `test_list_collects_md_txt_only_recursive`.
2. **Keyword scoring tiers** — filename 1.0 > heading 0.7 > content 0.5 (`connector.py:45-47` constants; `_score_and_snippet` `connector.py:~125`). Verified: `test_search_filename_scores_highest`, `test_search_heading_beats_content`.
3. **Tool spec auto-passes any tenant policy** — `KNOWLEDGE_SEARCH_SPEC` is `read_only=True` + `open_world=True` + `risk=LOW` + `hitl=AUTO` (`business_domain/knowledge/tools.py`); single-arity `(ToolCall) -> str` handler (mirrors business handlers, no `ExecutionContext` since no DB write). Verified: `test_spec_is_read_only_low_auto`, `test_spec_params_all_described` (57.144 lint).
4. **Opt-in wiring, byte-identical when off** — `make_default_executor(knowledge_root=None)` → no registration → executor unchanged; non-None → `register_knowledge_tools`; missing root → graceful `except ValueError: pass` (`_register_all.py`, mirrors `todo_store`/`skill_registry` opt-in). Handler threads `get_settings().knowledge_docs_root` (default ON in chat) (`api/v1/chat/handler.py` `build_real_llm_handler` + `DEMO_SYSTEM_PROMPT` nudge ~`:148`). Verified: `test_factory_and_mode.py` 8 passed + chat keystone 11 passed.
5. **Tokenized OR match (Day-3 drive-through fix)** — `search()` tokenizes on whitespace, drops empty (`connector.py:~107`); `_score_and_snippet` scores on ANY token (`stem_hits` / per-line `line_hits`) + `bonus = 0.01 * (len(matched) - 1)` so a single-token query keeps the exact tier (`connector.py:~155`). Verified: `test_search_multiword_query_or_match`, `test_search_multitoken_bonus_ranks_higher` + the real-Azure drive-through (multi-word OR query → real `04-anti-patterns.md` hit, score 1.04).
6. **End-to-end grounding (real Azure)** — drive-through session `0f91faa8`: agent → `write_todos` → `knowledge_search` (Trace span `agent_loop.tool.knowledge_search` 188ms real exec) → `stop: end_turn` → answer cites `08-glossary.md` + `04-anti-patterns.md` + `00-v2-vision.md`; "memory_read 跑了但沒讀 mem0" is verbatim the real `08-glossary.md` text (grounded, not fabricated). NO DEMO label.

**Verification commands (reproducible)**:
- Unit: `pytest backend/tests/unit/business_domain/knowledge -q` → 17 passed / 1 skipped (symlink on Win)
- Opt-in: `pytest backend/tests/unit/agent_harness -q -k make_default_executor` → 8 passed
- Lint: `python scripts/lint/run_all.py` (tool_descriptions confirms `knowledge_search` params described; llm_sdk_leak confirms connector is provider-neutral pure file IO)
- Drive-through (manual): real chat-v2 `localhost:3007` + real Azure, mode `real_llm`, ask "Potemkin Feature 是什麼意思" → agent calls `knowledge_search` → answer cites 3 `.md` paths (see progress.md Day 3 + `artifacts/sprint-57-145-drivethrough-3-clean-pass.png`)

**Test fixtures**: unit tests build temp docs dirs via `_write(root, rel, content)` helper (`backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py:17-20`). Drive-through uses the real in-repo `agent-harness-planning/` docs (no fixture — the real source).

---

## 4. Cross-Category Contracts

**N/A — reuses Cat 2 `ToolSpec`, adds NO new cross-category contract.** `knowledge_search` is an ordinary Cat-2 tool (neutral `ToolSpec` + single-arity handler); it registers through the existing `ToolRegistry`/`make_default_executor` seam (Sprint 57.113 `skill_registry` / 57.140 `todo_store` precedent). No new ABC, no new event type (wire stays 26), no `17-cross-category-interfaces.md` change. The connector lives in `business_domain/knowledge/` as a REAL sibling to the 5 mock domains (no `BusinessServiceFactory`/`mode` needed — it reads files, not the mock HTTP backend; Day-0 D-arch-home).

---

## 5. Open Invariants (deferred — NOT verified this spike)

| Deferred | Why out of Slice 1 | Target |
|----------|--------------------|--------|
| Snippet depth for enumeration | connector returns only the first-match line/file (usually the H1); "list ALL anti-patterns" can't get the 11-item body → agent over-searches → can hit `max_turns=8` with no answer | Slice 2 — multiple match segments / section-aware snippet |
| Embedding / Qdrant retrieval | keyword is enough to prove the 0→1 connection; semantic retrieval is a quality upgrade | Slice 2 |
| External sources (HTTP/connector framework) | a thin spike proves the pattern on a local source first | Slice 2/3 |
| Per-tenant RBAC + citation governance | Slice 1 uses a single shared root (multi-tenant rule N/A — no `tenant_id` data) | Slice 3 |
| Index/perf for large roots | default root recurses ~415 files, each `search` reads all (fine for small `.md`, <1s) | Slice 2 (index) |

**Verified vs deferred boundary is explicit**: §3 invariants are runtime-proven (unit + real-Azure drive-through); the table above is NOT verified and must not be presented as working.

---

## 6. Rollback / Fallback

- **Disable without revert**: leave `knowledge_root=None` (or unset `KNOWLEDGE_DOCS_ROOT` so the default in-repo path is intentionally pointed elsewhere / absent) → `make_default_executor` skips registration → tool absent, executor byte-identical. Already the graceful path if the root is missing (`except ValueError: pass`).
- **Full revert**: delete `business_domain/knowledge/` (3 files) + revert the 3 edits (`_register_all.py` opt-in branch, `core/config/__init__.py` setting, `api/v1/chat/handler.py` thread + nudge). No DB migration / no wire / no frontend → revert is backend-only, est. <1 hr. No sentinel/fallback data to clean (connector reads real files; nothing persisted).

---

## 7. References

- `claudedocs/5-status/v2-reality-audit-engine-vs-grounding-20260626.md` §9 (gate: move a grounding pillar 0→1) + §5 (接了沒人用 Potemkin risk the prompt nudge closes)
- `claudedocs/4-changes/feature-changes/CHANGE-112-knowledge-connector-first-real-source.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-145/progress.md` Day 0 (三-prong) + Day 3 (drive-through, 3 rounds + tokenize fix)
- `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` §範疇 2 (Tools)
- `.claude/rules/sprint-workflow.md` §Drive-Through (the hard-constraint that caught the multi-word 0-hit bug)
- Sprint 57.113 `31-skills-system-spike.md` (the `make_default_executor` opt-in + builtin-tool precedent) · Sprint 57.140 `44-task-primitive-write-todos-design.md` (`todo_store` opt-in precedent)
