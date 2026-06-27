# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

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

## 🆕 Sprint 57.143 Carryover — user Stop→continue durable interrupt-resume SHIPPED → **closes `AD-UserStop-Resume-Context`**

Sprint 57.143 (MERGED PR #339, main `3c1ce9c4`; branch from main `d7d97039`; CHANGE-110 + design note 47) closed the net-new `AD-UserStop-Resume-Context` gap (Scope B, full CC parity, user-prioritized). The interrupted-run `messages` ledger persisted nothing (per-append SAVEPOINT rode the request session → `get_db_session` rollback on the client-disconnect `CancelledError`). Fix: US-1 `DBMessageStore` own-session-per-call (ctor `session_factory` + `set_config('app.tenant_id')` for FORCE-RLS `messages` + immediate commit, mirrors `transcripts/retention.py`) → turn-0 prompt + completed tool batches durable; US-2 `cancel_session` persists a `[Request interrupted by user]` marker (best-effort own session) + chat-v2 Stop also `POST /cancel`. `loop.py` + `session_registry.py` UNTOUCHED; NO migration / wire stays 26 / NO mockup. Day-0 dropped synthetic tool_results (57.129 atomic-batch) + the cancel-handler DB dep (self-contained store). pytest 2881+5skip · mypy 0/381 · Vitest 922 · llm_sdk_leak 3/3. Drive-through PASS (real Azure gpt-5.2, session 35789e63): DB ledger seq5 durable essay prompt + seq6 marker; "continue" rehydrated 19 msgs → continued the ORIGINAL task (write_todos naming the computing essay), NOT "continue from what?". NEW calib class `chatv2-userstop-resume-durability` 0.60 (1st pt ~1.0 IN band, parent-direct).

**Carryover (Phase 58)**:
- **`AD-Loop-CancelEvent-Poll-Phase58`** — make the loop poll `cancel_event` (`session_registry.py:127`, currently set-but-never-polled) for a graceful in-process stop + in-flight LLM cancel (today the FE abort tears the run down; the marker covers transcript coherence).
- partial assistant-answer streaming capture on abort; `message_events` (57.125/126 replay ledger) disconnect durability; leading-assistant-marker guard for the sub-second Stop-before-turn-0 race (Azure lenient today).

---

## 🆕 Sprint 57.142 Carryover — OTel GenAI semantic-conventions span/attr mapping SHIPPED → **closes `AD-Observability-OTel-GenAI-Schema` (research #5)**

Sprint 57.142 **MERGED** (PR #337, main `54a7f1d3`; CI all-green; branch from `main` `3e9d069e`). A **translation-at-tracer** layer mapping V2's bespoke OTel span names + attribute keys to the CNCF GenAI semantic conventions (`gen_ai.*`). **Day-0 reframe** (the key finding): the research framed Cat 12 as a "self-authored wrapper" — but the OTel SDK is **already real** (`opentelemetry-*==1.22.0` + OTLP/Prometheus) → the gap is **only the bespoke schema** → a translation, NOT an adoption (scope collapsed like 57.125→126 / 57.134). **Latent bug found + fixed for free**: post-response token attrs (`loop.py`) never reached real exported spans (OTel snapshots at span start; only the by-reference test `RecordingTracer` saw them) → the close-time `set_attributes` re-read recovers them. NEW `_genai_semconv.py` (pure: stop_reason→finish_reason · span_type→operation · attr renames · `to_genai_span`/`assert_genai_conformant`) applied in `OTelTracer._span_cm` at start+close; **dual-view** (internal/test bespoke, exported `gen_ai.*`) → `loop.py` (1 line, decision B2) + existing obs tests UNTOUCHED. NEW `benchmark_otel_conformance.py` real `InMemorySpanExporter` harness (synthetic CI-safe + `--real` Azure) + corpus + 18 CI tests. pytest 2877+5skip (1 pre-existing `AD-Billing-Outbox-Drain-Test-Flake`, isolation-passes) · mypy src 0/381 · llm_sdk_leak 3/3 · NO migration / wire 26 / frontend / 17.md-contract. **Drive-through (real Azure gpt-5.2, `--real`)**: the production-path `chat gpt-5.2` span carries `gen_ai.operation.name`+`request.model`+`usage.input/output_tokens` (**latent bug FIXED on the real path**)+`response.finish_reasons`; `invoke_agent` conformant; `agent_loop.turn` exempt. GenAI **2/2 conformant 100%**. NEW calib class `otel-genai-semconv-spike` 0.60 (1st pt ~0.95-1.0 IN band, parent-direct). CHANGE-109 + design note 46. Detail: `memory/project_phase57_142_otel_genai_semconv.md`.

**Scope decisions (AskUserQuestion 2026-06-25)**: B2 allow 1 loop.py line (finish_reasons) · C1 defer content-capture.

**Follow-on (open, Phase 58)**:
- **`AD-Observability-Provider-Attr-Phase58`** — thread `gen_ai.provider.name` to the span (adapter→span plumbing > 1 line).
- **`AD-Observability-Content-Capture-OptIn-Phase58`** — opt-in `gen_ai.input/output.messages` flag (default off, truncate/hash; the C1 deferral).
- **`AD-Observability-Metrics-GenAI-Labels-Phase58`** — extend the gen_ai mapping to `record_metric` labels (this sprint = spans only).
- Optional: re-pin the CNCF semconv subset when more keys stabilize (cache tokens, `system`→`provider.name`).

---

## 🆕 Sprint 57.141 Carryover — pass^k reliability eval harness SHIPPED → **closes `AD-Eval-PassK-Reliability-Harness` (research #2)**

Sprint 57.141 **MERGED** (PR #335, main `041e9943`; CI all-green; branch from `main` `196d8892`). V2's first repeatability-measuring eval harness: a pure-offline `scripts/benchmark_pass_k.py` (mirrors `benchmark_judge.py`) running the SAME corpus input through V2's own `AgentLoopImpl.run()` **k times** and computing **4 axes** (user-picked over the recommended minimal 2): pass^k vs pass@1 (+divergence) · behavioral consistency (answer + tool-seq agreement) · fault injection (λ, `_FaultInjectingChatClient` wraps the `ChatClient` ABC) · perturbation (ε), with a **hybrid oracle** (rules inline normalized contains/exact + `LLMJudgeVerifier(profile.cheap, per-case-criterion raw template)`), over a 12-case difficulty-graded corpus. **3 NEW files, ZERO src edit** (WRAPS the existing `ChatClient`/`Verifier`/`AgentLoop` ABCs; loop is DB-less drivable per Day-0). 17 CI-safe unit tests (importlib + spy ChatClient driving the REAL loop offline + seeded rng). pytest 2859+5skip (the 1 fail = pre-existing `AD-Billing-Outbox-Drain-Test-Flake`, passes in isolation) · mypy src 380/0 · v2 lints 21 (incl. llm_sdk_leak) · NO migration / NO wire (stays 26) / NO frontend / NO `loop.py` edit. **Drive-through (real Azure gpt-5.2, 12 cases · k=3 · 90 runs · 94,373 tokens)**: pass^k 100% = pass@1 100% (**divergence 0% — corpus too easy to stress the τ-bench pass^8<25% regime; VALID verdict, either direction was acceptable**) BUT 2 pass@1-invisible signals surfaced — **answer-consistency 75%** (3/12 cases phrase differently across runs at 100% pass^k = "agent disagrees with itself") + **λ degradation 50%** (a 20% LLM-fault rate halves pass^k → no chat-level retry). NEW calib class `passk-reliability-spike` 0.60 (1st pt ratio ~1.0 IN band, parent-direct agent_factor 1.0). CHANGE-108 + design note 45. Detail: `memory/project_phase57_141_passk_reliability.md`.

**Follow-on (open)**:
- **`AD-Eval-PassK-Harder-Corpus-Phase58`** — add tool-heavy / longer multi-turn cases + k≥5 to reach the divergence regime (the reasoning corpus + k=3 + gpt-5.2 was too easy → 100%/100%; the harness is sound, the corpus is the lever).
- **`AD-Loop-ChatLevel-Retry-Phase58`** — the λ axis showed NO chat-call retry (pass^k 100%→50% at fault 0.2); evaluate a transient-classified chat retry (Cat 8).
- **`AD-Eval-Answer-Consistency-Surface-Phase58`** — attribute the 25% answer-inconsistency per-case (which 3? semantic vs cosmetic?).
- **`AD-Lint-RunAll-Stale-Path`** — CLAUDE.md + `sprint-workflow.md` reference `python scripts/lint/run_all.py` which does NOT exist; the v2 lints are pytest tests under `tests/unit/scripts/lint/` (stale-doc; Day-0 drift finding).

---

## 🆕 Sprint 57.138 Carryover — verification key-condition judge spike SHIPPED → **closes `AD-Verification-KeyCondition-PerTask` (research #8)**

Sprint 57.138 **PR-pending** (branch `feature/sprint-57-138-verification-key-condition` from `main` `57423a80`). Evidence-first thin spike: a NEW `key_condition.txt` judge template extracts the request's per-task must-satisfy conditions (count/format/ordering/inclusion) + checks each (superset of the generic `output_quality` floor), selectable via the EXISTING `chat_verification_judge_template` lever (env `CHAT_VERIFICATION_JUDGE_TEMPLATE` / per-tenant 57.106 C3), DEFAULT unchanged. **ZERO src code change** — `load_template`/`list_templates` GLOB `*.txt` (Day-0 found this → dropped the planned `__init__.py` edit); same `{output}`/`{trace}` placeholders + JSON contract → NO `llm_judge.py`/`VerificationResult` change. A permanent real-Azure A/B harness (`scripts/benchmark_key_condition.py` mirrors `benchmark_judge.py` + 11-case corpus + 9 CI-safe tests) measured: instruction_violation **83% (generic) → 100% (key_condition) = gain +16.67pp** BUT **false_positive_rate 20%** (1/5 acceptable over-flagged) + ~1.8× tokens → overall accuracy **tie 90.91%** → does NOT clear the gain≥30%/fp≤20% thresholds → **keep `output_quality` default; `key_condition` ships as a selectable opt-in**. Notable: the generic judge is less blind than theory (83% not ~0%) ∵ A3 trace-awareness already infers "asked 3, got 5 → contradicts-trace". Backend-only, NO migration / NO new wire event / NO frontend. pytest 2797+5skip (+11) · mypy 0/374 · run_all 10/10. **Drive-through PASS (兩者結合)**: chat-v2 real Azure gpt-5.2 — ARM A key_condition active ("exactly 3 colors"→"Red, blue, yellow"→verification_passed 0.99) + ARM B default ("capital of France"→"Paris"→verification_passed 0.99); the CATCH = the A/B harness (a real LLM complies on demand → can't force a UI catch, 57.136 honesty), the UI = selectability + no-regression. NEW calib class `verification-keycondition-spike` 0.60 (1st pt ~0.98 IN band). CHANGE-105 + design note 42. Detail: `memory/project_phase57_138_verification_key_condition.md`.

**Follow-on (open)**:
- **`AD-Verification-KeyCondition-TwoPhase-Phase58`** — a dedicated extract-then-check pipeline (closer to the literal EMNLP2024 method; only if a future A/B shows Option A's single-call gain is materially capped).
- **`AD-Verification-Conditions-Surface-Phase58`** — surface the structured conditions array (`VerificationResult.conditions` + SSE wire + Inspector render; the per-condition detail rides `reason` this sprint).
- **Larger / instruction-heavy A/B corpus + a no-trace generic arm** — isolate the key-condition contribution from A3 trace-awareness; the harness is permanent + re-runnable (thresholds parameterized).

---

## 🆕 Sprint 57.137 Carryover — sandbox detect→restrict spike SHIPPED → **closes `AD-Guardrail-Detect-To-Restrict` (research #3)**

Sprint 57.137 **MERGED** (PR #327, main `f47964ad`; CI all-green; branch from `main` `ba4c5c13`). Evidence-first thin spike: a permanent real-Docker escape harness (`scripts/benchmark_sandbox_escape.py` + 10-case corpus + 13 CI-safe tests) measured **regex_escape_rate 60% · docker_containment_rate 100%** (deny-list misses urllib/http.client/importlib-concat/asyncio/ftplib/smtplib; DockerSandbox `network none` contains all 10) → the regex is redundant-for-containment under Docker. Shipped: a Cat 2 `SandboxBackend.is_structurally_isolated` property (provider-neutral, not isinstance) + `_FailClosedSandbox` + `default_sandbox(require_isolation=...)` env-gated fail-closed (`SANDBOX_REQUIRE_ISOLATION`, DEFAULT OFF — dev/CI keep the SubprocessSandbox fallback; prod opts in) so a Docker-less host REFUSES rather than silently degrading; the regex detector reframed (ESCALATE-for-visibility, NOT the boundary; `check()` byte-unchanged → 23 risky tests green). Backend-only, NO migration / NO new wire event / NO frontend. pytest 2786+5skip (+21) · mypy 0/374 · run_all 10/10. **Drive-through PASS (兩者結合)**: backend runtime (real `_get_shared_sandbox`→`default_sandbox`→handler — ARM A require_isolation+Docker-unreachable → `_FailClosedSandbox` refusal, code NOT run; ARM B real Docker → `print(2+2)`→"4") + UI (chat-v2 real Azure gpt-5.2 → `print(31337*1337)` → HITL approve → real DockerSandbox → "41897569" + verification_passed 0.99 — no-regression). NEW calib class `guardrail-restrict-spike` 0.60 (1st pt ~0.97 IN band). CHANGE-104 + design note 41. Detail: `memory/project_phase57_137_sandbox_detect_to_restrict.md`.

**Follow-on (open)**:
- **`AD-SkillScript-Require-Isolation-Phase58`** — extend the `require_isolation` lever to `run_skill_script` / skills `_get_default_sandbox` (bundled non-LLM scripts, lower risk; the same gate can extend later).
- **`AD-Sandbox-PerTenant-Capability-Profile-Phase58`** — per-tenant network/fs isolation scope (was Option C; settings/env-only shipped — anti-AP-6).
- **Non-network Docker guarantees benchmarked independently** — read-only fs / cap-drop / non-root / no-bind-mounts are documented but only network egress was measured; the harness corpus is extensible (design note 41 §4).

---

## 🆕 Sprint 57.136 Carryover — verification correction-context hygiene spike SHIPPED → **closes `AD-Verification-Retry-Context-SelfConditioning` (research #6)**

Sprint 57.136 **MERGED** (PR #325, main `430f2434`; CI all-green; branch from `main` `074362c4`). Parameterized the in-loop verification correction branch (`loop.py:2645`) via `correction_context_strategy` ∈ {`keep` default = byte-identical / `summarize` = drop the failed answer to break self-conditioning}, wired through `CHAT_VERIFICATION_CORRECTION_STRATEGY` settings (config:142 → handler.py:673-676/705), + a permanent real-LLM A/B harness (`scripts/benchmark_correction_hygiene.py` + 10-case fixture + 15 CI-safe tests). **A/B verdict KEEP** (real Azure, 10 cases × 2 arms): repeat_error_rate −0.043 / tokens −17.2 / both arms 100% retry-pass → directionally real but **< 5% materiality threshold** → `keep` stays default, `summarize` env opt-in lever, #6 low-risk at the 2-turn horizon. Backend-only, NO migration / NO new wire event / NO frontend. pytest 2765+5skip (+18) · mypy 0/374 · run_all 10/10. Drive-through PASS (backend runtime: real handler→loop + controlled fail-once proved wiring + drop; UI: chat-v2 ×2 real Azure proved main-flow/gate/no-regression). CHANGE-103 + design note 40. Detail: `memory/project_phase57_136_verification_correction_hygiene.md`.

**Follow-on (open)**:
- **`AD-Verification-Correction-Strategy-PerTenant-Phase58`** — per-tenant `correction_context_strategy` via the C3 `harness_policy` seam (OUT this sprint — anti-AP-6; settings/env-only shipped).
- **Self-conditioning at >2 correction turns + production-distribution magnitude** — the harness is permanent + re-runnable on a larger / adversarial fixture if a future sprint wants a tighter number (design note 40 §4).

---

## 🆕 Sprint 57.135 Carryover — scheduled transcript-retention background job SHIPPED → **closes 57.134 follow-on #1**

Sprint 57.135 **MERGED** (PR #317, main `d5a572c2`; CI all-green; branch from `main` `c98b6368`). A scheduled background job auto-enforces per-tenant transcript retention: `run_transcript_retention_sweep` (enumerate all tenants → per-tenant `apply_transcript_retention` + audit + commit, fail-open) in `retention.py` + `_transcript_retention_poll_loop`/`_start_transcript_retention_job` + lifespan startup/shutdown wiring in `api/main.py`, mirroring the billing-outbox drainer. **DEFAULT OFF** (destructive opt-in via `TRANSCRIPT_RETENTION_JOB_ENABLED`, vs billing default-ON; interval `TRANSCRIPT_RETENTION_JOB_INTERVAL_S` default 86400). Backend-only, NO migration. +6 tests. mypy 0/374 · run_all 10/10 · pytest 2747+5skip (+6). **Drive-through PASS** (real backend PID 43144 + real DB; background job = runtime verification, no UI): startup sweep `tenants=5000 failed=0 messages_deleted=1`, throwaway tenant MESSAGES 2→1 + SCHEDULED_AUDITS=1, default-OFF re-confirmed. NEW class `scheduled-job-mirror-spike` 0.55→0.85 (1st pt ~1.4-1.5 over; ceremony-not-code-accelerated). CHANGE-102, no design note. (This branch also carries the subagent-AD-closure docs as commit 1.) Detail: `memory/project_phase57_135_scheduled_transcript_retention.md`.

- ~~transcript retention 57.134 follow-on #1 (scheduled job)~~ ✅ **CLOSED Sprint 57.135**.
- **Remaining 57.134 follow-ons**: (2) partition lifecycle — pg_partman + default partition (Ops slice); (3) FE Tenant Settings retention tab (frontend slice).
- **Observation** (non-blocker): one sweep over 5000 dev tenants took ~44s (per-tenant session+commit); fine for the daily cadence, batch optimization deferred. Possible `Tenant.state`-aware skip (skip suspended) deferred.
- Open (separate, subagent diagnostic 2026-06-17): TEAMMATE/HANDOFF-mode Tree relay verification (only `fork` driven). Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (did NOT surface).

---

## 🆕 Sprint 57.134 Carryover — per-tenant transcript retention (apply + preview) SHIPPED → **closes the transcript-retention (57.125) Option-A slice**

Sprint 57.134 **MERGED** (PR #314, main `42afc8c6`; CI all-green; from `main` `631f599a` post-#313). User-picked (2026-06-17: the OTHER item from "Inspector token-sweep leg、transcript retention(57.125)"; Option A "config + manual apply"). **Day-1 pivot** (user-approved AskUserQuestion "Pivot + 補一個 GET apply-preview"): a Day-1 read found `Tenant.retention_days` ALREADY EXISTS (Sprint 57.46 SaaS settings, settable via PATCH `/tenants/{id}`) → the planned `meta_data["transcript_retention"]` was a parallel config (AP-6) → DROPPED. Shipped = enforcement on the canonical column: `apply_transcript_retention(db, tid, retention_days, *, now, dry_run)` (DELETE-by-age on `messages`+`message_events`, `SET LOCAL app.tenant_id` for FORCE'd RLS + explicit `WHERE tenant_id`) + POST `/{id}/transcript-retention/apply` + GET `/{id}/transcript-retention/preview` (dry-run COUNT). Backend-only, NO migration. +10 tests (3 unit + 7 integration incl. multi-tenant isolation + audit). mypy 0/374 · run_all 10/10 · pytest 2741+5skip (+10). **Drive-through PASS** (real uvicorn PID 55768 + real admin auth dan@acme.com + real DB): preview on acme-prod (non-destructive, config-responsive) + apply on a throwaway tenant (destructive: deleted 1/1, recent survived, REMAINING_MESSAGES=1). NEW class `transcript-retention-apply-spike` 0.60 (ratio ~1.0-1.1 IN band). CHANGE-101 + design note 39. Detail: `memory/project_phase57_134_transcript_retention.md`.

- ~~transcript retention (57.125)~~ ✅ **Option A CLOSED Sprint 57.134** (apply + preview on canonical `tenants.retention_days`).
- **NEW follow-ons**: (1) ~~scheduled background retention job~~ ✅ **CLOSED Sprint 57.135**; (2) partition lifecycle — pg_partman activation + default partition (Option D / Ops; post-2026-06 write gap) [deferred]; (3) FE Tenant Settings retention tab (surface retention_days + preview/apply) [deferred].
- **NEW candidate rule**: Day-0 Prong-2 — grep the CONCEPT (e.g. `retention`) not just the proposed storage key when adding a per-tenant config (the AP-6 parallel-config trap; this sprint's pivot evidence; kin to the `AD-Day0-Prong2-WriteSide-Resource-Storage-Grep` family).
- ~~`AD-ChatV2-Resume-Replay-Drive-Through`~~ ✅ **CLOSED 2026-06-17** (follow-up drive-through, no code — the `escalate_output_phrases` admin surface already existed; see the 57.132 block below + `sprint-57-132/artifacts/drivethrough-leg2-output-escalate-PASS.md`). Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface).

---

## 🆕 Sprint 57.133 Carryover — chat-v2 Inspector Turn tab token-sweep SHIPPED → **fully closes `AD-ChatV2-Inspector-Turn-Metadata-Wire`** (3/3 legs; drive-through PASS, real Azure cache hit)

Sprint 57.133 **MERGED** (PR #312, main `e8440ad6`; from `main` `3e8ee330` post-#311). User-picked (2026-06-17 "現在開始執行 Inspector token-sweep leg、transcript retention(57.125)" — the first-listed item). The Inspector Turn tab showed `tokens.in/out/thinking` but not per-turn prompt-cache economics. The data was ALREADY on the wire (`llm_response.cached_input_tokens`, Sprint 57.65/57.108; in `generated/loopEvents.generated.ts:43`) → FE-only (3 src + 4 test edits, NO backend/wire/codegen/migration): `AgentTurn += cachedInputTokens: number|null` + `turn_start` init + `llm_response` 0-guard capture (mirrors 57.108 tokensIn) + 2 `InspectorTurn` KV rows — `tokens.cached` + a DERIVED per-turn `cache_hit` = round(cachedInputTokens / tokensIn × 100)% (no new store state; the wire's `loop_end.cache_hit_rate` is cumulative, this is per-turn). Docstring KV count corrected 8→12 (57.120/57.131 drift). +4 Vitest (2 store capture + 2 render). Carve-out: "actual vs estimate" dual-display (actual already overwrites the estimate). Gates: Vitest 915 (+4) · lint/build clean · mockup 51 byte-identical (0 new oklch) · tsc 0 · backend UNTOUCHED. **Drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, jamie@acme.com/acme-prod): turn 1 "capital of France?" → "Paris" Inspector `tokens.cached —` / `cache_hit —` (first request, no prior prefix → 0-guard honest "—"); turn 2 "its population?" → "…2.1 million…" Inspector **`tokens.cached 2,048`** / **`cache_hit 83%`** (re-sent ~2,435-token prefix → real Azure prompt-cache hit; 2048/2458 = 83% self-consistent; turn-varying real values, not fixture). NEW class `chatv2-inspector-existing-field-surface` 0.85 **3rd data point** ratio ~0.94-1.03 IN band → KEEP 0.85 (3-pt mean ~0.87 VALIDATES the class). CHANGE-100, NO design note. Detail: `memory/project_phase57_133_chatv2_inspector_token_sweep.md`.

- ~~**`AD-ChatV2-Inspector-Turn-Metadata-Wire`**~~ ✅ **CLOSED Sprint 57.133** (token-sweep leg; all 3 legs done — active_skill 57.120 + model 57.131 + token-sweep 57.133). `AD-ChatV2-Inspector-Cost-InStream` carve-out stands (cost stays honest "—", post-loop by design; YAGNI).
- **Bucket-C remaining (the only item left)**: transcript retention (57.125) — the OTHER user-named item; a backend retention/cleanup infra slice → next sprint per rolling discipline.
- ~~`AD-ChatV2-Resume-Replay-Drive-Through`~~ ✅ **CLOSED 2026-06-17** (follow-up drive-through, no code). Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface — FE-only).

---

## 🆕 Sprint 57.132 Carryover — chat-v2 resume-path ledger persistence SHIPPED → **closes `AD-ChatV2-Resume-Tool-RoundTrips`** (57.129 carryover) + the sibling held-answer gap (Leg-1 drive-through PASS; Leg-2 unit+gate honest)

Sprint 57.132 **MERGED** (PR #310, main `f2e243a1`; from main `75b177c0` post-#309). The HITL **resume path** (`loop.resume()`) appends its out-of-loop messages to the buffer but never persisted them to the `messages` Cat-3 ledger (the 57.129 send-path persist lives INSIDE `_run_turns`) → a follow-up after a HITL resume rehydrated an incomplete conversation. **User picked the comprehensive scope** (both legs). Fix (PURE backend, 1 src EDIT `loop.py` + 1 test EDIT): **Leg-1** in `resume()` tool-kind APPROVED (after the `tool` result append) — backward-scan `_resume_asst_idx` = last `role=="assistant"` → `await self._persist_to_ledger(messages[_resume_asst_idx:], turn_num=turn_count)` (one atomic `[assistant tool_use, *tool results]` batch mirroring 57.129; reached ONLY on APPROVED+exec → REJECTED/undecided return earlier → dangling-free); **Leg-2** in `_replay_approved_output` (after `yield Thinking`) — `if answer_text: await self._persist_to_ledger([Message(role="assistant", content=answer_text)], turn_num=turn_count)` (covers output 57.93 + verification 57.99-A2 APPROVE). `_persist_to_ledger` docstring generalized. NO new ABC/event/wire 24/codegen/migration/frontend; reuses `DBMessageStore.append` + `message_serde`. +4 unit tests (`RecordingMessageStore` + `message_store` param on `_build_resume_loop`). mypy 0/372 · run_all 10/10 (wire 25) · pytest 2731+5skip (+4) · Vitest/mockup UNTOUCHED. **Leg-1 FULL drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, dan@acme.com/acme-prod, session `02fa6bfb`; PUT hitl-policies auto=LOW/require=MEDIUM so python_sandbox ESCALATEs): python_sandbox → HITL pause → Approve & continue → resume → "ODD"; DB `messages` ledger 4 rows incl. **seq-2 assistant tool_use + seq-3 tool result persisted AT RESUME** (the fix); follow-up "what was the tool's `duration_seconds`?" → **"0.031"** (un-deducible from "ODD"; rehydrated from seq-3) → end-to-end rehydration proven, messages_count 4→5→8. **Leg-2 unit + composition verified, NOT UI-driven** (the real-LLM output-escalate trigger via the default `confidential` phrase did NOT fire — non-deterministic / Azure content-filter-prone; verified by 2 unit tests on the REAL `resume()`→`_replay_approved_output`→persist path + the persist primitive runtime-proven by Leg-1; honest gate-only label per the Drive-Through constraint). NEW class `chatv2-resume-ledger-persist-wiring` 0.70→0.85 (1st pt ratio ~1.4-1.6 over; ceremony-not-code-accelerated like 57.120/122/123/126/129). CHANGE-099, NO design note. First sprint drafted from the REFACTOR-008 frozen templates. Detail: `memory/project_phase57_132_chatv2_resume_ledger_persist.md`.

- ~~**`AD-ChatV2-Resume-Tool-RoundTrips`**~~ ✅ **CLOSED Sprint 57.132** (Leg-1, drive-through PASS). The sibling held-answer gap (Leg-2) also fixed (unit+gate verified).
- ~~**`AD-ChatV2-Resume-Replay-Drive-Through`** (🟡)~~ ✅ **CLOSED 2026-06-17** via a follow-up drive-through (NO code). The premise was WRONG — the per-tenant `escalate_output_phrases` admin surface ALREADY EXISTS (`PUT /admin/tenants/{id}/harness-policy`, `tenants.py:1671`; resolved + wired at `handler.py:588-642`); setting it to the benign `paris` (vs the content-filter-prone `confidential`) gave a deterministic output-escalate trigger. Drove real chat-v2 UI + real Azure + real DB (session `e0ec3410…`): output-escalate pause → Approve → `_replay_approved_output` delivered `Paris` AND persisted it to the `messages` ledger AT RESUME (`seq=2`); follow-up "letters?" → `5` proved rehydration. Evidence: `sprint-57-132/artifacts/drivethrough-leg2-output-escalate-PASS.{md,jpeg}`. **Lesson (reinforces 57.134 + the candidate Day-0 rule)**: grep the CONCEPT not the proposed storage key — the controllable surface already existed.
- Bucket-C remaining (separate slices): Inspector turn metadata token-sweep leg (57.120), transcript retention (57.125). (`AD-ChatV2-HITL-Card-Tool-Name` was already CLOSED by 57.108 — `approval_requested` carries `tool_name`/`reason`; removed from the pool.) Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface).

---

## 🆕 Sprint 57.131 Carryover — chat-v2 Inspector Turn tab `model` row SHIPPED → **closes the `model` row leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire`** (the 57.120 carryover; drive-through PASS)

Sprint 57.131 **MERGED** (PR #309, main `75b177c0`; from main `eef15c5e` post-#308). User-picked from bucket-C (over Resume-Tool-RoundTrips / HITL-Card / transcript-retention). The Inspector Turn tab showed `trace_id`/`tokens`/`cost`/`active_skill` but not the model that ran the turn; the model was store-captured (`currentModel` from `llm_request.model`, the ChatHeader badge — CHANGE-054) but session-latest only, not per-turn. FE-only, mirrors the 57.120 `active_skill` row: `AgentTurn += model: string | null` + per-turn capture in the EXISTING `llm_request` `mergeEvent` updater (init `model: null` at `turn_start`; capture-at-`llm_request`-not-`turn_start` because turn_start fires first) + a `<KV k="model" v={lastAgent.model ?? "—"} mono />` row in InspectorTurn (after `cost`, before `active_skill`; reuse `KV` → 0 new CSS/oklch, mockup 51 byte-identical). NO backend/wire/codegen/migration (`llm_request.model` already on wire — 25 unchanged). full Vitest 911 (+3) · build/lint clean · backend gates UNCHANGED (zero backend diff). **Drive-through PASS** (real Azure, jamie@acme.com/acme-prod): Inspector Turn tab `model = gpt-5.2`, matches the ChatHeader badge (×3 in body). Day-0 caught the required-field tsc ripple (+2 test factories the plan missed). Calib `chatv2-inspector-existing-field-surface` 0.85 **2nd data point** ratio ~0.82-0.93 IN band → KEEP 0.85. CHANGE-098, NO design note. Detail: `memory/project_phase57_131_chatv2_inspector_model_row.md`.

- **`AD-ChatV2-Inspector-Turn-Metadata-Wire` token-sweep leg** (🟢, still open) — actual `input_tokens` vs the `tokens_in` estimate + `cached_input_tokens` + `cache_hit_rate` per turn. + **`AD-ChatV2-Inspector-Cost-InStream`** carve-out (cost stays honest "—", post-loop by design; YAGNI).
- **`AD-ChatV2-HITL-Card-Tool-Name` (57.106) → REMOVE from the pool** — confirmed **already-closed by 57.108** during this sprint's slice-selection (the `approval_requested` wire carries `tool_name`/`reason` since 57.108; `mergeEvent` sets `tool: ev.data.tool_name ?? "—"` + `rationale: ev.data.reason`). Stale carryover.
- Bucket-C remaining (as of 57.131; `AD-ChatV2-Resume-Tool-RoundTrips` since CLOSED by 57.132 — see block above): transcript retention (57.125). Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface — FE-only).
- **Process (REFACTOR-008, interleaved per user observation)**: sprint plan/checklist format had drifted (49.1 freeform → 51.2/52.1 §0-9 中文 → 57.107-130 英文 giant-H1 + dense §0; root cause = the 鐵律's relative "mirror most-recent sprint" anchor → monotonic ratchet). Froze `claudedocs/templates/sprint-{plan,checklist}-template.md` + re-anchored the 鐵律 (sprint-workflow.md + CLAUDE.md) relative→absolute. 57.131 = first sprint mirroring the frozen template. See `REFACTOR-008`.

---

## 🆕 Sprint 57.130 Carryover — chat-v2 LoopTerminated wire surface SHIPPED → **closes `AD-LoopTerminated-Wire-Surface`** (the 57.110 carryover; drive-through PASS)

Sprint 57.130 **MERGED** (PR #307, main `d92c327b`; from main `b9334946` post-#306). A FATAL terminate's Cat-8 `LoopTerminated` event was dropped at `serialize_loop_event` (`NotImplementedError`) → silent stream end → stuck pending tool chip + no reason. Cross-stack surfacing of the EXISTING event: `sse.py` serializer branch (mirrors `tripwire_triggered`) + `WIRE_SCHEMA` `loop_terminated` (24→25) + codegen regen (`loopEvents.generated.ts` + `KNOWN_LOOP_EVENT_TYPES`) + `mergeEvent` `loop_terminated` case (flip dangling pending `ToolBlock`→error = the stuck-chip fix + record `turn.terminated` + chat `status:"completed"` = composer unfreeze) + `AgentTurn` `terminated · {reason}` `.badge.danger` (reuses existing class → 0 new CSS / 0 new oklch, mockup 51 byte-identical). NO new backend primitive / contract / migration. mypy 0/372 · run_all 10/10 (wire 25) · pytest 2727+5skip · Vitest 908 (+4) · build/lint clean. **Drive-through PASS** (real Azure gpt-5.2, jamie@acme.com/acme-prod): `web_search` + unset `BING_SEARCH_API_KEY` → `WebSearchConfigError` → unregistered → FATAL → `LoopTerminated(fatal_exception)` mid-tool → UI flipped the pending web_search chip to error (output `terminated: fatal_exception`) + rendered `terminated · fatal_exception` + unfroze the composer. 2 Day-0-missed drifts (codegen `WIRE_TYPE_TO_INTERFACE` map + 3 hardcoded count-test locations → "adding a wire type" Day-0 lesson). NEW class `chatv2-fatal-terminate-wire-surface` 0.55 (ratio ~1.29 over; drive-through-trigger-hunt the variance). CHANGE-097, NO design note. Detail: `memory/project_phase57_130_chatv2_loop_terminated_wire_surface.md`.

- No NEW carryover from the feature. Deferred follow-on: a richer mockup-authored `TerminatedBlock` (the minimal danger badge is the real fix); the resume-path terminate surfacing. Bucket-C remaining (separate slices): `AD-ChatV2-Resume-Tool-RoundTrips` (57.129), `AD-ChatV2-HITL-Card-Tool-Name` (57.106), Inspector turn metadata (57.120), transcript retention (57.125). Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface).

---

## 🆕 Sprint 57.129 Carryover — chat-v2 ledger intra-turn tool round-trips SHIPPED → **closes `AD-ChatV2-Ledger-Tool-RoundTrips`** (the 57.127 carryover; drive-through PASS)

Sprint 57.129 **MERGED** (PR #305, main `c2bcad09`; from main `858bd3af` post-#304). 57.127's `messages` Cat-3 ledger persisted ONLY the user prompt + final answer → a follow-up rehydrated `[user, final-answer]` but NOT the intra-turn `assistant tool_use` + `tool` result → a user couldn't reference a prior tool result. **User picked Option A** (incremental per-turn-batch persist) over Option B (end-of-run slice) + **defer resume() pending-tool**. Fix (PURE backend, 1 src EDIT `loop.py` + 1 test EDIT): in `_run_turns`'s `TOOL_USE` branch, `_tool_batch_start = len(messages)` before the assistant append (`:2777`) + `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` after the post-tool checkpoint (`:3072`) — one atomic batch reached ONLY when the round-trip is well-formed (every early-return path skips it → dangling-free). Reuses `DBMessageStore.append` + `message_serde`; NO new helper/ABC/event/wire 24/codegen/frontend/migration; final answer still end_turn-only (57.127, untouched); `_persist_to_ledger` docstring updated. +3 unit tests (persist / atomic single-`append` batch / prior-round-trip rehydrates into LLM request[0]) 6/6. mypy 0/372 · run_all 10/10 · pytest 2727+5skip (+3) · Vitest 904 / mockup 51 UNCHANGED. **Drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, dan@acme.com/acme-prod, session `9150a32f`; clean-restart PID 40596; SET acme-prod HITL `auto=MEDIUM/require=HIGH` so python_sandbox auto-runs in-loop, avoiding the resume() deferred path): turn 1 "run `random.randint(100000,999999)`, reply EVEN/ODD" → `stdout=333221` → "ODD" (number NOT in the answer); turn 2 innocent "add 7 to that number" → **"333228"** (= 333221 + 7; turn-2 POST sends only `{message, session_id}` → the number could ONLY come from the backend self-loading the rehydrated tool result); DB `messages` 6 rows incl. seq-2 assistant tool_calls=python_sandbox + seq-3 tool `{"stdout":"333221..."}`. **FALSE-ALARM lesson**: a first session's empty follow-ups looked like a "rehydrating-tool-round-trip-breaks-follow-up regression" but root-caused (backend log 212) to Azure content-filter `jailbreak` 400 on adversarial recall prompts ("disregard/do-not-reveal/recall-don't-run-tool") — a no-tool control follow-up (Paris→population) worked + innocent prompts work; NOT the change. NEW class `chatv2-ledger-tool-roundtrips-wiring` 0.55→0.85 (ratio ~1.9 over; drive-through + HITL-setup + content-filter investigation dominated; ceremony-not-code-accelerated like 57.120/122/123/126). CHANGE-096, NO design note (continuation). Detail: `memory/project_phase57_129_chatv2_ledger_tool_roundtrips.md`.

- **NEW** `AD-ChatV2-Resume-Tool-RoundTrips` (🟡) — resume()'s pending-tool observation is appended BEFORE driving `_run_turns` → not captured by the `TOOL_USE`-branch marker → a HITL-paused-then-approved tool's round-trip isn't persisted to the `messages` ledger. Niche HITL path; deferred (distinct from the SHIPPED `AD-ChatV2-Resume-Transcript-Persistence` `message_events` work). Still open: `AD-Billing-Outbox-Drain-Test-Flake` (intermittent Risk Class C billing flake); deferred infra (`message_events`/`messages` canonical-ledger consolidation, pg_partman, `turn_num` cross-send counter).

---

## 🆕 Sprint 57.128 Carryover — chat-v2 resume transcript persistence SHIPPED → **closes `AD-ChatV2-Resume-Transcript-Persistence`** (the pre-existing 57.125 gap; drive-through PASS)

Sprint 57.128 **PR-pending** (branch `feature/sprint-57-128-chatv2-resume-transcript-persistence`, from main `5ddc11cc`). The HITL resume generator `_stream_resume_events` (`router.py:1201-1223`, a "thin mirror") drove `loop.resume()` + yielded SSE bytes but NEVER called `_persist_main_event` like its send-path sibling → a paused-then-resumed session's replay stopped at the pause. **User picked minimal scope** (persist post-resume loop events only; approve/reject decision stays in `approvals` + audit-log — no new event type). The 57.127 `messages` Cat-3 ledger ALREADY covered resume; only the `message_events` SSE-replay ledger was missing. Fix (PURE backend, 1 file EDIT `router.py` + 1 test): thread `db`/`tenant_id`/`session_id` into `_stream_resume_events` + persist each post-resume event via `_persist_main_event` (seq seeded from `_max_main_seq` → continues past the pre-pause events, the 57.126 ordering; NO `user_message` row; best-effort). Day-0 settled the `_max_main_seq` arg-order the 2 Explore agents disagreed on = `(db, tenant_id, session_id)`. NO new event type / wire / codegen / frontend / migration; `loop.py` untouched. mypy 0/372 · run_all 10/10 · pytest 2724+5skip (+4) · Vitest 904 / mockup 51 UNCHANGED. **Drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, session `b78cb63d`; dan@acme.com admin set acme-prod HITL require=MEDIUM, python_sandbox MEDIUM escalates): pause → Approve & continue → 42 live → reload → click session → COMPLETE replay (user prompt → python_sandbox → "Decision: APPROVED" card → 42 → verification); `/events` = 40 events seq 1→40, post-resume seq 20-40 = the fix (approval_received → tool_call_result=42 → verification_passed → loop_end). NEW class `chatv2-resume-persistence-wiring` 0.55 (ratio ~1.13 IN band, parent-direct; the HITL drive-through setup is the cost driver). CHANGE-095, NO design note (continuation). Detail: `memory/project_phase57_128_chatv2_resume_transcript_persistence.md`.

- No NEW carryover from this sprint. (`AD-ChatV2-Ledger-Tool-RoundTrips` (57.127) → CLOSED by Sprint 57.129, see block above.) Still open: `AD-Billing-Outbox-Drain-Test-Flake` (intermittent Risk Class C billing flake); deferred infra (`message_events`/`messages` canonical-ledger consolidation, pg_partman).

---

## 🆕 Sprint 57.127 Carryover — chat-v2 live multi-turn context SHIPPED → **closes `AD-ChatV2-Live-MultiTurn-Context`** (the real product bug the 57.126 drive-through surfaced; drive-through PASS)

Sprint 57.127 **MERGED** (PR #303, main `5ddc11cc`, gh-verified MERGED, CI all-green first-run). The 57.126 drive-through found a follow-up send started `loop.run()` with no prior turns → "its population?" → "what is 'it'?". **User picked Approach A** (new `messages`-table writer over lossy B / O(turns²) C). A NEW provider-neutral `MessageStore` ABC (sibling to `Checkpointer`, bound to session+tenant) + `DBMessageStore` (load order-by-seq / append seq-from-MAX / best-effort SAVEPOINT / tenant-scoped 鐵律) + serde relocated to `_contracts/message_serde.py` (circular-import safety); the loop **self-loads** prior at `run()` start + persists user-prompt-at-start + final-answer-at-2-end_turn-sites; **`loop.run()` ABC signature UNCHANGED** (no caller ripple); `make_chat_message_store` factory + `build_handler` injects the MAIN loop only (child loops none). Pure backend; NO migration (default partitions exist `0028`); wire 24. **Day-1 de-risk**: dropped the plan's compaction-immune side-list (the FINAL branch yields end_turn WITHOUT appending the answer to `messages`) → a simpler 2-point persist (user + final answer). mypy 0/372 · run_all 10/10 · pytest 2720+5skip (+8) · Vitest 904 / mockup 51 UNCHANGED. **Drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, session `9e89775d`): turn 1 "capital of France?" → "Paris" (`messages_count=4`) → turn 2 "its population?" → "Paris ~2.1M" (`messages_count=6` = 4 +2 rehydrated) → resolved "its"→Paris; DB ledger 4 rows seq 1→4 monotonic. NEW class `chatv2-multiturn-rehydration-spike` 0.60 (ratio ~0.98 IN band, parent-direct). CHANGE-094 + design note 38 + 17.md `MessageStore` registered. Detail: `memory/project_phase57_127_chatv2_live_multiturn_context.md`.

- **`AD-ChatV2-Ledger-Tool-RoundTrips`** (🟡, NEW) — this slice persists ONLY the user prompt + final answer; intra-turn assistant/tool messages within a turn are NOT in the `messages` ledger. A follow-on slice to persist the full per-turn message sequence (needs care to avoid dangling-tool_call rows on a partial/failed turn — the reason the 2-point persist was chosen this slice). Needed for full tool-context multi-turn (e.g. "re-run that search" referencing a prior tool result).
- ~~**`AD-ChatV2-Resume-Transcript-Persistence`**~~ ✅ **SHIPPED Sprint 57.128** — `_stream_resume_events` now mirrors the send-path `_persist_main_event` so the post-resume transcript persists to `message_events` (the resumed-session replay is complete). See the 57.128 carryover block at top + CHANGE-095.
- **`AD-Billing-Outbox-Drain-Test-Flake`** (🟢, NEW — observed during the 57.127 final gate) — `tests/integration/billing/test_billing_outbox_drain.py::test_drain_materializes_cost_ledger_parity` is an intermittent Risk Class C flake (passes isolated + adjacent + on full re-run; the full-suite 1st run failed it once non-deterministically). Pre-existing (billing untouched by 57.127); the 2 new 57.127 test files only shifted collection order (FIX-032 pattern). Fix = an autouse cost_ledger / billing-outbox-drainer singleton reset (per Risk Class C / FIX-032 precedent). If CI hits it → re-run CI (do NOT skip the test).
- Deferred infra (carried): `message_events`/`messages` consolidation (canonical-ledger AD); pg_partman partition automation; `turn_num` cross-send counter (cosmetic — ordering is via `sequence_num`).

---

## 🆕 Sprint 57.126 Carryover — chat-v2 session history replay (arc slice 2/2: complete the backend transcript foundation + the frontend click→replay) SHIPPED → **closes `AD-ChatV2-Session-History-Replay-Phase58` → the 2-sprint arc (57.125+126) is COMPLETE** (drive-through PASS)

Sprint 57.126 **MERGED** (PR #301, main `d4f1a580`). Day-0 三-prong flipped the sprint frontend-only → full-stack (2 AskUserQuestions): the 57.125 foundation was **incomplete** — user prompts are persisted NOWHERE (`loop_start`/`turn_start`/`llm_*` carry no user text; the prompt is a client-side `pushUserMessage`; `state_data` EXCLUDES messages per `checkpointer.py:217`; the `messages` table has no writer; only HITL-pause stashes messages in `durable.metadata` as a spike shortcut) → a pure-FE replay would lose the user's questions. **Option C (interleave from `/state`) proved non-viable** (no messages in state_data). **User picked Option B**: complete the backend writer. Also caught + fixed a latent 57.125 **multi-turn `main_seq` collision** (`router.py:675` reset to 0 per request → ≥2-send sessions collide on `sequence_num`). Backend (`router.py`): `_max_main_seq` seeds `main_seq` from `MAX(sequence_num)` (globally monotonic per session) + persist the inbound user prompt as a `user_message` `message_events` row FIRST per send (persist-only — never yielded live; reuses `_persist_main_event`; sits before `loop_start` so the 57.116/120 active_skill stamping reconstructs on replay). Frontend: `fetchSessionEvents` + `UserMessageEvent` (hand-written persist-only — NOT codegen; wire 24) + `loadSessionHistory` (conversation-only reset → replay through the EXISTING `mergeEvent` + a new `user_message` case) + the `SessionList` click rewire. ZERO new CSS (mockup 51 byte-identical), no migration/codegen. mypy 0/370 · run_all 10/10 · pytest 2712+5skip (+1) · Vitest 904 (+9). **Drive-through PASS** (real Azure gpt-5.2): a 2-turn chat (session `d5bd3950…`) → `/events` 34 events / 2 user_message rows / seq 1..34 monotonic → reload (fresh store) → click → COMPLETE replay (user prompts + agent turns + verification + trace, AP-4 clear) → a follow-up continued the SAME session (`/events` 51 events / 3 user_message rows / seq 1..51 monotonic). NEW class `chatv2-history-replay-fullstack` 0.60→**0.85 re-pointed**. CHANGE-093, NO design note. Detail: `memory/project_phase57_126_chatv2_session_history_replay.md`.

- ~~**`AD-ChatV2-Session-History-Replay-Phase58`** (frontend half)~~ ✅ **SHIPPED Sprint 57.126** — the click→fetch→replay→continue, complete with the backend user_message persist + the multi-turn ordering fix. **The 2-sprint arc is COMPLETE.** See CHANGE-093.
- **`AD-ChatV2-Resume-Transcript-Persistence`** (🟢, NEW) — the resume path (`router.py:1175` `loop.resume`) doesn't persist main events (pre-existing 57.125 gap); a HITL-resumed session replays only up to the pause. A follow-on AD.
- ~~**`AD-ChatV2-Live-MultiTurn-Context`**~~ ✅ **SHIPPED Sprint 57.127** — the `messages` table got a writer (Approach A): a NEW `MessageStore` ABC + `DBMessageStore`; the loop self-loads prior at `run()` start + persists user-prompt + final-answer; the follow-up now carries prior context (drive-through: turn 2 "its population?" → "Paris ~2.1M"). See the 57.127 carryover block at top + CHANGE-094 + design note 38.
- **`AD-ChatV2-Transcript-Volume-Filter`** (🟢) + **`AD-ChatV2-Transcript-Retention`** (🟢, Phase 58+) — carried from 57.125 (still open).
- Inherited: `AD-ExecutionContext-ExplicitApproval-Tidy` (57.124) + other C-class / chrome Potemkin + the operator-portal drive-through audit backlog.

---

## 🆕 Sprint 57.125 Carryover — chat-v2 session history replay (arc slice 1/2: backend SSE transcript persistence + replay endpoint) SHIPPED (gate + live probe; closes the backend half of NEW `AD-ChatV2-Session-History-Replay-Phase58` + resolves stale `AD-ChatV2-SessionList-Backend`)

Sprint 57.125 **MERGED**. **Day-0 re-scope**: `AD-ChatV2-SessionList-Backend`'s literal scope (the session-LIST backend) was ALREADY shipped by Sprint 57.107 B3 (`GET /api/v1/sessions` real + `SessionList.tsx` wired + DEMO dropped + "New session"→`reset()`); the carryover line was STALE (snapshot 2026-06-06 predated 57.107). The genuine residual gap: clicking a historical session only highlights (`setActiveSessionId`), does NOT load/render its conversation — a soft Potemkin — because the main SSE stream is unpersisted. **User picked Option B** (full SSE persist + replay, ~2-sprint arc) over the lossy `state_snapshots` Option A. This slice 1 (backend): `_persist_main_event` (`router.py`, in `_stream_loop_events`) mirrors the 57.107 sidechain observer — best-effort `begin_nested()` SAVEPOINT, env-gate `MAIN_TRANSCRIPT_OBSERVER` (default on), persists the EXACT serialized main SSE `payload` (incl. active_skill) to `message_events` keyed by the MAIN `session_id` (sidechain rows key by subagent_id → no collision), monotonic `main_seq`; **NO migration** (table + partitions exist). Reader `GET /api/v1/sessions/{id}/events` returns the ordered stream; cross-tenant/unknown/event-less → 200 + `[]` (NOT 404). Backend-only (gate + probe, NOT a UI drive-through). mypy 0/370 · run_all 10/10 (wire 24) · pytest 2711+5skip (+8) · FE unchanged. **Live probe**: real-LLM chat → 16 events → `GET /events` returned 16 ordered, **streamed == persisted (order+type) TRUE** (full replay fidelity). CHANGE-092 + design note 37. Detail: `memory/project_phase57_125_chatv2_session_transcript_persistence.md`.

- **`AD-ChatV2-Session-History-Replay-Phase58` frontend half** (🟡, **Sprint 57.126 — NOT pre-written**) — click historical session → fetch `/events` → replay through the live `mergeEvent` reducer → render historical turns + route the continuation. The replay contract is fixed in design note 37 §4 (`{type, data, sequence_num, timestamp_ms}`, replay through the unchanged reducer).
- ~~**`AD-ChatV2-SessionList-Backend`**~~ ✅ **RESOLVED** — confirmed already-shipped by Sprint 57.107 B3 (Day-0); stale carryover + `sessions.py` docstring corrected.
- **`AD-ChatV2-Transcript-Volume-Filter`** (🟢, NEW) — optionally drop high-frequency span events from the persisted stream if volume becomes a concern (fidelity-first deferred).
- **`AD-ChatV2-Transcript-Retention`** (🟢, NEW, Phase 58+) — a `message_events` TTL / archival policy.
- Inherited: `AD-ExecutionContext-ExplicitApproval-Tidy` (57.124) + other C-class / chrome Potemkin + the operator-portal drive-through audit backlog.

---

## 🆕 Sprint 57.124 Carryover — HITL gate consolidation + 2 chrome/governance Potemkin fixes SHIPPED (3-track bundle; closes AD-PermissionChecker-Shadow-Gate-Phase58 + AD-HITL-Policy-Threshold-Validation + AD-NotificationsPanel-Backend-Feed)

Sprint 57.124 closed the 3 carryover items the user picked together (the next C-class items after 57.122/57.123). **Item 1 audit verdict**: `PermissionChecker` (Sprint 51.1, flagged from the 57.122 carryover as a "PARALLEL HITL abstraction not wired into the loop") is NOT a benign Potemkin but a **stale shadow gate** active on 主流量 (`make_default_executor` defaulted it on the executor) that OVERRIDES the 57.122 load-bearing per-tenant `HITLPolicy` — its dim 2 (`risk HIGH/CRITICAL → REQUIRE_APPROVAL`) is the exact flat hardcoding 57.122 removed from `loop.py:1007` (re-blocks a permissive `auto_approve_max_risk=HIGH`); its dim 3 (`destructive → DENY`) hard-blocked every destructive business tool in chat even after a human approved it (an approved-but-still-fails latent bug). **Fix B** (user-chosen): removed `PermissionChecker` from the executor + DELETED `permissions.py` + floored `destructive`→HIGH in `resolve_tool_risk` so destructive tools escalate-then-run via the per-tenant policy (single source of truth = loop `_cat9` + `HITLPolicy`). Day-0 `D-escalate-coverage` GREEN (all 8 ALWAYS_ASK/ASK_ONCE tools risk ≥ MEDIUM → no escalation lost; no `CHAT_HITL_ESCALATE_TOOLS` change). **Item 2** = `AD-NotificationsPanel-Backend-Feed`: a shared `notificationsFixture.ts` + a visible `BackendGapBanner` DEMO disclosure on `NotificationsPanel` + the bell badge derives from `DEMO_UNREAD_COUNT` (dropped the standalone `FIXTURE_UNREAD_COUNT`). **Item 3** = `AD-HITL-Policy-Threshold-Validation`: admin HITL-policy PUT `@model_validator` rejects `auto>=require` → 422. mypy 0/370 (−1 deleted) · run_all 10/10 · pytest 2703+5skip (−10 PermissionChecker tests +17 new) · FE mockup 51/vitest 16. Drive-through: Item 2 ✅ live (banner via real bell/panel) + Item 3 ✅ live (422 via real backend + real `platform_admin` session) + **Item 1 real-component-integration-verified** (gpt-5.2 declined the destructive trigger — `AD-DriveThrough-Deterministic-Tool-Trigger`; the loop `_cat9` + executor are exercised by real-component integration tests). CHANGE-091 + design note 36 (Track 1). **MERGED.**

- ~~**`AD-PermissionChecker-Shadow-Gate-Phase58`**~~ ✅ **SHIPPED Sprint 57.124** — removed the stale shadow gate from the executor + DELETED `permissions.py` + destructive HIGH-floor. See CHANGE-091 + design note 36.
- ~~**`AD-HITL-Policy-Threshold-Validation`**~~ ✅ **SHIPPED Sprint 57.124** — admin PUT `@model_validator` (auto<require → 422).
- ~~**`AD-NotificationsPanel-Backend-Feed`** (`FIXTURE_UNREAD_COUNT`)~~ ✅ **SHIPPED Sprint 57.124** — DEMO `BackendGapBanner` + shared fixture source.
- **`AD-ExecutionContext-ExplicitApproval-Tidy`** (🟢, NEW) — `ExecutionContext.explicit_approval` (`_contracts/tools.py:122`) lost its sole consumer (PermissionChecker dim 3); the frozen-dataclass field is retained for forward-compat. Removing it is a separate contract structural change.
- **Item-1 deterministic destructive-tool drive-through** (🟢, NEW) — a forced tool-call harness (inject a `tool_call` bypassing the LLM) would let the destructive escalate→run path be driven live without depending on gpt-5.2 calling a destructive tool (no reliable LLM trigger exists today).
- **`PermissionChecker`'s other annotation dims** (`open_world` etc.) were never gated; not introduced (noted, no action).
- Remaining: other C-class / chrome Potemkin + the operator-portal drive-through audit backlog.

---

## 🆕 Sprint 57.122 Carryover — HITL policy read-side load-bearing SHIPPED (closes AD-HITL-Policy-ReadSide-Potemkin-Phase58, the FLAGSHIP "C. 主流量 Potemkin / 載重 gap"; drive-through PASS)

Sprint 57.122 closed the flagship 載重 gap (`AD-HITL-Policy-ReadSide-Potemkin-Phase58`, flagged from the 57.106 Day-0 Explore) — the first of the "C. 主流量 Potemkin / 載重 gap (高價值修補)" class the user picked after the Skills epic. The per-tenant `HITLPolicy` risk thresholds (`auto_approve_max_risk` / `require_approval_min_risk`; write-side shipped 55.3/57.48/57.54, manager DB-wired at `service_factory.py:124/134-137`) were NEVER read at tool execution — the loop hardcoded `if requires_approval: ESCALATE` (`tool_guardrail.py:151-160`) + a flat `RiskLevel.HIGH` (`loop.py:1007`). Now the loop's Cat 9 path reads `hitl_manager.get_policy(tenant_id)` + applies a pure two-threshold `decide_tool_hitl` (escalate-first; risk from `ToolSpec.risk_level` per the user decision) + carries the resolved risk into the `ApprovalRequest` (hardcoded HIGH dropped). Implementation refinement caught pre-run: the per-rule flag is a MEDIUM risk FLOOR so flagged-LOW-spec tools still escalate under DEFAULT (no silent safety relaxation). Backend-only (2 src + 2 new tests + 1 stale-assertion HIGH→MEDIUM); scope held to the tool path (the 5 content-guardrail HIGH sites untouched — a tenant must not auto-approve a jailbreak). mypy 0/371 · run_all 10/10 · pytest 2695+5skip. Drive-through PASS (real chat-v2 + gpt-5.2, admin/acme-prod): the IDENTICAL `python_sandbox(print(6*7))` call auto-approved (`TOOL_EXEC`) under a permissive policy vs escalated (`approval_requested risk=MEDIUM` → `awaiting_approval`) under a strict policy set via admin PUT — same tool, different per-tenant DB policy, different runtime (NOT gate-only). `risk=MEDIUM` (not the hardcoded HIGH) = live proof. NEW class `harness-loadbearing-gap-fix` 0.60→**0.85 re-pointed**. CHANGE-089 + design note 35. **MERGED.**

- **`AD-HITL-Policy-Threshold-Validation`** (🆕) — the admin PUT should validate `auto_approve_max_risk < require_approval_min_risk`. The runtime is safe via escalate-first ordering, but a misconfigured overlap silently means "escalate". Own slice.
- **`AD-DriveThrough-Deterministic-Tool-Trigger`** (🆕, process) — a drive-through needing a tool call should use a tool the LLM cannot self-answer (`python_sandbox` / data retrieval), NOT a trivial transform (`echo_tool` — gpt-5.2 answered it directly in 4/5 sessions = `0 tool calls`). Candidate for the drive-through playbook.
- **`PermissionChecker` (Sprint 51.1) + `ToolSpec.hitl_policy`** are a PARALLEL HITL abstraction NOT wired into the loop (the live path is `guardrail_engine.check_tool_call` → `ToolGuardrail`) — a possible separate Potemkin to audit (NOT this slice).
- Remaining C-class 主流量 Potemkin: ~~**`AD-FE-Tenant-Display-Fixture-Phase58`**~~ ✅ **SHIPPED Sprint 57.123** (chrome reads `authStore.tenant`; `/auth/me` += plan/region; UserMenu 3→1 collapse; CHANGE-090) + the 2026-06-06/07 operator-portal drive-through audit backlog.

---

## 🆕 Sprint 57.121 Carryover — Skills slash-menu mockup + production re-point SHIPPED → **the Skills epic is COMPLETE** (closes AD-Skills-SlashMenu-Mockup; drive-through PASS)

Sprint 57.121 closed the LAST Skills-epic item, `AD-Skills-SlashMenu-Mockup` — **the Skills epic is now COMPLETE** (57.113 model-invoked lazy-load → 114 per-tenant overlay → 115 `/skill-name` slash-command → 116 user-turn chip → 117 catalog quota → 118 bundled scripts → 119 system visibility → 120 Inspector active_skill → **121 slash-menu mockup**). 57.115 shipped the chat-v2 `/`-slash picker (`SkillSlashMenu.tsx`) GREENFIELD with inline token-styles + a header "No mockup reference exists for this element" — the ONE chat-v2 element with no `reference/design-mockups/` entry (a Mockup-Fidelity Hard Constraint gap). This (1) AUTHORED it in the mockup (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*`, CommandPalette-consistent per the AskUserQuestion, token-only NO hex/oklch literal, no emoji; an interactive `Composer` makes the prototype demonstrable) and (2) RE-POINTED production `SkillSlashMenu.tsx` from inline-styles to the mockup classes (byte-identical CSS copy into `styles-mockup.css` → `diff` empty + a `Skills` group header + a `.kbd` footer + DROP the `eslint-disable no-restricted-syntax` = a net fidelity-debt reduction; KEEP the 57.115 `data-testid`s / `role`s / `aria-selected` / `onMouseDown`). The InputBar is UNTOUCHED (it owns the filter / activeIndex / keyboard / force-load — 57.115; the mockup's interactive Composer is prototype-only). Two-step, user-directed: author the mockup → review/approve → implement (the byte-identity gate couples reference + production, so they can't split across PRs — the mockup was held local until the production port). 5 files ALL FE, **0 `.py`** → mypy 0/371 / pytest 2648+5skip / wire 24 UNCHANGED. Gate: Vitest 888 (+4) · `diff` empty · `check:mockup-fidelity` 51 byte-identical · `npm run lint` clean (no unused-directive from the dropped disable) · build ✅ · run_all 10/10. Drive-through PASS (real chat-v2 + real backend, acme-prod, re-dev-login after the 57.120 JWT expired): type `/` → the menu renders with the new mockup styling + the REAL `useChatSkills` bundled skills (`/code-review` active / `/digest` / `/summarize`, real backend descriptions) + a `.kbd` footer "3 skills"; `/dig` filters to only `/digest` ("1 skill"); click `/digest` (via the preserved `skill-slash-item-digest` testid) → `/digest ` filled + menu closed (force-load). AP-4 clear; 3 screenshots (1 production + 2 mockup-prototype). NEW class `mockup-author-and-port` 0.70 (1st data point ~1.17 IN band). CHANGE-088, NO design note (feature continuation). **MERGED.**

- ~~**`AD-Skills-SlashMenu-Mockup`**~~ ✅ **SHIPPED Sprint 57.121** — the slash menu authored in `reference/design-mockups/` + production re-pointed to the classes. See CHANGE-088. **→ the Skills epic (57.113-121) is COMPLETE.**
- **Skills epic — remaining (explicitly-deferred larger slices, NOT epic-blocking)**: `AD-Skills-Authoring-UI` (versioning + bundled-registry hot-reload + per-tenant disable-toggle legs); `AD-Skills-Bundled-Scripts` (tenant-authored leg — an untrusted code author, needs a deny-list + quota); `AD-Config-Cache-MultiWorker-Invalidation` (the `_SkillRegistryCache` / `_ModelPolicyCache` cross-worker coherence); per-tenant-configurable quota. None block the epic — they are future enhancements selectable on demand.
- **Calibration watch** (`mockup-author-and-port` 0.70, 1st data point ~1.17 IN band) — KEEP; consistent with the 57.120 `chatv2-inspector-existing-field-surface` 0.55→0.85 re-point (mockup/FE-surface sprints with a bounded-but-real code core sit ~0.65-0.85, above the 0.45-0.55 pure-repoint range — ceremony is not code-accelerated). Validate over the next 1-2 such sprints.
- Tiny tidy (noted, not pursued): the InputBar's now-redundant inline `position: relative` on `.composer-inner` (the `.composer-inner` class provides it since this sprint).

---

## 🆕 Sprint 57.120 Carryover — chat-v2 Inspector Turn tab `active_skill` row SHIPPED (closes the Inspector-panel leg of AD-ChatV2-Inspector-Turn-Metadata-Wire / ISSUE-5; drive-through BOTH legs PASS)

Sprint 57.120 closed the **Inspector-panel active-skill leg** of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5, carried from the 2026-06-06 drive-through audit; the penultimate Skills-epic item; scope chosen via **AskUserQuestion** — active-skill row 單列 over also surfacing `model` / a broader token sweep). 57.116 had wired `loop_start.active_skill` onto the triggering `UserTurn` as a "⚡ {skill}" timeline CHIP only; this surfaces the SAME skill as a per-turn Inspector ROW (alongside trace_id/tokens). **PURE FE + store** — the field was ALREADY on the wire (57.116) → NO new wire field / codegen / backend / migration (count 24). `AgentTurn += activeSkill?` (`types.ts`) + at `turn_start` (`chatStore.ts`) carry it from the most-recent NON-injected `UserTurn` (the loop trigger; the SAME cross-slice point that already links `span_id`; skip injected 57.101 → no clear-on-injection; a new no-skill loop → undefined → no stale leak) + a `<KV k="active_skill" v={⚡skill / "—"}>` in `InspectorTurn.tsx` (reuse the private `KV` helper → no `styles-mockup.css` change → mockup-fidelity byte-identical). 5 files ALL FE (3 src + 2 test), **0 `.py`** → mypy 0/371 / pytest 2648+5skip / wire 24 definitionally UNCHANGED. Gate: Vitest 884 (+5) · build ✅ (57.116 lesson: optional field, no literal break) · lint clean · mockup 51 · run_all 10/10. Drive-through BOTH legs PASS (real chat-v2 + gpt-5.2, acme-prod, NO Risk-E restart — 0 `.py` delta; system-bundled `/code-review` resolves for any tenant): Leg A `/code-review`→user chip + Inspector Turn-1 `active_skill: ⚡ code-review` (between cost & trace_id); Leg B plain msg→Inspector Turn-2 `active_skill: —` (a new trace — the prior code-review did NOT leak = the no-leak design proven LIVE). AP-4 clear, 2 screenshots. NEW class `chatv2-inspector-existing-field-surface` 0.55→**0.85 re-pointed** (1st pt ratio ~1.6 OVER — a tiny-code + full-ceremony parent-direct sprint; the 0.45-0.65 band assumes code-hours to haircut, but ceremony is NOT code-accelerated). CHANGE-087, NO design note (feature continuation). **MERGED.**

- ~~**`AD-ChatV2-Inspector-Turn-Metadata-Wire`** (Inspector-panel active-skill leg / ISSUE-5)~~ ✅ **SHIPPED Sprint 57.120** — a per-turn `active_skill` KV row in the Inspector Turn tab, carrying the 57.116 `loop_start.active_skill` forward onto the `AgentTurn` at `turn_start`. See CHANGE-087.
- **`AD-ChatV2-Inspector-Turn-Metadata-Wire`** (`model` row leg) (🟡, carried) — a per-turn `model` KV row (the AskUserQuestion's 2nd option; `currentModel` is captured + in the ChatHeader badge but not per-turn). A natural follow-on (same store + Inspector pattern).
- **`AD-ChatV2-Inspector-Turn-Metadata-Wire`** (token sweep leg) (🟢, carried) — actual `input_tokens` vs the `tokens_in` estimate + `cached_input_tokens` + `cache_hit_rate` per turn. The 57.108 token carve-outs + `AD-ChatV2-Inspector-Cost-InStream` hold (cost/thinking stay honest "—" by design — post-loop).
- **Calibration watch** (`chatv2-inspector-existing-field-surface` 0.85, re-pointed from 0.55, 1st data point) — the generalizable insight: a TINY-CODE + FULL-CEREMONY parent-direct sprint should use a multiplier near ~0.85-1.0 regardless of the FE family it resembles; the 0.45-0.65 band assumes the bottom-up has enough code-hours for the acceleration haircut to matter. Validate over the next 2-3 `*-existing-field-surface` sprints.
- Last remaining Skills epic AD (the 1 left in the "順序執行" sequence): `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).

---

## 🆕 Sprint 57.119 Carryover — Skills system visibility + preview SHIPPED (Skills epic authoring-UX visibility leg; drive-through PASS; ships the system-skills-visibility slice of AD-Skills-Authoring-UI)

Sprint 57.119 shipped the **system-skills-visibility leg** of `AD-Skills-Authoring-UI` (the 3rd of the user's "complete all Skills work" sequence after 57.118; scope chosen via **AskUserQuestion** over the AD's other 2 interpretations — versioning / hot-reload). The 57.114 admin Skills tab showed ONLY the tenant's own overlay skills; the system-bundled set (`code-review`/`digest`/`summarize`, the base every tenant's skills overlay + what the model sees) was invisible in any admin UI. This adds a read-only **"System Skills"** section (a "🔧 script" badge for `has_script` (57.118) + a "shadowed by your skill" tag for per-tenant `overridden`) + a **Preview** modal rendering any skill's full instructions (bundled or tenant). ONE read-only `GET /admin/tenants/{tenant_id}/skills/system` (`list_system_skills`, mirrors `list_tenant_skills` auth) over `get_default_skill_registry().list()`; `has_script = skill.script is not None`, `overridden = name in {tenant skill names}` (the tenant_id makes it meaningful — which bundled skills THIS tenant has shadowed). The api→Cat-5 import follows the `handler.py:96`/`router.py:465` precedent (the #1 lint risk RESOLVED Day-0). FE: `SystemSkill`/`SystemSkillListResponse` + `fetchSystemSkills` + `useSystemSkills` (own key) + a `SkillsTab` sibling Card + an inline-overlay Preview modal (NO `Modal` primitive in mockup-ui → followed the `TenantMembersDrawer` a11y convention: a window Escape `useEffect` + `role="dialog"` + the matching `jsx-a11y` disables; tokens `var(--bg)`). Read-only — respects 57.118's tenant-script deferral (`has_script` is a boolean badge; the script SOURCE is never shown/edited). NO DB / migration / wire (count 24) / codegen. Gate: mypy 0/371 · run_all 10/10 · pytest 2648+5skip (+4) · Vitest 879 (+6) · mockup 51. Drive-through PASS (real admin Skills tab + real backend, acme-skills): the System Skills section lists the 3 bundled read-only · `digest` 🔧-badge ONLY · a live-created tenant `code-review` → the "shadowed by your skill" tag (then deleted 204) · `digest` Preview → a `role="dialog"` modal renders `digest.md` verbatim · Close dismisses · tenant `release-notes` Preview renders too — every control live (AP-4 clear). NEW `skills-admin-readonly-surface` 0.55 (1st data point ~0.97 IN band, parent-direct). CHANGE-086, NO design note (feature continuation). **MERGED.**

- ~~**`AD-Skills-Authoring-UI`** (system-skills-visibility leg)~~ ✅ **SHIPPED Sprint 57.119** — a read-only "System Skills" section (badge + shadowed tag) + a Preview modal, over a new read-only `GET /skills/system`. See CHANGE-086.
- **`AD-Skills-Authoring-UI`** (versioning leg) (🟡, carried) — a `version` column on `tenant_skills` + a version-history table + a rollback UI (a DB migration + RLS + UI). Deferred per the AskUserQuestion.
- **`AD-Skills-Authoring-UI`** (bundled-registry hot-reload leg) (🟢, carried, low prod value) — an admin reload action without a backend restart (the bundled registry loads once per process). Bundled skills are git-deployed → reload ≈ redeploy; mostly dev convenience.
- **Per-tenant disable-toggle for a bundled skill** (🟢, carried) — let a tenant hide/disable a built-in skill from the chat catalog (a larger governance slice than read-only visibility).
- Remaining Skills epic ADs (the 2 left in the "順序執行" sequence): `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).

---

## 🆕 Sprint 57.118 Carryover — Skills bundled scripts: system-bundled `run_skill_script` SHIPPED (Skills epic executable half; drive-through PASS in a REAL Docker sandbox; closes the system-bundled leg of AD-Skills-Bundled-Scripts)

Sprint 57.118 closed the **system-bundled leg** of `AD-Skills-Bundled-Scripts` (the 2nd of the 5 pending Skills ADs the user chose to run in sequence; cc-parity row 9's last missing piece — the executable half). A SYSTEM-BUNDLED skill may ship a sibling `<stem>.py` next to its `SKILL.md`; the model runs it on demand via a NEW Cat-2 `run_skill_script(skill_name)` tool through the SAME `SandboxBackend` that powers `python_sandbox` (Docker prod / Subprocess dev-CI). `Skill.script: str|None` (Cat 5, loaded by `from_dir` from the sibling — SERVER-controlled, never an LLM arg) + `RUN_SKILL_SCRIPT_TOOL_SPEC` (risk MEDIUM, input `{skill_name}` only) + `make_run_skill_script_handler` w/ a lazy process-wide sandbox singleton (Day-0 refinement — `make_default_executor` runs per request → avoid per-request Docker probe) + the `skill_registry` opt-in registers it (auto-PASS via the risk-blind permission matrix `handler.py:588-592`; Day-0 #1 risk RESOLVED — no `capability_matrix` entry) + a demo `bundled/digest.{md,py}` (prints a runtime sha256 the LLM can't fabricate). User-chosen scope (AskUserQuestion): system-bundled ONLY (tenant-authored deferred) + a dedicated tool (vs reuse `python_sandbox(code)` where code would pass through the LLM). NO DB / migration / wire (count 24) / codegen / frontend. Gate: mypy 0/371 · run_all 10/10 · pytest 2644+5skip (+14, 0 del). Drive-through PASS (real chat-v2 + Azure gpt-5.2, acme-skills, **REAL DockerSandbox 29.5.2**): `read_skill`→`run_skill_script("digest")` span 546ms exit 0 → final `039e824c…517b8b1e` == local `hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()` byte-for-byte + verification 0.99 = **first main-flow proof of sandboxed execution**. NEW `skills-bundled-script-spike` 0.60 (1st data point ~0.92 IN band, parent-direct). CHANGE-085 + design note 34 (spike, 8-pt gate ~96%). **MERGED.**

- ~~**`AD-Skills-Bundled-Scripts`** (system-bundled leg)~~ ✅ **CLOSED Sprint 57.118** — a system-bundled skill ships a sibling `<stem>.py` run via the NEW Cat-2 `run_skill_script` tool through the existing `SandboxBackend`. See CHANGE-085 + design note 34.
- **`AD-Skills-Bundled-Scripts`** (tenant-authored leg) (🟡, carried) — let a TENANT ship a script (`tenant_skills.script` + sandbox quota + a deny-list scan of the tenant source + abuse/billing controls); a tenant becomes an untrusted code author, a much bigger slice than the system-bundled (git-authored, review-trusted) leg.
- **Skills multi-file resources + script input/args + automated deny-list scan of bundled scripts** (🟢, carried, YAGNI) — a skill bundling a directory of helpers/data (vs one `<stem>.py`); passing runtime args to `run_skill_script`; an automated `RiskyActionDetector`-style scan of `Skill.script` at load (the system-bundled trust model is authorship-time review). See design note 34 §5.
- Remaining Skills epic ADs (the 3 left in the "順序執行" sequence): `AD-Skills-Authoring-UI` (57.119) · `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).

---

## 🆕 Sprint 57.117 Carryover — Skills catalog hardening: per-tenant quota + instructions body-size limit SHIPPED (Skills epic catalog-hardening; drive-through BOTH legs PASS; closes AD-Skills-Per-Tenant-Quota)

Sprint 57.117 closed the first two asks of `AD-Skills-Per-Tenant-Quota` (the 1st of the 5 pending Skills ADs the user chose to run in sequence). The 57.114 per-tenant catalog — an unbounded write surface — gains two write-path guardrails: a per-tenant skill-count quota (`SKILLS_MAX_PER_TENANT`, default 50, env-overridable — enforced in `TenantSkillService.create` via a NEW `SkillQuotaExceededError` 409 that the admin POST's existing `except TenantSkillError` auto-maps, no handler change) + an `instructions` body-size cap (`SKILLS_MAX_INSTRUCTIONS_CHARS`, default 20_000, env-overridable — a `max_length` on the `SkillCreate/UpdateRequest` Pydantic field → 422; DB column stays `Text`, NO migration). `SkillListResponse` surfaces both limits (`max_skills`/`max_instructions_chars`) → the admin "Skills" tab shows "N / max", disables Add at the cap, caps the textarea, renders 409/422 from the SERVER value (the FE type fields are OPTIONAL → existing mocks + older cached responses fall back to `Infinity`; `useTenantSkills`/`tenantSettingsService` UNCHANGED — the hook already passes the whole response). Gate: mypy 0/370 · run_all 10/10 · pytest 2630+5skip (+7) · Vitest 873 (+4) · mockup 51 (count 24, no codegen/migration). Drive-through BOTH legs PASS (real admin tab + a lowered env limit, acme-skills): Leg A "1/2"→Add enabled→create→"2/2"+"Skill limit reached"+Add disabled + forced POST → 409; Leg B textarea capped 200 + forced 201-char POST → 422 (the low env override visible in the tab proves the limits are server-sourced, AP-4-safe). NEW `config-validation-hardening` 0.55 (1st data point ~0.95-1.0 IN band, parent-direct). CHANGE-084, NO design note (feature continuation). **MERGED.**

- ~~**`AD-Skills-Per-Tenant-Quota`**~~ ✅ **CLOSED Sprint 57.117** (first two asks) — the per-tenant count quota + the `instructions` body-size limit, env-overridable, surfaced on `SkillListResponse` to the admin Skills tab. See CHANGE-084.
- **`AD-Config-Cache-MultiWorker-Invalidation`** (🟡, NEW Sprint 57.117 — the quota AD's 3rd ask, split out) — `_SkillRegistryCache` is in-process per worker (an admin mutation on worker A leaves worker B stale up to the 60 s TTL); shared with `_ModelPolicyCache` + the harness-policy cache → a cross-cutting cache-coherency infra slice (a shared invalidation signal — Redis pub/sub or a DB-version-stamp), YAGNI under single-worker deploy.
- **Per-tenant-CONFIGURABLE quota** (🟢, carried) — this slice ships a GLOBAL default (env-overridable); the 57.56 Quotas `tenants.meta_data` override pattern can add per-tenant configurability later if a real need appears.
- Remaining Skills epic ADs (the 3 left in the "順序執行" sequence; `AD-Skills-Bundled-Scripts` system-bundled leg CLOSED Sprint 57.118): `AD-Skills-Authoring-UI` (57.119) · `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).

---

## 🆕 Sprint 57.116 Carryover — Skills force-load Inspector affordance (user-turn "⚡ {skill}" chip) SHIPPED (Skills epic 1st UX affordance; drive-through ALL 3 cases PASS; closes AD-Skills-Inspector-Affordance)

Sprint 57.116 closed `AD-Skills-Inspector-Affordance` (the user chose: affordance = user-turn chip; scope = force-load only). A **server-confirmed** `active_skill` ADDITIVE field on the opening `loop_start` SSE event (count stays 24; `sse.py` defaults null + `event_wire_schema` declares + codegen regen; the ROUTER injects the validated force-load name at `_stream_loop_events:641` — `loop.py`/`events.py`/`LoopStarted` dataclass/`read_skill`/`_stream_resume_events` UNTOUCHED, Cat-1 boundary clean; REJECTED the Explore agent's thread-through-`AgentLoopImpl` option) drives a chat-v2 `UserTurn.activeSkill` store stamp (truthy-guard last-user-turn, resume-safe) → a `.route-pill` "⚡ {skill}" chip (reuses the 57.101 injected-tag, no new colour literal). The chip is from the SERVER value, NOT the sent `force_load_skill` (AP-4 guard). Gate: mypy 0/370 · run_all 10/10 · pytest 2623+5skip (+7) · Vitest 869 (+6) · mockup 51. Drive-through ALL 3 cases PASS (real chat-v2 + Azure gpt-5.2, acme-skills): A `/release-notes`→chip + output follows + `read_skill` 0× / B `/nonexistent`→no chip (router dropped→null, not a client echo) / C plain→no chip. NEW `frontend-feature-with-event-wire-addition` 0.55 **3rd data point** ~1.1-1.2 IN band → KEEP validated. CHANGE-083, NO design note (feature continuation). **MERGED.**

- ~~**`AD-Skills-Inspector-Affordance`**~~ ✅ **CLOSED Sprint 57.116** — the user-turn "⚡ {skill}" chip via the server-confirmed `loop_start.active_skill` additive field. See CHANGE-083.
- **`AD-ChatV2-Inspector-Turn-Metadata-Wire`** (🟡, the OTHER affordance — separate slice) — this sprint chose the user-turn chip; the Inspector-PANEL "active skill" metadata row (alongside trace_id / tokens) is a distinct, still-open slice (also carried from the 2026-06-06 drive-through audit as ISSUE-5).
- **Build-time process candidate** (🟢, 1 data point — fold into `sprint-workflow.md §Step 2.5` only if it recurs) — adding a REQUIRED field to a codegen wire type breaks every existing event LITERAL (fixtures), not just consumers; the Vitest oxc transform skips type-checking so `npm run test` stays green while `tsc -b` (build) fails. After a wire-schema field add, run `npm run build`, not only Vitest. (57.116 hit `demoLoopEvents.ts` + a union-narrowing issue; ~10 min fix.)
- Remaining Skills epic ADs (post-57.117): `AD-Skills-Bundled-Scripts` · `AD-Skills-Authoring-UI` · `AD-ChatV2-Inspector-Turn-Metadata-Wire` · `AD-Skills-SlashMenu-Mockup` · multi-skill-per-command (YAGNI). (`AD-Skills-Per-Tenant-Quota` CLOSED Sprint 57.117.)

---

## 🆕 Sprint 57.115 Carryover — Skills slash-command `/skill-name` force-load SHIPPED (Skills epic 3rd slice; drive-through ALL 3 legs PASS; closes AD-Skills-Slash-Command)

Sprint 57.115 closed `AD-Skills-Slash-Command` (the user-invoked half after 57.113 model-invoked + 57.114 per-tenant). A `/skill-name` composer picker (`SkillSlashMenu`, greenfield) + **deterministic force-load** (the picked skill's full instructions injected into the turn's system prompt under `## Active Skill` — the model loads it WITHOUT calling `read_skill`; drive-through Leg A proved `read_skill` 0× yet the output followed the skill) + a non-admin `GET /api/v1/chat/skills` picker list (name+description only, no instructions leak) + `ChatRequest.force_load_skill` + a router validate-and-pass (unknown → graceful). `make_default_executor`/`loop.py`/`read_skill` self-select/wire(24)/codegen/migration UNTOUCHED. Gate: mypy 0/370 · run_all 10/10 · pytest 2616+5skip (+14) · Vitest 863 (+12) · mockup 51. Calibration NEW `skills-slash-command-fullstack` 0.55 (1st pt ~1.0, parent-direct). CHANGE-082 + design note 33. **MERGED.**

- **`AD-Skills-Inspector-Affordance`** (🟢, reinforced) — force-load is INVISIBLE in the timeline after send (the `/token` is stripped, no `read_skill` event); a dedicated SSE "skill force-loaded" event + an Inspector chip / a "skill: X active" badge on the user turn would surface it (wire count stays 24 today).
- **Multi-skill per command** (🟢, NEW) — single `force_load_skill` per message; `force_load_skills: list` is additive (YAGNI until a real 2-skill use case).
- **`AD-Skills-SlashMenu-Mockup`** (🟢, NEW) — the `SkillSlashMenu` is a net-new element with NO mockup reference (built from `styles-mockup.css` tokens); if a chat composer slash-menu mockup is ever authored, re-point to it.
- **Picker stale-skill refetch** (🟢, NEW) — `useChatSkills` has `staleTime` 60s; a skill renamed/deleted mid-session won't reflect until refetch (minor; the backend validates the name anyway → graceful).

---

## 🆕 Sprint 57.113 Carryover — Skills System epic OPENED (first thin vertical, model-invoked lazy-load; drive-through ALL 3 legs PASS)

Sprint 57.113 opened the **Skills System epic** (cc-parity `agent-harness-cc-parity-20260607.md` row 9 — the last systematic CC-parity gap) with its first thin vertical: **model-invoked lazy-load** (user scope decision Option A). A system-global `SkillRegistry` (`agent_harness/skills/`, Cat 5) loads bundled `SKILL.md` (frontmatter name+description + body); a cheap `## Available Skills` block rides the `system_prompt` persona seam (`loop.py:1899`); a `read_skill` tool (Cat 2) lazy-loads a skill's full instructions when the model self-selects — `make_default_executor(skill_registry=)` opt-in (chat path's registry-derived perm matrix auto-PASSes) + `build_handler`/`router` wiring. 2 REAL bundled skills (`code-review`, `summarize`). No DB / no migration / no new wire event (count 24) / no FE. Gate: mypy 0/366 · run_all 10/10 · full pytest 2566+5skip (+20, 0 del). Drive-through (real chat-v2 + real Azure, dev-login jamie@acme.com): code-review→`read_skill`→Risks-table / summarize→`read_skill`→Decisions+owner—task / "2+2"→no-trigger — output shapes distinctly followed the loaded skills (load+follow, AP-4 guard) + no false-positive. **MERGED.** CHANGE-080 + design note `31-skills-system-spike.md`. NEW scope class `skills-system-spike` 0.60 (1st pt ~0.94). **Skills is NOT part of the harness-deepening roadmap** (sourced from the cc-parity analysis, a separate epic).

- ~~**`AD-Skills-Per-Tenant-Catalog`**~~ ✅ **CLOSED Sprint 57.114** — DB-backed per-tenant overlay shipped: `tenant_skills` table (RLS) + `resolve_tenant_skill_registry` (mirrors `resolve_session_persona`, TTL cache + fail-open) + `SkillRegistry.with_overlay` (override-by-name) + admin "Skills" tab; drive-through ALL 3 legs PASS. See `32-skills-per-tenant-catalog.md` + CHANGE-081.
- ~~**`AD-Skills-Per-Tenant-Quota`**~~ ✅ **CLOSED Sprint 57.117** (first two asks) — per-tenant skill-count quota (`SkillQuotaExceededError` 409) + `instructions` body-size limit (Pydantic `max_length` 422), env-overridable, surfaced on `SkillListResponse`. The 3rd ask (multi-worker shared cache-invalidation) split out as `AD-Config-Cache-MultiWorker-Invalidation`. See CHANGE-084.
- ~~**`AD-Skills-Slash-Command`**~~ ✅ **CLOSED Sprint 57.115** — `/skill-name` composer picker + deterministic force-load (`## Active Skill` system-prompt injection; `read_skill` 0× proven) + non-admin `GET /chat/skills` + `ChatRequest.force_load_skill` + greenfield `SkillSlashMenu`; drive-through ALL 3 legs PASS. See `33-skills-slash-command.md` + CHANGE-082.
- **`AD-Skills-Inspector-Affordance`** (🟢) — a dedicated SSE wire event + an Inspector "skill loaded" affordance (today `read_skill` rides the generic Cat 2 tool stream; wire count stays 24).
- **`AD-Skills-Authoring-UI`** — skill versioning / hot-reload / an authoring admin UI. **System-skills-visibility leg ✅ SHIPPED Sprint 57.119** (a read-only "System Skills" section + a Preview modal). The **versioning** + **bundled-registry hot-reload** + **per-tenant disable-toggle** legs remain 🟡/🟢 (see the Sprint 57.119 Carryover section above).
- **`AD-Skills-Bundled-Scripts`** — CC skills can bundle executable scripts/resources. **System-bundled leg ✅ CLOSED Sprint 57.118** (a sibling `<stem>.py` run via the NEW Cat-2 `run_skill_script` tool); the **tenant-authored leg + multi-file resources + script args remain 🟡/🟢** (see the Sprint 57.118 Carryover section above).
- **Skill-aware prompt-caching boundary** (🟢) — the block is appended to the cache-stable persona prefix; a dedicated cache breakpoint for the skills block was not measured.

---

## 🆕 Sprint 57.112 Carryover — IAM Block C MFA TOTP-only vertical SHIPPED (drive-through ALL 3 legs PASS; closes the TOTP leg of AD-Auth-MFA-Backend-IAM-Block-C)

Sprint 57.112 closed the TOTP leg of `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (the next C-12 leg after invites 57.85 / credentials 57.86 / register 57.87 / RBAC-JWT 57.105; CHANGE-079 + design note `30-iam-mfa-spike.md`). `users` + `totp_secret`/`mfa_enabled` (migration 0029) + `TOTPService` (enroll/confirm/verify, mirrors the 57.86 `CredentialsService`) + `POST /api/v1/mfa/{enroll,enroll/confirm,verify}` + a password-login **challenge-token gate** (`mfa_enabled` → a short-lived `mfa_pending` `v2_mfa_challenge` cookie + `{mfa_required}` — NO session — and `/mfa/verify` swaps a valid TOTP for the real `v2_jwt` via the shared `auth.issue_session`; `/mfa/verify` EXEMPT exact-match, `/mfa/enroll` full-session). Thin FE (password-login `mfa_required` branch + un-stubbed `/auth/mfa`). Drive-through (real UI + fresh backend + real Postgres, zero dev-login): enroll(API)→confirm→login(`mfa_required`)→TOTP→authenticated `/chat-v2`; wrong code → inline error. Gate: mypy 0/363 · run_all 10/10 (count 24) · full pytest 2546+5skip (+20, 0 del) · Vitest 840 (+3) · mockup 51. **MERGED.** Calibration `iam-backend-spike` 0.65 3rd data point ratio ~1.28 (slightly over — FE component + the D13 drive-through detour; KEEP 0.65, 3-pt mean ~1.08 in band).

- **`AD-MFA-Secret-At-Rest-Encryption`** (🟡) — `users.totp_secret` is base32 **plaintext** (a TOTP secret must be readable to recompute codes — can't be hashed; Day-0 confirmed NO encryption utility wired). Encrypt at rest (Fernet/app-key) once a key-management utility exists.
- **WebAuthn** (🟡) — the FE conic-ring is Simulate-only (`/mfa/verify` `method="webauthn"` → honest 400 today); a real `navigator.credentials` ceremony + `py_webauthn` + a `webauthn_credentials` table + FE rework is a separate C-12 spike.
- **`AD-Auth-MFA-Recovery-Page`** (🟡) — recovery codes + `/auth/mfa/recovery` (needs the recovery flow + an email adapter that does not exist).
- **OIDC-callback MFA gate** (🟢) — this sprint gated password-login only; SSO MFA is typically IdP-enforced; the 302-redirect gate is a separate slice.
- **`AD-MFA-Enroll-Setup-UI`** (🟢) — no enroll/setup mockup exists; enroll is API-driven for the drive-through.
- **`AD-Auth-PasswordLogin-Lockout`** (🟢, shared) — extend the brute-force throttle to `/mfa/verify`.
- **`AD-FE-FetchWithAuth-Validation-401-Lint`** (🟢 NEW from the D13 drive-through find) — the MFA `/mfa/verify` `fetchWithAuth` lacked `{redirectOn401:false}` → a wrong-code 401 bounced to SSO (Vitest mocks `global.fetch` + jsdom no-ops `window.location` → only the drive-through caught it). A lint/grep guard: any `fetchWithAuth` whose 401 is a validation error (not a session expiry) must pass `{redirectOn401:false}`.

---

## 🆕 Sprint 57.111 Carryover — A3 trace-aware critique + permanent cheap-judge benchmark SHIPPED (the harness-deepening 10-slice set is COMPLETE)

Sprint 57.111 closed A3 (CHANGE-078; design note 25 §2.6 + §4 A3/cheap-judge SHIPPED + 24 §4 cheap-judge RESOLVED): the in-loop Cat 10 judge is trace-aware (the gate threads a real `trace_state` built from its `messages` — mirroring `compact_state` — vs the old `cast(LoopState,None)`; `loop.py` diff 25/3 threading-only; ABC widened `state: LoopState|None`, the 3 Cat 9 fallback judge sites keep `None`) + a permanent `@pytest.mark.benchmark` cheap-judge accuracy harness (`scripts/benchmark_judge.py` + a 28-case golden fixture; `RUN_AZURE_INTEGRATION`-gated → CI skips it). Real Azure: cheap **92.86%** (stable ×2) / **trace_delta +42.86%** (stable; cheap-with-trace nails trace_dependent 100%, without-trace misses ~43%) / floor PASS → **verdict: keep the cheap tier** (the strong tier actually over-flags clear_pass). Drive-through Leg A (real UI + fresh A3 backend + real Azure): chat "Paris." + Verification (1) ✅ — the live trace-aware gate ran. **The full harness-deepening 10-slice set is COMPLETE — the items below are the open pool, none mandatory to the harness.**

- **`AD-Benchmark-Live-Trace-Fail-Drive`** (🟢 from the 57.111 dt — honest scope): Leg A drove a PASS case (a good answer the trace-aware judge correctly passed); a live trace-dependent FAIL was NOT engineered (gpt-5.2 won't claim success after a tool error w/o a config change). A future dt could swap the live judge template to `forced_fail_trace.txt` (created this sprint, unused) or inject a tool-error scenario to render a trace-citing critique in the UI. The behavior IS proven quantitatively (the benchmark trace_delta).
- **`AD-Strong-Tier-Over-Flags-ClearPass`** (🟢): the benchmark surfaced the strong tier (gpt-5.2) flagging good short answers as failures (clear_pass 37.5–87.5%, run-variant even at temp 0). Affects any future "move judge to strong" decision — is the template too strict for the strong model, or is it genuinely noisier as a lenient judge?
- **`AD-Benchmark-Floor-Calibration`** (🟢): `CHEAP_ACCURACY_FLOOR=0.70` is a first guess; the real run (cheap 92.86%) suggests raising it to ~0.85 once 2-3 runs confirm stability.

---

## 🆕 Sprint 57.110 Carryover — B4 subagent child governance SHIPPED (drive-through ALL legs PASS; the mandatory harness-deepening set is COMPLETE)

Sprint 57.110 closed proposal §2.5 B4 (CHANGE-077; design note 20 §5 child-governance + failure-policy rows RESOLVED): child loops inherit the tenant-composed Cat 9 engine (late-bound closure; **`loop.py` diff 0** — ESCALATE-in-child fail-closes to BLOCK by the existing invariant) + `GuardrailTriggered` joins the child relay (Tree row renders the fire) + `SubagentFailurePolicy` fail_fast/soft/partial on `SubagentBudget`, per-tenant via `HarnessPolicy.subagent_failure_policy` (PUT literal 422). Drive-through proved the INHERITED C3 detector blocking a child's `subprocess`/`os.popen` sandbox calls and fail_fast terminating the run (no re-spawn). **Roadmap status: only optional A3 (trace-aware critique) remains — next direction is the user's call (A3, or the carryover pool).**

- ~~**`AD-LoopTerminated-Wire-Surface`**~~ ✅ **CLOSED by Sprint 57.130** (serializer branch + `WIRE_SCHEMA` 24→25 + codegen + `mergeEvent` flip-pending-tool→error + `terminated · {reason}` danger badge + composer unfreeze; drive-through PASS via a real `web_search` FATAL terminate). [Original (🆕 from the 57.110 drive-through — D-DAY3-2): a FATAL-terminated run (`fail_fast`, rate-limit exhaustion 57.58, any Cat 8 terminator decision) ends with `LoopTerminated` — a **server-side-only event** (not in the wire schema / SSE serializer) → chat-v2 sees a silent stream end + a stuck "pending" tool chip. Surface the termination (reason + detail) to the FE — own slice; pre-existing, NOT a B4 regression.]
- **Deny-list completeness is a threat-model property** (🆕 process — D-DAY3-1): the dt caught the child REWRITING its blocked `os.system` call as `os.popen` (not in the C3 deny-list) and executing it — every gate was green; the completeness test pins pattern↔payload, not threat↔pattern. Fixed-forward (+`os.popen`/`os.spawn*`/`os.exec*`). Practice: enumerate the FAMILY when shipping deny-list entries; consider a periodic sandbox red-team dt.
- **`AD-Subagent-AsTool-FailFast`** (🆕 D-DAY2-1): the as_tool wrapper handler lives behind `SubagentDispatcher.as_tool_factory` — an ABC METHOD; threading fail_fast through it is a contract change (deferred; AS_TOOL failures stay soft-returned; fail_partial salvage already inherits via ForkExecutor).
- **`AD-HarnessPolicy-Tab-FailurePolicy-Field`** (🆕 🟢 FE): the C3 tenant-settings "Harness Policy" tab has no `subagent_failure_policy` field — admins set it via the API today; small FE field.
- **mypy deferred-closure watch** (🆕 1st pt — D-DAY1-1): a closure capturing a later-assigned local defers mypy's re-analysis of the enclosing function → a NEW strict error can surface on an UNTOUCHED line. Fix = explicit Optional annotation. Promote to a Risk Class on 2nd occurrence.
- Plan-deferred unchanged: `AD-Subagent-Child-Verification` (Cat 10 in the child — judge cost; demand-gated) · recursion depth>1 · child escalate-propagation-to-parent-pause (pairs with §2.5 detached teammate).
- Calibration: NEW `subagent-child-governance` **0.55** 1st data point ratio ≈1.1-1.2 IN band upper edge (the over-run = the dt discovery loop, same shape as 57.109); agent-delegated: no.

---

## 🆕 Sprint 57.109 Carryover — C2 compaction cheap tier SHIPPED (drive-through PASS; C-family 3/3 done)

Sprint 57.109 closed proposal §3.4 C2 (CHANGE-076; design note 24 §4 compaction invariant RESOLVED): `make_chat_compactor(profile.cheap)` + `_compaction` cost-ledger attribution (the 57.82 `_verification` sibling — usage rides `ContextCompacted` server-side fields per D-DAY1-1, billing every termination path) + `CHAT_COMPACTION_TOKEN_BUDGET` / `CHAT_COMPACTION_KEEP_RECENT_TURNS` env knobs. Drive-through proved a real summarize (9824→2679, 8 msgs) on `gpt-5.4-mini` with priced `_compaction` cost_ledger rows. Per the interleave (RBAC → C3 → B3 → UX → **C2 ✅** → B4), **next slice: B4** (child governance — the last B slice before optional A3).

- **`AD-Semantic-Compaction-User-Turn-Anchor`** (🆕 from the 57.109 drive-through — load-bearing): semantic compaction was a **latent main-flow NO-OP since 52.1** — chat continuity lives in Cat 3 memory (ONE user message per loop run; transient resets per POST), so the user-turn-anchored cutoff (`len(user_indices) > keep_recent_turns`) never engaged; every gate stayed green. The keep knob makes it deployable (keep=1 + B1 injection proved the machinery); a message-count / token-mass anchor would make it ORGANICALLY reachable — own Cat 4 slice.
- **`AD-Resume-Billing-Observers`** (🆕 🟢 pre-existing): the resume path (`router.py` resume stream) has NO billing/quota observers — loop + verification + compaction tokens all unbilled on resumed continuations.
- **Test-basename Prong-1 watch** (1st pt — D-DAY1-2): pytest unique-basename rule; Glob the basename across the test tree before creating any new test file (57.109: `tests/unit/api/v1/chat/test_category_factories.py` collided with the existing `tests/unit/api/` one — standalone green, full-run collection ERROR). Promote to a Prong-1 row on 2nd occurrence.
- Calibration: `multi-model-profile-spike` 0.55 **2nd data point** ratio ≈1.1-1.2 IN band upper edge (57.97 ~0.93; mean ~1.0 KEEP); agent-delegated: no.

---

## 🆕 Sprint 57.108 Carryover — UX slice: chat-v2 HITL card real tool/reason + Inspector turn metadata SHIPPED (drive-through ALL legs PASS)

Sprint 57.108 closed the chat-v2 UX bundle (CHANGE-075; **closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`** / ISSUE-5). Additive wire fields only (`approval_requested` +tool_name/reason from all 5 escalate sites; `llm_response` +token actuals; count 24 unchanged) + chatStore 4 captures (ZERO component edits — store-driven). Per the interleave decision (RBAC → C3 → B3 → **UX ✅** → C2 → B4), **next slice: C2** (compaction cheap tier — the remaining C slice).

- **Cost carve-out (documented, NOT silently dropped)**: Inspector `cost` + `tokens.thinking` stay honest "—" — cost is post-loop by design (cost_ledger / cost dashboard); only carve `AD-ChatV2-Inspector-Cost-InStream` if a real consumer demands it (YAGNI).
- **`AD-Day0-Prong2-Event-Emission-Order`** (🆕 watch, 1st data point — D9): when FE wiring depends on a SEQUENCE of events, Day-0 must verify EMISSION ORDER, not just each event's shape (`SpanStarted(TURN)` precedes `TurnStarted` — the plan's span_started-side linkage would have attached to the previous turn). Promote to a Prong-2 drift-class row on a 2nd occurrence.
- **`AD-LLMRequest-TokensIn-Zero`** (🆕 🟢 minor): `llm_request.tokens_in` streams 0 on the Azure adapter — populate the pre-call estimate or drop the now-redundant wire field (llm_response actuals are authoritative since 57.108).
- Calibration: `frontend-feature-with-event-wire-addition` 0.55 **2nd data point** ratio ≈1.05-1.1 IN band (57.100 ≈1.0); agent-delegated: no (parent-direct; Explore recon only).

---

## 🆕 Sprint 57.107 Carryover — B3 HANDOFF finish SHIPPED (drive-through 4 legs PASS; first-ever real-LLM handoff)

Sprint 57.107 closed proposal §2.4 B3 (CHANGE-074 + design note 29; closes `AD-ChatV2-SessionList-Backend` + `AD-Subagent-Transcript-Isolation`). Per the interleave decision (RBAC → C3 → B3 ✅ → **UX** → C2 → B4), **next slice: 1 UX slice** — candidates: chat-v2 bundle (`AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`) or `AD-FE-Tenant-Display-Fixture-Phase58`.

- **`AD-Sidechain-Transcript-Read-API`** (🆕) — sidechain sessions + `message_events` rows are WRITE-only (the 57.107 observer persists; nothing reads). A READ API (`GET /sessions/{id}/sidechains` + `GET /sessions/{sid}/events`) + an Inspector replay UI is the natural consumer slice.
- **`AD-RunAll-CWD-Guard`** (🆕 🟢 process) — `scripts/lint/run_all.py` from `backend/` CWD reports 9/10 false-FAIL (CWD-sensitive `--root` defaults); 2nd occurrence 57.107 — add a repo-root guard if it recurs.
- **Intentional behavior change** (record): no-policy tenants now have handoff ON with the 3 default personas (was: impossible — no ToolSpec). Per-tenant kill switch = `handoff_enabled=false`.
- Deferred unchanged: detached/streaming teammate (§2.5 — unlocks the 57.103 inject UI) · depth>1 · multi-hop lineage TREE walk (v1 = parent pointer) · parent-transcript `messages` writes (durable parent transcript remains `state_snapshots`).
- Calibration: `mixed-multidomain-bundle` 0.65 ratio ≈0.8-0.9 IN band (first clean point post-confound); agent-delegated **partial** (FE delegated + parent re-verified; backend parent-direct).

---

## 🆕 Sprint 57.106 Carryover — C3 per-tenant harness policy + risky-action detector SHIPPED (drive-through PASS)

Sprint 57.106 closed proposal §3.4 C3 (CHANGE-073 + design note 28). Per the 2026-06-12 interleave decision (RBAC → C3 → **B3** → UX → C2 → B4), **next slice: B3** (HANDOFF finish — the platform layer is ALREADY done 57.68-70 per the proposal; B3 shrinks to finish + governance, NOT a fresh build).

- **`AD-HITL-Policy-ReadSide-Potemkin-Phase58`** (🆕 from the 57.106 Day-0 Explore) — `DBHITLPolicyStore.get_policy()` (Sprint 57.54 write-side + admin GET/PUT) works but is **never consumed at tool execution**: `ToolGuardrail` Stage 3 hardcodes `if rule.requires_approval: ESCALATE` and does NOT read the tenant's `auto_approve_max_risk` / `require_approval_min_risk` risk thresholds. Risk-threshold semantics redesign = own slice (user decision 2026-06-12: NOT folded into C3).
- **`AD-ChatV2-HITL-Card-Tool-Name`** (🆕 from the 57.106 drive-through) — the chat-v2 HITL approval card renders `tool: —` for an `approval_requested` event (the tool name/reason isn't wired to the card). Pre-existing FE wiring gap; scoped chat-v2 task.
- **`tenant_policies` dedicated table** — evaluated NOT built (note 28 §5): the JSONB-on-meta_data shape is schema-less; graduate to a typed+RLS+versioned table when ≥2 more policy concerns land on meta_data OR a typed-query need arises (the `rate_limit_configs` 0019 precedent).
- capability_matrix per-tenant role/scope/max_calls override; raw verification-template upload; per-tenant injection policy (B-family); C2 compaction cheap tier (remaining C slice).

---

## 🆕 Sprint 57.105 Carryover — RBAC DB→JWT wiring SHIPPED (drive-through PASS, zero dev-login)

Sprint 57.105 closed `AD-RBAC-DB-To-JWT-Wiring-Phase58` (see roadmap block above + CHANGE-072 + note 23 §5 RESOLVED). Per the 2026-06-12 interleave decision (RBAC → C3 → B3 → UX → C2 → B4, 1 UX slice per 2-3 harness slices), **next slice: C3** (per-tenant policy 面 + risky-action detector).

- ~~**`AD-FE-Tenant-Display-Fixture-Phase58`**~~ ✅ **SHIPPED Sprint 57.123** (CHANGE-090) — the sidebar tenant-switcher + topbar tenant pill + UserMenu 3-tenant switcher rendered fixture **"acme-prod tenant_01h9a2 · Pro"** regardless of the real logged-in tenant. Fixed: `/auth/me` `AuthMeTenant` += plan + region (real `Tenant` cols, ALL 3 build sites) → FE `AuthTenant` auto-threads → the 3 components read `authStore.tenant`; the UserMenu collapses 3→1 to the single real current tenant. Drive-through PASS (chrome FOLLOWS session across 2 real logins). Residual (low-priority): the dev-login picker labels (dev-only tool, not 主流量) + the sidebar chevron/"Switch tenant" tooltip (mockup-fidelity) + `FIXTURE_UNREAD_COUNT` (separate non-tenant chrome fixture).
- **`AD-Register-OIDC-User-Linkage-Phase58`** — still open (register-by-email vs callback-upsert-by-external_id second-user-row risk; why the 57.105 drive-through spine is password-login).
- dev-login `_DEV_LOGIN_ROLES` hardcode — dev-only debt (prod 404), documented in CHANGE-072; folds into the OIDC-linkage slice when picked.
- Claim staleness until re-login — **documented invariant** (no token refresh by design — AP-6 avoidance), not an open item.

---

## 🆕 Sprint 57.103 Carryover — B2b inject-to-teammate: backend primitive + US-5 SHIPPED; inject UI 🚧 DEFERRED to §2.5 (await-completion finding)

Sprint 57.103 (B2b) shipped the **backend primitive** (proven, reusable) + the **US-5 inline mode-aware label** (drive-through-proven), but the **inject UI control is blocked by the await-completion + buffered-relay architecture** and was removed per Option A (no dead control).

- **SHIPPED + proven** — US-1 the `POST /chat/{id}/subagents/{sid}/inject` endpoint; US-2 the `TeammateInboxScope` lifecycle (`make_teammate_inbox_scope` registers the teammate's queue only while it runs); US-3 `MessageInjected`-in-relay; US-5 `SubagentForkBlock` "Teammate · peer" + real tokens (drive-through: "Teammate · peer" + "4,013 tok"; parent integrated "Teammate subagent finding (checkout patrol)" + verified). Commits `7e873583` + `35c4e797` + `982520a7`. See `CHANGE-070`.
- **🔴 inject UI (US-4/6) — DEFERRED → §2.5** — the Cat 11→12 SSE relay (Sprint 57.95) buffers `SubagentSpawned`/`Child`/`Completed` + flushes them only when the parent loop yields its NEXT event, which is AFTER the awaited teammate completes. So the FE **never observes a teammate as "running"** → a control gated on `status === "running"` can never render. The live inject window needs the **detached / streaming teammate** (proposal §2.5: the parent reasons while the child runs, OR the SSE relay streams subagent events live). When §2.5 lands, rebuild the inject control (`injectToSubagent` + the `InspectorTree` gated control; the `message_injected` child-row render is already wired) on top of the proven backend primitive.
- **Planning lesson (→ candidate AD for sprint-workflow Prong-2)** — when a feature's gating depends on a live in-progress state of a subagent/child, verify at Day-0 that the FE actually RECEIVES that state live (trace emit → SSE flush → store), not just that the event exists. A buffered / turn-boundary relay collapses in-progress states.
- **Deferred (unchanged)** — depth>1 child-of-child inject routing; per-tenant teammate inject policy (C3); durable teammate transcript.

---

## 🆕 Sprint 57.102 Carryover — B2a TEAMMATE real multi-turn child loop SHIPPED; B2b inject-to-teammate (FE producer) next

**Source**: Sprint 57.102 closed 2026-06-11 — harness-deepening workflow B slice B2 (first half). TEAMMATE single-shot → real multi-turn child loop (mirror 57.94 FORK) + `send_to_parent` tool (child→parent report folded into the summary) + the B1 `MessageInbox` wired (reuse 57.101; `TeammateChildLoopFactory` + an `inbox_factory` over `InjectionRegistry` keyed by `subagent_id`). Backend-only, `loop.py` unchanged, no new wire event (reuses `SubagentChildEvent` 57.96), no DB, no FE. Drive-through PASS (real Azure gpt-5.2: parent `task_spawn mode=teammate` → teammate 3-turn loop `mock_patrol_check_servers`→`send_to_parent`→answer → parent integrated the report). Day-0 split B2 into B2a (this) / B2b after confirming the await-completion constraint (the parent blocks on the child; live parent→child mid-run injection needs a detached teammate, deferred). Detail: `memory/project_phase57_102_teammate_multiturn.md` + CHANGE-069 + 17.md + design note 20 edit.

- **B2b — chat-user inject-to-teammate** (🔴 next slice) — the live UI producer for the teammate inbox B2a wired: `POST /chat/{id}/subagents/{subagent_id}/inject` (extend B1's inject with a subagent target, gated on the parent session active+owned + the child registered) + the `InjectionRegistry` spawn-time registration/unregistration for the child + the FE inject-to-teammate control + render of the injected child turn + that inbox's drive-through.
- **B2b — inline SubagentForkBlock mode-awareness** (🟢 FE, surfaced by the 57.102 drive-through) — the inline conversation fork-block hardcodes "Fork · concurrent" + shows "0t" for a teammate spawn (a pre-existing 57.95/96 carryover; the authoritative Inspector **Tree** correctly shows "teammate" + the real token count). Make the inline block mode-aware + fix the 0t display.
- **detached / non-blocking teammate** (🟢, deferred — proposal §2.5) — live parent→child mid-run injection (the parent reasons WHILE the child runs) needs non-blocking spawn + teammate lifecycle management. YAGNI until a real use case.
- **depth>1 (child-of-child)** (🟢) — the teammate child is recursion-bounded at 1 (no task_spawn); two-level `subagent_id` routing + nested render is a separate slice.
- `subagent-teammate-multiturn-spike` calibration class 0.55 (1st data point; ratio ~0.95-1.0 IN band; pending 2-3 sprint validation; `agent_factor` 1.0 parent-direct).

---

## 🆕 Sprint 57.101 Carryover — B1 between-turns injection primitive SHIPPED; B2 TEAMMATE reuses the drain seam next

**Source**: Sprint 57.101 closed 2026-06-11 — harness-deepening workflow B slice 1. A chat-v2 user injects an instruction MID-RUN; the loop drains it at the next turn boundary (`MessageInbox` ABC + `_run_turns` drain) and the agent picks it up. D-DAY1-1: the injection is an INPUT → it runs `check_input` (a non-PASS injection is dropped + `GuardrailTriggered(input)`), NOT the between-turns gate (which checks OUTPUTs). Module-level `InjectionRegistry` + `POST /{id}/inject`; new `MessageInjected` wire (count 23→24); FE composer usable mid-run (real_llm). Drive-through BOTH cases PASS (real Azure gpt-5.2). Detail: `memory/project_phase57_101_between_turns_injection.md` + CHANGE-068 + design note 26 + 17.md.

- **B2 TEAMMATE multi-turn** (🔴 next slice) — reuse the B1 `MessageInbox` ABC: give the child loop an inbox backed by the parent's mailbox channel (`teammate.py` factory→child-loop + `send_to_parent` + the B1 drain seam). The next harness-deepening B-workflow slice.
- **pause-on-injection** (🟢) — today a guardrail-blocked injection is DROPPED + `GuardrailTriggered(input)`; a HITL pause-on-injection (instead of drop) is a follow-on if a use case appears.
- **inject-during-HITL-pause** (🟢) — the loop is paused (not running) → the inject endpoint 409s; re-injecting into a paused loop is a separate concern (the 57.99 REJECT-with-note already covers the reviewer-note path).
- **optimistic FE echo / edit-or-cancel a queued injection / durable injection across resume** (🟢) — B1 renders on the `message_injected` drain (proof it landed); the queue is in-memory per-run; these are follow-ons.
- **per-tenant injection policy (rate-limit / disable)** (🟢) — workflow C (C3).
- `loop-injection-primitive-spike` calibration class 0.55 (1st data point; pending 2-3 sprint validation; `agent_factor` 1.0 parent-direct).
- **Infra-startup operational lesson** (🟢, process) — the dev infra (Docker Postgres/Redis/RabbitMQ) being DOWN makes integration tests time out ~104s/file (looks like a hang); always `docker compose ps` + port check BEFORE reading a slow integration suite as a code bug; never run 2 full-suites concurrently (test-DB contention).

---

## 🆕 Sprint 57.100 Carryover — chat-v2 verification-reject UI SHIPPED (the A2 reviewer-UI follow-up); net-new candidates below

**Source**: Sprint 57.100 closed 2026-06-11 — the A2 reviewer-UI follow-up. Surfaced the pause `kind` on the `approval_requested` wire (additive field, no new event type) → the chat-v2 `HITLTurn` branches REJECT on `kind="verification"` (coaching-note textarea → `decide(reason)` + `resume()`) + a kind-aware meta row. Drive-through PASS (the REJECT half — the 57.99 finding CLOSED). Detail: `memory/project_phase57_100_chatv2_verification_reject_ui.md` + CHANGE-067 + 17.md + 25.md §4.

- **rich verification-specific approval card** (🟢) — re-render the held answer + the verifier reasons richly INSIDE the card (today the inline `VerificationBlock` shows them above the card — sufficient, not gold-plated). A frontend follow-on.
- **`ApprovalCard.tsx` fallback kind-aware** (🟢) — the legacy 53.5 dual-emit fallback card could branch REJECT on `kind` too (low priority; the canonical chat-inline `HITLTurn` is the live path).
- **soft forced-fail judge template for drive-throughs** (🟢) — a reusable `{"passed": false}` judge prompt that does NOT trip Azure's jailbreak content-filter (the 57.100 D-DAY3-1 / 57.99 D-DAY3-2 family); store under `verification/templates/` for future verification drive-throughs.
- `frontend-feature-with-event-wire-addition` calibration class 0.55 (1st data point ~1.0 IN band; pending 2-3 sprint validation; `agent_factor` 1.0 parent-direct).

---

## 🆕 Sprint 57.99 Carryover — A2 verification-ESCALATE SHIPPED (max-fail terminal → conditional human pause; APPROVE-delivers / REJECT-coaches-one-turn); the chat-v2 reject UI + A3 + the rest next

**Source**: Sprint 57.99 closed 2026-06-10 — workflow A slice 2 (the 4th pause leg). The A1 `verification_failed` terminal now conditionally ESCALATEs to a human pause behind `chat_verification_escalate_on_max` (default OFF = A1 byte-identical); `resume()` `kind="verification"` — APPROVE delivers the held failed answer (human overrides the judge, reuses 57.93 `_replay_approved_output`, TERMINAL), REJECT-with-note re-injects the note + runs ONE human-coached turn then binds to the A1 terminal (durable `verification_escalated` flag on `metadata`). NO new event/wire/DB/DTO/frontend. Drive-through PASS (APPROVE half, real UI + real Azure + forced-fail real-LLM judge). Detail: `memory/project_phase57_99_verification_escalate.md` + CHANGE-066 + `25-verification-in-loop-design.md` §4 (A2 invariant SHIPPED).

- **chat-v2 verification-reject UI follow-up** — ✅ **SHIPPED Sprint 57.100** (CHANGE-067): added `kind` to the `approval_requested` wire (additive field, no new type) → `HITLTurn` branches REJECT on `kind="verification"` (a coaching-note textarea → `decide(reason)` + `resume()`) + a kind-aware meta row; drive-through PASS (the REJECT half). The 57.99 "REJECT not UI-drivable" finding is CLOSED. Detail: `memory/project_phase57_100_chatv2_verification_reject_ui.md`.
- **A3 — trace-aware critique** (🟢) — a verifier that sees recent turns / tool errors (not just the final string) + a formal cheap-judge accuracy benchmark (design-note 24+25 carryover).
- **per-tenant verification mode / policy** (🟡 — Config 分層 = workflow C / C3) — a tenant choosing its own escalate / verification policy.
- **deliver-with-flag terminal** (🟢, option b) — deliver the answer but flag verification failed; not chosen for A1/A2 (would need a new event/UI flag).
- **multi-round human coaching** (🟢) — A2 bounds to EXACTLY one coached turn; a >1-turn human-coaching loop is a separate slice.
- **cheap-judge accuracy benchmark** (🟢) — whether the cheap tier (57.97) over/under-corrects vs strong; documented, NOT measured.
- **forced-fail drive-through fixture lesson** (D-DAY3-2) — a tool-equipped agent ACTS on a forced fail (calls `request_approval`) rather than passively re-answering; a forced-fail correction must steer "no tools, just re-answer" so the candidate stays a FINAL answer (else a tool-kind pause fires, not the verification escalate). Reusable when authoring future verification drive-throughs.
- `loop-pause-point-feature` calibration class 0.50 (1st data point ~0.93 IN band; pending 2-3 sprint validation; `agent_factor` 1.0 parent-direct; honours the 57.92/93 proposed ~0.40, set higher for the bounded REJECT continuation).

---

## 🆕 Sprint 57.98 Carryover — A1 verification-into-loop SHIPPED (gate moved in-loop, wrapper retired, resume hole closed); A2/A3 + the rest next

**Source**: Sprint 57.98 closed 2026-06-10 — workflow A slice #1. The Cat 10 verify gate moved from the outer `run_with_verification` wrapper INTO `_run_turns` as a pre-delivery gate (after the Cat 9 output guardrail, before the terminator); the attempt counter is durable across pause→resume via `metadata["verification_attempts"]`; the max terminal is `LoopCompleted(stop_reason="verification_failed")`; the resume path is now verified for free (`resume()` drives the shared `_run_turns` + the ctor injection) — closing a real correctness hole (pre-57.98 a HITL-paused→resumed answer was delivered un-verified); `correction_loop.py` retired (sole consumer was the router). Drive-through PASS (the gate fires IN-STREAM before `loop_end`; resume re-enters the gated loop). Detail: `memory/project_phase57_98_verification_in_loop.md` + CHANGE-065 + design note `25-verification-in-loop-design.md`.

- **A2 — verification-ESCALATE human-in-the-loop** (🟡 — the natural next A slice) — on max-attempts (or a config), ESCALATE → `_emit_deferred_pause(kind="verification")` + human approve / reject-with-note → the note re-injects as human-coached correction feedback. A1's terminal is `verification_failed`; A2 swaps it for the pause. Reuses the 57.91-93 pause基建.
- **A3 — trace-aware critique** (🟢) — a verifier that sees recent turns / tool errors (not just the final string) + a formal cheap-judge accuracy benchmark (design-note 24+25 carryover).
- **deliver-with-flag terminal** (🟢, option b) — deliver the answer but flag verification failed; not chosen for A1 (would need a new event/UI flag).
- **per-tenant verification mode / template** (🟡 — Config 分層 = workflow C / C3) — a tenant choosing its own verification policy.
- **cheap-judge accuracy benchmark** (🟢) — whether the cheap tier (57.97) over/under-corrects vs strong; documented as a design-note Open Invariant, NOT measured. The action turn is NEVER verified-away (quality preserved).
- **judge-token accounting across a mid-correction pause** (🟢, D-DAY1-3) — within a non-paused run the verif tokens accumulate + stamp the terminal correctly; a rare pause-mid-correction may under-count (no `LoopCompleted` fires until resume). The attempt COUNTER is durable; the cross-pause token accounting is documented, not fixed.
- **strict-judge drive-through template** (🟢) — a template to force a real fail-then-pass + verified-resumed-FINAL for a future drive-through (A1's literal fail-then-pass was unit-proven, not drive-driven — a real gpt-5.2 answer passes the judge first try).
- `verification-in-loop-spike` calibration class 0.60 (1st data point ~0.92 IN band; pending 2-3 sprint validation; `agent_factor` 1.0 parent-direct).

---

## 🆕 Sprint 57.97 Carryover — Multi-model profile SHIPPED (verification → cheap tier); other phases + per-tenant policy + accuracy benchmark next

**Source**: Sprint 57.97 closed 2026-06-10 — the FIRST multi-model parity gap (cc-parity §4 C-class #1 ROI). A thin provider-neutral `ModelProfile{action, cheap}` value object (`adapters/_base/model_profile.py`) pairs two pre-built `ChatClient`s by role; `build_azure_model_profile` (`adapters/azure_openai/profile.py`) routes the per-request verification (Cat 10 llm_judge) to a cheap Azure deployment (gpt-5.4-mini) while the main turn + compaction keep the strong tier (gpt-5.2). The `ChatClient` ABC fixes model at construction (no per-call `model=`) → the seam is construction-time DI → `loop.py` diff=0, no ABC/event/DB change; unset cheap env → `cheap is action` (byte-identical). Drive-through PASS (~62% cheaper verification, cost_ledger-proven). Detail: `memory/project_phase57_97_multi_model_profile.md` + CHANGE-064 + design note `24-multi-model-profile-design.md`.

- **Compaction cheap-tier** (🟡 — highest token-volume target) — the seam is built; add a `profile.compaction` field (defaults to `action`) + the compactor factory reads it. Needs a long conversation to drive-through (compaction only triggers near the context budget).
- **Memory-extraction cheap-tier** (🟢) — same pattern (`memory/extraction.py` accepts a `ChatClient` at construction).
- **Thinking cheap-tier** (🟢) — route a cheaper model for non-final reasoning turns; needs in-loop phase awareness (see next item).
- **Thread `ModelProfile` into the loop** (🟡) — this sprint kept it handler-local (constructed + consumed in `handler.py`). In-loop per-phase model selection (e.g. cheap for intermediate turns, strong for the final answer) is a separate slice.
- **Per-tenant model policy (Config 分層)** (🟡) — a tenant choosing its own model/budget/guardrail override is the SEPARATE cc-parity §7.3 "Config 分層" gap, not multi-model profile.
- **Cheap-judge accuracy benchmark** (🟢) — a cheaper judge MAY be less reliable; documented as a design-note Open Invariant, NOT formally measured. If it visibly mis-verifies, keep the judge on the strong tier (the seam supports per-phase choice). The action turn is NEVER cheap (user-facing quality preserved).
- **Non-Azure cheap-tier builder** (🟢) — the seam is provider-neutral but only `build_azure_model_profile` is wired; an Anthropic/OpenAI cheap-tier builder is a follow-on.
- **LLM-call Trace span `model` attribute** (🟢) — deferred: the cost-ledger sub_type already carries the model attribution; add a span attr only if a future Trace-view feature needs per-call model on the span.
- `multi-model-profile-spike` calibration class 0.55 (1st data point ~0.93 IN band; pending 2-3 sprint validation).

---

## 🆕 Sprint 57.96 Carryover — Cat 11 Scope B child turn-stream nesting SHIPPED; recursion depth>1 + TEAMMATE/HANDOFF + leg-3 mid-thinking next

**Source**: Sprint 57.96 closed 2026-06-09 — closes the remaining (turn-stream) half of `AD-Subagent-Child-Event-SSE-Relay`. The chat Inspector "Tree" subagent node now EXPANDS to the child loop's per-turn TAO via a NEW `SubagentChildEvent(subagent_id, inner)` wrapper event (wire type `subagent_child`). The wrapper IS a `LoopEvent` → it rode the existing 57.95 emitter + the already-generic router buffer-drain → **`loop.py`/`router.py`/`LoopEvent` base UNCHANGED**; `ForkExecutor._drive` forwards the TAO subset (tagged with `subagent_id`) via the dispatcher's `_emit_safely` (AS_TOOL inherits free); frontend `SubagentNode.childEvents` + `chatStore` `subagent_child` routing + `InspectorTree` nested rows. Drive-through PASS (the FORK node expands to `turn 0 / LLM / → echo_tool() / ← echo_tool · … / turn 1 / LLM`; the Trace shows the relayed `subagent_child` frames). Detail: `memory/project_phase57_96_subagent_child_turnstream.md` + CHANGE-063.

- ~~**Recursion depth > 1 (child-of-child turn-stream)** (🟡)~~ ✅ **CLOSED 2026-06-17 as YAGNI (by design)** — Day-0 found children are built WITHOUT a `subagent_dispatcher` (`handler.py:354-356,363,401`: *"a child cannot itself spawn (depth bounded at 1)"*), a deliberate recursion-safety bound. depth>1 is unreachable without first removing that bound (no product need → AP-6). See `claudedocs/5-status/subagent-tree-relay-diagnostic-20260617.md`.
- **Full-fidelity child events** (🟢) — the non-TAO child events (`LLMRequested`/`PromptBuilt`/`MemoryAccessed`/`Span*`/`Metric*`/`Checkpoint`/`ContextCompacted`) were deliberately excluded (locked TAO subset). A future "show everything" toggle could relay them; low priority (Tree noise).
- **Inline `SubagentForkBlock` `0t` token/turn display** (🟢 minor frontend) — the inline fork-block in the conversation turn shows `{a.turns}t` = 0 (integer turn count, a separate component from the Tree; NOT a token bug). Surfaced by both the 57.95 + 57.96 drive-throughs; not a regression.
- **TEAMMATE / HANDOFF real loops · `HandoffService`** (🟡) — extend the 57.94 child-loop + 57.96 turn-stream pattern to modes 2/4 (TEAMMATE is single-shot + mailbox; HANDOFF's loop-side terminator is wired but the platform service is absent).
- **`AD-Subagent-Child-Span-Nesting`** (🟢) — `task_spawn` passes `trace_context=None` → the child LOOP span isn't explicitly parented. Orthogonal to the SSE relay.
- Other Cat 11 deferrals: `AD-Subagent-Transcript-Isolation` · `AD-Subagent-Child-Governance` (Cat 9/10 inside the child) · failure policies (FAIL_FAST/SOFT/PARTIAL).
- **Slice 3 leg 3 — mid-thinking pause** (🟡 — the ONLY remaining generalized-pause-point leg from 地基 A) — orthogonal to Cat 11.
- `subagent-child-turnstream-nesting` calibration class 0.55 (1st data point ~0.9-1.1 IN band; pending 2-3 sprint validation).

---

## 🆕 Sprint 57.95 Carryover — Cat 11 → Cat 12 subagent SSE relay SHIPPED (node-level); Scope B child turn-stream + TEAMMATE/HANDOFF next

**Source**: Sprint 57.95 closed 2026-06-09 — closes `AD-Subagent-Child-Event-SSE-Relay` at the **node level**. The chat subagent dispatcher's `event_emitter` is now wired (`make_chat_subagent_dispatcher` ← a router-owned buffer drained by `_stream_loop_events`), so `SubagentSpawned`/`SubagentCompleted` reach the SSE stream and the Inspector "Tree" tab shows the FORK subagent node (was "no subagents"). Day-0 探勘 found the relay chain already existed (dispatcher `event_emitter` slot + emission since 57.12, `sse.py` serialization, `chatStore`/`InspectorTree` consumers); the only gap was the unwired emitter → **NO `LoopEvent` contract change, NO frontend change, `loop.py` UNCHANGED**. Drive-through PASS (Tree node `fork` · completed · 3,692 tok · "subagent node is visible" + Trace `subagent_spawned`/`subagent_completed` frames). Detail: `memory/project_phase57_95_subagent_sse_relay.md` + CHANGE-062.

- **Scope B — child INNER turn-stream nesting** (🟡 — the remaining half of `AD-Subagent-Child-Event-SSE-Relay`) — the Tree shows the subagent as a single collapsed node; to EXPAND it to show the child's per-turn TAO loop (the child's `LLMResponded`/`ToolCall`), relay the child's INNER `LoopEvent`s. Needs a `LoopEvent` base `parent_session_id`/`depth` field (or a wrapper event) + `ForkExecutor` forwarding every child event (currently drained, not relayed) + frontend nested render + `chatStore` routing by `subagent_id`. Larger; touches the contract + frontend.
- **Inline `SubagentForkBlock` `0t` token-display** (🟢 minor frontend) — the inline fork-block in the conversation turn shows `0t` while the Tree node + the `subagent_completed` frame correctly show 3,692 tokens. A frontend dual-emit display detail surfaced by the 57.95 drive-through; not a 57.95 regression (backend-only sprint).
- **`AD-Subagent-Child-Span-Nesting`** (🟢) — `task_spawn` passes `trace_context=None` → the child LOOP span isn't explicitly parented. Orthogonal to SSE relay.
- **TEAMMATE / HANDOFF real loops · `HandoffService`** (🟡) — extend the 57.94 child-loop pattern to modes 2/4.
- Other Cat 11 deferrals: recursion depth > 1 · `AD-Subagent-Transcript-Isolation` · `AD-Subagent-Child-Governance` · failure policies (FAIL_FAST/SOFT/PARTIAL).
- **Slice 3 leg 3 — mid-thinking pause** (🟡 — the ONLY remaining generalized-pause-point leg from 地基 A) — orthogonal to Cat 11.
- `subagent-sse-relay-wiring` calibration class 0.55 (1st data point ~0.9-1.0 IN band; pending 2-3 sprint validation).

---

## 🆕 Sprint 57.94 Carryover — Cat 11 FORK real child loop SHIPPED (地基 A payoff Slice 1); TEAMMATE/HANDOFF + SSE-relay + leg-3 mid-thinking next

**Source**: Sprint 57.94 closed 2026-06-09 — the FIRST real child agent loop in Cat 11. FORK now drives a real multi-turn, tool-capable child `AgentLoopImpl` (reusing the re-enterable `run()`/`_run_turns`, **ZERO `loop.py` change** — the 57.89 payoff) via an injected `ChildLoopFactory` built at `build_real_llm_handler`, with a recursion-safe tool subset (`make_default_executor(subagent_dispatcher=None)` → no task_spawn/handoff → depth bounded at 1). AS_TOOL inherits the real loop; TEAMMATE/HANDOFF unchanged. No single-shot fallback (US-5 → no AP-10). **Drive-through PASS** (real chat-v2 + Azure: `task_spawn` → child uses `echo_tool` → `summary="child loop is real"` + 3684 tokens + 2389ms TOOL_EXEC span — impossible under the old single-shot). Detail: `memory/project_phase57_94_subagent_fork_child_loop.md` + CHANGE-061 + design note `20-subagent-child-loop-design.md`.

- **TEAMMATE real loop** (🟡) — `teammate.py` stays single-shot + mailbox; a mailbox-consuming multi-turn teammate is a separate slice (now that the FORK child-loop pattern is proven).
- **HANDOFF consumer / `HandoffService`** (🟡) — the loop-side `stop_reason="handoff"` terminator is wired (57.68/69); the platform service that boots the child session + emits `AgentHandoff(new_session_id)` is absent. Separate slice.
- ~~**`AD-Subagent-Child-Event-SSE-Relay`** (🟡)~~ ✅ **FULLY CLOSED 2026-06-17** — this line-469 "built WITHOUT emitter / no subagents / child HEADLESS" framing is STALE (the pre-57.95 problem statement). 2026-06-17 diagnostic drive-through (real chat-v2 UI + real Azure + real backend) proved the chat dispatcher IS wired with the emitter (`handler.py:440`, Sprint 57.95) → `task_spawn` (fork) → Inspector **Tree** tab renders the subagent (`b6a11c09 · fork · Depth 1 · 1,826 tok · child turn 0`), NOT "no subagents". node-level relay (57.95) ✅ + depth-1 child turn-stream (57.96) ✅ + depth>1 = YAGNI-by-design (above). Full evidence + Day-0: `claudedocs/5-status/subagent-tree-relay-diagnostic-20260617.{md,jpeg}`. (Untested/separate: TEAMMATE/HANDOFF-mode Tree relay — only `fork` was driven.)
- **`AD-Subagent-Child-Span-Nesting`** (🟢) — the `task_spawn` handler passes `trace_context=None` to `spawn`, so the child's LOOP span is not explicitly parented (best-effort via ambient tracer); the parent trace shows only the wrapping `task_spawn` TOOL_EXEC span. Thread the parent loop ctx for true nesting.
- **Slice 3 leg 3 — mid-thinking pause** (🟡 — the ONLY remaining generalized-pause-point leg from 地基 A) — interrupt an in-flight streaming LLM call + checkpoint mid-stream. Still deferred; orthogonal to Cat 11.
- Other Cat 11 deferrals: recursion depth > 1 / nested spawning · `AD-Subagent-Transcript-Isolation` (parentUuid chain / child checkpoint) · `AD-Subagent-Child-Governance` (Cat 9/10 inside the child) · failure policies (FAIL_FAST/SOFT/PARTIAL).
- `subagent-child-loop-spike` calibration class 0.60 (1st data point ~0.93 IN band; pending 2-3 sprint validation).

---

## 🆕 Sprint 57.93 Carryover — output-guardrail leg SHIPPED (output ESCALATE pre-delivery pause); leg 3 mid-thinking + subagent next

**Source**: Sprint 57.93 closed 2026-06-09 — the THIRD generalized pause point on `_emit_deferred_pause`: output-guardrail ESCALATE **pre-delivery** pause. Reuses the EXISTING `GuardrailType.OUTPUT` + `check_output` (no new type, unlike leg 2). A conditional **pre-gate** (`_cat9_output_escalate_pause` + `_cat9_output_hitl_pause`) runs the OUTPUT chain in `_run_turns` right after `parse(...)`, **BEFORE `LLMResponded`** (gated on `is_final_answer` + full deferred-HITL wiring) → ESCALATE on a FINAL answer pauses (output-kind, no tool_call, carries held-answer `response_snapshot`). **The pre-delivery placement is load-bearing**: the frontend renders the answer from the `llm_response` SSE event, so a pause at the existing post-`LLMResponded` check would be a Potemkin. `resume()` output kind is TERMINAL (does NOT drive `_run_turns`): APPROVED → `_replay_approved_output` re-emits the held answer from the snapshot (no LLM re-call), REJECTED → `GUARDRAIL_BLOCKED`. Real trigger = `OutputKeywordEscalationGuardrail` at priority=5 (D-DAY0-1: before default Toxicity p10/SensitiveInfo p20; fail-fast-first-non-PASS). Drive-through PASS (withhold-then-deliver / withhold-permanently; no frontend change). Detail: `memory/project_phase57_93_output_guardrail_pause.md` + CHANGE-060 + `19-pause-resume-design.md §5`.

- **Slice 3 leg 3 — mid-thinking pause** (🟡 hardest, **the ONLY remaining generalized-pause-point leg** — input/between-turns/output/tool all shipped) — interrupt an in-flight streaming LLM call + checkpoint mid-stream. Separate sprint; the durable tail (`_emit_deferred_pause`) exists; the new work is interrupting/checkpointing a streaming call.
- **Output-on-non-final ESCALATE pause** (🟢 small refinement) — this sprint scoped the pre-gate to FINAL answers only (the most meaningful "approve before deliver"); pausing on a TOOL_USE turn's text whose output escalates is a possible future refinement (the per-response `_cat9_output_check` ESCALATE stays "continue"; the tool guardrail already pauses before tool exec).
- **Subagent child-loop (Cat 11)** (🟡 downstream) — consumes the shared re-enterable `_run_turns` + the now-generalized pause machinery. Distinct larger sprint; the 地基 A lifecycle 骨架 feeds it.
- **`loop-pause-point-feature` calibration class** (🟢 process — **TRIGGER NOW MET**) — propose ~0.40: 3 consecutive feature-add-on-pause-primitive sprints (57.91 + 57.92 + 57.93) all landed < 0.7 at `backend-core-loop-refactor` 0.55 (the leg-1 keystone makes each subsequent pause point a thin mirror). Record as a proposal pending 2-3 sprint validation in the next pause-point plan; KEEP `backend-core-loop-refactor` 0.55 for genuine extraction/rewire (Slice 1/2 shape).
- 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (the output pause adds the held-answer `response_snapshot` checkpoint writer) / `AD-Resume-Tenant-Capability-Policy` (now also per-tenant output phrases) / `AD-Resume-Reject-Path` (**re-confirmed by this sprint's reject drive**: the frontend records `/decide` but does NOT call `/resume`, leaving a dangling checkpoint).

---

## Sprint 57.92 Carryover — Slice 3 leg 2 SHIPPED (between-turns guardrail ESCALATE); output-guardrail ✅ DONE (Sprint 57.93); leg 3 + subagent next

**Source**: Sprint 57.92 closed 2026-06-08 — Slice 3 leg 2: the SECOND generalized pause point on `_emit_deferred_pause` — between-turns guardrail ESCALATE. NEW `GuardrailType.BETWEEN_TURNS` + `check_between_turns` (distinct chain → no double-fire with the per-response OUTPUT check); a gate at the `_run_turns` loop TOP (after ≥1 completed turn, before the next LLM call) → ESCALATE pauses BETWEEN turns (`pending_approval.kind="between_turns"`, no tool_call); `resume()` continues with `skip_between_turns_once`. **The loop-top seam (not the dormant mid-turn `_cat9_output_check` ESCALATE branch) was the key correctness choice** — a mid-output-check pause would re-call the LLM on resume → re-generate + re-escalate. Real trigger = `BetweenTurnsKeywordGuardrail` + a non-escalate `note_tool` (echo_tool can't reach a between-turns boundary). Drive-through PASS (no frontend change). Detail: `memory/project_phase57_92_between_turns_pause.md` + CHANGE-059 + `19-pause-resume-design.md §5`.

- **Slice 3 leg 3 — mid-thinking pause** (🟡 hardest) — interrupt an in-flight streaming LLM call + checkpoint mid-stream. Separate sprint; the durable tail (`_emit_deferred_pause`) exists, the new work is interrupting/checkpointing a streaming call.
- **Output-guardrail ESCALATE pause** (🟢 small, but has a gotcha) — the per-response `_cat9_output_check` ESCALATE (currently "continue") → pause. **Distinct from the between-turns gate** (per-response, mid-turn) — would need the same re-generation question answered that the between-turns gate sidestepped by using the loop-top seam. The primitive supports it.
- **Subagent child-loop (Cat 11)** (🟡 downstream) — consumes the shared re-enterable `_run_turns` + the now-generalized pause machinery. Distinct larger sprint; the 地基 A lifecycle 骨架 feeds it.
- **`loop-pause-point-feature` calibration class** (🟢 process) — propose ~0.40 in the next pause-point sprint's plan: 2 consecutive feature-add-on-pause-primitive sprints (57.91 + 57.92) both landed < 0.7 at `backend-core-loop-refactor` 0.55; the leg-1 keystone makes each subsequent pause point a thin mirror. A 3rd same-shape point confirms.
- 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (the between-turns pause adds another `resume_messages` writer) / `AD-Resume-Tenant-Capability-Policy` (now also per-tenant between-turns phrases) / `AD-Resume-Reject-Path` (a between-turns reject leaves a dangling checkpoint the same way).

---

## Sprint 57.91 Carryover — Slice 3 leg 1 SHIPPED (generalized pause primitive + input-ESCALATE); leg 2 ✅ DONE (Sprint 57.92)

**Source**: Sprint 57.91 closed 2026-06-08 — Slice 3 leg 1: extracted the generalized `_emit_deferred_pause` primitive (durable-pause tail decoupled from a tool; `pending_approval.kind` discriminator) + the FIRST new pause point = input-guardrail ESCALATE (pauses before any LLM call, no tool; resume continues to the first LLM turn). New `KeywordEscalationGuardrail` (Cat 9 input). Drive-through PASS (no frontend change). Detail: `memory/project_phase57_91_generalized_pause_input_escalate.md` + CHANGE-058 + `19-pause-resume-design.md §5`.

- **Slice 3 leg 2 — between-turns pause** — ✅ **DONE (Sprint 57.92)**: shipped as a between-turns guardrail ESCALATE (loop-top gate; not the budget/turn-count framing — the trigger-policy design landed on a content-driven guardrail per AskUserQuestion). See the Sprint 57.92 Carryover section above.
- **Slice 3 leg 3 — mid-thinking pause** (🟡 hardest) — interrupt an in-flight streaming LLM call. Separate.
- **Output-guardrail ESCALATE pause** (🟢 small) — the primitive supports it (an output ESCALATE → pause before the answer is committed). Possible smaller future leg.
- **Subagent child-loop (Cat 11)** (🟡 downstream) — consumes the shared re-enterable `_run_turns` + the now-generalized pause machinery. Distinct larger sprint; the 地基 A lifecycle 骨架 feeds it.
- 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (the input pause adds another `resume_messages` writer) / `AD-Resume-Tenant-Capability-Policy` (now also per-tenant input-escalation phrases) / `AD-Resume-Reject-Path` (an input-kind reject leaves a dangling checkpoint the same way).

---

## Sprint 57.90 Carryover — `AD-Resume-Continuation-Fidelity` CLOSED (Slice 1+2); Slice 3 leg 1 ✅ DONE (Sprint 57.91)

**Source**: Sprint 57.90 closed 2026-06-08 — Slice 2/2: rewired `resume()` onto the shared `_run_turns` + DELETED `_resume_continuation` + multi-pause-per-run + drive-through PASS. **`AD-Resume-Continuation-Fidelity` is now CLOSED.** Detail: `memory/project_phase57_90_resume_reentrancy_slice_2.md` + CHANGE-057 + `19-pause-resume-design.md §5`.

- **`AD-Resume-Continuation-Fidelity` Slice 3** — ✅ **leg 1 DONE (Sprint 57.91)**: generalized pause primitive + input-ESCALATE pause point (see Sprint 57.91 Carryover above); legs 2/3 (between-turns / mid-thinking) carried forward there.
- **Subagent child-loop (Cat 11)** (🟡 downstream) — consumes the shared re-enterable `_run_turns` (no longer inherits the reduced-copy debt — a child loop can now pause/resume properly). Distinct larger sprint; the 地基 A lifecycle 骨架 (pause-resume + re-entrant loop) now feeds it.
- **Cat 8 retry on the resumed pre-approved pending-tool exec** (🟢 minor, deferred plan §9) — the pending tool currently executes raw (already approved); wrapping that single bridge exec in Cat 8 retry is a minor enhancement (a failure already surfaces to the continuation LLM).
- 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` / `AD-Resume-Tenant-Capability-Policy` / `AD-Resume-Reject-Path` (see Sprint 57.88 Carryover below).

---

## Sprint 57.89 Carryover — run() re-entrancy refactor (地基 A keystone) — **Slice 2 ✅ DONE (Sprint 57.90)**

**Source**: Sprint 57.89 closed 2026-06-08 — Slice 1/2 of `AD-Resume-Continuation-Fidelity` (pure extraction of `_run_turns`; resume()/`_resume_continuation` untouched). Detail: `memory/project_phase57_89_run_loop_reentrancy.md` + REFACTOR-006 + analysis note `run-loop-reentrancy-refactor-analysis-20260608.md §7`.

- **`AD-Resume-Continuation-Fidelity` Slice 2** — ✅ **DONE (Sprint 57.90)**: rewired `resume()` onto `_run_turns` + DELETED `_resume_continuation` + multi-pause + drive-through PASS. See the Sprint 57.90 Carryover section above.
- **`AD-Resume-Continuation-Fidelity` Slice 3** — see Sprint 57.90 Carryover above (now the immediate next step).
- **Subagent child-loop (Cat 11)** — see Sprint 57.90 Carryover above.

---

## 🆕 Sprint 57.88 Carryover — durable HITL pause-resume (地基 A keystone)

**Source**: Sprint 57.88 closed 2026-06-08 — first 地基 A spike (durable pause-resume vertical, chat path). Design note `19-pause-resume-design.md` §5 Open Invariants. Detail: `memory/project_phase57_88_pause_resume.md`.

- **`AD-Resume-Continuation-Fidelity`** (🟡 — the top carryover) — `_resume_continuation` (`loop.py:1992`) is a SECOND, reduced copy of run()'s loop body: a real while-true through PromptBuilder honoring max_turns/token_budget (passes AP-1/AP-8), BUT deliberately omits run()'s Cat 8 retry / Cat 9 guardrail+tripwire / Cat 4 compaction / per-turn checkpoint+span; the continuation cannot itself pause again (one-approval-per-run). Production needs run()'s core refactored into a shared re-enterable loop (or resume re-arms the full machinery). This is the keystone unblocker for the subagent child-loop.
- **`AD-Resume-Checkpoint-Bloat`** (🟡) — `resume_messages` self-contains the full conversation buffer in the pause checkpoint JSONB (no `messages` table exists in the codebase, Decision B). Long conversations → large rows; long-horizon (days) retention assumes messages persist. Production: a `messages` table / bounded summary + checkpoint TTL.
- **`AD-Resume-Tenant-Capability-Policy`** (🟢) — the ESCALATE matrix is derived from the live `registry.list()` (every tool PASS except `echo_tool` → requires_approval). Production per-tenant `capability_matrix.yaml` policy (which tools require approval per tenant/role) is deferred.
- **`AD-Resume-Reject-Path`** (🟢) — reject is recorded via the governance decide endpoint but the client does NOT call `/resume` on reject → the checkpoint is left dangling (not GC'd). A reject-then-resume (emit the block + clean the checkpoint) or a checkpoint reaper is deferred.
- **地基 A generalization** (🟡) — generalized pause points (input ESCALATE / mid-thinking / between turns), session-list "paused / awaiting approval" badge + cross-device resume, approval notification (email/webhook to the approver). 地基 B explicit cognition phases + subagent child-loop build are distinct larger sprints (the 地基 A lifecycle 骨架 now feeds them).

---

**Updated**: 2026-05-29 (Sprint 57.62 closed — **RateLimits Alerting** closes `AD-RateLimits-Alerting-Phase58` (Sprint 57.57/57.60/57.61 carryover): server-side 80%-threshold usage alerting that **persists** a row when a tenant's rate-limit usage crosses 80% of quota — the breach is captured **even when no admin is watching the live-usage card**. Day 0 pivot: the carryover claim "SSE infra ~80%; ~3-4 hr" proved FALSE (only SSE in repo is the agent-loop `LoopEvent` stream; admin SSE is greenfield ~8-12 hr) → AskUserQuestion → user locked **Option A persisted alert log** (~4-6 hr, polling-reuse). NEW `RateLimitAlert` ORM (`rate_limit_alerts`, `TenantScopedMixin`; severity lowercase `warning`/`critical` 2-tier + CHECK; UNIQUE `(tenant_id, resource_type, window_type, window_start)` + index `(tenant_id, triggered_at)`) + Alembic `0021` (down_revision `0020`; CREATE + ENABLE+FORCE RLS + 2 policies) + stateless `RateLimitAlertStore.maybe_record` (idempotent peak/escalate `pg_insert.on_conflict_do_update` GREATEST + warning→critical; early-return quota<=0/pct<80; fail-open) hooked into `RedisRateLimitCounter._write_through` (D-DAY0-G: session + 7 values already in scope → **NO ctor DI / NO main.py wiring**) + `GET /admin/tenants/{tid}/rate-limits/alerts?limit=N` + frontend `useRateLimitsAlerts` (15s poll) + QuotasTab Recent alerts Card (`.badge.warning`/`.badge.danger`, 0 new oklch; existing Rate limits + Live usage cards bit-for-bit scope-guard). Sequential 2-agent (`rl-alerts-backend` 28th + `rl-alerts-frontend` 29th consecutive). Day 0 三-Prong 16 checks (13 GREEN + 1 NOTABLE D-DAY0-G + 3 corrections; 0 CRITICAL). Commits `79282286` Day 0 + `95c65e09` Day 1 (17 files +1614/-26) + Day 2 closeout pending. pytest 1887 → **1907** (+20: 12 store + 6 endpoint + 2 migration) / mypy `src/ --strict` 0/319 / 9/9 V2 lints (check_rls_policies 20 → **21** tables) / Vitest → **686** (+17) / oklch delta 0 (baseline 48) / Alembic `0021` live down→up clean / DUAL CLEAN 22/22 PARITY **18 consecutive 57.45-57.62**. **CALIBRATION**: `mechanical-greenfield-design-decisions` 0.65 4th validation **BACK TO PAIR SHAPE** ratio ~0.77 BELOW band by 0.08 → KEEP single-data-point-per-shape (pair sub-seq 57.56=1.02 + 57.57=1.15 + 57.62=0.77 mean ~0.98 IN band); **R6 WEAKENS** — 57.61 backend-only 0.74 + 57.62 pair 0.77 = 2 consec `-design-decisions` below band regardless of shape → likely agent over-delivers generally; NEW `AD-AgentFactor-DesignDecisions-Below-Band-Watch` (cross-shape: next < 0.85 → tighten 0.65 → 0.55). `medium-backend` 0.80 13th data point ~0.50 — last-3 3-consecutive < 0.7 BUT all agent-delegated → confound resolved at agent_factor sub-class layer (0.65×0.77≈0.50 coherent) KEEP. No PROMOTION reaches codify threshold. CHANGE-030. `AD-AgentDelegate-DevStack-Precheck` CLOSED (applied Day 0). Phase 58.x RateLimits arc: enforce + persist + single-source + fail-loud-validate + **alert** (57.58-57.62); 8 carryovers.)

**Previous Updated**: 2026-05-29 (Sprint 57.61 closed — **RateLimits SyntaxValidation** closes `AD-RateLimits-SyntaxValidation-Phase58` (Sprint 57.60 carryover): add PUT-time syntax validation so a malformed rate-limit `value` returns **422** with a per-item reason instead of being silently dropped by `replace_configs` (`if parse is None: continue` → admin got 200 OK but the row vanished on the next GET). NEW `is_recognized_rate_limit_value(value) -> tuple[bool, str|None]` predicate in `rate_limit_config_store.py` (reuses existing `_VALUE_RE` + `_WINDOW_ALIASES`; only NEW pattern `_CONCURRENCY_RE` — **no 4th rate-regex copy**) accepts enforceable rate `N / <sec|min|hour|day>` + display-only `N concurrent`, rejects garbage/unsupported-window/non-positive/non-numeric/empty. NEW `field_validator("items")` on `RateLimitsUpsertRequest` (the REQUEST model — **NOT** shared `RateLimitItem` which also feeds GET; D-DAY0-E) → 422 per-item reason. US-2 parser-consistency guard (`test_rate_limit_parser_consistency.py`): store ⟺ counter validity for rates + concurrency asymmetry (validator True / parsers None, documented) + `_WINDOW_TO_SECONDS` (counter) == `_WINDOW_ALIASES` (store) key-set equality (fails loudly on future divergence). Single code-implementer agent `rl-syntax-validation` **27th consecutive**. Day 0 三-Prong 10 checks (8 GREEN + 2 NOTABLE; 0 CRITICAL; Prong 3 N/A no migration): D-DAY0-E 🔴 CRITICAL GREEN shared-model placement; D-DAY0-F 🔴 CRITICAL GREEN `"50 concurrent"` default present (load-edit-save round-trip risk); D-DAY0-J micro-simplification (`field_validator` already imported). 39 NEW tests (16 integration + 23 unit) additive — 0 existing conversions. Commits `6bf23e63` Day 0 + `093a161d` Day 1 (6 files) + Day 2 closeout pending. pytest 1848 → **1887** (+39) / mypy `src/ --strict` 0/317 / 9/9 V2 lints (check_rls_policies 20 tables unchanged — no schema change) / black/isort/flake8 clean / 0 frontend touched (Vitest 675) / no Alembic migration / DUAL CLEAN 22/22 PARITY **17 consecutive 57.45-57.61**. **CALIBRATION**: `mechanical-greenfield-design-decisions` 0.65 3rd validation **1st BACKEND-ONLY** ratio actual/agent-adjusted ~0.74 BELOW band [0.85,1.20] by 0.11 (prior 2 IN band 57.56=1.02 + 57.57=1.15 were backend+frontend pairs; single BELOW point vs 2 IN → rollback rule needs 2 consec same-direction → **KEEP 0.65 single-data-point caution**; R6 materialized — backend-only validator + 422 envelope runs faster than the backend+frontend pair the 0.65 was calibrated on; counterfactual `-port-style` 0.45 → ~1.06 IN band so port-style fit this backend-only shape better → NEW carryover `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch`); `medium-backend` 0.80 12th data point ~0.48 confound-resolved-at-sub-class-layer KEEP (last-3 57.57≈0.72 + 57.60≈0.33 + 57.61≈0.48 = 2/3 < 0.7 but NOT 3-consec → lower-trigger NOT met). No PROMOTION reaches codify threshold this sprint (Prong promotions already codified 57.57+57.60; the 2 NEW ADs are single-data-point). CHANGE-029. Phase 58.x RateLimits arc: write path now fail-loud at the boundary (57.57 WRITE + 57.58 RuntimeEnforce + 57.59 two-table + 57.60 cleanup + 57.61 syntax-validation); 6 carryovers.)

**Previous Updated**: 2026-05-29 (Sprint 57.60 closed — **RateLimits MetaData Cleanup** closes `AD-RateLimits-MetaData-Cleanup-Phase58` (Sprint 57.59 carryover): retire the transitional `tenant.meta_data["rate_limits"]` fallback at 4 read sites (GET / usage GET / middleware `_load_rate_limits` / Cat 2 gate `_load_tool_limits`) + PUT dual-write; config single-source `rate_limit_configs`. NEW Alembic `0020_clear_rate_limits_meta_data.py` strips the JSONB (`"metadata" - 'rate_limits'`, idempotent, physical column) + reverse-populate downgrade from config table (inline `_inline_project`, dep-light, `CAST(:items AS jsonb)` asyncpg-compat). Orphan cleanup (Karpathy §3): unused `tenant` bindings → bare `await _load_tenant_or_404`, orphaned `select`/`Tenant` imports, vestigial `db.refresh` + redundant `db.flush`. single code-implementer agent `rl-metadata-cleanup` **26th consecutive**. Tests (Never-Delete — convert): 5 files (incl. Day 0 D-DAY0-G drift `test_admin_tenant_rate_limits.py` 57.48-era missed by plan §4.4) + NEW `test_clear_rate_limits_meta_data_migration.py` (7 tests). Day 0 三-Prong 14 checks (11 GREEN + 3 NOTABLE/DRIFT + 0 CRITICAL-blocker): D-DAY0-E 🔴 CRITICAL GREEN `0019` unconditional migration → fallback removal safe; D-DAY0-G DRIFT 3rd test file; D-DAY0-M physical `"metadata"` column. Commits `621afe72` Day 0 + `416c9f84` Day 1 (9 files +187/-137 + 2 NEW) + Day 2 closeout pending. pytest 1840 → **1848** (+8) / mypy `src/ --strict` 0/317 (CI parity backend-ci.yml:152) / 9/9 V2 lints (check_rls_policies 20 tables unchanged) / Alembic live up→down→up clean / 0 frontend touched (Vitest 675) / DUAL CLEAN 22/22 PARITY **16 consecutive 57.45-57.60**. **CALIBRATION**: `mechanical-pattern-reuse-heavy` 0.30 **1st DELIBERATE FORWARD application** ratio actual/agent-adjusted ~1.09 IN BAND ✅ → KEEP 0.30 (57.49 was retroactive 0.21; counterfactual `-port-style` 0.45 → ~0.73 below band so 0.30 better fit; shape-variance noted); `medium-backend` 0.80 11th data point ~0.33 confound-resolved-at-sub-class-layer KEEP. **2 PROMOTIONS codified** into `sprint-workflow.md §Step 2.5`: Prong 2 +1 row `Claimed-but-nested-shape-mismatch` (`AD-Day0-Prong2-Nested-Shape-Read` 57.58+57.59) + Prong 3 +1 row `Physical-column-vs-ORM-alias` (`AD-Day0-Prong3-Physical-Column-Read` 57.59+57.60). Phase 58.x RateLimits arc config-complete; 5 carryovers. Deviation: `::jsonb`→`CAST(... AS jsonb)` asyncpg fix; pre-existing `mypy .` whole-dir conftest collision (NOT CI; Phase 58+ candidate).)

**Previous Updated**: 2026-05-28 (Sprint 57.59 closed — **RateLimits Potemkin Migration C1 two-table split (Phase 58.x deeper extensions 2/5)** closes `AD-RateLimits-Potemkin-Migration-Phase58` + **AP-4 CLOSED** (dormant `rate_limits` table since Phase 49 now activated) + CLOSED `AD-RateLimits-DedicatedTable-Phase58` (folded). NEW `rate_limit_configs` table (durable config, replaces `meta_data["rate_limits"]` JSONB) + activate existing `rate_limits` usage table; user-locked C1 two-table split over C2 nullable-window_start + over Option A/B at 2 AskUserQuestion gates. 2 sequential code-implementer agents (`rl-config-table` 24th + `rl-runtime-repoint` 25th consecutive): US-1+US-2 NEW `RateLimitConfig` ORM + Alembic `0019` (down_revision `0018_tenant_settings_extension`; CREATE + 2 RLS policies isolation+insert + inline-parse additive data migration) + `RateLimitConfigStore` + re-point GET/PUT (fallback meta_data + transitional dual-write; API `{label,value}` shape UNCHANGED → frontend untouched); US-3 re-point middleware/tool-gate + activate usage table via `RedisRateLimitCounter` write-through (window_start+window_end upsert `pg_insert.on_conflict_do_update` used=GREATEST) + `_recover_from_table` Redis-miss + optional `session_factory` DI + usage GET table-backed. Day 0 三-Prong 15 checks (12 GREEN + 3 NOTABLE + 1 minor; 0 CRITICAL): D-DAY0-J head 0018→0019, D-DAY0-G usage table has window_end, D-DAY0-K RLS 2-policy, D-DAY0-N inline-parse. Day 1 drift: D-DAY1-1 tenants JSONB physical column `metadata` (ORM `meta_data` alias) migration raw SQL fixed; D-DAY1-2 transitional dual-write; D-DAY1-3 asyncpg `set_config` bind-param fix. Commits `560a7697`+`195072ef` (17 files +1898/-76). pytest 1819 → **1840** (+21; plan +15) / mypy 0 / 9/9 V2 lints (check_rls_policies 20 tables +1 + check_llm_sdk_leak) / 0 frontend touched (Vitest 675 unaffected) / migration up/down/up clean / DUAL CLEAN 22/22 PARITY **15 consecutive 57.45-57.59**. **CALIBRATION ROLLBACK**: `mixed-multidomain-bundle-mechanical` 0.65 tier-3 **2nd validation** ratio ~0.34 BELOW band by 0.51 → 57.58 (0.49) + 57.59 (0.34) = **2 consec < 0.7 → ROLLBACK RULE MET → tighten 0.65 → 0.45 effective Sprint 57.60+** (note even 0.45 ≈ 0.49 still below — if 57.60 also < 0.7 escalate 0.30 / fold pattern-reuse-heavy); `mixed-multidomain-bundle` 0.65 SCOPE 3rd data point ~0.22 confound-resolved-at-sub-class-layer KEEP. Phase 58.x portfolio 2/5 RateLimits deeper extensions; 3 NEW carryovers.)

**Previous Updated**: 2026-05-28 (Sprint 57.58 closed — **RateLimits RuntimeEnforcement D3 Full (Phase 58.x deeper extensions 1/5)** closes `AD-RateLimits-RuntimeEnforcement-Phase58` + PARTIAL-CLOSE `AD-RateLimits-LiveUsageTracking-Phase58` (live usage exposure DONE; alerting remains). **Path B** (JSONB config + Redis sliding window counter) locked at Day 0 AskUserQuestion gate after 🚨 D-DAY0-CRITICAL caught AP-4 Potemkin `RateLimit` ORM (`api_keys.py:141` table `rate_limits` dormant since Phase 49 baseline, NEVER queried/written) → NEW carryover `AD-RateLimits-Potemkin-Migration-Phase58`. 4 tracks via 2 sequential code-implementer agents (22nd backend + 23rd frontend consecutive): Track A `RateLimitMiddleware(BaseHTTPMiddleware)` + `RedisRateLimitCounter` MULTI/EXEC pipeline sliding window (D-DAY1-2 fakeredis no EVAL → reserve-then-rollback) + `parse_rate_limit_item()` `{label,value}` normalizer (D-DAY1-1 stored shape UI strings NOT `{resource,window,limit}`); Track B LLM-neutral `RateLimitGate` Protocol + `RedisToolRateLimitGate` + `RateLimitExceededError` FATAL; Track C `GET /admin/tenants/{tid}/rate-limits/usage` peek; Track D `useRateLimitsUsage` 5s polling + QuotasTab Live usage Card (UNCHANGED scope-guard) 0 new oklch. Commits `f20ef896`+`5e6fc72f` (24 files +2172/-106). pytest **1819** (+13 exact) / Vitest **675** (+12) / mypy 0 / tsc 0 / 9/9 V2 lints / DUAL CLEAN 22/22 PARITY **14 consecutive 57.45-57.58**. CALIBRATION: `mixed-multidomain-bundle-mechanical` 0.65 tier-3 **1st validation** ratio ~0.49 BELOW band by 0.36 → single-data-point caution KEEP (flag Sprint 57.59+ 2nd validation; if < 0.7 tighten 0.45, if > 1.20 rollback 1.0); `mixed-multidomain-bundle` 0.65 SCOPE 2nd data point ~0.32 confound-resolved-at-sub-class-layer KEEP. 2 ADs closed (1 CLOSED + 1 PARTIAL) + 3 NEW carryovers; Phase 58.x portfolio 1/5 RateLimits deeper extensions shipped.)

**Previous Updated**: 2026-05-27 (Sprint 57.57 closed — **RateLimits WRITE-side ship (Phase 58.x portfolio FINAL 4/4 CLOSURE 🎉)** closes `AD-AgentFactor-Tier-4-Validation-Sprint-57.57` (Sprint 57.56 carryover) + `AD-TenantSettings-RateLimits-Write-Endpoint` (Phase 58.x portfolio remaining FINAL) + **3 PROMOTION ADs codified** (AD-Plan-Workload-AgentDelegation-Explicit-Field MANDATORY plan-time field + AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep NEW Drift Class row + AD-Day0-Prong2-CanonicalService-Grep NEW Drift Class row); D-DAY0-A ✅ GREEN inverse-validation (storage path established Sprint 57.48 Track D); D-DAY0-B ✅ GREEN NO canonical service direct ORM mirrors Sprint 57.56; D-DAY0-C/D 🆕 NOTABLE Variable-length list UX + free-form labels qualifies tier-4 `-design-decisions` 0.65; D-DAY0-E reverse scope guard (RateLimits Card edit mode + Usage Card UNCHANGED bit-for-bit). User 4-question scope locked Day 0 BEFORE plan v1 (Composite-replace + Add/Remove rows + Empty list allowed + Insertion order + 3 PROMOTION bundle; zero rework cycle). Day 1 sequential agent delegation (~55 min: Track A ~25 + Track B ~30; **20th+21st consecutive code-implementer chain**): NEW Pydantic `RateLimitsUpsertRequest`/`Response` + PUT endpoint dict-identity-swap + manual `append_audit("tenant_rate_limits_upsert")` + 10 NEW pytest (1796→**1806 PASS** exact target) + `RATE_PUT_%` LIKE sweep; NEW `useRateLimitsSave.ts` mutation hook verbatim mirror Sprint 57.56 + RateLimits Card edit mode (variable-length list UX) + softened BackendGapBanner 2nd + 18 NEW Vitest (645→**663 PASS** over plan +5-8 by 10-13 acceptable Sprint 57.56 +15 precedent) + D-DAY1-2 Karpathy §3 cleanup obsolete `handleRequestIncrease` removed. Day 0+1 commit `08695112` (13 files +2022/-44). **TIER-4 SPLIT FULLY VALIDATED**: `mechanical-greenfield-design-decisions` 0.65 2nd validation ratio ~1.15 ✅ IN BAND top edge → 2 consec IN band (57.56=1.02 + 57.57=1.15); KEEP 0.65 baseline; rollback rule baseline established. `medium-backend` 0.80 10th data point ~0.72 KEEP per `When to adjust` 3-sprint window rule; `medium-frontend` 0.65 7th data point ~0.55 5th consecutive < 0.7 KEEP per confound-resolved-at-sub-class-layer discipline; 5 ADs CLOSED simultaneously (1 Tier-4 validation + 1 portfolio FINAL + 3 PROMOTIONS) + 5 NEW Phase 58+ RateLimits extensions; DUAL CLEAN 22/22 PARITY preserved **13 consecutive 57.45-57.57** ⭐ strongest streak Phase 57+. **Phase 58.x portfolio FINAL CLOSURE**: HITLPolicies + FeatureFlags + Quotas + **RateLimits ALL CLOSED 🎉** — wave complete; Phase 58+ moves to deeper extensions per individual AD carryovers.)

**Previous Updated**: 2026-05-27 (Sprint 57.56 closed — **Quotas WRITE-side ship Phase 58.x portfolio 3/4** closes `AD-AgentFactor-Tier-4-Validation-Sprint-57.56` (Sprint 57.55 carryover); D-DAY0-A 🔴 RED resolved via user Option B Recommended at AskUserQuestion BEFORE plan v1 (zero rework cycle): `tenant.meta_data["quota_overrides"]` JSONB direct ORM write pattern (mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity precedent); D-DAY0-D 🆕 NOTABLE = inverse validation of Sprint 57.55 carryover `AD-Day0-Prong2-CanonicalService-Grep` — NO canonical service exists for Quotas (architectural simplification path = direct ORM UPDATE + manual `append_audit` Sprint 57.3 PATCH precedent; D-DAY1-1 fix-forward `append_audit` not `audit_log_append`); D-DAY0-E QuotasTab Quotas + RateLimits combined → scope guard Usage Card ONLY (RateLimits = Sprint 57.57); sequential agent delegation Track A backend ~25 min + Track B frontend ~25-30 min (18th+19th consecutive code-implementer); NEW `_PLAN_QUOTA_RESOURCE_WHITELIST` frozenset + Pydantic `QuotaOverridesUpsert{Request,Response}` + helper overrides param + PUT endpoint dict-identity-swap SQLAlchemy JSONB pattern + 12 NEW pytest (1784→**1796 PASS** exact upper target) + `QUOTA_PUT_%` LIKE sweep; `useQuotasSave` mutation hook + Usage Card edit mode (128→262 lines) + RateLimits Card UNCHANGED verified 11th scope-guard assertion test + 15 NEW Vitest (630→**645 PASS**); **TIER-4 1ST VALIDATION `mechanical-greenfield-design-decisions` 0.65 ratio ~1.02 ✅ IN BAND middle [0.85, 1.20] → CONFIRMED CLEANLY**; KEEP 0.65 baseline; Sprint 57.54+57.55 retroactive `-design-decisions` mapping VINDICATED; `medium-backend` 0.80 9th data point 0.66 KEEP per confound-resolved-at-sub-class-layer discipline; `medium-frontend` 0.65 6th data point ~0.50 4th consecutive KEEP per discipline; 1 AD CLOSED + 3 NEW carryovers; DUAL CLEAN 22/22 PARITY preserved **12 consecutive 57.45-57.56** ⭐ strongest streak Phase 57+; Day 0+1 commit `45735484` (13 files +2002/-43); Phase 58.x portfolio 3/4 → RateLimits remains Sprint 57.57 final 4/4.)

**Previous Updated**: 2026-05-27 (Sprint 57.55 closed — **FeatureFlags WRITE-side ship Phase 58.x portfolio 2/4** closes `AD-AgentFactor-Tier-3-Validation-Sprint-57.55` (Sprint 57.54 carryover); Day 0 D-DAY0-B 🔴 RED pivot: plan §4.1 assumed `tenants.meta_data["tenant_overrides"]` → reality `feature_flags.tenant_overrides[str(tid)]` JSONB ON registry table; D-DAY0-T 🆕 NOTABLE: `FeatureFlagsService.set_tenant_override` (Sprint 56.1) canonical setter auto-emits audit chain → pivot to clean V2 service path (REMOVED `AD-FeatureFlags-PerFlag-AuditLog-Phase58` carryover positive side-effect); sequential agent delegation Track A backend ~12 min + Track B frontend ~25 min (16th+17th consecutive code-implementer chain extended); NEW `clear_tenant_override` ~15-line method + helper extract + PUT endpoint composite-replace semantics SET+CLEAR loops + 12 NEW pytest (1772→**1784 PASS** exact target) + FF_PUT_% + `ff.%` sweep (D-DAY1-1 mid-Track-A self-resolved); `useFeatureFlagsSave` mutation hook (verbatim mirror Sprint 57.54 useHITLPoliciesSave) + FeatureFlagsTab edit mode (per-row Switch + Clear override + reverse-projection draft seed + tenant-switch reset) + softened BackendGapBanner + 13 NEW Vitest (617→**630 PASS** over target +5-8); **TIER-3 2ND VALIDATION `mechanical-greenfield` 0.50 ratio ~1.57 ABOVE band by 0.37 → 2 consec > 1.20 ROLLBACK RULE MET → TIER-4 SPLIT ACTIVATED** (`-port-style` 0.45 RESERVED + `-design-decisions` 0.65 NEW; Sprint 57.54+57.55 retroactive `-design-decisions` mapping; equivalent ratios 1.05-1.55 / 1.21 IN band top edge ✅); `medium-backend` 0.80 8th data point 0.79 KEEP (last-3 mean 0.87 IN band lower-middle); `medium-frontend` 0.65 5th data point 0.53 KEEP per confound-resolved-at-sub-class-layer discipline; 4 ADs CLOSED + 3 NEW carryovers; DUAL CLEAN 22/22 PARITY preserved **11 consecutive 57.45-57.55**; Day 0+1 commit `aff39394` (14 files +2173/-47); Phase 58.x portfolio 2/4 → Quotas + RateLimits remain Sprint 57.56+57.57.)

**Previous Updated**: 2026-05-26 (Sprint 57.54 closed — **HITLPolicies WRITE-side ship Phase 58.x portfolio 1/4**; tier-3 1st validation `mechanical-greenfield` 0.50 ratio ~1.37-2.0 ABOVE band by 0.17-0.8 → KEEP single-data-point caution + flag Sprint 57.55+ 2nd validation; 1 AD CLOSED + 3 NEW carryovers; DUAL CLEAN 22/22 PARITY 10 consecutive 57.45-57.54; commit `f2f95b11`.)

**Previous Updated**: 2026-05-26 (Sprint 57.53 closed — **Checkpointer test tenant isolation pre-existing fail FIX** closes `AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` (Sprint 57.51+57.52 trail carryover); Option A enriched with Sprint 57.12 `§Committed-Row Cleanup Pattern` lift to agent_harness scope (NEW `backend/tests/integration/agent_harness/conftest.py` ~120 lines mirrors `api/conftest.py` verbatim); 0 modifications to existing files; pytest baseline restored to **1760 PASS + 0 fail** (was 1759 + 1 PRE-EXISTING fail); H1-H6 hypothesis methodology (5 REFUTED + 1 PLAUSIBLE) + D-DAY0-9 NEW MAJOR finding (Sprint 57.12 precedent discovery); **`medium-backend` 0.80 6th data point ratio 0.83 in band lower edge** (cleaner signal under human 1.0 factor); **`mechanical-greenfield` 0.50 1st validation NOT GENERATED** (parent-assistant-direct per Sprint 57.45 Path B precedent → `agent_factor = 1.0` applied; carryover renamed Sprint-57.54); 1 AD CLOSED + 4 NEW carryovers; 25-sprint code-implementer chain BROKEN (parent-assistant-direct shape); DUAL CLEAN 22/22 PARITY preserved 9 consecutive 57.45-57.53.)

**Previous Updated**: 2026-05-26 (Sprint 57.52 closed — **triple-AD audit/docs hygiene bundle continuation** (Track A `AD-Day0-Prong2-Oklch-Delta-Grep` + Track B `AD-REFACTOR-Numbering-Collision` + Track C `AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern`) — 0 production code change; 5 files +593/-0; 1 git mv rename 88% similarity; 24th consecutive code-implementer agent delegation; **2nd validation tier-2 `mixed-multidomain-bundle` 0.65 sub-class agent_factor** ratio ~1.7-2.0 ABOVE band by 0.5-0.8 = 2nd rollback-trigger > 1.20 (Sprint 57.51=1.49 + 57.52=~1.85) → **ROLLBACK RULE MET → Option B tier-3 SPLIT ACTIVATED** effective Sprint 57.53+: NEW `-mechanical` 0.65 UNCHANGED + `-non-mechanical` 1.0 NEW (Sprint 57.51 + 57.52 retroactively validate cleanly at 1.0); `audit-cycle/docs/template` 0.40 3rd data point 3-pt mean 1.13 IN band middle KEEP (3-sprint window complete; class calibration mature); 3 ADs CLOSED + CLOSES AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52 via tier-3 ACTIVATION; 2 NEW carryover ADs (AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation Sprint 57.53 user-confirmed scope + AD-AgentFactor-Tier-3-Validation-Sprint-57.53); mockup-fidelity DUAL CLEAN 22/22 PARITY preserved through 8 consecutive sprints 57.45-57.52.)

**Previous Updated**: 2026-05-26 (Sprint 57.51 closed — **triple-AD audit/docs hygiene bundle** (Lint Detector + ORM Risk + HEX_OKLCH Verdict A) — 0 production code change; 7 `.md` files +1022/-3; **1st validation NEW tier-2 `mixed-multidomain-bundle` 0.65 sub-class agent_factor** ratio 1.49 ABOVE band by 0.29 → KEEP single-data-point caution; 3 ADs closed + 4 NEW carryovers; 23rd consecutive code-implementer delegation.)

**Previous Updated**: 2026-05-26 (Sprint 57.50 closed — single-track 1-hr hygiene closes `AD-TenantSettings-IdentityFixture-Cleanup` via Option A fixture-projection; **2nd validation `mechanical-single-domain` 0.45 ratio 0.58 → ROLLBACK RULE MET → Option B tier-2 ESCALATED ACTIVATED**: NEW `mechanical-pattern-reuse-heavy` 0.30 + `mechanical-greenfield` 0.50; 3 ADs closed + 4 NEW carryovers; 22nd consecutive code-implementer delegation.)

**Previous Updated**: 2026-05-26 (Sprint 57.43-57.49 batch closed; 4-sprint window landed via 14 ADs total — Phase-2 epic + NEAR-PARITY **DUAL CLEAN milestone 22/22 PARITY** reached Sprint 57.45; Phase 58+ Backend Schema Extension COMPLETE for TenantSettings 6-tab + admin-tenants LIST; Phase 58+ Frontend Real-Data Migration COMPLETE for /tenant-settings + /admin-tenants Members; Sprint 57.48 Option B sub-class split ACTIVATED.)

**Previous Updated**: 2026-05-25 (Sprint 57.42 closed; Option A `agent_factor = 0.55` ACTIVATED — later SUPERSEDED Sprint 57.48 via Option B sub-class split.)

---

## 🆕 Drive-Through Audit Carryover (2026-06-06 — 35-page full Playwright sweep)

**Source**: `claudedocs/5-status/drive-through-20260606/audit.md` (+ 20 screenshots in `shots/`). First systematic drive-through of all 35 frontend pages (real UI :3007 + real backend :8000 + real Azure LLM), per CLAUDE.md §Drive-Through Acceptance. **Audit-only — no code changed.** Headline: the spine is REAL (chat-v2 main-flow drive-through PASSES e2e — real gpt-5.2 loop → answer render → verification 0.78 → trace spans → cost_ledger; chat→cost_ledger→cost-dashboard confirmed by Total $0.0291→$0.0337). 11/15 full-impl pages honestly label fixtures; 12 proposed = honest ComingSoon stubs. Only **2 genuine page problems + 1 env blocker**.

### NEW carryover ADs (from the audit; NOT yet fixed)
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

### Confirmed (already-tracked) by the audit
- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** (✅ **RESOLVED 2026-06-12 — Sprint 57.105**, CHANGE-072) — was: dev-login selected `admin` but every page renders role=`user` (ISSUE-6). Fixed at the issue sites: login bakes DB role codes into the JWT claim; 57.105 drive-through renders **"DT Founder / admin"** + model-policy PUT 200 with zero dev-login; role-less JWT → 403.
- **`AD-ChatV2-SessionList-Backend`** (✅ **RESOLVED — Sprint 57.107 B3**, confirmed Sprint 57.125 Day-0) — the audit snapshot (2026-06-06) predated 57.107: `GET /api/v1/sessions` is real, `SessionList.tsx` loads it on mount, the DEMO banner is dropped, "New session" → `reset()`, the count is real. The session **LIST** backend is done. The separate history-**REPLAY** gap (clicking a session to reload its conversation) is `AD-ChatV2-Session-History-Replay-Phase58` (Sprint 57.125 backend SSE persistence + `GET /{id}/events`; 57.126 frontend replay — see the 57.125 carryover block).

### 🆕 Deep Drive-Through (2026-06-07 — 15 full-impl pages, per-control)

**Source**: `claudedocs/5-status/drive-through-20260606/deep-audit-15-fullimpl.md` (+ `shots-deep/`). Second pass that actually *drives* every action control (the 2026-06-06 audit left most "untested this pass"). Verified all 3 fixes live (FIX-028 sla-report 200 / FIX-029 orchestrator banner / FIX-030 overview-KPI banner + admin-tenants "50 tenants") and re-drove the chat-v2 main flow first-hand (real gpt-5.2 "Tokyo" → verification passed → full TAO trace → **cost_ledger $0.034→$0.038**). Caught 3 dead-control findings the surface audit missed:

- **`AD-Subagents-DeadControls-Disable-Or-Alert`** (✅ **RESOLVED 2026-06-07 — FIX-031**) — was: /subagents "Sync from repo" / "New subagent" / "Test invoke" (+ "Attach tool") clickable but no-op, no disclosure (AP-4). Fix: each now discloses via `window.alert("...: backend gap (Phase 58+) — ... pending")` (codebase gold pattern; visual unchanged). Drive-through verified. Backend wiring stays Phase 58+. Detail: `claudedocs/4-changes/bug-fixes/FIX-031-dead-action-controls-disclose-gap.md`.
- **`AD-AdminTenants-Toolbar-Filter-Sort-Wire-Or-Disable`** (✅ **RESOLVED 2026-06-07 — FIX-031**) — was: toolbar "Filter by name…" static `<span>` faking a search input + "Plan: all" / "Sort: runs (24h)" no-op (AP-4). Fix: cmdk filter (now `role="button"` + `tabIndex` + `onKeyDown` a11y) + both buttons disclose via `window.alert`. Drive-through verified. Real client-side filter/sort wiring stays Phase 58+ (`AD-AdminTenants-Toolbar-Filter-Sort-Real-Wire` if pursued). FIX-031.
- **`AD-Orchestrator-DeadControls-Disable-Or-Toast`** (✅ **RESOLVED 2026-06-07 — FIX-031**) — was: header Test / View repo / Deploy (+ PromptTab History / Test) silently no-op despite FIX-029's page banner. Fix: each discloses via `window.alert` (`discloseOrchestratorGap`). Drive-through verified (Deploy → alert). Real config/deploy pipeline stays Phase 58+ (`AD-Orchestrator-Config-Backend`). FIX-031.
- **`AD-Observability-AbortError-Network-Noise-Filter`** (🟢 minor, NEW) — route-change cancels React-Query requests → `AbortError: signal is aborted without reason` logged as `kind: network` error via `observability.ts:42` on nearly every page nav (telemetry noise, not a real failure); `POST /api/v1/telemetry/frontend` also `ERR_ABORTED`. Filter AbortError from network-error telemetry.
- Minor (fold into existing fixture-note coverage when touched): tenant-settings FF tab badge "14" vs body "No feature flags registered" (NEW-6); cost-dashboard + overview top-KPI deltas (+8.4% / +2.1M) likely fixture, unlabelled (NEW-7).

**Positive (no action — record only)**: governance Audit Log tab is real (`/audit/log` 200, ~17 rows) — better than the surface audit's "peripheral demo". loop-debug scrubber confirmed interactive. memory write-controls + tenant-settings disabled-when-empty are the two GOLD honesty patterns the dead-control fixes above should copy. `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) + `AD-RBAC-DB-To-JWT-Wiring-Phase58` (ISSUE-6) confirmed still open, unchanged.

---

## 🆕 Sprint 57.87 Carryover (2026-06-06 — C-12 IAM Block B self-service tenant registration; closes AD-Auth-Register-Backend-IAM-Block-B-Phase58)

**Closed**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` — the self-service registration leg of C-12 (the **third C-12 spike**, after 57.85 invites + 57.86 credentials). NEW `RegistrationService.register` (slug-unique → 409 / `Tenant` state **ACTIVE** + plan ENTERPRISE + requested_plan/size in meta_data / `_set_tenant` RLS / seed real **admin `Role`** — codebase's first real Role-creation / founding `User` + `UserRole` / `tenant_registered` audit) + public EXEMPT `POST /api/v1/tenants/register` (`api/v1/tenants.py` + `api/main.py` mount) + un-stubbed `/auth/register` wizard (201→`/auth/callback`, 409→slug-taken; AP-2 banner removed; i18n en/zh-TW). **No migration / no mockup-CSS change.** Design note `23-iam-registration-spike.md` (8-pt gate ~95%). mypy 0/344 + pytest 2214 + run_all 10/10 + Vitest 763 + mockup-fidelity ✓ (oklch baseline 53 UNCHANGED). Detail: `memory/project_phase57_87_iam_registration.md` + retrospective. CHANGE-055.

### NEW carryovers (this sprint)
- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** (NEW) — the seeded admin `UserRole` is DB-real but NOT yet authz-effective: gating reads the JWT `roles` claim and the OIDC callback bakes `roles=["user"]` (`auth.py:302`). Make the DB role grant JWT admin (per-request RBACManager load or a register-issued elevated JWT). The system-wide `has_permission()`-is-stub gap (gap-assessment §6) lives here too.
- **`AD-Register-OIDC-User-Linkage-Phase58`** (NEW) — register creates the user by `email` (no `external_id`); the OIDC callback upserts by `(tenant_id, external_id)` → a later login creates a SECOND user row. Fix: callback link-by-email OR register OIDC-initiated.
- **`AD-Tenant-Plan-Tiers-Phase58`** (NEW) — `TenantPlan` only has ENTERPRISE; the wizard's trial/pro/enterprise choice is stored in `meta_data` only. Real BASIC/STANDARD/trial tiers + quota enforcement are Phase 56+ Stage 2.
- **Process (single occurrence — fold into `sprint-workflow.md` only if recurs)**: a concurrent Claude session sharing the repo working directory switched the branch mid-sprint (to `chore/drive-through-acceptance-principle`), stranding uncommitted Day-3 edits + hiding `registration.py` → a phantom mypy `import-untyped` first mis-chased as editable-install staleness. Diagnostic lesson: when a first-party import reads "installed missing py.typed" + the mypy source-file count doesn't increment → check `git branch` FIRST. Root cause = two-sessions-one-worktree (recommend separate git worktrees/clones per session); not a workflow gap.

### C-12 epic — remaining legs (rolling, NOT pre-written)
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn; `/auth/mfa` still stub 501.
- **`AD-Auth-Recovery-Page-Phase58`** — password reset/recovery; needs an email adapter (none exists); `/auth/recovery` does not exist.
- **`AD-Auth-PasswordLogin-Lockout-Phase58`** — brute-force throttle on `/auth/password-login` (+ register-spam throttle); reuse the Redis rate-limit infra.
- **Calibration — `iam-backend-spike` 0.65 1st validation**: ratio ≈1.0 core (≈1.1-1.2 incl. the branch-collision anomaly) → KEEP single data point; flag the next IAM backend spike (MFA/recovery) for the 2nd validation per the 3-sprint window.

---

## 🆕 Sprint 57.86 Carryover (2026-06-06 — C-12 IAM Block B/C local credentials + password-login spike; closes AD-Auth-Credentials-PasswordLogin-Phase58)

**Closed**: `AD-Auth-Credentials-PasswordLogin-Phase58` — the local-password leg of C-12 (the **second C-12 spike**, completes 57.85's accepted-not-stored gap). `bcrypt` dep + `users.password_hash` (migration 0027, inherits users RLS) + `passwords.py` (hash/verify, anyio offload, 72-byte guard, DUMMY_HASH) + `CredentialsService` (set_password/authenticate; **every** miss → one generic 401 + constant-time DUMMY_HASH miss = anti-enumeration) + invite-accept now bcrypt-stores the password + `POST /auth/password-login` (JSON body, generic 401, JWT/cookie/AuthMeResponse mirror dev-login, EXEMPT) + NEW mockup-faithful `/auth/password-login` page (route + i18n en/zh-TW + mockup `AuthPasswordLogin` + `fetchWithAuth {redirectOn401:false}` UX fix). Design note `22-iam-credentials-spike.md` (8-pt gate ~96%). mypy 0/342 + pytest 2202 + run_all 10/10 + Vitest 761 + mockup-fidelity ✓ (HEX_OKLCH_BASELINE 50→53). Detail: `memory/project_phase57_86_iam_credentials.md` + retrospective. CHANGE-053.

### C-12 epic — remaining legs (rolling, NOT pre-written)
- **`AD-Auth-Register-Backend-IAM-Block-B-Phase58`** — self-service tenant registration (POST /tenants/register: create tenant + first admin user + password; reuses `passwords.py` + `CredentialsService.set_password`). The register page is still fixture/501.
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn (password-login lands the user via `consumePostLoginRedirect()`; `/auth/mfa` still stub 501).

### NEW carryovers (this sprint)
- **`AD-Auth-PasswordLogin-Lockout-Phase58`** (NEW) — brute-force / lockout throttle on `/auth/password-login` (no per-tenant login-attempt counter this spike; bcrypt cost=12 + generic-401 raise per-guess cost but no rate limit). Candidate substrate: the Redis rate-limit-counter infra (57.48/57.58).
- **Password-strength policy** — invite-accept keeps `min_length=1`; password fields gain only `max_length=72` (bcrypt safety). Min length / complexity / breach-check is a follow-up.
- **`AD-Auth-Recovery-Page-Phase58`** — password reset / recovery; `/auth/recovery` does not exist.
- **Login-page discoverability link** — the OIDC `/auth/login` page does NOT link to `/auth/password-login` (kept pristine per mockup); the page is reachable by direct route + is its own consumer. A mockup-gated link is a follow-up.
- **Calibration — `AD-Sprint-Plan-IAM-Backend-Spike-Class`** (NEW): `medium-backend` 0.80 ran ratio ~1.15-1.2 (greenfield-IAM over-run) — **2nd consecutive** greenfield-IAM over-run (57.85 ~1.25 + 57.86 ~1.15-1.2). Propose a `iam-backend-spike` class (~0.65) for the next IAM backend spike (register/MFA); adopt in that sprint's plan, do NOT pre-create.

---

## 🆕 Sprint 57.85 Carryover (2026-06-06 — C-12 IAM Block B invites vertical spike; closes AD-Auth-Invite-Backend-IAM-Block-B-Phase58)

**Closed**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` — the invites leg of C-12 Block B (the **first C-12 spike**, per the thin-spike discipline). DB-backed invite lifecycle: NEW `invites` table (migration 0026, RLS two-policy + system-sentinel guest-lookup escape) + `InvitesService` (opaque token sha256-stored-returned-once / create / get_metadata / single-use accept → User+UserRole+WORM-audit / revoke) + 3 endpoints (admin create `require_admin_platform_role` + guest GET/accept EXEMPT) + frontend invite page wired (fixture + AP-2 banner removed; 404/410 states). `password` accepted-not-stored (split → 57.86). Spike design note `21-iam-invites-spike.md` (8-pt gate). mypy 0/339 + pytest 2179 + run_all 10/10 + Vitest 757 + mockup-fidelity ✓. Detail: `memory/project_phase57_85_iam_invites.md` + retrospective. CHANGE-052.

### C-12 epic — remaining legs (rolling, NOT pre-written)
- **`AD-Auth-Credentials-PasswordLogin-Phase58`** (NEW, next obvious = 57.86) — local-password credentials table + bcrypt + a tenant-scoped password-login endpoint. The accept's `password` is accepted-not-stored until then; the created user authenticates via OIDC/dev-login. (Login-page UI wiring further gated by mockup-fidelity — mockup login has no password field.)
- **`AD-Auth-Register-Backend-IAM-Block-B-Phase58`** — self-service tenant registration (POST /tenants/register: create tenant + first admin user).
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — Block C MFA TOTP + WebAuthn (accept navigates to `/auth/mfa`, still stub 501).

### NEW carryovers (this sprint)
- **Invite email delivery** — no email facility exists; create returns the raw token in-response. Phase-58 follow-up (e.g. SMTP/SES adapter).
- **Admin invites-list / resend UI** — `revoke` service method exists (US-4 revocable); a full management surface (list pending / resend / revoke UI) is a follow-up.
- **Calibration**: `medium-backend` 0.80 greenfield-IAM data point ran ratio ~1.25 (over-band, as the plan flagged). Single outlier (ignored for the multiplier); if 57.86 (also greenfield IAM) confirms > 1.0 → propose a new `iam-backend-spike` class (~0.55-0.65). Track in `sprint-workflow.md §Scope-class matrix` if it recurs.
- **Process** (single data point, fold into `sprint-workflow.md` only if recurs): a Day-0 check — "if the test DB role is superuser, RLS-block is untestable → plan an application-layer isolation assertion" (D5 cost one isolation-test rewrite).

### Other in-repo C-area items still open (per `5-status/README-integration-gap-abc.md`)
- **C-13** workflows page (全缺; greenfield front+back) / agents catalog already partially done (57.70).
- **C-14** 企業合規軸 (SOC2/PDPA/CRA/AI Act) — 0% code, large, needs policy decisions.
- **C-15** IaC pipeline / DR / Analytics — external-blocked (Azure provision + GitHub Secrets + infra decisions); billing-write-atomicity leg already CLOSED (57.84).
- **B-9** 4 mockup re-point 二階債 (minor).

---

## 🆕 Sprint 57.83 Carryover (2026-06-05 — B-8 leg-2: general judge + real-LLM e2e + flip default; closes B-8 / AD-Cat10-Wire-1-Production)

**Closed**: B-8 fully (blocker B + C + flip) / `AD-Cat10-Wire-1-Production` — **完整 B-8 epic COMPLETE**. NEW lightweight `output_quality` judge + default template swap; a real-Azure measurement data-gated the flip; flipped `chat_verification_mode` default `disabled`→`enabled`. Final-output verification now ON by default for `real_llm` chat (env-overridable rollback). Detail: `memory/project_phase57_83_verification_default_enable.md` + retrospective + `claudedocs/5-status/cat10-verification-real-llm-measurement-20260605.md`. CHANGE-050.

### Key result (the data-driven gate worked)
- Pass 1 (Q1 fail-on-any judge): real-Azure FP ~75% (normal answers failed + up to 3× correction re-runs) → DO-NOT-FLIP.
- Re-tune (Q2 + AskUserQuestion): lightweight "clearly-failed-only" judge → Pass 2 FP 0% (8/8 normal pass, 0 corrections) + nonsense caught → FLIP. The leg-1 low-FP judge recommendation was vindicated; the gate caught the strict version before it shipped.

### NEW carryovers (this sprint)
- **Monitor production verification_failed rate post-flip** — 0% FP is from an 8-prompt sample; watch real-traffic FP + correction rate (verification_log + `_verification` ledger give the data). Re-tune `output_quality` if FP creeps up.
- **Per-verifier cost attribution** (leg-1 carryover) — still one `_verification` sub_type.
- **Multi-judge registry** (safety + quality on the main path) — shipped one general quality judge; layering safety/PII is a separate decision.
- Remaining billing bundle: **C-15** (DevOps/data-platform billing — cost_ledger 雙扣 risk).

---

## 🆕 Sprint 57.82 Carryover (2026-06-05 — B-8 leg-1: verification judge token → cost ledger + quota; closes AD-Cat10-Judge-Cost-Ledger)

**Closed**: B-8 **blocker A** / `AD-Cat10-Judge-Cost-Ledger` — the billing leg of the 完整 B-8 epic (user selected "clear 3 blockers + flip default"; this is leg 1 of a 2-leg epic). When verification is enabled, the LLM judge call's tokens are now recorded as a distinct `_verification` cost-ledger sub_type + counted against quota (previously discarded → billing/quota under-report). Design Option 1 (user AskUserQuestion): the correction-loop wrapper accumulates judge tokens across verifiers+attempts (the loop accumulator is frozen by the time verification runs in the wrapper) → `LoopCompleted.verification_*_tokens` → router records a distinct ledger entry + adds to quota actual. Default `chat_verification_mode` UNCHANGED (`disabled`) — a correctness fix activating only on the enabled path. backend+docs; no design note (17.md §1.1/§4.1 in-place). backend mypy 0/332 + pytest 2147 (+10) + run_all 10/10. Detail: `memory/project_phase57_82_verification_judge_cost_ledger.md` + retrospective. CHANGE-049.

### 完整 B-8 epic — remaining (leg 2 = Sprint 57.83)
- ✅ **leg 1 (57.82)**: blocker A — judge token → cost ledger + quota.
- ⏳ **leg 2 (57.83, plan written at 57.83 kickoff — rolling)**: blocker B (design a general final-output judge template replacing the Cat 9-fitted `safety_review` default + measure false-positive rate) + blocker C (real-LLM e2e: false-positive / p95 latency / per-chat cost) + **flip `chat_verification_mode` → `enabled`**. B+C bundled (B's FP eval needs C's real-LLM). Needs real Azure (live since 57.79).

### NEW carryovers (this sprint)
- **Per-verifier cost attribution** — leg 1 aggregates all judge tokens into ONE `_verification` sub_type; a per-verifier breakdown is deferred.
- **Drift D3 (sse server-side decision)** — verification tokens are NOT on the SSE wire (consistent with loop input/output_tokens being server-side only; router reads the event object). If a future UI needs to show judge cost, add the LoopCompleted serializer fields + frontend codegen then.
- No blocking carryover. Remaining billing bundle: **C-15** (DevOps/data-platform billing — cost_ledger 雙扣 risk).

---

## 🆕 Sprint 57.81 Carryover (2026-06-05 — B-7 ErrorBudget Redis wiring; closes B-7 / AD-ErrorBudget-Redis-Wiring)

**Closed**: B-7 / `AD-ErrorBudget-Redis-Wiring` — wiring gap (not missing logic): `RedisBudgetStore` built + fakeredis-tested Sprint 53.2 but never wired (AP-2); `make_chat_error_deps()` hardcoded a fresh `InMemoryBudgetStore()` per request → counters reset every request → budget non-functional even single-instance. Fix Tier 1 (parent-direct, agent_harness DI-pure): NEW `platform_layer/governance/error_budget_provider.py` singleton (mirror rate_limit_counter) + `_wire_error_budget()` startup (fail-open) + export RedisBudgetStore + factory swap `maybe_get_budget_store() or InMemoryBudgetStore()`. Shared store fixes per-request reset AND cross-instance; pure Redis (no DB/RLS). Verified: fakeredis accumulation (2 factory calls → count=2) + startup-log `error budget store wired`; NO real-Azure (budget increments on errors only). backend-only Cat 8; no design note. Detail: `memory/project_phase57_81_errorbudget_redis_wiring.md` + retrospective. CHANGE-048.

### NEW carryovers (this sprint)
- **error_budgets.yaml per-tenant overrides** — `budget.py` docstring mentions YAML-tunable caps; the factory uses defaults (1000/day, 20000/month). Loading per-tenant overrides is a separate feature (not wiring). Candidate.
- **Day-0 export check (rule candidate)** — when wiring an already-built component, add a one-line Day-0 check that it's EXPORTED on the public import path (D1 this sprint: RedisBudgetStore was not exported; 30-sec find vs a Day-1 import error). Fold into `sprint-workflow.md §Step 2.5` if it recurs.
- No blocking carryover. Remaining bundle: **B-8** (Verification default-enable) / **C-15** (DevOps/data-platform billing).

---

## 🆕 Sprint 57.80 Carryover (2026-06-04 — chat real_llm orphan-tool-message fix; closes AD-Chat-RealLLM-Orphan-Tool-Message)

**Closed**: `AD-Chat-RealLLM-Orphan-Tool-Message` (the 57.79 carryover) — real_llm `POST /chat` 400'd on every tool turn. Builder-level tool-call adjacency invariant (`_enforce_tool_adjacency` after `strategy.arrange()`, fix B, protects all strategies / LostInMiddle untouched) + pending-tool-turn user re-anchor suppression (fix C, in-sprint extension per the real-LLM finding — B-only gave 200 but `stop_reason=max_turns`; C → `end_turn`). Real Azure (gpt-5.2) verified converged + cost_ledger written. AP-10 (MockChatClient never validated adjacency → invisible until real Azure). backend-only Cat 5; no design note. Detail: `memory/project_phase57_80_orphan_tool_adjacency.md` + retrospective. FIX-027.

### NEW carryovers (this sprint)
- **Candidate rule fold-in (not yet codified)** — Cat 5 / message-assembly tests must assert the provider structural invariant (tool-call adjacency / ordering) directly, not rely on the mock to reject; and a real-LLM DoD for agent-loop prompt changes should check `stop_reason=end_turn` (convergence), not just no-400 / loop_end present. (Single-data-point; fold into `sprint-workflow.md` if a 2nd sprint hits the same gap.)
- No blocking carryover. Unrelated bundle remains: ~~**B-7** (ErrorBudget Redis wiring)~~ ✅ CLOSED Sprint 57.81 / **B-8** (Verification default-enable) / **C-15** (DevOps/data-platform billing).

---

## 🆕 Sprint 57.79 Carryover (2026-06-04 — C-11 billing-correctness; closes AD-Cost-Ledger-Model-Pricing-Key-Mismatch + AD-Adapter-MaxTokens-NewModel-Param)

**Closed**: `AD-Cost-Ledger-Model-Pricing-Key-Mismatch` + `AD-Adapter-MaxTokens-NewModel-Param` — the 2 C-11 billing gaps. First post-Area-A sprint (user picked C-11 收尾 over carryover/B). Gap 1: `get_llm_pricing` strips `-YYYY-MM-DD` on exact-miss → base key (`gpt-5.2-2025-12-11` → `gpt-5.2`); yaml + `gpt-5.2` (1.75/14.00/0.175 user-provided); chose normalize over per-date yaml keys. Gap 2: adapter `_max_tokens_param_name` gpt-5→`max_completion_tokens` (config.model_name keyed). Real Azure verified: cost_ledger DB `unit_cost>0` (direct record path) + token-cap no 400. backend-only; no design note. Detail: `memory/project_phase57_79_c11_billing_correctness.md` + retrospective. CHANGE-047.

### NEW carryovers (this sprint)
- **`AD-Chat-RealLLM-Orphan-Tool-Message`** — ✅ **CLOSED Sprint 57.80 (FIX-027)**. Root cause = `LostInMiddleStrategy.arrange()` moved recent assistant to the tail while the tool result stayed in mid_history → tool preceded its assistant. Fixed builder-level (`_enforce_tool_adjacency` after `strategy.arrange()`, fix B) + pending-tool-turn user re-anchor suppression (fix C, for convergence). Real Azure verified: 200 + `stop_reason=end_turn`. Detail: `memory/project_phase57_80_orphan_tool_adjacency.md`. ~~chat router real_llm e2e blocked by a pre-existing, UNRELATED message-structure 400; needs separate investigation into the real_llm prompt assembly.~~
- **Deployment requirement: `AZURE_OPENAI_MODEL_NAME`** — prod/other envs using a gpt-5.x deployment MUST set this to the real generation (e.g. `gpt-5.2`). Config default is `gpt-4o` (stale); if unaligned, Gap 2 mis-branches to `max_tokens` → 400 on gpt-5.x. (Gap 1 unaffected — uses response.model.) Deployment/ops note, not a code item.

### Still-open billing bundle (Sprint 57.82+ candidates)
- ~~B-7 ErrorBudget Redis wiring~~ ✅ CLOSED Sprint 57.81 / B-8 Verification default-enable / C-15 DevOps-data-platform billing — the billing-correctness bundle's remaining legs.
- Auto-sync pricing from provider API (`llm_pricing.yml:3` future idea) — stays manual yaml.

---

## 🆕 Sprint 57.78 Carryover (2026-06-04 — Subagents Registry real list; closes AD-Subagent-RealList-Phase58 → 🎉 Area-A program COMPLETE)

**Closed**: `AD-Subagent-RealList-Phase58` — the LAST Area-A item. Re-pointed `GET /subagents` STUB (never-persisted invocations) → real per-tenant `agent_catalog` (57.70) registry view + wired the mockup-ported `/subagents` page. Catalog/Registry view (AskUserQuestion) over runtime invocations. Real role←key/model/modes←allowed_modes/status; KPI counts derived; detail spec/budget/tools real; usage metrics (calls24h/p95/stats) honest-gapped "—" (AP-4); removed 8-row fixture + carryover banner. Backend re-point + FE wire (sequential 2-agent); no migration; feature-continuation (no design note). Detail: `memory/project_phase57_78_subagents_registry_real_list.md` + retrospective. CHANGE-046.

### 🎉 Area-A "process all carryover except A-4 Tier 2" program — COMPLETE
- ✅ #1+#2 Inspector Trace + Memory tabs (57.75) · #3 admin-tenants stats (57.74) · A-5c Inspector Tree (57.72) · A-6 admin re-mount + memory matrix (57.73)
- ✅ Memory ops-history backend (57.76) + frontend (57.77, PR #243) → `AD-Memory-OpsHistory-Backend` FULLY CLOSED
- ✅ **FE /subagents real list (57.78) → `AD-Subagent-RealList-Phase58` CLOSED — LAST ITEM**
- (A-4 Tier 2 real Jaeger export = EXCLUDED per user program → Area-C/DevOps)

### NEW carryovers (this sprint)
- **`AD-Subagent-Invocations-Persistence-Phase58`** — the runtime per-spawn timeline (the heavy path NOT chosen): NEW SubagentInvocation ORM + dispatcher persist hook + read-side projection. Re-log if a real invocations timeline is later wanted.
- **agent_catalog tenant-facing write from /subagents** — Sync-from-repo / New-subagent buttons stay AP-2 stubs (admin CRUD at `/admin/tenants/{id}/agents`).
- **budget/tools loop enforcement** — stored not enforced (57.70 §9).
- **Usage-metrics backing** (calls24h/p95/success/avg-tokens/top-orchestrator) — needs runtime invocation telemetry; honest-gapped this sprint.

### Process / Calibration
- **D-DAY1-1 lesson (agent missed existing same-endpoint test)**: code-implementer added a NEW `test_subagents.py` without noticing the existing `test_subagent_registry.py` (57.19) → 2 superseded stub-contract failures. Parent rewrote the existing file into the catalog contract + deleted the new dup (Never Delete respected). Lesson: a re-point agent prompt should say "find + update the EXISTING endpoint tests" not "add a NEW test file" (researcher B flagged the file but it didn't reach the agent prompt).
- **D-DAY1-2 lesson (i18n locale vs UI-state-string conflation — 57.73 D-DAY1-1 variant, 2nd occurrence)**: agent put 3 new keys in English in zh-TW citing "English convention"; but i18n LOCALE files ARE translated (existing subagents zh-TW all 繁中). Parent fixed → 繁中. **2 occurrences (57.73 opposite direction) → Before-Commit item 7 sub-bullet candidate**: distinguish "component inline string = English" from "i18n locale file = follow the file's language".
- Calibration: `mixed-multidomain-bundle` 0.65 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 — CAVEATED (16th consecutive agent-delegated no-clean-wall-clock; `AD-Calibration-AgentDelegated-WallClock-Measure`).

---

## 🆕 Sprint 57.77 Carryover (2026-06-04 — Memory ops-history frontend full-wire; closes AD-Memory-OpsHistory-Backend frontend half → AD FULLY CLOSED)

**Closed**: `AD-Memory-OpsHistory-Backend` **fully closed** (backend 57.76 + frontend 57.77). Wired shipped `GET /memory/ops`: NEW `useMemoryOps` hook (mirror useMemoryMatrix) + `fetchOps` service (URLSearchParams, `before` only-when-provided) + `MemoryOpItem`/`MemoryOpsResponse` wire-verbatim types; RecentMemoryOpsCard real cursor-filter (`created_at_ms ≤ cursor`, honest browse-ops-timeline, AP-4 not state-reconstruction) + loading/error/empty; TimeTravelScrubber marks from real `created_at_ms` domain + scrub→onCursor(ms) + hasDomain div-by-zero guard; MemoryView cursor ms|null + playback over real op range; deleted `_fixtures.ts` (3 fixtures + 3 orphan types + MemoryScopeId, 0 importers). Frontend-only; feature-continuation (no design note). Agent-delegated (Track A) + parent re-verify. Detail: `memory/project_phase57_77_memory_ops_history_frontend.md` + retrospective. CHANGE-045.

### Area-A "process all carryover except A-4 Tier 2" program — remaining
- ✅ #1+#2 Inspector Trace + Memory (57.75) · #3 admin-tenants stats (57.74)
- ✅ `AD-Memory-OpsHistory-Backend` **fully closed** (backend 57.76 + frontend 57.77)
- ⏳ **FE `/subagents` real list (`AD-Subagent-RealList-Phase58`) — THE LAST Area-A remaining item** (agent_catalog specs exist; needs tenant-facing GET + FE re-mount, like 57.73)
- (A-4 Tier 2 real Jaeger export = EXCLUDED per user program → Area-C/DevOps)

### NEW carryovers (this sprint)
- **READ-path ops** — write/evict only (57.76 backend); sampled reads a future option (row-volume tradeoff).
- **role/session/system layer ops** — those layers raise / in-memory (57.76); not recorded → never appear in RecentOps/marks.
- **Point-in-time state reconstruction** — scrub = ops-browsing (filter visible ops by time); replaying snapshots to rebuild memory state at an arbitrary timestamp is deeper future work.
- **Server-side ops time-window scrub** — current filters client-side from a single 50-row page; `before` cursor wired in `fetchOps` but pagination-only. Deep-history scrub needs server-side windowed fetch.

### Process / Calibration
- **D-DAY1-1 lesson (state-wiring seam)**: agent stayed narrowly in-scope (`MemoryPageHeader cursor={0}` hardcode) leaving a dead `cursor<0` branch + inert header; scrub didn't reflect in the header. Parent re-verify caught it (user-approved scope expansion → header migrated minute-offset→ms|null). Lesson: when delegating "wire X into page", trace the migrated state through EVERY page consumer (header was a 3rd, under-scoped in plan), not just named widgets — extend the Day-0 frontend audit to grep state consumers. Complements Prong-2.5 (which audits *styling* drift; this was a *state-wiring* seam). 1 data point.
- **D-DAY1-2**: plan assumed colocated `src/**/*.test.tsx` NEW; Vitest `include` = `tests/unit/**` + 4 memory tests already existed (57.73) → rewrite-in-place (Sprint 57.66 test-infra-file-verify applied to FE Vitest layout). No coverage lost.
- Calibration: `medium-frontend` 0.65 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 — CAVEATED (15th consecutive agent-delegated no-clean-wall-clock; `AD-Calibration-AgentDelegated-WallClock-Measure`).

---

## 🆕 Sprint 57.76 Carryover (2026-06-04 — Memory ops-history backend; closes AD-Memory-OpsHistory-Backend backend half)

**Closed (backend half)**: `AD-Memory-OpsHistory-Backend` — NEW append-only `memory_ops` table (Option B) + Alembic 0024 (RLS 2-policy + FORCE mirror 0023) + user/tenant write/evict emit (same-txn, Risk-C atomicity tested; evict SELECT-before-DELETE) + `GET /memory/ops` (cursor pagination). **Backend-only; frontend half = Sprint 57.77**.

### Sprint 57.77 (frontend half — next obvious follow-up)
- `useMemoryOps` hook (mirror `useMemoryMatrix`) + wire `RecentMemoryOpsCard` (consume `GET /memory/ops`) + `TimeTravelScrubber` (timeline marks from ops) + remove fixtures + e2e. `MemoryOpItem` → FE `RecentMemoryOp {op, scope, k, v, by, at}`.

### Area-A "process all carryover except A-4 Tier 2" program — remaining
- ✅ #1+#2 Inspector Trace + Memory (57.75)
- 🔶 `AD-Memory-OpsHistory-Backend` backend done (57.76); frontend → 57.77
- ⏳ FE `/subagents` real list (`AD-Subagent-RealList-Phase58`) — last item (agent_catalog specs exist; needs tenant-facing GET + FE re-mount, like 57.73)

### NEW carryovers (this sprint)
- **READ-path emit** — write/evict only this sprint; sampled reads a future option (row-volume tradeoff)
- **role/session/system layer ops** — role/system raise (admin-managed/read-only); session in-memory volatile; emittable if they gain live DB write paths
- **Full point-in-time state reconstruction** — this sprint = time-ordered ops log (sufficient for RecentOps + TimeTravel marks); replaying snapshots to rebuild memory state at an arbitrary timestamp is deeper future work

### Process / Calibration
- **Q4 lesson (researcher behavioral-claim drift)**: a researcher's "layer X does INSERT" is a Prong-2 *content* assertion to confirm by reading the write/evict method body before the plan commits. The researcher reported `role_layer.py:76 = INSERT` (actually a `read()` SELECT); role write/evict raise NotImplementedError → no emit. Agent + parent re-verify both caught it (no harm). 1 data point; if recurs, consider Day-0 rule "grep-confirm each `layer does X` against the method body".
- Calibration: `medium-backend` 0.80 + `agent_factor` 0.45 — CAVEATED (14th consecutive agent-delegated); medium-backend 3-sprint-mean recalibration watch (fresh data point).

---

## 🆕 Sprint 57.75 Carryover (2026-06-03 — chat-v2 Inspector Trace + Memory tabs full-chain; closes AD-ChatV2-Inspector-Trace-Phase2 + -Memory-Phase2)

**Closed**: `AD-ChatV2-Inspector-Trace-Phase2` + `AD-ChatV2-Inspector-Memory-Phase2` (Area-A program #1+#2). All 4 chat-v2 Inspector tabs now real (Turn 57.21 / Tree 57.72 / Trace+Memory 57.75).

### Area-A "process all carryover except A-4 Tier 2" program — remaining
- ✅ #1+#2 Inspector Trace + Memory tabs (THIS sprint)
- ⏳ `AD-Memory-OpsHistory-Backend` — persisted memory ops-history (distinct from this sprint's live-session SSE Memory tab; needs audit-emit or `memory_ops` table — Day-0 design decision)
- ⏳ FE `/subagents` real list (`AD-Subagent-RealList-Phase58`)

### NEW carryovers (this sprint)
- **subagent-boundary spans** — cross-process `parent_span_id` so a subagent's spans nest under the parent loop's TURN in the Trace waterfall (this sprint is single-loop only)
- **memory write/evict emit** — Memory tab shows read-on-build only; write/evict happen inside tools (under TOOL_EXEC span); emit if the tab needs the full op set

### Process / Calibration
- **Q4 lesson (cross-boundary re-verify gap)**: an agent track mutating files across the backend↔frontend boundary (codegen output / shared schema) requires parent re-verify of BOTH sides' gates. Track A (backend) regen'd frontend codegen → Track-A re-verify ran only backend gates → frontend `eventSchema.generated.test.ts` (19→22) was stale (Track B caught + fixed). Candidate Before-Commit item 7 fold-in if it recurs (rolling — 1 data point).
- Calibration: `mixed-multidomain-bundle` 0.65 + `agent_factor` 0.45 — CAVEATED (13th consecutive agent-delegated no-clean-wall-clock).
- **A-4 Tier 2** (Jaeger export / Area-C DevOps) still excluded per user program.

---

## 🆕 Sprint 57.74 Carryover (2026-06-03 — admin-tenants stats aggregate; closes AD-AdminTenants-Stats-Aggregate-Endpoint)

Sprint 57.74 (Area-A **#3** of the "process all carryover except A-4 Tier 2" program) ✅ **CLOSED** `AD-AdminTenants-Stats-Aggregate-Endpoint`: NEW `GET /admin/tenants/stats` fleet aggregate (active_tenants/total_seats/agents_deployed + per-tenant agents/runs24 map) + wired `TenantsStatsStrip` (3 real stats) + filled `TenantsTable` Agents/Runs·24h columns. Anomalies stat + trend deltas honest-gapped (no fabrication). Agent-delegated (Track A backend + Track B frontend + parent re-verify). Detail: `memory/project_phase57_74_admin_tenants_stats.md` + retrospective. CHANGE-042.

**2 NEW carryovers** (honest-gapped this sprint):
- `AD-AdminTenants-Anomalies-Stat-Backend` — define + back the Anomalies stat (e.g. per-tenant verification failures / guardrail blocks / SLA breaches + aggregate query).
- `AD-AdminTenants-Stats-Trend-Deltas` — period-over-period delta source (snapshot table or time-windowed diff) for the stat trend arrows.
- (minor) page-scoped per-tenant stats — perf optimization if the fleet grows beyond admin scale.

**Remaining "process all carryover except A-4 Tier 2" program** (user-selected; sequenced next):
- A-5c Inspector **Trace** tab — `AD-ChatV2-Inspector-Trace-Phase2` (needs SpanStarted/SpanEnded over SSE).
- A-5c Inspector **Memory** tab — `AD-ChatV2-Inspector-Memory-Phase2` (needs `memory_accessed` event).
- A-6b memory ops-history backend — `AD-Memory-OpsHistory-Backend` (memory write-path audit/version instrumentation).
- FE `/subagents` wiring — `AD-Subagent-RealList-Phase58` (subagent invocations list backend).

(A-4 Tier 2 real Jaeger export = explicitly EXCLUDED from the program → Area-C/DevOps.)

---

## 🆕 C-11 Real-LLM Execution Findings (2026-06-03 — 本機 smoke 實跑；real-LLM 閉環 LIVE；cost-ledger row-count leg RESOLVED via restart，$ 值 gap 開放)

C-11 本機 real-LLM smoke 已實跑（用既有 `.env` Azure 憑證、零 GitHub secret、零 code change；詳 `claudedocs/5-status/c11-real-llm-e2e-analysis-20260601.md §8`）。**real-LLM 閉環 = LIVE + 已驗證**（HTTP 200 / `loop_end` / 真實 gpt-4o 回覆 / `audit_log` Δ=1）。`cost_ledger` Δ=0；root-cause 深查**推翻**初判的 streaming code bug（loop 用非串流 `chat()`、adapter usage 實測正常 prompt=12/comp=9、`record_llm_call` 缺 pricing 仍寫 0 成本行、yaml 載入 OK、FIX-022 已 wire）。3 衍生 AD：

1. **`AD-RealLLM-CostLedger-ProcessState-Verify`**（✅ **RESOLVED** 2026-06-03，非 code bug）— 已執行重啟驗證：殺光 stale uvicorn reloader/worker → fresh restart 啟動 log `api.main: pricing loader wired`（`main.py:149`，非 `:151` fail-soft）→ smoke `cost_ledger Δ=2`（stale 進程為 Δ=0；input 1987 + output 11 tok）。確認「完全沒 cost 行」為運行進程啟動時 loader 未裝成的 **process-state**，非 code bug。e2e gate `Δ≥2` row-count leg 現已綠。詳 `c11-real-llm-e2e-analysis-20260601.md §8.6`。
2. **`AD-Cost-Ledger-Model-Pricing-Key-Mismatch`**（✅ **CLOSED** Sprint 57.79 — date-suffix normalize + gpt-5.2 yaml）— deployment=`gpt-5.2` / config `model_name`=`gpt-4o` / `config/llm_pricing.yml` 僅 `gpt-4o-mini` → `get_llm_pricing` None → cost 行 `total_cost_usd=0`（`cost_ledger.py:138-144`「observable anomaly」）。修法：對齊 `model_name`↔真實 deployment + 補 pricing yaml 真實模型條目（§8.6 實測 cost_ledger 記錄 model = `azure_openai/gpt-5.2-2025-12-11`，deployment 回傳值，非 gpt-4o）。屬 billing 正確性束（B-7/B-8/C-15）。~1-2 hr。
3. **`AD-Adapter-MaxTokens-NewModel-Param`**（✅ **CLOSED** Sprint 57.79 — adapter max_completion_tokens for gpt-5.x）— gpt-5.2-class deployment 拒 `max_tokens`（回 400「use `max_completion_tokens`」）；loop 主流量未傳故不撞，但 `e2e-real-llm-smoke.yml` 成本護欄（`MAX_TOKENS_PER_CALL`/`max_tokens` `:132`）+ adapter `chat()`/`_stream_impl:282` 需依 model/api-version 切換 param 名。~1-2 hr。

> CI gate（`e2e-real-llm-smoke.yml`）維持手動/關閉（用戶 policy：secret 不進 GitHub）；本機路徑為實際驗收途徑。

---

## 🆕 Sprint 57.84 — C-15 billing-write-atomicity leg CLOSED + sub-items deferred (2026-06-06)

**C-15 的 in-repo billing leg = DONE**（transactional billing Outbox；CHANGE-051；`memory/project_phase57_84_billing_outbox.md`）。`billing_outbox` 表 + enqueue（請求 txn 內原子、ON CONFLICT 冪等 → 無漏扣）+ drainer（per-row txn 精確一次、materialize via 既有 CostLedgerService → 無雙扣）+ lifespan poller；router 已 flip（chat cost-write → billing_outbox enqueue）。real-Azure smoke ✅（gpt-5.2 chain chat→enqueue→drain→cost_ledger，unit_cost>0）。**billing key-chain ②（C-11 57.79 + B-7 57.81 + B-8 57.82/83 + C-15-billing-leg 57.84）= 全部 closed。**

**C-15 剩餘 sub-items — DEFERRED（external-blocked，非本 repo 可獨力完成）**：
- **IaC deploy pipeline** — Bicep 5 模組齊全但 pipeline 停用；需 Azure provision + GitHub Secrets（用戶 policy：secret 不進 GitHub）。
- **DR 自動化 / multi-region / WAL streaming** — 僅設計文件；需確認 Azure Postgres Flexible Server 內建 backup/geo-redundancy 是否滿足 RPO 1h/RTO 4h + 流量管理拓樸決策。
- **Analytics / data warehouse / CDC / dbt / BI** — 0% 實作；全新外部基礎設施。
- **Stripe（外部 billing）consumer** — outbox backbone 已就位（為此設計的解耦）；本 sprint drainer 只 materialize cost_ledger，Stripe drain target 是未來純 worker 變更。
- **enqueue-itself failure** — 目前 logged best-effort（SSE 安全）；罕見、若 metrics 顯示再議。

> 詳見 `claudedocs/5-status/c15-devops-data-platform-analysis-20260601.md`（4 sub-item 現況）。開工任一 sub-item 前需用戶提供對應外部輸入（Azure 資源 / Secrets / 基礎設施決策）。

---

## 🆕 Process / Calibration carryover (2026-06-03 — Area-A 教訓固化副產物)

固化 Area-A（57.66-73）教訓時，6 條可行教訓已 fold-in `.claude/rules/sprint-workflow.md`（Prong-1 test-infra verify / Prong-2 +2 drift rows: codegen-shape + no-live-producer / Risk Class E stale-`--reload`-masks-wiring / Risk Class C 補強 DB-call-test-isolation / Before-Commit item 7 agent-delegation 紀律）+ README-integration-gap-abc A 區同步至 57.73。1 條無法用「一行規則」解決，記此追蹤：

- **`AD-Calibration-AgentDelegated-WallClock-Measure`**（方法論，未解）— 連續 11 個 agent-delegated sprint（57.63→57.73）都拿不到乾淨 wall-clock 量測 → 所有 calibration 點被 CAVEAT、baseline 不動。根因：現行「focused human hours」分母不適配「staged 委派 + parent re-verify」模式（agent wall-clock + parent Day-0/re-verify overhead 未被建模）。需設計新量測口徑（例：分段記 agent wall-clock + parent overhead），agent-delegated sprint 的 ratio 才能重新有信號。**屬獨立小設計，非一行規則** → 故不塞進已精簡的 calibration 規則段，留此待選。

---

## 🆕 Sprint 57.62 Carryover (2026-05-29 — RateLimits Alerting; durable 80%-threshold alert log captured even when unwatched; Phase 58.x RateLimits arc + alert)

Sprint 57.62 (sequential 2-agent — `rl-alerts-backend` 28th + `rl-alerts-frontend` 29th consecutive; durable 80%-threshold usage alerting closing `AD-RateLimits-Alerting-Phase58`) ✅ **CLOSED**: 2 ADs closed (`AD-RateLimits-Alerting-Phase58` + `AD-AgentDelegate-DevStack-Precheck` applied Day 0) + 8 carryovers (5 NEW + 3 continuing). No PROMOTION reaches codify threshold.

### Sprint scope

Day 0 pivot — carryover "SSE infra ~80%" proved FALSE (only SSE is the agent-loop `LoopEvent` stream; admin SSE greenfield ~8-12 hr) → user-locked **Option A persisted alert log** (~4-6 hr). NEW `RateLimitAlert` ORM (`rate_limit_alerts`, severity lowercase `warning`/`critical` 2-tier + CHECK, UNIQUE window) + Alembic `0021` (FORCE RLS 2-policy) + stateless `RateLimitAlertStore.maybe_record` (idempotent peak/escalate `on_conflict_do_update` GREATEST; early-return quota<=0/pct<80; fail-open) hooked into `RedisRateLimitCounter._write_through` (D-DAY0-G: session + 7 values in scope → NO ctor DI / NO main.py wiring) + `GET .../rate-limits/alerts` + frontend `useRateLimitsAlerts` (15s poll) + QuotasTab Recent alerts Card (0 new oklch; existing 2 cards scope-guard). Detection at the enforcement write-through (NOT the GET poll) — the core reason Option A persists: a breach crossing 80% while no admin watches is still captured. 20 NEW pytest + 17 NEW Vitest. Day 1.4 repo-health: cleared a stray orphaned `AA` unmerged remnant on 2 `sprint-52-2` docs (restore-from-HEAD; out of scope; no data loss).

### Still-open RateLimits deeper extensions (Sprint 57.63+ candidates)

1. **`AD-RateLimits-Alerting-Webhook`** (NEW) — push 80%/100% breaches to a tenant-configured webhook / Slack (the persisted log is the substrate); ~3-4 hr.
2. **`AD-RateLimits-Alerting-Ack-Mute`** (NEW) — admin ack / mute / resolve on an alert row (add `resolved_at` like `SLAViolation`) + filter resolved from the Recent alerts card; ~2 hr.
3. **`AD-Quotas-Alerting-Template`** (NEW) — the 57.62 pattern (write-through detection → idempotent alert upsert → GET → polling card) reused for Quotas usage alerts (the Quotas usage card exists from 57.56); ~3 hr.
4. **`AD-RateLimits-DuplicateResource-Validation`** (CONTINUES — 57.61 R7) — PUT-time 422 on two payload items resolving to the same (resource_type, window_type); currently silent last-wins dedup; ~1 hr.
5. **`AD-RateLimits-SyntaxValidation-ClientSide-Polish`** (CONTINUES — 57.61 R5) — mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting; risks a 5th parser copy; ~2 hr.
6. **`AD-RateLimits-Parser-Extract-Shared-Predicate`** (CONTINUES — 57.61 R3) — extract the window-alias table to ONE source the counter + store reference; ~2-3 hr.

### Other carryovers (Sprint 57.63+)

7. **`AD-RepoHealth-Orphaned-Unmerged-Sweep`** (NEW — Q2 lesson) — add a Day-0 `git status --short` scan for `AA`/`UU`/`DD` markers to the 三-Prong (catch orphaned conflicts at sprint start, not the Day-1 commit gate; an orphaned conflict can block a path-scoped commit). 57.62 cost ~15 min to diagnose at the Day-1 sweep; ~0.5 hr to codify.
8. **`AD-AgentFactor-DesignDecisions-Below-Band-Watch`** (NEW — Q4; broadens 57.61 `-BackendOnly-Variant-Watch`) — `-design-decisions` 0.65 now has 2 consecutive below-band readings (57.61 backend-only 0.74 + 57.62 pair 0.77) regardless of shape → R6's "backend-only is the outlier" weakens; likely agent over-delivers generally. Cross-shape watch: if the NEXT `-design-decisions` sprint (either shape) lands < 0.85 → 3rd consecutive cross-shape below → propose tighten `agent_factor` 0.65 → 0.55. Pair-shape sub-sequence mean (0.98) is the only thing holding 0.65.
9. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation`** (DEFERS again — 57.62 was single-domain, not a multi-track bundle; awaits the next genuine `mixed-multidomain-bundle` sprint) · **`AD-MediumBackend-AICadence-Recalibration`** (CONTINUES — class baseline 0.80 recalibration needs human-factor data; the agent-delegation streak has produced no non-agent medium-backend sprint) · **`AD-AgentPrompt-CrossPlatform-Mypy-Warning`** (CONTINUES — 57.62 counter edit touched `rate_limit_counter.py` but mypy did not diverge cross-platform this run) · **`AD-Mypy-WholeDir-Conftest-Collision`** (CONTINUES — pre-existing since 57.53; CI runs `mypy src/` unaffected; Phase 58+).

### Calibration note (Sprint 57.62)

`mechanical-greenfield-design-decisions` 0.65 4th validation (BACK TO PAIR SHAPE) ~0.77 BELOW band by 0.08 → KEEP single-data-point-per-shape (pair sub-seq 57.56=1.02 + 57.57=1.15 + 57.62=0.77 mean ~0.98 IN band). **R6 WEAKENS** (2 consec `-design-decisions` below cross-shape — 57.61 backend-only 0.74 + 57.62 pair 0.77). `medium-backend` 0.80 13th data point ~0.50 — last-3 (57.60+57.61+57.62) 3-consecutive < 0.7 BUT all agent-delegated, confound resolved at agent_factor sub-class layer (actual/agent-adjusted ~0.77 near band; 0.65×0.77≈0.50 coherent) KEEP.

---

## 🆕 Sprint 57.61 Carryover (2026-05-29 — RateLimits SyntaxValidation; PUT-time 422 replaces silent drop; Phase 58.x RateLimits arc write-path fail-loud)

Sprint 57.61 (single code-implementer agent `rl-syntax-validation` 27th consecutive; PUT-time syntax validation closing `AD-RateLimits-SyntaxValidation-Phase58`) ✅ **CLOSED**: 1 AD closed (`AD-RateLimits-SyntaxValidation-Phase58`) + 6 carryovers (4 NEW + 2 continuing). No PROMOTION reaches codify threshold (Prong promotions already codified 57.57+57.60; the 2 NEW agent/process ADs are single-data-point).

### Sprint scope

NEW `is_recognized_rate_limit_value` value-shape predicate (reuses store `_VALUE_RE` + `_WINDOW_ALIASES`; only NEW regex `_CONCURRENCY_RE`; no 4th rate-regex copy) + `field_validator("items")` on `RateLimitsUpsertRequest` (NOT shared `RateLimitItem` — D-DAY0-E) → PUT 422 per-item reason replaces the silent `replace_configs` drop. Accepts enforceable rate + display-only `N concurrent` (D-DAY0-F `"50 concurrent"` default round-trip preserved). US-2 parser-consistency guard locks store⟺counter validity + concurrency asymmetry + window-alias key-equality. 39 NEW tests (16 integration + 23 unit); 0 schema change → frontend untouched.

### Still-open RateLimits deeper extensions (Sprint 57.62+ candidates)

1. **`AD-RateLimits-Alerting-Phase58`** (CARRYOVER) — SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr.
2. **`AD-RateLimits-DuplicateResource-Validation`** (NEW — R7 deferred) — PUT-time 422 on two payload items resolving to the same (resource_type, window_type); currently silent last-wins dedup; ~1 hr.
3. **`AD-RateLimits-SyntaxValidation-ClientSide-Polish`** (NEW — R5 deferred) — mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting; risks a 5th parser copy (weigh carefully); ~2 hr.
4. **`AD-RateLimits-Parser-Extract-Shared-Predicate`** (NEW — R3 follow-on) — extract the window-alias table to ONE source the counter + store reference (migration stays dep-light inline); removes the 2-live-copy smell the US-2 guard currently watches; ~2-3 hr.

### Other carryovers (Sprint 57.62+)

5. **`AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch`** (NEW — Q4 calibration) — `mechanical-greenfield-design-decisions` 0.65 3rd validation (1st backend-only) landed ~0.74 BELOW band; prior 2 (57.56+57.57, backend+frontend pairs) were IN band. Single BELOW point → KEEP 0.65 single-data-point caution. If the NEXT backend-only `-design-decisions` sprint ALSO lands BELOW (2nd consecutive backend-only OOB-below) → propose a `-design-decisions-backend-only` ~0.45 variant OR reclassify backend-only validator/schema work as `-port-style` 0.45 (counterfactual showed `-port-style` 0.45 → ~1.06 IN band for this sprint). Needs a 2nd backend-only data point.
6. **`AD-AgentDelegate-DevStack-Precheck`** (NEW — process lesson) — agent-delegated backend sprints with integration tests should confirm the Postgres/Redis dev stack is up (or state the prerequisite in the agent prompt) so the agent runs the full suite itself; this sprint the parent had to start `docker-compose.dev.yml` (the file name, NOT the `dev.py start docker` default which reported "no configuration file") after the agent reported the integration tests couldn't run. ~single-occurrence; codify if it recurs.
7. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.62`** (DEFERS — was -Sprint-57.61) — 57.61 was single-domain (not a multi-track bundle) so the tightened-0.45 1st validation did NOT generate; awaits the next genuine `mixed-multidomain-bundle` sprint. If that 1st validation under 0.45 is also < 0.7 → escalate 0.30 OR fold into `mechanical-pattern-reuse-heavy` 0.30.
8. **`AD-AgentPrompt-CrossPlatform-Mypy-Warning`** (CONTINUES — 57.59 lesson; 57.61 did NOT touch Redis/asyncpg stubs so it didn't recur) · **`AD-Mypy-WholeDir-Conftest-Collision`** (CONTINUES — pre-existing since 57.53; CI runs `mypy src/` unaffected; Phase 58+ add `__init__.py` to 2 conftest dirs OR pin scope; ~15 min).

### Calibration note (Sprint 57.61)

`mechanical-greenfield-design-decisions` 0.65 3rd validation 1st BACKEND-ONLY ~0.74 BELOW band by 0.11 → KEEP single-data-point caution (3 data points now: 57.56=1.02 + 57.57=1.15 IN band backend+frontend pairs + 57.61=0.74 BELOW backend-only; R6 hypothesis materialized — backend-only validator runs faster). `medium-backend` 0.80 12th data point ~0.48 (confound resolved at agent_factor sub-class layer; last-3 2/3 < 0.7 NOT 3-consec) KEEP.

---

## 🆕 Sprint 57.60 Carryover (2026-05-29 — RateLimits MetaData Cleanup; config single-source; Phase 58.x RateLimits arc config-complete)

Sprint 57.60 (single code-implementer agent `rl-metadata-cleanup` 26th consecutive; retire transitional meta_data fallback closing `AD-RateLimits-MetaData-Cleanup-Phase58`) ✅ **CLOSED**: 1 AD closed (`AD-RateLimits-MetaData-Cleanup-Phase58`) + 2 PROMOTIONS codified (`AD-Day0-Prong2-Nested-Shape-Read` + `AD-Day0-Prong3-Physical-Column-Read` → `sprint-workflow.md §Step 2.5`).

### Still-open RateLimits deeper extensions (Sprint 57.61+ candidates)

1. **`AD-RateLimits-SyntaxValidation-Phase58`** (CARRYOVER) — now easier post-split (config table has typed `quota`/`window_type` columns); PUT-time validation rejecting malformed `value` strings before they reach the table; ~2-3 hr.
2. **`AD-RateLimits-Alerting-Phase58`** (CARRYOVER) — SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr.

### Other carryovers (Sprint 57.61+)

3. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.61`** (DEFERS — was -Sprint-57.60) — 57.60 was single-domain (not multi-track bundle) so the tightened-0.45 1st validation did NOT generate; awaits the next genuine `mixed-multidomain-bundle` sprint. Reminder: if that 1st validation under 0.45 is also < 0.7 → escalate 0.30 OR fold into `mechanical-pattern-reuse-heavy` 0.30.
4. **`AD-AgentPrompt-CrossPlatform-Mypy-Warning`** (CANDIDATE — 57.59 lesson) — agent prompts touching Redis/asyncpg code should flag Risk Class B cross-platform mypy + suggest the dual-ignore pattern. (57.60 did NOT edit Redis/asyncpg stubs so it didn't recur, but the candidate stands for the next such sprint.)
5. **`AD-Mypy-WholeDir-Conftest-Collision`** (NEW — pre-existing since 57.53) — `mypy --strict .` (whole-dir) reports a duplicate-`conftest` collection error (two `tests/integration/{api,agent_harness}/conftest.py` lack `__init__.py`). NOT a CI concern (CI runs `mypy src/`). Phase 58+: add `__init__.py` to the 2 conftest dirs OR pin the mypy invocation scope; ~15 min.

### Calibration note (Sprint 57.60)

`mechanical-pattern-reuse-heavy` 0.30 1st DELIBERATE FORWARD application ratio ~1.09 IN BAND ✅ KEEP (2 data points now: 57.49 retroactive 0.21 + 57.60 forward 1.09 — wide shape-variance; if a future ≥20× repetition sprint at 0.30 lands < 0.7 again, consider tier `-high-repetition` ~0.20 vs `-moderate` 0.30). `medium-backend` 0.80 11th data point ~0.33 (deepest confound; resolved at agent_factor sub-class layer) KEEP.

---

## 🆕 Sprint 57.59 Carryover (2026-05-28 — RateLimits Potemkin Migration C1 two-table split; Phase 58.x deeper extensions 2/5; AP-4 CLOSED)

Sprint 57.59 (2 sequential code-implementer agents — `rl-config-table` 24th + `rl-runtime-repoint` 25th consecutive; C1 two-table split closing the AP-4 Potemkin surfaced Sprint 57.58) ✅ **CLOSED**: 2 ADs closed (`AD-RateLimits-Potemkin-Migration-Phase58` + folded `AD-RateLimits-DedicatedTable-Phase58`) + 3 NEW carryovers.

### Sprint scope

NEW `rate_limit_configs` table (durable config) + activate dormant `rate_limits` usage table (AP-4 closed) + migrate `meta_data` JSONB → config rows (additive) + re-point all 4 RateLimits paths (GET/PUT/usage/middleware). API shapes UNCHANGED → frontend untouched. Alembic `0019` + 2 RLS policies + inline-parse data migration. Redis write-through to usage table (window_start+window_end upsert) + restart recovery.

### 2 ADs closed

1. ✅ `AD-RateLimits-Potemkin-Migration-Phase58` (CLOSED — `rate_limits` usage table now written + queried; AP-4 resolved)
2. ✅ `AD-RateLimits-DedicatedTable-Phase58` (CLOSED — folded into this sprint; the "dedicated table" IS the activated `rate_limits` + new `rate_limit_configs`)

### 3 NEW carryovers

1. **`AD-RateLimits-MetaData-Cleanup-Phase58`** (NEW — after 1-2 sprints validating table path stable → remove `meta_data["rate_limits"]` read-fallback + transitional dual-write + clear stored JSONB via data migration; ~1-2 hr)
2. **`AD-Day0-Prong3-Physical-Column-Read`** (NEW — Q3 Lesson: D-DAY1-1 tenants JSONB physical column is `metadata` not ORM attr `meta_data`; codify Prong 3 "read physical column names + full schema, not ORM attr names"; combine with Sprint 57.58 `AD-Day0-Prong2-Nested-Shape-Read` — both "read the body, not the name"; codify when 2 data points)
3. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.60`** (NEW — 1st validation under tightened 0.45; 57.58=0.49 + 57.59=0.34 → 2 consec < 0.7 → tightened 0.65→0.45; if 57.60 also < 0.7 → escalate 0.30 / fold into `mechanical-pattern-reuse-heavy` 0.30)

### Still-open RateLimits deeper extensions (Sprint 57.60+ candidates)

- **`AD-RateLimits-MetaData-Cleanup-Phase58`** (above — natural follow-on; small)
- **`AD-RateLimits-SyntaxValidation-Phase58`** (now easier post-split: config table has typed `quota`/`window_type` columns; PUT-time validation)
- **`AD-RateLimits-Alerting-Phase58`** (SSE 80% threshold; pairs with the activated usage table)

---

## 🆕 Sprint 57.58 Carryover (2026-05-28 — RateLimits RuntimeEnforcement D3 Full; Phase 58.x deeper extensions 1/5; AP-4 Potemkin caught Day 0)

Sprint 57.58 (4 tracks via 2 sequential code-implementer agents — backend `rl-backend` 22nd + frontend `rl-frontend` 23rd consecutive chain; **Path B** JSONB config + Redis sliding window counter) ✅ **CLOSED**: 2 ADs closed (1 CLOSED + 1 PARTIAL-CLOSE) + 3 NEW carryovers.

### Sprint scope

Transform `tenant.meta_data["rate_limits"]` from admin-display-only (Sprint 57.48+57.57 WRITE storage) into RUNTIME-ENFORCED. Day 0 三-Prong 9 findings (4 RED path + 4 NOTABLE + **1 CRITICAL AP-4 Potemkin `RateLimit` ORM**) → user chose **Path B** at AskUserQuestion gate (NOT activate dormant ORM).

- **Track A** (Cat 12 platform): NEW `platform_layer/middleware/rate_limit.py` `RateLimitMiddleware(BaseHTTPMiddleware)` (fail-open + 429 + Retry-After/X-RateLimit-* headers + bypass via `roles` claim) + `platform_layer/tenant/rate_limit_counter.py` `RedisRateLimitCounter` MULTI/EXEC pipeline sliding window + `parse_rate_limit_item()` normalizer; EDIT `api/main.py` register + `_lifespan` Redis wiring
- **Track B** (Cat 2, LLM-neutral): `RateLimitGate` Protocol pre-call hook in `tools/executor.py` + `RedisToolRateLimitGate` adapter + `RateLimitExceededError` FATAL (no LLM retry)
- **Track C**: `GET /admin/tenants/{tid}/rate-limits/usage` peek endpoint + Pydantic models
- **Track D**: `useRateLimitsUsage` 5s polling hook + QuotasTab Live usage Card (reused `.bar-track` + `var(--success/--warning/--danger)`; 0 new oklch; Rate limits Card UNCHANGED scope-guard)

### 2 ADs closed

1. ✅ `AD-RateLimits-RuntimeEnforcement-Phase58` (CLOSED — runtime middleware + Cat 2 tool layer enforcement shipped)
2. 🔸 `AD-RateLimits-LiveUsageTracking-Phase58` (PARTIAL-CLOSE — live usage exposure via GET endpoint + frontend Card DONE; per-rule alerting threshold remains → folds into `AD-RateLimits-Alerting-Phase58`)

### 3 NEW carryovers

1. **`AD-RateLimits-Potemkin-Migration-Phase58`** (NEW — Day 0 D-DAY0-CRITICAL: `RateLimit` ORM `api_keys.py:141` table `rate_limits` dormant since Phase 49 V2 baseline, NEVER wired = AP-4 Potemkin. Sprint 57.59+ ~5-8 hr: activate ORM as persistence layer OR formally delete. Folds in CONDITIONAL `AD-RateLimits-DedicatedTable-Phase58` — same table.)
2. **`AD-Day0-Prong2-Nested-Shape-Read`** (NEW — Q3 Lesson 1: D-DAY1-1 stored shape was `{label,value}` UI strings not `{resource,window,limit}`; Prong 2 grep matched the key but not nested dict shape. Codify "when plan asserts `X["key"] = {a,b,c}`, Day 0 Prong 2 reads the Pydantic/serializer body not just greps the key" into `sprint-workflow.md §Step 2.5 Prong 2` when 2-3 data points accumulate.)
3. **`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Validation-Sprint-57.59`** (NEW — 2nd validation of `mixed-multidomain-bundle-mechanical` 0.65 tier-3; Sprint 57.58 1st = ~0.49 BELOW band single-data-point caution KEEP; if 2nd also < 0.7 tighten 0.45, if > 1.20 rollback 1.0.)

### Still-open RateLimits deeper extensions (Sprint 57.59+ candidates)

- **`AD-RateLimits-SyntaxValidation-Phase58`** (PUT-time parse `"100 / min"` → structured; ~2 hr port-style)
- **`AD-RateLimits-Alerting-Phase58`** (per-rule SSE/webhook alert when threshold crossed; pairs with the Live usage Card shipped this sprint)
- **`AD-RateLimits-Potemkin-Migration-Phase58`** (above — natural follow-on closing the AP-4 surfaced this sprint)

---

## 🆕 Sprint 57.57 Carryover (2026-05-27 — RateLimits WRITE-side ship; Phase 58.x portfolio FINAL 4/4 CLOSURE 🎉; tier-4 SPLIT FULLY VALIDATED)

Sprint 57.57 (single greenfield NEW component-pair via sequential agent delegation Track A backend + Track B frontend; **Phase 58.x portfolio FINAL ship — WRITE-side wave complete**) ✅ **CLOSED**: **5 ADs CLOSED simultaneously** + 5 NEW Phase 58+ RateLimits extension carryovers.

### Sprint scope

WRITE side only per Day 0 三-prong (18 findings: 13 GREEN + 0 RED + 5 NOTABLE; storage path `tenant.meta_data["rate_limits"]` established Sprint 57.48 Track D — zero plan mid-Day-0 pivot vs Sprint 57.55+57.56 RED situations):

- Backend: NEW Pydantic `RateLimitsUpsertRequest`/`Response` (reuses Sprint 57.48 `RateLimitItem` verbatim) + NEW `PUT /admin/tenants/{tid}/rate-limits` endpoint via dict-identity-swap pattern on `tenant.meta_data["rate_limits"]` JSONB + manual `append_audit("tenant_rate_limits_upsert")` (Sprint 57.3 + 57.56 precedent) + 10 NEW pytest tests + `RATE_PUT_%` LIKE sweep
- Frontend: NEW `useRateLimitsSave` mutation hook (verbatim mirror Sprint 57.56 `useQuotasSave`) + types + service func + QuotasTab RateLimits Card edit mode with **variable-length list UX** (add row + per-row Remove + per-row label+value text inputs + empty list save allowed + reverse-projection draft seed + Usage Card UNCHANGED scope guard verified) + softened BackendGapBanner (2nd banner) + D-DAY1-2 Karpathy §3 cleanup (removed obsolete `handleRequestIncrease` placeholder) + 18 NEW Vitest tests

### Q4 Calibration outcome — TIER-4 SPLIT FULLY VALIDATED ✅

**`mechanical-greenfield-design-decisions` 0.65 — 2nd validation IN BAND top edge → 2 consec IN band cleanly**:
- Sprint 57.56 (1st): ratio ~1.02 ✅ IN BAND middle
- Sprint 57.57 (2nd): ratio ~1.15 ✅ IN BAND top edge
- **2-pt mean** ~1.08 IN BAND middle-to-top edge
- **tier-4 SPLIT FULLY VALIDATED** with 2 consec IN band; KEEP 0.65 baseline; rollback rule baseline established (need 3 consec OOB-same-direction to fire structural action)
- Sprint 57.54+57.55 retroactive `-design-decisions` mapping VINDICATED (Sprint 57.55 retro Q4 decision validated by Sprint 57.56+57.57 evidence)

`medium-backend` 0.80 10th data point ~0.72 (10-pt mean 0.66; last-3 mean ~0.72; KEEP per `When to adjust` 3-sprint window rule; lower-trigger NOT MET)
`medium-frontend` 0.65 7th data point ~0.55 (5th consecutive < 0.7 lower-trigger MET BUT KEEP per confound-resolved-at-sub-class-layer discipline; `AD-medium-frontend-Baseline-Recalibration` continues Sprint 57.58+ 8th data point)

### 5 ADs CLOSED simultaneously

1. ✅ `AD-AgentFactor-Tier-4-Validation-Sprint-57.57` (Sprint 57.56 carryover — 2nd validation data point under tier-4 sub-class table; ratio ~1.15 IN BAND top edge → tier-4 SPLIT 2nd validation CONFIRMED CLEANLY)
2. ✅ `AD-TenantSettings-RateLimits-Write-Endpoint` (Sprint 57.48-57.50+ carryover — Phase 58.x portfolio FINAL 4/4 closed; WRITE-side wave complete)
3. ✅ `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` (PROMOTION codified into `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies` as MANDATORY plan-time field; 5-data-point evidence Sprint 57.53+57.54+57.55+57.56+57.57 consecutive)
4. ✅ `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` (PROMOTION codified as NEW Drift Class row **Claimed-but-missing-storage-path** in `§Step 2.5 Prong 2 Drift Class table`; 3-data-point evidence: Sprint 57.55 RED + 57.56 RED + 57.57 GREEN inverse-validation)
5. ✅ `AD-Day0-Prong2-CanonicalService-Grep` (PROMOTION codified as NEW Drift Class row **Claimed-but-missing-canonical-service** in `§Step 2.5 Prong 2 Drift Class table`; 2-data-point both directions actionable: Sprint 57.55 positive direction + 57.56 inverse direction + 57.57 inverse continued)

### 5 NEW carryovers (Phase 58+ RateLimits extensions)

1. **`AD-RateLimits-SyntaxValidation-Phase58`** (NEW — parse "100 / min" into structured `{limit: int, unit: "request", period: "minute"}` shape; currently raw display strings)
2. **`AD-RateLimits-RuntimeEnforcement-Phase58`** (NEW — currently `tenant.meta_data["rate_limits"]` is admin display only; no runtime enforcement; needs runtime middleware reading the override list)
3. **`AD-RateLimits-LiveUsageTracking-Phase58`** (NEW — analogous to `AD-Quotas-LiveUsageTracking-Phase58`; per-rule live usage counter exposure)
4. **`AD-RateLimits-Alerting-Phase58`** (NEW — per-rule alerting thresholds + notification webhook)
5. **`AD-RateLimits-DedicatedTable-Phase58`** (NEW CONDITIONAL — Sprint 57.48 D-DAY0-5 noted; Phase 58+ option if persistence requirements grow beyond JSONB)

Optional additional (not from Sprint 57.57 ship; reclassified from Sprint 57.56 close — informational):

- **`AD-RateLimits-OptimisticConcurrency`** (NEW CONDITIONAL — Phase 58+ If-Match header pattern if concurrent edit race conditions surface)
- **`AD-AgentFactor-Tier-4-Validation-Sprint-57.58`** (NEW CONDITIONAL — IF Sprint 57.58 chooses agent-delegated sprint under tier-4 `-design-decisions` 0.65, generates 3rd validation data point; tier-4 SPLIT now FULLY VALIDATED with 2-consec IN band so this carryover is informational tracking — NOT blocking for any user direction)

### Carryovers from Sprint 57.56 still active (re-list; informational)

- **`AD-Quotas-LiveUsageTracking-Phase58`** + **`AD-Quotas-UsageHistory-Phase58`** + **`AD-Quotas-Alerting-Phase58`** + **`AD-Quotas-RequestIncrease-Workflow-Phase58`** + **`AD-Quotas-PlanUpgrade-AutoRollover-Phase58`** + **`AD-Quotas-OptimisticConcurrency`** (Phase 58+ deeper Quotas extensions; out of Sprint 57.58 scope unless explicitly selected)
- **`AD-FeatureFlags-RegistryCRUD-Phase58`** + **`AD-FeatureFlags-NumericOverrides-Phase58`** + **`AD-FeatureFlags-AuditLogFiltering-UI-Phase58`** + **`AD-FeatureFlags-PerFlag-RolloutSchedule-Phase58`** + **`AD-FeatureFlags-OptimisticConcurrency`** (Phase 58+ FF deeper extensions)
- **`AD-TenantSettings-Identity-Persistence-Phase58`** (Sprint 57.50 carryover continues; full SSO admin schema)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (Sprint 57.53-57.57 carryover continues; Phase 58.x — extract `_clear_committed_test_tenants` LIKE patterns to shared helper after 4 sprints of `<RESOURCE>_PUT_%` extensions)
- **`AD-MediumBackend-AICadence-Recalibration`** (Sprint 57.53-57.57 carryover continues; Phase 58+ — revisit `medium-backend` 0.80 if next 2-3 human-factor sprints continue at 0.70-0.85 lower edge)
- **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49-57.57 carryover continues; need consistent human-factor data point to recalibrate; agent-delegated confound persists across 5 sprints 57.49+57.54+57.55+57.56+57.57)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Sprint 57.54-57.57 carryover continues — codify multi-pattern test file glob)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Sprint 57.54-57.57 carryover continues — pattern template now 4-data-point base after Sprint 57.57; reference template for Phase 58+ similar work; documents 4-architecture decision tree)

### Phase 58.x portfolio progress

- 1/4 (Sprint 57.54 HITLPolicies) → 2/4 (Sprint 57.55 FeatureFlags) → 3/4 (Sprint 57.56 Quotas) → **4/4 (Sprint 57.57 RateLimits) ✅ FINAL CLOSURE 🎉**
- WRITE-side wave complete; Phase 58+ moves to deeper extensions per individual AD carryovers above

### Mockup-fidelity DUAL CLEAN milestone

**13 consecutive sprints 57.45-57.57** preserved 22/22 PARITY + HEX_OKLCH baseline 47. **Strongest streak of Phase 57+ epic**; no regression on drift-audit-2026-05-25 #1 priority since closure.

---

## Sprint 57.56 Carryover (2026-05-27 — Quotas WRITE-side ship; Phase 58.x portfolio 3/4; tier-4 1st validation CONFIRMED CLEANLY)

Sprint 57.56 (single greenfield NEW component-pair via sequential agent delegation Track A backend + Track B frontend; **architectural simplification path** — direct ORM UPDATE vs Sprint 57.54+57.55 canonical service paths) ✅ **CLOSED**: 1 AD CLOSED + 3 NEW carryovers.

### Sprint scope

True gap = WRITE side only per D-DAY0-A 🔴 RED resolved via user Option B Recommended (BEFORE plan v1 drafting; zero rework cycle):
- Backend: NEW `_PLAN_QUOTA_RESOURCE_WHITELIST` frozenset + Pydantic `QuotaOverridesUpsert{Request,Response}` + `_project_plan_quota_to_items` overrides param extension + GET refactor + NEW `PUT /admin/tenants/{tid}/quotas` endpoint dict-identity-swap SQLAlchemy JSONB pattern + manual `append_audit` (Sprint 57.3 PATCH precedent; D-DAY1-1 helper name fix-forward) + 12 NEW pytest + `QUOTA_PUT_%` LIKE sweep
- Frontend: NEW `useQuotasSave` mutation hook (verbatim mirror Sprint 57.55 `useFeatureFlagsSave`) + types + service func + QuotasTab Usage quotas Card edit mode (Edit/Cancel/Save + per-row numeric input + Clear override + reverse-projection draft seed + auto-exit on success + tenant-switch reset + inline error + softened BackendGapBanner) + **RateLimits Card UNCHANGED** scope guard verified via 11th assertion test + 15 NEW Vitest

### Q4 Calibration outcome — TIER-4 1ST VALIDATION ✅ CONFIRMED CLEANLY

**`mechanical-greenfield-design-decisions` 0.65 — 1st validation IN BAND middle**:
- Sprint 57.56 (1st): ratio actual/agent-adjusted ~**1.02** ✅ IN BAND middle [0.85, 1.20]
- **tier-4 SPLIT 1st validation CONFIRMED CLEANLY**; KEEP 0.65 baseline
- Sprint 57.54+57.55 retroactive `-design-decisions` mapping VINDICATED (equivalent ratios 1.05-1.55 / 1.21 → Sprint 57.56 ~1.02 bullseye)
- Flag Sprint 57.57+ 2nd validation under same sub-class for rollback rule baseline

`medium-backend` 0.80 9th data point 0.66 (BELOW band by 0.19; 9-pt mean ~0.65; last 3 = 2/3 < 0.7 lower-trigger NOT MET; KEEP per confound-resolved-at-sub-class-layer discipline)
`medium-frontend` 0.65 6th data point ~0.50 (BELOW band 4th consecutive sprint; KEEP per same discipline; AD-medium-frontend-Baseline-Recalibration continues — need consistent human-factor data point)

### 1 AD CLOSED

1. ✅ `AD-AgentFactor-Tier-4-Validation-Sprint-57.56` (Sprint 57.55 carryover — 1st validation data point under tier-4 sub-class table; ratio ~1.02 IN BAND middle → tier-4 SPLIT 1st validation CONFIRMED CLEANLY)

### 3 NEW carryovers

1. **`AD-AgentFactor-Tier-4-Validation-Sprint-57.57`** (NEW priority — 2nd validation needed under tier-4 `mechanical-greenfield-design-decisions` 0.65 for rollback rule baseline; Sprint 57.57 RateLimits WRITE = natural candidate; same architectural simplification as Sprint 57.56)
2. **`AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`** PROMOTION-CANDIDATE (Sprint 57.53+57.54+57.55+57.56 = 4-data-point evidence reached; per AD-Plan-2/3/4/5 promotion precedent 3-data-point sufficient; promote to MANDATORY field in `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies`)
3. **`AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** PROMOTION-CANDIDATE (Sprint 57.55 + 57.56 = 2 mid-plan-draft pivots in 2 sprints; 3-data-point evidence across Sprint 57.54+57.55+57.56 reached; promote to NEW Drift Class row in `sprint-workflow.md §Step 2.5 Prong 2 Drift Class table`)

### Carryovers from Sprint 57.55 still active (re-list)

- **`AD-Day0-Prong2-CanonicalService-Grep`** PROMOTION-CANDIDATE (Sprint 57.55 → Sprint 57.56 = 2-data-point evidence; both directions actionable — service exists OR doesn't; promote to MANDATORY rule)
- **`AD-FeatureFlags-RegistryCRUD-Phase58`** + **`AD-FeatureFlags-NumericOverrides-Phase58`** + **`AD-FeatureFlags-AuditLogFiltering-UI-Phase58`** + **`AD-FeatureFlags-PerFlag-RolloutSchedule-Phase58`** + **`AD-FeatureFlags-OptimisticConcurrency`** (Phase 58+ FF deeper extensions; out of Sprint 57.56+57.57 scope)
- **`AD-Quotas-LiveUsageTracking-Phase58`** (NEW Sprint 57.56 — expose QuotaEnforcer Redis counters at admin layer for `current_usage` real value)
- **`AD-Quotas-UsageHistory-Phase58`** (NEW Sprint 57.56 — per-resource usage history / trend chart UI)
- **`AD-Quotas-Alerting-Phase58`** (NEW Sprint 57.56 — per-resource alerting thresholds)
- **`AD-Quotas-RequestIncrease-Workflow-Phase58`** (NEW Sprint 57.56 — existing "Request increase" button is alert stub; backend endpoint + approval workflow)
- **`AD-Quotas-PlanUpgrade-AutoRollover-Phase58`** (NEW Sprint 57.56 — override map invalidation logic on tenant plan change)
- **`AD-Quotas-OptimisticConcurrency`** (CONDITIONAL Sprint 57.56 — Phase 58+ If-Match header)
- **`AD-TenantSettings-RateLimits-Write-Endpoint`** (Phase 58.x portfolio remaining — **FINAL** 4/4; Sprint 57.57 natural candidate; same direct-ORM mechanical-greenfield-design-decisions pattern as Sprint 57.56)
- **`AD-TenantSettings-Identity-Persistence-Phase58`** (Sprint 57.50 carryover continues; full SSO admin schema)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (Sprint 57.53+57.54+57.55+57.56 carryover continues; Phase 58.x)
- **`AD-MediumBackend-AICadence-Recalibration`** (Sprint 57.53+57.54+57.55+57.56 carryover continues; Phase 58+)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Sprint 57.54 carryover already CLOSED Sprint 57.55 — pattern in usage)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Sprint 57.54+57.55+57.56 carryover continues — template now has 3 sub-patterns: dedicated table + canonical service / JSONB on registry + canonical service / JSONB on tenants + direct ORM; Sprint 57.57 RateLimits will be 4th data point validating the JSONB-on-tenants + direct ORM sub-pattern)

### Phase 58.x portfolio progress

- 1/4 (Sprint 57.54 HITLPolicies) → 2/4 (Sprint 57.55 FeatureFlags) → **3/4 (Sprint 57.56 Quotas)** ✅
- Remaining: RateLimits (Sprint 57.57 candidate; final 4/4)

### Mockup-fidelity DUAL CLEAN milestone

**12 consecutive sprints 57.45-57.56** preserved 22/22 PARITY + HEX_OKLCH baseline 47. Strongest streak of Phase 57+ epic; no regression on drift-audit-2026-05-25 #1 priority since closure.

---

## Sprint 57.55 Carryover (2026-05-27 — FeatureFlags WRITE-side ship; Phase 58.x portfolio 2/4; tier-4 SPLIT ACTIVATED)

Sprint 57.55 (single greenfield NEW component-pair via sequential agent delegation Track A backend + Track B frontend) ✅ **CLOSED**: 4 ADs CLOSED.

### Sprint scope

True gap = WRITE side only per D-DAY0-B 🔴 RED pivot + D-DAY0-T 🆕 NOTABLE canonical service path:
- Backend: NEW `clear_tenant_override` method on `FeatureFlagsService` + `_project_feature_flags_for_tenant` helper extract + `PUT /admin/tenants/{tid}/feature-flags` composite-replace endpoint (SET+CLEAR loops via canonical service) + Pydantic `FeatureFlagOverridesUpsertRequest`/`Response` + 12 NEW pytest
- Frontend: NEW `useFeatureFlagsSave` mutation hook (verbatim mirror Sprint 57.54) + types + service func + FeatureFlagsTab edit mode (per-row Switch + Clear override + reverse-projection draft seed + tenant-switch reset + softened BackendGapBanner) + 13 NEW Vitest

### Q4 Calibration outcome — TIER-4 SPLIT ACTIVATED

**`mechanical-greenfield` 0.50 — 2nd validation ABOVE band by 0.37 → 2 consec > 1.20 ROLLBACK RULE MET**:
- Sprint 57.54 (1st): ~1.37-2.0 ABOVE
- Sprint 57.55 (2nd): ~1.57 ABOVE
- **TIER-4 SPLIT ACTIVATED** per Sprint 57.54 CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement`:
  - `mechanical-greenfield-port-style` 0.45 RESERVED (single NEW component-pair via mirror-port; NO NEW design)
  - `mechanical-greenfield-design-decisions` 0.65 NEW (single NEW component-pair WITH NEW Pydantic + UX state design)
- Retroactive mapping Sprint 57.54+57.55 = `-design-decisions`; equivalent ratios 1.05-1.55 / 1.21 IN band top edge ✅

`medium-backend` 0.80 8th data point 0.79; last-3 mean 0.87 IN band lower-middle; KEEP
`medium-frontend` 0.65 5th data point 0.53; lower-trigger criteria MET but confound at tier-4 sub-class layer (human-equivalent 1.07 IN BAND); KEEP per discipline

### 4 ADs CLOSED

1. ✅ `AD-AgentFactor-Tier-3-Validation-Sprint-57.55` (2nd validation generated; rollback rule MET → tier-4 SPLIT)
2. ✅ `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement` (Sprint 57.54 CONDITIONAL → ACTIVATED via tier-4 SPLIT)
3. ✅ `AD-FeatureFlags-PerFlag-AuditLog-Phase58` (REMOVED — canonical service auto-emits audit chain; positive side-effect)
4. ✅ `AD-Day0-Prong1-Test-Glob-Multi-Pattern` (Sprint 57.54 carryover; pattern confirmed in usage Sprint 57.55)

### 3 NEW carryovers

1. **`AD-AgentFactor-Tier-4-Validation-Sprint-57.56`** (NEW — 1st validation needed under tier-4 `mechanical-greenfield-design-decisions` 0.65 baseline; Sprint 57.56 Quotas WRITE candidate)
2. **`AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** (Lesson 1 codification — extend sprint-workflow.md §Step 2.5 Prong 2 Drift Class table with Phase 58.x WRITE-side resource storage architecture identification row)
3. **`AD-Day0-Prong2-CanonicalService-Grep`** (Lesson 2 codification — extend Phase 58.x WRITE-side pattern template with canonical service grep step BEFORE plan §4)

### Phase 58.x portfolio progress

- ✅ Sprint 57.54: HITLPolicies WRITE (1/4)
- ✅ **Sprint 57.55: FeatureFlags WRITE (2/4)**
- 🔄 Sprint 57.56: Quotas WRITE (3/4 — natural next candidate per Option B cadence; 1st validation under tier-4 `-design-decisions` 0.65)
- 🔄 Sprint 57.57: RateLimits WRITE (4/4)

---

## Sprint 57.54 Carryover (2026-05-26 — HITLPolicies WRITE-side ship; Phase 58.x portfolio item; tier-3 `mechanical-greenfield` 0.50 1st validation)

Sprint 57.54 (single greenfield NEW component-pair via sequential agent delegation Track A backend + Track B frontend) ✅ **CLOSED**: 1 carryover AD closed (`AD-AgentFactor-Tier-3-Validation-Sprint-57.54` Sprint 57.53 carryover; 1st validation generated under agent-delegated mode).

### Sprint scope (true gap = WRITE side after Day 0 critical pivot)

**Original framing (WRONG)**: Phase 58.x = NEW table + Alembic. **Day 0 Prong 2 content verify at plan-drafting time** revealed table + ORM + RLS + read-only `DBHITLPolicyStore.get` + GET endpoint + frontend read hook ALL exist since Sprint 55.3 (Alembic 0013) + 57.48 (admin GET) + 57.49 (frontend tab). **True gap = WRITE side only**:

**Backend Track A** (~25 min agent wall-clock; 14th consecutive code-implementer):
- NEW `DBHITLPolicyStore.put(tenant_id, policy)` upsert via `pg_insert.on_conflict_do_update` (**1st usage of pattern in repo** D-DAY0-13 NOTABLE; LOW risk under V2 PostgreSQL-only stance)
- NEW Pydantic `HITLPolicyUpsertRequest` (`extra="forbid"` + `field_validator` on risk enums) + `HITLPolicyUpsertResponse`
- NEW `PUT /api/v1/admin/tenants/{tenant_id}/hitl-policies` endpoint (composite write; reuses `_load_tenant_or_404` + `_session_factory_from` + `_project_hitl_policy_to_items` for response.items cache hydration)
- 12 NEW pytest tests covering auth/404/upsert-create/upsert-update/projection/422 risk enum/422 extra field/multi-tenant isolation/idempotency/persistence verify/empty dicts
- `tests/integration/api/conftest.py` extended with `HITL_PUT_%` LIKE cleanup sweep (parallels Sprint 57.12 + 57.53 `§Committed-Row Cleanup Pattern` at sibling scope)

**Frontend Track B** (~25 min agent wall-clock; 15th consecutive):
- NEW `saveHITLPolicies` service func (PUT pattern mirror of `updateTenantSettings`)
- NEW `useHITLPoliciesSave` TanStack mutation hook (mirror `useTenantSettingsSave` Sprint 57.9 precedent verbatim; invalidates `HITL_POLICIES_QUERY_KEY_BASE` on success)
- NEW `HITLPolicyUpsertRequest`/`HITLPolicyUpsertResponse` TypeScript types
- HITLPoliciesTab edit mode (Edit/Cancel/Save buttons + per-risk reviewer/SLA inputs + reverse-projection items→composite draft seed + softened BackendGapBanner copy + error display)
- 10 NEW Vitest tests (3 hook + 2 service + 5 tab; +10 vs plan +5-8 target justified for full edit-mode state coverage)

### Validation (9/9 GREEN)

- pytest **1772 PASS + 4 skip + 0 fail** (+12 NEW; exact target)
- mypy --strict **0/310 errors**
- 9/9 V2 lints **GREEN** (incl. HEX_OKLCH 47 preserved via `check_ap4_frontend_placeholder.py`)
- Vitest **617 PASS / 0 fail** (+10 NEW)
- Vite build clean (3.36s); tsc strict 0 errors; ESLint 0 errors
- LLM SDK leak 0

### Calibration outcome (TIER-3 1ST VALIDATION)

- Bottom-up ~3.5 hr → class-calibrated ~2.8 hr (mult 0.80) → agent-adjusted ~1.4 hr (factor 0.50 `mechanical-greenfield` tier-3)
- Actual estimated total ~2.7-2.9 hr (Day 0+1 ~1.92 hr + Day 2 ~0.7-1.0 hr)
- **Ratio actual/agent-adjusted ≈ ~2.0** ABOVE band [0.85, 1.20] by ~0.8 (Day 0+1 only sub-validation ~1.37 ABOVE by 0.17) = **1st rollback-trigger > 1.20 candidate**
- Ratio actual/class-committed ≈ ~1.0 ✅ IN BAND middle (`medium-backend` 0.80 class baseline holds cleanly when confound stripped at tier-3 sub-class layer)
- **Decision per Sprint 57.52 retro Q4 single-data-point caution rule**: **KEEP `mechanical-greenfield` 0.50** + flag Sprint 57.55+ for 2nd validation

**Root cause analysis**: Sprint 57.40-44 mockup-strict-rebuild was pure mechanical port (~5× speedup vs human); Sprint 57.54 is single greenfield NEW feature with backend upsert design + Pydantic write schema decisions + frontend edit-mode UX (~2× speedup not ~5×). The 0.50 baseline may be too aggressive for true greenfield work; sub-class refinement candidate `mechanical-greenfield-port-style` (0.45) vs `mechanical-greenfield-design-decisions` (0.65) — defer to 2nd-3rd data point evidence.

### Class baseline tracking

- `medium-backend` 0.80 **7th data point ratio ~1.0 ✅ IN BAND middle** (7-pt mean 0.63; last 3 only 1/3 < 0.7 lower-trigger NOT MET; **KEEP** — Sprint 57.50/57.53 retro Q4 prediction validated 2x: when agent_factor confound stripped at sub-class layer, class baseline holds cleanly for human-pace + agent residual captured at tier-3)
- `medium-frontend` 0.65 **3rd data point** confound persists; 4-pt mean ~0.56 below band; `AD-medium-frontend-Baseline-Recalibration` continues for Sprint 57.55+ 5th data point

### 14th + 15th consecutive code-implementer agent delegation

Sprint 57.40-50 chain extends from 13 to 15 consecutive delegations. Sprint 57.53 was parent-assistant-direct (chain broken at 13 historical). Sprint 57.54 resumes pattern with sequential Track A + Track B delegation.

### Mockup-fidelity DUAL CLEAN milestone PRESERVED

22/22 PARITY (Sprint 57.45 milestone) preserved through **10 consecutive sprints 57.45-57.54**. Edit mode UI additions used existing token references only; HEX_OKLCH baseline 47 unchanged; AP-2 banner intact + AP-4 frontend placeholder lint GREEN.

### Carryover ADs after Sprint 57.54

**NEW for Sprint 57.55+**:
- **`AD-AgentFactor-Tier-3-Validation-Sprint-57.55`** (highest priority — 2nd validation needed under `mechanical-greenfield` 0.50; candidate substrates: 3 remaining Phase 58.x WRITE-side ADs FeatureFlags/Quotas/RateLimits)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Q3 Lesson 1 codification — D-DAY0-1 Glob false-negative: `__tests__/` convention NOT used in repo; actual layout `frontend/tests/unit/<feature>/` mirror; codify multi-pattern test file glob in `.claude/rules/sprint-workflow.md §Step 2.5 Prong 1`)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Q3 Lesson 2 codification — Sprint 57.54 pattern reusable as template for FeatureFlags/Quotas/RateLimits WRITE sprints; if batched 4-track → `mechanical-pattern-reuse-heavy` 0.30 candidate; if single domain at a time → continue `mechanical-greenfield` 0.50 2nd validation)
- **`AD-Sub-Class-Greenfield-Port-vs-Design-Refinement`** (CONDITIONAL — Q4 root cause analysis; split `mechanical-greenfield` 0.50 into `-port-style` 0.45 vs `-design-decisions` 0.65 if 2-3 consecutive > 1.20 patterns surface)

**Phase 58.x portfolio CONTINUES** (3 remaining WRITE-side ADs):
- `AD-TenantSettings-FeatureFlags-Backend-Persistence-WriteSide`
- `AD-TenantSettings-Quotas-Backend-Persistence-WriteSide`
- `AD-TenantSettings-RateLimits-Backend-Persistence-WriteSide`

(All can use Sprint 57.54 pattern as template per `AD-Phase58-Persistence-WriteSide-Pattern-Template`. Sprint 57.55+ candidate substrate decision: pick one of these → 2nd validation data point; OR batch 2-3 → likely shifts class to `mechanical-pattern-reuse-heavy` 0.30 sub-class.)

**Sprint 57.53 carryover items CONTINUE**:
- `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` — Sprint 57.54 successfully filled the field at plan time; ready to codify into `sprint-workflow.md §Workload Calibration §Four-segment form` as MANDATORY field after Sprint 57.55 also fills cleanly
- `AD-Test-Cleanup-Pattern-Shared-Helper` — Sprint 57.54 Track A naturally extended Sprint 57.12 + 57.53 trail; helper extraction (separate `tests/common/cleanup.py`) still deferred Phase 58.x; pattern now battle-tested across 3 scopes
- `AD-MediumBackend-AICadence-Recalibration` — Sprint 57.54 7th data point at ratio ~1.0 IN BAND middle (cleaner signal continues); no action this sprint

**Phase 58.x portfolio (full)** — see prior carryover sections for all open ADs:
- HITLPolicies off-platform channel routing (Slack/email/SMS) — `AD-HITLPolicies-OffPlatformChannelRouting` (Phase 58+ deeper extension)
- HITLPolicies optimistic concurrency / If-Match — `AD-HITLPolicies-OptimisticConcurrency` (CONDITIONAL if Sprint 57.55+ surfaces concurrent edit race)
- HITLPolicies audit_log entry on change — `AD-HITLPolicies-AuditLogOnChange` (CONDITIONAL)
- TenantSettings Identity persistence — `AD-TenantSettings-Identity-Persistence-Phase58` (Sprint 57.50 carryover; full SSO admin schema scope)
- Mockup capture visual diff pipeline — `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` (Phase 58+)

---

## Sprint 57.53 Carryover (2026-05-26 — Checkpointer Test Tenant Isolation Pre-Existing Fail FIX; Sprint 57.12 `§Committed-Row Cleanup Pattern` Lift)

Sprint 57.53 (single-track investigation+fix sprint) ✅ **CLOSED**: 1 carryover AD closed (`AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` Sprint 57.51+57.52 trail). Pytest baseline restored to **1760 PASS + 0 fail** (was 1759 + 1 PRE-EXISTING fail).

### Sprint scope (single track + investigation methodology)

- **Day 1 Task 1.1** — H1-H6 hypothesis elimination investigation (5 evidence steps + verdict): H1 REFUTED in state_mgmt scope + CONFIRMED via Sprint 57.12 cross-scope precedent / H2 PLAUSIBLE secondary / H3 REFUTED (TRIGGER_COUNT=0) / H4 REFUTED (no refactor history) / H5 REFUTED (1/9 codes leaked) / H6 REFUTED (0 .commit() in checkpointer.py)
- **Day 1 Task 1.2** — Option A enriched with Sprint 57.12 precedent (Options B/C/D explicitly rejected per `testing.md` documented anti-patterns)
- **Day 1 Task 1.3** — Implementation:
  - One-shot manual DELETE ISO_A row (WORM trigger toggle pattern; `DELETED_ROWS=1`)
  - NEW `backend/tests/integration/agent_harness/conftest.py` (~120 lines mirroring `tests/integration/api/conftest.py` Sprint 57.12 `§Committed-Row Cleanup Pattern` verbatim at sibling scope)
  - Allowlist `_COMMITTING_STATE_MGMT_TENANT_CODES` (9 codes: CHKPT_TEST + ISO_A + MISSING + MM_SID + MM_TID + RT + SIZE + TT + TEST_TENANT)
  - `_clear_committed_state_mgmt_tenants()` cleanup with WORM trigger toggle (DISABLE → DELETE → ENABLE → COMMIT, single transaction)
  - `@pytest.fixture(autouse=True) _reset_state_mgmt_test_state` before+after yield
  - **0 modifications to existing files** (zero-edit-on-existing scope)

### Day 0 三-prong + Day 1 validation

- 6 GREEN + 1 YELLOW (D-DAY0-3 plan SAVEPOINT reference resolved Day 1.1.4) + 2 NEW NOTABLE (D-DAY0-7 H1 refutation evidence + D-DAY0-8 broader committer catalog) + **1 NEW MAJOR D-DAY0-9** (Sprint 57.12 §Committed-Row Cleanup precedent discovery upgraded Option A from speculative to direct-precedent-applicable; saved ~30-45 min Day 1 work)
- 0 RED; GO with no plan revision
- Day 1 validation 9/9 GREEN (pytest 1760 PASS + 4 skip + 0 fail = +1 net vs Sprint 57.52 baseline; mypy 0/310 source files; 9/9 V2 lints 1.19s; Vitest 607 PASS / 118 test files preserved; Vite build 3.51s clean; LLM SDK leak 0; 0 .ts/.tsx files touched)
- **Parent-assistant-direct execution** (0% code-implementer agent delegation); ~80 min wall-clock total (Day 0 ~25 min + Day 1 ~30 min + Day 2 ~25 min closeout)

### Calibration (Day 2 retro Q4)

- **Class**: `medium-backend` 0.80 — **6th data point ratio 0.83** ✅ in band lower edge (was 5-pt mean 0.52; 6-pt mean **0.57** improvement; last 3 only 2/3 < 0.7 → lower-trigger NOT MET → **KEEP 0.80 baseline** per 3-sprint window rule; Sprint 57.50 retro Q4 prediction "6th data point cleaner signal under tier-2" validated)
- **Sub-class agent_factor**: `mechanical-greenfield` 0.50 — **1st validation NOT GENERATED**. Plan §6 predicted agent-delegated execution at `mechanical-greenfield` 0.50, but reality was parent-assistant-direct → per Sprint 57.45 Path B precedent ("Path B = 0 code change → `agent_factor = 1.0` applied"; extended logic for "0% delegation" generally), `agent_factor = 1.0 (human)` applied. Carryover renamed to `AD-AgentFactor-Tier-3-Validation-Sprint-57.54` continues open.

### 1 AD CLOSED + 4 NEW carryover ADs for Sprint 57.54+

**CLOSED**:
- ✅ `AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` (Sprint 57.51+57.52 trail carryover; root-cause investigated; fix applied; pytest baseline restored to 1760 PASS + 0 fail)

**NEW carryover**:
- **`AD-AgentFactor-Tier-3-Validation-Sprint-57.54`** (renumbered from Sprint-57.53; need agent-delegated sprint at `mechanical-greenfield` 0.50 sub-class for 1st validation data point — estimated scope: any backend or frontend sprint with single-track NEW component-pair where user pre-confirms agent delegation at Day 0)
- **`AD-Plan-Workload-AgentDelegation-Explicit-Field`** (NEW from retro Q3 Lesson 3 — codify sprint plan §6 pre-commit "agent-delegated: yes/no/partial/TBD-Day-1-decision" field BEFORE Day 0 三-prong; default to "TBD" at draft, finalize at Day 0 approval gate; default to "yes" if user defers — protects calibration matrix from accidental no-data-point sprints)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (NEW from retro Q3 Lesson 1; Phase 58.x — extract `_clear_committed_test_tenants` to shared `tests/conftest_helpers.py` module so api + agent_harness + future scopes can import-and-allowlist rather than duplicate the function body)
- **`AD-MediumBackend-AICadence-Recalibration`** (NEW from retro Q4 sub-lesson; Phase 58+ — revisit `medium-backend` 0.80 baseline if next 2-3 human-factor sprints continue to land 0.70-0.85; class baseline may be slightly too high for AI-cadence parent-assistant-direct work)

### Continuing carryover (unchanged this sprint)

- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.49 carryover continues; 3rd data point pending at next medium-frontend sprint)
- `AD-TenantSettings-{HITLPolicies,FeatureFlags,Quotas,RateLimits}-Persistence` Phase 58.x (Sprint 57.48 carryover)
- `AD-TenantSettings-Identity-Persistence-Phase58` (Sprint 57.50 carryover)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` (Phase 58+ deferred)

### Highlights

- 🎉 **Backend pytest baseline restored to ALL-GREEN** after 3-sprint carryover (57.51 → 57.52 → 57.53)
- ⭐ **Sprint 57.12 §Committed-Row Cleanup Pattern lift** = direct precedent application (NOT new invention); ~120-line conftest.py sibling at agent_harness scope; 0 modifications to existing files
- 🎯 **H1-H6 hypothesis elimination methodology** delivered 5 explicit REFUTED + 1 PLAUSIBLE in <30 min Day 1 investigation
- 🟢 **Mockup-fidelity DUAL CLEAN milestone (22/22 PARITY)** PRESERVED through **9 consecutive sprints 57.45-57.53**
- ⚠️ **25-sprint code-implementer agent delegation streak BROKEN** (Sprint 57.40-57.52 chain preserved as historical; Sprint 57.53 parent-assistant-direct due to investigation+small-fix shape)
- 📊 **`medium-backend` 0.80 6th data point under human 1.0 factor** = 1st post-confound clean class-baseline data point (0.83 in band lower edge)

---

## Sprint 57.52 Carryover (2026-05-26 — Triple-AD Audit/Docs Hygiene Bundle Continuation; Tier-3 `mixed-multidomain-bundle` SPLIT ACTIVATED)

Sprint 57.52 (triple-AD audit/docs hygiene bundle continuation) ✅ **CLOSED**: 3 carryover ADs from Sprint 57.50-51 trail closed in single bundled sprint (0 production code change; 5 files +593/-0; 1 git mv rename 88% similarity).

### Sprint scope (3 tracks, sequential per user direction)

- **Track A** — `AD-Day0-Prong2-Oklch-Delta-Grep` ✅ CLOSED (Sprint 57.51 Track C AUDIT-001 §Lesson carryover) → extended `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2` Drift Class table at L357-361 with NEW row 6 **Claimed-but-silent-constraint-delta** (concrete bash grep template `git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' | grep -cE '^\+[^+].*oklch\('` generalizes to AP-N detector counts / Vite bundle size byte delta / pytest+Vitest count deltas)
- **Track B** — `AD-REFACTOR-Numbering-Collision` ✅ CLOSED (Sprint 57.51 Day 0.8 BONUS observation carryover) → `git mv claudedocs/4-changes/refactoring/REFACTOR-001-llm-protocol-chat-with-tools.md → REFACTOR-002-llm-protocol-chat-with-tools.md` (88% similarity; history preserved per `git log --follow`; 0 reference updates needed beyond rename); appended NEW `## Modification History` section at END (light-touch append-new-section approach per D-DAY0-5 pre-convention format)
- **Track C** — `AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern` ✅ CLOSED (Sprint 57.50 D-DAY0-8 carryover) → same Prong 2 Drift Class table NEW row 7 **Stale-docstring-Karpathy-3** (Karpathy §3 cleanup mindset codified — docstrings + MHist + module-level comments are "code" for dead-code rule)

### Day 0 三-prong + Day 1 validation

- 5 GREEN + 1 GREEN+ (D-DAY0-2 Track B simplified to 0 ref updates) + 1 YELLOW (D-DAY0-5 pre-convention file format → append-new-section approach) + 1 BONUS observation (Prong 2 L357-361 vs Prong 3 Schema L407-410 disambiguation)
- 0 RED; GO with no plan revision
- Day 1 validation 9/9 GREEN (9/9 V2 lints + pytest 1759 PASS + 1 PRE-EXISTING fail flagged `test_checkpointer_db::test_tenant_isolation` 0 backend source changes → Sprint 57.53 user-confirmed scope; Vitest 607 preserved; ESLint 0 / tsc 0 / Vite build 3.49s / LLM SDK leak 0)
- 24th consecutive code-implementer agent delegation; ~40-45 min wall-clock total (Day 0 ~15-18 min + Day 1 agent ~25-27 min)

### Calibration (Day 2 retro Q4) — TIER-3 SPLIT ACTIVATED

- **Class**: `audit-cycle/docs/template` 0.40 — **3rd data point** (1st 57.10=1.63 + 2nd 57.51=0.97 + 3rd 57.52=~0.75) — 3-pt mean **1.13 IN BAND middle** — **KEEP per `When to adjust` 3-sprint window rule (3-sprint window evaluation COMPLETE; class calibration mature)**
- **Sub-class agent_factor**: `mixed-multidomain-bundle` 0.65 — **tier-2 2nd validation** post Sprint 57.50 ESCALATION
- Bottom-up ~1.5 hr → class-calibrated ~36 min (mult 0.40) → agent-adjusted ~23 min (× 0.65) → actual ~40-45 min
- Ratio actual/class-committed = **~1.17-1.25** ABOVE band by 0-0.05 (near upper edge — validates class 0.40 cleanly)
- Ratio actual/committed-with-agent-factor = **~1.7-2.0** ABOVE band by 0.5-0.8 = **2nd rollback-trigger > 1.20 data point** (Sprint 57.51=1.49 + 57.52=~1.85)
- **Rollback rule MET** → flat rollback 0.65 → 1.0 REJECTED (over-corrects for Sprint 57.46-style multi-track-mechanical work) → **DECISION: Option B tier-3 SPLIT ACTIVATED** effective Sprint 57.53+:
  - `mixed-multidomain-bundle-mechanical` **0.65** UNCHANGED (multi-track WITH mechanical pattern reuse; e.g. Sprint 57.46 backend ORM + Pydantic + tests bundle)
  - `mixed-multidomain-bundle-non-mechanical` **1.0** NEW (pure audit/docs/rules multi-track; NO mechanical pattern reuse; Sprint 57.51 + 57.52 retroactively validate cleanly at 1.0)
- Other Option B sub-classes UNCHANGED (`mechanical-pattern-reuse-heavy` 0.30 / `mechanical-greenfield` 0.50 / `partial` 0.75 / `human` 1.0)
- **Retroactive validation under tier-3 1.0**: Sprint 57.51 ratio at 1.0 = ~0.97 ✅ IN BAND middle (was 1.49 at 0.65); Sprint 57.52 ratio at 1.0 = ~1.1-1.25 ✅ IN BAND upper edge (was ~1.85 at 0.65)

### 2 NEW carryover ADs (Sprint 57.53+ pickup)

1. **`AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation`** (**Sprint 57.53 user-confirmed scope**) — Sprint 57.51 carryover continues; pre-existing fail on main `6327e597`; investigate root cause + classify fix (test issue vs code bug) + optional fix; ~1-2 hr scope; class TBD pending root cause (likely `medium-backend` 0.80 OR `frontend-page-bug-fix` 0.45)
2. **`AD-AgentFactor-Tier-3-Validation-Sprint-57.53`** (NEW from Sprint 57.52 retro Q4 tier-3 ACTIVATION) — 1st validation under new sub-class table; Sprint 57.53 maps to which sub-class TBD pending root cause investigation; class-dependent

### CLOSED via tier-3 ACTIVATION

- `AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52` (was conditional NEW carryover from Sprint 57.51; consumed via tier-3 SPLIT ACTIVATION)

### Continuing carryover (unchanged Sprint 57.52)

- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.49 carryover; 3rd data point pending at next medium-frontend sprint)
- `AD-TenantSettings-{HITLPolicies,FeatureFlags,Quotas,RateLimits}-Persistence` Phase 58.x (Sprint 57.48 carryover)
- `AD-TenantSettings-Identity-Persistence-Phase58` (Sprint 57.50 carryover)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` Phase 58+ deferred

### Top 3 next-sprint candidates (post Sprint 57.52)

1. **🥇 AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation** (~1-2 hr) — **user-confirmed Sprint 57.53 scope**; bug-fix sprint; production stability matters; surfaces root cause for "how did silent failure land in main"
2. **🥈 Phase 58.x TenantSettings persistence work** (any of 4 sub-tracks) — meaningful production extension; class `medium-backend` 0.80
3. **🥉 Pause / Phase 57.x SaaS feature work resumption** — accumulated audit/docs hygiene work cleared (5 ADs closed Sprint 57.48-52 trail); Phase 57+ feature pipeline could resume

---

## 🆕 Sprint 57.51 Carryover (2026-05-26 — Triple-AD Audit/Docs Hygiene Bundle; Tier-2 `mixed-multidomain-bundle` 0.65 1st Validation)

Sprint 57.51 (triple-AD audit/docs hygiene bundle) ✅ **CLOSED**: 3 carryover ADs from Sprint 57.48-50 trail closed in single bundled sprint (0 production code change; 7 `.md` files +1022/-3).

### Sprint scope (3 tracks, sequential per user direction)

- **Track A** — `AD-Lint-Detector-Code-Aware-Masking-Rule` ✅ CLOSED (Sprint 57.48 D-DAY0-6 carryover) → NEW `docs/rules-on-demand/lint-detector-authoring.md` ~145 lines (Why / 3-step authoring pattern / AP-4 placeholder JSX attr + TS key mask actual code + hypothetical AP-N case / 4 anti-patterns / cross-refs); `.claude/rules/README.md` on-demand index 11→12 entries.
- **Track B** — `AD-Plan-Risk-ORM-File-Path-Reference-Style` #82 ✅ CLOSED (Sprint 57.50 D-DAY0-2 carryover) → NEW Risk Class D in `.claude/rules/sprint-workflow.md §Common Risk Classes` mirroring A/B/C 4-field template (Symptom/Source/Workaround/Long-term fix); cites `09-db-schema-design.md §Group 1 Identity & Tenancy` → identity.py.
- **Track C** — `AD-Sprint-57.49-HEX_OKLCH-Silent-Drift-Audit` ✅ CLOSED (PR #200 hotfix carryover) → NEW `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md` ~145 lines with **Verdict A — intended verbatim port** (Sprint 57.44 MembersTab avatar gradient `linear-gradient(135deg, oklch(0.65 0.15 ${c % 360}), oklch(0.5 0.16 ${(c + 60) % 360}))` reused in Sprint 57.49 NEW TenantMembersDrawer.tsx for cross-component visual consistency; fix-forward at PR #200 hotfix `74ed8a2f` correct; no fix-back needed).

### Day 0 三-prong + Day 1 validation

- 8 GREEN + 2 GREEN+ (D-DAY0-5 NET +1 oklch confirmed + D-DAY0-6 TenantMembersDrawer source identified) + 1 BONUS observation (REFACTOR-001 numbering collision)
- 0 RED / 0 YELLOW; GO with no plan revision
- Day 1 validation 8/8 GREEN (9/9 V2 lints + pytest 1759 PASS + 1 PRE-EXISTING fail flagged `test_checkpointer_db::test_tenant_isolation` 0 backend source changes → NEW carryover AD; Vitest 607 preserved; ESLint 0 / tsc 0 / Vite build 3.40s / LLM SDK leak 0)
- 23rd consecutive code-implementer agent delegation; ~70 min wall-clock total (Day 0 ~20 min + Day 1 ~50 min)

### Calibration (Day 2 retro Q4)

- **Class**: `audit-cycle/docs/template` 0.40 (**2nd data point**; 1st was Sprint 57.10 ratio 1.63) — 2-pt mean **1.30** ABOVE band by 0.10 (lower band edge); KEEP per `When to adjust` 3-sprint window rule
- **Sub-class agent_factor**: `mixed-multidomain-bundle` 0.65 (**tier-2 1st validation** post Sprint 57.50 Option B tier-2 ESCALATION)
- Bottom-up ~3.0 hr → class-calibrated ~1.2 hr (mult 0.40) → agent-adjusted ~0.78 hr (× 0.65) → actual ~70 min
- Ratio actual/class-committed = **0.97** ✅ in band middle (validates class 0.40 cleanly)
- Ratio actual/committed-with-agent-factor = **~1.49** ABOVE band by 0.29 = **1st rollback-trigger > 1.20 data point** under `mixed-multidomain-bundle` 0.65
- **KEEP `mixed-multidomain-bundle` 0.65 single-data-point caution**; flag Sprint 57.52+ for 2nd validation; if also > 1.20 → roll back 0.65 → 1.0 (drop modifier; multi-domain non-mechanical = `human` cadence) OR tier-3 sub-class split `-mechanical` (keep 0.65) vs `-non-mechanical` (propose 1.0)

### NEW carryover ADs (Sprint 57.52+ pickup)

1. **`AD-Day0-Prong2-Oklch-Delta-Grep`** (NEW Track C lesson) — Codify oklch-delta grep step into `sprint-workflow.md §Step 2.5 Prong 2` for future agent-delegated frontend migration sprints. Generalizes beyond oklch to any baseline-constrained metric (HEX_OKLCH / AP-N detector counts / bundle size / test-count thresholds). ~30 min `audit-cycle/docs/template` 0.40 class. Recommended as Sprint 57.52 scope.
2. **`AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail`** (NEW Day 1 surface) — `test_checkpointer_db::test_tenant_isolation` fails on main `8431646f` (Sprint 57.50 baseline); 0 backend source changes in Sprint 57.51 → pre-existing failure. Suggests Sprint 57.50 closeout missed full backend pytest sweep OR paths-filter masked. ~1-2 hr investigation + fix. Class TBD (medium-backend OR frontend-page-bug-fix depending on root cause).
3. **`AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52`** (NEW retro Q4 carryover) — 2nd validation data point needed under `mixed-multidomain-bundle` 0.65; conditional structural action if also > 1.20 (rollback to 1.0 OR tier-3 split).
4. **`AD-REFACTOR-Numbering-Collision`** (NEW Sprint 57.51 Day 0.8 BONUS observation) — 2 files share `REFACTOR-001-*.md` prefix. Rename one to REFACTOR-002 for traceability. ~10 min chore. Could be bundled with #1 as 2-track audit/docs sprint.

### Continuing carryover (unchanged Sprint 57.51)

- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.49 carryover; 3rd data point pending; not addressed this sprint since `audit-cycle/docs/template` not medium-frontend)
- `AD-TenantSettings-{HITLPolicies,FeatureFlags,Quotas,RateLimits}-Persistence` Phase 58.x (Sprint 57.48 carryover)
- `AD-TenantSettings-Identity-Persistence-Phase58` (Sprint 57.50 carryover — full SSO admin schema)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` Phase 58+ deferred
- `AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern` (Sprint 57.50 D-DAY0-8 lesson — codify docstring claims as Karpathy §3 dead-code class for Prong 2 content verify; ~30 min `audit-cycle/docs/template`; could bundle with #1 + #4)

### Top 3 next-sprint candidates (post Sprint 57.51)

1. **🥇 Audit/docs hygiene bundle continuation** (~1-1.5 hr) — Bundle #1 + #4 + AD-Stale-Docstring-Karpathy-3 into a Sprint 57.52 triple-track `audit-cycle/docs/template` 0.40 sprint. Naturally tests 2nd validation under `mixed-multidomain-bundle` 0.65. Closes 3 small carryovers cleanly.
2. **🥈 Investigate AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail** (~1-2 hr) — Bug-fix sprint; production stability matters; class TBD pending root cause. Would surface "how did silent failure land in main" + close the lint hygiene gap.
3. **🥉 Pause** — Sprint 57.51 just closed 3 ADs from Sprint 57.48-50 trail; carryover queue reduced; tier-2 1st validation data point captured; let user direct Phase 58.x persistence work OR Phase 57.x SaaS frontend feature work resumption.

---

## 🆕 Sprint 57.50 Carryover (2026-05-26 — TenantSettings Identity Fixture Cleanup; Option B Tier-2 ESCALATION)

Sprint 57.50 (`AD-TenantSettings-IdentityFixture-Cleanup`) ✅ **CLOSED**: single-track 1-hr hygiene migrates `IDENTITY_FIXTURE` 4 fields to real backend via Option A fixture-projection (mirror Sprint 57.48 Track D RateLimits exactly).

### Sprint scope

- **Backend**: NEW `GET /admin/tenants/{tenant_id}/identity` + `TenantIdentityResponse` Pydantic (4 fields: provider/scim_enabled/allowed_domains/mfa_required) + `DEFAULT_IDENTITY` constant + 7 NEW pytest tests (217→224); auth `require_admin_platform_role` (mirror sibling HITL/FF/Quotas/RateLimits)
- **Frontend**: NEW `fetchTenantIdentity` single-record service func + NEW `useTenantIdentity` TanStack Query hook + GeneralTab.tsx Identity Card refactor (4 Badge rows via hook with shape adapters bool→"enabled"/"disabled" / list→", ".join / bool→"required"/"optional") + softened BackendGapBanner copy per D-DAY0-9 + `_fixtures.ts` DANGER_OPS only (~50 lines) + 9 NEW Vitest tests (598→607) across 4 test files
- **Day 0 三-prong**: 9 drift findings (7 GREEN + 1 GREEN+ D-DAY0-8 SEATS_FIXTURE already removed + 1 YELLOW D-DAY0-9 BackendGapBanner copy pre-flag); ROI ~5-7×
- **Sequential agent delegation**: Backend agent ~4.1 min + Frontend agent ~6.7 min = ~11 min total agent wall-clock; 22nd consecutive code-implementer delegation
- **Validation chain**: pytest +7 / mypy --strict 0 / black + isort + flake8 clean / Vitest +9 / ESLint 0 / tsc 0 / Vite build 3.45s / 9/9 V2 lints GREEN / LLM SDK leak 0

### 🎯 Structural calibration event (Sprint 57.50 retro Q4)

**Ratio actual/committed-with-agent-factor ~0.58 BELOW [0.85, 1.20] band by 0.27 = 2nd consecutive < 0.7 under `mechanical-single-domain` 0.45 sub-class** (Sprint 57.49 = 0.14 + Sprint 57.50 = 0.58; mean 0.36; **4× variance bimodal NOT Gaussian**).

Rollback rule "2 sprints < 0.7 → tighten" MET — flat tighten 0.45 → 0.35 REJECTED (doesn't address variance root cause). **Decision: ACTIVATE Option B tier-2 refinement** (parallel Sprint 57.38 `-simple/-with-extras` + Sprint 57.48 Option B precedent).

**Active tier-2 sub-class table** (effective Sprint 57.51+):

| Tier-2 sub-class | `agent_factor` | Activation criterion | Evidence base |
|------------------|---------------|----------------------|---------------|
| `mechanical-pattern-reuse-heavy` | **0.30** | ≥ 4 mechanical repetitions of same template in 1 sprint | Sprint 57.49 retroactive (5-tab+1-drawer; ratio 0.21 under 0.30 vs 0.14 under 0.45) |
| `mechanical-greenfield` | **0.50** | Single NEW component-pair; < 4 mechanical repetitions | Sprint 57.50 retroactive (1-endpoint+1-hook+1-refactor; ratio 0.54 under 0.50 vs 0.58 under 0.45) |
| `mixed-multidomain-bundle` | 0.65 | 3+ independent tracks with context-switching | Sprint 57.46 (UNCHANGED from Sprint 57.48 Option B) |
| `partial` | 0.75 | 20-79% via agent (linear interpolation) | — |
| `human` | 1.0 | < 20% via agent | — |

Tier-2 split reduces 4.1× → 2.6× variance spread; both classes still below band globally (bottom-up estimates also generous). See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for full formula + rollback rule reset + tracking discipline.

### `medium-backend` 0.80 5th data point

- 5-pt: 55.5=1.14 / 55.6=0.92 / 57.47=0.16 / 57.48=0.11 / 57.50=0.27
- 5-pt mean **0.52** (last-3 mean 0.18) — last 3 all < 0.7 BUT all agent-delegated
- **KEEP 0.80 per confound-resolved-by-sub-class-split discipline**; 6th data point Sprint 57.51+ under tier-2 will be cleaner signal

### 3 ADs closed this sprint

- ✅ #73 **`AD-AgentFactor-Sub-Class-Validation-Sprint-57.50`** — via 2nd validation ratio 0.58 + ROLLBACK RULE MET
- ✅ #74 **`AD-AgentFactor-Tier-2-Refinement-Proposal`** — via Q4 ACTIVATION (mechanical-pattern-reuse-heavy 0.30 + mechanical-greenfield 0.50)
- ✅ **`AD-TenantSettings-IdentityFixture-Cleanup`** (Sprint 57.49 carryover) — Identity Card now consumes real backend

### 🆕 4 NEW carryover ADs (Sprint 57.51+ candidates)

80. 🆕 **`AD-AgentFactor-Tier-2-Sub-Class-Validation-Sprint-57.51`** — 1st validation needed under tier-2 sub-class table. Sprint 57.51 will naturally generate either `pattern-reuse-heavy` 0.30 OR `greenfield` 0.50 data point depending on work shape.

81. 🆕 **`AD-TenantSettings-Identity-Persistence-Phase58`** Phase 58.x — full SSO admin schema: dedicated `tenant_identity` table + admin PATCH endpoint + audit chain WORM + tenant_overrides → real table migration. Mirrors `AD-TenantSettings-RateLimits-Persistence` (#79) pattern.

82. 🆕 **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** — Plan §8 Risks ORM file path references should use 09-db-schema-design.md Group references (e.g. "identity.py per Group 1 Identity & Tenancy") not table_name.py speculation. D-DAY0-2 lesson: Tenant ORM lives in `identity.py` not `tenant.py`. Codify in plan template + sprint-workflow.md §Step 1 risk class catalog. ~30 min `chore(rules)` micro-sprint.

83. 🆕 **`AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern`** — Treat docstring claims as "code" for Day 0 三-prong Prong 2 content verify. D-DAY0-8 lesson: Sprint 57.49 _fixtures.ts docstring referenced SEATS_FIXTURE which Sprint 57.49 already removed; stale comment caught Day 0. Generalize: docstring claims grep-verified against repo reality, not just at MHist entry creation time. ~15-30 min `chore(rules)` codification.

### Carryover from prior sprints (continuing)

- **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (Sprint 57.48 carryover) — `.claude/rules/` codification still pending; recommended Sprint 57.51+ scope per user direction. ~1-2 hr `audit-cycle / docs / template` 0.40 class.
- **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49 carryover) — 3rd data point pending under tier-2 sub-class confound-cleared table; happens organically at next medium-frontend sprint.
- **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (Phase 58+ deferred) — carryover continues.
- **`AD-TenantSettings-RateLimits-Persistence`** (Phase 58.x deferred) — carryover continues; pair with new #81 `AD-TenantSettings-Identity-Persistence-Phase58`.

### Top 3 next-sprint candidates (post Sprint 57.50)

1. 🥇 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** ~1-2 hr (`audit-cycle / docs / template` 0.40 class; codifies Sprint 57.48 D-DAY0-6 lesson into `.claude/rules/`; original Sprint 57.50 plan candidate (b) for follow-up)
2. **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** ~30 min (#82 micro-sprint; quick `chore(rules)` codification)
3. **Pause** — Natural break point after 6 consecutive sprints (57.45-50) cleanly closed + DUAL CLEAN milestone preserved + tier-2 ESCALATION just landed (let 1-2 sprints validate tier-2 before more carryover work)

---

## 🆕 Sprint 57.43-57.49 Carryover Batch (2026-05-26 — Phase-2 Epic DUAL CLEAN + Phase 58+ Backend Schema Extension + Frontend Migration Wave)

4-sprint window closes **14 ADs total** + introduces **7 new carryover ADs**. Per-sprint detail single-source = `memory/project_phase57_4{3,4,5,6,7,8,9}_*.md` subfile + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/retrospective.md`.

### Milestones reached

- **Sprint 57.43** (PR `12af6060` later `34c5ad1c` merge): `/admin-tenants` Tenants table full mockup-fidelity rebuild closes drift audit 2026-05-25 #1 priority CATASTROPHIC (4th of 5 original). 5 NEW components + _fixtures.ts 8 TENANTS verbatim + 6 orphan delete Karpathy §3 + 33 NEW Vitest tests +312-560% over target + 24-route sweep cleanest of Phase-2 epic. `frontend-mockup-strict-rebuild` 0.60 9th data point + **1st validation under newly ACTIVATED `agent_factor = 0.55`** ratio ~0.41 BELOW band by 0.44 = 1st rollback-trigger data point → KEEP 0.55 single-data-point caution.
- **Sprint 57.44** (PR squash merge): `/tenant-settings` 6-tab full rebuild closes Phase-2 epic FULL CLEAN (5th of 5 original CATASTROPHIC). 7 NEW components + 1 REWRITE + _fixtures.ts verbatim port + 4 orphan delete + 50 NEW Vitest tests +287% over +12 target. `frontend-mockup-strict-rebuild` 0.60 10th data point ratio ~0.20 = **2nd rollback-trigger data point → MANDATORY tighten `agent_factor` 0.55 → 0.45 effective Sprint 57.45+**. 🎉 **Phase-2 epic FULL CLEAN milestone (21 PARITY + 1 NEAR-PARITY + 0 CATASTROPHIC)**.
- **Sprint 57.45** (PR #195): 🎉 **Phase-2 Epic + NEAR-PARITY DUAL CLEAN milestone (22/22 PARITY)** — `/chat-v2` Inspector tab NEAR-PARITY closed via Path B audit overrule (Day 0 Prong 2 grep proved audit row 9 was Sprint 57.22 transcription error; canonical mockup `page-chat.jsx:378-381` `Turn/Trace/Memory/Tree` matched production exactly). 0 code change docs-only closure. `frontend-refactor-mechanical 0.80` 3rd data point + `agent_factor` 1st validation NOT generated (Path B 0 code change → `agent-delegated: NO` → `agent_factor = 1.0`).
- **Sprint 57.46** (PR #196 `034846f3`): 3-AD multi-domain bundle — AuditDocSync rule codified + Tenant ORM +5 cols Alembic 0018 + 12 NEW pytest tests + mockup capture D-DAY0-5 already-implemented Option B revelation -1 hr scope. NEW class `mixed-multidomain-bundle` 0.65 1-data-point baseline opens. `agent_factor = 0.45` 1st validation ratio ~1.60 ABOVE band by 0.40 → **ROLLBACK to 0.65** effective Sprint 57.47+ per single-data-point caution.
- **Sprint 57.47** (PR #197 `12f97635`): Phase 58+ Backend Schema Extension — 🔴 BLOCKING `AD-AdminTenants-Backend-Schema-Extension` closed (TenantListItem 7→12 fields + region filter + 12 NEW pytest tests) + TenantSettings 6-tab Day 0.8b audit + MEMBERS cheapest tab impl (8 NEW pytest tests incl. CRITICAL multi-tenant isolation). `agent_factor = 0.65` 1st validation ratio ~0.27 = 1st < 0.7 → KEEP single-data-point caution.
- **Sprint 57.48** (PR #198 `c451f584`): **5-track wave** (largest single-sprint AD closure of Phase 57+: **5 ADs**) — HITLPolicies (DBHITLPolicyStore projection) + FeatureFlags (JSONB tenant_overrides) + Quotas (PlanQuota projection) + RateLimits (Option A fixture-projection) + AP-4 lint detector false-positive fix → **9/9 V2 lints GREEN restored** (was 8/9 since Sprint 57.46). 29 NEW pytest tests +132% over target. `agent_factor = 0.65` 2nd validation ratio ~0.17 = 2nd consec < 0.7 → **ROLLBACK RULE MET → Option B sub-class split ESCALATED ACTIVATED** (parallel Sprint 57.38 `-simple/-with-extras` precedent).
- **Sprint 57.49** (PR #199 `33e9f2aa`): Dual-track frontend migration wave — TenantSettings 5-tab fixture→hook via 5 NEW TanStack Query hooks + 5 NEW service functions + per-tab adapter projection D-DAY0-1 pattern + AdminTenants TenantMembersDrawer NEW with slide-over. 37 NEW Vitest tests +264% over target. **24× pattern-reuse speedup observed (highest of 21 consecutive code-implementer delegations)**. NEW sub-class `mechanical-single-domain` 0.45 1st validation ratio ~0.14 → KEEP single-data-point caution.

### Structural calibration event (Sprint 57.48 retro Q4 — escalation)

`agent_factor` evolved from single coefficient to sub-class table via Option B structural split. Single-coefficient pendulum 0.55 → 0.45 → 0.65 → 0.45 inadequate to capture Day 1 work shape variance (Sprint 57.46 multi-track 2.1× speedup vs Sprint 57.40-44 single-domain 5× speedup).

**Active sub-class table** (effective Sprint 57.49+):

| Sub-class | `agent_factor` | Activation criterion | Evidence base |
|-----------|---------------|----------------------|---------------|
| `mechanical-single-domain` | **0.45** | High pattern-reuse OR mechanical port; single-domain backend/frontend | Sprint 57.40-44 + 57.47 + 57.48 + 57.49 |
| `mixed-multidomain-bundle` | **0.65** | 3+ independent tracks with context-switching | Sprint 57.46 |
| `partial` | **0.75** | 20-79% via agent (linear interpolation) | — |
| `human` | **1.0** | < 20% via agent | — |

See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for full formula + rollback rule + tracking discipline. **NEW pattern-reuse acceleration scaling observation** (Sprint 57.49 retro Q4): 5× (single-domain) → 7× (single-tab) → 11× (4-endpoint) → **24× (5-tab+1-drawer; highest of 21 consecutive delegations)** — speedup scales with mechanical repetition count.

### 🆕 7 NEW carryover ADs (Sprint 57.50+ candidates; ordered by ROI / actionability)

73. 🆕 **`AD-AgentFactor-Sub-Class-Validation-Sprint-57.50`** (Sprint 57.49 NEW) — 2nd validation under `mechanical-single-domain` 0.45 needed. Current: 1st = Sprint 57.49 ratio actual/committed-with-agent-factor **~0.14 BELOW band by ~0.71** → KEEP single-data-point caution. If Sprint 57.50 also < 0.7 → escalate to tier-2 refinement (see #74). Naturally generated by any single-domain agent-delegated sprint scope.

74. 🆕 **`AD-AgentFactor-Tier-2-Refinement-Proposal`** (Sprint 57.49 NEW) — If Sprint 57.50 2nd `mechanical-single-domain` data point also < 0.7 → propose tier-2 refinement: split `mechanical-pattern-reuse-heavy` **0.30** (≥4 mechanical repetitions in 1 sprint; matches Sprint 57.48/49 mean ~0.155) vs `mechanical-greenfield` **0.50** (single new component/endpoint; matches Sprint 57.47 ratio ~0.27 closer to band). Pending Sprint 57.50 evidence.

75. 🆕 **`AD-TenantSettings-IdentityFixture-Cleanup`** (Sprint 57.49 NEW) **~1 hr** — `IDENTITY_FIXTURE` in `tenantSettingsService.ts` retained per Sprint 57.49 §_fixtures.ts cleanup; not yet migrated to real backend (5-tab migration shipped + DANGER_OPS retained too). Completes the fixture purge. Class `mechanical-single-domain` 0.45 candidate (single-file migration; natural 2nd validation data point for #73).

76. 🆕 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (Sprint 57.48 NEW) **~1-2 hr** — Codify D-DAY0-6 lesson into `.claude/rules/`: lint detectors using regex pattern matching must apply code-aware masking (HTML/JSX attribute names like `placeholder=` / TS keys / string literals) to avoid false-positives. Root cause for AP-4 detector breaking 9/9 V2 lints in Sprint 57.46 → Sprint 57.48 Track E false-positive fix. Class `audit-cycle / docs / template` 0.40 candidate.

77. 🆕 **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49 carryover) — 3rd data point needed for class `medium-frontend` 0.65. Current: 1st = Sprint 57.13 ratio 0.95-1.0 in band; 2nd = Sprint 57.49 ratio actual/class-committed 0.064 (confound resolved by sub-class split; under agent_factor `mechanical-single-domain` 0.45 = ratio ~0.14). Per `When to adjust` 3-sprint window rule → KEEP class baseline pending 3rd data point. Naturally generated by next medium-frontend sprint.

78. 🆕 **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (Sprint 57.46 carryover) DEFERRED Phase 58+ **~5-8 hr** — `mockup-sweep.mjs` (Option B Python http.server + Playwright 1440×900) already implements basic capture per Sprint 57.46 D-DAY0-5 revelation; missing: per-page parity scoring + drift alerting + CI integration.

79. 🆕 **`AD-TenantSettings-RateLimits-Persistence`** (Sprint 57.48 carryover) DEFERRED Phase 58.x — Sprint 57.48 Track D shipped Option A fixture-projection from `tenants.meta_data` JSONB; full persistence model (dedicated `tenant_rate_limits` table + admin PATCH endpoint + audit chain) deferred to Phase 58.x.

### Phase progress (post Sprint 57.49)

- V2 22/22 ✅ (unchanged)
- SaaS Stage 1 3/3 ✅ (unchanged)
- **Phase 57+ DUAL CLEAN 22/22 PARITY ✅ preserved** through Sprint 57.45-57.49 (5 consecutive sprints maintain milestone)
- **Phase 58+ Backend Schema Extension COMPLETE** for tenant-settings 6-tab + admin-tenants LIST + members (Sprint 57.46-48)
- **Phase 58+ Frontend Real-Data Migration COMPLETE** for /tenant-settings + /admin-tenants Members (Sprint 57.49)

### Top 3 next-sprint candidates (post Sprint 57.49)

1. 🥇 **`AD-TenantSettings-IdentityFixture-Cleanup`** (#75) **~1 hr** — Class `mechanical-single-domain` 0.45; naturally generates #73 (2nd validation data point). Cleanest hygiene close.
2. **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (#76) **~1-2 hr** — Class `audit-cycle / docs / template` 0.40; codifies repeatable lesson into `.claude/rules/`.
3. **Pause** — Natural break point after 5 consecutive sprints (57.45-57.49) cleanly closed + 14 ADs total + DUAL CLEAN milestone preserved.

---

## 🆕 Sprint 57.42 Carryover (2026-05-25 — /memory Memory Layers Matrix Full Mockup-Fidelity Rebuild)

Sprint 57.42 (`AD-Memory-Layers-Matrix-Rebuild`) ✅ **CLOSED**: single-domain rebuild closes drift audit 2026-05-25 #2 priority `/memory` 🔴 CATASTROPHIC verdict (post Sprint 57.41 it was elevated to #2 priority; with Sprint 57.42 close it is fully RESOLVED).

- **6 NEW components** (under `frontend/src/features/memory/components/`): MemoryPageHeader (~85 lines; `.page-head` + 3 actions + cond time-travel Badge) / TimeTravelScrubber (~155; 24h interactive playback Card with slider+op markers+marks+cursor display) / MemoryMatrix (~175; 5×3 grid with cursor-aware visibility filter + hover bg + AP-2 banner) / RecentMemoryOpsCard (~105; 6-col fixture table + AP-2 banner) / GdprErasureCard (~70; subject+select+danger Button + AP-2 banner) / MemoryView (~85; container with useState cursor/playing + useEffect setInterval cleanup)
- **`_fixtures.ts` verbatim port** (~195 lines): SCOPES / TIME_SCALES / MEMORY_ENTRIES / TIME_TRAVEL_MARKS / MEMORY_OPS_TIMELINE / RECENT_MEMORY_OPS / TOTAL_ENTRIES
- **Outer 2-tab DROP per §1.4 Option B** — **1st DROP precedent** of Phase-2 epic (Recent + By-Scope BOTH subsumed by mockup unified view, unlike Sprint 57.40 `/audit-log` / Sprint 57.41 `/timeline` distinct production-only concepts preserved)
- **Backward-compat redirects**: `/memory/recent` + `/memory/by-scope` + `*` → `<Navigate to="/memory" replace />` inside `pages/memory/index.tsx`
- **11 orphan deletes per Karpathy §3** — **largest single-wave of Phase-2 epic** (3 vintage components MemoryRecentList/MemoryByScopeBrowser/MemoryScopeBadge + 3 vintage hooks useMemoryByScope/useMemoryByTime/useMemoryRecent + 4 Vitest specs (24 tests) + 1 e2e memory-page.spec.ts)
- **`mockup-ui.tsx` `ButtonVariant` 1-line widen** to add `"warning" | "danger"` (D-DAY1-1; CSS+styles-mockup.css already supported; same pattern as Sprint 57.41 Badge tones widening)
- **+12 NEW Vitest tests** (6 NEW spec files; 474 → **486**; +150-240% over +5-8 target; within Sprint 57.40 +15 / 57.41 +9 cohort range)
- **route-sweep envelope mock NO-OP decision** (D-DAY2-2) — rebuild fixture-only; `AD-RouteSweep-Envelope-Mock-Convention` stays at 2 applications
- **HEX_OKLCH_BASELINE 46 unchanged** (estimated +0-4 didn't materialize — 3rd consecutive +0 actual; verbatim-CSS protocol +0-4 envelope consistently over-cautious)
- **Drift audit report `/memory` verdict 🔴 → ✅ PARITY**; summary 18→19 PARITY / 3→2 CATASTROPHIC
- **3-way evidence pair**: BEFORE 71.4 KB / AFTER 173.9 KB / MOCKUP 189.4 KB → **AFTER = 92% of MOCKUP** (structural PARITY confirmed)
- **24-route sweep cleanest of Phase-2 epic**: 20 IDENTICAL + 4 CHANGED (1 INTENDED `/memory` +144% + 3 sub-300-byte noise auth-callback -23 / chat-v2 -19 / overview -38) + 0 unintended regressions (lowest noise + lowest regression count of class history)
- **Class `frontend-mockup-strict-rebuild` 0.60 8th data point ratio ~0.33** — BELOW band by 0.52; 8-pt mean 0.71 lower band edge; **last 3 = 3 of 3 < 0.7 → `When to adjust` lower-trigger MET ✅** → propose Sprint 57.43 baseline lift 0.60 → 0.40-0.45
- ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up `chore/agent-delegation-factor-activate` branch). 5 cross-class data points (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 + 57.42 0.33) + 4 consecutive `mockup-strict-rebuild` < 0.7 = activation criteria FULLY MET. See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for formula + rollback rule + tracking discipline. First validation: Sprint 57.43 retro Q2.

### Phase-2 epic progress (post Sprint 57.42)

- Pre-Sprint 57.42: 18 PARITY + 1 NEAR-PARITY + 3 🔴 CATASTROPHIC
- **Post Sprint 57.42**: **19 PARITY + 1 NEAR-PARITY + 2 🔴 CATASTROPHIC** remaining (`/admin-tenants` + `/tenant-settings`)

### 🆕 7 NEW carryover ADs (Sprint 57.43+ candidates; ordered by ROI / priority)

66. 🆕 **`AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint`** — Backend `/api/v1/memory/matrix?scope=*&time_scale=*&cursor=*` endpoint for real cursor-aware time-travel data. Sprint 57.42 fixture + client-side filter simulation. Phase 58+.
67. 🆕 **`AD-Memory-Ops-Timeline-Backend-Endpoint`** — Backend `/api/v1/memory/ops/recent?limit=100` endpoint for RecentMemoryOpsCard. Sprint 57.42 fixture-only. Phase 58+.
68. 🆕 **`AD-Memory-GDPR-Erasure-Backend-Endpoint`** — Backend `/api/v1/memory/erasure` POST endpoint for GdprErasureCard form (audit chain WORM record). Sprint 57.42 form button non-functional (window.alert stub). Phase 58+.
69. 🆕 **`AD-Memory-Vintage-Hooks-Cleanup`** — `memoryService.ts` preserved Day 1 but has 0 consumers post-rebuild. Phase 58+ either wire to RecentMemoryOpsCard (when ops endpoint ships) OR fully orphan delete.
70. 🆕 **`AD-Memory-Old-URL-Redirect-Phase58-Retire`** — Sprint 57.42 keeps `/memory/recent` + `/memory/by-scope` → `/memory` redirects for backward compat. Phase 58+ analytics-based retire once bookmark traffic decays.
71. 🆕 **`AD-Memory-New-Entry-Modal-Phase58`** + **`AD-Memory-Export-Action-Phase58`** — Mockup `.page-head` "New entry" and "Export" buttons are Sprint 57.42 AP-2 stubs. Phase 58+ wires write modal + CSV/JSON export endpoint.
72. 🆕 **`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift`** — **Lower-trigger MET** (3 consecutive < 0.7: 57.40 0.36 + 57.41 0.18 + 57.42 0.33). Propose Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45. Validate next 2-3 sprints.

### Carryover from Sprint 57.41 (still open as of Sprint 57.42 closeout)

- ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up; 5 cross-class data points + 4 consecutive mockup-strict-rebuild < 0.7 = activation FULLY MET). See top of file `Updated` field + `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`.
- `AD-Verification-Out-Of-Scope-Components-Phase2-C-Mop-Up` — 2 residue sites in VerificationPanel.tsx (chat-v2) + CorrectionTraceView.tsx (/timeline) — still out-of-scope
- `AD-Verification-Filter-Form-Phase58-Migrate` / `AD-Verification-Backend-Claim-Evidence-Extension` / `AD-Verification-Failure-Kinds-+-Flaky-Checks-Aggregation-Endpoints` — Sprint 57.41 Phase 58+ carryover continues

### Top 3 next-sprint candidates (post Sprint 57.42)

1. 🥇 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` ~12-15 hr (4th CATASTROPHIC; backend GET list endpoint already wired; pure frontend work)
2. **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` ~15-20 hr (5th and LAST CATASTROPHIC; largest scope; mostly form work)
3. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename ~30 min (NEAR-PARITY quick win)

---

## 🆕 Sprint 57.41 Carryover (2026-05-25 — /verification recent view Full Mockup-Fidelity Rebuild)

Sprint 57.41 (`AD-Verification-Catastrophic-Rebuild`) ✅ **CLOSED**: single-domain rebuild closes drift audit 2026-05-25 #2 priority `/verification` 🔴 CATASTROPHIC verdict.

- **6 NEW components** (under `frontend/src/features/verification/components/`): VerificationPageHeader (rename Sprint 57.40 ApprovalsPageHeader) / VerificationStatsStrip (rename + Pass rate compute swap) / VerificationRunsTable (NEW 6-col with claim+evidence dual-line + adaptItem mapping) / FailureKindsCard (NEW 5-row bar-track AP-2) / FlakyChecksCard (NEW 3-row rate Badge AP-2) / VerificationView (NEW container)
- **VerificationList.tsx orphan-deleted 299 lines** per Karpathy §3 (filter form retired; carryover `AD-Verification-Filter-Form-Phase58-Migrate`)
- **route swap**: `pages/verification/index.tsx` `recent` Route element swapped; outer 2-tab + `/timeline` CorrectionTraceView preserved
- **+9 NEW Vitest specs** (5 files; 489→498; +112-225% over +5-8 target)
- **route-sweep `/verification/recent` envelope mock**: 2nd application of `AD-RouteSweep-Envelope-Mock-Convention`
- **HEX_OKLCH_BASELINE 46 unchanged** (estimated +2-4 bump didn't materialize — verbatim-CSS protocol correct; components use `var(--*)` refs)
- **e2e adapt**: 3 obsolete filter-form tests deleted + 2 NEW mockup-shape view tests added (D-DAY0-3 resolution)
- **drift audit report `/verification` verdict 🔴 → ✅ PARITY**; summary 17→18 PARITY / 4→3 CATASTROPHIC
- **3-way evidence pair**: BEFORE 79.9 KB / AFTER 133.0 KB / MOCKUP 207.2 KB
- **22-route sweep cleanest of Phase-2 epic**: 22 IDENTICAL + 1 expected CHANGED (`/verification` +66.4%) + 1 sub-300-byte noise (`/overview` -44 bytes) + 0 unintended regressions
- **Class `frontend-mockup-strict-rebuild` 0.60 7th data point ratio ~0.18** — deepest below-band of class history; 7-pt mean 0.76; last 3 only 2 < 0.7 → KEEP 0.60 per 3-sprint window rule (need 3+ consecutive)
- **🔴 Critical**: `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` 4th cross-class data point — **activation criteria MET** (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 all agent-delegated < 0.7); propose Sprint 57.42 retro structural evaluation

### Phase-2 epic progress (post Sprint 57.41)

- Pre-Sprint 57.41: 17 PARITY + 1 NEAR-PARITY + 4 🔴 CATASTROPHIC
- **Post Sprint 57.41**: **18 PARITY + 1 NEAR-PARITY + 3 🔴 CATASTROPHIC** remaining (`/memory` + `/admin-tenants` + `/tenant-settings`)

### 🆕 6 NEW carryover ADs (Sprint 57.42+ candidates; ordered by ROI / priority)

60. ✅ **`AD-Memory-Layers-Matrix-Rebuild`** — **CLOSED Sprint 57.42** (Day 1 agent-delegated 10th consecutive code-implementer ~40 min wall-clock + Day 2 +12 NEW Vitest specs + drift audit verdict PARITY; 6 NEW components + _fixtures.ts + outer 2-tab DROP §1.4 Option B + 11 orphan deletes Karpathy §3; actual ~3 hr human-eq vs est 10-15 hr → 8th data point for `frontend-mockup-strict-rebuild` 0.60 baseline ratio 0.33; lower-trigger MET for Sprint 57.43 baseline lift; 5th cross-class data point for agent-delegation modifier activation FULLY MET)
61. 🆕 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` tenants table rebuild ~12-15 hr.
62. 🆕 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab rebuild ~15-20 hr. **Largest scope of remaining 3 CATASTROPHIC.**
63. 🆕 **`AD-Verification-Filter-Form-Phase58-Migrate`** — Sprint 57.41 retired filter form per Karpathy §3 (mockup has none). Phase 58+ admin filter UI on `/verification/admin` separate route OR collapsible `<details>` panel.
64. 🆕 **`AD-Verification-Backend-Claim-Evidence-Extension`** — Backend `VerificationLogItem` lacks structured `claim` / `evidence` / `kind`; mapped best-effort via Sprint 57.41 `adaptItem()`. Phase 58+ backend schema extension.
65. 🆕 **`AD-Verification-Failure-Kinds-+-Flaky-Checks-Aggregation-Endpoints`** — Sprint 57.41 sidebar Failure kinds + Flaky checks are AP-2 fixtures. Phase 58+ backend `GET /verifications/stats/{failure-kinds,flaky-checks}` endpoints.

### Carryover from Sprint 57.40 (still open as of Sprint 57.41 closeout)

- `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` — Sprint 57.41 contributes 4th cross-class data point; activation criteria now MET; **propose Sprint 57.42 retro structural evaluation** (Option A multiplicative `agent_factor` 0.55 coefficient OR Option B per-class sub-class split)
- `AD-Verification-Out-Of-Scope-Components-Phase2-C-Mop-Up` — 2 residue sites in VerificationPanel.tsx (chat-v2) + CorrectionTraceView.tsx (/timeline) out-of-scope for Sprint 57.41

---

## 🆕 Sprint 57.40 Carryover (2026-05-25 — /governance Approvals view Full Mockup-Fidelity Rebuild)

Sprint 57.40 (`AD-Governance-Full-Mockup-Fidelity-Rebuild`) closed: single-domain rebuild closes drift audit 2026-05-25 (`claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`) #3 priority `/governance` 🔴 CATASTROPHIC verdict.

- **5 NEW components**: ApprovalsPageHeader / ApprovalsStatsStrip (4 KPI + AP-2 banner) / ApprovalsFilterTabs (5-tab nav + TabId union) / ApprovalDetailPane (rich right-col Detail) / ApprovalsEmptyTab (AP-2 placeholder)
- **1 NEW `KvRow` primitive** in `mockup-ui.tsx` (verbatim port of `page-governance.jsx:265-272`)
- **`ApprovalsPage.tsx`** restructure (73 → 115 lines; 5-component composition + `selected` state)
- **`ApprovalList.tsx`** upgrade (102 → 131 lines; 6-col → 7-col with SevDot; row `onClick` replaces DecisionModal flow; `RISK_COLOR_CLASS` deleted in favor of mockup-ui `<RiskBadge>`)
- **`DecisionModal.tsx`** Karpathy §3 orphan delete
- **+15 NEW Vitest specs** (478 → 493; target +4-8 → **188-375%**)
- **`route-sweep.mjs`** `/governance/approvals` envelope-shape mock (D-DAY0-1 closes audit's red-banner sweep-mock artifact)
- **`check-mockup-fidelity.mjs`** `HEX_OKLCH_BASELINE` 45 → 46 (+1 row-highlight literal mockup-token vocabulary)
- **Drift audit report**: `/governance` 🔴 → ✅ PARITY; 16 → 17 PARITY / 5 → 4 CATASTROPHIC; Recommendations #1+#3 struck; Key finding #5 RESOLVED
- **22-route sweep**: 19 IDENTICAL + 1 expected CHANGED + 4 noise + 0 unintended regressions
- **3-way evidence pair** (BEFORE 79.9 KB / AFTER 115.8 KB / MOCKUP 210.7 KB) staged

**6th data point for `frontend-mockup-strict-rebuild` 0.60 baseline**: sprint-aggregate ratio ≈0.36 BELOW band [0.85, 1.20] by 0.49 (deepest below-band of class history). 6-pt mean 0.86 at lower band edge (-0.10 vs prior 5-pt mean 0.96). Per `When to adjust` rule: only 1 of last 3 < 0.7 → lower-trigger NOT met → **KEEP 0.60 baseline**.

Root cause: code-implementer agent-delegation 7th consecutive ~40 min wall-clock for 5 NEW + 1 primitive + 2 restructures (human-equivalent ~6-8 hr); not modeled in baseline. **3rd data point for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** across 2 classes (57.39=0.41 + FIX-015 + 57.40=0.36).

### Phase-2 epic progress

- Pre-Sprint 57.40 (per audit): 16 PARITY + 1 NEAR-PARITY + 5 🔴 CATASTROPHIC + 12 PROP stubs + 4 DRAFT inactive
- **Post Sprint 57.40**: **17 PARITY + 1 NEAR-PARITY + 4 🔴 CATASTROPHIC** remaining
- 4 remaining CATASTROPHIC: `/memory` (Memory Layers 5×N matrix) / `/verification` (4-KPI + 2-col Recent + sidebar) / `/admin-tenants` (Tenants table 9-col) / `/tenant-settings` (6-tab architecture)
- 1 NEAR-PARITY: `/chat-v2` Inspector tab rename (~30 min quick win)

### 🆕 9 NEW carryover ADs (Sprint 57.41+ candidates; ordered by ROI per audit Recommendations 1-6)

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

## 🆕 Sprint 57.39 Carryover (2026-05-24 — Governance Category Multi-Page Phase-2 4-domain batched)

Sprint 57.39 (`AD-Governance-Category-Multipage-Phase-2`) closed: 4-domain batched.

- **Domain A `/governance`**: tab-shell verbatim CSS swap to `Tabs` mockup-ui primitive (commit `71088441`; 75 → 83 lines; backend wiring untouched)
- **Domain B `/verification`**: same tab-shell pattern (commit `019fa12f`; 77 → 80 lines; Sprint 57.33 defensive `(items ?? []).length` guard intact in `VerificationList.tsx`)
- **Domain C `/redaction`**: PROP→real port (commit `2eefffcd`; 1-line stub → 273 lines verbatim per `page-platform2.jsx:254 RedactionPage` + 6 NEW Vitest specs + AP-2 BackendGapBanner)
- **Domain D `/error-policy`**: PROP→real port (commit `3d5b442e`; 1-line stub → 272 lines verbatim per `page-platform.jsx:426 ErrorPolicyPage` + 8 NEW Vitest specs + AP-2 BackendGapBanner)
- **routes.config.ts cleanup** (commit `085dacec`): dropped `proposed: true` from `/redaction` + `/error-policy` rows
- **22-route sweep** (Day 2.5 `e97cb05b`): 13 CHANGED / 9 IDENTICAL / 0 unexpected regression — 2 intended Day 1 (governance + verification) + 11 collateral sidebar PROP-badge cascade (consistent ~-1.9 KB delta)

**1st deliberate-test data point for `-with-extras` 0.65 baseline**: sprint-aggregate ratio ≈0.41 BELOW band [0.85, 1.20] by 0.44. Root cause = code-implementer agent-delegation (6th + 7th consecutive) ~3-5× speedup vs human-rewrite estimates not modeled in baseline. KEEP 0.65 per `When to adjust` 3-sprint window rule (1-data-point insufficient).

### Phase-2 epic progress

- **11/17 → 15/17 Phase-2 routes shipped / 2 🟡 remaining**: only Phase 58+ STRUCTURAL: `/memory` + `/tenant-settings` (both need backend pair)
- /governance + /verification are NEAR-PARITY shell-level only (child component re-point deferred — see new AD #47 below)
- `/audit-log` still requires backend pair (Round 4 carryover; not part of this sprint per plan §1.3)

### 🆕 5 NEW carryover ADs (Sprint 57.40+ candidates)

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

### Next sprint candidates (post-57.39)

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

## 🆕 Sprint 57.38 Follow-up Carryover (2026-05-24 — 3 user-reported issues → FIX-011 + 3 NEW ADs + frontend-mockup-fidelity.md updated)

User-reported via screenshots after Sprint 57.38 PR #176 merge `44489aba`:

1. `/state-inspector` left/right padding visibly wider than mockup
2. `/state-inspector` detail card title `[v18 by orchestrator_loop]` — `by` baseline lower than mono tokens
3. All-page buttons render black borders vs mockup light grey

### What got fixed in PR (this hotfix)

- ✅ **Issue 1 — FIX-011**: `StateInspectorPage.tsx` drop `padding: 18` from outer wrapper (production-only Sprint 57.19 vintage; mockup has no outer wrapper)
- ✅ **3 systematic anti-patterns codified** in `docs/rules-on-demand/frontend-mockup-fidelity.md` §Phase-2 re-point systematic anti-patterns:
  - **AP-Phase2-A**: Production-only outer padding wrapper (translation-era artifact)
  - **AP-Phase2-B**: Inline mixed-font span baseline misalignment
  - **AP-Phase2-C**: Tailwind utility `border-border` → shadcn `--sc-border` token residue
- ✅ Code review checklist (3 new mandatory items per Phase-2 re-point PR)

### 🆕 NEW carryover ADs (Sprint 57.39+)

- 🆕 **`AD-State-Inspector-Outer-Padding-Wrapper-Fix`** — ✅ RESOLVED by FIX-011 (logged for trace)
- ✅ **`AD-Inline-Font-Baseline-Alignment`** — RESOLVED 2026-05-25 via **FIX-013** for the FIX-011 §Issue 2 documented case (`StateInspectorPage` card title row `CARD_TITLE_ROW_STYLE` adds `alignItems: "baseline"`). Day 0 audit dispositioned Candidate B (CostBurnChart legend — plain inline `<span>`, no flex) + Candidate C (IncidentsCard row — compound badge+text children where `center` is correct) as Skip per Karpathy §3. Closes AP-Phase2-B deferred fix from FIX-011. See `claudedocs/4-changes/bug-fixes/FIX-013-inline-font-baseline-alignment.md`.
- ✅ **`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** — RESOLVED 2026-05-25 via **FIX-012** (user chose Path A as transitional fix). Both consumer sites retargeted at mockup `--border` (`index.css:85` global `* { border-color }` + `tailwind.config.ts:26` `border` utility); `--sc-border` declarations fully retired (0 residual code references). Sprint 57.28 4-layer dual-track partially relaxed (only `--sc-primary` remains as de-collided shadcn token). Path B Phase-2 epic completion still proceeds independently — Path A does NOT substitute for finishing the remaining 2 🟡 STRUCTURAL routes. See `claudedocs/4-changes/bug-fixes/FIX-012-shadcn-border-token-align-to-mockup.md`.
- 🆕 **Sister-bug observation**: FIX-010 (`/loop-debug` fullBleed prop drop) + FIX-011 (`/state-inspector` outer padding wrapper) form a recurring **layout-class production-only artifact** class. Each Phase-2 re-point sprint Day 0 Prong 1 should grep for these artifacts on the target page BEFORE Day 1 code.

### Why Sprint 57.38 Day 2.1 audit missed Issue 1

Domain C `AD-FullBleed-Pages-Audit` cross-referenced production `AppShellV2` mounts vs mockup outer wrapper classes (`chat-shell` / `loop-canvas` / `page-head`) — looking for **fullBleed prop drops**. It found 0 sites. But the audit scope was **only the `fullBleed` decision class**; it did NOT scan for *production-only outer padding wrappers ADDED inside the AppShellV2 mount*. Issue 1 falls into a different class (AP-Phase2-A) that the Sprint 57.38 audit didn't cover.

**Lesson for next audit**: extend Day 0 grep to include:
```bash
grep -n "style={{.*padding\|<div style={{[^}]*padding" frontend/src/pages/<target>/<page>.tsx
```

---

## 🆕 Sprint 57.38 Carryover (2026-05-24 — 3-domain batched: class-split decision + /subagents re-point + fullbleed audit)

Sprint 57.38 (`AD-ClassSplit-Decision-And-Subagents-Repoint-And-FullBleed-Audit`) closed:

- **Domain A — Option 2 class split applied** for `frontend-verbatim-css-repoint`:
  - `-simple` baseline **0.50** — applies when ALL hold: ≤3 files / no AP-2 banner / no dual-mount / no playback/filter widgets / HEX_OKLCH_BASELINE bump < 4. Empirical: 57.34 (/orchestrator) + 57.38B (/subagents) — 2-pt mean ~1.0 in band middle ✅
  - `-with-extras` baseline **0.65** — applies when ANY hold: multi-file > 3 / AP-2 BackendGapBanner / dual-mount / playback/filter/inspector widgets / HEX_OKLCH_BASELINE bump ≥ 4. Empirical: 57.35 + 57.36 + 57.37B historical mean 1.48 at 0.50 → equivalent ~1.14 at 0.65 in band ✅
  - Per-sprint classification rule codified in `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`
- **Domain B — `/subagents` Phase-2 verbatim CSS re-point shipped** (commit `7466d6ef`; agent-delegated 5th consecutive). Day 0 D5 cautiously reclassified `-with-extras` but Day 3 strict criteria re-eval reverted to `-simple` 2nd app (0/5 criteria met). Ratio ~0.91-1.09 estimated.
- **Domain C — `AD-FullBleed-Pages-Audit` 0 sites missing** (happy outcome) — confirms FIX-010 was isolated prop-drop, NOT systematic layout-class assignment failure. 13 production AppShellV2 mounts mapped to mockup wrapper classes: 2 fullbleed (loop-canvas + chat-shell) both correctly opt in; 11 page-head padded card-layout pages all correctly default to NO fullBleed.

### 🔚 CLOSED carryover ADs (Sprint 57.38)

- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal`** (Sprint 57.37 NEW) — RESOLVED via Option 2 split
- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch`** (Sprint 57.36 NEW) — RESOLVED; class split absorbs multi-D variance into 2 baselines
- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 NEW) — RESOLVED; class split was alternative chosen path
- **`AD-FullBleed-Pages-Audit`** (FIX-010 Sprint 57.37+ follow-up) — RESOLVED 0 sites missing

### 🆕 NEW carryover candidates (Sprint 57.39+)

- **`AD-Day0-Prong-Test-Dir-Convention`** — extend Day 0 Prong 1 grep template to cover BOTH `frontend/src/**/__tests__/` AND `frontend/tests/unit/pages/<name>/<name>.test.*` (per Sprint 57.38 D-DB1-2 lesson — project uses separated test dir convention not always co-located `__tests__/`)
- **`AD-Day0-D5-Reclass-Strict-Criteria-Checklist`** — codify 5-item strict checklist before reclassifying `-simple` → `-with-extras` at Day 0 D5 (per Sprint 57.38 retro Q4#2: multi-file > 3 / AP-2 banner / dual-mount / playback widgets / HEX_OKLCH_BASELINE bump ≥ 4 — if 0 of 5 check, keep `-simple` even when internal structure complex)
- **Convention candidate (D-DB1-1)**: agent proactive div-wrap pattern preserves text+role+class-selector spec compat — document in `docs/rules-on-demand/frontend-react.md` as recommended-pattern when spec uses `getByText(x, { selector: "div" })`

### Phase-2 epic progress

- **11 routes shipped** since Sprint 57.29 epic open: /overview / /chat-v2 / /cost-dashboard / /sla-dashboard / /orchestrator / /loop-debug LoopVisualizer (Sprint 57.36) / /state-inspector / /subagents (Sprint 57.38) + AuthShell + LoopVisualizer dual-mount + StateInspectorPage
- **6 🟡 routes remaining**: /governance multi-page / /admin-tenants / /tenant-settings STRUCTURAL Phase 58+ / /memory STRUCTURAL Phase 58+ / /verification / /compaction (PROP stub representative)

---

## 🆕 Sprint 57.37 Carryover (2026-05-24 — 2-domain batched: /loop-debug full rebuild + /state-inspector Phase-2)

Sprint 57.37 (`AD-LoopDebug-Full-Rebuild-And-StateInspector-Repoint`) closed: 2-domain batched. **Domain A /loop-debug full mockup-fidelity rebuild** closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap — 18-event fixture (`_fixtures/demoLoopEvents.ts` NEW) + playback strip (cursor/play/pause/scrubber/speed 1×/4×/8×/16×) + filter pills (6 categories) + LoopInspector right pane (KvRow + HITL Policy + Raw payload) + corrected AP-2 DEMO DATA banner. **User-reported `/loop-debug` empty-state issue FULLY RESOLVED** (after.png shows visual parity with mockup `localhost:8080/#loop-debug`). **Domain B /state-inspector** Phase-2 verbatim CSS re-point per `page-platform.jsx:21-155` preserves Sprint 57.19 US-B3 backend wiring. 22-route sweep **18 IDENTICAL + 4 CHANGED** (loop-debug +63,405 B fixture-rich +66%; state-inspector -14,681 B verbatim simpler; chat-v2 **0 B PERFECT cascade**; auth-callback -68 B + overview +138 B noise). 4 gates green. Vitest **464/464** (+8 NEW Domain A specs; D-DAY3-1 Domain B spec class-swap-resilient — NO update needed). HEX_OKLCH_BASELINE 41→50 within Day 0 D-DAY0-6 estimate. Sprint total ratio ~1.0 IN BAND middle (2-domain HYBRID averaging). Agent-assisted Day 1-3 (4th consecutive code-implementer; ~4.5 hr wall-clock). Updates:

- ✅ **RESOLVED: Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap on /loop-debug** — fixture demo + 4 mockup widgets shipped per CLAUDE.md rule "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture"
- ✅ **RESOLVED: User-reported `/loop-debug` empty-state UX issue 2026-05-24** — page now visually parity with mockup

- 🆕 **NEW DECISION CANDIDATE: `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal`** — Domain B 4th non-rich data point 1.33 ABOVE band; **3-consecutive-above-band lift trigger MET** (57.35=1.7 + 57.36=1.42 + 57.37B=1.33; 4-pt non-rich mean 1.36). Per `When to adjust` rule (3+ consecutive > 1.20 → raise multiplier). **Two options for Sprint 57.38 retro decision**:
  - **Option 1**: class-wide baseline lift 0.50 → 0.60 (simpler; over-corrects truly simple 57.34 baseline)
  - **Option 2 (recommended)**: class split `-simple` (0.50): pure 1-file CSS swap no extras (Sprint 57.34 baseline 1.0 in-band) vs `-with-extras` (0.65): + any of {AP-2 banner, dual-mount, playback/filter/inspector widgets, verbatim oklch-heavy port with HEX_OKLCH_BASELINE bumps, multi-file batched > 3 files} (Sprints 57.35/57.36/57.37B mean 1.48)

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch`** (Sprint 57.36 NEW) — 4th non-rich data point empirically confirms multi-D hypothesis; closed either Option 1 or Option 2 in Sprint 57.38

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 NEW) — alternative lift path; closed either Option 1 or Option 2 in Sprint 57.38

- 🆕 **Convention candidate (D-DAY3-1 positive surprise)**: Vitest spec class-swap-resilience — prefer `getByText` / `getByRole` / `data-testid` over class-name selectors. Codify in `.claude/rules/sprint-workflow.md` OR `docs/rules-on-demand/frontend-react.md`. StateInspectorPage spec needed NO update during Sprint 57.37 Day 3 verbatim port — saved ~10-15 min spec adapt time.

- 🆕 **Lesson**: Calibration ratio formula clarification — `actual / calibrated` (NOT `actual / bottom-up`); codify in sprint-workflow.md to prevent agent prediction errors like Sprint 57.37 Day 3 estimate

- 🆕 **Tracking**: `/overview` + `/auth-callback` recurring noise pattern in route-sweep PNGs (overview +138 B Sprint 57.37 / +70 B Sprint 57.36; auth-callback -68 B Sprint 57.37 first occurrence) — investigate if persists 3+ sprints; likely time-relative text or PNG AA variance

- 🎯 **Phase-2 epic progress**: 7+1 routes shipped (7 Phase-2 routes + AuthShell + LoopVisualizer dual-mount + StateInspectorPage full re-point) / **7 🟡 routes remaining** (governance / admin-tenants / tenant-settings STRUCTURAL Phase 58+ / memory STRUCTURAL Phase 58+ / compaction + 3 unblocked-by-57.33 PROP stubs)

- 🔍 **Drift findings** (Day 0-3): D-DAY0-1..7 (Day 0 verifications) / D-DAY1-1 (TS forEach→for-loop) / D-DAY2-1..3 (17 lint fixes + baseline +3 + fixture 18 events) / D-DAY3-1..3 (spec NO update positive surprise + baseline +6 + KvLine helper <10 line creep)

## 🆕 Sprint 57.36 Carryover (2026-05-24 — /loop-debug Phase-2)

Sprint 57.36 (`AD-Loop-Debug-Verbatim-Repoint`) closed: `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` single-file re-pointed to mockup verbatim per `reference/design-mockups/page-governance.jsx:33-212`. **7th Phase-2 epic app; 3rd shape-validation data point.** 22-route sweep **19 IDENTICAL + 3 CHANGED** (loop-debug +22,512 B expected structural; chat-v2 +18 B cascade ε; overview +70 B time-text noise). 4 gates green (TS 0 / lint 0 / Vitest 456/456 / mockup-fidelity 41/41 unchanged). Agent-assisted Day 1-2 via code-implementer agent (3rd consecutive validated; ~80 min wall-clock). AP-2 BackendGapBanner + EmptyInspectorPlaceholder explicitly defer playback/scrubber/filter/inspector pane to Phase 58+ per Sprint 57.12 AP-6. Dual-mount preserved (Sprint 57.30 chat-v2 inline ship safe). ~205 min total human-equivalent. Ratio actual/committed ~1.42 ABOVE band by 0.22. Updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch** — Sprint 57.36 is 3rd shape data point: 1-file non-rich AGAIN (like 57.34) but ratio diverged sharply (1.0 vs 1.42). Both prior 1-D hypotheses (bimodal-by-shape AND scale-overhead) insufficient. Emerging compound drivers: file count + AP-2 banner addition + dual-mount complexity + spec adapt + drift handling. If Sprint 57.37+ continues > 1.20, propose either (a) baseline lift 0.50 → 0.60, or (b) class split `frontend-verbatim-css-repoint-simple` (0.50, no AP-2 / no dual-mount) vs `frontend-verbatim-css-repoint-with-ap2-or-dual-mount` (0.65). KEEP 0.50 this iteration per `When to adjust` 3-sprint window rule (3-pt non-rich: 1.0/1.7/1.42 needs 1 more above-band for formal lift trigger).

- 🔚 **CLOSED: AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW; Sprint 57.35 weakened) — 3 non-rich data points (57.34=1.0 / 57.35=1.7 / 57.36=1.42) span the whole band; not bimodal. REJECTED.

- 🔄 **Updated → WEAKENED: AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** (Sprint 57.35 NEW) — 1-file (57.36) ALSO above band (1.42); file-count alone is not the variance driver. Broaden into multi-dimensional-variance-watch.

- 🔄 **Updated: AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 4th validation data point logged. 0.50 baseline still appropriate for **simple non-rich 1-file** sprints (57.34 only in-band data point); above-band trend (57.35 + 57.36) needs 1 more above-band sprint for formal lift trigger.

- 📚 **Lessons logged**:
  - Day 0 Prong 1 glob coverage rule: extend to BOTH `frontend/src/**` AND `frontend/tests/**` for spec-existence claims (test files conventionally live outside `src/`). D-DAY1-1 cost ~5 min in agent re-discovery. Codify in `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 1.
  - AP-2 BackendGapBanner addition: ~10-15% calibration surcharge candidate.
  - Dual-mount preservation (mode-branching): ~5-10% surcharge candidate.
  - Combined sprints (AP-2 + dual-mount) should baseline ~0.60-0.65 not 0.50.
  - ESLint `no-restricted-syntax` JSXAttribute style matcher is body-blind for `style={CONSTANT_REF}`; Sprint 57.24 BarTrack STYLE.md §3 escape hatch (module-scope constants + per-site `eslint-disable-next-line`) is the documented workaround.

- 🔍 **Drift findings** (Day 0-1): D-DAY0-1..7 catalogued in progress.md; D-DAY1-1 (test file location) + D-DAY1-2 (ESLint body-blind) caught by agent.

- 🎯 **Phase-2 epic progress**: 6 routes shipped (+ AuthShell + LoopVisualizer dual-mount) / 8 routes remaining (state-inspector, memory STRUCTURAL Phase 58+, governance multi-page, admin-tenants, tenant-settings STRUCTURAL, compaction, 3 unblocked-by-57.33 PROP stubs).

## Sprint 57.35 Carryover (2026-05-24 — AuthShell + 7 auth routes Phase-2)

Sprint 57.35 (`AD-Auth-Shell-And-Pages-Verbatim-Repoint`) closed: 8 files (1 AuthShell + 7 auth routes) re-pointed to mockup verbatim — **6th Phase-2 epic app**; user-reported `/auth/login` drift 2026-05-24 (SSO unstyled / Continue no fill / `dev-login` orange missing) **fully RESOLVED**; **closes Sprint 57.23 vintage HSL-translation epic gap** on auth routes (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning). 22-route sweep **0 regressions** on other 14 routes. 5 gates green. Vitest **456/456 baseline preserved** (4 spec files updated `getByLabelText` → `getByText`+id selectors for mockup-ui Field DOM change; behavioral test intent preserved). Agent-assisted Day 1-3 via code-implementer agent. ~7-7.5 hr human-equivalent effort. Updates:

- ✅ **RESOLVED — Sprint 57.23 vintage HSL-translation epic gap on auth routes** (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning) — fully closed by this sprint.

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** — Sprint 57.35 ratio ~1.65-1.75 ABOVE [0.85, 1.20] band by ~0.45-0.55 (8-file batched sprint). Combined with 57.34 (1-file ≈1.0 in band) + 57.35 (8-file ~1.7 above band), both non-rich-dashboard but vastly different ratios — **file-count + Vitest-spec-update overhead emerging as 2nd variance driver** (not pure shape-driven). If Sprint 57.36+ multi-file sprints again > 1.20 → propose **file-count surcharge** in calibration multiplier (e.g. 0.50 + 0.05/extra-file beyond ~3). KEEP 0.50 baseline this iteration per `When to adjust` 3-sprint window rule (3-pt span 0.40/1.0/1.7 inconclusive).

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW) — bimodal-by-shape hypothesis **WEAKENED but not REJECTED**. 2 non-rich data points (57.34 vs 57.35) span ratio 1.0 to 1.7, suggesting shape is NOT the dominant variance driver; file-count is. Broaden to **scale-and-shape watch**; don't propose class split until 4th data point discriminates.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 3rd validation data point logged. 0.50 baseline still appropriate for typical 1-file re-points.

- 📚 **Lessons logged**:
  - File-count + Vitest-spec-update overhead may be 2nd variance driver beyond shape; budget per-file linearly for multi-file sprints
  - Vitest spec update budget when primitive API changes (e.g. `<label>` → `<div>`); 30-60 min per primitive switch
  - Mockup-internal drift: `page-extras.jsx:13` AuthShell width 400px vs sibling `page-auth-extras.jsx:13` AuthShellX 420px — designate canonical source in `reference/design-mockups/AGENTS.md`

- 🔍 **Drift findings** (Day 1-3): D-DAY1-1 (AuthShell width 420→400 mockup truth) / D-DAY2-1 (register plan label a11y aria-label added) / D-DAY2-2 (register demo banner recast as `.hitl-card[data-severity="risk-medium"]`) / D-DAY3-1 (expired Badge tone="warning" per mockup)

## Sprint 57.34 Carryover (2026-05-24 — /orchestrator Phase-2)

Sprint 57.34 (`AD-Orchestrator-Verbatim-Repoint`) closed: `/orchestrator` re-pointed to mockup verbatim — **1st non-rich-dashboard shape** in the Phase-2 epic (prior 4 = rich operator dashboards). 22-route sweep **0 regressions** on other 21 routes. 5 gates green. Vitest 456/456 baseline preserved. Agent-assisted Day 1-3 via code-implementer agent (per CLAUDE.md Tool Optimization). 3 mockup-ui primitives promoted (Tabs / Field / Switch). OrchestratorPage 644 → 605 net –39 lines (drop ~150 lines of local primitives + Tailwind translations; add mockup-ui imports + verbatim CSS classes + data-testid hooks). ~3-4 hr human-equivalent effort. Carryover updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** — Sprint 57.34 ratio ≈0.95-1.05 lands in [0.85, 1.20] band middle. Combined with prior 4 rich-dashboard apps (3-pt mean ≈0.40 below band ex-57.29 anchor), **bimodal-by-shape pattern emerging** — rich-dashboard ratios consistently below band; non-rich-dashboard (1st data point) in band middle. 2-data-point span (57.32 rich + 57.34 non-rich) suggestive but insufficient per `When to adjust` 3-sprint window rule. **KEEP 0.50 baseline this iteration.** If Sprint 57.35 (another non-rich-dashboard shape — `/loop-debug` / `/state-inspector` / `/admin-tenants` / `/governance` / `/tenant-settings`) confirms in-band → propose class split `-rich-dashboard` (0.40) vs `-config-form` (0.50). If lands below band → class-wide variance after all → 0.50 → 0.40 lift.

- 🆕 **AD-Tabs-Migration-To-MockupUi** (low priority) — `frontend/src/components/ui/tabs.tsx` Sprint 57.19 vintage primitive still imported by other consumers (governance/loop-debug/state-inspector candidates); out-of-scope this sprint. Future Phase-2 re-point of those routes will naturally migrate them to mockup-ui Tabs, then `ui/tabs.tsx` can be deleted.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 2nd validation data point logged. 0.50 baseline still appropriate but bimodal-by-shape signal emerging. If 57.35 confirms, may close this AD in favor of class split.

- 📚 **Atomic primitive promotion lesson** — when primitive promotions span multiple Days but consumer components consume them together, atomic Day 1 promotion is the right call (vs staggered across Days). Agent correctly identified this build-dep; Day 2/3 commits became cycle housekeeping. Plan structure looks "off" in retrospect but result was clean.

## Sprint 57.33 Carryover (2026-05-24 — Page Bug Fix Sweep)

Sprint 57.33 (`AD-Page-Bug-Fix-Sweep`) closed: 3 ⚪ pre-existing crash routes (`/subagents` + `/memory` + `/verification`) fixed by adding defensive `(query.data.X ?? []).length/map` across 5 files / 11 sites including 4 drift sites D1-D4 (`.map` × 3 + `_groupByTurn(items)` × 1) found by widening Day 0 grep beyond `.length`. 22-route sweep: **3 ⚪ → ✅ flip + 0 regressions** on other 19 routes. Vitest 452 → 456 (4 NEW defensive specs). NEW class `frontend-page-bug-fix` 0.45 1st application; ratio actual/committed **1.24** top edge of [0.85, 1.20] band +0.04 over. ~2.8 hr wall-clock. Closes `AD-Overview-PreExisting-Route-Crashes` carryover from Sprint 57.29-32. Updates:

- ✅ **RESOLVED — AD-Overview-PreExisting-Route-Crashes** (Sprint 57.29-32 carryover) — fully closed. 3 ⚪ routes now render proper UI (subagents = full Registry + 4 KPI cards + table; memory = Recent + By Scope tabs + empty state; verification = Recent + Correction Trace tabs + filter form + empty state).

- 🆕 **AD-Sprint-Plan-frontend-page-bug-fix-1st-data-point** — KEEP 0.45 baseline per `When to adjust` 3-sprint window rule. If next 2-3 applications show ratio > 1.20 consistently → propose **0.45 → 0.55-0.60 lift** (mechanical-class-like trend, parallel to Sprint 57.16 AD-Sprint-Plan-13 `frontend-refactor-mechanical` 0.50 → 0.80 evidence).

- 🆕 **AD-CorrectionTraceView-Defensive-Spec** (low priority) — defensive Vitest spec for `CorrectionTraceView` deliberately skipped this sprint per US-D3 "1-2 new specs" scope discipline. Crash path is indirect (via `_groupByTurn(entries)` for…of); covered by Day 4 manual smoke + 22-route sweep flip. Add in future maintenance sprint if `/verification` structural rebuild is scheduled.

- 📚 **Lesson logged in retrospective Q4** — for "undefined-field" / "missing property" crash classes, Day 0 Prong 2 grep should query **all access patterns** on the at-risk field (`\.length`, `\.map`, `\.filter`, `\.forEach`, bare references as function args), not just the access pattern surfaced in the bug repro. 4 drift sites D1-D4 in this sprint are evidence.

- 🔓 **Unblocks** — Phase-2 verbatim CSS re-point candidates for `/subagents`, `/memory`, `/verification` (sweep `after` baselines now meaningful; visual fidelity audit can proceed). `/memory` STRUCTURAL rebuild Phase 58+ remains unchanged scope (independent of crash-fix).

## Sprint 57.32 Carryover (2026-05-24 — /sla-dashboard Phase-2)

Sprint 57.32 (`AD-Sla-Dashboard-Verbatim-Repoint`) closed: `/sla-dashboard` 7 files re-pointed — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (17 🟢 PARITY shell + 1 🟢 PARITY target + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails). 4th data point for `frontend-verbatim-css-repoint` 0.50 (lifted) class; **cleanest mockup mapping of any Phase-2 sprint** (0 production-only widgets — distinct from Sprint 57.31 cost-dashboard which had 3). ~3 hr total wall-clock. Carryover updates:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW; **1st validation data point this sprint**) — Sprint 57.32 ratio actual/committed ~0.40-0.55 (lower band edge). 4-pt mean ≈0.55 lower edge; 3-pt mean ≈0.40 excluding 57.29 anchor (below band by 0.30). Per `When to adjust` 3-sprint window rule, 1 validation data point insufficient to adjust further → **KEEP 0.50 baseline this iteration**. If Sprint 57.33 + 57.34 also < 0.7 → propose 0.50 → 0.40 in Sprint 57.34 retrospective.

- **Hybrid Tailwind+inline color bridge pattern matured across 5 files** (Sprint 57.29 carryover `AD-Inline-Style-Rule-vs-Verbatim-Method` partial exercise) — applied across SLAOverview, LatencyChart, SLOStatusCard, TopSlowOpsTable, ErrorRateByServiceCard. Day 2 SLOStatusCard caught 2 spec drift; Day 3 applied bridge preemptively → 0 spec drift. Pattern documented as standard for Sprint 57.25+ dashboards being Phase-2 re-pointed. Lesson: any color-tone Tailwind class (`text-warning`, `text-danger`, `text-fg-muted`) used in Sprint 57.25 spec contracts should be preserved alongside inline `style={{ color: var(--*) }}` for verbatim.

## Sprint 57.31 Carryover (2026-05-23 — /cost-dashboard Phase-2)

Sprint 57.31 (`AD-Cost-Dashboard-Verbatim-Repoint`) closed: `/cost-dashboard` 7 components batched Day 1 single agent delegation — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (18 🟢 PARITY + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails — shell unchanged from 57.30 + cost-dashboard gain internal). 3rd data point for `frontend-verbatim-css-repoint` 0.60 class. New carryover:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Day 4 calibration) — replaces CLOSED `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` (Sprint 57.30 carryover). Bimodal hypothesis REJECTED — 57.29 + 57.31 same rich-dashboard shape with vastly different ratios (1.0 vs 0.35), so shape NOT the driver of variance. Driver IS estimate generosity diminishing as class iteration matures. Per `When to adjust` 3+ consecutive < 0.7 rule (57.30 + 57.31 + the 0.45+ below-band magnitude on 2 of 3 = clear signal) → LOWER baseline 0.60 → 0.50. Validate 0.50 across next 2-3 sprints; if continues < 0.5 → consider 0.40 next iteration.
- **AD-CostBreakdownTable-Backend-Tenant-Scope** (Day 1 D4 finding) — `CostBreakdownTable.tsx` shows real backend `by_type` 2-level drill-down (`cost_type/sub_type/quantity/total_cost_usd/entry_count`) for current authenticated tenant; distinct from `TenantTopTable` (cross-tenant admin fixture). Document data ownership to prevent accidental merge in future sprints; consider adding ARCHITECTURE.md section on cost-dashboard data flows.

**3 production-only widget patterns identified** (generalizable for future Phase-2 sprints):
1. **Mockup token vocabulary only** (MonthPicker D5) — `var(--*)` inline; no AP-2 banner; UI affordance.
2. **Mockup `.table` vocabulary verbatim** (CostBreakdownTable D4 decision c) — real backend; no AP-2; same vocabulary as if mockup had it.
3. **Mockup vocabulary + AP-2 BackendGapBanner** (e.g. Sprint 57.30 InputBar error) — fixture data; AP-2 honesty banner.

---

## Sprint 57.30 Carryover (2026-05-23 — chat-v2 Phase-2 + shell hotfix; AD-Sprint-Plan-frontend-verbatim-bimodal-watch CLOSED in 57.31)

Sprint 57.30 (`AD-Chatv2-Verbatim-Repoint + Shell-Hotfix-UserMenu-Avatar`) closed: `/chat-v2` 19 components re-pointed to verbatim mockup CSS + Day 1 shell hotfix (UserMenu Radix-drop + verbatim `useDismiss` port + avatar trigger 36→26 split + topbar icon audit 0 drift) — fidelity verdict **PARITY**, 22-route sweep 0 catastrophic / 0 structural; Day 5 orphan cleanup deletes `dropdown-menu.tsx` + `npm uninstall @radix-ui/react-dropdown-menu` → bundle **-116.87 KB / -38.37 KB gzipped**. Closed `AD-UserMenu-Mockup-Structural-Deltas` (Sprint 57.29 carryover). New carryover:

- ✅ **CLOSED Sprint 57.31**: **AD-Sprint-Plan-frontend-verbatim-bimodal-watch** — Sprint 57.31 3rd data point evaluation rejected bimodal hypothesis; replaced by `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` above.
- **AD-Tsconfig-Node-NoEmit** (Day 1 finding) — `tsc --strict` reports pre-existing `TS6310: referenced project tsconfig.node.json may not disable emit` since baseline `5c0ce0dd`. Not introduced by Sprint 57.30. Defer to tooling cleanup sprint or separate PR.
- **AD-Topbar-Use-Button-Primitive** (Day 0 D4 finding) — production Topbar uses raw `<button className="btn ghost" data-size="sm">` instead of mockup-ui `<Button>` primitive. Rendered DOM byte-identical; cosmetic-code-style refactor, low ROI. Defer.
- **AD-Topbar-Tweaks-Panel-Phase58+** (Day 0 D5 finding) — mockup `shell.jsx:218` has `<Button icon="sliders" onToggleTweaks>` Tweaks button; production omits it (no Tweaks panel implementation). Defer to Phase 58+ when Tweaks panel ships.
- **AD-ApprovalCard-Legacy-Phase58-Migrate** (Day 4 finding) — `ApprovalCard` confirmed legacy per `chatStore.ts:L324` dual-emit comment; HITLTurn is canonical Phase-1 chat-inline render. Re-pointed this sprint for completeness; 0 main render path. Migrate governance integration to HITLTurn-only in Phase 58+, then delete.

---

## 🆕 Sprint 57.29 Carryover (2026-05-22 — Phase-2 per-page re-point opens; partially closed in 57.30)

Sprint 57.29 (`AD-Overview-Verbatim-Repoint`) closed: `/overview` + app shell + 3 topbar overlays + 7 widgets re-pointed to verbatim mockup CSS — fidelity verdict **PARITY**, 22-route regression sweep 0 catastrophic / 0 structural. The Phase-2 per-page re-point template is validated (`frontend-verbatim-css-repoint` 0.60 class). Carryover:

- **AD-Inline-Style-Rule-vs-Verbatim-Method** — the `no-restricted-syntax` ESLint inline-`style=` ban (Sprint 57.15/57.16) conflicts with the verbatim method's required mockup inline-style literals; currently handled per-file with `eslint-disable` + rationale. Decide: scope the rule to exclude verbatim-re-pointed dirs, or retire it.
- **AD-UserMenu-Mockup-Structural-Deltas** — ✅ **CLOSED in Sprint 57.30 Day 1**: Radix `<DropdownMenu>` dropped entirely; `useDismiss` hook ported verbatim from mockup `topbar-overlays.jsx:9-27`; avatar trigger 36→26 split via `.avatar` CSS class; dropdown now flush against topbar bottom edge (`top:50; right:12` verbatim positioning honoured).
- **AD-MockupFidelity-Guard-TokenRelative-Oklch** — `frontend/scripts/check-mockup-fidelity.mjs` grep counts token-relative `oklch(from var(--token) …)` literals as "hardcoded"; refine the grep to exclude them so faithful verbatim re-points don't grow `HEX_OKLCH_BASELINE` (raised 18→21 in 57.29; 21→25 in 57.30).
- ~~**AD-Overview-PreExisting-Route-Crashes** — `/subagents`, `/memory`, `/verification` render an error boundary (`Cannot read properties of undefined (reading 'length')`) — pre-existing (Day-0 baseline == after sweep on both 57.29 and 57.30); NOT a regression. Separate FIX sprint candidate (Sprint 57.31+ "frontend-page-bug-fix" class at ~0.45 mid-band).~~ **✅ RESOLVED Sprint 57.33** — see Sprint 57.33 Carryover section above.
- **Next Phase-2 per-page re-point** — Sprint 57.30 picked `/chat-v2`. Remaining 12 🟡 AppShellV2 routes: orchestrator / loop-debug / memory / state-inspector / governance / verification / cost-dashboard / sla-dashboard / admin-tenants / tenant-settings / compaction (+ subagents / memory / verification but those need crash fix first).

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

- New carryover ADs from each sprint retrospective should be **appended here**, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then move to "Closed" section or delete.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail.

---

## Modification History

- 2026-05-22: Sprint 57.28 Day 4 closeout — verbatim-CSS foundation switch SHIPPED (22-route sweep 0 catastrophic / 0 structural regression); +2 ADs (#45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`); the Phase-2 per-page re-point epic now runs on a correct verbatim foundation
- 2026-05-21: Sprint 57.27 Day 3 closeout — `/overview` rebuild SHIPPED (DRIFT verdict PARITY); +2 ADs (#43 `AD-Overview-Backend-Extensions-Phase58` + #44 `AD-CardShell-Title-Crossverify-cost-sla`); RESOLVED #41 (rich-dashboard sub-class DROPPED — 57.27 `/overview` 4th `frontend-mockup-strict-rebuild` data point ratio ≈0.95 in-band; rich-subset 3-pt mean ~1.01 → no split, KEEP single 0.60 baseline)
- 2026-05-21: Sprint 57.26 post-closeout CI fix — +1 AD #42 (`AD-Day0-Prong4-Visual-Baseline-Scope`); PR #159's first CI run failed on 5 stale `visual-regression.spec.ts` baselines (foundation-token correction deliberately moved the visuals); baselines regenerated via `playwright-e2e.yml` workflow_dispatch (`f0b24bd2`), CI re-run green / `state: CLEAN`
- 2026-05-21: Sprint 57.26 Day 3 closeout — foundation-fidelity sprint (global token correction across 22 routes; user-directed insertion, NOT drawn from this candidate list) shipped with 0 regression; 0 new carryover ADs at closeout (later +1 AD #42 post-closeout CI fix — see entry above); 3 FOUNDATION-APPLIED routes folded into the existing rebuild epic per DRIFT-REPORT §5; #33/#34/#35 candidate sprint numbers shifted +1 (→ 57.27/57.28/57.29) + #41 4th-data-point sprint → 57.27 (foundation-fidelity took the 57.26 slot)
- 2026-05-19: Sprint 57.25 Day 3 closeout — close #32 (sla-dashboard rebuild SHIPPED) + +3 ADs (#39-#41) SLA Dashboard Rebuild carryovers (backend extensions + LatencyChart extraction trigger + rich-dashboard sub-class DEFER decision)
- 2026-05-19: Sprint 57.24 v2 Day 3 closeout — +7 ADs (#32-#38) Cost Dashboard Rebuild carryovers (4 page rebuilds 57.25-57.28 + 1 backend extension + 1 Playwright MCP recovery + 1 plan-draft Prong 5 discipline addition)
- 2026-05-19: Sprint 57.24 Day 0 — +1 AD #31 Memory STRUCTURAL Rebuild carryover (Q2 decision: defer from 57.24 cosmetic retrofit to dedicated Phase 58+ sprint)
- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
