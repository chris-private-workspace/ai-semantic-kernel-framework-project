# Sprint 57.145 — Checklist (first real knowledge connector — knowledge_search tool + local docs source)

[Plan](./sprint-57-145-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `7cedcea4`)
- [x] **Prong 1 — path verify**: NEW files free (`business_domain/knowledge/{__init__,connector,tools}.py`, `tests/unit/business_domain/knowledge/`); EDIT files present (`_register_all.py`, `handler.py`, `core/config/__init__.py`); `CHANGE-NNN` number free (next after CHANGE-111) → CHANGE-112 / design note 49
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-arch-home** — decide connector+tool home; grep `BusinessServiceFactory` / `mode=` usage to confirm knowledge needs NEITHER → real sibling under `business_domain/knowledge/`, docstring marked REAL; confirm `knowledge_search` / `knowledge` names don't collide (`grep -rn "knowledge_search\|name=\"knowledge"` + check `memory_search`)
  - [x] **D-optin-kwarg** — read `_register_all.py:215-359` confirm `knowledge_root` kwarg mirrors `todo_store`/`skill_registry` (None → byte-identical); confirm `build_real_llm_handler` (`handler.py`) is the per-request thread point
  - [x] **D-config-default** — read `core/config/__init__.py` Settings shape; confirm `docs/03-implementation/agent-harness-planning/` exists + has real `.md` (`ls`); pick `knowledge_docs_root` default + env `KNOWLEDGE_DOCS_ROOT`
  - [x] **D-prompt-nudge** — read `DEMO_SYSTEM_PROMPT` (`handler.py:148`) + the `## Active Skill` inject (`:514-522`); confirm a knowledge nudge co-exists without contradicting existing guidance
  - [x] **D-fe-toolcall-render** — confirm chat-v2 renders a tool_call request + result (name + result text) so `knowledge_search` + snippets/source are visible WITHOUT a new wire event (grep chat-v2 transcript / Inspector tool rendering)
  - [x] **D-toolspec-arity** — confirm `knowledge_search` handler is single-arity `(ToolCall) -> str` (mirror business handlers; no DB write → no ExecutionContext)
