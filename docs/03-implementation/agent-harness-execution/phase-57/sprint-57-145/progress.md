# Sprint 57.145 Progress — first real knowledge connector

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-145-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-145-checklist.md)

---

## Day 0 — 2026-06-26 — Plan-vs-Repo Verify (三-prong) + branch

### Three-prong verify (against `main` HEAD `7cedcea4`)

**Prong 1 — path verify**: ✅
- NEW `business_domain/knowledge/**` → Glob 0 results (free)
- CHANGE number: highest = CHANGE-111 → **CHANGE-112 free**; design note → **49** (highest = 48)
- EDIT targets present: `_register_all.py` ✅ · `handler.py` ✅ · `core/config/__init__.py` ✅

**Prong 2 — content verify** (drift findings):

| ID | Finding | Implication |
|----|---------|-------------|
| **D-arch-home** | knowledge needs NEITHER `BusinessServiceFactory` nor `mode` (reads local files, not mock HTTP / not DB service) | Home = `business_domain/knowledge/` as a **REAL sibling**; docstring marks REAL to avoid mock-as-real confusion with the 5 mock domains. No §3/§4 change. |
| **D-name-collision** | `knowledge_search` / `register_knowledge` / `knowledge_docs_root` grep = **0 results** | Names clean; no collision with `memory_search` etc. |
| **D-optin-kwarg** | `make_default_executor` opt-in pattern confirmed at `_register_all.py:357-359` (`todo_store`) / `:346-350` (`skill_registry`) | `knowledge_root` kwarg mirrors exactly; None → byte-identical. |
| **D-config-default** | `core/config/__init__.py` is `Settings(BaseSettings)`; `business_domain_mode` `:104`, `sandbox_require_isolation: bool = False` `:150` | Add `knowledge_docs_root: str = <in-repo planning docs>`; env `KNOWLEDGE_DOCS_ROOT` auto-read by BaseSettings. |
| **D-prompt-nudge** | `DEMO_SYSTEM_PROMPT` at `handler.py:148`; ends "...For any other request, answer directly." with a `write_todos` multi-step block before it | Insert knowledge nudge after the write_todos block, before the catch-all — no contradiction. |
| **D-fe-toolcall-render** | `sse.py:18-20,202-226` — `tool_call_request` ← ToolCallRequested / `tool_call_result` ← ToolCallExecuted+Failed, carries `result_content` | **FE UNTOUCHED confirmed** — existing tool-call rendering surfaces `knowledge_search` + snippets/sources; NO new wire event. |
| **D-toolspec-arity** | business/echo handlers are single-arity `(ToolCall) -> str` (executor invokes `(call: ToolCall)`); `MEMORY_SEARCH_SPEC` is the read-only-query template | `knowledge_search` = single-arity (no DB write → no ExecutionContext). Spec mirrors `MEMORY_SEARCH_SPEC` (`read_only=True, idempotent=True` + `open_world=True` for file IO). |

**Prong 3 — schema verify**: N/A — NO new DB table / migration / ORM column.

**Real source confirmed**: `docs/03-implementation/agent-harness-planning/` has **52 real `.md`** (00-48 + README + spikes/design notes) — rich real content for drive-through (11+1 categories spec, anti-patterns, each design note).

**Baselines (57.144 closeout, to re-confirm at Day-2 gate)**: pytest 2930+5skip · wire 26 · Vitest 922 · mockup 51 · mypy 0/382 · run_all 11/11.

### Go/no-go: ✅ **GO** — scope shift 0% (plan matches repo reality exactly; D-arch-home folder choice confirmed, no §3/§4 change).

### Branch
- ✅ `feature/sprint-57-145-knowledge-connector-spike` from `main 7cedcea4`

---

## Day 1 — 2026-06-26 — Real connector + tool (US-1, US-2)

**Written**: `connector.py` (LocalDocsConnector + KnowledgeHit) · `tools.py` (KNOWLEDGE_SEARCH_SPEC + register_knowledge_tools, single-arity handler) · `__init__.py` (exports).

**Connector smoke-test PASS (real docs, pre-unit-test sanity)**: ran `LocalDocsConnector` against `docs/03-implementation/agent-harness-planning/` —
- `files indexed: 415` (.md/.txt, recursive incl. phase-XX sprint subdirs)
- query `anti-pattern` → `04-anti-patterns.md` score **1.0** (filename) + `00-v2-vision.md` 0.7 (heading) — REAL snippet + REAL source + REAL score
- query `11+1` / `drive-through` → real sprint plans / design notes
- **Proves the core real connection works** (connector-unit level; full drive-through is Day 3).

**Env note (not a bug)**: the smoke-test `print` hit `UnicodeEncodeError: cp950` on `≥`/繁中 — a Windows terminal display issue only; the connector reads utf-8 correctly and the real path is JSON→SSE→FE (utf-8, no terminal). Mirror the Risk Class E / cp950 lessons.

**D-perf (observation, not blocker)**: default root recurses to 415 files; every `search` reads all of them. Fine for Slice 1 keyword (small .md, <1s); Slice 2 embedding will build an index. Optionally narrow the default root or add a file cap if drive-through latency is poor.

