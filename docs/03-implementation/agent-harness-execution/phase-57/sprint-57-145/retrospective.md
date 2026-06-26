# Sprint 57.145 Retrospective — first real knowledge connector

**Sprint goal**: ship the platform's FIRST real external data-source connector (`knowledge_search` + `LocalDocsConnector`) as the knowledge-base research golden-path Slice 1, moving vision pillar 1 (connect external systems) from 0→1 per the 2026-06-26 reality audit §9 gate.

**Outcome**: ✅ achieved. Drive-through PASS (3 rounds, real chat-v2 + real Azure gpt-5.2): agent really calls `knowledge_search` → really reads real project `.md` → grounded answer citing 3 real source paths. Vision pillar 1: 0 → 1.

---

## Q1 — What went well

- **Day-0 三-prong caught arch-home cleanly**: D-arch-home confirmed knowledge needs NEITHER `BusinessServiceFactory` nor `mode` (reads files, not mock HTTP) → REAL sibling under `business_domain/knowledge/`, 0% scope shift, no §3/§4 change.
- **Opt-in wiring reused proven seams**: `make_default_executor(knowledge_root=None)` mirrored `todo_store`/`skill_registry` exactly → byte-identical when off, 1-line graceful branch.
- **Drive-through delivered its entire reason for existing**: gate was fully green (15 unit tests, mypy, lints) yet the feature was unusable on the real main flow — the multi-word 0-hit bug only surfaced when a real LLM sent a real semantic query. Caught + fixed + regression-tested in the same sprint.
- **Bonus verifications for free**: the drive-through also exercised `write_todos` (task primitive), per-tenant output-ESCALATE HITL (acme-prod "checkpoint" phrase → pause → approve → resume), and verification (claim verified · llm_judge) — all live on the real flow.
- **Honest grounding proof**: R3 answer cited 3 real `.md` paths and "memory_read 跑了但沒讀 mem0" was verbatim the real glossary text — cross-checked, not fabricated.

## Q2 — Estimate accuracy (calibration)

- **Class**: `knowledge-connector-real-source-spike` **0.55** (NEW, 1st data point). Parent-direct, **agent_factor 1.0** (no code-implementer agent used).
- **Plan**: bottom-up ~9.5 hr → class-calibrated commit ~5.2 hr (mult 0.55).
- **Actual**: ~6-6.5 hr equivalent. Day 0-2 ≈ committed; **Day 3 ran heavier than the plan's single-round assumption** — 3 drive-through rounds + the tokenize fix + 2 regression tests + the clean-restart env-injection debug (the `backend/.env`-absent / OS-env mechanism). Day 4 ≈ committed.
- **Ratio ≈ 1.15-1.25** (upper edge / just at band top). **KEEP 0.55** — single data point; the over-edge is the drive-through-found bug fix, which is the *normal* cost of a real-connection spike (a connector you can't drive-through is a Potemkin). If a 2nd `knowledge-connector-real-source-spike` lands > 1.2, re-point toward 0.65. The bug-fix-in-scope is a feature of the drive-through discipline, not an estimate miss.

## Q3 — What to improve

- **Plan a multi-word drive-through query up front**: the plan listed example questions but didn't flag that a real LLM sends *phrases*; a Day-0 note "the first drive-through query WILL be multi-word — verify tokenization" would have pre-empted the R1 bug (or at least pre-written the regression test).
- **Snippet depth was under-specified**: the plan/connector returned first-match-line only; for a "list everything" question this is structurally insufficient. A Slice-1 connector for a research golden path should have anticipated enumerate-style questions need more than the H1.

## Q4 — Lessons / ADs

- **`AD-Knowledge-Connector-First-Real-Source`** (carryover, Slice 2): (a) deepen snippet (multiple match segments / section-aware) so enumerate questions get a usable body and the agent stops over-searching into `max_turns`; (b) embedding/Qdrant index; (c) external sources; (d) per-tenant RBAC/citation.
- **Lesson (reusable, → feedback candidate)**: a keyword/retrieval tool's unit tests must include a **multi-word OR query** case — a real LLM never sends a single keyword. Single-word-only tests pass while the tool is unusable. This is a specific instance of the drive-through-over-paper-metrics principle.
- **Env mechanism (recorded for next chat drive-through)**: chat real-LLM config (`AzureOpenAIConfig` + `Settings`) is read from OS env vars, NOT `backend/.env` (which doesn't exist; `env_file=".env"` is relative to `cwd=backend/`). A clean restart MUST inject root `.env`'s `AZURE_OPENAI_*` into the start shell (same call, shell state doesn't persist). `/health`=401 (auth middleware) = ready, not failure. Reinforces Risk Class E.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ tool reachable from chat main flow via opt-in default-ON handler thread — drive-through proved the path.
- **AP-4** (Potemkin): ✅ NOT a Potemkin — drive-through proved real call + real file read + real grounded answer (the whole point of the sprint); the multi-word 0-hit bug was found + fixed precisely because of the drive-through.
- **AP-6** (speculative abstraction): ✅ keyword not embedding; single shared root not premature multi-tenant; no "for the future" layers.
- **AP-11** (naming): ✅ `knowledge_search` / `LocalDocsConnector` / `knowledge_docs_root` — names match behavior; `list()` → `list_files()` to avoid shadowing builtin.
- **v2 lints**: tool_descriptions (params described) + llm_sdk_leak (provider-neutral pure file IO) green.

## Q6 — Carryover

- `AD-Knowledge-Connector-First-Real-Source` → Slice 2 (snippet depth + embedding + external sources) + Slice 3 (RBAC/citation). Recorded in `next-phase-candidates.md`.

## Q7 — Drive-through evidence

- Sessions: `f38b32e6` (R1, found bug) / `02857f31` (R2, fix verified + max_turns finding) / `0f91faa8` (R3, clean PASS). 3 screenshots in `artifacts/`. Full narrative in progress.md Day 3.

---

## Design Note Extract (spike sprint — §5.5)

**File**: `docs/03-implementation/agent-harness-planning/49-knowledge-connector-first-real-source-design.md`
**Verified ratio (estimated)**: ~96% (every §3 invariant has file:line + a verification command or the real-Azure drive-through; §5 deferred items are explicitly marked NOT verified)
**8-Point Quality Gate**:
- [x] 1. Section headers map to spike US (US-1..US-4 in §1)
- [x] 2. Each technical claim has file:line (§3 invariants 1-6)
- [x] 3. Decision rationale has a comparison matrix (§2: 4-option matrix + retrieval-match decision)
- [x] 4. Verification commands reproducible (§3: pytest + lint + manual drive-through)
- [x] 5. Test fixture reference (§3: `_write` helper file:line + the real in-repo docs)
- [x] 6. Open invariants explicitly bounded (§5 verified-vs-deferred table + explicit boundary statement)
- [x] 7. Rollback path (§6: disable-via-None + full revert <1 hr, no sentinel to clean)
- [x] 8. 17.md cross-ref (§4: explicitly N/A — reuses Cat 2 ToolSpec, no new contract)

**Reviewer pass**: self-review (solo-dev).