- [x] **Prong 3 — schema verify**: N/A (NO new DB table / migration / ORM column — confirm none needed)
- [x] **D-baselines** — pytest 2930+5skip · wire 26 (UNCHANGED) · Vitest 922 (UNCHANGED) · mockup 51 · mypy 0/382 · run_all 11/11 (mypy now 0/385: +3 knowledge files)
- [x] **Catalog drift** — progress.md Day-0 table (D-IDs + finding + implication + which §Risks row)
- [x] **Go/no-go** — scope-shift % (D-arch-home folder choice ≤20% → proceed; >20% → revise §3/§4) → 0% shift, GO

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-145-knowledge-connector-spike` (from `main` `7cedcea4`)

---

## Day 1 — Real connector + tool (US-1, US-2)

### 1.1 `LocalDocsConnector` (US-1) — `business_domain/knowledge/connector.py`
- [x] **`LocalDocsConnector(root)` + `list_files()` + `search(query, top_k)` + `KnowledgeHit`** (method `list()` → `list_files()`: avoid shadowing builtin `list` type in class scope)
  - DoD: reads `.md`/`.txt` under root; keyword score (filename/title > content, mirror mock kb `_score`); returns `(source_path_relative, snippet, score)` with a context window; resolves+confines to root, rejects `..` traversal/escape; raises clearly if root missing
  - Verify: `pytest backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py -q`

### 1.2 `test_knowledge_connector.py` (US-1) — renamed from `test_connector.py` (basename clash, 57.140 lesson)
- [x] **connector unit tests** (9 tests, 1 skipped on Win no-symlink-priv)
  - DoD: list (.md/.txt only, skips others) · search scoring/ordering · empty-query · top_k cap · **path-traversal reject** · snippet contains matched text + source path
  - Verify: `pytest backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py -q`

### 1.3 `knowledge_search` tool (US-2) — `business_domain/knowledge/tools.py` + `__init__.py`
- [x] **`KNOWLEDGE_SEARCH_SPEC` + `register_knowledge_tools(registry, handlers, *, docs_root)`**
  - DoD: spec name `knowledge_search`, input `{query (req), top_k (1..20, def 5)}` ALL params described (57.144 lint); `read_only=True`+`destructive=False`+`risk=LOW`+`hitl=AUTO`; single-arity handler returns compact hits (source+snippet+score) as str
  - Verify: `pytest backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py -q` + `python scripts/lint/...check_tool_descriptions` (params described)

### 1.4 `test_knowledge_tools.py` (US-2)
- [x] **tool unit tests** (7 tests)
  - DoD: spec shape · handler returns real snippets from a temp docs dir · auto-pass risk (LOW+read_only) · registration mutates registry+handlers
  - Verify: `pytest backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py -q`

### 1.x partial gate
- [x] `mypy backend/src/business_domain/knowledge` clean · `black/isort/flake8` on new files · LLM-SDK-leak clean (pure file IO)

---

## Day 2 — Opt-in wiring + prompt + full gate (US-3)

### 2.1 Opt-in `knowledge_root` wiring — `_register_all.py`
- [x] **`make_default_executor(knowledge_root=...)` opt-in branch**
  - DoD: when `knowledge_root` not None → `register_knowledge_tools(...)`; None → executor byte-identical (mirror `todo_store` `:357-359`)
  - Verify: `pytest backend/tests/unit/.../test_make_default_executor*.py -q` (opt-in registers tool / None byte-identical) → 8 passed

### 2.2 Config + handler thread + prompt nudge — `core/config` + `handler.py`
- [x] **`knowledge_docs_root` setting + `build_real_llm_handler` thread + `DEMO_SYSTEM_PROMPT` nudge**
  - DoD: `knowledge_docs_root` (env `KNOWLEDGE_DOCS_ROOT`, default in-repo planning docs); handler passes it to `make_default_executor`; prompt nudge instructs agent to call `knowledge_search` for knowledge questions + cite sources
  - Verify: `pytest backend/tests/unit/api/v1/chat/ -q -k "handler or prompt"` + grep nudge present → chat keystone 11 passed

### 2.x Full gate (Day-2 to-drive-through state; final counts re-confirmed Day 4 after Day-3 tokenize fix)
- [x] mypy `src` 0/385 · run_all 11/11 · knowledge 17 passed/1 skip (Day-3: +2 multiword regression) · Vitest 922 (UNCHANGED) · wire 26 (UNCHANGED) · mockup 51 · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] Kill stale uvicorn reloader + orphan spawn-workers (`Get-CimInstance Win32_Process` PID/PPID/StartTime sweep per 57.97); confirm fresh sole :8000 owner + startup log; mock_services not needed (LocalDocsConnector reads files directly) → killed stale pid 3700 + spawn-worker; fresh pid 56132; Azure env injected (mechanism finding in progress.md); /health=401=ready

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] Real UI chat-v2 (`localhost:3007`, dev-login dan@acme.com·admin / acme-prod) + real Azure gpt-5.2 (mode=`real_llm`, NOT echo — cache_hit 98% confirms real Azure)
- [x] Ask a knowledge question whose answer lives in a real planning doc → R1+R2 anti-patterns (found+fixed multi-word 0-hit bug) → R3 focused "Potemkin Feature 是什麼意思" (clean PASS)
- [x] **THE proof (real UI, per-control AP-4 walk)**:
  - [x] agent CALLS `knowledge_search` (not echo / not from training) — Trace span `agent_loop.tool.knowledge_search` 140-234ms real exec
  - [x] tool result = REAL content from a real `.md` — `04-anti-patterns.md` / `08-glossary.md` / `00-v2-vision.md` snippets cross-checked against actual file text (NOT seed/mock)
  - [x] agent's answer is grounded in + cites the real source path — R3 answer cited `08-glossary.md` + `04-anti-patterns.md` + `00-v2-vision.md`; "memory_read 跑了但沒讀 mem0" verbatim from real glossary
  - [x] rendered with NO DEMO label (the data is real — labelling it DEMO would itself be dishonest)
- [x] Screenshot + observed-vs-intended + session id → progress.md Day 3 → 3 screenshots in `artifacts/`; sessions `f38b32e6` / `02857f31` / `0f91faa8`; playwright scratch cleaned
- [x] **BONUS**: per-tenant output-ESCALATE HITL verified live (acme-prod "checkpoint" phrase → pause `awaiting_approval` → Approve → resume)

---

## Day 4 — CHANGE-NNN + closeout (US-5)

### 4.1 CHANGE-NNN + design note
- [x] **`CHANGE-112-knowledge-connector-first-real-source.md`** (gap + fix + drive-through PASS + AD recorded)
- [x] **Spike design note** (8-point gate per sprint-workflow §5.5): `49-knowledge-connector-first-real-source-design.md` — first-real-connector decision matrix (local-folder vs wire-kb-mock vs external-API vs embedding) + verified invariants (file:line) + path-safety + Slice 2/3 open invariants + rollback + 17.md cross-ref (N/A — reuses Cat 2 ToolSpec); 8-point gate self-checked in retrospective (~96% verified)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`knowledge-connector-real-source-spike` 0.55, 1st data point; ratio ~1.15-1.25 upper-edge IN band → KEEP 0.55)
- [x] Final gate sweep: mypy 0/385 · run_all 11/11 · pytest 2947+6skip · Vitest 922 · mockup 51 byte-identical · LLM-SDK-leak green (FE build/lint not re-run — 0 FE diff)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (grounding pillar block + Slice 2/3 carryover) · sprint-workflow matrix (NEW `knowledge-connector-real-source-spike` 0.55 row) · **reality-audit §0 update: pillar 1 connectors 0 → 1**
- [x] Anti-pattern self-check (retro Q5): AP-2 (tool reachable from 主流量 via opt-in default-ON) / AP-4 (NOT Potemkin — drive-through proves real read + cites 3 real .md) / AP-6 (keyword not embedding) / AP-11 (naming; `list()`→`list_files()`); v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