**Day 1 tests written**: `test_knowledge_connector.py` (9 tests incl. path-traversal-symlink-reject, skipped on Win no-symlink-priv) + `test_knowledge_tools.py` (7 tests: spec read-only/LOW/AUTO, all-params-described 57.144 lint, real-snippet handler, empty-query, bad-top_k fallback, registration, missing-root-raises). Renamed `test_connector.py` → `test_knowledge_connector.py` to avoid basename clash (57.140 D-test-basename-clash lesson). Connector method `list()` → `list_files()` (mypy: `list` shadowed builtin `list` type in class scope → `list[Path]` annotation mis-resolved).

---

## Day 2 — 2026-06-26 — Opt-in wiring + config + prompt nudge (US-3)

**Written**:
- `core/config/__init__.py` — `knowledge_docs_root: str` (env `KNOWLEDGE_DOCS_ROOT`, default = computed in-repo `agent-harness-planning/` via `Path(__file__).parents[4]`) + MHist.
- `_register_all.py` — `make_default_executor(knowledge_root: str | None = None)` opt-in branch (mirrors `todo_store` `:357`); `if knowledge_root:` → `try register_knowledge_tools` / `except ValueError: pass` (graceful — missing root → tool absent, never breaks build) + import + MHist.
- `handler.py` — `build_real_llm_handler` threads `knowledge_root = get_settings().knowledge_docs_root or None` into the main `make_default_executor` call + `DEMO_SYSTEM_PROMPT` knowledge nudge ("for company-knowledge questions, FIRST call `knowledge_search` + cite sources" — closes the audit §5 "接了沒人用" Potemkin).

**Decision**: pure opt-in (None → not registered, byte-identical), consistent with `skill_registry`/`todo_store`; handler explicit-threads the settings value (default ON in chat main flow — the connector we want to drive-through). Default path graceful if absent.

