# Sprint 57.145 Plan — first real knowledge connector (knowledge_search tool + local docs source)

**Summary**: Ships the platform's **first real external data-source connector** — a `knowledge_search` tool (Cat 2) backed by a REAL `LocalDocsConnector` that reads + keyword-searches a configured folder of real `.md`/`.txt` files (default: the project's own `docs/03-implementation/agent-harness-planning/` 21 real planning docs → zero external dependency, 100% real content, dogfooding). This is the first slice of the "知識庫/文件研究" golden path and the first move on vision pillar 1 (連接外部系統, audited at ~15% with ZERO real connectors on 2026-06-26). Per the reality audit (`v2-reality-audit-engine-vs-grounding-20260626.md`) §9 落地 Gate, this sprint MOVES the grounding dimension (real connection, real content) — it is NOT another engine-polish spike. **The drive-through is MANDATORY and is the whole point**: prove a real human, via chat-v2 + real LLM, can ask a knowledge question and get an answer grounded in the project's REAL documents with real source attribution (NOT a mock/seed article, NOT a DEMO label — this data is real). Spike sprint (new domain: first connector) → a design note is required. Scope = single thin vertical slice; NO embedding/Qdrant, NO RBAC filtering, NO multi-tenant folder isolation (later slices).

**Status**: Approved-to-execute (user 2026-06-26 — "正式啟動 Sprint 57.145"; golden-path direction + "知識庫/文件研究" pillar + "升級:Slice 1 就做最小真實連接" all confirmed via AskUserQuestion; first real source = project docs folder per parent default, user did not object)
**Branch**: `feature/sprint-57-145-knowledge-connector-spike`
**Base**: `main` HEAD `7cedcea4` (Sprint 57.144 flip #343 merged — tool-desc lint + structured-error reflection)
**Slice**: opens the "知識庫/文件研究" golden-path arc (Slice 1 of 3: 1=first real connector / 2=embedding or external-API source / 3=RBAC + multi-doc + citation). No pre-existing AD — this is a NEW direction grounded in `v2-reality-audit-engine-vs-grounding-20260626.md` §10 #2. Tracked as `AD-Knowledge-Connector-First-Real-Source`.
**Scope decisions**: (a) **first real source = a local docs folder** (`LocalDocsConnector` reads `.md`/`.txt` under a configured root; default root = the project's own `docs/03-implementation/agent-harness-planning/`) — real content, zero external auth, swappable to a company folder by changing one env var (b) **retrieval = simple keyword/substring scoring** (mirror the mock kb `_score` shape: title>tag>content), NOT embedding/Qdrant (that is Slice 2) (c) **tool = `knowledge_search`**, `risk=LOW`+`read_only=True`+`destructive=False` → auto-pass under any tenant policy (read-only query) (d) **opt-in wiring** = a new `knowledge_root` kwarg on `make_default_executor` (mirrors the `skill_registry` / `todo_store` opt-in pattern at `_register_all.py:346-359`) → NO change to the loop, NO new wire event (e) **frontend UNTOUCHED** — the existing tool-call request/result rendering surfaces the search call + snippets + source paths; the report is the agent's normal streamed final answer (f) **NOT a DEMO** — the data is real project documents, so NO `BackendGapBanner` / DEMO label (the honesty rule cuts the other way here: labelling real data as DEMO would be a lie too) (g) path-safety: the connector confines reads to the configured root (reject `..` traversal / absolute escapes) — the only real new risk surface.

---

## 0. Background

### The gap (`AD-Knowledge-Connector-First-Real-Source`, per `v2-reality-audit-engine-vs-grounding-20260626.md`)

The reality audit (2026-06-26, 4 Explore agents + adversarial cross-verify) found a **two-pole split**: engine ~80% (7/12 categories L3 drive-through) but vision grounding ~17%. Vision pillar 1 (連接公司「既有外部系統」) is audited at **~15% with ZERO real connectors, ZERO MCP tool layer, ZERO ToolRegistry bridge** — every `business_domain` tool routes to a `mock_executor` (the audit's "most dangerous Potemkin": `business_domain_mode` defaults to `"mock"`). The agent today literally has **no tool that reads any real, non-platform-self-built data source**: builtin tools are `echo` / `python_sandbox` / `web_search` (external web) / `memory_search` (5-scope memory, not a knowledge base) / `request_approval` / `write_todos`.

### Why it matters (the missing capability)

The user's core vision is "個人代理，能訪問公司資源（安全可控）、連上不同系統做調查/研究/分析". The engine to drive a knowledge-research task is all there and drive-through-proven (plan via `write_todos`, multi-turn loop, verification, rehydration). What is missing is **a single real hand reaching into real knowledge**. Until one real connector exists, "能訪問公司資源" is structurally false — the demos that "work" all read mock/seed data. This sprint makes pillar 1 move from 0 real connectors → 1, with the smallest honest increment.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `7cedcea4`) | Anchor |
|-------|-------------------------------------|--------|
| External connectors | NONE — `adapters/` holds only LLM-provider adapters (`_base`/`azure_openai`/`_mock`/`_testing`), no data-source connector | `adapters/` glob (19 files, all LLM) |
| Business tools | all 18 route to mock HTTP `localhost:8001`; `business_domain_mode` defaults `"mock"` | `_register_all.py:89,128` · `incident/mock_executor.py:22` |
| KB mock exists, unwired to agent | `/mock/kb/search` naive substring scorer present, but NO `business_domain/knowledge/`, NO `register_knowledge_tools`, agent cannot call it | `mock_services/routers/kb.py:52` |
| Builtin tool can call "external" | `web_search` is a builtin tool that reaches outside → precedent for a `knowledge_search` builtin-style tool | `tools/__init__.py:65` register_builtin_tools |
| Opt-in wiring pattern | each capability = an opt-in kwarg on `make_default_executor`; present → register its tool(s) | `_register_all.py:215-359` (skill_registry :346-350, todo_store :357-359) |
| Prompt driver seam | `DEMO_SYSTEM_PROMPT` + per-request `## Active Skill`/`## Active Plan` append | `handler.py:148` (prompt) · `:514-522` (Active Skill inject) |
| Tool gating | `risk=LOW`+`destructive=False` → auto-pass under any tenant policy (no HITL) | `_contracts/hitl.py` decide_tool_hitl · matrix built from `registry.list()` |
| Tool-call rendering (FE) | existing tool_call request/result render in chat-v2 transcript → reused, NO new wire event | chat-v2 transcript / Inspector (Day-0 D-fe-toolcall-render) |

→ The fix must add (1) a REAL `LocalDocsConnector` that reads + keyword-searches a configured real folder with path-safety, (2) a `knowledge_search` tool wrapping it, (3) an opt-in `knowledge_root` kwarg on `make_default_executor`, (4) a prompt nudge so the agent actually uses it (avoid the §5 "接了沒人用" Potemkin), then PROVE it via drive-through reading the project's REAL docs.

### The design (backend-mostly: real connector + 1 tool + opt-in wiring + prompt nudge; NO migration / wire / panel)

```
NEW  business_domain/knowledge/connector.py  LocalDocsConnector(root): list()/search(query, top_k)
        → reads .md/.txt under root, keyword score (title>tag-less>content), returns (path, snippet, score)
        → path-safety: resolve within root, reject traversal/escape
NEW  business_domain/knowledge/tools.py      KNOWLEDGE_SEARCH_SPEC + register_knowledge_tools(registry, handlers, *, docs_root)
        → risk=LOW, read_only=True, destructive=False → auto-pass
EDIT business_domain/_register_all.py        make_default_executor(knowledge_root=...) opt-in → register knowledge_search
EDIT api/v1/chat/handler.py                   DEMO_SYSTEM_PROMPT nudge ("for company-knowledge questions, call knowledge_search first")
                                              + build_real_llm_handler passes knowledge_root from settings
EDIT core/config/__init__.py                  knowledge_docs_root setting (env KNOWLEDGE_DOCS_ROOT; default project planning docs)
(frontend UNTOUCHED — existing tool-call rendering surfaces the search; report = normal streamed answer)
```

WHY a local-folder connector over wiring the existing kb mock: the kb mock returns **seed/fake articles** — wiring it would be another mock-as-real (exactly what the audit flags). A local-folder connector reading the project's OWN real docs is the same engineering effort but reads **real content** → it actually moves pillar 1. WHY keyword over embedding: smallest honest increment that proves "real connection + real content"; embedding/Qdrant is a Slice-2 quality upgrade, not needed to prove the connection.

### Ground truth (recon head-start — code read on `main` HEAD `7cedcea4`; ALL re-verified §checklist 0.1)

- `_register_all.py:215-411` — `make_default_executor` opt-in pattern; `:346-350` skill_registry, `:357-359` todo_store are the exact shape `knowledge_root` mirrors.
- `_register_all.py:123-189` — `register_all_business_tools` mutates the shared `(registry, handlers)`; a domain's `register_*_tools` is the shape `register_knowledge_tools` mirrors.
- `incident/tools.py:53` — `ToolSpec` construction shape (name/description/input schema/`ToolAnnotations`/`RiskLevel`/`ToolHITLPolicy`/tags).
- `incident/mock_executor.py:25-58` — httpx executor shape (the connector is the REAL analogue, reading files instead of HTTP).
- `mock_services/routers/kb.py:40-49` — `_score` keyword scorer (title 1.0 / tag 0.7 / content 0.5) — the shape `LocalDocsConnector.search` mirrors for files.
- `handler.py:148` `DEMO_SYSTEM_PROMPT`; `:485` + `:514-522` per-request inject seam (where the knowledge nudge / root threading lives).
- `tools/__init__.py:65` `register_builtin_tools` (web_search precedent for an external-reaching builtin tool).
- `_contracts/` `ToolSpec`/`ToolAnnotations`/`RiskLevel`/`ToolHITLPolicy` (read_only/destructive flags drive the auto-pass matrix).

**Baselines (57.144 closeout)**: pytest 2930+5skip · wire 26 · Vitest 922 · mockup 51 · mypy 0/382 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-arch-home** — confirm the connector+tool home: `business_domain/knowledge/` (proposed; reuses the register_*_tools + opt-in pattern) vs `agent_harness/tools/` (builtin-style like web_search) vs a new `connectors/`. Decide by: does it need `BusinessServiceFactory`/mode threading? (NO → it's NOT a mock business domain; keep it a sibling but mark REAL in docstring to avoid mock-as-real confusion). Confirm naming `knowledge_search` / `knowledge` does not collide with `memory_search` or any registered tool.
- **D-optin-kwarg** — confirm adding a `knowledge_root: str | None` kwarg to `make_default_executor` mirrors `skill_registry`/`todo_store` (opt-in, byte-identical when None) + confirm `build_real_llm_handler` is where it's threaded (per-request, settings-sourced).
- **D-config-default** — confirm `core/config` Settings shape + add `knowledge_docs_root` (env `KNOWLEDGE_DOCS_ROOT`); pick a real default folder that EXISTS in-repo (`docs/03-implementation/agent-harness-planning/`) so drive-through has real content with zero setup.
- **D-prompt-nudge** — confirm the `DEMO_SYSTEM_PROMPT` append point + that a knowledge nudge co-exists with the existing tool-use / write_todos / Active-Skill guidance without contradiction.
- **D-fe-toolcall-render** — confirm chat-v2 already renders a tool_call request + result (name + result text) in the transcript so `knowledge_search` + its snippets/source paths are visible WITHOUT a new wire event / panel. If the result text is truncated such that sources are invisible, note scope risk (still no new event — just confirm visibility).
- **D-toolspec-arity** — confirm whether `knowledge_search` handler is single-arity `(ToolCall) -> str` (like business tools / echo) or needs dual-arity ExecutionContext (it does NOT write DB → single-arity, mirror business handlers).
- **D-baselines** — re-confirm pytest 2930+5skip · wire 26 (UNCHANGED — no new event) · Vitest 922 (UNCHANGED — FE untouched) · mockup 51 · mypy 0/382 · run_all 11/11.

## 1. Sprint Goal

Deliver the platform's first real external data-source connector on the chat-v2 main flow and **PROVE it grounds answers in real documents** via a mandatory drive-through: a real UI + real backend + real LLM session where the user asks a knowledge question, the agent (1) calls `knowledge_search`, (2) the tool reads the project's REAL `.md` docs (not mock/seed), (3) returns real snippets + source file paths, and (4) the agent's answer is grounded in that real content with attribution — rendered in chat-v2 with no DEMO label (because it is real). Gates: full backend green (FE untouched). Produces CHANGE-NNN + spike design note. Moves vision pillar 1 from 0 → 1 real connector.

## 2. User Stories

- **US-1** (Cat 2 connector): 作為平台，我希望有一個真實的 `LocalDocsConnector` 能讀取 + 關鍵字檢索一個設定資料夾內的真實 `.md`/`.txt` 文件（含路徑安全），以便 agent 第一次能接觸到非平台自建的真實資料。
- **US-2** (Cat 2 tool): 作為 agent，我希望有一個 `knowledge_search` 工具（read-only、LOW risk、auto-pass）包裝該 connector，以便我被問到公司知識問題時能查真實文件。
- **US-3** (wiring + prompt): 作為平台，我希望 `make_default_executor` 用一個 opt-in `knowledge_root` 掛上工具、且 `DEMO_SYSTEM_PROMPT` 引導 agent 在知識問題時優先呼叫它，以便它真的會被使用（非「接了沒人用」的虛數）。
- **US-4** (drive-through, MANDATORY): 作為驗收者，我希望真 UI + 真後端 + 真 LLM 跑一個知識研究問題，觀察 agent 呼叫 `knowledge_search` → 拿到專案真實文件的真實片段 + 來源 → 產出有出處的答案，且 chat-v2 真實渲染（無 DEMO 標籤，因為是真的），以便證明這是真連接而非 Potemkin。
- **US-5** (closeout): CHANGE-NNN + spike design note (8-point gate) + retrospective + navigators + `AD-Knowledge-Connector-First-Real-Source` 記錄 + golden-path arc Slice 2/3 carryover。

## 3. Technical Specifications

### 3.0 Architecture (backend-mostly: Cat 2 connector + tool + opt-in wiring + config + prompt; NO migration / NO wire event / NO frontend)

```
NEW   business_domain/knowledge/__init__.py            — exports KNOWLEDGE_SEARCH_SPEC + register_knowledge_tools + LocalDocsConnector
NEW   business_domain/knowledge/connector.py           — LocalDocsConnector(root): list()/search(query, top_k); .md/.txt; keyword score; path-safe
NEW   business_domain/knowledge/tools.py               — KNOWLEDGE_SEARCH_SPEC + register_knowledge_tools(registry, handlers, *, docs_root)
EDIT  business_domain/_register_all.py                 — make_default_executor(knowledge_root=...) opt-in → register knowledge_search (mirror todo_store branch)
EDIT  api/v1/chat/handler.py                            — DEMO_SYSTEM_PROMPT knowledge nudge + build_real_llm_handler threads knowledge_root from settings
EDIT  core/config/__init__.py                          — knowledge_docs_root setting (env KNOWLEDGE_DOCS_ROOT; default in-repo planning docs)
NEW   backend/tests/unit/business_domain/knowledge/test_connector.py — list/search/scoring/empty-query/path-traversal-reject/non-md-skip
NEW   backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py — spec shape / handler returns real snippets / auto-pass risk / registration
EDIT  backend/tests/unit/.../test_make_default_executor*.py (if exists) — knowledge_root opt-in registers tool / None = byte-identical
(frontend: UNTOUCHED — existing tool-call rendering + streamed answer)
(NO migration / NO new wire event / NO codegen / NO new panel)
```

### 3.1 `LocalDocsConnector` (US-1) — `business_domain/knowledge/connector.py`

- `LocalDocsConnector(root: Path | str)`: resolves `root` to an absolute, real directory at construction (raise if missing).
- `list() -> list[Path]`: recursively collect `.md`/`.txt` under root.
- `search(query: str, top_k: int = 5) -> list[KnowledgeHit]`: for each file, keyword score (filename/title-line match > body content match; mirror mock kb `_score` ordering), return top-k `KnowledgeHit(source_path_relative, snippet, score)` where snippet = the matched line + a small window of context (so the agent + UI see WHERE it came from).
- **Path safety**: every resolved file path must be `root`-relative (`Path.resolve()` startswith `root.resolve()`); reject anything escaping (defense-in-depth even though input is a query string, not a path — the only real new risk surface).
- REAL connector — module docstring explicitly states it reads real files (distinguishes from the sibling 5 mock domains; avoids mock-as-real confusion the audit warns about).

### 3.2 `knowledge_search` tool (US-2) — `business_domain/knowledge/tools.py`

- `KNOWLEDGE_SEARCH_SPEC`: name `knowledge_search`, neutral JSON-schema input `{query: str (required), top_k: int (default 5, 1..20)}`, `ToolAnnotations(read_only=True, destructive=False, idempotent=True)`, `risk_level=RiskLevel.LOW`, `hitl_policy=AUTO`, tags `("knowledge","read-only")`. Description names that it searches the company knowledge/docs folder and returns snippets with source paths (per the 57.144 tool-description lint — all params described).
- `register_knowledge_tools(registry, handlers, *, docs_root)`: build a `LocalDocsConnector(docs_root)`, register the spec, install a single-arity handler `(call: ToolCall) -> str` that runs `connector.search(...)` and returns a compact JSON/string of hits (`source` + `snippet` + `score`) — so the agent can cite sources.

### 3.3 Opt-in wiring + prompt nudge (US-3) — `_register_all.py` + `handler.py` + `config`

- `make_default_executor(..., knowledge_root: str | None = None)`: when `knowledge_root` is not None, `register_knowledge_tools(registry, handlers, docs_root=knowledge_root)` (mirror the `todo_store` branch at `:357-359`). When None → byte-identical (opt-in).
- `core/config`: `knowledge_docs_root: str` (env `KNOWLEDGE_DOCS_ROOT`), default = the in-repo planning docs folder so drive-through has real content with zero setup.
- `handler.py`: `build_real_llm_handler` passes `knowledge_root=get_settings().knowledge_docs_root` into `make_default_executor`. Append to `DEMO_SYSTEM_PROMPT` a short nudge: "For questions about company knowledge / internal documents, FIRST call `knowledge_search` and ground your answer in the returned snippets, citing the source paths." (the load-bearing instruction — closes the §5 "接了沒人用" risk).

### 3.x What is explicitly NOT done

- Embedding / Qdrant semantic retrieval (Slice 2 — keyword is enough to prove the connection).
- RBAC per-document filtering / multi-tenant folder isolation (Slice 3 — this slice reads one shared configured root).
- PDF / Office parsing (Slice 2+ — `.md`/`.txt` only).
- New wire event / Inspector panel / FE component (existing tool-call rendering suffices; confirmed Day-0 D-fe-toolcall-render).
- Swapping the existing 5 mock business domains to real / the §10 mock-as-real startup warning + Filter dead-control (separate chore, user deferred).

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 0/382+ · run_all 11/11 · pytest 2930+ (+ new) · Vitest 922 (UNCHANGED — FE untouched) · wire 26 (UNCHANGED) · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean (connector is pure-Python file IO, no provider import). Plus the §3 drive-through (MANDATORY — US-4).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `business_domain/knowledge/__init__.py` | NEW |
| 2 | `business_domain/knowledge/connector.py` | NEW |
| 3 | `business_domain/knowledge/tools.py` | NEW |
| 4 | `business_domain/_register_all.py` | EDIT (opt-in `knowledge_root` kwarg + branch) |
| 5 | `api/v1/chat/handler.py` | EDIT (prompt nudge + thread knowledge_root) |
| 6 | `core/config/__init__.py` | EDIT (`knowledge_docs_root` setting) |
| 7 | `backend/tests/unit/business_domain/knowledge/test_connector.py` | NEW |
| 8 | `backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py` | NEW |
| 9 | `backend/tests/unit/.../test_make_default_executor*.py` | EDIT (if present — opt-in coverage) |
| — | `agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** (no loop change; tool flows through existing executor) |
| — | `api/v1/chat/sse.py` / `event_wire_schema.py` / codegen | **UNTOUCHED** (no new wire event) |
| — | `frontend/**` | **UNTOUCHED** (existing tool-call rendering) |
| — | `infrastructure/db/**` | **UNTOUCHED** (no migration) |

## 5. Acceptance Criteria

1. `LocalDocsConnector` reads + keyword-searches real `.md`/`.txt` under a configured root, returns hits with source path + snippet, and rejects path traversal (unit-tested).
2. `knowledge_search` tool registered via opt-in `knowledge_root`; `risk=LOW`+`read_only` → auto-pass under default tenant policy; None → executor byte-identical (unit-tested).
3. `DEMO_SYSTEM_PROMPT` nudge present; `build_real_llm_handler` threads the settings root.
4. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — in chat-v2, a knowledge question makes the agent call `knowledge_search`, which returns REAL content from the project's own docs (verify the snippet matches a real file's real text, NOT a seed/mock article), and the agent's answer cites the real source path; rendered with NO DEMO label. Screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
5. `AD-Knowledge-Connector-First-Real-Source` recorded; CHANGE-NNN + spike design note (8-point gate); calibration recorded; navigators + next-phase-candidates updated (arc Slice 2/3 carryover); reality-audit health indicator noted (pillar 1: 0 → 1 real connector).

## 6. Deliverables

- [ ] US-1 `LocalDocsConnector` (read + keyword search + path-safety)
- [ ] US-2 `knowledge_search` tool (spec + handler + registration)
- [ ] US-3 opt-in `knowledge_root` wiring + config + prompt nudge
- [ ] US-4 drive-through PASS (real docs, real attribution, no DEMO label)
- [ ] US-5 CHANGE-NNN + design note + retro + navigators + AD recorded

## 7. Workload Calibration

- Scope class **`knowledge-connector-real-source-spike` 0.55** (NEW class, 1st data point). Rationale: a greenfield Cat 2 tool + main-flow opt-in wiring + drive-through, shape ~ `skills-system-spike` 0.60 / `skills-bundled-script-spike` 0.60 (greenfield tool module + register-*-tools + opt-in + real execution), but LIGHTER (NO migration / NO wire event / NO new panel / FE untouched — cf. 57.140 which had all three); the one offsetting NET-NEW weight is a REAL connector (file IO + keyword scoring + path-safety) vs a pure wiring spike. Net → 0.55 (a touch under skills-system-spike's 0.60). Cite `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix; flag for re-point if 1st-pt ratio lands out of [0.7, 1.2].
- **Agent-delegated: no** (parent-direct; consistent with the 57.136-144 spike run). `agent_factor` 1.0 → 3-segment form. Rationale: first golden-path sprint involving an architecture-home decision (D-arch-home) + a real new risk surface (path-safety) + a mandatory drive-through — parent-direct keeps the judgment in-loop.
- Bottom-up est ~9.5 hr (connector + path-safety ~2 · tool spec/handler ~1 · opt-in wiring + config + prompt ~1.5 · unit tests ~1.5 · drive-through ~1.5 · closeout incl. design note ~2) → class-calibrated commit ~5.2 hr (mult 0.55). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Architecture-home ambiguity** (business_domain vs tools vs connectors) | Day-0 D-arch-home decides via the "needs BusinessServiceFactory/mode?" test (NO → real sibling, marked REAL in docstring). Proposed: `business_domain/knowledge/`. ≤20% scope shift either way (same 3 files, different folder). |
| **Path traversal / reads outside root** (real new risk surface) | Connector confines all reads to `root.resolve()`; unit test asserts a `..`-style escape is rejected. Input is a query string not a path, so risk is low, but defense-in-depth. |
| **"接了沒人用" Potemkin** (audit §5: memory/skills registered but no prompt driver) | US-3 prompt nudge is REQUIRED, not optional; drive-through US-4 fails if the agent does not call the tool → the nudge is gated by a real check. |
| **Stale `--reload` masks the new opt-in wiring** (Risk Class E) | Clean restart before drive-through: kill stale uvicorn reloader + orphan spawn-workers (Win32_Process PID/PPID/StartTime sweep per 57.97), confirm fresh sole port owner + startup log, THEN drive-through (the knowledge_root is read at executor-build per-request, but the settings load is at startup). |
| **Tool result truncation hides sources in FE** | Day-0 D-fe-toolcall-render confirms the existing tool-call result renders enough to show source paths; if truncated, the agent's final answer still cites sources (the report, not the raw tool result, is the user-facing artifact). |
| **Default docs root not present / empty at runtime** | Default to an in-repo folder that EXISTS (`docs/03-implementation/agent-harness-planning/`, 21 real .md); connector raises clearly if root missing (caught at registration → tool simply absent, agent degrades gracefully). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Embedding / Qdrant semantic retrieval → `AD-Knowledge-Connector-Embedding-Slice2`.
- External-platform source (SharePoint/Confluence/Notion read API) → `AD-Knowledge-Connector-External-Source-Slice2`.
- RBAC per-doc filtering + multi-tenant folder isolation → `AD-Knowledge-Connector-RBAC-Slice3`.
- PDF/Office parsing → `AD-Knowledge-Connector-DocTypes`.
- Citation-structured report + multi-doc synthesis → `AD-Knowledge-Connector-Citation-Slice3`.
- §10 audit follow-ons (mock-as-real startup warning + SessionList Filter dead-control) → separate `chore` (user deferred this sprint).
