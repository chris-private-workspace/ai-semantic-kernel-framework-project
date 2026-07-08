# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

**Structure** (post REFACTOR-010, 2026-07-07): this file = forward-looking registry only — (1) roadmap + research status, (2) §Shipped Sprints Pointer Index + §Open Carryover ADs (57.29→57.161), (3) §Top Candidates (#1–#46). The **full verbatim per-sprint SHIPPED narration** lives in [`next-phase-candidates-shipped-archive.md`](next-phase-candidates-shipped-archive.md) (record) + each `memory/project_phase57_*.md` subfile (authoritative). Do NOT paste full SHIPPED blocks back here — see §Maintenance Notes.

---

## 🗺️ Harness Deepening Roadmap (2026-06-10) — organizes many of the carryovers below into 3 workflows + a 10-slice order

**Doc**: [`harness-deepening-proposal-20260610.md`](harness-deepening-proposal-20260610.md) — full 終態 design + all-path slice decomposition (a roadmap / design rationale, NOT a pre-written sprint plan; each slice still runs thin-spike → Day-0 三-prong → code). Built on git HEAD Sprint 57.97 by 3 Explore agents + direct grep (HandoffService) + alignment to this file's carryovers. Provenance + full detail: `memory/project_harness_deepening_proposal.md`.

It condenses the user's "5-point deepening discussion" into 3 workflows and a recommended slice order — **the items in the per-sprint carryovers below (verification, subagent TEAMMATE/HANDOFF, model policy / config 分層) are the raw material it organizes**:

- **A. Verification into loop** (points 1 + 5) — ✅ **A1 SHIPPED (Sprint 57.98)**: in-loop verify gate (retired the `correction_loop.py` wrapper; closed the **resume-bypasses-verification structural hole** — `resume()` now drives the same gated `_run_turns`) → ✅ **A2 SHIPPED (Sprint 57.99)**: verification-ESCALATE human loop (the max-fail terminal conditionally becomes a human pause; APPROVE delivers the held answer, REJECT-with-note coaches one bounded turn; behind a toggle, default OFF = A1) → ✅ **A3 SHIPPED (Sprint 57.111)**: trace-aware critique (the in-loop Cat 10 judge sees recent turns + tool errors — the gate threads a real `trace_state` vs `cast(LoopState,None)`; `loop.py` diff 25/3 threading-only) + a permanent cheap-judge accuracy benchmark (`scripts/benchmark_judge.py` + 28-case golden fixture; real Azure verdict cheap **92.86%** / **trace_delta +42.86%** → **keep cheap**, design note 24 settled; CHANGE-078). **A-family 3/3 done.**
- **B. Subagent completion** (point 3 + C-class live injection) — ✅ **B1 SHIPPED (Sprint 57.101)**: between-turns injection primitive (`MessageInbox` ABC + `_run_turns` drain seam + `InjectionRegistry` + `POST /{id}/inject` + FE composer-mid-run; serves the chat live-injection payoff now, designed so **B2 reuses the same drain seam** — one primitive, two payoffs) → ✅ **B2a/B2b SHIPPED (57.102/57.103)** → ✅ **B3 SHIPPED (Sprint 57.107)**: HANDOFF finish — stub trio retired + spec-only `handoff` tool (**first LLM-drivable handoff**; the Day-0 finding: no ToolSpec was ever registered on 主流量) + handoff governance on `harness_policy` (enabled + allowlist double-gate) + `GET /sessions` lineage + sidechain transcript persistence (0028; CHANGE-074 + note 29) → ✅ **B4 SHIPPED (Sprint 57.110)**: child governance — the tenant-composed Cat 9 engine into BOTH child loops (`loop.py` diff 0; ESCALATE-in-child fail-closes) + `GuardrailTriggered` relay visibility + spawn failure policies fail_fast/soft/partial per-tenant (CHANGE-077 + note 20 §5 RESOLVED). **B-family 4/4 done.** (And A3 ✅ Sprint 57.111 → the FULL harness-deepening 10-slice set A1→A2→B1→B2a→B2b→C1→B3→C2→C3→B4→A3 is COMPLETE — remaining work is the per-sprint carryovers below, none mandatory to the harness.)
- **C. Model policy + config tiering** (point 4 + cc-parity §7.3) — **C1 ✅ SHIPPED Sprint 57.104** (per-tenant model policy; CHANGE-071 + note 27) → **C3 ✅ SHIPPED Sprint 57.106** (per-tenant harness policy 面 — escalate phrases/tools + verification overrides in `meta_data["harness_policy"]` + "Harness Policy" tab — + NEW Cat 9 `RiskyActionDetector` ESCALATE-not-BLOCK, per-tenant switchable; drive-through PASS; CHANGE-073 + design note 28) → C2 compaction cheap tier (remaining C slice).

**Recommended 10-slice order**: A1 → A2 → B1 → B2 → C1 → B3 → C3 → C2 → B4 → A3 (driven by `loop.py` write-contention: A1+B1 both touch loop.py → serialize). **C1 can float to #2** if a per-tenant-governance milestone is prioritized (it doesn't touch loop.py).

**C1 soft-prereq — ✅ FULLY RESOLVED Sprint 57.105**: `AD-RBAC-DB-To-JWT-Wiring-Phase58` shipped as its own slice (per the 57.104 decision below): the OIDC callback + password-login now source the JWT `roles` claim from `RBACManager.get_user_role_codes` (DB `Role JOIN UserRole`, tenant-scoped) — a DB role grant IS authz-effective at login; drive-through proved the full no-dev-login chain (register → password-login → admin renders → model-policy PUT 200; role-less JWT → 403). ISSUE-6 closed. CHANGE-072 + note 23 §5 RESOLVED. *(Historical context: C1 shipped 57.104 using dev-login's `platform_admin` JWT; the prod gap was pre-existing + shared across all 57.55-57.57 admin PUTs; user confirmed "直接做 C1" — don't bundle.)*

> **Status**: roadmap selected/acknowledged by user; NO slice sprint kicked off yet (rolling discipline — A1 plan is written only on explicit user go).

---

## 🔬 Research-Derived Candidates (2026-06-22) — the 8 opportunities × already-shipped reconciliation

**Provenance**: the three 2026-06-22 deep-research docs — [`5-status/ai-agent-harness-consolidated-analysis-20260622.md`](../5-status/ai-agent-harness-consolidated-analysis-20260622.md) §5 (the 8 ranked opportunities) + [`...-market-research-panorama-20260622.md`](../5-status/ai-agent-harness-market-research-panorama-20260622.md) (14 claim-level findings) + [`...-research-vs-v2-mapping-20260622.md`](../5-status/ai-agent-harness-research-vs-v2-mapping-20260622.md) — reconciled against the already-shipped harness-deepening 10-slice set (57.98–57.111) + ABC 15-item gaps + Skills epic + chat-v2. Reconciliation run 2026-06-23 (3 Explore-mapped + direct re-read of `loop.py` / `risky_action_detector.py` / `llm_judge.py` + templates).

**Why this block exists**: the research is a NEW input (2026-06-22) that landed AFTER the 10-slice set finished shipping (6/13). The two pre-existing planning lines (harness-deepening + ABC) were verified **mutually consistent, no rework** (the 10 slices map 1:1 to 57.98–57.111 with zero order drift; ABC keys A/B closed, C uneven). The only un-reconciled surface was "new research ↔ already-shipped" — that is this block. **None of the 8 is a redo of shipped work**; 3 are *tensions with shipped designs* (the real "方向不一致" risk the user worried about), 2 are *partially covered*, 3 are *net-new*.

> **Verification honesty**: the 3 tension items below are **code-grounded (file:line read 2026-06-23), NOT drive-through** — the structural risk is confirmed; the *effect magnitude* + *remedy efficacy* need a real-LLM thin spike before any `loop.py` change. Per evidence-first discipline, these are registered as candidates, NOT as remedies to apply.

### ⚠️ Tensions with already-shipped designs (highest reconciliation value)

- **`AD-Verification-Retry-Context-SelfConditioning`** (research #6; Cat 8/10; tension with **A1 57.98**) — ✅ **CLOSED Sprint 57.136** (MERGED PR #325, main `430f2434`). Thin spike shipped the pluggable `correction_context_strategy` ∈ {`keep` default / `summarize` drop} + a permanent real-LLM A/B harness; the 2-turn self-conditioning effect was measured **directionally real but immaterial** (repeat −4.3pp < 5% threshold; both arms 100% retry-pass) → `keep` stays default, `summarize` is an env opt-in lever, #6 = low-risk. CHANGE-103 + design note `40-verification-correction-hygiene-design.md`. Follow-up: per-tenant strategy → `AD-Verification-Correction-Strategy-PerTenant-Phase58` (C3 seam). Detail: `memory/project_phase57_136_verification_correction_hygiene.md`. *(Original finding, preserved:)* **CONFIRMED real (code-grounded)**: on a failed verification the loop appends the *failed assistant answer verbatim* then a correction message and continues — `loop.py:2620` (`messages.append(Message(role="assistant", content=parsed.text))`), self-documented at `_build_correction_block` docstring (`loop.py:299-301`: *"the conversation — including the just-failed assistant answer — is already in `messages`"*). The next correction turn's context therefore carries the model's own failed output → exactly the self-conditioning shape research §7 warns about (model sees its failure → tends to repeat it). **Calibrate (do NOT overclaim)**: the self-conditioning evidence (arXiv 2509.09677) is from 2000+-step single-task runs; here `max_correction_attempts=2` (only 2 extra turns) and the correction block is an *explicit* "failed verification / please retry" framing (partial mitigation). Effect size at 2-turn horizon is **unmeasured in this repo**. A3 (57.111 trace-aware judge) does NOT address this — it makes the *judge* smarter, not the *corrector's* context. **Remedy direction (needs spike first)**: on `outcome=="correct"`, append the correction feedback WITHOUT the verbatim failed answer (or compress it) — watch LLM-API role-pairing legality after removing the assistant message. ← **recommended first spike** (証據優先: construct fail-then-retry with real Azure, A/B "keep failed answer vs remove" on retry quality).
- **`AD-Guardrail-Detect-To-Restrict`** (research #3; Cat 9/2; tension with **C3 57.106**) — ✅ **CLOSED Sprint 57.137** (MERGED PR #327, main `f47964ad`). Thin evidence-first spike: a permanent real-Docker escape harness measured the gap — **regex_escape_rate 60% · docker_containment_rate 100%** (the deny-list misses urllib/http.client/importlib-concat/asyncio/ftplib/smtplib; DockerSandbox `network none` contains all 10) → the regex is redundant-for-containment under Docker. Shipped: a Cat 2 `SandboxBackend.is_structurally_isolated` property + an env-gated fail-closed lever (`SANDBOX_REQUIRE_ISOLATION`, DEFAULT OFF) so `default_sandbox()` refuses execution (`_FailClosedSandbox`) on a non-isolating backend instead of silently degrading to the production-unsafe SubprocessSandbox; the regex detector docstring is reframed (ESCALATE-for-visibility, NOT the boundary), `check()` byte-unchanged. Backend-only, NO migration/wire/frontend. CHANGE-104 + design note `41-sandbox-detect-to-restrict-design.md`. Follow-ups: `AD-SkillScript-Require-Isolation-Phase58`, `AD-Sandbox-PerTenant-Capability-Profile-Phase58`. Detail: `memory/project_phase57_137_sandbox_detect_to_restrict.md`. *(Original finding, preserved:)* **CONFIRMED regex-based (code-grounded)**: `risky_action_detector.py:64-79` is a regex deny-list (`re.compile` :103, `pattern.search` :132). The detector's OWN MHist (`:31`) is the live evidence for research's "detect→restrict" thesis: *"Sprint 57.110 B4 — +os.popen/os.spawn*/os.exec* (dt found the popen bypass)"* — a child agent rewrote a blocked `os.system` as `os.popen` and slipped through, forcing another pattern (cat-and-mouse). **Calibrate**: python_sandbox already runs under Docker isolation (FIX-033) = partial structural restriction; the detector is a supplementary ESCALATE-to-human layer, not the sole defense. So the directional insight holds (don't treat the regex detector as a primary boundary) but urgency is **medium**, not high.
- **`AD-Verification-KeyCondition-PerTask`** (research #8; Cat 10; refine **A3 57.111**) — ✅ **CLOSED Sprint 57.138** (MERGED PR #329, main `3bf4a727`). Thin evidence-first spike: a NEW `key_condition.txt` judge template extracts the request's per-task must-satisfy conditions (count/format/ordering/inclusion) + checks each (superset of the generic `output_quality` floor), selectable via the EXISTING `chat_verification_judge_template` lever (DEFAULT unchanged, ZERO src code change — `list_templates()` globs). A permanent real-Azure A/B harness measured it: instruction_violation **83% (generic) → 100% (key_condition), gain +16.67pp** BUT **false_positive_rate 20%** + ~1.8× tokens → overall accuracy **tie 90.91%** → does NOT clear the gain≥30%/fp≤20% thresholds → **keep `output_quality` default; `key_condition` ships as a selectable opt-in**. Notable: the generic judge is less blind than theory (83% not ~0%) ∵ A3 trace-awareness already infers "asked 3, got 5 → contradicts-trace". Backend-only, NO migration/wire/frontend. CHANGE-105 + design note `42-verification-key-condition-design.md`. Follow-ups: `AD-Verification-KeyCondition-TwoPhase-Phase58`, `AD-Verification-Conditions-Surface-Phase58`. Detail: `memory/project_phase57_138_verification_key_condition.md`. *(Original finding, preserved:)* **Partially done (code-grounded)**: `output_quality.txt` is already structured (4 explicit failure-modes: refuses / incoherent / empty / contradicts-trace) — NOT an open-ended "is this good?" score. Research #8's key-condition verifier (EMNLP2024) means *extracting per-task must-satisfy conditions and checking each* — the current templates are a generic failure-mode list, not per-task condition extraction. "Refinable" is accurate; **priority low**.

### 🟡 Partially covered

- **`AD-Context-Layered-Compaction-ACON`** (research #4; Cat 4) — ✅ **CLOSED Sprint 57.139** (MERGED PR #331, main `ac8c5ff3`). Evidence-first thin spike: a NEW LLM-free `PreClearCompactor` (standalone tool-result clear at a LOWER trigger, reuses `DefaultObservationMasker`, real token-reduction-ratio `tokens_after`) + `ChainedCompactor` (preclear→hybrid, threads state to defer semantic; `loop.py` UNTOUCHED) + a default-OFF env lever `CHAT_COMPACTION_PRECLEAR_RATIO` (factory returns bare HybridCompactor when unset = byte-identical) + a permanent per-layer yield harness (`benchmark_layered_compaction.py`). A real-Azure A/B (6 cases): **mean tool_clear_reduction 33.72% → IN the ACON band [26-54%]**, captures ~83% of total yield for free + **semantic_deferred_rate 66.67%** → keep default OFF, ship preclear as a selectable opt-in (the win is composition-dependent + the user-anchored masker NO-OPs single-send). The different axis from C2 (57.109): C2 made the summarizer cheap; #4 runs the free layer FIRST to defer it. Backend-only, NO migration/wire/frontend. CHANGE-106 + design note `43-layered-compaction-acon-design.md`. Follow-ons: `AD-Compaction-ToolAnchored-Preclear-Phase58` (tool_use_id-anchored clear for single-send), `AD-Compaction-Preclear-PerTenant-Phase58` (C3 seam). Detail: `memory/project_phase57_139_layered_compaction.md`. *(Original finding, preserved:)* C2 shipped compaction on the cheap tier — a *different axis* (cheaper model, same single-layer 75%/turn>30 trigger); research #4 is *layered* compaction (tool-result clearing first, ACON 26–54% band). Not a redo of C2.

### 🟢 Already identified

- ~~**Explicit task primitive (linear list)** (research #1; Cat 1/2/3/5/7/12)~~ — ✅ **MERGED Sprint 57.140** (PR #333, main `196d8892`; the LINEAR primitive thin spike; DAG deferred). `write_todos` tool + `session_todos` durable store (migration 0031) + run-start `## Active Plan` re-injection + `todos_updated` wire + chat-v2 Todos tab. **Drive-through STRONG PASS** — agent proactively planned (3 todos) + cross-send rehydrated + added a 4th (4/4); AP-4 "ignores the list" risk FALSIFIED. Carryover: `AD-TaskPrimitive-DAG-Phase58` (the DAG evolution) + `AD-TaskPrimitive-Scheduler-Phase58` (research #3 cross-burst auto-continue — its prerequisite durable spine is now shipped) + `AD-TaskPrimitive-Saturation-DriveThrough-Phase58` (5+-send test).

### 🆕 Net-new directions

- ~~**`AD-Eval-PassK-Reliability-Harness`** (research #2; Cat 12)~~ — ✅ **DONE Sprint 57.141** (offline `benchmark_pass_k.py`; pass^k+behavioral-consistency+λ+ε; drive-through real Azure 90 runs — see the 57.141 carryover block below + design note 45).
- ~~**`AD-Observability-OTel-GenAI-Schema`** (research #5; Cat 12)~~ — ✅ **DONE Sprint 57.142** (translation-at-tracer layer mapping bespoke → CNCF `gen_ai.*`; the OTel SDK was ALREADY real so the gap was ONLY the schema; close-time set_attributes FIXED a latent post-response token-loss bug; 1-line loop.py finish_reason; real-`InMemorySpanExporter` conformance harness; drive-through real Azure — production-path `chat` span conformant w/ usage + finish_reasons; see the 57.142 carryover block below + design note 46). Carryover: `AD-Observability-Provider-Attr-Phase58` (`gen_ai.provider.name` adapter→span plumbing) + `AD-Observability-Content-Capture-OptIn-Phase58` (opt-in `gen_ai.input/output.messages` flag) + `AD-Observability-Metrics-GenAI-Labels-Phase58` (extend mapping to `record_metric` labels).
- ~~**`AD-Tool-Description-Lint-Reflection`** (research #7; Cat 2)~~ — ✅ **DONE Sprint 57.144** (MERGED PR #341, main `06d2ca59`; the LAST canonical research item). Half A: `check_tool_descriptions.py` AST lint (11th in run_all) — surfaced + filled **40 real missing param descriptions** (9 harness + 31 business_domain). Half B (evidence-first, default OFF): pure `classify_tool_error`/`render_reflection` (5-taxonomy, orthogonal to Cat 8 ErrorClass) enriched at `executor._build_failure` (dominant path — fixes a latent empty-observation gap: the loop renders `content` not `error`) + `loop.py:3023` rare path (B2 full coverage), gated by `CHAT_TOOL_ERROR_REFLECTION`; `ToolResult += error_taxonomy`. A/B real Azure (8 cases): fix_rate 87.5%=87.5% (+0.00% < 5% materiality) → **KEEP lever OFF** (strong model no headroom; consistent with §2.4 RL-confound hedge; −32 tokens; opt-in lever shipped). See CHANGE-111 + design note 48 + the carryover ADs listed here. Carryover: `AD-Tool-Error-Reflection-Loop-RarePath-DriveThrough` + `AD-Tool-Description-AutoFix-Phase58` + `AD-Tool-Error-Taxonomy-UI-Phase58` + reflection-gain-on-weaker-models/harder-corpora.
- ~~**`AD-UserStop-Resume-Context`** (drive-through-found gap 2026-06-25; Cat 1/7 + chat-v2)~~ — ✅ **DONE Sprint 57.143** (Scope B full CC parity: US-1 `DBMessageStore` own-session-per-call (factory + `set_config('app.tenant_id')` FORCE-RLS + immediate commit) → interrupted-run prompt + tool batches survive the disconnect rollback, loop.py UNTOUCHED; US-2 `/cancel` persists `[Request interrupted by user]` marker + chat-v2 Stop→/cancel; synthetic tool_results dropped per 57.129 atomic-batch. Drive-through PASS real Azure — durable prompt + marker in DB ledger, "continue" rehydrated 19 msgs + continued the ORIGINAL task. See the 57.143 carryover block below + CHANGE-110 + design note 47). Carryover: `AD-Loop-CancelEvent-Poll-Phase58` (graceful in-process loop stop + in-flight LLM cancel) + partial-answer-capture + `message_events` replay-ledger disconnect durability + leading-assistant-marker race guard. **Original analysis (historical)**: when a user STOPS mid-run + types "continue" the agent had no memory of the interrupted run. When a user **STOPS** a chat turn mid-run and types "continue", the agent has **no memory of the interrupted run** (it remembers earlier *completed* turns only → "Continue from what, exactly?"). Drive-through + DB ledger inspection (2026-06-25) confirmed: a stopped-mid-run turn persists **nothing** — not even the user's prompt (a latent **commit-on-disconnect rollback** bug vs the `loop.py:1974` "remembered even if the run fails" intent). CC handles this exact case ("**user clicks Stop seconds after send**", `QueryEngine.ts:436-463`): persist+flush the user msg **before** the LLM call + record `[Request interrupted by user]` + replay the transcript. Fix = add CC's "persist immediately + record the interrupt" discipline onto our existing `DBMessageStore` replay — **NOT new architecture**. **Distinct from 57.88 HITL pause-resume** (different trigger: a user hard-abort, no checkpoint). Why it was missed: cc-parity #2 box-checked "Interrupt & cancellation ✅" at the *mechanism* level + the pause-resume blueprint declared us "ahead of CC" on *mid-loop* resume and dismissed CC's transcript-replay as "mere reload" — the user-facing continue-after-stop case fell in the gap + was never drive-through-tested. Full analysis + root-cause: [`5-status/user-interrupt-resume-context-gap-20260625.md`](../5-status/user-interrupt-resume-context-gap-20260625.md). Proposed spike: US-1 turn-0 immediate-commit (fixes the latent bug standalone) / US-2 Stop→`/cancel` + persist `[interrupted]` marker + synthetic tool_results / US-3 incremental per-append commit / US-4 drive-through (stop mid-run → continue → agent knows what it was doing).

### 🌐 Grounding pillars (reality-audit §9 — 開引擎前先問落地動了沒)

- ~~**`AD-Knowledge-Connector-First-Real-Source`** (Slice 1; Cat 2 + `business_domain/knowledge`)~~ — ✅ **DONE Sprint 57.145** (MERGED PR #344, main `4d3ebdf5`; the **FIRST real external data-source connector** — `knowledge_search` + `LocalDocsConnector` reading real in-repo `.md`, opt-in `make_default_executor` (mirrors todo_store/skill_registry) + handler default-ON + prompt nudge). Answers the reality-audit §9 gate: **vision pillar 1 (connect external systems) 0 → 1**. **Drive-through PASS** real Azure gpt-5.2 (3 rounds, session `0f91faa8`): agent calls `knowledge_search` → real `04-anti-patterns`/`08-glossary`/`00-v2-vision` snippets → grounded answer cites 3 real source paths → `end_turn`. The drive-through **FOUND+FIXED a multi-word-query 0-hit bug** (tokenize + OR match) the green gate couldn't catch (15 single-word unit tests passed while the tool was unusable — textbook gate-green≠usable). BONUS: per-tenant output-ESCALATE HITL verified live. Backend-only NO migration/wire(26)/frontend, reuses Cat 2 ToolSpec. CHANGE-112 + design note `49-knowledge-connector-first-real-source-design.md`. **Carryover (Slice 2/3)**: `AD-Knowledge-Connector-Snippet-Depth-Phase58` (return multiple match segments / section-aware so enumerate questions get a usable body + stop the agent over-searching into `max_turns=8`) + `AD-Knowledge-Connector-Embedding-Phase58` (Qdrant/embedding index over keyword) + `AD-Knowledge-Connector-External-Sources-Phase58` (HTTP/connector framework beyond local files) + `AD-Knowledge-Connector-RBAC-Citation-Phase58` (per-tenant access + citation governance). Detail: `memory/project_phase57_145_knowledge_connector.md`.
- ~~**`AD-Knowledge-Connector-First-Real-Source` Slice 2** (snippet depth + embedding/Qdrant)~~ — ✅ **DONE Sprint 57.146** (MERGED PR #346, main `ee22375d`): section-aware `##` chunking → keyword snippet returns whole section = **fixes 57.145 R2 over-search**; + platform's FIRST real `EmbeddingClient` ABC (`adapters/_base/`, provider-neutral) + Azure `text-embedding-3-large` adapter + `QdrantVectorStore` (`query_points`; **closes CARRY-026 for KB**) + `KnowledgeVectorIndex` (batched ingest + cosine), opt-in `KNOWLEDGE_VECTOR_ENABLED` vector-primary + keyword fail-soft (default OFF → 57.145 byte-identical). **Drive-through PASS** real chat-v2 + real Azure gpt-5.2 + real `text-embedding-3-large` + real Qdrant (trace `f5b394db`): a query with NO literal "adapter"/"neutrality" → `knowledge_search` TOOL_EXEC 1750ms → Qdrant returns `adapters-layer.md`/`llm-provider-neutrality.md` by similarity → answer cites each real source path+section. 2 drive-through bugs the green gate missed: env-name rename (`deployment_embedding`) + **429 batching** (`_EMBED_BATCH=16`; `list_files()` recursion pulls the default root to 418 files/3818 sec → bounded `docs/rules-on-demand` 129 = realistic prod pattern). The 57.145 Slice-2 carryover (`AD-Knowledge-Connector-Snippet-Depth` + `AD-Knowledge-Connector-Embedding`) is now **CLOSED**. CHANGE-113 + design note `50-knowledge-embedding-vector-design.md`. **Remaining (Slice 3 + scale)**: `AD-Knowledge-Connector-RBAC-Citation-Slice3` (per-tenant KB collection isolation via `QdrantNamespaceStrategy` `"kb"` + RBAC per-doc + citation governance) + **NEW `AD-Knowledge-Connector-Ingest-Scale`** (background/offline idempotent ingest — startup-blocking ingest works for a bounded corpus but NOT the full 418-file/3818-section default root) + `AD-Knowledge-Connector-Hybrid-Rerank` (keyword∪vector fusion) + `AD-Knowledge-Connector-External-Sources` (HTTP/SharePoint/Confluence) + `AD-Knowledge-Connector-DocTypes` (PDF/Office). The new `EmbeddingClient` ABC + `QdrantVectorStore` **unblock the Cat 3 memory semantic axis** (CARRY-026, not wired here). Detail: `memory/project_phase57_146_knowledge_embedding_vector.md`.
- ~~**`AD-Knowledge-Connector-RBAC-Citation-Slice3` — isolation half (Slice 3a; per-tenant KB isolation)**~~ — ✅ **DONE Sprint 57.147** (MERGED PR #348, main `ba8d07e1`; branch from main `91ade673`, CI all-green): threads `tenant_id` end-to-end **mirroring `memory_search`** (dual-arity `(ToolCall, ExecutionContext)` + forgery guard) → per-tenant Qdrant collection (`QdrantNamespaceStrategy.collection_name(tid,"kb")` = `tenant_<hex>_kb`) + `payload_filter` (defense-in-depth) + per-tenant corpus subfolder (`<root>/<tenant>/`, shared-root fallback) + lazy idempotent per-tenant ingest; `tenant_id=None` = 57.146 byte-identical. Every building block pre-existed (`QdrantNamespaceStrategy` 49.3 / executor arity auto-dispatch 52.5 / loop `ExecutionContext(tenant_id=…)`) → backend-only, NO executor/loop/migration/wire(26)/frontend; `_ingest_knowledge`→`_warm_knowledge_index` (drop blocking startup ingest → lazy per-tenant). **Drive-through PASS** real chat-v2 + real Azure gpt-5.2 + real `text-embedding-3-large` + real Qdrant (2 tenants alpha/beta, distinct corpora falcon.md(Skyhook)/condor.md(Nightjar)): alpha asks Falcon → only `falcon.md`; **alpha asks Condor → 0 `condor.md`, agent "I did not find Project Condor" (judge 0.98)**; beta asks Condor → only `condor.md`, 0 `falcon.md` leak; Qdrant 2 distinct `tenant_*_kb` collections — bidirectional isolation at agent + vector-store layers. NEW calib `knowledge-per-tenant-isolation-spike` 0.55 (1st pt ~1.0-1.15 IN band). CHANGE-114 + design note `51-knowledge-per-tenant-isolation-design.md`. **Remaining (Slice 3b/3c + scale)**: `AD-Knowledge-Connector-RBAC-Citation-Slice3` **RBAC per-doc half (3b)** + **citation governance (3c)** STILL OPEN + `AD-Knowledge-Connector-Ingest-Scale` (background ingest) + `AD-Knowledge-Connector-Hybrid-Rerank` + `AD-Knowledge-Connector-External-Sources` (HTTP/SharePoint/Confluence) + `AD-Knowledge-Connector-DocTypes` (PDF/Office) + Cat 3 memory semantic axis on this per-tenant pattern (CARRY-026, unblocked NOT wired). Detail: `memory/project_phase57_147_knowledge_per_tenant_isolation.md`.
- ~~**`AD-Memory-Formation-Identity` — Slice 1 (user-identity write + always-on inject)**~~ — ✅ **DONE Sprint 57.148** (MERGED PR #350, main `4fe02965`): the fix for a LIVE-drive-through gap the user found on chat-v2 (new session → "我不知道你是誰…沒有取到任何記錄"). Diagnosis (reality-audit "引擎接好 ≠ 落地"): the 5-layer memory is WIRED but (1) **formation never fires** (`memory_write` LLM-discretionary, nothing nudges it) + (2) **surfacing is ILIKE query-gated** (`builder.py:581` passes the user msg as query → `user_layer.py:88` `content ILIKE %query%` → "你是誰" never matches "name is Chris"). Two coupled pieces (both required or it's an AP-4 Potemkin): a system-prompt `MEMORY_FORMATION_NUDGE` (rides the proven skills-catalog seam `loop.py:1970`, gated on memory tools) → agent proactively `memory_write(scope=user)`; + a NEW additive `MemoryRetrieval.profile()` (wildcard user-scope long_term, bypasses the empty-query guard) merged UNCONDITIONALLY into `DefaultPromptBuilder.build()`'s user block (dedup by hint_id + Tier2 cap + graceful-degrade) so identity surfaces EVERY turn keyword-independently. Backend-only NO migration/wire(26)/frontend; `user_id=None` byte-identical. **Drive-through PASS** real chat-v2 + real Azure gpt-5.2 (jamie@acme.com baseline 0 rows): Leg 1 stated identity (no "remember me") → agent proactively `memory_write` ×2 (`'User name is Chris.'` 0.90 / `'Chris is responsible for developing the Knowledge Connector feature…'` 0.85, perm); Leg 2 NEW session "你知道我是誰嗎?" (0 keyword overlap) → "你是 Chris。我也記得你目前負責…開發 Knowledge Connector" (Inspector 2 user-reads, trace `ddc56264`) — proves always-on inject NOT query-gated; Leg 3 priya (diff user) → "我不知道你是誰" (per-user isolation). pytest 2999 (+11; 1 regression `test_skills_wiring` real_llm `==DEMO` byte-identical assumption caught+fixed) · run_all 11/11. NEW calib `memory-formation-identity-spike` 0.60. CHANGE-115 + design note `52-memory-formation-identity-design.md`. **Bonus recon**: `MemoryExtractor.extract_session_to_user` ALREADY exists (unwired) = the Option-B building block. **Carryover (next slices)**: `AD-Memory-Formation-Auto-Extract` (Option B deterministic post-turn extraction — wire the existing `MemoryExtractor`) + `AD-Memory-User-Upsert-By-Key` (dedup dup identity rows — `UserLayer.write` always INSERTs) + `AD-Memory-Formation-Session-Recall` (缺口 2 — cross-session CONVERSATION/message recall + session-summary → Layer 5) + CARRY-026 (memory semantic/Qdrant axis, now unblocked by 57.146 EmbeddingClient + the 57.147 per-tenant pattern) + tenant/role/session always-on injection. Detail: `memory/project_phase57_148_memory_formation_identity.md`.
- ~~**`AD-Memory-Formation-Auto-Extract` — Option-B deterministic post-send extraction (Slice 2)**~~ — ✅ **DONE Sprint 57.149** (MERGED PR #352, main `02ca23ba`): wires the long-unwired `MemoryExtractor` (Cat 3, 51.2) onto the chat path — after EVERY real_llm send (env-gated `CHAT_MEMORY_AUTO_EXTRACT` default ON, cheap `profile.cheap` tier), a Starlette `BackgroundTask` deterministically extracts durable user facts → `UserLayer` tagged `source="auto_extract"`, so the platform forms memory **even when the agent never calls `memory_write`** (57.148 Option-A nudge is discretionary; this is the deterministic safety net). Prompt-level dedup reads the 57.148 `profile()` first. `build_chat_memory_extractor` is self-contained (0 of `build_handler`'s ~12 callers touched). Backend-only, NO migration (the `memory_user.source` column pre-existed)/wire(26)/frontend; `=false`/`user_id=None` byte-identical. **Drive-through PASS** real chat-v2 + Azure gpt-5.2 (3 legs): dan "Project Aurora, Oracle→PostgreSQL, Q3" → `[auto_extract]` conf 0.99 → NEW session recalls Aurora (via always-on `profile()`, Inspector read of `memory_user:5d487f86`) → priya (diff user) 0-leak. **Day-3 evolution**: extraction moved sync→`BackgroundTask` off the SSE generator (the `async generator ignored GeneratorExit` + OTel `Failed to detach context` noise was investigated + found PRE-EXISTING `agent_harness/observability/tracer.py:200 _span_cm`, the 57.71/57.142 OTel-on-SSE-close issue — NOT the extraction). pytest 3013 (+14) · mypy 0/392 · v2 lints 25. NEW calib `memory-formation-extract-spike` 0.60 → re-pointed **0.85** (1st pt ~1.3-1.4 OVER per the 57.148 note; drive-through discovery loop = variance driver). CHANGE-116 + design note `53-memory-auto-extract-design.md`. **Remaining (memory-formation arc)**: `AD-Memory-User-Upsert-By-Key` (`UserLayer.write` still INSERTs → dup rows) + `AD-Memory-Formation-Session-Recall` (缺口 2 — cross-session CONVERSATION recall + session-summary → Layer 5) + **NEW `AD-Verification-Judge-Memory-Inject-Blind`** (the in-loop 57.98 judge false-positive-REJECTs memory-injected recalls — it sees only the conversation trace, not the `profile()`-injected memory; agent still recalled correctly) + CARRY-026 (semantic axis) + CARRY-027 (async queue) + per-tenant auto-extract override + tenant/role/session always-on injection. Detail: `memory/project_phase57_149_memory_auto_extract.md`.
- ~~**`AD-Memory-User-Upsert-By-Key` — write-side dedup (memory-formation arc dedup slice)**~~ — ✅ **DONE Sprint 57.150** (MERGED PR #354, main `32ae4489`): `UserLayer.write()` always INSERTed → 57.149's auto_extract (every send) piled up duplicate user-fact rows that diluted 57.148 `profile()` top-k (top_k=5 conf-ordered → one fact ×5 fills all identity slots). Fix: `MemoryUser.dedup_key VARCHAR(32) = md5(normalize(content))` + `(tenant,user,dedup_key)` unique constraint + `pg_insert … on_conflict_do_update` (greatest confidence / latest content / bump updated_at / **KEEP first-writer source+metadata** — a later auto_extract does NOT relabel a manual fact) + migration **0032** (add col → backfill `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` matches `_dedup_key` byte-for-byte → delete pre-existing dups (row_number keep highest-conf/newest) → add constraint). All 3 writers (57.148 nudge / 57.149 auto_extract / agent `memory_write` via `memory_tools.py:352`) dedup at the one `UserLayer.write` chokepoint. **Exact-normalized** dedup (case/whitespace), NOT semantic (→ CARRY-026). Backend-only NO wire(26)/frontend/new-contract. **Drive-through PASS** real chat-v2 + Azure gpt-5.2 (dan): send-1 agent `memory_write` (conf 0.6, source none) + auto_extract BackgroundTask (conf 0.99) of the SAME verbatim "Project Helix DT150…" fact → **1 row** (key dd16b505, conf=greatest=0.99, updated bumped, first-writer source kept) = INTRA-send dedup LIVE; send-2 repeat → **STILL 1 row** (updated bumped again) = cross-send; new-session single clean recall. Pre-57.150 = 2-4 rows. 6 real-Postgres integration tests + adapted unit/ops_emit tests + migration up/down/up clean. pytest 3022 (+9) · mypy 0/393 · run_all 11/11. NEW calib `memory-upsert-dedup-spike` 0.60 (1st pt ~1.07 IN band). CHANGE-117 (no design note — focused correctness fix). **Remaining (memory-formation arc)**: **NEW `AD-Memory-Ops-Emit-Dedup-On-Reaffirm`** (the `memory_ops` log still emits a WRITE op on a no-change re-affirm — doesn't dilute `profile()` which reads `memory_user`, deferred) + `AD-Memory-Formation-Session-Recall` (缺口 2 — cross-session CONVERSATION recall + session-summary → Layer 5) + `AD-Verification-Judge-Memory-Inject-Blind` (in-loop judge memory-blind) + CARRY-026 (semantic axis → would enable semantic near-dup dedup beyond this exact-normalized dedup) + CARRY-027 (async queue) + per-tenant auto-extract override + tenant/role/session-layer dedup (this = user layer only). Detail: `memory/project_phase57_150_memory_upsert_dedup.md`.
- ~~**`AD-Memory-Formation-Session-Recall` — cross-session conversation recall (缺口 2; the memory-formation arc's last slice)**~~ — ✅ **DONE Sprint 57.151** (MERGED PR #356, main `496d8dcf`; branch from main `f664f34d`, CI all-green): the arc (57.148/149/150) recalled discrete user FACTS but NOT what was *discussed/decided* in a prior session. **Day-0 三-prong MAJOR catch** (`D-table-already-exists`): plan v0 invented a `memory_session` table; grep found `memory_session_summary` ALREADY designed + created (`0007_memory_layers.py:221` / `09-db-schema-design.md:481`, "Layer 5 持久化") with richer cols (`session_id UNIQUE` + `summary` + `key_decisions`/`unresolved_issues` JSONB + `extracted_to_user_memory`), junction-style (no direct RLS) → REUSE it (Check-Existing 鐵律, saved ~1.5 hr + avoided AP-3 duplicate-table + a wrong direct-RLS migration). Shipped: additive `updated_at` (migration **0033**, revision id ≤32 chars — Day-1 `D-revision-id-len`: `alembic_version.version_num` is VARCHAR(32)) + `DBSessionSummaryStore` (`upsert_summary` ON CONFLICT on the session_id UNIQUE = one rolling row, mirrors 57.150; `recent_for_user` JOINs `sessions` for tenant+user scope + exclude-current + ORDER BY updated_at DESC, own-session + `set_config` since `sessions` is FORCE RLS) + `SessionSummarizer` (cheap-tier ChatClient → structured JSON `{summary, key_decisions, unresolved_issues}`, provider-neutral, AP-8 allowlisted like extraction.py, rides the 57.149 post-send `_maybe_auto_extract` BackgroundTask seam) + `MemoryRetrieval.recent_sessions()` (mirrors 57.148 `profile()`, `SessionSummaryReader` Protocol) injected into `DefaultPromptBuilder.build()` (prepend session slot, graceful-degrade). One env flag `chat_session_summary` (default ON) gates BOTH formation + recall → byte-identical to 57.150 when off. Backend-only NO new table/wire(26)/frontend. **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2: Leg 1 dan's session A `bac53436` (billing MongoDB→Postgres / dual-write / invoices JSONB-vs-table) → `memory_session_summary` row with ALL 3 cols populated; Leg 2 NEW session B `760d5db9` "what were we working on last session?" → recalled A's arc VERBATIM (Verification 0.98) + coexists w/ 57.149 "Project Aurora" user fact; Leg 3 priya (same tenant) → 0 leak (`dan_content_leak: false`), only her SOC 2 profile. pytest 3042 (+20) · mypy 0/396 · run_all 11/11 · migration up/down/up clean · FE untouched. NEW calib `memory-session-recall-spike` 0.60 (1st pt ~1.05 IN band). CHANGE-118 + design note `54-memory-session-recall-design.md`. **Carryover**: `AD-Memory-Session-Summary-Extract-Coordination` (set `extracted_to_user_memory`) + `AD-Memory-Formation-Combine-Extract-Summarize` (one LLM call for extract+summarize — two cheap calls/send today) + `AD-Memory-Session-Summary-Incremental` (non-full-ledger summarization) + `AD-Memory-Session-Summary-Inspector-Phase58` (chat-v2 Inspector surface + wire event) + CARRY-026 (semantic ranking) + CARRY-029 (SessionLayer→DB). **The memory-formation arc (57.148→151) is now CLOSED** (identity → auto-extract → dedup → session-recall). Detail: `memory/project_phase57_151_memory_session_recall.md`.
- ~~**`AD-Memory-Formation-Combine-Extract-Summarize` — combine post-send extract + summarize into ONE LLM call**~~ — ✅ **DONE Sprint 57.152** (MERGED PR #358, main `cd317ec7`, CI all-green; branch from main `a6e8d586`): a memory-formation arc efficiency follow-on (the arc was already closed). The chat post-send hook loaded the ledger ONCE but made TWO cheap-tier LLM calls over the SAME conversation (57.149 extract + 57.151 summarize) = ~2× background token/latency. Fix: a NEW `MemoryFormationWorker` (`agent_harness/memory/formation.py`) that **COMPOSES** the two existing workers (NOT replace — `SessionSummarizer`'s only non-test caller was the chat path = AP-2/AP-4 orphan risk) and by default makes ONE combined `chat()` returning both the facts array + the summary object, dispatching each half to the SAME write code via extracted behavior-preserving `MemoryExtractor.write_facts` + `SessionSummarizer.store_summary`; `_form_separate` (the `chat_memory_combined_formation=false` fallback) delegates to the two full single-call methods → both stay live on the chat path. One flag `chat_memory_combined_formation` (default ON) = one-env-var revert to the proven two-call path. Wiring: ctx `{extractor,summarizer}`→`{former}`; `_maybe_auto_extract` calls `former.form()` once (profile() gated on `former.wants_user_facts`). AP-8 allowlist += formation.py. Backend-only NO migration/wire(26)/frontend/loop.py; parent-direct agent_factor 1.0. **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2: one send ("I'm Marcus … Redis→DynamoDB session store … write-through cache … TTL vs explicit invalidation") → DB shows a `memory_session_summary` row (3 cols) AND `memory_user [auto_extract]` rows at the SAME `15:20:30` timestamp = ONE combined call (unit test `chat_call_count==1`); 57.150 dedup coexists. Leg-2 recall (read path unchanged): both halves trace-injected; final answer hit 2 PRE-EXISTING carryovers (cross-sprint dan identity conflict + `AD-Verification-Judge-Memory-Inject-Blind`) — NOT 57.152 regressions. pytest 3053 (+11) · mypy 0/397 · run_all 11/11. NEW calib `memory-formation-combine-spike` 0.60 (1st pt ~1.0 IN band). CHANGE-119 + design note `55-memory-combined-formation-design.md`. **NEW carryover**: `AD-Memory-Combined-Formation-AB-Quality` (a real-Azure A/B harness measuring whether the combined prompt degrades either half's quality vs two focused calls — mirrors 57.136/137/138; the flag + drive-through sufficed this sprint). Detail: `memory/project_phase57_152_memory_combined_formation.md`.
- ~~**`AD-Verification-Judge-Memory-Inject-Blind` — memory-aware in-loop verification judge**~~ — ✅ **DONE Sprint 57.153** (MERGED PR #360, main `0ce4d1fa`, CI all-green; branch from main `5bbf1a77`; closes the AD logged 57.149 carryover, re-confirmed 57.152 Leg-2): the in-loop Cat 10 judge (57.98 A1 + 57.111 A3) saw only `{output}`+`{trace}` (built from the `messages` accumulator); the `profile()`/`recent_sessions()`-injected memory lives in the per-turn prompt artifact (system prompt, `loop.py:2377`), NEVER in `messages`, and `build_trace_block` drops system msgs (`_trace.py:107`) → the judge was BLIND to the agent's grounding → false-positive-REJECTed memory-grounded recalls → coached into no-recall answers (57.149/152 Leg-2). Fix = the direct parallel of 57.111 A3 (`{trace}`): a NEW `TransientState.injected_memory` field + `build_memory_block` helper + a `{memory}` judge-template placeholder + a "consistent-with-memory = GROUNDED, still flag contradictions" instruction (`output_quality`+`key_condition`); the loop captures per-turn `memory_accesses` at the PromptBuilder build branch and threads them into `_cat10_verify_gate(injected_accesses=)`, gated by a NEW default-ON env lever `CHAT_VERIFICATION_MEMORY_GROUNDING` (ctor kwarg mirrors 57.136). **Key design**: a `TransientState` field (the gate already builds a throwaway trace_state) over a `Verifier.verify` ABC kwarg = 0 verifier-impls + 0 test-stubs vs ~13. `build_memory_block`/`build_trace_block` re-exported from `verification/__init__.py` (check_cross_category_import). Backend-only NO migration/wire(26)/frontend; parent-direct agent_factor 1.0. **Real-Azure A/B** (`benchmark_memory_grounded_judge.py`, 10 cases): `fabrication_catch_rate` bare **0%→memory 100%** (+100pp), `grounded_recall_false_reject_rate` 0%→0% → **KEEP default ON** (honest finding: the lenient `output_quality` judge doesn't false-reject grounded recalls in isolation → the fix's deterministic value is CONTRADICTION detection at zero false-reject cost; verdict logic = two-sided OR). **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2: Leg-1 jamie "Dana Okafor / Verification Loops" → memory_write ×2 + verify 0.99; Leg-2 NEW session 0-keyword "你知道我是誰?" → the Loop trace shows the user memory injected (NEW Dana facts + accumulated 57.148 Chris facts = a CONTRADICTION = the 57.152 Leg-2 scenario reproduced); the agent recalled both grounded facts + flagged the conflict; memory-aware judge **VerificationPassed 0.98** (grounded recall DELIVERED vs pre-fix blind judge → rejected→no-recall). pytest 3082 (+29) · mypy 0/397 · run_all 11/11. NEW calib `verification-memory-grounding-spike` 0.60 (1st pt ~1.0 IN band). CHANGE-120 + design note `56-verification-memory-grounding-design.md`. **NEW carryover**: `AD-Verification-Memory-Grounding-PerTenant-Phase58` (C3 config-tiering per-tenant grounding policy) + `AD-Verification-Memory-Grounding-Inspector-Phase58` (a chat-v2 surface / wire event for "the judge saw memory this turn"). Detail: `memory/project_phase57_153_verification_memory_grounding.md`.

- ~~**`AD-Memory-Combined-Formation-AB-Quality` — combined-vs-separate formation quality A/B**~~ — ✅ **DONE Sprint 57.154** (MERGED PR #362, main `64732999`, CI all-green; branch from main `a0cf503a`; CHANGE-121 + design note `57-memory-combined-formation-quality-ab-design.md`): the 57.152 carryover — Sprint 57.152 combined the two post-send cheap-tier formation calls (57.149 facts + 57.151 summary) into ONE `chat()` via `MemoryFormationWorker` default ON with NO numbers on quality. Fix = a real-Azure A/B harness (backend-only, **ZERO src change**): NEW `benchmark_combined_formation_quality.py` drives the REAL `form()` under both arms (`combined=True` one call / `False` two focused calls) via **capturing sinks** (`_CapturingUserLayer`/`_CapturingSummaryStore` — AP-10 safe, the only doubles are the terminal DB writes; build→chat→parse→dispatch is production code) + a **Hybrid oracle** (user-picked via AskUserQuestion: deterministic facts keyword-group coverage + spurious count; LLM-judge summary faithfulness `[0,1]` via a self-contained rubric over the neutral ChatClient ABC, NOT a production `verification/templates/` orphan) + a two-sided verdict (KEEP iff no material facts/summary regression + no spurious inflation; the ~2× efficiency win was established 57.152) + a 10-case difficulty-graded corpus (`tests/fixtures/memory/memory_formation_quality_cases.yaml`) + 24 CI-safe tests (spy formation+judge clients; `run_arm` drives the REAL worker offline asserting combined=1 / separate=2 chat/case). parent-direct agent_factor 1.0. **Verdict — 3 real-Azure runs, KEEP combined default ON**: the mechanical single-run verdict FLIPPED on Run 1 (facts_coverage combined **95%** vs 100% = exactly −5pp, one case dropping one keyword-group at the float `0.95−1.0` boundary), but re-running 2× → both clean KEEP (facts 100%/100%); the −5pp did NOT reproduce → run-to-run LLM noise (temp=0 is deterministic-*ish*). summary tied-to-better (mean Δ +0.009); spurious tied-to-better (0.30–0.40 vs 0.40) → combined ≈ separate **quality-equivalent within LLM noise** → **57.152 default validated, NO src change**. Honest discipline: did NOT take the single-run FLIP at face value NOR tune the threshold to force a KEEP — re-ran to distinguish noise from signal. NO migration/wire(26)/frontend; NO chat-v2 drive-through (default unchanged). 24 new tests · run_all 11/11 · black/isort/flake8 + llm_sdk_leak clean · mypy `src/` 0/397 (harness in `scripts/` not CI-mypy-gated). NEW calib `memory-formation-combine-ab-spike` 0.60 (1st pt ~0.95–1.03 IN band). **Carryover**: `AD-Memory-Formation-AB-Robustness-MultiRun` (a `--runs N` averaging flag to remove the single-run ±5pp variance — the borderline first run forced a manual 3× repeat) + `AD-Memory-Combined-Formation-PerTenant-Phase58` (C3 per-tenant combined/separate override) + extend the A/B to weaker models / harder corpora if a future strong-model verdict is inconclusive. Detail: `memory/project_phase57_154_combined_formation_quality_ab.md`.
- ~~**`CARRY-026` — Cat 3 memory semantic axis, Slice 1 (L4 user-layer vector recall)**~~ — ✅ **DONE Sprint 57.155** (MERGED PR #364, main `e1083964`, CI all-green; branch from main `c3d1bff1`; CHANGE-122 + design note `58-memory-vector-recall-design.md`): wires the long-stubbed `"semantic"` time-scale (logged 51.2 as CARRY-026; KB half closed 57.146, memory half open) onto the L4 user layer. NEW `agent_harness/memory/vector_index.py` `MemoryVectorIndex` mirrors `KnowledgeVectorIndex` (reuse the `EmbeddingClient` ABC + `QdrantVectorStore` + `QdrantNamespaceStrategy("user_memory")`, all pre-existing) → per-tenant+per-user cosine recall replacing the `[]` stub in `UserLayer.read`; opt-in `MEMORY_VECTOR_ENABLED` (default OFF → byte-identical to 57.154), lazy ingest-on-search (per-user count-idempotency + `dedup_key`-derived point ids — does NOT touch the 57.150 write path), fail-soft to keyword/stub. `QdrantVectorStore.count` gains `payload_filter` (per-user count). Backend-only NO migration/wire(26)/frontend; parent-direct agent_factor 1.0. Day-0 三-prong 0-drift + 1 scope REDUCTION (AP-8 flags only `.chat()`/`.stream()` → the embed/search-only index needs NO allowlist). **Drive-through PASS** (real chat-v2 + Azure gpt-5.2 + real `text-embedding-3-large` 3072-dim + real Qdrant): machinery LIVE (`memory vector index built` on the main flow + per-user Qdrant ingest jamie 5 / priya 2 pts in `tenant_09eb…_user_memory`, Cosine + count-idempotency) + Leg-1 fact written + Leg-2 keyword-disjoint recall + **CLEAN per-user isolation** (priya cannot retrieve jamie's memory-only "Project Lodestar" nor his name despite the shared per-tenant collection — the `user_id` payload filter isolates). **Honest caveat**: the Leg-2 recall is co-supported by the always-on `profile()` (57.148) + `knowledge_search` muddied attribution → the semantic axis's DISTINCTIVE value (relevance-ranked recall at many-fact scale) is proven at the machinery/isolation layer, NOT behaviourally → a many-fact A/B is deferred (`AD-Memory-Vector-Recall-Precision-AB`). 17 new tests · pytest 3123/6skip · mypy `src` 399/0 · run_all 11/11. NEW calib `memory-vector-recall-spike` 0.60 (1st pt ~1.0 IN band). **Carryover (CARRY-026 remaining + follow-ons)**: `AD-Memory-Semantic-Axis-System-Tenant-Layers` (L1 system + L2 tenant slices) + `AD-Memory-Session-Summary-Semantic-Rank` (57.151 recency→semantic) + `AD-Memory-Semantic-NearDup-Dedup` (extend 57.150 exact→semantic) + `AD-Memory-Vector-Incremental-Write` (embed-on-write + orphan cleanup on delete) + `AD-Memory-Vector-PerTenant-Phase58` (C3 override) + `AD-Memory-Vector-Recall-Precision-AB` (many-fact semantic-vs-profile A/B) + `AD-Memory-Vector-Inspector-Phase58`. Detail: `memory/project_phase57_155_memory_vector_recall.md`.

### 🛡️守住不要動 (reverse-direction guard — do NOT weaken these to chase research)

Two places where **V2 is already stronger than the research exemplars** (research §5):
- **Durable, governable HITL pause** (heavier than LangGraph/CC — the correct multi-tenant-SaaS choice). Don't simplify to match lighter exemplars.
- **5-scope memory isolation** (stricter than CC's single `MEMORY.md`). If/when learning from ACE memory-scoring, do NOT weaken the scope isolation.

### Recommended next move (NOT a plan — selection-gated per the Selection Rule above)

This list follows the canonical research §5 ranked order (#6 → #3 → #8 → #4 → #1 → #2 → #5 → #7); work the next un-done item unless the user selects otherwise.

1. ~~#6 `AD-Verification-Retry-Context-SelfConditioning`~~ — ✅ **DONE Sprint 57.136** (keep-default verdict; #6 low-risk at 2 turns; `summarize` env lever shipped).
2. ~~#3 `AD-Guardrail-Detect-To-Restrict`~~ — ✅ **DONE Sprint 57.137** (60% regex escape / 100% Docker containment measured; env-gated fail-closed lever shipped; detector reframed).
3. ~~#8 `AD-Verification-KeyCondition-PerTask`~~ — ✅ **DONE Sprint 57.138** (key_condition template + A/B; gain +16.67pp on instruction_violation but 20% FP → net tie → keep output_quality default, key_condition = opt-in; #8 directionally real, low-priority refinement confirmed).
4. ~~#4 `AD-Context-Layered-Compaction-ACON`~~ — ✅ **DONE Sprint 57.139** (tool-result preclear layer + per-layer yield harness; mean tool_clear 33.72% IN ACON band + 66.67% semantic-deferral → keep default OFF, preclear = selectable opt-in; follow-ons `AD-Compaction-ToolAnchored-Preclear-Phase58` + `AD-Compaction-Preclear-PerTenant-Phase58`).
5. ~~#1 Explicit task primitive (linear)~~ — ✅ **MERGED Sprint 57.140** (PR #333, main `196d8892`; LINEAR primitive; `write_todos` + `session_todos` store + run-start re-injection + chat-v2 Todos tab; drive-through STRONG PASS — proactive plan + cross-send rehydration; AP-4 risk FALSIFIED; DAG / scheduler deferred to Phase 58).
6. ~~#2 `AD-Eval-PassK-Reliability-Harness`~~ — ✅ **DONE Sprint 57.141** (offline `benchmark_pass_k.py`; pass^k+consistency+λ+ε; divergence 0% on a too-easy corpus BUT answer-consistency 75% + λ-degradation 50% surfaced; design note 45).
7. ~~#5 `AD-Observability-OTel-GenAI-Schema`~~ — ✅ **DONE Sprint 57.142** (translation-at-tracer bespoke→CNCF `gen_ai.*`; SDK already real → schema-only gap; latent token-loss bug FIXED; drive-through real Azure conformant; design note 46).
8. ~~#7 `AD-Tool-Description-Lint-Reflection`~~ — ✅ **DONE Sprint 57.144** (Half A lint + 40 param fixes; Half B taxonomy + executor/loop enrich + env lever; A/B real Azure → KEEP lever OFF; CHANGE-111 + design note 48).

> **ALL 8 canonical research items (#1-#8) are now CLOSED** (#6 57.136 / #3 57.137 / #8 57.138 / #4 57.139 / #1 57.140 / #2 57.141 / #5 57.142 / #7 57.144). The candidate pool is now the deferred **Phase-58 carryover ADs**: DAG task primitive + cross-burst scheduler (`AD-TaskPrimitive-{DAG,Scheduler}-Phase58`, prereq #1 shipped) / observability provider-attr + content-capture + metrics-labels / `AD-Loop-CancelEvent-Poll` / the per-research follow-ons (tool-error rare-path drive-through, autofix, taxonomy-UI; verification answer-consistency surface; compaction tool-anchored/per-tenant; harder pass^k corpus). No canonical-ranked "next" remains — the next sprint is a user-selected pick from this pool (each still runs thin-spike → Day-0). (`AD-UserStop-Resume-Context` ✅ CLOSED Sprint 57.143.)

---

## 📦 Shipped Sprints — Pointer Index (57.29 → 57.161)

> The full verbatim SHIPPED carryover narration for every sprint below moved to **[`next-phase-candidates-shipped-archive.md`](next-phase-candidates-shipped-archive.md)** (REFACTOR-010; Ctrl-F the sprint id). Per-sprint authoritative detail = the `memory/project_phase57_*.md` subfile + the sprint's `retrospective.md`. **This table is the pointer; the archive + memory subfile are the record.** The curated, actionable open items are §Top Candidates (#1–#46) further below.

| Sprint | Shipped (closes / PR) | Detail pointer |
|--------|-----------------------|----------------|
| 57.162 | DAG soft-enforce advisory + cycle report + Inspector Viz — closes AD-TaskPrimitive-DAG-{Enforce,CycleReport,Viz}-Phase58 (57.156 carryovers); **committed LOCAL, PR-pending (not pushed per user)** | memory/project_phase57_162_dag_enforce_cyclereport_viz.md |
| 57.161 | structural compactor real token re-count — closes AD-Compaction-Structural-RealTokenCount; PR #378 | memory/project_phase57_161_structural_realcount.md |
| 57.160 | tool-anchored observation masking — closes AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path; PR #376 | memory/project_phase57_160_tool_anchored_masking.md |
| 57.159 | compaction L2→L3 drive-through + Inspector timeline marker — PR #374 | memory/project_phase57_159_compaction_drivethrough_marker.md |
| 57.156 | DAG task primitive — closes AD-TaskPrimitive-DAG-Phase58; PR #366 | memory/project_phase57_156_dag_task_primitive.md |
| 57.157 | cross-burst scheduler — closes AD-TaskPrimitive-Scheduler-Phase58; PR #370 | memory/project_phase57_157_scheduler_cross_burst.md |
| 57.158 | memory recall precision A/B — closes AD-Memory-Vector-Recall-Precision-AB; PR #372 | memory/project_phase57_158_memory_recall_precision_ab.md |
| 57.143 | user Stop→continue durable interrupt-resume — closes AD-UserStop-Resume-Context; PR #339 | memory/project_phase57_143_userstop_resume.md |
| 57.142 | OTel GenAI semantic-conventions span/attr mapping — closes AD-Observability-OTel-GenAI-Schema; PR #337 | memory/project_phase57_142_otel_genai_semconv.md |
| 57.141 | pass^k reliability eval harness — closes AD-Eval-PassK-Reliability-Harness; PR #335 | memory/project_phase57_141_passk_reliability.md |
| 57.138 | verification key-condition judge spike — closes AD-Verification-KeyCondition-PerTask | memory/project_phase57_138_verification_key_condition.md |
| 57.137 | sandbox detect→restrict spike — closes AD-Guardrail-Detect-To-Restrict; PR #327 | memory/project_phase57_137_sandbox_detect_to_restrict.md |
| 57.136 | verification correction-context hygiene spike — closes AD-Verification-Retry-Context-SelfConditioning; PR #325 | memory/project_phase57_136_verification_correction_hygiene.md |
| 57.135 | scheduled transcript-retention background job — PR #317 | memory/project_phase57_135_scheduled_transcript_retention.md |
| 57.134 | per-tenant transcript retention — PR #314 | memory/project_phase57_134_transcript_retention.md |
| 57.133 | chat-v2 Inspector Turn tab token-sweep — closes AD-ChatV2-Inspector-Turn-Metadata-Wire; PR #312 | memory/project_phase57_133_chatv2_inspector_token_sweep.md |
| 57.132 | chat-v2 resume-path ledger persistence — closes AD-ChatV2-Resume-Tool-RoundTrips; PR #310 | memory/project_phase57_132_chatv2_resume_ledger_persist.md |
| 57.131 | chat-v2 Inspector Turn tab `model` row — PR #309 | memory/project_phase57_131_chatv2_inspector_model_row.md |
| 57.130 | chat-v2 LoopTerminated wire surface — closes AD-LoopTerminated-Wire-Surface; PR #307 | memory/project_phase57_130_chatv2_loop_terminated_wire_surface.md |
| 57.129 | chat-v2 ledger intra-turn tool round-trips — closes AD-ChatV2-Ledger-Tool-RoundTrips; PR #305 | memory/project_phase57_129_chatv2_ledger_tool_roundtrips.md |
| 57.128 | chat-v2 resume transcript persistence — closes AD-ChatV2-Resume-Transcript-Persistence | memory/project_phase57_128_chatv2_resume_transcript_persistence.md |
| 57.127 | chat-v2 live multi-turn context — closes AD-ChatV2-Live-MultiTurn-Context; PR #303 | memory/project_phase57_127_chatv2_live_multiturn_context.md |
| 57.126 | chat-v2 session history replay — closes AD-ChatV2-Session-History-Replay-Phase58; PR #301 | memory/project_phase57_126_chatv2_session_history_replay.md |
| 57.125 | chat-v2 session history replay | memory/project_phase57_125_chatv2_session_transcript_persistence.md |
| 57.124 | HITL gate consolidation + 2 chrome/governance Potemkin fixes — closes AD-PermissionChecker-Shadow-Gate-Phase58 | memory/project_phase57_124_hitl_gate_consolidation.md |
| 57.122 | HITL policy read-side load-bearing — closes AD-HITL-Policy-ReadSide-Potemkin-Phase58 | memory/project_phase57_122_hitl_policy_readside.md |
| 57.121 | Skills slash-menu mockup + production re-point — closes AD-Skills-SlashMenu-Mockup | memory/project_phase57_121_skills_slash_menu_mockup.md |
| 57.120 | chat-v2 Inspector Turn tab `active_skill` row | memory/project_phase57_120_chatv2_inspector_active_skill.md |
| 57.119 | Skills system visibility + preview | memory/project_phase57_119_skills_system_visibility.md |
| 57.118 | Skills bundled scripts: system-bundled `run_skill_script | memory/project_phase57_118_skills_bundled_scripts.md |
| 57.117 | Skills catalog hardening: per-tenant quota + instructions body-size limit — closes AD-Skills-Per-Tenant-Quota | memory/project_phase57_117_skills_per_tenant_quota.md |
| 57.116 | Skills force-load Inspector affordance — closes AD-Skills-Inspector-Affordance | memory/project_phase57_116_skills_inspector_affordance.md |
| 57.115 | Skills slash-command `/skill-name` force-load — closes AD-Skills-Slash-Command | memory/project_phase57_115_skills_slash_command.md |
| 57.113 | Skills System epic OPENED | memory/project_phase57_113_skills_system_spike.md |
| 57.112 | IAM Block C MFA TOTP-only vertical | memory/project_phase57_112_iam_mfa_totp.md |
| 57.111 | A3 trace-aware critique + permanent cheap-judge benchmark | memory/project_phase57_111_trace_aware_critique_benchmark.md |
| 57.110 | B4 subagent child governance | memory/project_phase57_110_subagent_child_governance.md |
| 57.109 | C2 compaction cheap tier | memory/project_phase57_109_compaction_cheap_tier.md |
| 57.108 | UX slice: chat-v2 HITL card real tool/reason + Inspector turn metadata — closes AD-ChatV2-HITL-Card-Tool-Name | memory/project_phase57_108_chatv2_hitl_inspector_wire.md |
| 57.107 | B3 HANDOFF finish — closes AD-ChatV2-SessionList-Backend | memory/project_phase57_107_handoff_finish.md |
| 57.106 | C3 per-tenant harness policy + risky-action detector | memory/project_phase57_106_harness_policy.md |
| 57.105 | RBAC DB→JWT wiring | memory/project_phase57_105_rbac_jwt_wiring.md |
| 57.103 | B2b inject-to-teammate: backend primitive + US-5 | memory/project_phase57_103_inject_to_teammate.md |
| 57.102 | B2a TEAMMATE real multi-turn child loop | memory/project_phase57_102_teammate_multiturn.md |
| 57.101 | B1 between-turns injection primitive | memory/project_phase57_101_between_turns_injection.md |
| 57.100 | chat-v2 verification-reject UI | memory/project_phase57_100_chatv2_verification_reject_ui.md |
| 57.99 | A2 verification-ESCALATE | memory/project_phase57_99_verification_escalate.md |
| 57.98 | A1 verification-into-loop | memory/project_phase57_98_verification_in_loop.md |
| 57.97 | Multi-model profile | memory/project_phase57_97_multi_model_profile.md |
| 57.96 | Cat 11 Scope B child turn-stream nesting | memory/project_phase57_96_subagent_child_turnstream.md |
| 57.95 | Cat 11 — closes AD-Subagent-Child-Event-SSE-Relay | memory/project_phase57_95_subagent_sse_relay.md |
| 57.94 | Cat 11 FORK real child loop | memory/project_phase57_94_subagent_fork_child_loop.md |
| 57.93 | output-guardrail leg | memory/project_phase57_93_output_guardrail_pause.md |
| 57.92 | Slice 3 leg 2 | memory/project_phase57_92_between_turns_pause.md |
| 57.91 | Slice 3 leg 1 | memory/project_phase57_91_generalized_pause_input_escalate.md |
| 57.90 | AD-Resume-Continuation-Fidelity` CLOSED | memory/project_phase57_90_resume_reentrancy_slice_2.md |
| 57.89 | run() re-entrancy refactor | memory/project_phase57_89_run_loop_reentrancy.md |
| 57.88 | durable HITL pause-resume — closes AD-RateLimits-Alerting-Phase58 | memory/project_phase57_88_pause_resume.md |
| — | 35-page full Playwright sweep | (→ archive / MEMORY.md range pointer) |
| 57.87 | C-12 IAM Block B self-service tenant registration; closes AD-Auth-Register-Backend-IAM-Block-B-Phase58 — closes AD-Auth-Register-Backend-IAM-Block-B-Phase58 | memory/project_phase57_87_iam_registration.md |
| 57.86 | C-12 IAM Block B/C local credentials + password-login spike; closes AD-Auth-Credentials-PasswordLogin-Phase58 — closes AD-Auth-Credentials-PasswordLogin-Phase58 | memory/project_phase57_86_iam_credentials.md |
| 57.85 | C-12 IAM Block B invites vertical spike; closes AD-Auth-Invite-Backend-IAM-Block-B-Phase58 — closes AD-Auth-Invite-Backend-IAM-Block-B-Phase58 | memory/project_phase57_85_iam_invites.md |
| 57.83 | B-8 leg-2: general judge + real-LLM e2e + flip default; closes B-8 / AD-Cat10-Wire-1-Production | memory/project_phase57_83_verification_default_enable.md |
| 57.82 | B-8 leg-1: verification judge token — closes AD-Cat10-Judge-Cost-Ledger | memory/project_phase57_82_verification_judge_cost_ledger.md |
| 57.81 | B-7 ErrorBudget Redis wiring; closes B-7 / AD-ErrorBudget-Redis-Wiring | memory/project_phase57_81_errorbudget_redis_wiring.md |
| 57.80 | chat real_llm orphan-tool-message fix; closes AD-Chat-RealLLM-Orphan-Tool-Message — closes AD-Chat-RealLLM-Orphan-Tool-Message | memory/project_phase57_80_orphan_tool_adjacency.md |
| 57.79 | C-11 billing-correctness; closes AD-Cost-Ledger-Model-Pricing-Key-Mismatch + AD-Adapter-MaxTokens-NewModel-Param — closes AD-Cost-Ledger-Model-Pricing-Key-Mismatch | memory/project_phase57_79_c11_billing_correctness.md |
| 57.78 | Subagents Registry real list; closes AD-Subagent-RealList-Phase58 — closes AD-Subagent-RealList-Phase58; PR #243 | memory/project_phase57_78_subagents_registry_real_list.md |
| 57.77 | Memory ops-history frontend full-wire; closes AD-Memory-OpsHistory-Backend frontend half — closes AD-Memory-OpsHistory-Backend | memory/project_phase57_77_memory_ops_history_frontend.md |
| 57.76 | Memory ops-history backend; closes AD-Memory-OpsHistory-Backend backend half — closes AD-Memory-OpsHistory-Backend | memory/project_phase57_76_memory_ops_history_backend.md |
| 57.75 | chat-v2 Inspector Trace + Memory tabs full-chain; closes AD-ChatV2-Inspector-Trace-Phase2 + -Memory-Phase2 — closes AD-ChatV2-Inspector-Trace-Phase2 | memory/project_phase57_75_inspector_trace_memory.md |
| 57.74 | admin-tenants stats aggregate; closes AD-AdminTenants-Stats-Aggregate-Endpoint — closes AD-AdminTenants-Stats-Aggregate-Endpoint | memory/project_phase57_74_admin_tenants_stats.md |
| — | 本機 smoke 實跑；real-LLM 閉環 LIVE；cost-ledger row-count leg RESOLVED via restart，$ 值 gap 開放 | (→ archive / MEMORY.md range pointer) |
| 57.84 | C-15 billing-write-atomicity leg CLOSED + sub-items deferred (2026-06-06 | memory/project_phase57_84_billing_outbox.md |
| — | Area-A 教訓固化副產物 | (→ archive / MEMORY.md range pointer) |
| 57.62 | RateLimits Alerting; durable 80%-threshold alert log captured even when unwatched; Phase 58.x RateLimits arc + alert | memory/project_phase57_62_rate_limits_alerting.md |
| 57.61 | RateLimits SyntaxValidation; PUT-time 422 replaces silent drop; Phase 58.x RateLimits arc write-path fail-loud | memory/project_phase57_61_rate_limits_syntax_validation.md |
| 57.60 | RateLimits MetaData Cleanup; config single-source; Phase 58.x RateLimits arc config-complete | memory/project_phase57_60_rate_limits_metadata_cleanup.md |
| 57.59 | RateLimits Potemkin Migration C1 two-table split; Phase 58.x deeper extensions 2/5; AP-4 CLOSED | memory/project_phase57_59_rate_limits_potemkin_migration.md |
| 57.58 | RateLimits RuntimeEnforcement D3 Full; Phase 58.x deeper extensions 1/5; AP-4 Potemkin caught Day 0 | memory/project_phase57_58_rate_limits_runtime_enforcement.md |
| 57.57 | RateLimits WRITE-side ship; Phase 58.x portfolio FINAL 4/4 CLOSURE 🎉; tier-4 SPLIT FULLY VALIDATED | memory/project_phase57_57_rate_limits_write_endpoint.md |
| 57.56 | Quotas WRITE-side ship; Phase 58.x portfolio 3/4; tier-4 1st validation CONFIRMED CLEANLY | memory/project_phase57_56_quotas_write_endpoint.md |
| 57.55 | FeatureFlags WRITE-side ship; Phase 58.x portfolio 2/4; tier-4 SPLIT ACTIVATED | (→ archive / MEMORY.md range pointer) |
| 57.54 | HITLPolicies WRITE-side ship; Phase 58.x portfolio item; tier-3 `mechanical-greenfield` 0.50 1st validation | memory/project_phase57_54_hitl_policies_write_endpoint.md |
| 57.53 | Checkpointer Test Tenant Isolation Pre-Existing Fail FIX; Sprint 57.12 `§Committed-Row Cleanup Pattern` Lift | memory/project_phase57_53_checkpointer_tenant_isolation_fix.md |
| 57.52 | Triple-AD Audit/Docs Hygiene Bundle Continuation; Tier-3 `mixed-multidomain-bundle` SPLIT ACTIVATED | memory/project_phase57_52_audit_docs_hygiene_continuation.md |
| 57.51 | Triple-AD Audit/Docs Hygiene Bundle; Tier-2 `mixed-multidomain-bundle` 0.65 1st Validation — PR #200 | memory/project_phase57_51_audit_docs_hygiene_bundle.md |
| 57.50 | TenantSettings Identity Fixture Cleanup; Option B Tier-2 ESCALATION | memory/project_phase57_50_tenant_settings_identity_fixture_cleanup.md |
| 57.43 | Phase-2 Epic DUAL CLEAN + Phase 58+ Backend Schema Extension + Frontend Migration Wave — PR #195 | memory/project_phase57_43_admin_tenants_rebuild.md |
| 57.42 | /memory Memory Layers Matrix Full Mockup-Fidelity Rebuild | memory/project_phase57_42_memory_matrix_rebuild.md |
| 57.41 | /verification recent view Full Mockup-Fidelity Rebuild | memory/project_phase57_41_verification_full_rebuild.md |
| 57.40 | /governance Approvals view Full Mockup-Fidelity Rebuild | memory/project_phase57_40_governance_full_rebuild.md |
| 57.39 | Governance Category Multi-Page Phase-2 4-domain batched | memory/project_phase57_39_governance_multipage_phase2.md |
| 57.38 | 3 user-reported issues — PR #176 | memory/project_phase57_38_followup_3_user_reported_issues.md |
| 57.38 | 3-domain batched: class-split decision + /subagents re-point + fullbleed audit | memory/project_phase57_38_followup_3_user_reported_issues.md |
| 57.37 | 2-domain batched: /loop-debug full rebuild + /state-inspector Phase-2 | memory/project_phase57_37_loop_debug_fixture_state_inspector.md |
| 57.36 | /loop-debug Phase-2 | memory/project_phase57_36_loop_debug_repoint.md |
| 57.35 | AuthShell + 7 auth routes Phase-2 | memory/project_phase57_35_auth_repoint.md |
| 57.34 | /orchestrator Phase-2 | memory/project_phase57_34_orchestrator_repoint.md |
| 57.33 | Page Bug Fix Sweep | memory/project_phase57_33_page_bug_fix_sweep.md |
| 57.32 | /sla-dashboard Phase-2 | memory/project_phase57_32_sla_dashboard_repoint.md |
| 57.31 | /cost-dashboard Phase-2 | memory/project_phase57_31_cost_dashboard_repoint.md |
| 57.30 | chat-v2 Phase-2 + shell hotfix; AD-Sprint-Plan-frontend-verbatim-bimodal-watch CLOSED in 57.31 | memory/project_phase57_30_chatv2_shell_repoint.md |
| 57.29 | Phase-2 per-page re-point opens; partially closed in 57.30 | memory/project_phase57_29_overview_shell_repoint.md |

---

## 🌱 Open Carryover ADs (raw per-sprint seeds)

> Un-curated AD seeds lifted verbatim from each sprint's closeout `NEW carryover` / `Still-open` lists. **Some may since have been closed** (any `✅ CLOSED` / strike-through markers are preserved verbatim — trust the marker). Full context per AD → the archive block + the sprint's memory subfile. For the curated, prioritized candidate list see §Top Candidates (#1–#46) below.

#### 57.161
**NEW carryover** `AD-Compaction-Structural-TombstoneCount-Marker` (mirror preclear's tombstoned count into `StructuralCompactor.messages_compacted` so the marker shows `· N msgs` on pure tombstone instead of `· 0 msgs`) + per-tenant real-count toggle (C3 seam). CHANGE-128 + design note `63-structural-realcount-design.md`. Detail: `memory/project_phase57_161_structural_realcount.md`.

#### 57.156
**NEW carryover**: ~~`AD-TaskPrimitive-Scheduler-Phase58`~~ ✅ **CLOSED Sprint 57.157** · ~~`AD-TaskPrimitive-DAG-Enforce-Phase58`~~ ✅ **CLOSED Sprint 57.162** (SOFT — advisory not reject, AskUserQuestion pick) · ~~`AD-TaskPrimitive-DAG-CycleReport-Phase58`~~ ✅ **CLOSED Sprint 57.162** (`detect_cycles` → observation advisory + `render_active_plan` `(blocked by cycle: …)`) · ~~`AD-TaskPrimitive-DAG-Viz-Phase58`~~ ✅ **CLOSED Sprint 57.162** (Inspector `TodoDagGraph` leveled node-link). All 4 57.156 DAG carryovers now closed (57.162 committed LOCAL, PR-pending — not pushed per user 完成即暫停). Detail: `memory/project_phase57_156_dag_task_primitive.md` + `memory/project_phase57_162_dag_enforce_cyclereport_viz.md`.

#### 57.157
**NEW carryover**: `AD-Scheduler-Burst-Stats-Aggregate-Phase58` (final `loop_end` reflects only the last burst's counters, not the cross-burst total) · `AD-Scheduler-Burst-Boundary-Wire-Phase58` (no wire event marks a burst boundary; a FE burst counter would need one) · `AD-Scheduler-PerTenant-Phase58` (global env, not per-tenant policy — deliberate anti-AP-6) · `AD-Scheduler-TokenBudget-Continue-Phase58` (only `max_turns` continues; `token_budget` conservatively stops) · `AD-TaskPrimitive-DAG-Enforce-Phase58` (still open — DAG + scheduler both remain guidance).

#### 57.158
**NEW carryover**: `AD-Memory-Vector-Recall-Adversarial-Corpus` (the corpus is discriminating but NON-adversarial — single clear gold per case, no semantic distractors / ambiguous multi-topic queries; a harder corpus would stress precision@k; the recall@k win is robust). **Now evidence-backed (were gated on this A/B)**: `AD-Memory-Semantic-Axis-System-Tenant-Layers` · `AD-Memory-Vector-Incremental-Write` · `AD-Memory-Semantic-NearDup-Dedup` · `AD-Memory-Session-Summary-Semantic-Rank`.

#### 57.143
**Carryover (Phase 58)**:
- **`AD-Loop-CancelEvent-Poll-Phase58`** — make the loop poll `cancel_event` (`session_registry.py:127`, currently set-but-never-polled) for a graceful in-process stop + in-flight LLM cancel (today the FE abort tears the run down; the marker covers transcript coherence).
- partial assistant-answer streaming capture on abort; `message_events` (57.125/126 replay ledger) disconnect durability; leading-assistant-marker guard for the sub-second Stop-before-turn-0 race (Azure lenient today).

#### 🆕 Drive-Through Audit Carryover (2026-06-06 — 35-page full P
- **`AD-SLA-Report-Endpoint-500`** (✅ **RESOLVED 2026-06-07 — FIX-028**) — was: `GET /api/v1/admin/tenants/{tid}/sla-report → HTTP 500`; /sla-dashboard "Failed to load data". Root cause = AP-4 wired-but-never-activated (twin of FIX-022): `set_sla_recorder()` only ever called in 2 test files, never in `backend/src`, so `main.py` lifespan never wired the recorder → strict `get_sla_recorder()` raised `RuntimeError` on the cache-miss generate path → 500 (tests masked it by injecting their own recorder; chat router uses lenient `maybe_get_sla_recorder()` so it silently no-op'd). Fix: add `_wire_sla_recorder()` to `main.py` lifespan (mirror `_wire_error_budget`, fail-open) + regression test `test_lifespan_wires_sla_recorder`. Drive-through verified: sla-report → **200**; /sla-dashboard renders (`shots/21-sla-dashboard-after-FIX-028.png`). Detail: `claudedocs/4-changes/bug-fixes/FIX-028-sla-recorder-unwired-500.md`.
  - **`AD-SLA-Report-CrossTenant-RLS-Check`** (🟡 follow-on, NEW) — FIX-028 drive-through covered same-tenant only; verify the on-demand generate path's `SLAReport`/`SLAViolation` INSERT under RLS when a platform_admin views a tenant **other than** their own JWT tenant.
  - **`AD-SLA-Report-Endpoint-Degrade-Lenient`** (🟢 follow-on, NEW) — consider making the report endpoint degrade (503/empty) like the chat router rather than 500ing if the recorder is ever unwired (Redis down at startup → fail-open leaves singleton None → endpoint still strict-fails).
- **`AD-Orchestrator-Page-Potemkin`** (✅ **RESOLVED 2026-06-07 — FIX-029**) — was: /orchestrator entire surface (4 KPIs + 6 config tabs + Test/View-repo/Deploy actions) hardcoded fixture with NO fixture note + dead action buttons; the LONE unlabeled Potemkin among 15 full-impl pages. Fix (honest-label, not wire-backend — no orchestrator config/deploy backend exists): added one page-level `BackendGapBanner` above the tabs (the same canonical AP-2 marker every other fixture page uses; mockup widgets/buttons kept visually faithful, banner is additive). Drive-through verified: banner renders above tabs, declares settings non-persisted + actions non-functional (`shots/22-orchestrator-after-FIX-029.png`). Detail: `claudedocs/4-changes/bug-fixes/FIX-029-orchestrator-page-potemkin.md`.
  - **`AD-Orchestrator-Config-Backend`** (🟡 follow-on, NEW — Phase 58+) — wire a real orchestrator config + deploy backend (agent config CRUD + deploy pipeline) so the 6 config tabs persist + Test/Deploy actions function; then drop the BackendGapBanner. Whole new feature, deliberately out of FIX-029 scope.
- **`AD-DriveThrough-Phase58-Endpoints-Reverify`** (✅ **RESOLVED 2026-06-07**) — was: stale backend (PID 15056 + orphaned `--reload` spawn-workers, Risk Class E) made register/invite/password-login 404/401. After a clean restart (kill all 3 uvicorn procs + `dev.py start`), re-verified ALL PASS: register full wizard → **201 + DB write + slug-unique 409**; password-login bad creds → **401 generic invalid**; invite fake token → **404 invalid**. **No code bug — 100% stale-process artifact.** Recommend separate git worktree per session to avoid recurrence (two-sessions-one-worktree). Detail: audit.md §8.
- **`AD-Register-Concurrent-Slug-Race`** (✅ **RESOLVED 2026-06-07 — FIX-030**) — audit suspected the double POST created 2 same-slug tenants; **investigation corrected this**: `tenants.code` already has `unique=True`, so dups are impossible. Empirical concurrent probe: two same-slug registrations → **201 + 500** (not 2×201, not a dup) — the 2nd hit an unhandled `IntegrityError`. Real bug = raw 500 instead of clean 409 (affects prod too: two people racing for the same workspace URL). Fix: wrap the tenant INSERT flush in `try/except IntegrityError → TenantSlugTakenError` (409); no migration. Drive-through verified: concurrent → **201 + 409**. Detail: `claudedocs/4-changes/bug-fixes/FIX-030-drive-through-minor-bundle.md` Item C.
- **`AD-Overview-TopKPI-Fixture-Label`** (✅ **RESOLVED 2026-06-07 — FIX-030**) — /overview top-4 KPI cards were unlabeled fixture ($2,847 MTD contradicts real cost_ledger). Fix: added one `BackendGapBanner` under the KPI row (the 5 widgets below already had theirs) + `overview.kpiBackendGap` i18n (en/zh-TW); mockup-faithful (values kept, banner additive). Drive-through verified: 6 banners now, KPI banner renders (`shots/23-overview-kpi-banner-FIX-030.png`). Follow-on: **`AD-Overview-TopKPI-Backend`** (🟡 Phase 58+) — wire real KPI aggregation then drop the banner.
- **`AD-ChatV2-Inspector-Turn-Metadata-Wire`** (🟡 wiring — STILL OPEN, deferred from FIX-030 bundle) — NOT a minor label fix: `InspectorTurn` is already HONEST (renders "—" for unwired fields, not fake values), so it's not a Potemkin. Wiring needs store + backend-SSE work: `trace_id` IS on every SSE frame (cheap to map) + `span_id` is on span events (store already tracks `spans`), BUT `tokens_out` / `cost` are NOT in the SSE stream (cost is written server-side to cost_ledger only) → emitting them needs a backend `event_wire_schema` change. Scoped wiring task for a dedicated slice (frontend store + backend SSE).
- **`AD-AdminTenants-ListHeader-Fixture-String`** (✅ **RESOLVED 2026-06-07 — FIX-030**) — /admin-tenants "All tenants" subtitle was hardcoded `"48 active · 3 anomalies in last 24h"`. Fix: derive from real loaded rows — `` `${tenants.length} tenants` `` (table already real-data); dropped the fixture string + deleted orphan `_fixtures.ts` + its obsolete single-assertion test (coverage moved to `TenantsTable.test.tsx`). Drive-through verified: subtitle shows **"50 tenants"** (real count), "48 active" gone (`shots/24-admin-tenants-real-subtitle-FIX-030.png`).

#### 57.87
- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** (NEW) — the seeded admin `UserRole` is DB-real but NOT yet authz-effective: gating reads the JWT `roles` claim and the OIDC callback bakes `roles=["user"]` (`auth.py:302`). Make the DB role grant JWT admin (per-request RBACManager load or a register-issued elevated JWT). The system-wide `has_permission()`-is-stub gap (gap-assessment §6) lives here too.
- **`AD-Register-OIDC-User-Linkage-Phase58`** (NEW) — register creates the user by `email` (no `external_id`); the OIDC callback upserts by `(tenant_id, external_id)` → a later login creates a SECOND user row. Fix: callback link-by-email OR register OIDC-initiated.
- **`AD-Tenant-Plan-Tiers-Phase58`** (NEW) — `TenantPlan` only has ENTERPRISE; the wizard's trial/pro/enterprise choice is stored in `meta_data` only. Real BASIC/STANDARD/trial tiers + quota enforcement are Phase 56+ Stage 2.
- **Process (single occurrence — fold into `sprint-workflow.md` only if recurs)**: a concurrent Claude session sharing the repo working directory switched the branch mid-sprint (to `chore/drive-through-acceptance-principle`), stranding uncommitted Day-3 edits + hiding `registration.py` → a phantom mypy `import-untyped` first mis-chased as editable-install staleness. Diagnostic lesson: when a first-party import reads "installed missing py.typed" + the mypy source-file count doesn't increment → check `git branch` FIRST. Root cause = two-sessions-one-worktree (recommend separate git worktrees/clones per session); not a workflow gap.
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn; `/auth/mfa` still stub 501.
- **`AD-Auth-Recovery-Page-Phase58`** — password reset/recovery; needs an email adapter (none exists); `/auth/recovery` does not exist.
- **`AD-Auth-PasswordLogin-Lockout-Phase58`** — brute-force throttle on `/auth/password-login` (+ register-spam throttle); reuse the Redis rate-limit infra.
- **Calibration — `iam-backend-spike` 0.65 1st validation**: ratio ≈1.0 core (≈1.1-1.2 incl. the branch-collision anomaly) → KEEP single data point; flag the next IAM backend spike (MFA/recovery) for the 2nd validation per the 3-sprint window.
---

#### 57.86
- **`AD-Auth-Register-Backend-IAM-Block-B-Phase58`** — self-service tenant registration (POST /tenants/register: create tenant + first admin user + password; reuses `passwords.py` + `CredentialsService.set_password`). The register page is still fixture/501.
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn (password-login lands the user via `consumePostLoginRedirect()`; `/auth/mfa` still stub 501).
- **`AD-Auth-PasswordLogin-Lockout-Phase58`** (NEW) — brute-force / lockout throttle on `/auth/password-login` (no per-tenant login-attempt counter this spike; bcrypt cost=12 + generic-401 raise per-guess cost but no rate limit). Candidate substrate: the Redis rate-limit-counter infra (57.48/57.58).
- **Password-strength policy** — invite-accept keeps `min_length=1`; password fields gain only `max_length=72` (bcrypt safety). Min length / complexity / breach-check is a follow-up.
- **`AD-Auth-Recovery-Page-Phase58`** — password reset / recovery; `/auth/recovery` does not exist.
- **Login-page discoverability link** — the OIDC `/auth/login` page does NOT link to `/auth/password-login` (kept pristine per mockup); the page is reachable by direct route + is its own consumer. A mockup-gated link is a follow-up.
- **Calibration — `AD-Sprint-Plan-IAM-Backend-Spike-Class`** (NEW): `medium-backend` 0.80 ran ratio ~1.15-1.2 (greenfield-IAM over-run) — **2nd consecutive** greenfield-IAM over-run (57.85 ~1.25 + 57.86 ~1.15-1.2). Propose a `iam-backend-spike` class (~0.65) for the next IAM backend spike (register/MFA); adopt in that sprint's plan, do NOT pre-create.
---

#### 57.85
- **`AD-Auth-Credentials-PasswordLogin-Phase58`** (NEW, next obvious = 57.86) — local-password credentials table + bcrypt + a tenant-scoped password-login endpoint. The accept's `password` is accepted-not-stored until then; the created user authenticates via OIDC/dev-login. (Login-page UI wiring further gated by mockup-fidelity — mockup login has no password field.)
- **`AD-Auth-Register-Backend-IAM-Block-B-Phase58`** — self-service tenant registration (POST /tenants/register: create tenant + first admin user).
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn (accept navigates to `/auth/mfa`, still stub 501).
- **Invite email delivery** — no email facility exists; create returns the raw token in-response. Phase-58 follow-up (e.g. SMTP/SES adapter).
- **Admin invites-list / resend UI** — `revoke` service method exists (US-4 revocable); a full management surface (list pending / resend / revoke UI) is a follow-up.
- **Calibration**: `medium-backend` 0.80 greenfield-IAM data point ran ratio ~1.25 (over-band, as the plan flagged). Single outlier (ignored for the multiplier); if 57.86 (also greenfield IAM) confirms > 1.0 → propose a new `iam-backend-spike` class (~0.55-0.65). Track in `sprint-workflow.md §Scope-class matrix` if it recurs.
- **Process** (single data point, fold into `sprint-workflow.md` only if recurs): a Day-0 check — "if the test DB role is superuser, RLS-block is untestable → plan an application-layer isolation assertion" (D5 cost one isolation-test rewrite).

#### 57.83
- **Monitor production verification_failed rate post-flip** — 0% FP is from an 8-prompt sample; watch real-traffic FP + correction rate (verification_log + `_verification` ledger give the data). Re-tune `output_quality` if FP creeps up.
- **Per-verifier cost attribution** (leg-1 carryover) — still one `_verification` sub_type.
- **Multi-judge registry** (safety + quality on the main path) — shipped one general quality judge; layering safety/PII is a separate decision.
- Remaining billing bundle: **C-15** (DevOps/data-platform billing — cost_ledger 雙扣 risk).
---

#### 57.82
- ✅ **leg 1 (57.82)**: blocker A — judge token → cost ledger + quota.
- ⏳ **leg 2 (57.83, plan written at 57.83 kickoff — rolling)**: blocker B (design a general final-output judge template replacing the Cat 9-fitted `safety_review` default + measure false-positive rate) + blocker C (real-LLM e2e: false-positive / p95 latency / per-chat cost) + **flip `chat_verification_mode` → `enabled`**. B+C bundled (B's FP eval needs C's real-LLM). Needs real Azure (live since 57.79).
- **Per-verifier cost attribution** — leg 1 aggregates all judge tokens into ONE `_verification` sub_type; a per-verifier breakdown is deferred.
- **Drift D3 (sse server-side decision)** — verification tokens are NOT on the SSE wire (consistent with loop input/output_tokens being server-side only; router reads the event object). If a future UI needs to show judge cost, add the LoopCompleted serializer fields + frontend codegen then.
- No blocking carryover. Remaining billing bundle: **C-15** (DevOps/data-platform billing — cost_ledger 雙扣 risk).
---

#### 57.81
- **error_budgets.yaml per-tenant overrides** — `budget.py` docstring mentions YAML-tunable caps; the factory uses defaults (1000/day, 20000/month). Loading per-tenant overrides is a separate feature (not wiring). Candidate.
- **Day-0 export check (rule candidate)** — when wiring an already-built component, add a one-line Day-0 check that it's EXPORTED on the public import path (D1 this sprint: RedisBudgetStore was not exported; 30-sec find vs a Day-1 import error). Fold into `sprint-workflow.md §Step 2.5` if it recurs.
- No blocking carryover. Remaining bundle: **B-8** (Verification default-enable) / **C-15** (DevOps/data-platform billing).
---

#### 57.80
- **Candidate rule fold-in (not yet codified)** — Cat 5 / message-assembly tests must assert the provider structural invariant (tool-call adjacency / ordering) directly, not rely on the mock to reject; and a real-LLM DoD for agent-loop prompt changes should check `stop_reason=end_turn` (convergence), not just no-400 / loop_end present. (Single-data-point; fold into `sprint-workflow.md` if a 2nd sprint hits the same gap.)
- No blocking carryover. Unrelated bundle remains: ~~**B-7** (ErrorBudget Redis wiring)~~ ✅ CLOSED Sprint 57.81 / **B-8** (Verification default-enable) / **C-15** (DevOps/data-platform billing).
---

#### 57.79
- **`AD-Chat-RealLLM-Orphan-Tool-Message`** — ✅ **CLOSED Sprint 57.80 (FIX-027)**. Root cause = `LostInMiddleStrategy.arrange()` moved recent assistant to the tail while the tool result stayed in mid_history → tool preceded its assistant. Fixed builder-level (`_enforce_tool_adjacency` after `strategy.arrange()`, fix B) + pending-tool-turn user re-anchor suppression (fix C, for convergence). Real Azure verified: 200 + `stop_reason=end_turn`. Detail: `memory/project_phase57_80_orphan_tool_adjacency.md`. ~~chat router real_llm e2e blocked by a pre-existing, UNRELATED message-structure 400; needs separate investigation into the real_llm prompt assembly.~~
- **Deployment requirement: `AZURE_OPENAI_MODEL_NAME`** — prod/other envs using a gpt-5.x deployment MUST set this to the real generation (e.g. `gpt-5.2`). Config default is `gpt-4o` (stale); if unaligned, Gap 2 mis-branches to `max_tokens` → 400 on gpt-5.x. (Gap 1 unaffected — uses response.model.) Deployment/ops note, not a code item.
- ~~B-7 ErrorBudget Redis wiring~~ ✅ CLOSED Sprint 57.81 / B-8 Verification default-enable / C-15 DevOps-data-platform billing — the billing-correctness bundle's remaining legs.
- Auto-sync pricing from provider API (`llm_pricing.yml:3` future idea) — stays manual yaml.
---

#### 57.78
- **`AD-Subagent-Invocations-Persistence-Phase58`** — the runtime per-spawn timeline (the heavy path NOT chosen): NEW SubagentInvocation ORM + dispatcher persist hook + read-side projection. Re-log if a real invocations timeline is later wanted.
- **agent_catalog tenant-facing write from /subagents** — Sync-from-repo / New-subagent buttons stay AP-2 stubs (admin CRUD at `/admin/tenants/{id}/agents`).
- **budget/tools loop enforcement** — stored not enforced (57.70 §9).
- **Usage-metrics backing** (calls24h/p95/success/avg-tokens/top-orchestrator) — needs runtime invocation telemetry; honest-gapped this sprint.

#### 57.77
- ✅ #1+#2 Inspector Trace + Memory (57.75) · #3 admin-tenants stats (57.74)
- ✅ `AD-Memory-OpsHistory-Backend` **fully closed** (backend 57.76 + frontend 57.77)
- ⏳ **FE `/subagents` real list (`AD-Subagent-RealList-Phase58`) — THE LAST Area-A remaining item** (agent_catalog specs exist; needs tenant-facing GET + FE re-mount, like 57.73)
- (A-4 Tier 2 real Jaeger export = EXCLUDED per user program → Area-C/DevOps)
- **READ-path ops** — write/evict only (57.76 backend); sampled reads a future option (row-volume tradeoff).
- **role/session/system layer ops** — those layers raise / in-memory (57.76); not recorded → never appear in RecentOps/marks.
- **Point-in-time state reconstruction** — scrub = ops-browsing (filter visible ops by time); replaying snapshots to rebuild memory state at an arbitrary timestamp is deeper future work.
- **Server-side ops time-window scrub** — current filters client-side from a single 50-row page; `before` cursor wired in `fetchOps` but pagination-only. Deep-history scrub needs server-side windowed fetch.

#### 57.76
- ✅ #1+#2 Inspector Trace + Memory (57.75)
- 🔶 `AD-Memory-OpsHistory-Backend` backend done (57.76); frontend → 57.77
- ⏳ FE `/subagents` real list (`AD-Subagent-RealList-Phase58`) — last item (agent_catalog specs exist; needs tenant-facing GET + FE re-mount, like 57.73)
- **READ-path emit** — write/evict only this sprint; sampled reads a future option (row-volume tradeoff)
- **role/session/system layer ops** — role/system raise (admin-managed/read-only); session in-memory volatile; emittable if they gain live DB write paths
- **Full point-in-time state reconstruction** — this sprint = time-ordered ops log (sufficient for RecentOps + TimeTravel marks); replaying snapshots to rebuild memory state at an arbitrary timestamp is deeper future work

#### 57.75
- ✅ #1+#2 Inspector Trace + Memory tabs (THIS sprint)
- ⏳ `AD-Memory-OpsHistory-Backend` — persisted memory ops-history (distinct from this sprint's live-session SSE Memory tab; needs audit-emit or `memory_ops` table — Day-0 design decision)
- ⏳ FE `/subagents` real list (`AD-Subagent-RealList-Phase58`)
- **subagent-boundary spans** — cross-process `parent_span_id` so a subagent's spans nest under the parent loop's TURN in the Trace waterfall (this sprint is single-loop only)
- **memory write/evict emit** — Memory tab shows read-on-build only; write/evict happen inside tools (under TOOL_EXEC span); emit if the tab needs the full op set

#### 57.62
1. **`AD-RateLimits-Alerting-Webhook`** (NEW) — push 80%/100% breaches to a tenant-configured webhook / Slack (the persisted log is the substrate); ~3-4 hr.
2. **`AD-RateLimits-Alerting-Ack-Mute`** (NEW) — admin ack / mute / resolve on an alert row (add `resolved_at` like `SLAViolation`) + filter resolved from the Recent alerts card; ~2 hr.
3. **`AD-Quotas-Alerting-Template`** (NEW) — the 57.62 pattern (write-through detection → idempotent alert upsert → GET → polling card) reused for Quotas usage alerts (the Quotas usage card exists from 57.56); ~3 hr.
4. **`AD-RateLimits-DuplicateResource-Validation`** (CONTINUES — 57.61 R7) — PUT-time 422 on two payload items resolving to the same (resource_type, window_type); currently silent last-wins dedup; ~1 hr.
5. **`AD-RateLimits-SyntaxValidation-ClientSide-Polish`** (CONTINUES — 57.61 R5) — mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting; risks a 5th parser copy; ~2 hr.
6. **`AD-RateLimits-Parser-Extract-Shared-Predicate`** (CONTINUES — 57.61 R3) — extract the window-alias table to ONE source the counter + store reference; ~2-3 hr.

#### 57.61
1. **`AD-RateLimits-Alerting-Phase58`** (CARRYOVER) — SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr.
2. **`AD-RateLimits-DuplicateResource-Validation`** (NEW — R7 deferred) — PUT-time 422 on two payload items resolving to the same (resource_type, window_type); currently silent last-wins dedup; ~1 hr.
3. **`AD-RateLimits-SyntaxValidation-ClientSide-Polish`** (NEW — R5 deferred) — mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting; risks a 5th parser copy (weigh carefully); ~2 hr.
4. **`AD-RateLimits-Parser-Extract-Shared-Predicate`** (NEW — R3 follow-on) — extract the window-alias table to ONE source the counter + store reference (migration stays dep-light inline); removes the 2-live-copy smell the US-2 guard currently watches; ~2-3 hr.

#### 57.60
1. **`AD-RateLimits-SyntaxValidation-Phase58`** (CARRYOVER) — now easier post-split (config table has typed `quota`/`window_type` columns); PUT-time validation rejecting malformed `value` strings before they reach the table; ~2-3 hr.
2. **`AD-RateLimits-Alerting-Phase58`** (CARRYOVER) — SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr.

#### 57.59
1. **`AD-RateLimits-MetaData-Cleanup-Phase58`** (NEW — after 1-2 sprints validating table path stable → remove `meta_data["rate_limits"]` read-fallback + transitional dual-write + clear stored JSONB via data migration; ~1-2 hr)
2. **`AD-Day0-Prong3-Physical-Column-Read`** (NEW — Q3 Lesson: D-DAY1-1 tenants JSONB physical column is `metadata` not ORM attr `meta_data`; codify Prong 3 "read physical column names + full schema, not ORM attr names"; combine with Sprint 57.58 `AD-Day0-Prong2-Nested-Shape-Read` — both "read the body, not the name"; codify when 2 data points)
3. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.60`** (NEW — 1st validation under tightened 0.45; 57.58=0.49 + 57.59=0.34 → 2 consec < 0.7 → tightened 0.65→0.45; if 57.60 also < 0.7 → escalate 0.30 / fold into `mechanical-pattern-reuse-heavy` 0.30)
- **`AD-RateLimits-MetaData-Cleanup-Phase58`** (above — natural follow-on; small)
- **`AD-RateLimits-SyntaxValidation-Phase58`** (now easier post-split: config table has typed `quota`/`window_type` columns; PUT-time validation)
- **`AD-RateLimits-Alerting-Phase58`** (SSE 80% threshold; pairs with the activated usage table)
---

#### 57.58
1. **`AD-RateLimits-Potemkin-Migration-Phase58`** (NEW — Day 0 D-DAY0-CRITICAL: `RateLimit` ORM `api_keys.py:141` table `rate_limits` dormant since Phase 49 V2 baseline, NEVER wired = AP-4 Potemkin. Sprint 57.59+ ~5-8 hr: activate ORM as persistence layer OR formally delete. Folds in CONDITIONAL `AD-RateLimits-DedicatedTable-Phase58` — same table.)
2. **`AD-Day0-Prong2-Nested-Shape-Read`** (NEW — Q3 Lesson 1: D-DAY1-1 stored shape was `{label,value}` UI strings not `{resource,window,limit}`; Prong 2 grep matched the key but not nested dict shape. Codify "when plan asserts `X["key"] = {a,b,c}`, Day 0 Prong 2 reads the Pydantic/serializer body not just greps the key" into `sprint-workflow.md §Step 2.5 Prong 2` when 2-3 data points accumulate.)
3. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Validation-Sprint-57.59`** (NEW — 2nd validation of `mixed-multidomain-bundle-mechanical` 0.65 tier-3; Sprint 57.58 1st = ~0.49 BELOW band single-data-point caution KEEP; if 2nd also < 0.7 tighten 0.45, if > 1.20 rollback 1.0.)
- **`AD-RateLimits-SyntaxValidation-Phase58`** (PUT-time parse `"100 / min"` → structured; ~2 hr port-style)
- **`AD-RateLimits-Alerting-Phase58`** (per-rule SSE/webhook alert when threshold crossed; pairs with the Live usage Card shipped this sprint)
- **`AD-RateLimits-Potemkin-Migration-Phase58`** (above — natural follow-on closing the AP-4 surfaced this sprint)
---

#### 57.57
1. **`AD-RateLimits-SyntaxValidation-Phase58`** (NEW — parse "100 / min" into structured `{limit: int, unit: "request", period: "minute"}` shape; currently raw display strings)
2. **`AD-RateLimits-RuntimeEnforcement-Phase58`** (NEW — currently `tenant.meta_data["rate_limits"]` is admin display only; no runtime enforcement; needs runtime middleware reading the override list)
3. **`AD-RateLimits-LiveUsageTracking-Phase58`** (NEW — analogous to `AD-Quotas-LiveUsageTracking-Phase58`; per-rule live usage counter exposure)
4. **`AD-RateLimits-Alerting-Phase58`** (NEW — per-rule alerting thresholds + notification webhook)
5. **`AD-RateLimits-DedicatedTable-Phase58`** (NEW CONDITIONAL — Sprint 57.48 D-DAY0-5 noted; Phase 58+ option if persistence requirements grow beyond JSONB)
Optional additional (not from Sprint 57.57 ship; reclassified from Sprint 57.56 close — informational):
- **`AD-RateLimits-OptimisticConcurrency`** (NEW CONDITIONAL — Phase 58+ If-Match header pattern if concurrent edit race conditions surface)
- **`AD-AgentFactor-Tier-4-Validation-Sprint-57.58`** (NEW CONDITIONAL — IF Sprint 57.58 chooses agent-delegated sprint under tier-4 `-design-decisions` 0.65, generates 3rd validation data point; tier-4 SPLIT now FULLY VALIDATED with 2-consec IN band so this carryover is informational tracking — NOT blocking for any user direction)

#### 57.56
1. **`AD-AgentFactor-Tier-4-Validation-Sprint-57.57`** (NEW priority — 2nd validation needed under tier-4 `mechanical-greenfield-design-decisions` 0.65 for rollback rule baseline; Sprint 57.57 RateLimits WRITE = natural candidate; same architectural simplification as Sprint 57.56)
2. **`AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`** PROMOTION-CANDIDATE (Sprint 57.53+57.54+57.55+57.56 = 4-data-point evidence reached; per AD-Plan-2/3/4/5 promotion precedent 3-data-point sufficient; promote to MANDATORY field in `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies`)
3. **`AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** PROMOTION-CANDIDATE (Sprint 57.55 + 57.56 = 2 mid-plan-draft pivots in 2 sprints; 3-data-point evidence across Sprint 57.54+57.55+57.56 reached; promote to NEW Drift Class row in `sprint-workflow.md §Step 2.5 Prong 2 Drift Class table`)

#### 57.55
1. **`AD-AgentFactor-Tier-4-Validation-Sprint-57.56`** (NEW — 1st validation needed under tier-4 `mechanical-greenfield-design-decisions` 0.65 baseline; Sprint 57.56 Quotas WRITE candidate)
2. **`AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** (Lesson 1 codification — extend sprint-workflow.md §Step 2.5 Prong 2 Drift Class table with Phase 58.x WRITE-side resource storage architecture identification row)
3. **`AD-Day0-Prong2-CanonicalService-Grep`** (Lesson 2 codification — extend Phase 58.x WRITE-side pattern template with canonical service grep step BEFORE plan §4)

#### 57.53
**CLOSED**:
- ✅ `AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` (Sprint 57.51+57.52 trail carryover; root-cause investigated; fix applied; pytest baseline restored to 1760 PASS + 0 fail)
**NEW carryover**:
- **`AD-AgentFactor-Tier-3-Validation-Sprint-57.54`** (renumbered from Sprint-57.53; need agent-delegated sprint at `mechanical-greenfield` 0.50 sub-class for 1st validation data point — estimated scope: any backend or frontend sprint with single-track NEW component-pair where user pre-confirms agent delegation at Day 0)
- **`AD-Plan-Workload-AgentDelegation-Explicit-Field`** (NEW from retro Q3 Lesson 3 — codify sprint plan §6 pre-commit "agent-delegated: yes/no/partial/TBD-Day-1-decision" field BEFORE Day 0 三-prong; default to "TBD" at draft, finalize at Day 0 approval gate; default to "yes" if user defers — protects calibration matrix from accidental no-data-point sprints)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (NEW from retro Q3 Lesson 1; Phase 58.x — extract `_clear_committed_test_tenants` to shared `tests/conftest_helpers.py` module so api + agent_harness + future scopes can import-and-allowlist rather than duplicate the function body)
- **`AD-MediumBackend-AICadence-Recalibration`** (NEW from retro Q4 sub-lesson; Phase 58+ — revisit `medium-backend` 0.80 baseline if next 2-3 human-factor sprints continue to land 0.70-0.85; class baseline may be slightly too high for AI-cadence parent-assistant-direct work)

#### 57.52
1. **`AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation`** (**Sprint 57.53 user-confirmed scope**) — Sprint 57.51 carryover continues; pre-existing fail on main `6327e597`; investigate root cause + classify fix (test issue vs code bug) + optional fix; ~1-2 hr scope; class TBD pending root cause (likely `medium-backend` 0.80 OR `frontend-page-bug-fix` 0.45)
2. **`AD-AgentFactor-Tier-3-Validation-Sprint-57.53`** (NEW from Sprint 57.52 retro Q4 tier-3 ACTIVATION) — 1st validation under new sub-class table; Sprint 57.53 maps to which sub-class TBD pending root cause investigation; class-dependent
1. **🥇 AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation** (~1-2 hr) — **user-confirmed Sprint 57.53 scope**; bug-fix sprint; production stability matters; surfaces root cause for "how did silent failure land in main"
2. **🥈 Phase 58.x TenantSettings persistence work** (any of 4 sub-tracks) — meaningful production extension; class `medium-backend` 0.80
3. **🥉 Pause / Phase 57.x SaaS feature work resumption** — accumulated audit/docs hygiene work cleared (5 ADs closed Sprint 57.48-52 trail); Phase 57+ feature pipeline could resume
---

#### 57.51
1. **`AD-Day0-Prong2-Oklch-Delta-Grep`** (NEW Track C lesson) — Codify oklch-delta grep step into `sprint-workflow.md §Step 2.5 Prong 2` for future agent-delegated frontend migration sprints. Generalizes beyond oklch to any baseline-constrained metric (HEX_OKLCH / AP-N detector counts / bundle size / test-count thresholds). ~30 min `audit-cycle/docs/template` 0.40 class. Recommended as Sprint 57.52 scope.
2. **`AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail`** (NEW Day 1 surface) — `test_checkpointer_db::test_tenant_isolation` fails on main `8431646f` (Sprint 57.50 baseline); 0 backend source changes in Sprint 57.51 → pre-existing failure. Suggests Sprint 57.50 closeout missed full backend pytest sweep OR paths-filter masked. ~1-2 hr investigation + fix. Class TBD (medium-backend OR frontend-page-bug-fix depending on root cause).
3. **`AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52`** (NEW retro Q4 carryover) — 2nd validation data point needed under `mixed-multidomain-bundle` 0.65; conditional structural action if also > 1.20 (rollback to 1.0 OR tier-3 split).
4. **`AD-REFACTOR-Numbering-Collision`** (NEW Sprint 57.51 Day 0.8 BONUS observation) — 2 files share `REFACTOR-001-*.md` prefix. Rename one to REFACTOR-002 for traceability. ~10 min chore. Could be bundled with #1 as 2-track audit/docs sprint.
1. **🥇 Audit/docs hygiene bundle continuation** (~1-1.5 hr) — Bundle #1 + #4 + AD-Stale-Docstring-Karpathy-3 into a Sprint 57.52 triple-track `audit-cycle/docs/template` 0.40 sprint. Naturally tests 2nd validation under `mixed-multidomain-bundle` 0.65. Closes 3 small carryovers cleanly.
2. **🥈 Investigate AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail** (~1-2 hr) — Bug-fix sprint; production stability matters; class TBD pending root cause. Would surface "how did silent failure land in main" + close the lint hygiene gap.
3. **🥉 Pause** — Sprint 57.51 just closed 3 ADs from Sprint 57.48-50 trail; carryover queue reduced; tier-2 1st validation data point captured; let user direct Phase 58.x persistence work OR Phase 57.x SaaS frontend feature work resumption.
---

#### 57.50
80. 🆕 **`AD-AgentFactor-Tier-2-Sub-Class-Validation-Sprint-57.51`** — 1st validation needed under tier-2 sub-class table. Sprint 57.51 will naturally generate either `pattern-reuse-heavy` 0.30 OR `greenfield` 0.50 data point depending on work shape.
81. 🆕 **`AD-TenantSettings-Identity-Persistence-Phase58`** Phase 58.x — full SSO admin schema: dedicated `tenant_identity` table + admin PATCH endpoint + audit chain WORM + tenant_overrides → real table migration. Mirrors `AD-TenantSettings-RateLimits-Persistence` (#79) pattern.
82. 🆕 **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** — Plan §8 Risks ORM file path references should use 09-db-schema-design.md Group references (e.g. "identity.py per Group 1 Identity & Tenancy") not table_name.py speculation. D-DAY0-2 lesson: Tenant ORM lives in `identity.py` not `tenant.py`. Codify in plan template + sprint-workflow.md §Step 1 risk class catalog. ~30 min `chore(rules)` micro-sprint.
83. 🆕 **`AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern`** — Treat docstring claims as "code" for Day 0 三-prong Prong 2 content verify. D-DAY0-8 lesson: Sprint 57.49 _fixtures.ts docstring referenced SEATS_FIXTURE which Sprint 57.49 already removed; stale comment caught Day 0. Generalize: docstring claims grep-verified against repo reality, not just at MHist entry creation time. ~15-30 min `chore(rules)` codification.
1. 🥇 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** ~1-2 hr (`audit-cycle / docs / template` 0.40 class; codifies Sprint 57.48 D-DAY0-6 lesson into `.claude/rules/`; original Sprint 57.50 plan candidate (b) for follow-up)
2. **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** ~30 min (#82 micro-sprint; quick `chore(rules)` codification)
3. **Pause** — Natural break point after 6 consecutive sprints (57.45-50) cleanly closed + DUAL CLEAN milestone preserved + tier-2 ESCALATION just landed (let 1-2 sprints validate tier-2 before more carryover work)
---

#### 57.43
73. 🆕 **`AD-AgentFactor-Sub-Class-Validation-Sprint-57.50`** (Sprint 57.49 NEW) — 2nd validation under `mechanical-single-domain` 0.45 needed. Current: 1st = Sprint 57.49 ratio actual/committed-with-agent-factor **~0.14 BELOW band by ~0.71** → KEEP single-data-point caution. If Sprint 57.50 also < 0.7 → escalate to tier-2 refinement (see #74). Naturally generated by any single-domain agent-delegated sprint scope.
74. 🆕 **`AD-AgentFactor-Tier-2-Refinement-Proposal`** (Sprint 57.49 NEW) — If Sprint 57.50 2nd `mechanical-single-domain` data point also < 0.7 → propose tier-2 refinement: split `mechanical-pattern-reuse-heavy` **0.30** (≥4 mechanical repetitions in 1 sprint; matches Sprint 57.48/49 mean ~0.155) vs `mechanical-greenfield` **0.50** (single new component/endpoint; matches Sprint 57.47 ratio ~0.27 closer to band). Pending Sprint 57.50 evidence.
75. 🆕 **`AD-TenantSettings-IdentityFixture-Cleanup`** (Sprint 57.49 NEW) **~1 hr** — `IDENTITY_FIXTURE` in `tenantSettingsService.ts` retained per Sprint 57.49 §_fixtures.ts cleanup; not yet migrated to real backend (5-tab migration shipped + DANGER_OPS retained too). Completes the fixture purge. Class `mechanical-single-domain` 0.45 candidate (single-file migration; natural 2nd validation data point for #73).
76. 🆕 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (Sprint 57.48 NEW) **~1-2 hr** — Codify D-DAY0-6 lesson into `.claude/rules/`: lint detectors using regex pattern matching must apply code-aware masking (HTML/JSX attribute names like `placeholder=` / TS keys / string literals) to avoid false-positives. Root cause for AP-4 detector breaking 9/9 V2 lints in Sprint 57.46 → Sprint 57.48 Track E false-positive fix. Class `audit-cycle / docs / template` 0.40 candidate.
77. 🆕 **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49 carryover) — 3rd data point needed for class `medium-frontend` 0.65. Current: 1st = Sprint 57.13 ratio 0.95-1.0 in band; 2nd = Sprint 57.49 ratio actual/class-committed 0.064 (confound resolved by sub-class split; under agent_factor `mechanical-single-domain` 0.45 = ratio ~0.14). Per `When to adjust` 3-sprint window rule → KEEP class baseline pending 3rd data point. Naturally generated by next medium-frontend sprint.
78. 🆕 **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (Sprint 57.46 carryover) DEFERRED Phase 58+ **~5-8 hr** — `mockup-sweep.mjs` (Option B Python http.server + Playwright 1440×900) already implements basic capture per Sprint 57.46 D-DAY0-5 revelation; missing: per-page parity scoring + drift alerting + CI integration.
79. 🆕 **`AD-TenantSettings-RateLimits-Persistence`** (Sprint 57.48 carryover) DEFERRED Phase 58.x — Sprint 57.48 Track D shipped Option A fixture-projection from `tenants.meta_data` JSONB; full persistence model (dedicated `tenant_rate_limits` table + admin PATCH endpoint + audit chain) deferred to Phase 58.x.
1. 🥇 **`AD-TenantSettings-IdentityFixture-Cleanup`** (#75) **~1 hr** — Class `mechanical-single-domain` 0.45; naturally generates #73 (2nd validation data point). Cleanest hygiene close.
2. **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (#76) **~1-2 hr** — Class `audit-cycle / docs / template` 0.40; codifies repeatable lesson into `.claude/rules/`.
3. **Pause** — Natural break point after 5 consecutive sprints (57.45-57.49) cleanly closed + 14 ADs total + DUAL CLEAN milestone preserved.
---

#### 57.42
66. 🆕 **`AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint`** — Backend `/api/v1/memory/matrix?scope=*&time_scale=*&cursor=*` endpoint for real cursor-aware time-travel data. Sprint 57.42 fixture + client-side filter simulation. Phase 58+.
67. 🆕 **`AD-Memory-Ops-Timeline-Backend-Endpoint`** — Backend `/api/v1/memory/ops/recent?limit=100` endpoint for RecentMemoryOpsCard. Sprint 57.42 fixture-only. Phase 58+.
68. 🆕 **`AD-Memory-GDPR-Erasure-Backend-Endpoint`** — Backend `/api/v1/memory/erasure` POST endpoint for GdprErasureCard form (audit chain WORM record). Sprint 57.42 form button non-functional (window.alert stub). Phase 58+.
69. 🆕 **`AD-Memory-Vintage-Hooks-Cleanup`** — `memoryService.ts` preserved Day 1 but has 0 consumers post-rebuild. Phase 58+ either wire to RecentMemoryOpsCard (when ops endpoint ships) OR fully orphan delete.
70. 🆕 **`AD-Memory-Old-URL-Redirect-Phase58-Retire`** — Sprint 57.42 keeps `/memory/recent` + `/memory/by-scope` → `/memory` redirects for backward compat. Phase 58+ analytics-based retire once bookmark traffic decays.
71. 🆕 **`AD-Memory-New-Entry-Modal-Phase58`** + **`AD-Memory-Export-Action-Phase58`** — Mockup `.page-head` "New entry" and "Export" buttons are Sprint 57.42 AP-2 stubs. Phase 58+ wires write modal + CSV/JSON export endpoint.
72. 🆕 **`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift`** — **Lower-trigger MET** (3 consecutive < 0.7: 57.40 0.36 + 57.41 0.18 + 57.42 0.33). Propose Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45. Validate next 2-3 sprints.
1. 🥇 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` ~12-15 hr (4th CATASTROPHIC; backend GET list endpoint already wired; pure frontend work)
2. **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` ~15-20 hr (5th and LAST CATASTROPHIC; largest scope; mostly form work)
3. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename ~30 min (NEAR-PARITY quick win)
---

#### 57.41
60. ✅ **`AD-Memory-Layers-Matrix-Rebuild`** — **CLOSED Sprint 57.42** (Day 1 agent-delegated 10th consecutive code-implementer ~40 min wall-clock + Day 2 +12 NEW Vitest specs + drift audit verdict PARITY; 6 NEW components + _fixtures.ts + outer 2-tab DROP §1.4 Option B + 11 orphan deletes Karpathy §3; actual ~3 hr human-eq vs est 10-15 hr → 8th data point for `frontend-mockup-strict-rebuild` 0.60 baseline ratio 0.33; lower-trigger MET for Sprint 57.43 baseline lift; 5th cross-class data point for agent-delegation modifier activation FULLY MET)
61. 🆕 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` tenants table rebuild ~12-15 hr.
62. 🆕 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab rebuild ~15-20 hr. **Largest scope of remaining 3 CATASTROPHIC.**
63. 🆕 **`AD-Verification-Filter-Form-Phase58-Migrate`** — Sprint 57.41 retired filter form per Karpathy §3 (mockup has none). Phase 58+ admin filter UI on `/verification/admin` separate route OR collapsible `<details>` panel.
64. 🆕 **`AD-Verification-Backend-Claim-Evidence-Extension`** — Backend `VerificationLogItem` lacks structured `claim` / `evidence` / `kind`; mapped best-effort via Sprint 57.41 `adaptItem()`. Phase 58+ backend schema extension.
65. 🆕 **`AD-Verification-Failure-Kinds-+-Flaky-Checks-Aggregation-Endpoints`** — Sprint 57.41 sidebar Failure kinds + Flaky checks are AP-2 fixtures. Phase 58+ backend `GET /verifications/stats/{failure-kinds,flaky-checks}` endpoints.

#### 57.40
50. ✅ ~~**`AD-Verification-Catastrophic-Rebuild`**~~ — **CLOSED Sprint 57.41** (this rebuild). `/verification` rebuild to mockup 4-KPI + 2-col Recent verification runs + Failure modes + Flaky checks sidebar. Class `frontend-mockup-strict-rebuild` 0.60. Final actual 1.5 hr / committed 8.5 hr / ratio 0.18 (deepest below band; agent-delegated 8th+9th consecutive). Pattern reuse hit: 2 of Sprint 57.40's 5 NEW (PageHeader + StatsStrip) transferred via rename + 4 NEW unique (RunsTable + FailureKindsCard + FlakyChecksCard + View container). See `memory/project_phase57_41_verification_full_rebuild.md` for detail.
51. 🆕 **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename `Turn/Trace/Memory/Tree` → mockup `Run/Tools/Memory/Verify`. Class `frontend-refactor-mechanical` 0.50. Est ~30 min (quick win).
52. 🆕 **`AD-Memory-Layers-Matrix-Rebuild`** — `/memory` rebuild to mockup `Memory Layers` 5×N matrix design (SYSTEM/TENANT/ROLE/USER/SESSION × time-scale columns + playback slider + time travel + Export + New write + Recent memory ops strip). Currently Sprint 57.12 vintage shadcn-utility. Class `frontend-mockup-strict-rebuild` 0.60. Est ~10-15 hr.
53. 🆕 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` rebuild to mockup Tenants + 4 KPI + 9-col table 9 rows (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED). Known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #1 + matches Sprint 57.22 audit `6-tab architectural finding`. Backend GET endpoint already wired. Class `frontend-mockup-strict-rebuild` 0.60. Est ~12-15 hr.
54. 🆕 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` rebuild to mockup 6-tab nav (General/Feature Flags 14/Quotas/HITL Policies/Members 8/Danger Zone) + 2-col General form + Identity & SSO sidebar. Known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #2. Class `frontend-mockup-strict-rebuild` 0.60. **Largest scope** (mostly form work). Est ~15-20 hr.
55. 🆕 **`AD-Shell-Defensive-Guards-For-Malformed-AuthMe`** (D-DAY1-1 investigation byproduct) — pre-emptive hardening of Sidebar / Topbar / OverviewPage / UserMenu against hypothetical malformed `/auth/me` shape. Sprint 57.33 pattern precedent. FIX-019 candidate. Est ~30 min.
56. 🆕 **`AD-Playwright-Mock-LIFO-Fixture-Convention`** (D-DAY1-2 investigation byproduct) — codify `r.fallback()` LIFO pattern + envelope-shape mock requirement into `.claude/rules/testing.md` or `docs/rules-on-demand/testing.md`. Est ~30 min.
57. 🆕 **`AD-DecisionModal-Doc-References-Mop-Up`** (Day 1 Karpathy §3 orphan delete follow-up) — clean 3 stale doc refs after `DecisionModal.tsx` delete (dialog.tsx / useApprovalDecide.ts / guardrails README). Est ~15 min.
58. 🆕 **`AD-RouteSweep-Envelope-Mock-Convention`** (Day 2 audit-report carryover) — codify in `frontend-mockup-fidelity.md` or `testing.md`: any endpoint returning envelope shape (e.g. `{items, total, has_more}`) needs explicit sweep mock entry; default `[]` is only safe for list-shaped endpoints. Grep-pattern + example. Est ~30 min.
59. ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up `chore/agent-delegation-factor-activate` branch). 5 cross-class data points (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 + 57.42 0.33) + 4 consecutive `mockup-strict-rebuild` < 0.7 = activation criteria FULLY MET at Sprint 57.42 retro Q4. See top of file `Updated` field + `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`. Actual ~1 hr (calibration class `audit-cycle / docs / template` 0.40 — within estimate).
---

#### 57.39
47. ✅ **`AD-Governance-Verification-Child-Component-Re-Point-Phase58`** — RESOLVED 2026-05-25 via **FIX-015** (6 child component re-point with agent delegation; ~25 min wall-clock). Day 0 grep scope adjusted from AD spec: 5 listed → final 6 files (ApprovalsPage already clean / VerificationDetail renamed to VerificationPanel / +ApprovalList +DecisionModal NEW findings). Token-level swap shadcn-utility (`bg-card`/`text-foreground`/`border-border`/`bg-muted`/`text-muted-foreground`) → mockup verbatim (`.card`/`.table`/`.btn`/`.badge`/`.field`/`.input`/`.subtle`/`.mono`/`.row`). HEX_OKLCH_BASELINE tightened 51→50. Vitest 478/478 + mockup-fidelity ✓ + build ✓ + tsc 0. Phase-2 epic 15/17 → 17/17 non-STRUCTURAL routes (2 🟡 STRUCTURAL `/memory` + `/tenant-settings` remain Phase 58+). See `claudedocs/4-changes/bug-fixes/FIX-015-governance-verification-child-component-repoint.md`.
47.5. ✅ **`AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels`** — RESOLVED 2026-05-25 via **FIX-017** (post-4-AD-sequence next item per user authorization). Day 0 scope adjusted from AD spec 1 file → 3 governance files (ApprovalList + Badge cva variants + AuditChainBadge; chat_v2 already migrated). Tailwind v4 typed arbitrary value with CSS var pattern: `text-[color:var(--risk-X)]` + `bg-[color:var(--risk-X)]/10` (preserves `/<opacity>` modifier). Vitest spec assertion updated (`tests/unit/components/ui/components.test.tsx:91` hex literal → token reference). HEX_OKLCH_BASELINE tightened 50→45. All validation green (tsc 0 / lint 0 / mockup-fidelity ✓ / Vitest 478/478 / build 3.44s). See `claudedocs/4-changes/bug-fixes/FIX-017-risk-color-normalization-approvallist-and-governance-badge-family.md`.
48. ✅ **`AD-Day0-Prong2-Child-Component-Tree-Depth-Audit`** — RESOLVED 2026-05-25 via **`chore(rules)`** (rule update commit, not FIX). `.claude/rules/sprint-workflow.md §Step 2.5` adds new sub-prong **Prong 2.5 — Child Component Tree Depth Audit** (frontend page sprints only): enumerate child component tree via `grep "import.*@/features/<area>"` then run anti-pattern greps (shadcn-utility token residue / inline style escape comments / outer wrapper artifact / fullBleed drop / tab-shell-vs-monolithic divergence) on each child file. Promoted as **AD-Plan-5** alongside existing AD-Plan-1/2/3/4. ROI evidence appended (Sprint 57.39 D-DAY1-1 escape + FIX-015 post-hoc validation = 20-60× when caught Day 0 vs Day 1+ scope expansion). MHist updated. See sprint-workflow.md §Step 2.5 §Prong 2.5.
48.5. ✅ **`AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern`** — RESOLVED 2026-05-25 via **`chore(rules)` Item #4 bundle** (Option A — documentation update). `.claude/rules/sprint-workflow.md §Before Commit Checklist §2 Lint+Format` Frontend line annotated: "**MUST run WITHOUT `--silent` flag**"; documents FIX-015 CI fail evidence + suggests `2>&1 | tail -20` for clean-but-error-preserving output. Lighter than Option B/C (package.json edits) — keeps the discipline in the rule layer where the lesson is reusable. See sprint-workflow.md §Before Commit Checklist.
49. ✅ **`AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages`** — RESOLVED 2026-05-25 via **FIX-016** (Option A — manual additions per Karpathy §2 Simplicity First). Added `/redaction` + `/error-policy` to `APPSHELL_ROUTES` (14 → 16 entries: 13 → 15 real + 1 PROP rep unchanged). Comment refreshed (13 PROP → 11 PROP). Sprint 57.40+ route-sweep runs now capture the 2 promoted routes in before/after directories. See `claudedocs/4-changes/bug-fixes/FIX-016-route-sweep-coverage-extend-prop-promoted.md`.
49.5. ✅ **`AD-RouteSweep-Auto-Derive`** — RESOLVED 2026-05-25 via **FIX-018**. Option (b) regex text-parse chosen and validated robust: split routes.config.ts ROUTES body on `},` boundaries (safe — RouteEntry blocks have no nested braces since `lazy(() => import(...))` uses parens), extract `path` + `active` + optional `proposed` per block. Derived 16 entries (15 real + 1 PROP rep `/compaction`) byte-identical to prior FIX-016 hardcoded list. Fail-fast `throw` on schema mismatch / zero-real result (per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern lesson). `--list-only` dry-run mode added for future validation. Greppable count log on real runs (`auto-derived: 15 real + 1 of 12 PROP rep`). Future PROP→real promotions auto-sync — `AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages` class of bug eliminated. See `claudedocs/4-changes/bug-fixes/FIX-018-route-sweep-auto-derive-from-routes-config.md`.
50. ✅ **`AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix`** — RESOLVED 2026-05-25 via **FIX-014**. ESM `__dirname` derivation via `fileURLToPath(import.meta.url)` + `path.resolve(__dirname, '../../claudedocs/...')` makes OUT_DIR cwd-invariant. Smoke-tested from non-project-root cwd; resolution correctly lands at `<project>/claudedocs/4-changes/<slug>/screenshots/<mode>/`. See `claudedocs/4-changes/bug-fixes/FIX-014-route-sweep-cwd-relative-outdir.md`.
51. ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **RESOLVED twice 2026-05-25** (same day, 2-step closure):
    1. **Step 1 — PROPOSAL** via `chore(rules)` Item #4 bundle (2026-05-25 morning): `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` adds **Proposed Agent Delegation Factor Modifier (PENDING VALIDATION)** subsection (Hypothesis + 2-data-point Evidence table + Option A 0.50-0.60 + Option B fallback + Activation rule 3-sprint window + Tracking discipline). 2 data points (57.39 + FIX-015) — INSUFFICIENT for activation.
    2. **Step 2 — ACTIVATED** via `chore/agent-delegation-factor-activate` branch (2026-05-25 — Sprint 57.42 closeout follow-up): 5th cross-class data point reached at Sprint 57.42 retro Q4 (57.39 0.41 + FIX-015 + 57.40 0.36 + 57.41 0.18 + 57.42 0.33; 4 consecutive `mockup-strict-rebuild` < 0.7) = **activation criteria FULLY MET**. Selected **Option A multiplicative `agent_factor = 0.55`** (mid-band conservative). §Proposed block replaced with §Active block + §Workload Calibration §Four-segment form added. First validation: Sprint 57.43 retro Q2. See sprint-workflow.md §Active Agent Delegation Factor Modifier.
After Sprint 57.39, the Phase-2 epic non-STRUCTURAL backlog is mostly cleared. High-ROI next candidates:
- ~~**`AD-Governance-Verification-Child-Component-Re-Point-Phase58`**~~ ✅ DONE 2026-05-25 via FIX-015 (6 child component re-point + HEX_OKLCH_BASELINE 51→50; ~25 min agent wall-clock; closes Phase-2 epic NEAR-PARITY → PARITY for /governance + /verification)
- **`/audit-log` DRAFT→active** (paired with Cat 9 backend; medium-backend + medium-frontend joint sprint)
- ~~**`AD-RouteSweep-Auto-Derive`**~~ ✅ DONE 2026-05-25 via FIX-018 (regex text-parse Option (b) chosen; 16 entries byte-identical match; fail-fast on schema drift; `--list-only` dry-run; future PROP→real promotions auto-sync)
- ~~**`AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern`**~~ ✅ DONE 2026-05-25 via `chore(rules)` Item #4 bundle (sprint-workflow.md §Before Commit annotation; Option A documentation update)
- ~~**`AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels`**~~ ✅ DONE 2026-05-25 via FIX-017 (3 governance files token swap + Vitest spec update + HEX baseline 50→45; chat_v2 already migrated pre-FIX-017)
- ~~**`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`**~~ ✅ DONE 2026-05-25 via `chore(rules)` Item #4 bundle (proposal logged in matrix; Option A `agent_factor` 0.50-0.60 PENDING 2-3 sprint validation per existing 3-sprint window rule)
- **`/admin-tenants` Phase-2** (`-simple` 0.50 3rd validation data point; ~1.5-2 hr with agent)
- ~~**`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** Path A 1-line global micro-fix~~ ✅ DONE 2026-05-25 via FIX-012 (Path A applied; see §Sprint 57.38 Follow-up Carryover for resolution detail)
- ~~**`AD-Inline-Font-Baseline-Alignment`** typography audit~~ ✅ DONE 2026-05-25 via FIX-013 (documented case; B/C dispositioned Skip per Karpathy §3)
- **Phase 58+ structural epic** `/memory` or `/tenant-settings` (~25-30 hr; needs backend pair)
- ~~**`AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix`**~~ ✅ DONE 2026-05-25 via FIX-014 (ESM `__dirname` via `fileURLToPath` + `path.resolve(__dirname, '../../...')`)
---

#### 57.38
- 🆕 **`AD-State-Inspector-Outer-Padding-Wrapper-Fix`** — ✅ RESOLVED by FIX-011 (logged for trace)
- ✅ **`AD-Inline-Font-Baseline-Alignment`** — RESOLVED 2026-05-25 via **FIX-013** for the FIX-011 §Issue 2 documented case (`StateInspectorPage` card title row `CARD_TITLE_ROW_STYLE` adds `alignItems: "baseline"`). Day 0 audit dispositioned Candidate B (CostBurnChart legend — plain inline `<span>`, no flex) + Candidate C (IncidentsCard row — compound badge+text children where `center` is correct) as Skip per Karpathy §3. Closes AP-Phase2-B deferred fix from FIX-011. See `claudedocs/4-changes/bug-fixes/FIX-013-inline-font-baseline-alignment.md`.
- ✅ **`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** — RESOLVED 2026-05-25 via **FIX-012** (user chose Path A as transitional fix). Both consumer sites retargeted at mockup `--border` (`index.css:85` global `* { border-color }` + `tailwind.config.ts:26` `border` utility); `--sc-border` declarations fully retired (0 residual code references). Sprint 57.28 4-layer dual-track partially relaxed (only `--sc-primary` remains as de-collided shadcn token). Path B Phase-2 epic completion still proceeds independently — Path A does NOT substitute for finishing the remaining 2 🟡 STRUCTURAL routes. See `claudedocs/4-changes/bug-fixes/FIX-012-shadcn-border-token-align-to-mockup.md`.
- 🆕 **Sister-bug observation**: FIX-010 (`/loop-debug` fullBleed prop drop) + FIX-011 (`/state-inspector` outer padding wrapper) form a recurring **layout-class production-only artifact** class. Each Phase-2 re-point sprint Day 0 Prong 1 should grep for these artifacts on the target page BEFORE Day 1 code.

#### 57.38
- **`AD-Day0-Prong-Test-Dir-Convention`** — extend Day 0 Prong 1 grep template to cover BOTH `frontend/src/**/__tests__/` AND `frontend/tests/unit/pages/<name>/<name>.test.*` (per Sprint 57.38 D-DB1-2 lesson — project uses separated test dir convention not always co-located `__tests__/`)
- **`AD-Day0-D5-Reclass-Strict-Criteria-Checklist`** — codify 5-item strict checklist before reclassifying `-simple` → `-with-extras` at Day 0 D5 (per Sprint 57.38 retro Q4#2: multi-file > 3 / AP-2 banner / dual-mount / playback widgets / HEX_OKLCH_BASELINE bump ≥ 4 — if 0 of 5 check, keep `-simple` even when internal structure complex)
- **Convention candidate (D-DB1-1)**: agent proactive div-wrap pattern preserves text+role+class-selector spec compat — document in `docs/rules-on-demand/frontend-react.md` as recommended-pattern when spec uses `getByText(x, { selector: "div" })`

---
---

## 🔴 Top Candidates (User-Aligned Priority)

### 1. AD-ChatV2-Full-Mockup-Fidelity Phase-2

Multi-sprint epic continuation. Sprint 57.21 Phase-1 already shipped:
- Turn Block Model
- SessionList fixture
- Inspector 4-tab frame
- Composer visual scaffolding

**Phase-2 carryover ADs** (from Sprint 57.21 retro):
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness-Phase2
- AD-ChatV2-Composer-Wire-Phase2
- AD-ChatV2-Inspector-{Trace, Memory, SubagentTree}-Phase2
- AD-ChatV2-SessionList-Backend
- AD-Cat12-SSE-Trace-Id-Phase2

**Mode**: Pick subset for Phase-2 first sprint depending on backend dependency ordering. Likely structural-rewrite mode → `frontend-mockup-direct-port` ratio ~1.0-1.2 predicted.

### 2. 🆕 AD-Mockup-Direct-Port-Round-2

NEW Sprint 57.20 Day 4 DRIFT-REPORT-ROUND-2 (16 R2 findings).

**Scope** — Token migration sweep for **8 remaining ship pages**:
- cost-dashboard / memory / verification / governance + 4 governance sub-routes / sla-dashboard / admin-tenants / tenant-settings

Plus:
- 3 overlay backend wiring
- R2-A 5 cosmetic Card visual polish

**Class**: Same `frontend-mockup-direct-port` 0.55 class likely.

### 3. AD-Mockup-Existing-Pages-Retrofit Tier 1

Sprint 57.19 US-F1 DRIFT-REPORT; partially closed Sprint 57.20 via `/overview` + `/chat-v2` token migration; **folds INTO Round-2 above**.

**Scope**: 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80).

**5 priority pages**:
- cost-dashboard (3 hr)
- chat-v2 (3 hr)
- memory (2 hr)
- verification (2 hr)
- governance (1.5 hr)

**Tier 2**: ~5.5 hr → Sprint 57.21+
**Tier 3**: ~1 hr + Round 3 epic

---

## 🟡 Mockup-Page-Port Continuation

### 4. AD-Mockup-Page-X-Port Round 3 — Auth 4

Sprint 57.19 carryover. Pages:
- register / invite / mfa / expired

**Pairing**: IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」.

### 5. AD-Mockup-Page-X-Port Round 4 — Governance 3

Sprint 57.19 carryover. Pages:
- redaction / error-policy / audit-log (DRAFT → active promote)

**Pairing**: Cat 9 endpoint extensions.

---

## 🟢 Backend Wire Bundle

### 6. AD-Backend-Wire Bundle

Sprint 57.19 4 NEW ADs:
- Subagent-RealList-Phase58
- Loop-Session-Enrich-Phase58
- Overview-Backend-Wire
- Orchestrator-Backend-Wire

**Scope**: Backend persistence + aggregation for Operations 4 pages (current fixture/stub). Can pair with retrofit work.

### 7. 🆕 AD-CommandPalette-Backend-Wire

NEW Sprint 57.19 US-D1. Tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index.

### 8. 🆕 AD-NotificationsPanel-Backend-Feed

NEW Sprint 57.19 US-D2. 6 mockup items local state; Cat 12 SSE/poll feed spec TBD.

### 9. 🆕 AD-UserMenu-Tenant-Switch

NEW Sprint 57.19 US-D3. Wire tenant switching paired with Round 2 WorkOS SCIM.

---

## 🛠️ Tooling / Infrastructure / Style

### 10. AD-Tailwind-v4-Config-Migration

Sprint 57.17 carryover. Full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file. ~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`.

### 11. AD-Post-Hotfix-Token-Audit

NEW Sprint 57.17 contrast-ratio portion. **Folds INTO** AD-Mockup-Existing-Pages-Retrofit Tier 1 work (same shadcn slate base sub-AA pairs).

### 12. 🆕 AD-Brand-Primary-Color-Decision

Sprint 57.18 D-PRE-1. Partially actioned by Sprint 57.19 US-A1 mockup indigo; finalization decision pending.

### 13. 🆕 AD-Theme-Variant-Mechanism

Sprint 57.18 D-PRE-2.

### 14. 🆕 AD-Density-Variant-Mechanism

Sprint 57.18 D-PRE-3.

### 15. AD-CI-7-GHA-PR-Permission

Sprint 57.17 carryover. `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting.

### 16. AD-Lighthouse-Visual-Hard-Gate

Baselines reliable post-57.17; required CI check.

### 17. AD-Bundle-Size code-split

### 18. AD-i18n-Feature-Namespaces

### 19. AD-A11y-Structural-Nits

Sprint 57.16 carryover. `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one`.

---

## 🏢 Enterprise / SaaS Stage 2

### 20. IAM Block B Spike

~12-18 hr — WorkOS SCIM/SAML/org-level. Pairs with #4 Auth 4.

### 21. Tier 1 IaC + DR Drill

~15-20 hr.

### 22. SOC 2 + SBOM

~12-15 hr.

---

## 🟣 Sprint 57.23 Auth Page Rebuild Carryovers (NEW 2026-05-18)

7 ADs from Sprint 57.23 AD-Auth-Page-Full-Rebuild-Round-2 closeout. Frontend rebuild shipped 8/8 USs with stub-501 demo banners; backend wiring deferred to Phase 58+ IAM Block B/C per Q2 frontend-only decision.

### 23. AD-Auth-Register-Backend-IAM-Block-B-Phase58
`POST /api/v1/tenants/register` real implementation. Currently 501 stub. Frontend `/auth/register` 4-step wizard fully shipped + i18n + Vitest 5 cases. Phase 58+ IAM Block B scope.

### 24. AD-Auth-Invite-Backend-IAM-Block-B-Phase58
`GET /api/v1/invites/:token` (metadata) + `POST /api/v1/invites/:token/accept`. Currently 501 stubs; frontend falls back to fixture metadata silently for GET, surfaces explicit error for POST. Frontend `/auth/invite/:token` shipped + Vitest 4 cases. Phase 58+ IAM Block B scope.

### 25. AD-Auth-MFA-Backend-IAM-Block-C-Phase58
`POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Currently 501 stub. Frontend `/auth/mfa` Roll-own UI shipped (TOTP 6-digit grid + WebAuthn conic ring + Simulate button) + Vitest 7 cases. Phase 58+ IAM Block C scope.

### 26. AD-Auth-MFA-Recovery-Page-Phase58
`/auth/mfa/recovery` page wire — currently displayed as `<span pointer-events-none>` with tooltip "Recovery flow pending Phase 58+ IAM Block C". Backend recovery-code generation + verification. Phase 58+ IAM Block C scope.

### 27. AD-Auth-Callback-Loading-UX-Phase58
Replace static 3-step `setTimeout` (800/1800/2800ms) with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Frontend already has 3-step UI + parallel-bootstrap + min-2800ms-enforce mechanism. Phase 58+ IAM Block B scope.

### 28. AD-WorkOS-Multi-IdP-Phase58
Wire actual SAML / Microsoft / Google SSO via WorkOS. Currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip per mockup. Backend WorkOS Multi-IdP integration. Phase 58+ IAM Block B scope. (Existed pre-57.23 as design intent; now actively blocks Sprint 57.23 login button enablement.)

### 29. AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup
Re-run Playwright MCP visual pair-verify on Sprint 57.23 12 page-states. Day 4 closeout encountered stuck browser state from prior Sprint 57.22 session (`Error: Browser is already in use ... use --isolated`). Closure via code-level audit + Sprint 57.22 baseline + visual-regression CI mechanism. Re-run in future session with fresh browser instance. **Low priority** — line-by-line port discipline + DRIFT-REPORT verdicts (all PARITY or COSMETIC; 0 STRUCTURAL/FUNCTIONAL) already cover fidelity gate.

### 30. AD-I18n-Symmetric-Keys-Lint-Phase58
Implement automated symmetric-keys lint at `frontend/tests/unit/i18n/` that runs `jq paths(scalars)` diff between en/<namespace>.json and zh-TW/<namespace>.json on every PR. Sprint 57.23 verified manually for `auth.json`; this AD generalizes for `chat-v2.json` / `governance.json` / `tenant-settings.json` etc. ~2-3 hr.

---

## 🔵 Sprint 57.24 Decision Carryovers (NEW 2026-05-19)

### 31. AD-Memory-Structural-Rebuild-Phase58
`/memory` page rebuild — Sprint 57.22 Unit 10 audit identified STRUCTURAL severity drift: production has simple 2-tab UI (Recent / By Scope) + 3 backend-wired scopes (system/tenant/user); mockup `page-governance.jsx:462-598` has full 5-scope × 3-time-scale matrix grid + time-travel scrubber + memory-ops timeline + per-memory CRUD.

**Scope**: Frontend rebuild ~12-15 hr + backend Cat 3 NEW SSE event `memory_op_emitted` ~3-4 hr + Cat 12 audit log ~2 hr + role/session backend scopes (currently Phase 58+ stubs) ~6-8 hr. **Total ~25-30 hr**.

**Class candidate**: NEW `frontend-mockup-structural-rebuild` (parallel to Sprint 57.23 NEW `frontend-mockup-strict-rebuild` 0.60 1st app; or HYBRID with backend wire).

**Defer rationale (Sprint 57.24 Q2 decision 2026-05-19)**: STRUCTURAL retrofit exceeds Sprint 57.24 `mockup-fidelity-retrofit` 0.55 scope (which is cosmetic-only by class definition). Memory structural rebuild needs dedicated sprint with backend pairing per Sprint 57.22 §Sprint 57.23+ Recommendation Tier 2 priority.

**Phase**: 58+ (after Auth Block B/C IAM backend lands; role/session memory scopes are part of IAM).

---

## 🟢 Sprint 57.24 v2 Cost Dashboard Rebuild Carryovers (NEW 2026-05-19)

7 ADs from Sprint 57.24 v2 AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild closeout. Frontend rebuild shipped 6 widget groups + 7 reusable primitives (PageHead/Spark/StatCard/AreaChart/BarTrack/CardShell/BackendGapBanner) for Sprint 57.25-57.28 epic; 3 of 6 widgets ship fixture + visible BackendGapBanner per AP-2 honesty (backend wiring deferred).

### 32. ✅ CLOSED — AD-Mockup-Fidelity-Rebuild-Sla-Dashboard (shipped Sprint 57.25 2026-05-19)
~~Rebuild `/sla-dashboard` per mockup `reference/design-mockups/page-admin.jsx:31-199` (SlaPage).~~ **Shipped Sprint 57.25**: 6 widget groups (page-head + TimeRangeTabs / 4-stat sparkline / 24h LatencyChart 3-series / 5-row SLO status / Top slow ops table / Error rate by service); reused 7 Sprint 57.24 v2 primitives without API change validating Karpathy §2 ROI; 1 NEW feature-scoped LatencyChart inline; SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER (see #41). See `memory/project_phase57_25_sla_dashboard_rebuild.md` for detail.

### 33. AD-Mockup-Fidelity-Rebuild-Admin-Tenants-Phase58
Rebuild `/admin/tenants` list per mockup `page-admin.jsx:322-410` (AdminTenants section). Existing filters/table/pagination preserved; mockup-fidelity polish + admin context widgets added (avatar rendering / row-level actions / status badges per mockup). Sprint 57.27 candidate (foundation-fidelity Sprint 57.26 was inserted ahead as a user-directed sprint, shifting this +1).

### 34. AD-Mockup-Fidelity-Rebuild-Verification-Phase58
Rebuild `/verification` per mockup `page-extras.jsx:817-927` (VerificationPage). 2-tab structure (Recent / Correction Trace) preserved; inner widget mockup-fidelity port pending. Sprint 57.28 candidate.

### 35. AD-Mockup-Fidelity-Rebuild-Tenant-Settings-Phase58
Rebuild `/admin/tenants/settings` per mockup `page-admin.jsx:411+` (TenantSettings 6-tab) + lift `/feature-flags` out per Sprint 57.22 Unit 31 architectural finding + page-extras.jsx:928 comment "/feature-flags (lifted out of /tenant-settings)". Architectural-level refactor + new standalone `/feature-flags` route. Sprint 57.29 candidate.

### 36. AD-Cost-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.24 v2 fixture-driven widgets:
- Cross-tenant aggregation endpoint (`GET /api/v1/admin/cost-summary/by-tenant` returning top-N tenant rows; platform-admin-scoped) — drives TenantTopTable
- Cross-provider aggregation endpoint (`GET /api/v1/admin/cost-summary/by-provider`; platform-admin-scoped) — drives ProviderMixCard with LLM-neutrality redacted labels
- 30-day daily history endpoint (`GET /api/v1/admin/cost-summary/history?days=30`) — drives AreaChart
- Harmonize category taxonomy: mockup 6 flat categories (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) ≠ current backend `by_type` 2-level dict shape (cost_type → sub_type → AggregatedSlice); decision: either backend reshape OR define explicit aggregation mapping in spec

Drives Sprint 57.24 BackendGapBanner removal for 3 of 6 widgets + flips fixture data to real. ~8-12 hr backend + ~2-3 hr frontend wire-up. Phase 58+ backend-led; could pair with Sprint 57.25 sla-dashboard rebuild if scope permits.

### 37. AD-Playwright-MCP-Recovery-Phase58
**3-consecutive-sprint blocker** (Sprint 57.22 + 57.23 + 57.24 v2): Playwright MCP browser-stuck on every visual pair-verify attempt. `browser_close` returns "Browser is already in use for ...mcp-chrome-... use --isolated to run multiple instances of the same browser". Root cause: Claude Code session-process management — prior session's chrome instance not released to next session.

**Mitigation today**: code-level audit + Vitest spec coverage + Playwright CLI (separate from MCP) cover verification; visual baselines regen via CI workflow_dispatch + cherry-pick (Sprint 57.14 + 57.23 PR #156 + 57.24 v2 PR pattern).

**Phase 58+ resolution paths**:
- Option A: pass `--isolated` flag to MCP browser per session
- Option B: explicit cleanup hook on Claude Code session end (`process.kill` on chrome PID)
- Option C: contribute fix upstream to Anthropic Playwright MCP plugin

Cost: ~2-4 hr investigation + fix. Phase 58+; meanwhile workaround acceptable.

### 38. AD-Sprint-Plan-Audit-Cross-Ref-Prong5
**Plan-draft discipline addition** (Sprint 57.24 v1 abort lesson):

Sprint 57.24 v1 plan misclassified 3 of 5 retrofit targets (cost / sla / tenant-settings) as "cosmetic-feasible Tier 1" when Sprint 57.22 AUDIT-REPORT had already marked them P0 full-rebuild. Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema + Prong 4 test selector) didn't catch this because they verify code-vs-plan drift, NOT plan-vs-audit-classification mismatch.

**Proposed Prong 5: Audit Cross-Reference**:
Before drafting Tier-N retrofit/rebuild plan, grep AUDIT-REPORT(s) for each target's prior classification:
```bash
# Example for Sprint 57.24 v1
for target in cost-dashboard sla-dashboard verification admin/tenants tenant-settings; do
  grep -l "Unit.*$target" docs/03-implementation/agent-harness-execution/phase-57/sprint-57-*/artifacts/*audit*/AUDIT-REPORT*.md
done
```
If any target is already audit-classified as P0 / structural-rebuild → lift conflicting entries into structural-rebuild scope before drafting cosmetic-retrofit batch.

**Scope**: Add to `.claude/rules/sprint-workflow.md` §Step 2.5 as new Prong 5; ~30 min doc edit. Phase 58+ when next Tier-N retrofit/rebuild batch is drafted.

---

## 🟢 Sprint 57.25 SLA Dashboard Rebuild Carryovers (NEW 2026-05-19)

3 ADs from Sprint 57.25 AD-Mockup-Fidelity-Rebuild-Sla-Dashboard closeout. Frontend rebuild shipped 6 widget groups reusing 7 Sprint 57.24 v2 primitives without API change + 1 NEW feature-scoped LatencyChart (Karpathy §2 inline); SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER pending 4th data point.

### 39. AD-SLA-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.25 fixture-driven widgets:
- 24h time-series aggregation endpoint (`GET /api/v1/sla/latency-history?range=24h`) returning per-time-bucket {p50, p95, p99} — drives LatencyChart 24h
- Cross-operation p99 aggregation endpoint (`GET /api/v1/sla/slow-operations?range=24h&limit=N`) — drives TopSlowOpsTable
- Per-service error rate aggregation endpoint (`GET /api/v1/sla/error-rates?range=1h`) — drives ErrorRateByServiceCard
- Dedicated SLO threshold metrics (`tool_success_pct` / `hitl_response_p95_min` / `subagent_depth_max` / `cost_per_run_usd`) — drives SLOStatusCard 4 of 5 fixture rows
- Existing `useSLAReport` SLAReportResponse extension: `latency_p50_ms` + `latency_p95_ms` + `error_budget_pct` fields (currently fixture per D-PRE-2)

Drives Sprint 57.25 BackendGapBanner removal for 3 widgets (LatencyChart 24h / cross-op p99 / per-service error rate) + flips 3 stat cards (p50/p95/error_budget) + 4 of 5 SLO rows from fixture to real. ~10-14 hr backend + ~3-4 hr frontend wire-up. Phase 58+ backend-led; pairs with Sprint 57.26-57.28 backend extensions for cost-dashboard #36.

### 40. AD-LatencyChart-Extraction-Phase58
Extract `LatencyChart` from `frontend/src/features/sla-dashboard/components/` to `frontend/src/components/charts/` as generalizable 3-series multi-line primitive **IF 2nd consumer arises** per Karpathy §2 "extract on 2nd consumer" rule.

Current state (Sprint 57.25): inline feature-scoped (~110 lines); single consumer = SLA dashboard 24h LatencyChart. Sprint 57.26+ may have 2nd consumer if `/admin/tenants` rebuild needs similar multi-series visualization OR Sprint 57.27 `/verification` correction-trace shows latency distribution.

**Extraction trigger criteria**:
- 2 distinct production consumers with comparable 3-series multi-line shape (NOT just any chart need)
- API generalizable beyond hardcoded p50/p95/p99 series → e.g. `<MultiLineChart series={[{key, stroke, width, opacity}]} data />`
- Estimate: ~2 hr extraction + Vitest update

If 4th data point sprint (57.26+) doesn't surface 2nd consumer → DROP this AD entirely (Karpathy §2 rule applied correctly).

### 41. AD-Sprint-Plan-rich-dashboard-sub-class-DEFER — ✅ RESOLVED (Sprint 57.27 — DROPPED)
Sub-classification proposal logged Sprint 57.24 v2 retro Q4 (rich-dashboard ratio 1.19 vs auth-flow 0.59) deferred per Sprint 57.25 3rd data point ratio 0.88. 2-data-point rich-dashboard mean (57.24 v2 + 57.25) = ~1.04 sits in-band middle of [0.85, 1.20] — does NOT justify split.

**Resolution path** (original):
- Sprint 57.27 = 4th data point (admin-tenants list rebuild; rich-dashboard shape — foundation-fidelity Sprint 57.26 was inserted ahead, shifting it +1)
- If 57.27 ratio in band → **DROP** sub-class proposal (3-of-3 rich in band; KEEP 0.60 baseline)
- If 57.27 ratio > 1.20 → reconsider rich sub-class higher (~0.70-0.75); 2-of-3 rich above band
- If 57.27 ratio < 0.85 → drop rich-dashboard pattern entirely; KEEP 0.60 baseline accepts auth-flow + rich mixed

**✅ RESOLVED 2026-05-21 (Sprint 57.27 closeout — DROPPED)**: Sprint 57.27 became the `/overview` full rebuild (user-directed; superseded the planned admin-tenants 57.27 candidate, but `/overview` is itself a rich operator dashboard — 2 charts + 4-stat KPI + 4 cards — so it serves as the 4th rich data point). 57.27 ratio ≈0.95 — **IN BAND**. Rich-subset 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → 3-pt mean ~1.01 in-band middle → **sub-class proposal DROPPED, no split**; KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class. Matrix row + MHist updated in `.claude/rules/sprint-workflow.md`.

---

## 🟡 Sprint 57.26 Foundation-Fidelity Carryover (NEW 2026-05-21)

1 AD from Sprint 57.26 post-closeout CI investigation. PR #159's first `Frontend E2E` run failed — `visual-regression.spec.ts` 5 `toHaveScreenshot()` baselines (auth-login / cost-dashboard / governance / verification-recent / admin-tenants) mismatched because the foundation-token correction deliberately moved the visuals. Resolved by regenerating baselines via the Sprint 57.14 `playwright-e2e.yml` workflow_dispatch mechanism (baseline commit `f0b24bd2`); CI then green, `state: CLEAN`. The gap is a planning-discipline miss, not a code defect.

### 42. AD-Day0-Prong4-Visual-Baseline-Scope
Sprint 57.26 plan §Risks listed the "22-route blast radius" of changing `html` font-size but scoped it only to the sprint's own route-sweep harness — it missed CI's pre-existing Playwright `visual-regression.spec.ts` screenshot baselines. Day 0 三-prong Prong 4 (test selector verify) checks only **Vitest** specs asserting literal foundation values; it does not cover `tests/e2e/visual/*-snapshots/` PNG baselines, which are a second class of "asserts the visuals" test. Visual-baseline regen is a known pattern (Sprint 57.14 mechanism, used in 57.23 + 57.24) but was not pre-adopted into the 57.26 plan.

**Fix proposal**: extend `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 4 — when a sprint plan touches global CSS / foundation tokens / shell layout / any broad visual change, Day 0 must (a) `Glob tests/e2e/visual/**/*-snapshots/*.png` to confirm baselines exist + assess visual blast radius, and (b) if visuals will move, plan §Risks must pre-list "visual baseline regen via `playwright-e2e.yml` workflow_dispatch" as a known closeout step rather than a post-CI surprise.

**Cross-ref**: AD GHA-PR-create-blocked (line 131 — `playwright-e2e.yml` `gh pr create` step failed for the 3rd time across 57.23 / 57.24 / 57.26; the bot pushes the baseline branch fine but cannot open the PR, so the manual `fetch + ff-merge` is the working path). Effort: ~15 min rule edit; no code change.

---

## 🟢 Sprint 57.27 Overview Rebuild Carryover (NEW 2026-05-21)

2 ADs from Sprint 57.27 `AD-Mockup-Fidelity-Rebuild-Overview` closeout. `/overview` operator dashboard rebuilt 1:1 from `reference/design-mockups/page-overview.jsx` — 9 widgets, OverviewPage 728→~215-line assembly (AP-3 reversal complete), DRIFT-REPORT verdict PARITY. 8 of 9 widgets are fixture-backed (declared via `<BackendGapBanner>`); ActiveLoopsCard targets real data but its endpoint 404s.

### 43. AD-Overview-Backend-Extensions-Phase58
The 9 `/overview` widgets need real backend data. Currently 8 are fixture-backed (HITL Queue / Providers / Incidents / Error Trend / Cost Burn + the 4-stat KPI row), declared honestly via `<BackendGapBanner>`. ActiveLoopsCard targets real data via `useActiveLoops` → `fetchLoops` → `GET /api/v1/loops?status=running` — but that endpoint returns **404 (does not exist)**, so the widget always renders its error state in production (pre-existing; the hook + `loopsService` predate Sprint 57.27). Phase 58 scope: (a) build the `GET /api/v1/loops` list endpoint — closes ActiveLoopsCard live data + folds in D15 (`maxTurns` hardcoded; `Session` ORM enrich = existing `AD-Loop-Session-Enrich-Phase58`); (b) aggregation endpoints for HITL-queue / providers-health / incidents / error-trend / cost-burn / KPI stats. Pairs with cost-dashboard #36 + sla-dashboard #39 backend-extension ADs (same Phase 58+ backend-led batch).

### 44. AD-CardShell-Title-Crossverify-cost-sla
Sprint 57.27 R9 (user decision) changed the shared `CardShell` card-title `text-sm` → `text-[12.5px]` (closes D8 toward mockup `.card-title` 12.5px). `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) also consume `CardShell` → both shifted toward the mockup (they carried the same D8 drift unnoticed). Pure mockup-fidelity correction, NOT a regression — but a light Playwright pair-verify pass on those 2 pages should confirm the 12.5px title renders right. Fold into the next dashboard-touching sprint, or a small shared-primitive token-audit pass. ~15 min.

---

## 🟢 Sprint 57.28 Foundation-Switch Carryover (NEW 2026-05-22)

Sprint 57.28 `AD-Mockup-Fidelity-Foundation-Switch` switched the production frontend CSS delivery to the verbatim-CSS 4-layer sync protocol (Phase 1 — foundation only; Option B). The 22-route sweep verified 0 catastrophic / 0 structural regression. The Phase-2 per-page re-point epic (the `frontend-mockup-strict-rebuild` candidates #2 / #33-35 etc.) now re-points page markup on a **correct foundation** — CSS colour fidelity comes "for free" per re-point.

### 45. AD-RouteSweep-Object-Mock-Gap

NEW Sprint 57.28 D-DAY3-2. The `route-sweep.mjs` harness's generic `[]` API mock crashes the object-shaped data hooks of `/subagents`, `/memory`, `/verification` (AppErrorBoundary `undefined.length` — identically in before/ + after/ sweeps, so NOT a foundation-switch regression). Extend `route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents` + `/api/v1/memory/recent` + the verification endpoint (mirroring the Sprint 57.26 D-DAY1-1 `cost-summary` / `sla-report` object mocks) so those 3 routes become sweep-assessable. Harness maintenance ~1 hr; fold into a Phase-2 re-point sprint touching those pages.

### 46. AD-Mockup-Fidelity-HexBaseline-Migration

NEW Sprint 57.28. `check-mockup-fidelity.mjs` grep guard baselines `HEX_OKLCH_BASELINE = 18` — 18 hardcoded `bg-[#hex]`/`text-[#hex]` lines in the governance + chat_v2 risk-colour maps (DecisionModal / AuditChainBadge / ApprovalList / ApprovalCard / HITLTurn). Each Phase-2 re-point of those pages should migrate the literals to mockup `--risk-*` tokens and lower `HEX_OKLCH_BASELINE` accordingly. Not a standalone sprint — folds into the governance + chat-v2 re-point work.

---

## Maintenance Notes

- **Sprint-closeout append contract** (post REFACTOR-010, 2026-07-07): at closeout, the **full SHIPPED carryover block** goes to [`next-phase-candidates-shipped-archive.md`](next-phase-candidates-shipped-archive.md) (newest-first, same `## Sprint 57.X …` header). Into THIS file append only: (a) a 1-line row in §Shipped Sprints Pointer Index, and (b) the still-**open** ADs into §Open Carryover ADs. **Do NOT paste the full narration (file:line / drive-through / pytest counts / CHANGE-NNN / design note) here** — that is the REFACTOR-001/005/009/010 re-bloat anti-pattern (detail is single-sourced in the memory subfile + retrospective).
- New carryover ADs (open) are appended to §Open Carryover ADs here, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then flip its pointer-index row + move its narration to the archive.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail; `next-phase-candidates-shipped-archive.md` for verbatim closeout narration.

---

## Modification History

- 2026-07-07: REFACTOR-010 tier ① — 103 per-sprint SHIPPED carryover blocks (57.29→57.161) moved **verbatim** to `next-phase-candidates-shipped-archive.md`; replaced by §Shipped Sprints Pointer Index + §Open Carryover ADs; file 445 KB → ~155 KB (−66%). Zero deletion (moved, not deleted; also single-sourced in memory subfiles + retrospectives). Closeout append contract added (§Maintenance Notes) + sprint-workflow.md §Sprint Closeout self-check. See `claudedocs/4-changes/refactoring/REFACTOR-010-*.md`.
- 2026-05-22: Sprint 57.28 Day 4 closeout — verbatim-CSS foundation switch SHIPPED (22-route sweep 0 catastrophic / 0 structural regression); +2 ADs (#45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`); the Phase-2 per-page re-point epic now runs on a correct verbatim foundation
- 2026-05-21: Sprint 57.27 Day 3 closeout — `/overview` rebuild SHIPPED (DRIFT verdict PARITY); +2 ADs (#43 `AD-Overview-Backend-Extensions-Phase58` + #44 `AD-CardShell-Title-Crossverify-cost-sla`); RESOLVED #41 (rich-dashboard sub-class DROPPED — 57.27 `/overview` 4th `frontend-mockup-strict-rebuild` data point ratio ≈0.95 in-band; rich-subset 3-pt mean ~1.01 → no split, KEEP single 0.60 baseline)
- 2026-05-21: Sprint 57.26 post-closeout CI fix — +1 AD #42 (`AD-Day0-Prong4-Visual-Baseline-Scope`); PR #159's first CI run failed on 5 stale `visual-regression.spec.ts` baselines (foundation-token correction deliberately moved the visuals); baselines regenerated via `playwright-e2e.yml` workflow_dispatch (`f0b24bd2`), CI re-run green / `state: CLEAN`
- 2026-05-21: Sprint 57.26 Day 3 closeout — foundation-fidelity sprint (global token correction across 22 routes; user-directed insertion, NOT drawn from this candidate list) shipped with 0 regression; 0 new carryover ADs at closeout (later +1 AD #42 post-closeout CI fix — see entry above); 3 FOUNDATION-APPLIED routes folded into the existing rebuild epic per DRIFT-REPORT §5; #33/#34/#35 candidate sprint numbers shifted +1 (→ 57.27/57.28/57.29) + #41 4th-data-point sprint → 57.27 (foundation-fidelity took the 57.26 slot)
- 2026-05-19: Sprint 57.25 Day 3 closeout — close #32 (sla-dashboard rebuild SHIPPED) + +3 ADs (#39-#41) SLA Dashboard Rebuild carryovers (backend extensions + LatencyChart extraction trigger + rich-dashboard sub-class DEFER decision)
- 2026-05-19: Sprint 57.24 v2 Day 3 closeout — +7 ADs (#32-#38) Cost Dashboard Rebuild carryovers (4 page rebuilds 57.25-57.28 + 1 backend extension + 1 Playwright MCP recovery + 1 plan-draft Prong 5 discipline addition)
- 2026-05-19: Sprint 57.24 Day 0 — +1 AD #31 Memory STRUCTURAL Rebuild carryover (Q2 decision: defer from 57.24 cosmetic retrofit to dedicated Phase 58+ sprint)
- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