### Gate (to-drive-through state) — ALL GREEN
- mypy `src`: **0 issues / 385 files** (was 382; +3 knowledge module files)
- flake8 / black / isort: clean (2 E501 hand-fixed — black doesn't wrap long docstring/MHist; sprint-workflow lesson)
- knowledge unit tests: **15 passed / 1 skipped** (symlink, Win priv)
- `test_factory_and_mode.py`: **8 passed** (make_default_executor opt-in backward-compatible)
- v2 lints (`tests/unit/scripts/lint/`): **25 passed** (tool_descriptions 10 — knowledge_search params all described; llm_sdk_leak 3 — connector pure file IO)
- chat keystone wiring: **11 passed** (handler prompt nudge + default-on knowledge_search did NOT break main flow)
- Baselines confirmed UNCHANGED: wire 26 (no new event) · Vitest 922 (FE untouched) · mockup 51.

**Next (Day 3)**: drive-through — real UI (chat-v2) + real Azure + ask a knowledge question whose answer lives in a real planning doc → confirm agent CALLS knowledge_search → real snippet from a real .md → answer cites real source path → NO DEMO label. (Heavier step: needs clean backend restart + real LLM — do together.)

---

## Day 3 — 2026-06-26 — Drive-through (US-4): real UI + real Azure + real LLM

**Setup**: clean backend restart (Risk Class E) — killed stale pid 3700 (yesterday's pre-change code) + its spawn-worker; fresh pid 56132 with Azure env injected into the start shell (mechanism finding below). Frontend node@3007 untouched. dev-login `dan@acme.com·admin` / tenant `acme-prod`. chat-v2 mode `real_llm` (gpt-5.2, cache_hit 98% — confirmed real Azure, NOT echo).

**Env mechanism finding (not a bug)**: `AzureOpenAIConfig` (`adapters/azure_openai/config.py`) + `Settings` both use `env_file=".env"` *relative to CWD*; dev.py starts uvicorn with `cwd=backend/`, and `backend/.env` does **not exist** (root `.env` only). So Azure config is read purely from **OS env vars**, which the previous backend inherited from whatever shell launched it. A clean restart MUST inject root `.env`'s `AZURE_OPENAI_*` into the start shell (same PowerShell call, since shell state doesn't persist across tool calls) or the new process silently degrades off real-LLM. Also: `/health` returns **401** (TenantContextMiddleware) — readiness probe must treat 401 as ready, not failure (dev.py's own check mis-reports "may have failed").

### Round 1 — found a real bug (multi-word query → 0 hits)
- Asked: "請用 knowledge_search 查...我們定義了哪些 anti-patterns?..." (session `f38b32e6...`)
- ✅ Wiring proven NON-Potemkin: agent really CALLED `knowledge_search` (Trace span `agent_loop.tool.knowledge_search` 140ms real exec); `write_todos` task primitive also fired; Verification 0.99.
- ❌ But agent sent a multi-word semantic query `"anti-pattern 反模式 規劃文件 定義"` → connector matched the **whole phrase as a single substring** (`if q in line`) → `{"hits": [], "count": 0}` → agent honestly answered "找不到". Root cause: LLM naturally sends phrases; Slice-1 connector didn't tokenize. **15 unit tests all passed because they each used single-word queries** — exactly the "gate-green ≠ usable" trap the drive-through hard-constraint exists to catch. Screenshot `artifacts/sprint-57-145-drivethrough-1-zero-hits.png`.

### Day-3 fix — tokenize + OR match (connector.py, behavioral change)
- `search()` now tokenizes the query on whitespace; `_score_and_snippet()` matches with OR semantics (a file scores on ANY token) + a small +0.01-per-extra-distinct-token relevance bonus (single-token query keeps the exact filename/heading/content tier → all prior tests unchanged).
- Added 2 regression tests: `test_search_multiword_query_or_match` (the exact drive-through bug) + `test_search_multitoken_bonus_ranks_higher`. Gate after fix: knowledge **17 passed / 1 skipped** · mypy 0/385 · black/isort/flake8 clean (1 MHist E501 hand-fixed — the file-header rule's classic trap). MHist updated.

### Round 2 — tokenize fix verified + 2 more findings
- Re-drove same anti-patterns question (clean restart with fix; session `02857f31...`).
- ✅ **Fix works**: multiple OR queries returned REAL hits — `04-anti-patterns.md` score 1.04/1.07 snippet "# V1 Anti-Patterns（V2 必須避免的反模式）" + "## Anti-Pattern 4：Potemkin Features（結構槽位但無內容）"; also `08-glossary.md`, `01-eleven-categories-spec.md`, `17-cross-category-interfaces.md` — all real files, real source paths, real scores (cross-checked against actual file text).
- ✅ **Bonus — output-ESCALATE HITL verified**: agent output contained the word "checkpoint" → acme-prod tenant's between-turns escalation phrase → loop paused `awaiting_approval` (severity HIGH, policy always_ask); clicked Approve → loop resumed (per-tenant output-ESCALATE + HITL approve path proven live).
- ⚠️ **Finding (real usability gap, → Slice 2)**: agent over-searched (kept trying quoted-phrase queries, all 0-hit because quotes stick to the token) → exhausted `max_turns=8` → `stop: max_turns`, no synthesized answer. Root cause: connector returns only the **first-match line per file** (usually the H1), so an enumerate-style question ("list ALL anti-patterns") never gets the 11-item body → agent keeps searching. Screenshot `artifacts/sprint-57-145-drivethrough-2-real-hits-maxturns.png`. **Decision (AskUserQuestion)**: re-drive with a focused question; snippet-depth + over-search → Slice 2 carryover (keep Slice 1 thin).

### Round 3 — CLEAN PASS (focused question)
- Asked: "在我們專案的內部文件裡, \"Potemkin Feature\" 是什麼意思?請用 knowledge_search 查並引用來源檔案路徑。" (session `0f91faa8...`)
- ✅ agent CALLED `knowledge_search` (Trace span 188ms real exec) → `stop: end_turn` (turns=5, **no over-search, no max_turns**) → Verification "claim verified · llm_judge".
- ✅ **Grounded answer citing 3 real source paths** (full text via DOM eval — chat-v2 transcript renders a 49-char preview, full answer in the rendered block):
  > Potemkin Feature = 結構/槽位看起來有做出來但無實際內容/效果 (文件例: V1 Step 1 `memory_read` 跑了但沒讀 mem0)。**來源 `08-glossary.md`** · 被標記為反模式 Anti-Pattern 4 **來源 `04-anti-patterns.md`** · 願景文件同樣描述 **來源 `00-v2-vision.md`**
  - Cross-check PASS: "memory_read 跑了但沒讀 mem0" is verbatim the real `08-glossary.md` definition — grounded, NOT fabricated.
- ✅ NO DEMO label (data is real → labelling DEMO would itself be dishonest). Screenshot `artifacts/sprint-57-145-drivethrough-3-clean-pass.png`.

### Drive-through verdict: ✅ **PASS**
The platform's first real external data-source connector is proven end-to-end on the chat-v2 main flow: agent really calls `knowledge_search` → really reads real project `.md` files → answer grounded in + cites real source paths → real LLM (gpt-5.2) → no Potemkin, no DEMO. Vision pillar 1 (connect external systems): **0 → 1**.

**Carryover (Slice 2, recorded honestly — NOT this sprint)**: (a) connector returns only first-match line per file → enumerate-style questions can't get full lists; deepen snippet (multiple match segments / section-aware) so one query yields a usable body; (b) agent over-search on quoted-phrase queries vs `max_turns=8` bound; (c) embedding/Qdrant index + external sources + per-tenant RBAC/citation (original Slice 2/3 scope). Logged under `AD-Knowledge-Connector-First-Real-Source`.

**Next (Day 4)**: CHANGE-112 + spike design note 49 (8-point gate) + retrospective + final gate sweep + navigators (CLAUDE.md / MEMORY.md / next-phase-candidates / sprint-workflow calibration matrix `knowledge-connector-real-source-spike` 0.55) + reality-audit health indicator pillar-1 connectors 0→1. Then commit → PR (pending user confirmation for push).
