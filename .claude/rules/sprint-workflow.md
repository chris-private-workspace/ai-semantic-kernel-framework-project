# Sprint Workflow Rules

**Purpose**: Enforce sprint execution discipline; prevent Phase 35-38 shortcut lessons from repeating.

**Category**: Development Process
**Created**: 2026-04-28
**Last Modified**: 2026-06-17
**Status**: Active

> **Modification History**
> - 2026-06-17: REFACTOR-008 — Reference Template (Step 1 + Step 2) re-anchored from "most-recent sprint" (relative/floating → monotonic drift) to FROZEN `claudedocs/templates/sprint-{plan,checklist}-template.md` (absolute); enforce short H1 + Summary block + §0 line-breaks (fix the 57.107-130 drift defects)
> - 2026-06-16: chore(rules) — §Sprint Closeout post-merge status-flip rule: flip `PR-pending`→`MERGED` on the 2 current-status surfaces (CLAUDE.md Current Sprint row + next-phase head block) after gh-verified merge + interregnum Current-Sprint-row wording + historical-block sweep only if misleading (one done 2026-06-16 for 57.112-126)
> - 2026-06-03: chore(rules) — Area-A (57.66-73) lessons fold-in: Prong-1 test-infra verify (AD-Day0-Prong1-TestInfra-File-Verify) + Prong-2 +2 drift rows (codegen-shape AD-Day0-Codegen-Existing-Shape-Capture / no-live-producer) + Risk Class E (stale --reload masks wiring; C-11 cost_ledger) + Risk Class C reinforce (AD-Source-DB-Call-Test-Isolation) + Before-Commit item 7 (agent-delegation: all gates + pin language + parent re-verify)
> - 2026-05-31: REFACTOR-005 — extract per-sprint calibration history (matrix per-cell narration + §Scope-class MHist list + agent_factor activation history 57.42→57.62 + top calibration-retro entries) to calibration-log.md; kept active multiplier table + agent_factor Formula/Rollback/Escalation/Tracking rules (always-loaded file ~90k→~25k tok)
> - 2026-05-29: Sprint 57.62 follow-up chore — mark §Common Risk Classes Risk Class A **RETIRED Sprint 55.6** (paths filter removed → docs-only PRs run full CI; stale touch-backend-ci.yml workaround description corrected; residual webhook-miss edge case noted)
> - 2026-05-26: Sprint 57.52 — Drift Class table +2 rows (closes AD-Day0-Prong2-Oklch-Delta-Grep + AD-Stale-Docstring-Karpathy-3)
> - 2026-05-26: Sprint 57.51 — add §Common Risk Classes Risk Class D ORM File Path Reference Style (closes AD-Plan-Risk-ORM-File-Path-Reference-Style #82; Sprint 57.50 D-DAY0-2 lesson)
> - 2026-05-25: Bundle Item #4 — propose Agent Delegation Factor Modifier (matrix proposal, pending 2-3 sprint validation) + §Before Commit lint must be non-silent (closes AD-Sprint-Plan-Agent-Delegation-Factor-Modifier as proposal + AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
> - 2026-05-25: AD-Plan-5 fold-in §Step 2.5 Prong 2.5 Child Component Tree Depth Audit (closes AD-Day0-Prong2-Child-Component-Tree-Depth-Audit; Sprint 57.39 D-DAY1-1 + FIX-015 evidence)
> - 2026-05-18: Sprint 57.22 — add §Sprint Closeout CLAUDE.md+MEMORY.md update policy (closes REFACTOR-001 Step 2)
> - 2026-05-06: Sprint 57.1 — fold-in §Step 2.5 Prong 3 Schema Verify (closes AD-Plan-4 promotion)
> - 2026-05-05: Sprint 55.6 — promote AD-Plan-3 (Prong 2 content verify + ROI + grep patterns)
> - 2026-05-04: Sprint 55.3 — add §Step 2.5 Day-0 plan-vs-repo grep verify (closes AD-Plan-1) + drop per-day "Estimated X hours" headers from checklist template (closes AD-Lint-2)
> - 2026-05-04: Sprint 53.7 — add §Workload Calibration sub-section under Step 1 (closes AD-Sprint-Plan-1) + new §Common Risk Classes top-level section (closes AD-CI-4) + Pre-Push reference `python scripts/lint/run_all.py` wrapper (closes AD-Lint-1 doc portion)
> - 2026-04-28: Initial creation (V2 foundation) — enforce 5-step workflow + change record conventions
>
> Per-sprint calibration-retro entries (Sprint 57.42→57.62, dropped here per REFACTOR-005) → [calibration-log.md §3](../../docs/03-implementation/agent-harness-execution/calibration-log.md).

---

## Overview

This document enforces the **mandatory 5-step sprint execution flow** used in V2 (Phase 49+). Phase 35-38 violated this flow by skipping plan + checklist, leading to scattered implementation and poor traceability.

**Golden Rule**: `Phase README → Sprint Plan → Sprint Checklist → Code → Update Checklist → Progress Doc`

---

## Mandatory 5-Step Workflow

### Step 1: Create Plan File

**Before writing any code**, create sprint plan at `docs/03-implementation/agent-harness-planning/phase-XX-name/sprint-XX-Y-plan.md`.

**Required Sections**:
- **Sprint Goal**: One sentence. What does this sprint deliver?
- **User Stories**: 3-5 stories in "As a / I want / So that" format
- **Technical Specifications**: Design decisions, architecture rationale, technology choices
- **File Change List**: Explicit list of all files to be created/modified (with counts)
- **Acceptance Criteria**: Measurable, testable definition of done
- **Deliverables**: `- [ ]` checkbox list mapping to stories
- **Dependencies & Risks**: What could block? What's the mitigation?

**Reference Template** (FROZEN — REFACTOR-008, 2026-06-17): Mirror the **frozen canonical template** `claudedocs/templates/sprint-plan-template.md` — an ABSOLUTE anchor, **NOT** the most-recent sprint's plan. Mirror its §0-9 section structure + the `**Status/Branch/Base/Slice/Scope decisions**` metadata block + the 2 readability rules it enforces: **(1) the H1 is ONE short scope line** — the full description goes in the `**Summary**` block, never embedded in the H1; **(2) §0 Background uses sub-headers + line breaks**, not a wall of prose. Express sprint scope differences through **content** (more stories / files / risks), **never through structure** (don't add/rename sections, don't change the Day count).

**Why FROZEN** (drift audit, REFACTOR-008): the prior "mirror the most-recent completed sprint" rule used a RELATIVE / floating anchor — each sprint copied the previous, so small per-sprint drifts compounded monotonically. Audit across 80+ sprints: 49.1 (freeform 中文, no §-numbering) → 51.2/52.1 (clean §0-9 中文) → 57.107-130 (英文, ~600-char run-on H1, dense §0). Any adjacent pair looked "consistent"; the cumulative drift was large. The frozen template stops the ratchet. (The 51.2/52.1 §0-9 was the prior closest-to-canonical; the 57.x era added genuinely valuable sections — §6 Deliverables, §7 Workload Calibration, the metadata block, Drive-through — which the frozen template KEEPS while fixing the H1 + §0-density defects.)

**Why**: Prevents vague scope. Forces thinking before coding. Becomes sprint contract. Format consistency lets reviewer / next-session AI navigate any sprint plan with the same mental map.

**Violation Pattern** ❌: "I'll start coding and see what happens" → scattered PRs → unclear scope → Phase 35-38 repeat.

**Violation Pattern** ❌ (Sprint 52.1 v1 — 2026-04-30): Drafted plan with 10 sections + 6 days + custom section names without consulting most recent (51.2) plan format. User had to point out inconsistency; 3 rewrites (v1→v2→v3) before format aligned. **Lesson**: Read prior sprint plan FIRST, then mirror exactly.

#### Workload Calibration (Sprint 53.7+ — closes AD-Sprint-Plan-1)

Plan §Workload (or equivalent header) **must** state estimate in this three-segment form:

> Bottom-up est ~X hr → calibrated commit ~Y hr (multiplier Z)

- **X** = sum of per-task / per-US bottom-up estimates (raw, no calibration applied)
- **Z** = calibration multiplier in [0.4, 1.0]; default **0.5–0.6** (mid-band 0.55) per 53.4 + 53.5 + 53.6 retrospectives Q2 evidence (3 consecutive ~50% over-estimate; ~7-14 hr banked across 3 sprints)
- **Y** = X × Z = number you actually commit to (PR description / sprint goal acceptance / Day 4 retrospective Q2 baseline)

**When to adjust the multiplier**:
- 3+ consecutive sprints with `actual / committed > 1.2` → raise multiplier (e.g. 0.55 → 0.70) — under-estimating
- 3+ consecutive sprints with `actual / committed < 0.7` → lower multiplier (e.g. 0.55 → 0.40) — buffer too generous
- Single-sprint outliers: ignore; 3-sprint moving evidence required

**Day 4 retrospective Q2 must verify the multiplier**:
- Compute `actual_total_hr / committed_total_hr` ratio
- Document delta vs expected `≈ 1.0`
- If `|delta| > 30%`: log `AD-Sprint-Plan-N+1` to revisit multiplier in next plan template iteration

**Why**: Three consecutive ~50% over-estimate sprints (53.4 + 53.5 + 53.6) showed bottom-up estimates consistently double actual; without calibration, sprint commitments were inflated and "banked" hours obscured velocity tracking.

**First plan to apply**: Sprint 53.7 itself (`sprint-53-7-plan.md` §Workload).

#### Four-segment form when `agent_factor` applies (Sprint 57.43+ — ACTIVATED 2026-05-25 per Sprint 57.42 retro)

When the sprint anticipates code-implementer agent-delegation as the primary Day 1 mechanism (≥ 80% of Day 1 work via agent), Plan §Workload **must** use the four-segment form:

> Bottom-up est ~X hr → class-calibrated commit ~Y hr (mult Z) → agent-adjusted commit ~Y' hr (agent_factor 0.55)

where `Y' = Y × 0.55 = X × Z × 0.55`. See §Active Agent Delegation Factor Modifier below for full formula, evidence, rollback rule, and tracking discipline.

**MANDATORY plan-time `Agent-delegated:` field** (Sprint 57.57+ — codified via `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` PROMOTION; 5-data-point evidence Sprint 57.53+57.54+57.55+57.56+57.57 consecutive usage):

Plan §Workload section MUST include an explicit `Agent-delegated:` field at plan-time (NOT just retrospective Q2). Acceptable values:

- **`yes`** — ≥ 80% of Day 1 work via code-implementer agent. Apply 4-segment form with appropriate `agent_factor` sub-class baseline. Required for sprints generating validation data points under the tier-4 agent_factor sub-class table.
- **`partial`** — 20-79% via agent. Apply `agent_factor = 0.75` linear interpolation per §Active block formula. Sprint plan §Workload still uses 4-segment form.
- **`no`** — < 20% via agent (parent-assistant-direct execution). Apply `agent_factor = 1.0`. Sprint plan §Workload uses 3-segment form (no agent-adjusted commit line; class-calibrated commit IS the final commit).
- **`TBD-Day-1-decision`** — when delegation choice is contingent on Day 0 三-prong findings or Day 1 scope clarification (e.g. Sprint 57.45 Path A vs Path B branch). MUST resolve to `yes`/`no`/`partial` by Day 1 start; recorded as final value in retrospective Q2.

**Rationale** (5-data-point evidence base): plan-time `Agent-delegated:` field surfaced calibration class selection decisions upfront (Sprint 57.53 parent-direct → `agent_factor = 1.0` applied retroactively per Sprint 57.45 Path B precedent; Sprint 57.54-57.57 all delegated-yes pre-declared and consistently honored). Without this field, the `agent_factor` row in §Active block was inconsistently applied — some sprints retroactively classified, some pre-declared. Pre-declaration prevents retro confusion AND surfaces sub-class baseline selection (mechanical-pattern-reuse-heavy 0.30 vs -greenfield-port-style 0.45 vs -design-decisions 0.65) in plan §Workload §Sub-class declaration. Per AD-Plan-2/3/4/5 promotion precedent: 3-data-point evidence sufficient; Sprint 57.57 = 5th consecutive consistent usage.

**Tracking discipline cross-ref**: §Active Agent Delegation Factor Modifier §Tracking discipline (MANDATORY from Sprint 57.43+) §3 row reads "**NEW**: explicit `agent-delegated: yes / no / partial` tag" — Sprint 57.57 codification clarifies this is PLAN-TIME tag (was ambiguous between plan-time vs retro-time in original wording).

#### Scope-class multiplier matrix (Sprint 57.6+ — closes AD-Reality-10 + AD-Sprint-Plan-7)

Per AD-Sprint-Plan-4 (logged Sprint 55.3) + 4-sprint window evidence,one-multiplier-fits-all approach loses signal when scope class differs。Below matrix記錄 active classes per scope。`mid-band` value 0.55 for default unclassified scopes;diversification per evidence。

> **Per-class data-point history + per-cell narration + the matrix change log moved** (REFACTOR-005, 2026-05-31) → [`calibration-log.md` §1](../../docs/03-implementation/agent-harness-execution/calibration-log.md). The table below = current multiplier + 3-sprint mean + 1-line status only. Adjustment rule = §Workload Calibration §When to adjust the multiplier above (3-sprint moving window).

| Scope class | Mult | 3-sprint mean | Status (1-line) |
|-------------|------|---------------|-----------------|
| `mixed` (greenfield + reuse) | 0.60 | 0.79 ⬇ | KEEP; AD-Sprint-Plan-6 propose split greenfield 0.60 / pattern-reuse 0.40 |
| `knowledge-connector-real-source-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.145 ratio ~1.15-1.25 upper-edge IN band; the FIRST real external data-source connector — `knowledge_search` + `LocalDocsConnector` reading real in-repo `.md`, opt-in `make_default_executor` (mirrors todo_store/skill_registry) + handler-threaded default-ON + prompt nudge, parent-direct agent_factor 1.0. Backend-only NO migration/wire(26)/frontend, reuses Cat 2 ToolSpec. The upper-edge = the Day-3 drive-through-found multi-word 0-hit bug fix (tokenize + OR match) + 2 regression tests + the clean-restart env-injection debug — NORMAL spike cost (a connector you can't drive-through is a Potemkin), NOT an estimate miss. Drive-through PASS real Azure gpt-5.2 (session 0f91faa8): agent calls knowledge_search → real `04-anti-patterns.md`/`08-glossary.md`/`00-v2-vision.md` snippets → grounded answer cites 3 real source paths → end_turn. If a 2nd `knowledge-connector-real-source-spike` lands > 1.2, re-point toward 0.65. CHANGE-112 + design note 49) |
| `knowledge-embedding-vector-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.146 ratio ~1.05-1.15 IN band upper half; Slice 2 of the knowledge arc — section-aware `##` chunking (fixes 57.145 R2 over-search) + the platform's FIRST real `EmbeddingClient` ABC (`adapters/_base/`, provider-neutral) + Azure `text-embedding-3-large` adapter (SDK confined per 約束 3) + `QdrantVectorStore` (`query_points`; closes CARRY-026 for KB) + `KnowledgeVectorIndex` (batched ingest + cosine), opt-in `KNOWLEDGE_VECTOR_ENABLED` vector-primary + keyword fail-soft, parent-direct agent_factor 1.0. Backend-only NO migration/wire(26)/frontend, new dep `qdrant-client`. Set 0.60 ABOVE the 57.145 `knowledge-connector-real-source-spike` 0.55 because the new cross-category ABC + Qdrant infra wrapper are real design-decision content — though the EXISTING Qdrant container + `QdrantNamespaceStrategy` offset some greenfield (so 0.60 not higher). The upper-half landing = the Day-3 drive-through's 2 real-connection bug fixes (env-name rename `embedding_deployment`→`deployment_embedding` caught a latent AttributeError + 429 batching `_EMBED_BATCH=16` after discovering `list_files()` recursion pulls the default root to 418 files/3818 sec → bounded `docs/rules-on-demand` 129) + the orphan-spawn-worker clean-restart hunt — NORMAL spike cost (a vector path you can't drive-through is a Potemkin), same shape as 57.145. Drive-through PASS real chat-v2 + real Azure gpt-5.2 + real text-embedding-3-large + real Qdrant (trace f5b394db): a query with NO literal "adapter"/"neutrality" → knowledge_search TOOL_EXEC 1750ms → Qdrant returns `adapters-layer.md`/`llm-provider-neutrality.md` by similarity → answer cites each real source path+section. If a 2nd `knowledge-embedding-vector-spike` lands > 1.2, re-point toward 0.70 (the external-dep drive-through is the variance driver). CHANGE-113 + design note 50) |
| `knowledge-per-tenant-isolation-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.147 ratio ~1.0-1.15 IN band; Slice 3a of the knowledge arc — closes the **isolation half** of `AD-Knowledge-Connector-RBAC-Citation-Slice3`. Threads `tenant_id` end-to-end **mirroring `memory_search`** (dual-arity `(ToolCall, ExecutionContext)` + `_reject_forged_scope` guard) → per-tenant Qdrant collection (`QdrantNamespaceStrategy.collection_name(tid,"kb")`) + `payload_filter` (defense-in-depth) + per-tenant corpus subfolder (`<root>/<tenant>/`, shared fallback) + lazy idempotent per-tenant ingest; `tenant_id=None` = 57.146 byte-identical; `_ingest_knowledge`→`_warm_knowledge_index` (drop blocking startup ingest). parent-direct agent_factor 1.0. Set 0.55 BELOW 57.146's `knowledge-embedding-vector-spike` 0.60 because EVERY building block pre-existed (`QdrantNamespaceStrategy` 49.3 / executor arity auto-dispatch 52.5 / loop `ExecutionContext(tenant_id=…)` / `QdrantVectorStore.search(payload_filter=)` pre-wired in 57.146) — this WIRES existing pieces + mirrors a proven pattern, no new ABC/infra. The Day-0 三-prong's key win: a 2-file read (`loop.py:2925` + `executor.py:213`) turned the gating "does the chat path thread a tenant-populated ExecutionContext?" risk GREEN before any code. **UNLIKE 57.145/146, NO connection-shape bug surfaced** at drive-through ∵ payload_filter was pre-tested in 57.146 + the pre-UI programmatic sanity was clean — so the 2-tenant drive-through (clean restart + 3-leg Playwright) ran on-budget, not over. Drive-through PASS real chat-v2 + real Azure gpt-5.2 + real text-embedding-3-large + real Qdrant (2 tenants): alpha asks Falcon → only `falcon.md`; alpha asks Condor → **0 condor.md, "I did not find Project Condor"** (judge 0.98); beta asks Condor → only `condor.md` (Nightjar), 0 falcon leak; Qdrant 2 distinct `tenant_*_kb` — bidirectional isolation at agent + vector-store layers. If a 2nd `knowledge-per-tenant-isolation-spike` (e.g. Slice 3b RBAC) lands > 1.20, re-point toward 0.65 — the multi-tenant drive-through SETUP (2 tenants + per-tenant corpora + JWT + clean restart) is the variance driver. CHANGE-114 + design note 51) |
| `memory-formation-identity-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.148 ratio ~1.0-1.1 IN band; closes `AD-Memory-Formation-Identity` Slice 1 — the fix for a LIVE-drive-through gap (new session → "我不知道你是誰"): a system-prompt `MEMORY_FORMATION_NUDGE` → agent proactively `memory_write(scope=user)` (rides the proven skills-catalog seam `loop.py:1970`) + a NEW additive `MemoryRetrieval.profile()` (wildcard user-scope long_term) merged UNCONDITIONALLY into `DefaultPromptBuilder.build()`'s user block (dedup by hint_id + within the Tier2 ≤2000-tok cap + graceful-degrade) so identity surfaces EVERY turn keyword-independently (bypasses the ILIKE query-gating `builder.py:581`+`user_layer.py:88` that caused the bug). Backend-only NO migration/wire/frontend; `user_id=None` byte-identical. parent-direct agent_factor 1.0. Closest kin: `verification-in-loop-spike` 0.60 (a Cat-core new-domain spike with a real-code core) + `harness-loadbearing-gap-fix` 0.85 (57.122 — make an existing mechanism load-bearing). Set 0.60 NOT 0.85 because the real-code core (new profile() + builder merge + nudge + 11 multi-tenant tests, ~3-4 hr) HELD the spike mult per the 57.137 lesson — this is NOT a tiny-code-wrapped-in-ceremony sprint. Drive-through PASS real chat-v2 + Azure gpt-5.2: jamie states identity (no "remember me") → 2 `memory_user` rows proactively written → NEW session "你知道我是誰嗎?" (0 keyword overlap) recalls "你是 Chris…Knowledge Connector" (Inspector 2 user-reads) → priya (diff user) "我不知道你是誰" (per-user isolation). 1 regression caught+fixed (`test_skills_wiring` real_llm `system_prompt == DEMO` byte-identical assumption — updated to expect the nudge). The variance driver = the 2-session/2-identity drive-through + DB-evidence plumbing (raw asyncpg pw≠.env → backend `get_session_factory()` + `set_config('app.tenant_id',:t,true)` for FORCE-RLS). If a 2nd `memory-formation-*-spike` lands > 1.20, re-point toward 0.85. CHANGE-115 + design note 52) |
| `memory-formation-extract-spike` | 0.60 → **0.85** (re-pointed Sprint 57.149) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.149 — the 2nd memory-formation-* spike, closes `AD-Memory-Formation-Auto-Extract` Slice 2: wires the long-unwired `MemoryExtractor` (51.2) onto the chat path — after EVERY real_llm send (env-gated `CHAT_MEMORY_AUTO_EXTRACT` default ON, cheap `profile.cheap` tier) a Starlette `BackgroundTask` deterministically extracts durable user facts → `UserLayer` tagged `source="auto_extract"`, so the platform forms memory even when the agent never calls `memory_write` (57.148 Option-A nudge is discretionary). Prompt-level dedup via 57.148 `profile()`; `build_chat_memory_extractor` self-contained (0 of build_handler's ~12 callers touched). Backend-only NO migration (the `memory_user.source` column pre-existed)/wire(26)/frontend; `=false`/`user_id=None` byte-identical. parent-direct agent_factor 1.0. **1st pt ratio ~1.3-1.4 OVER band at 0.60 → re-point 0.85** per the 57.148 sibling note ("2nd memory-formation-* spike > 1.20 → re-point 0.85"). The real-code core (6 src edits + 14 tests, ~4 hr) HELD its share; the over-run is ALL Day 3 — the drive-through discovery loop: a sync→`BackgroundTask` re-architecture (moved extraction off the SSE generator — the plan's "synchronous to avoid an orphan" wrongly conflated Starlette BackgroundTask, which is managed-lifecycle NOT an orphan, with fire-and-forget `asyncio.create_task`) + a noise investigation (the `async generator ignored GeneratorExit` + OTel detach errors were found PRE-EXISTING `tracer.py:200 _span_cm`, NOT the extraction) + a full clean-restart re-drive. Same ceremony-not-code-accelerated pattern as the 57.120/122/123/126/129/132 0.85 re-points, except here the over-run is a genuine drive-through-found architecture change, not just fixed-cost ceremony. Drive-through PASS real chat-v2 + Azure gpt-5.2 (3 legs): dan "Project Aurora" → `[auto_extract]` conf 0.99 → NEW session recalls Aurora → priya 0-leak; BackgroundTask re-drive (priya) → `[auto_extract]` conf 0.78 SOC 2 row. NEW finding `AD-Verification-Judge-Memory-Inject-Blind` (in-loop judge false-positive-REJECTs memory-injected recalls). CHANGE-116 + design note 53. If a 2nd `memory-formation-extract-spike` lands < 0.7 at 0.85, lower again) |
| `memory-upsert-dedup-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.150 ratio ~1.07 IN band; the memory-formation arc dedup slice — closes `AD-Memory-User-Upsert-By-Key`: `UserLayer.write()` always INSERTed → 57.149's auto_extract (every send) piled up duplicate user-fact rows that diluted 57.148 `profile()` top-k. A focused Cat-3 write-path correctness fix WITH a real migration — `MemoryUser.dedup_key VARCHAR(32) = md5(normalize(content))` + `(tenant,user,dedup_key)` unique constraint + `pg_insert … on_conflict_do_update` (greatest confidence / latest content / bump updated_at / KEEP first-writer source+metadata) + migration 0032 (add col → backfill `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` matches `_dedup_key` byte-for-byte → delete pre-existing dups (row_number keep highest-conf/newest) → add constraint) + a `_dedup_key` normalization helper + a unit-test refactor (write tests add→execute + `test_ops_emit` add→execute) + 6 real-Postgres integration tests + drive-through. parent-direct agent_factor 1.0. Set 0.60 NOT a tiny-code 0.85 because the real-code core (migration + write rewrite + test refactor ≥~3 hr) HELD the spike multiplier per the 57.137 lesson. **UNLIKE the 57.149 `memory-formation-extract-spike` over-run, this landed CLEAN (~1.07)** because the drive-through fired the dedup on send 1 — the agent's `memory_write` + the auto_extract re-extract of the same verbatim fact collapsed to ONE row immediately (visible as `updated > created`), NO re-architecture / noise investigation / re-drive. Kin: `transcript-retention-apply-spike` 0.60 (bounded backend spike w/ a destructive DB op) + the memory-formation-* spikes 0.60. Drive-through PASS real chat-v2 + Azure gpt-5.2 (dan): send-1 memory_write (conf 0.6, source none) + auto_extract (conf 0.99) of "Project Helix DT150…" → 1 row (key dd16b505, conf=greatest=0.99, source kept = first writer); send-2 repeat → still 1 row (cross-send); new-session single clean recall. Pre-57.150 = 2-4 rows. If a 2nd `memory-upsert-dedup-spike` diverges > 30% from 0.60, re-point. NEW carryover `AD-Memory-Ops-Emit-Dedup-On-Reaffirm`. CHANGE-117) |
| `memory-session-recall-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.151 ratio ~1.05 IN band; the memory-formation arc's conversation-recall slice — closes `AD-Memory-Formation-Session-Recall` (缺口 2): the arc (57.148/149/150) recalled discrete user FACTS but NOT the conversation arc of a prior session. A Cat-3 FULL vertical slice that FILLS the designed-but-unwired `memory_session_summary` table (Day-0 三-prong MAJOR catch `D-table-already-exists`: plan v0 invented a `memory_session` table; grep found `memory_session_summary` ALREADY created `0007`/designed `09.md:481` with richer cols → REUSE per Check-Existing, saved ~1.5 hr + avoided AP-3 duplicate-table + a wrong direct-RLS migration): additive `updated_at` (migration 0033, revision id ≤32 chars — Day-1 `D-revision-id-len`) + `DBSessionSummaryStore` (upsert on the session_id UNIQUE = one rolling row, mirrors 57.150; `recent_for_user` JOINs `sessions` for tenant+user scope + exclude-current + set_config since sessions is FORCE RLS) + `SessionSummarizer` (cheap-tier structured-JSON, rides the 57.149 post-send BackgroundTask seam, AP-8 allowlisted like extraction.py) + `recent_sessions()` (mirrors 57.148 `profile()`) injected into PromptBuilder + 20 tests. parent-direct agent_factor 1.0. Anchored to `memory-formation-identity-spike` 0.60 (57.148) + `task-primitive-spike` 0.60 (57.140) — same greenfield-Cat-3 + main-flow-wiring + migration shape; the Day-0 reuse-table catch's −1.5 hr was BALANCED by the JOIN read + structured summary + the 3-leg drive-through, and the real-code core (store + summarizer + recall + inject + 20 tests + migration ≥~3.5 hr) HELD the 0.60 per the 57.137 lesson — NOT a tiny-code 0.85. **Landed clean (~1.05)** because the drive-through was textbook (formation visible in DB immediately; recall recited the prior arc verbatim first try; isolation 0-leak first try), NO re-architecture / re-drive. Drive-through STRONG PASS real chat-v2 + Azure gpt-5.2: dan's billing-migration session A → NEW session B recalls it verbatim (Verification 0.98), priya (same tenant) 0 leak. If a 2nd `memory-session-recall-spike` diverges > 30% from 0.60, re-point. CHANGE-118 + design note 54) |
| `memory-formation-combine-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.152 ratio ~1.0-1.05 IN band; a memory-formation arc EFFICIENCY follow-on — combine the two post-send cheap-tier formation calls (57.149 `MemoryExtractor` facts + 57.151 `SessionSummarizer` summary) into ONE combined `chat()` via a NEW `MemoryFormationWorker` that COMPOSES the two existing workers (NOT replace — `SessionSummarizer`'s only non-test caller was the chat path = AP-2/AP-4 orphan risk). Extracted behavior-preserving dispatch halves `MemoryExtractor.write_facts` + `SessionSummarizer.store_summary` (the single-call methods now END with them) → the combined parse feeds the SAME write code; `_form_separate` (env `chat_memory_combined_formation=false`) delegates to the two FULL methods → both stay live. Backend-only NO migration/wire(26)/frontend/loop.py; parent-direct agent_factor 1.0. Anchored to the arc's `memory-formation-identity-spike` 0.60 (57.148) + `memory-session-recall-spike` 0.60 (57.151) — same Cat-3 + main-flow-wiring shape, LIGHTER (no migration/table/recall — reuses ALL of 57.149/151's stores/layers/prompts) but offset by the combined-prompt design + the both-halves drive-through. The 57.137 lesson HELD: the real-code core (worker + 2 dispatch extractions + combined prompt/parse + 10 tests, ≥~3 hr) held the 0.60, NOT a tiny-code 0.85 — UNLIKE the ceremony-heavy re-points (57.120/122/etc.), the code here is a real composition + 2 refactors, and the drive-through ran on-budget (Leg 1 formed both halves first try). The only extra wall-clock was the DB-inspector column-name iteration + the Leg-2 carryover analysis. **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2: one send → a `memory_session_summary` row + `memory_user [auto_extract]` rows at the SAME `15:20:30` timestamp = ONE combined call (unit test proves `chat_call_count==1`); 57.150 dedup coexists. Leg-2 recall (read path unchanged) injected both halves (trace) but the final answer hit 2 PRE-EXISTING carryovers (cross-sprint dan identity conflict + `AD-Verification-Judge-Memory-Inject-Blind`) — NOT 57.152 regressions. If a 2nd `memory-formation-combine-spike` diverges > 30% from 0.60, re-point. CHANGE-119 + design note 55) |
| `memory-formation-combine-ab-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.154 ratio ~0.95-1.03 IN band; closes `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover) — a real-Azure A/B harness measuring whether `MemoryFormationWorker`'s combined single-call formation (57.152) degrades either half's quality vs two focused calls. **ZERO src change**: NEW `benchmark_combined_formation_quality.py` drives the REAL `form()` under both arms via **capturing sinks** (`_CapturingUserLayer`/`_CapturingSummaryStore` — AP-10 safe, the only doubles are the terminal DB writes; build→chat→parse→dispatch is production code) + a **Hybrid oracle** (user-picked via AskUserQuestion: deterministic facts keyword-group coverage + spurious count; LLM-judge summary faithfulness `[0,1]` via a self-contained rubric over the ChatClient ABC, NOT a production `verification/templates/` orphan) + a two-sided verdict + a 10-case golden corpus + 24 CI-safe tests (spy formation+judge clients; `run_arm` drives the REAL worker offline asserting combined=1 / separate=2 chat/case). parent-direct agent_factor 1.0. Anchored to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138) + the sibling `memory-formation-combine-spike` 0.60 (57.152) — same measurement-harness spike shape with a real-code core (~370-line harness + capturing doubles + Hybrid oracle + 10-case corpus + 24 tests ≥~3.5 hr) that held the 0.60 per the 57.137 lesson (NOT a tiny-code 0.85 re-point). **Verdict — 3 real-Azure runs, KEEP combined default ON**: the mechanical single-run verdict FLIPPED on Run 1 (facts_coverage combined 95% vs 100% = exactly −5pp, one case dropping one keyword-group at the float boundary), but re-running 2× → both clean KEEP; the −5pp did NOT reproduce → LLM run-to-run noise. summary tied-to-better (mean Δ +0.009); spurious tied-to-better (0.30-0.40 vs 0.40) → combined ≈ separate quality-equivalent within noise → 57.152 default validated, NO src change. Honest discipline: re-ran to distinguish noise from signal rather than take the single-run FLIP at face value or tune the threshold. If a 2nd `memory-formation-combine-ab-spike` lands > 1.20, re-point toward 0.75 (the real-Azure staging + oracle tuning is the variance risk). CHANGE-121 + design note 57) |
| `memory-vector-recall-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.155 ratio ~1.0 IN band; closes `CARRY-026` Slice 1 — wires the long-stubbed Cat 3 memory `"semantic"` time-scale onto the L4 user layer. A NEW `MemoryVectorIndex` mirrors `KnowledgeVectorIndex` (reuse the `EmbeddingClient` ABC + `QdrantVectorStore` + `QdrantNamespaceStrategy("user_memory")`, all pre-existing) → per-tenant+per-user cosine recall replacing the `[]` stub in `UserLayer.read`; opt-in `MEMORY_VECTOR_ENABLED` (default OFF → byte-identical), lazy ingest-on-search (per-user count-idempotency + `dedup_key` point ids, does NOT touch the 57.150 write path), fail-soft; `QdrantVectorStore.count` gains `payload_filter`. Backend-only NO migration/wire(26)/frontend; parent-direct agent_factor 1.0. Anchored to `knowledge-embedding-vector-spike` 0.60 (57.146 — same new-index + Qdrant + `EmbeddingClient`-ABC-reuse shape) + the `memory-*` spikes 0.60 (57.148/150/151/152/154). Set 0.60 not the pure-wiring 0.55 (`knowledge-per-tenant-isolation-spike` 57.147) because a NEW index + the layer read-branch + the count-filter are real design content beyond wiring; set 0.60 not a tiny-code 0.85 because the real-code core (new index ~155 lines + layer branch + singleton + 17 tests ≥~3.5 hr) held the 0.60 per the 57.137 lesson. Ran CLEAN: Day-0 三-prong 0-drift (1 scope REDUCTION — AP-8 flags only `.chat()`/`.stream()` so the embed/search-only index needs no allowlist), mirrored a proven pattern, drive-through smooth first try (the one mid-run HITL pause on priya was an unrelated 57.106 per-tenant policy). **Drive-through PASS** real chat-v2 + Azure gpt-5.2 + real `text-embedding-3-large` 3072-dim + real Qdrant: machinery LIVE (jamie 5 / priya 2 pts in `tenant_09eb…_user_memory`, Cosine + count-idempotency) + CLEAN per-user isolation jamie↛priya. Honest caveat: Leg-2 recall co-supported by 57.148 `profile()` so the semantic axis's value is proven at the machinery/isolation layer, not the answer (many-fact A/B deferred `AD-Memory-Vector-Recall-Precision-AB`). If a 2nd `memory-vector-recall-spike` (e.g. L1/L2 layers) lands > 1.20, re-point toward 0.70 (the real-Azure-embeddings + real-Qdrant drive-through is the variance driver, per the 57.146 note). CHANGE-122 + design note 58) |
| `medium-backend` | 0.80 | ~0.61 (last-3 ~0.44) | KEEP — 3-consec <0.7 but agent-confound resolved at agent_factor sub-class layer; AD-MediumBackend-AICadence-Recalibration needs human-factor data |
| `medium-frontend` | 0.65 | ~0.54 | KEEP — confound-resolved-at-sub-class-layer; AD-medium-frontend-Baseline-Recalibration |
| `large multi-domain` | 0.55 | 0.81 | KEEP — lower-trigger (3+ consec <0.7) not met |
| `reality-check` | 0.85 | n/a (1 pt) | KEEP pending 2-3 sprint validation |
| `reality-gap-fix` | 0.50 | n/a (1 pt) | KEEP; AD-Sprint-Plan-8 maybe →0.35 |
| `iam-frontend-spike` | 0.60 | n/a (1 pt) | KEEP pending validation |
| `iam-backend-spike` | 0.65 | ~1.08 (3 pt) | KEEP — 57.87 ≈1.0 + 57.105 ≈0.95 (IN band) + 57.112 ≈1.28 (slightly over — the FE component + the D13 drive-through detour vs the prior two's purer-backend shape); single over-point, 3-pt mean ≈1.08 IN band → KEEP; if the next IAM-backend spike WITH an FE component also runs >1.20 propose an `iam-backend-with-fe` sub-class ~0.75 |
| `frontend-arch-spike` | 0.50 | n/a (1 pt) | KEEP; AD-Sprint-Plan-10 maybe split greenfield/reuse-ship |
| `frontend-feature-with-migration` | 0.50 | n/a (1 pt) | KEEP |
| `audit-cycle / docs / template` | 0.40 | 1.13 | KEEP — 3-sprint window complete |
| `frontend-foundation-spike` | 0.50 | n/a (1 pt) | KEEP pending validation |
| `frontend-e2e-sweep` | 0.50 | n/a (1 pt) | KEEP pending validation |
| `frontend-refactor-mechanical` | 0.50 → **0.80** (3rd+ app, AD-Sprint-Plan-13) | ~1.7 | KEEP 0.80; flag 4th data point; if >1.20 →0.90 |
| `frontend-css-engine-hotfix` | 0.60 | n/a (1 pt) | KEEP pending validation |
| `mockup-integration-foundation` | 0.55 | n/a (1 pt) | KEEP |
| `mockup-page-port-with-backend-pairing-and-audit` | 0.60 | n/a (1 pt) | KEEP; if <0.7 recurs →0.40 |
| `frontend-mockup-direct-port` | 0.55 | 0.85 (bimodal) | KEEP; if 3rd bimodal → split token-sweep 0.40 / structural 0.85 |
| `mockup-author-and-port` | 0.70 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.121 ratio ~1.17 IN band; AUTHOR a NET-NEW mockup element (`reference/` styles.css + page-chat.jsx, no prior visual → real design + prototype-verification) + verbatim CSS copy into production + a bounded component re-point (inline-styles→classes + a group header/footer + DROP the eslint-disable escape-hatch) + tests + drive-through, parent-direct agent_factor 1.0. Set 0.70 ABOVE a pure `frontend-verbatim-css-repoint -with-extras` 0.65 because the authoring half has no prior source to copy AND per the 57.120 ceremony-aware insight (a 0.65 would over-commit → ~1.25); the 1.17 landing confirms it. Consistent with 57.120's `chatv2-inspector-existing-field-surface` 0.55→0.85 re-point: mockup/FE-surface sprints with a bounded-but-real code core sit ~0.65-0.85, NOT the 0.45-0.55 pure-repoint range — ceremony is not code-accelerated. If a 2nd `mockup-author-and-port` lands > 1.20, re-point toward 0.85) |
| `harness-loadbearing-gap-fix` | 0.60 → **0.85** (re-pointed Sprint 57.122) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.122 — make an existing write-side feature's read-side load-bearing: a pure decision contract (`decide_tool_hitl`/`resolve_tool_risk` in `_contracts/hitl.py`) + a bounded loop integration (read the ALREADY-wired `get_policy` + apply the decision; `loop.py` `_cat9` only) + multi-tenant tests + a per-tenant-delta drive-through + a semantics design note, parent-direct agent_factor 1.0. 1st pt ratio **~1.8 OVER band** at 0.60 → re-point 0.85. The bottom-up (~6.5 hr) was about right; the 0.60 wrongly assumed acceleration. **Same 57.120 ceremony-not-code-accelerated insight as `mockup-author-and-port`/`chatv2-inspector-existing-field-surface`**: a parent-direct sprint with a real-but-bounded backend core + FULL ceremony (plan/checklist/Day-0/multi-leg drive-through/**design note**/CHANGE/retro) lands ~0.85-1.0, NOT the 0.45-0.65 range — the design-note + drive-through ceremony is fixed-cost. If a 2nd `harness-loadbearing-gap-fix` lands < 0.7 at 0.85, lower again) |
| `frontend-fixture-to-real-data-wiring` | 0.75 → **0.90** (re-pointed Sprint 57.123) | n/a (1 pt) | KEEP 0.90 pending 2-3 sprint validation (Sprint 57.123 — wire chrome fixtures → real `authStore.tenant`: a small backend display-field add (`AuthMeTenant` += plan + region at ALL 3 build sites `me()`/`dev_login()`/`issue_session()`, NO migration) + an auto-threading FE interface (+2 fields; whole-object `set` + hand-written `as` cast → no store/service edit, no codegen) + a 3-component fixture→authStore data-swap (CSS byte-identical) + a UserMenu 3→1 tenant collapse + i18n + 4 tests + a 2-tenant drive-through, parent-direct agent_factor 1.0. 1st pt ratio **~1.33 OVER band** at 0.75 → re-point 0.90. Same 57.120/57.122 ceremony-not-code-accelerated insight: full-ceremony parent-direct (plan/checklist/Day-0 三-prong/multi-leg drive-through/CHANGE/retro) lands ~0.85-1.0 even for bounded mechanical FE code; the Risk Class E orphan-worker detour added wall-clock too. If a 2nd lands < 0.7 at 0.90, lower again) |
| `frontend-mockup-fidelity-audit` | 0.85 | n/a (1 pt) | KEEP; if recurs →0.45-0.55 |
| `frontend-mockup-strict-rebuild` | 0.60 | ~0.63 | KEEP — agent-confound resolved at agent_factor sub-class layer |
| `frontend-foundation-token-correction` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-foundation` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-repoint -simple` | 0.50 | ~1.0 | KEEP (criteria: ≤3 files / no AP-2 banner / no dual-mount / no playback widgets / oklch bump <4) |
| `frontend-verbatim-css-repoint -with-extras` | 0.65 | ~1.04 | KEEP (criteria: any of multi-file >3 / AP-2 banner / dual-mount / playback widgets / oklch bump ≥4) |
| `frontend-page-bug-fix` | 0.45 | n/a (1 pt) | KEEP; if >1.20 recurs →0.55-0.60 |
| `mixed-multidomain-bundle` | 0.65 | ~0.9-1.0 (latest 57.124) | KEEP — 57.124 (3 tracks: Cat 2/9/1 PermissionChecker-removal + destructive-floor + admin-validator + FE-DEMO) ratio ≈1.0-1.1 IN band, parent-direct agent_factor 1.0 (the PermissionChecker test-surgery 10-removed/+17-new + the Risk-E restart offset the GREEN Day-0 D-escalate-coverage); 57.107 B3 (4 tracks) ≈0.8-0.9 also IN band; prior 0.42 mean was the agent-confound era |
| `subagent-child-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.94 ratio ~0.93 IN band; Cat 11 new-domain spike, parent-direct) |
| `subagent-sse-relay-wiring` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.95 ratio ~0.9-1.0 IN band; Cat 11→12 backend composition wiring, parent-direct) |
| `chatv2-transcript-persistence-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.125 ratio ~1.0 IN band; backend SSE-stream persistence observer mirroring the proven 57.107 `_persist_subagent_transcript` + a sibling read endpoint mirroring `get_state_snapshot` — reuses an existing table/partitions/serializer, NO migration; parent-direct agent_factor 1.0. Closest: `subagent-sse-relay-wiring` 0.55 + the read-endpoint half → 0.60. The Day-0 re-scope (the AD's literal scope was already shipped by 57.107) added discovery time but SAVED building the wrong thing → net ~commit. If a 2nd such sprint diverges > 30% from 0.60, re-point) |
| `chatv2-history-replay-fullstack` | 0.60 → **0.85** (re-pointed Sprint 57.126) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.126 — the 57.125 arc's frontend half, but Day-0 三-prong flipped it frontend-only → full-stack: the foundation was incomplete (user prompts persisted NOWHERE — state_data EXCLUDES messages, messages table no writer) → a small backend writer completion (`_max_main_seq` MAX-seed multi-turn ordering fix + a per-send `user_message` row, reuses `_persist_main_event`) + a frontend replay feature (`fetchSessionEvents` + `loadSessionHistory` replaying `/events` through the EXISTING `mergeEvent` + a new persist-only `user_message` case + the SessionList click rewire), ZERO new CSS / wire 24 / no migration. Parent-direct agent_factor 1.0. **1st pt ratio ~1.43 OVER band at 0.60 → re-point 0.85.** Same 57.120/57.122/57.123 ceremony-not-code-accelerated insight: a full-ceremony parent-direct sprint WITH a mandatory multi-step drive-through + a Day-0 dead-end re-scope (Option C investigated then proven non-viable, ~2-2.5 hr — but it PREVENTED building Option C wrong) has a large fixed cost the 0.60 wrongly assumed code-hour acceleration would absorb. The bounded code (1 backend helper + a 2-line writer add + 4 FE files) does NOT pull the commit down to the 0.55-0.60 pure-wiring range when the ceremony + drive-through + investigation dominate. If a 2nd full-stack-chatv2 sprint lands < 0.7 at 0.85, lower again) |
| `chatv2-multiturn-rehydration-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.127 ratio ~0.98 IN band; the fix for the 57.126 drive-through-surfaced bug — a follow-up send started `loop.run()` with no prior turns. A NEW provider-neutral `MessageStore` ABC (sibling to `Checkpointer`) + `DBMessageStore` (load order-by-seq / append seq-from-MAX / best-effort SAVEPOINT / tenant-scoped) + serde relocated to `_contracts/message_serde.py` + the loop self-loads prior at `run()` start + persists user-prompt + final-answer (the FINAL branch yields end_turn WITHOUT appending the answer → a Day-1 de-risk dropped the plan's side-list for a simpler 2-point persist) + a `make_chat_message_store` factory + `build_handler` wiring, parent-direct agent_factor 1.0. `loop.run()` ABC signature UNCHANGED. Closest: `subagent-child-loop-spike` 0.60 + `verification-in-loop-spike` 0.60 (both new-domain loop.py-core touches reusing a proven injected-ABC). UNLIKE the 57.126 `chatv2-history-replay-fullstack` 0.85 re-point — this is a PURE-backend spike (no FE / no mandatory dead-end re-scope), so the new-ABC + persist-precision land it at 0.60 not the ceremony-heavy 0.85. The Day-0 NET scope-reduction (drop migration + side-list) offset the serde-relocation + factory work. If a 2nd `chatv2-multiturn-rehydration-spike` diverges > 30% from 0.60, re-point) |
| `chatv2-resume-persistence-wiring` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.128 ratio ~1.13 near band-top IN band; closes AD-ChatV2-Resume-Transcript-Persistence — the HITL resume generator `_stream_resume_events` omitted the `_persist_main_event` call its send-path sibling has, so a paused-then-resumed session's replay stopped at the pause. Pure-backend mirror-wiring: thread `db`/`tenant_id`/`session_id` into `_stream_resume_events` + persist each post-resume event (seq seeded from `_max_main_seq`, best-effort, no `user_message` row) — 1 file EDIT (`router.py`) + 1 test, NO new event type / wire / codegen / frontend / migration, `loop.py` untouched (the 57.127 `messages` ledger already covers resume). Parent-direct agent_factor 1.0. Closest: `subagent-sse-relay-wiring` 0.55; lighter than `chatv2-transcript-persistence-spike` 0.60 (which BUILT the observer). The CODE is tiny (~12 lines) but the **HITL drive-through SETUP dominated** wall-clock (admin policy PUT + escalating-tool pause trigger + approve + reload + replay) — exactly the ceremony-floor pattern; that's the variance source. If a 2nd `chatv2-resume-persistence-wiring` (or HITL-drive-through sprint) lands > 1.20, re-point toward 0.65) |
| `chatv2-ledger-tool-roundtrips-wiring` | 0.55 → **0.85** (re-pointed Sprint 57.129) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.129 — closes AD-ChatV2-Ledger-Tool-RoundTrips, the 57.127 carryover: the `messages` Cat-3 ledger persisted ONLY the user prompt + final answer, so a follow-up rehydrated `[user, final-answer]` but NOT the intra-turn `assistant tool_use` + `tool` result. Option A incremental per-turn-batch persist: in `_run_turns`'s `TOOL_USE` branch `_tool_batch_start = len(messages)` before the assistant append + `_persist_to_ledger(messages[_tool_batch_start:], turn_num)` after the post-tool checkpoint — one atomic batch reached ONLY when well-formed → early-return paths skip → dangling-free. PURE backend 1 src EDIT `loop.py` + 1 test EDIT, reuses `DBMessageStore.append`+`message_serde`, NO new helper/ABC/event/wire 24/codegen/frontend/migration, final answer still end_turn-only (57.127 untouched). Parent-direct agent_factor 1.0. **1st pt ratio ~1.9 OVER band at 0.55 → re-point 0.85.** The CODE+tests were on-budget (~1.5 hr, ~2-line change); the over-run was the Day-3 drive-through (clean restart + HITL-policy setup so python_sandbox auto-runs in-loop + multiple real-LLM cycles + DB verify + a content-filter false-alarm investigation ~1-1.5 hr; even excluding that, base drive-through → ~1.35). Same ceremony-not-code-accelerated insight as 57.120/122/123/126: a tiny-code, full-ceremony, parent-direct sprint WITH a mandatory drive-through lands ~0.85-1.0, NOT the 0.45-0.55 band — the drive-through ceremony (here amplified by HITL setup + the recall-prompt content-filter chase) is the cost driver. Drive-through PASS session 9150a32f: turn 1 python_sandbox auto-run stdout=333221→"ODD"; turn 2 innocent "add 7 to that number"→"333228" (rehydrated tool result + 7, POST only {message,session_id}); DB 6 rows incl. seq-2 tool_calls + seq-3 tool result. If a 2nd `chatv2-ledger-tool-roundtrips-wiring` lands < 0.7 at 0.85, lower again) |
| `chatv2-resume-ledger-persist-wiring` | 0.70 → **0.85** (re-pointed Sprint 57.132) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.132 — closes AD-ChatV2-Resume-Tool-RoundTrips + sibling held-answer gap, comprehensive scope: the HITL **resume path** appends its out-of-loop messages (a paused-then-approved tool's round-trip; an output/verification held answer) to the buffer but never persisted them to the `messages` ledger — the 57.129 send-path fix lives INSIDE `_run_turns`. 2 `loop.py` persist call sites: Leg-1 in `resume()` tool-kind APPROVED (backward-scan last assistant → persist `[assistant tool_use, *tool results]`, mirrors 57.129 atomic batch, REJECTED/undecided return earlier → dangling-free); Leg-2 in `_replay_approved_output` (persist the held answer, output+verification APPROVE). PURE backend 1 src + 1 test, +4 unit tests, NO new ABC/event/wire 24/codegen/migration/frontend. parent-direct agent_factor 1.0. Between 57.128 `chatv2-resume-persistence-wiring` 0.55 (1 leg, message_events) and 57.129 `chatv2-ledger-tool-roundtrips-wiring` 0.85. **1st pt ratio ~1.4-1.6 OVER band at 0.70 → re-point 0.85.** Same ceremony-not-code-accelerated insight as 57.120/122/123/126/129: tiny code (~10 lines, on-budget) but a mandatory HITL drive-through (policy setup + pause→approve→resume→follow-up→2×DB-verify) + a Leg-2 output-escalate dead-end (real-LLM trigger non-deterministic / content-filter-prone, didn't fire) dominated wall-clock. Drive-through: Leg-1 FULL PASS (session 02fa6bfb — seq-2 assistant tool_use + seq-3 tool result persisted AT RESUME; follow-up "0.031" from `duration_seconds` un-deducible from "ODD" → rehydration proven, messages_count 4→5→8); Leg-2 unit + composition verified (NOT UI-driven, honest; carryover AD-ChatV2-Resume-Replay-Drive-Through). If a 2nd lands < 0.7 at 0.85, lower again) |
| `chatv2-userstop-resume-durability` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.143 ratio ~1.0 IN band; closes `AD-UserStop-Resume-Context` (Scope B full CC parity) — full-stack durability fix: US-1 `DBMessageStore` own-session-per-call (ctor `db_session`→`session_factory` + `_set_tenant` `set_config('app.tenant_id')` for FORCE-RLS `messages` + `append()` immediate commit, mirrors `transcripts/retention.py:91-93`; `make_chat_message_store`→`get_session_factory()`) so the interrupted-run user prompt + completed tool batches survive the client-disconnect `CancelledError` request-session rollback (`get_db_session` rolls back on ANY exception, `session.py:54-56`); `loop.py` UNTOUCHED — the turn-0 persist becomes durable for free. US-2 `cancel_session` persists an `assistant` `[Request interrupted by user]` marker via a self-contained `DBMessageStore` (best-effort, never fails the 204) + chat-v2 `cancel()` → `abort()` + `void cancelSession(sid)` (`POST /sessions/{id}/cancel`). parent-direct agent_factor 1.0. Day-0 dropped synthetic tool_results (57.129 atomic-batch ⇒ no dangling tool_use) + the cancel-handler DB dep (self-contained store) — both scope reductions. Closest kin: `chatv2-resume-persistence-wiring` 0.55 (57.128) + `chatv2-ledger-tool-roundtrips-wiring` (57.129) — same chatv2 ledger-durability family, but this is bigger (own-session refactor + RLS + cancel handler + FE + a test-isolation rewrite to committed-seed/CASCADE-cleanup) so 0.60 over the 0.55 wiring entries. **The plan's ceremony-risk did NOT fire** — UNLIKE the tiny-code 0.85 re-points (57.120/122/123/126/129/132), the Stop-mid-run drive-through went smoothly (dev-login UI + Playwright + a long-essay prompt gave a wide mid-run window, caught first try) AND the core is real code (≥~3 hr), so the 0.60 spike multiplier held (57.137 lesson). Drive-through PASS real Azure gpt-5.2 (session 35789e63): DB ledger seq5 = interrupted essay prompt DURABLE (survived Stop, pre-57.143 absent) + seq6 = marker; "continue" rehydrated 19 msgs → continued the ORIGINAL computing-essay task (write_todos), NOT "continue from what?". CHANGE-110 + design note 47. If a 2nd `chatv2-userstop-resume-durability` (or a HITL/Stop-drive-through-heavy chatv2 sprint) lands > 1.20, re-point toward 0.85) |
| `subagent-child-turnstream-nesting` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.96 ratio ~0.9-1.1 IN band; Cat 11×12 multi-layer feature — new wrapper event + executor forward + frontend store/render, parent-direct) |
| `chatv2-fatal-terminate-wire-surface` | 0.55 | n/a (1 pt) | KEEP single-data-point (Sprint 57.130 ratio ~1.29 slightly OVER band-top; closes AD-LoopTerminated-Wire-Surface — cross-stack surfacing of an EXISTING Cat-8 event: `sse.py` serializer branch + `WIRE_SCHEMA` 24→25 + codegen regen + `mergeEvent` `loop_terminated` case (flip dangling pending ToolBlock→error + `terminated` `.badge.danger` + status terminal) + AgentTurn badge, parent-direct agent_factor 1.0. The cross-stack CODE was on-budget; the over-run = the **drive-through trigger hunt** (python_sandbox always returns success=True so it can't trigger; had to trace the Cat-8 FATAL-classification path + find that `web_search` RAISES on unset BING key) + 2 Day-0-missed wire-count drifts (codegen `WIRE_TYPE_TO_INTERFACE` map + 3 hardcoded count-test locations). Closest: `frontend-feature-with-event-wire-addition` 0.55 (3-pt ~1.07) but those added a FIELD not a new event TYPE; `loop-injection-primitive-spike` 0.55 added a new TYPE too but ALSO built a backend primitive (this is lighter on backend). Rollback needs 2 consec >1.20 → KEEP 0.55; if a 2nd `*-wire-surface` sprint lands >1.20, re-point toward 0.65 — the drive-through-staging cost is under-priced for "surface an existing event" sprints. Reinforces AD-DriveThrough-Deterministic-Tool-Trigger 57.122) |
| `multi-model-profile-spike` | 0.55 | ~1.0 (2 pt) | KEEP — 57.97 ~0.93 + 57.109 ~1.1-1.2 both IN band (2-consec). Shape: a ChatClient consumer retiered to cheap + cost attribution + drive-through, parent-direct (57.109 C2: compaction retier + `_compaction` ledger mirror + 2 env knobs; the upper-edge ratio = the dt discovery loop — D-DAY3-1 semantic-unreachable finding forced a knob pivot) |
| `subagent-child-governance` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.110 B4 ratio ~1.1-1.2 IN band upper edge; Cat 11×9×8 composition over the proven child-loop machinery — engine injection via closure (`loop.py` diff 0) + failure-policy contract field + C3-policy mirror + thin FE label + 2-leg dt, parent-direct agent_factor 1.0; the upper-edge over-run = the dt discovery loop: D-DAY3-1 popen deny-list fix-forward + re-drive + D-DAY3-2 LoopTerminated terminal-shape pin — same dt-loop shape as 57.109) |
| `verification-in-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.98 ratio ~0.92 IN band; Cat 1×10×7×12 loop.py-core new-domain spike — in-loop verify gate + durable counter on checkpoint metadata + wrapper retire + drive-through, parent-direct; agent_factor 1.0) |
| `verification-context-hygiene-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.136 ratio ~1.0 IN band; closes `AD-Verification-Retry-Context-SelfConditioning` (research #6) — an evidence-first thin spike: parameterize the in-loop verification correction branch (`loop.py:2645`) via `correction_context_strategy` ∈ {`keep` default = byte-identical / `summarize` = drop the failed answer to break self-conditioning} + env wire (`CHAT_VERIFICATION_CORRECTION_STRATEGY`, per-tenant OUT anti-AP-6) + a permanent real-LLM A/B harness (`benchmark_correction_hygiene.py` mirrors `benchmark_judge.py`; REPRODUCES the 2645 two-construction WITHOUT the full loop). A/B verdict KEEP (real Azure 10×2: repeat −0.043 / tokens −17.2 / both 100% retry-pass → directionally real but < 5% materiality → keep default, summarize env lever, #6 low-risk at 2-turn). Backend-only NO migration/wire/frontend. parent-direct agent_factor 1.0. Closest kin: `verification-in-loop-spike` 0.60 (57.98) + `verification-trace-and-benchmark-spike` 0.60 (57.111) — both loop.py-core verification touches paired with a measurement script; the Day-0 三-prong NET-washed scope (D-azure-role-pairing RESOLVED → drop-only −5% vs D-benchmark-anchor drive-a-correction-cycle +5%) so the 0.60 held cleanly. UNLIKE the ceremony-heavy re-points (57.120/132 etc.), this is a real-code spike (loop branch + config wire + a 200-line A/B harness + 18 tests) where the 0.60 bottom-up haircut fit — NOT a tiny-code full-ceremony sprint. If a 2nd `verification-context-hygiene-spike` diverges > 30% from 0.60, re-point) |
| `verification-keycondition-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.138 ratio ~0.98 IN band; closes `AD-Verification-KeyCondition-PerTask` (research #8) — an evidence-first thin spike: a NEW `key_condition.txt` judge template (extract per-task must-satisfy conditions → check each → generic floor; superset, same `{output}`/`{trace}`/JSON contract) selectable via the EXISTING `chat_verification_judge_template` lever (DEFAULT unchanged) + a permanent real-Azure A/B harness (`scripts/benchmark_key_condition.py` mirrors `benchmark_judge.py` + 11-case corpus + 9 CI tests). A/B verdict: instruction_violation 83%→100% (gain +16.67pp) BUT fp 20% + ~1.8× tokens → net accuracy tie → does NOT clear gain≥30%/fp≤20% → keep output_quality default, key_condition opt-in (the generic judge is less blind than theory ∵ A3 trace-awareness infers contradicts-trace). **ZERO src code change** — `list_templates()` globs `*.txt` (Day-0 dropped the planned `__init__.py` edit); the template is a data file + the lever pre-exists. Backend-only NO loop.py/config/handler/migration/wire/frontend, parent-direct agent_factor 1.0. Closest kin: `verification-context-hygiene-spike` 0.60 (57.136) + `verification-trace-and-benchmark-spike` 0.60 (57.111) + `verification-in-loop-spike` 0.60 (57.98). LIGHTER on src than 57.136/137 (no loop.py/config) but the harness (~3 hr) is a real-code core → the 0.60 held (57.137 lesson: a >~3 hr real implementation core holds the spike multiplier; only a ~10-line surface change wrapped in full ceremony needs ~0.85). If a 2nd `verification-keycondition-spike` diverges > 30% from 0.60, re-point) |
| `task-primitive-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.140 ratio ~0.95-1.0 IN band; closes research #1 `Explicit task primitive` (eval `task-primitive-thin-spike-eval-20260618.md`) — a full vertical slice (NOT a measurement-harness spike like the #136-139 kin): Cat 2 `write_todos` tool (replace-whole-list, `risk=LOW`+`destructive=False`+`additionalProperties:False` → auto-pass any tenant policy; opt-in in `make_default_executor` mirrors skills 57.113) + Cat 3/7 `session_todos` table (migration 0031, RLS mirror 0030) + `DBTodoStore` (upsert, mirrors DBMessageStore 57.127) + `Todo` contract + Cat 5 plan-first nudge + Cat 1 (loop.py 2 edits) run-start `## Active Plan` re-injection in `loop.run()` ASYNC (build_real_llm_handler is SYNC so the dynamic load can't live in the handler — D-loop-runstart-inject) + `TodosUpdated` emit after write_todos + Cat 12 `todos_updated` wire event (6-file 25→26) + chat-v2 Inspector 5th "Todos" tab (existing mockup classes → styles-mockup.css byte-identical). ~28 files. parent-direct agent_factor 1.0. **Anchored to `skills-system-spike` 57.113 (0.60)** — same greenfield-module + builtin-tool + main-flow-wiring shape — but at the UPPER edge (this ALSO has a migration AND a new wire event AND a panel, which 57.113 lacked); the 0.60 held because every pipeline had a recent precedent (store↔DBMessageStore, tool↔memory_tools, wire↔loop_terminated, panel↔Inspector tabs) so the bottom-up haircut fit despite the larger surface. **Drive-through STRONG PASS** (real Azure gpt-5.2: send 1 proactive write_todos 3 items → 3/3; send 2 cross-send rehydrated 3 + added 4th → 4/4 — AP-4 ignores-the-list FALSIFIED). UNLIKE the tiny-code 0.85 ceremony re-points (57.120/122/123/126/129/132), this is a real-code full-stack slice where the spike multiplier fit. If a 2nd `task-primitive-spike` (e.g. the DAG follow-on) lands > 1.20, re-point toward 0.70. CHANGE-107 + design note 44) |
| `task-primitive-dag-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.156 ratio ~0.95-1.0 IN band; the DAG follow-on the 57.140 `task-primitive-spike` row predicted — evolves the LINEAR `write_todos` into a dependency DAG: `Todo.depends_on` end-to-end (tolerant serde + `ready_todos` direct-dependency/cycle-safe/unknown-dep-ignored + dependency-aware `## Active Plan` `(ready)`/`(blocked by:…)` render, byte-identical when no dep) + `write_todos` schema `depends_on` + chat-v2 Todos panel "⤷ needs" line + `blocked` badge. **Guidance not enforcement** (renders ready/blocked, never blocks the agent — the 57.140 nudge-not-force pattern). Rode the 57.140 machinery serde-transparently → NO migration/wire schema(26)/codegen/loop.py/sse.py/store change (backend delta 2 files `_contracts/todo.py`+`tools/todo_tools.py` + 2 FE `chatStore.ts`+`InspectorTodos.tsx`); parent-direct agent_factor 1.0. Anchored to `task-primitive-spike` 0.60 (57.140, its parent) but LIGHTER (that built the whole primitive greenfield incl. migration/table/wire/event/panel; this REUSES all of it — the delta is a contract field + serde + topological helper + render redesign + FE mirror). The 0.60 held (NOT a tiny-code 0.85 re-point) because the real-code core (readiness logic + tolerant serde + render + FE mirror + 19 tests ≥~3.5 hr) HELD it per the 57.137 lesson AND the drive-through ran on-budget (both legs first try, no re-drive) — the Day-0 prediction that loop.py/sse.py/wire/store/migration stay UNTOUCHED held exactly, so serde-transparent reuse kept the surface small. **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2 (trace `743c72d4…`): Leg 1 agent authored a real DAG (`2→[1]`,`3→[1]`,`4→[3]`,`5→[4]`), the `todos_updated` wire carried `depends_on` (sse.py UNCHANGED confirmed live), identified the ready root, panel rendered blocked badges + "⤷ needs" lines; Leg 2 completing step 1 LIVE-unblocked steps 2+3 while 4+5 stayed blocked. If a 2nd `task-primitive-dag-spike` lands > 1.20 (drive-through-dominated), re-point toward 0.70. CHANGE-123 + design note 59) |
| `scheduler-cross-burst-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.157 ratio ~1.15-1.3 near/slightly-over band top; closes `AD-TaskPrimitive-Scheduler-Phase58` (research #3, the task-primitive range's flagship in the engine-debt program kickoff) — a **guidance-not-enforcement** cross-burst scheduler: when a chat `real_llm` burst ends at `max_turns=8` with an unfinished `write_todos` plan, the SSE generator auto-continues the loop for the next bounded burst (driven by a `CONTINUATION_NUDGE` user turn) instead of forcing a manual "continue" — the fix for the reality-audit §9 long-lived-agent 5% `max_turns=8` ceiling. NEW `orchestrator_loop/scheduler.py` pure `should_continue_plan()` 4-condition AND predicate + a `_scheduled_loop_events` chaining generator in `router.py` yielding `(event, swallow)` (the existing `async for` gains 3 `if not _swallow` guards) + 2 default-OFF settings; billing every burst / quota·SLA·audit·handoff final-burst-only (Day-0 MAJOR drift `D-router-loopcompleted-shape` — repeated quota reconcile of the same reservation would over-release). NO migration/wire(26)/codegen/frontend/`loop.py` change — continuation rides the FREE 57.127 ledger + 57.156 `## Active Plan` rehydration. parent-direct agent_factor 1.0 (3-segment). Anchored to `task-primitive-spike` 0.60 (57.140) / `verification-in-loop-spike` 0.60 (57.98) / `loop-injection-primitive-spike` 0.55 (57.101) — same Cat-1 loop-core-adjacent new-mechanism + main-flow-wiring shape; set 0.60 not a tiny-code 0.85 because the real-code core (predicate + router outer-loop + swallow control-flow + 18 tests ≥~3.5 hr) held the 0.60 per the 57.137 lesson. The near/slightly-over landing = the drive-through env-resolution detective work (a first-session cost — the app's real DSN is `…/ipa_v2` not the `.env` `DB_NAME=ipa_platform`; container role `ipa_v2` not `postgres`; a trace-id grep-order bug in the first poll), NOT the feature/a re-drive. **Drive-through STRONG PASS** real chat-v2 + Azure gpt-5.2: ON = 1 POST → 15 gpt-5.2 turns / 2 bursts under one trace (LOOP 14 turns, one continuous stream), the `messages` ledger shows the scheduler-injected `CONTINUATION_NUDGE` user turn between bursts (`13:38:33`, DB count 1), Todos 12/12 completed with NO manual continue, Verification 0.98, billing `materialized=15`; OFF (control) = same prompt → 8 completions / 1 burst, `stop_reason=max_turns`, plan 7/12 unfinished, no nudge injected, billing `materialized=8` (byte-identical single-burst). 850 chat regression OFF byte-identical. If a 2nd `scheduler-*-spike` lands > 1.20 (drive-through-dominated), re-point toward 0.70. CHANGE-124 + design note 60) |
| `memory-vector-recall-precision-ab-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.158 ratio ~1.0-1.05 IN band; closes `AD-Memory-Vector-Recall-Precision-AB` (CARRY-026 semantic-axis follow-on) — an evidence-first A/B measurement spike settling 57.155's honest gap: does the semantic vector axis actually out-recall confidence-ranked `profile()` at many-fact scale? **ZERO `src/` change** — a 3-arm harness (`profile` confidence-desc / `keyword` substring / `semantic` the REAL `MemoryVectorIndex.search`; all rank the case's `MemoryRow` list — `search(rows=…)` takes rows as a param → DB-free) + a discriminating 10-case corpus (8/10 gold-low-conf-outside-top-5 + question-query non-substring so both baselines miss) + a CI-safe offline test (importlib-shadow + re-inlined `_FakeMemStore` + `DeterministicEmbeddingClient` — machinery/oracle/discrimination only, the semantic win is real-Azure-only ∵ hash embeddings have no semantic structure). parent-direct agent_factor 1.0. Anchored to `memory-formation-combine-ab-spike` 0.60 (57.154 — same real-Azure A/B harness + golden corpus + two-sided-verdict shape) + `verification-context-hygiene-spike` 0.60 (57.136); the real-code core (harness + oracle + corpus + 17 tests ≥~3.5 hr) held the 0.60 per the 57.137 lesson. Ran CLEAN: Day-0 0-drift (every double/scaffold/idiom pre-existed), a single smooth real-Azure run (no re-drive — embedding cosine is deterministic, UNLIKE 57.154's stochastic LLM-judge). **Verdict semantic-wins (decisive)**: real `text-embedding-3-large` + real Qdrant → semantic recall@k **100%** (MRR 1.0 = gold always first) vs profile **20%** vs keyword **10%** (semantic − profile **+80pp** ≫ 10% materiality). Honest caveat: the corpus is discriminating but NON-adversarial (single clear gold per case) → the recall@k win is robust but precision@k under distractors is a follow-on (`AD-Memory-Vector-Recall-Adversarial-Corpus`). If a 2nd `*-ab-spike` lands > 1.20, re-point 0.75. CHANGE-125 + design note 61) |
| `chatv2-compaction-drivethrough-surface` | 0.85 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.159 ratio ~1.06 IN band; raises Cat 4 compaction L2→L3 — surfaces the already-wired `context_compacted` as a persistent chat-v2 timeline marker (`CompactionMarkerTurn` in the `Turn` union + a `context_compacted` store case pushing it, mirrors the `message_injected` pseudo-turn + `.badge.warning` chip — fills the 57.66 deferred A-5c; the event was loop→sse→wire→store wired, only the render was missing → **FE-only ZERO backend/wire/codegen**) + a MANDATORY live compaction drive-through. parent-direct agent_factor 1.0. Anchored to `chatv2-inspector-existing-field-surface` 0.85 (57.120/131/133) — surface an already-store-captured wire field in a NEW render location, tiny-code + full-ceremony + parent-direct + MANDATORY drive-through = ceremony-dominated not code-accelerated (the 57.120 generalizable insight). Slightly heavier than the KV-row surfaces (a new turn variant + component + a long-conversation drive-through + a `keep_recent=1` backend restart to expose the reduction cutoff) but offset by the FE-only surface, so the 0.85 held. **Drive-through PASS** real chat-v2 + Azure gpt-5.2: marker renders live (no-op `4,086→4,086` … `35,144→35,144` on a long tool-using send + a REAL `4,604 → 1,770 tokens (hybrid · 8 msgs)` −62% at `keep_recent=1`) + context retained after compaction (Aurora/Oracle→Postgres/NUMBER(38,4) 0.99 + Beacon/October/Lodestar 0.99). **L2→L3 finding**: compaction TRIGGERS every over-budget turn but 0-REDUCES on the single-user-turn chat path (`user_indices > keep_recent` unreachable → context grows 4k→35k) — NOT a correctness bug (retention 0.99) → carryover `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`. If a 2nd `chatv2-compaction-drivethrough-surface` lands > 1.20 (long-conversation drive-through staging is the variance driver) re-point toward 1.0. CHANGE-126, no design note (existing-field-surface + drive-through)) |
| `passk-reliability-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.141 ratio ~1.0 IN band; closes `AD-Eval-PassK-Reliability-Harness` (research #2, Cat 12) — V2's first repeatability eval: a pure-offline `scripts/benchmark_pass_k.py` (mirrors `benchmark_judge.py` 57.111) running the SAME corpus input through V2's own `AgentLoopImpl.run()` k times, computing 4 axes (pass^k vs pass@1 + divergence · behavioral consistency · λ fault-injection via `_FaultInjectingChatClient` wrapping the ChatClient ABC · ε perturbation) with a hybrid oracle (rules inline normalized contains/exact + `LLMJudgeVerifier(profile.cheap, per-case-criterion raw template)`). 3 NEW files **ZERO src edit** (WRAPS the existing ChatClient/Verifier/AgentLoop ABCs; loop DB-less drivable per Day-0; direct-construct AgentLoopImpl ∵ the factory takes no chat_client param) + 12-case difficulty-graded corpus + 17 CI tests (spy ChatClient drives the REAL loop offline). NO migration/wire(stays 26)/frontend/loop.py-edit. Drive-through real Azure gpt-5.2 (12 cases · k=3 · 90 runs · 94k tok): pass^k 100%=pass@1 100% (divergence 0% — corpus too easy to stress the τ-bench pass^8<25% regime, VALID either-direction verdict) BUT answer-consistency 75% + λ-degradation 50% (no chat-level retry) surfaced — 2 pass@1-invisible signals = the payoff. parent-direct agent_factor 1.0. Closest kin: `verification-trace-and-benchmark-spike` 0.60 (57.111) + `layered-compaction-spike` 0.60 (57.139) + the #136-139 measurement-harness spikes — same Cat-12/10 greenfield-benchmark-script + golden-fixture shape; the 57.137 lesson held (a >~3 hr real implementation core — 4-axis + fault wrapper + corpus + 17 tests — holds the spike multiplier, NOT a tiny-code 0.85 re-point). If a 2nd `passk-reliability-spike` lands > 1.20, re-point toward 0.75 (the 4-axis breadth is the variance risk)) |
| `otel-genai-semconv-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.142 ratio ~0.95-1.0 IN band; closes `AD-Observability-OTel-GenAI-Schema` (research #5, Cat 12) — a translation-at-tracer layer mapping V2's bespoke OTel span names + attr keys to CNCF `gen_ai.*`. **Day-0 reframe**: the OTel SDK is ALREADY real (`opentelemetry-*==1.22.0` + OTLP/Prometheus) → the gap is ONLY the bespoke SCHEMA, NOT an adoption. NEW `_genai_semconv.py` (pure: STOP_REASON→finish_reason · span_type→operation · attr renames · `to_genai_span`/`assert_genai_conformant`) applied in `OTelTracer._span_cm` at start+close; the close-time `set_attributes` re-read **fixes a discovered latent bug** (post-response token attrs never reached real exported spans — only the by-ref test RecordingTracer saw them). 1-line `loop.py` finish_reason (decision B2); dual-view (internal/test bespoke, exported `gen_ai.*`) → loop.py + existing obs tests UNTOUCHED. NEW `benchmark_otel_conformance.py` (real `InMemorySpanExporter`, synthetic CI-safe + `--real` Azure) + corpus + 18 CI tests. NO migration/wire(26)/frontend/17.md-contract; pytest 2877+5skip · mypy 0/381 · llm_sdk_leak 3/3. Drive-through real Azure gpt-5.2: production-path `chat gpt-5.2` span carries gen_ai.operation.name + request.model + usage.input/output_tokens (latent bug FIXED on real path) + response.finish_reasons; GenAI 2/2 conformant 100%. parent-direct agent_factor 1.0. Closest kin: `verification-trace-and-benchmark-spike` 0.60 (57.111) + `layered-compaction-spike` 0.60 (57.139) + `passk-reliability-spike` 0.60 (57.141) — Cat-12 schema/measurement spike with a real-code core (mapping + tracer + harness + 18 tests) that holds the 0.60 (57.137 lesson). content-capture + `gen_ai.provider.name` deferred (Phase58 ADs). If a 2nd `otel-genai-semconv-spike` diverges > 30% from 0.60, re-point) |
| `layered-compaction-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.139 ratio ~0.97 IN band; closes `AD-Context-Layered-Compaction-ACON` (research #4, Cat 4) — an evidence-first thin spike: a NEW LLM-free `PreClearCompactor` (standalone tool-result clear at a LOWER trigger, reuses `DefaultObservationMasker`, real token-reduction-ratio `tokens_after` fixing structural's message-count-ratio blindness) + a `ChainedCompactor` (preclear→hybrid, threads state to defer semantic; `loop.py` UNTOUCHED — single `compact_if_needed` call site) + a default-OFF env lever `CHAT_COMPACTION_PRECLEAR_RATIO` (factory returns the bare HybridCompactor when unset = byte-identical) + a permanent per-layer yield harness (`scripts/benchmark_layered_compaction.py` mirrors `benchmark_sandbox_escape.py` + 6-spec corpus + 13 CI tests). A/B verdict (real Azure 6 cases): mean tool_clear_reduction 33.72% IN ACON band [26-54%] (captures ~83% of total yield free) + semantic_deferred_rate 66.67% → keep default OFF, preclear = selectable opt-in (composition-dependent + the user-anchored masker NO-OPs single-send). Backend-only NO migration/wire/codegen/frontend, parent-direct agent_factor 1.0. Closest kin: `verification-in-loop-spike` 0.60 (57.98) + `guardrail-restrict-spike` 0.60 (57.137) + `verification-keycondition-spike` 0.60 (57.138) — a Cat-spike measurement-harness + bounded-lever shape; the harness + 2 new compactors are a real-code core ≥3 hr so the 0.60 held (57.137 lesson). LIGHTER on Azure than #136/#138 (the ACON-band core L0/L1/L2 is LLM-free). If a 2nd `layered-compaction-spike` diverges > 30% from 0.60, re-point) |
| `verification-memory-grounding-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.153 ratio ~1.0 IN band; closes `AD-Verification-Judge-Memory-Inject-Blind` — make the in-loop Cat 10 judge memory-aware, the direct parallel of 57.111 A3 (`{trace}`): a NEW `TransientState.injected_memory` field + a `build_memory_block` helper (`verification/_trace.py`, sibling to `build_trace_block`) + a `{memory}` judge-template placeholder (`output_quality`+`key_condition`) + a "consistent-with-memory = GROUNDED, still flag contradictions" instruction; the loop captures per-turn `memory_accesses` at the PromptBuilder build branch and threads them into `_cat10_verify_gate(injected_accesses=)`, gated by a default-ON env lever `CHAT_VERIFICATION_MEMORY_GROUNDING` (ctor kwarg mirrors 57.136 `correction_context_strategy`) + a real-Azure A/B harness (`benchmark_memory_grounded_judge.py` mirrors `benchmark_correction_hygiene.py`, 10 cases). Key design: a `TransientState` field over a `Verifier.verify` ABC kwarg (0 verifier-impls + 0 test-stubs vs ~13). Backend-only NO migration/wire/frontend, parent-direct agent_factor 1.0. Anchored to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138) — same Cat 10 verification-spike shape (bounded judge-context change + env lever + real-Azure A/B harness + a real-code core ≥~3.5 hr that held the 0.60 per the 57.137 lesson, NOT a tiny-code 0.85 re-point). A/B verdict KEEP-default-ON: `fabrication_catch_rate` bare 0%→memory 100% (+100pp) at 0% false-reject (honest finding: the lenient `output_quality` judge doesn't false-reject grounded recalls in isolation → the fix's deterministic value is CONTRADICTION detection; verdict logic = two-sided OR). Drive-through STRONG PASS real chat-v2 + Azure gpt-5.2: a NEW-session 0-keyword recall under an accumulated Dana+Chris memory contradiction was DELIVERED + VerificationPassed 0.98 (vs pre-fix blind judge → rejected→no-recall). If a 2nd `verification-memory-grounding-spike` lands > 1.20, re-point toward 0.75 — the 2-leg drive-through staging is the variance risk. CHANGE-120 + design note 56) |
| `guardrail-restrict-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.137 ratio ~0.97 IN band; closes `AD-Guardrail-Detect-To-Restrict` (research #3) — an evidence-first thin spike: a permanent real-Docker escape harness (`scripts/benchmark_sandbox_escape.py` mirrors `benchmark_correction_hygiene.py`; `regex_screen` imports the REAL `DEFAULT_SANDBOX_PATTERNS` + `docker_contain` checks an `__ESCAPED__` sentinel under DockerSandbox; `main()` dogfoods the new `is_structurally_isolated` property) measured **regex_escape_rate 60% / docker_containment_rate 100%** → the regex deny-list is redundant-for-containment under Docker. Shipped: a Cat 2 `SandboxBackend.is_structurally_isolated` `@property` (provider-neutral, not isinstance; default False) + `_FailClosedSandbox` + `default_sandbox(require_isolation=...)` env-gated fail-closed (`SANDBOX_REQUIRE_ISOLATION`, DEFAULT OFF — dev/CI keep the SubprocessSandbox fallback, prod opts in) so a Docker-less host REFUSES rather than silently degrading + the Cat 9 detector docstring reframed (ESCALATE-for-visibility, `check()` byte-unchanged). Backend-only NO migration/wire/frontend, parent-direct agent_factor 1.0. Closest kin: `verification-context-hygiene-spike` 0.60 (57.136) + `verification-in-loop-spike` 0.60 (57.98) — Cat 2/9 structural-guardrail spike paired with a measurement harness + an env-gated surgical change + drive-through. The plan §7 ceremony-not-code-accelerated risk did NOT fire — UNLIKE the tiny-code 0.85 re-points (57.120/122/123/126/129/132), the core here is real code (a property on 3 classes + a refusing backend + a 3-way factory branch + a ~150-line harness + a 10-case corpus) so the 0.60 bottom-up haircut fit. Lesson: estimate code-hours honestly — a >~3 hr real implementation core holds the spike multiplier; a ~10-line surface change wrapped in full ceremony needs ~0.85. If a 2nd `guardrail-restrict-spike` diverges > 30% from 0.60, re-point) |
| `tool-reflection-and-lint-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.144 ratio ~1.05-1.1 IN band upper edge; closes `AD-Tool-Description-Lint-Reflection` (research #7, the LAST canonical item) — TWO orthogonal halves in one Cat 2 spike: **A** an AST `check_tool_descriptions.py` lint (11th in run_all; surfaced + filled 40 real missing param descriptions, 9 harness + 31 business_domain, user-approved scope expansion 11→18 files) + **B** an evidence-first structured-error reflection (pure `_error_taxonomy.py` classify/render, 5-taxonomy orthogonal to Cat 8 ErrorClass, consumed at `executor._build_failure` dominant path + `loop.py:3023` rare path B2, env-gated `CHAT_TOOL_ERROR_REFLECTION` default OFF) + a real-Azure A/B harness (`benchmark_tool_error_reflection.py` mirrors `benchmark_correction_hygiene.py`; plain-vs-reflection) whose verdict KEEP-lever-OFF (fix_rate 87.5%=87.5%, +0.00% < 5%) — parent-direct agent_factor 1.0. Closest kin: `guardrail-restrict-spike` 0.60 (57.137) + `verification-context-hygiene-spike` 0.60 (57.136) — a Cat-2 structural-guardrail/measurement spike + an env-gated surgical change + a measurement harness; the 57.137 lesson held (the real-code core — AST detector + pure taxonomy + executor `_build_failure` refactor + loop B2 + ~250-line harness + 49 tests — holds the 0.60, NOT a tiny-code 0.85 re-point). The upper-edge came from the user-approved +40-param expansion, NOT ceremony. Lesson recorded: a delegated-agent gate MUST include flake8 E501 — black does NOT wrap long string-literal lines, so the 40-param agent's black-clean descriptions still had 3 E501 the parent full-flake8 re-verify caught. If a 2nd `tool-reflection-and-lint-spike` lands > 1.20, re-point toward 0.75) |
| `verification-trace-and-benchmark-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.111 ratio ~1.0-1.1 IN band upper edge; A3 — Cat 1×10 loop.py trace-threading (the gate builds a `trace_state` vs `cast(LoopState,None)`; diff 25/3 threading-only) + a greenfield eval harness (`scripts/benchmark_judge.py` + a 28-case golden fixture + `@pytest.mark.benchmark`), parent-direct agent_factor 1.0; the over-edge = the dt+tooling discovery loop — D12 `tests.unit.scripts` importlib shadow + D-DAY3-1 cp950 print + the `api.main:app` startup fix + 2 MHist E501 — same shape as 57.109/110) |
| `loop-pause-point-feature` | 0.50 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.99 ratio ~0.93 IN band; the 4th pause leg — A2 verification-ESCALATE: conditional escalate pause + resume APPROVE-replay/REJECT-coach-one-turn + durable flag, Cat 1×10×9×7, parent-direct agent_factor 1.0; honours the 57.92/93 proposed `loop-pause-point-feature` ~0.40 but set 0.50 for the bounded REJECT continuation + held-answer snapshot beyond a pure pause leg) |
| `skills-system-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.113 ratio ~0.94 IN band; Skills System epic first vertical — greenfield Cat 5 `agent_harness/skills/` module (SkillRegistry + frontmatter loader + render_catalog_block) + a Cat 2 `read_skill` lazy-load tool + main-flow wiring (make_default_executor opt-in + build_handler system_prompt-append riding the persona seam + router), parent-direct agent_factor 1.0; shape ~ `subagent-child-loop-spike` 0.60 / `loop-injection-primitive-spike` 0.55 — the markdown/frontmatter loader + 2 real skill bodies add a bit over a pure-wiring spike; clean Day-0 三-prong (D1 system_prompt-seam GREEN → no PromptBuilder rewire; D2 registry-derived-matrix → dropped a planned yaml edit) kept it IN band) |
| `per-tenant-catalog-table-backed` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.114 ratio ~0.92 IN band; Skills System epic 2nd slice — a DB-backed per-tenant overlay on the 57.113 bundled registry: NEW `tenant_skills` table + migration 0030 (RLS two-policy minus sentinel) + `TenantSkillService` RLS-scoped CRUD + `resolve_tenant_skill_registry` (TTL cache, fail-open, mirrors `resolve_tenant_model_policy`) + `SkillRegistry.with_overlay` + 4 admin endpoints + FE list-CRUD tab; the backend wiring was **1 line** (router swap — `build_handler` already took the registry since 57.113), `loop.py`/`handler.py` diff 0, no new wire event (24). Plan said agent-delegated partial but executed **parent-direct** (agent_factor 1.0) so the 0.60 class mult alone was the calibration. Shape = config-tiering full-stack (admin tab + TTL resolver + per-request wiring) + a table/RLS/CRUD half — between `config-tiering-model-policy-spike` 0.60 and a pure tab port; the pre-commit-projection-vs-expire_on_commit invariant was the only table-backed novelty over the dict-projected policy precedents) |
| `config-validation-hardening` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.117 ratio ~0.95-1.0 IN band; Skills System epic catalog-hardening — add count + size write-path guardrails to the EXISTING 57.114 per-tenant catalog: env-overridable module constants (`SKILLS_MAX_*`, the 57.109 `_env_int` pattern) + a service-layer count guard (`SkillQuotaExceededError` 409 the admin POST's existing `except TenantSkillError` auto-maps — NO handler change) + a Pydantic-field `max_length` (422; DB stays `Text`, NO migration) + a `SkillListResponse` that surfaces the limits + an FE limit-surface (count/disable/textarea-cap/error-render) + a lowered-env-limit drive-through. NO table/migration/wire/codegen (count 24). Parent-direct (agent_factor 1.0); clean run — the only Day-2 surprise was a *simplification* (`useTenantSkills`/`tenantSettingsService` UNCHANGED — the React-Query hook already returns the whole response → 1 FE file lighter than plan). Lighter than 57.114's `per-tenant-catalog-table-backed` 0.60 (no table/migration/resolver/overlay — this hardens what 57.114 built); kin to the WRITE-side config family but pure validation. If a 2nd hardening sprint diverges > 30% from 0.55, re-point) |
| `skills-bundled-script-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.118 ratio ~0.92 IN band; Skills System epic executable half — a SYSTEM-BUNDLED skill ships a sibling `<stem>.py` the model runs via a NEW Cat-2 `run_skill_script(skill_name)` tool through the EXISTING `SandboxBackend`: `Skill.script: str\|None` (Cat 5 `from_dir` sibling-loader) + `RUN_SKILL_SCRIPT_TOOL_SPEC` (risk MEDIUM) + `make_run_skill_script_handler` w/ a lazy process-wide sandbox singleton (Day-0 refinement — `make_default_executor` runs per request → avoid per-request Docker probe) + the `skill_registry` opt-in registers it (auto-PASS via the risk-blind matrix `handler.py:588-592`, Day-0 #1 risk RESOLVED) + a demo `bundled/digest.{md,py}`. NO DB/migration/wire (count 24)/codegen/frontend; parent-direct (agent_factor 1.0 — plan said partial but no code-implementer agent used). Same 0.60 as `subagent-child-loop-spike` — the frontmatter loader + a real bundled script + sandbox reuse put it a touch above a pure-wiring spike, but it reuses the proven 57.113 registry/opt-in machinery + the existing `SandboxBackend`. 2 Day-0 scope-reducing refinements held (lazy singleton over per-request probe; integration injects `SubprocessSandbox()` over a Docker-availability skip). Drive-through PASS in a REAL DockerSandbox — `run_skill_script("digest")` → a sha256 == local compute byte-for-byte (first main-flow sandboxed-execution proof). If a 2nd `skills-bundled-script-spike` (e.g. the tenant-authored leg) diverges > 30% from 0.60, re-point) |
| `skills-admin-readonly-surface` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.119 ratio ~0.97 IN band; Skills System epic authoring-UX visibility leg — a read-only "System Skills" section + a Preview modal in the admin Skills tab: ONE read-only `GET /admin/tenants/{id}/skills/system` (`list_system_skills`, mirrors `list_tenant_skills`) over `get_default_skill_registry().list()` with `has_script` + per-tenant `overridden` + a FE `SystemSkill` type/`fetchSystemSkills`/`useSystemSkills` (own key) + a `SkillsTab` sibling Card + an inline-overlay Preview modal. NO DB/migration/wire (count 24)/codegen; parent-direct (agent_factor 1.0). Same 0.55 as `config-validation-hardening` — FE-heavier here (a new section + a modal) but thinner backend (one read endpoint, no service/error/constants); lighter than 57.114's `per-tenant-catalog-table-backed` 0.60 (read-only over what exists, no table/CRUD/RLS). Day-0 三-prong RESOLVED the #1 lint risk (api→Cat-5 import — the `handler.py:96`/`router.py:465` precedent) + caught 2 path/contingency drifts (D-fe-test-path: tests under `frontend/tests/unit/...`; D-modal-primitive: no `Modal` → inline overlay). Only friction: the modal a11y lint (4 jsx-a11y) → ~10 min mirroring `TenantMembersDrawer` (window Escape + role=dialog + matching disables). Drive-through PASS (real admin Skills tab — a live-created+deleted tenant skill flipped the shadowed tag, the Preview modal rendered real instructions). If a 2nd read-only-surface sprint diverges > 30% from 0.55, re-point) |
| `skills-slash-command-fullstack` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.115 ratio ~1.0 IN band; Skills System epic 3rd slice — the user-invoked force-load: a DRY `render_skill_instructions` helper (read_skill stays byte-identical) + `build_handler` `## Active Skill` deterministic system-prompt injection + a non-admin `GET /chat/skills` picker list (name+desc only) + a `ChatRequest.force_load_skill` field/router-validate-and-pass + a **greenfield** `SkillSlashMenu` composer picker (`/`-trigger + ↑/↓/Enter/Esc + leading-KNOWN-skill-token parse → strip). No DB/migration/new-event (lighter than 57.114's 0.60); the greenfield FE autocomplete was the main net-new risk (no reusable inline-textarea pattern — `CommandPalette` is global ⌘K), offset by light backend mirror over the 57.113 catalog seam (force-load = 1 append). Parent-direct (plan said partial but no code-implementer agent used → agent_factor 1.0); matches the `frontend-feature-with-event-wire-addition` 0.55 family. Drive-through Leg A proved `read_skill` 0× yet output followed the skill = deterministic injection) |
| `frontend-feature-with-event-wire-addition` | 0.55 | ~1.07 (3 pt) | KEEP — 57.100 ~1.0 + 57.108 ~1.05-1.1 + 57.116 ~1.1-1.2 all IN band (3-consec → VALIDATED). Shape: additive field on an EXISTING event (count unchanged) + codegen regen + chat-v2 FE store-capture + render + cross-stack parity, parent-direct agent_factor 1.0 (57.116: server-confirmed `active_skill` on loop_start → user-turn skill chip; the over-edge = the tsc required-field detour — a demo fixture literal + union narrowing the Vitest oxc transform didn't catch) |
| `chatv2-inspector-existing-field-surface` | 0.55 → **0.85** (re-pointed Sprint 57.120) | ~0.87 (3 pt) | KEEP 0.85 — 3 data points IN band (Sprint 57.120 — surface an ALREADY-store-captured wire field in a NEW chat-v2 render location + a thin store carry-forward, NO new wire field/codegen/backend/migration: `AgentTurn += activeSkill?` + `turn_start` carry from the most-recent non-injected UserTurn + a `<KV active_skill>` row in InspectorTurn, parent-direct agent_factor 1.0; 1st pt ratio **~1.6 OVER band** at the borrowed 0.55 → re-point to 0.85. **Generalizable insight**: a TINY-CODE + FULL-CEREMONY parent-direct sprint should use ~0.85-1.0 regardless of the FE family it resembles — the 0.45-0.65 band assumes the bottom-up has enough code-hours for the AI/agent acceleration haircut to bite; here the code was ~10 lines and the cost was dominated by fixed-cost ceremony (plan/checklist/Day-0/drive-through/CHANGE/retro/navigators) which is NOT code-accelerated. Single-over-point → conservative re-point (0.85), not back to 1.0; if a 2nd `*-existing-field-surface` lands < 0.7 at 0.85, lower again. **Sprint 57.131 = the 2nd data point** — the `model` row leg (`AgentTurn += model: string \| null` + per-turn capture in the EXISTING `llm_request` `mergeEvent` case + a `<KV model>` row reusing `KV`, NO backend/wire/codegen, parent-direct agent_factor 1.0; drive-through `model = gpt-5.2`); feature-only ratio ~0.82-0.93 IN band → KEEP 0.85, the 2-pt trend confirms the class — a tiny-code + full-ceremony parent-direct sprint sits ~0.85, NOT the 0.45-0.55 pure-repoint band. **Sprint 57.133 = the 3rd data point** — the token-sweep leg (`AgentTurn += cachedInputTokens: number\|null` + an `llm_response` 0-guard capture of the already-on-wire `cached_input_tokens` + 2 `<KV>` rows: `tokens.cached` + a DERIVED per-turn `cache_hit` = round(cached/tokensIn×100)%, NO backend/wire/codegen/migration, parent-direct agent_factor 1.0; drive-through real Azure prefix-cache hit turn-2 `tokens.cached 2,048` / `cache_hit 83%`, turn-1 honest "—"); ratio ~0.94-1.03 IN band → KEEP 0.85, 3-pt mean ~0.87 VALIDATES the class. AD-ChatV2-Inspector-Turn-Metadata-Wire fully CLOSED 3/3 legs) |
| `loop-injection-primitive-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.101 B1 — cross-stack new-domain primitive: NEW Cat 1 `MessageInbox` ABC + NEW `_run_turns` drain seam + NEW `MessageInjected` event TYPE (codegen 23→24) + module-level `InjectionRegistry` + new `POST /{id}/inject` + FE composer-mid-run + store/render; Cat 1×12×9×frontend, parent-direct agent_factor 1.0; larger surface than 57.96 but each layer thin over the 57.88-99 pause/resume + 57.96 codegen machinery → 0.55 like 57.96; D-DAY1-1 input-guardrail-not-between-turns-gate correction caught Day-1) |
| `subagent-teammate-multiturn-spike` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.102 B2a ratio ~0.95-1.0 IN band; Cat 11×1×12 composition spike — TEAMMATE single-shot → real child loop (mirror 57.94 FORK) + `send_to_parent` tool + `TeammateChildLoopFactory` + B1 inbox wiring (reuse 57.96 relay + 57.101 inbox), backend-only, no new wire event / DB / FE, parent-direct agent_factor 1.0; lighter than 57.94's `subagent-child-loop-spike` 0.60 because it reuses 3 proven assets vs building the child-loop machinery) |
| `subagent-inject-to-teammate` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.103 B2b ratio ~1.15-1.25 slightly OVER; cross-stack — `POST /subagents/{sid}/inject` endpoint + `TeammateInboxScope` register/unregister lifecycle + `MessageInjected`-in-relay + US-5 inline mode-aware label, parent-direct agent_factor 1.0; the over-run = a build-then-revert tax: the drive-through found the inject UI un-drivable under the buffered relay + await-completion → US-4/6 built then removed per Option A (the backend primitive + US-5 kept). A sprint whose user-facing half is architecture-blocked carries a hidden build-then-revert cost the bottom-up didn't price) |
| `config-tiering-model-policy-spike` | 0.60 | ~0.98 (2 pt) | KEEP — C1 57.104 ~0.9-0.95 + C3 57.106 ~1.02 both IN band (2-consec) → validated. Full-stack config-tiering family (value object + TTL resolver Risk Class C + admin PUT/GET + tenant-settings tab + per-request wiring); backend parent-direct + FE agent-delegated-then-parent-re-verified = blended full-stack so NO single agent_factor; loop.py diff 0, no migration, no new event. C3 (57.106) widened it with a NEW Cat 9 `RiskyActionDetector` (only non-mirror piece) + a 9-field richer policy + `list_templates()` NAME allow-list; drive-through PASS proved per-tenant escalate-phrase + risky-detector on/off via cache invalidation |
| `transcript-retention-apply-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.134 ratio ~1.0-1.1 IN band; new-domain backend spike — a bounded DELETE-by-age on partitioned FORCE'd-RLS tables (`SET LOCAL app.tenant_id` + explicit `WHERE tenant_id`) + an apply POST + a dry-run preview GET on the EXISTING canonical `tenants.retention_days` column (Day-1 pivot DROPPED a parallel `meta_data` config = AP-6 trap, caught mid-Day-1 by reading identity.py), parent-direct agent_factor 1.0; NO migration/new-event/ABC. Kin to `config-tiering-model-policy-spike` 0.60 but the config half was REMOVED by the pivot (canonical column already existed) + a destructive deletion core added; the pivot write-then-drop (~0.5 hr) offset the saved config work → on-budget. Drive-through PASS both legs (preview non-destructive on acme-prod + apply destructive on a throwaway tenant: deleted 1/1, recent survived, REMAINING_MESSAGES=1). If a 2nd diverges > 30% from 0.60, re-point) |
| `scheduled-job-mirror-spike` | 0.55 → **0.85** (re-pointed Sprint 57.135) | n/a (1 pt) | KEEP 0.85 pending 2-3 sprint validation (Sprint 57.135 — closes 57.134 follow-on #1: a scheduled background job auto-enforcing per-tenant transcript retention. `run_transcript_retention_sweep` (enumerate all tenants → per-tenant apply+audit+commit, fail-open) reusing the 57.134 `apply_transcript_retention` + a `_transcript_retention_poll_loop`/`_start_*`/lifespan wiring mirroring the billing-outbox drainer (`main.py:267-336`); DEFAULT OFF (destructive opt-in, vs billing default-ON). Backend-only, NO migration. parent-direct agent_factor 1.0. **1st pt ratio ~1.4-1.5 OVER band at 0.55 → re-point 0.85.** The mirror-code was small+quick (~90 lines + 6 tests) but the **drive-through ceremony dominated** — a Risk-Class-E orphan spawn-worker hunt (57.97 trap) + clean single-proc restart + seed/verify/cleanup scripts + the timed sweep observation. Same ceremony-not-code-accelerated insight as 57.120/122/123/126/129/132: tiny-code + full-ceremony + parent-direct + mandatory drive-through lands ~0.85-1.0, NOT the 0.45-0.55 band. Kin to `transcript-retention-apply-spike` 0.60 (the same domain) but the drive-through here is a background-job runtime verification (no UI) with the orphan-worker detour. Drive-through PASS: sweep `tenants=5000 failed=0 messages_deleted=1`, throwaway tenant MESSAGES 2→1 + SCHEDULED_AUDITS=1, default-OFF re-confirmed. If a 2nd `scheduled-job-mirror-spike` lands < 0.7 at 0.85, lower again) |

> Collapsed/closed historical classes (`frontend-mockup-strict-rebuild — historical`; `frontend-verbatim-css-repoint` pre-57.38 single-baseline, CLOSED Sprint 57.38) → calibration-log.md §1. For verbatim-css-repoint use `-simple` (0.50) or `-with-extras` (0.65) per criteria above.

#### Active Agent Delegation Factor Modifier (ACTIVATED 2026-05-25 — Sprint 57.42 retro structural decision per `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`)

> **Per-sprint activation/validation history moved** (REFACTOR-005, 2026-05-31): activation evidence, tier-2/3/4 split evolution, per-sprint history (Sprint 57.42→57.62), deprecated baselines → [`calibration-log.md` §2](../../docs/03-implementation/agent-harness-execution/calibration-log.md). Below = active rules only (Status + Formula tier-4 table + When + Rollback + Escalation + Tracking discipline).

**Status**: **ACTIVE — Option A multiplicative `agent_factor` coefficient with mid-band start `0.55`**. Closes `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`. Activation criteria FULLY MET at Sprint 57.42 retro Q4 (5 cross-class data points + 4 consecutive `mockup-strict-rebuild` agent-delegated < 0.7).

**Hypothesis (validated)**: code-implementer agent-delegated frontend work shows ~3-5× speedup vs the human-rewrite cadence the bottom-up estimates assume. Existing per-class multipliers (0.45-0.85) bake in a human-cadence haircut; agent-delegated sprints consistently undershoot the calibrated band lower edge because the haircut isn't enough. Validated by 5 data points (full activation evidence → calibration-log.md §2).

**Formula** (applies from Sprint 57.43+ onwards):

```
effective_calibrated_hours = bottom_up × scope_class_multiplier × agent_factor

where agent_factor = {
  human (default):      1.0
  agent-delegated (tier-4 sub-class table — Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATED effective 2026-05-28 onwards):
    mechanical-pattern-reuse-heavy:               0.30   (≥ 4 mechanical repetitions of same template in 1 sprint; evidence: Sprint 57.49 retroactive — 5-tab+1-drawer migration ratio 0.21 under 0.30 vs 0.14 under 0.45; Sprint 57.60 1st DELIBERATE FORWARD application ratio ~1.09 IN BAND ✅ — backend 5-site fallback removal + 0020 cleanup migration + test conversions; KEEP 0.30 single forward-data-point; counterfactual `-port-style` 0.45 → ~0.73 below band so 0.30 better fit; shape-variance: 57.49 high-repetition ~24× ratio 0.21 vs 57.60 moderate-repetition ratio 1.09 — if a future ≥20× sprint at 0.30 lands < 0.7 again consider tier refinement `-high-repetition` ~0.20 vs `-moderate` 0.30, defer until 2+ such data points)
    mechanical-greenfield-port-style:             0.45   (single NEW component-pair via mirror-port of existing service shape; predecessor template ≥ 95% internalized; NO NEW Pydantic schema design / UX state design — RESERVED for future port-only sprints)
    mechanical-greenfield-design-decisions:       0.65   (single NEW component-pair WITH NEW Pydantic schema design + NEW UX state design — e.g. edit-mode draft state — design decisions add ~30-50% wall-clock vs pure port; evidence: Sprint 57.54 HITLPolicies WRITE ratio ~1.37-2.0 at 0.50 / Sprint 57.55 FeatureFlags WRITE ratio ~1.57 at 0.50 — 2 consec > 1.20 → tier-4 SPLIT ACTIVATED; equivalent ratios under 0.65 = 1.05-1.55 / 1.21 → band top edge / IN band; Sprint 57.56=1.02 + 57.57=1.15 both IN band 2-consec → SPLIT FULLY VALIDATED; **Sprint 57.61 3rd validation 1st BACKEND-ONLY ratio ~0.74 BELOW band by 0.11** — single BELOW point vs 2 IN → rollback rule needs 2 consec same-direction → KEEP 0.65 single-data-point caution; backend-only validator+422-envelope runs faster than the backend+frontend pair the 0.65 was calibrated on, counterfactual `-port-style` 0.45 → ~1.06 IN band → NEW carryover `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` needs 2nd backend-only point before any sub-class refinement; **Sprint 57.62 4th validation BACK TO PAIR SHAPE ratio ~0.77 BELOW band by 0.08** — pair sub-seq 57.56=1.02 + 57.57=1.15 + 57.62=0.77 mean ~0.98 IN band → KEEP 0.65 single-data-point-per-shape; **R6 WEAKENS** — 57.61 backend-only 0.74 + 57.62 pair 0.77 = 2 consec below regardless of shape → likely agent over-delivers generally; `AD-AgentFactor-DesignDecisions-Below-Band-Watch` broadens cross-shape: next `-design-decisions` (either shape) < 0.85 → tighten 0.65 → 0.55)
    mixed-multidomain-bundle-mechanical:          0.45   (3+ independent tracks WITH mechanical pattern reuse component — e.g. backend ORM + Pydantic + tests bundle; History: Sprint 57.46 ratio 1.60 at 0.45→rollback 0.65 (Option B); Sprint 57.58 tier-3 1st validation ~0.49 BELOW band single-data-point KEEP 0.65; Sprint 57.59 tier-3 2nd validation ~0.34 BELOW band → 2 consec < 0.7 ROLLBACK RULE MET → **tighten 0.65 → 0.45 effective Sprint 57.60+**; note even 0.45 ≈ 0.49 still below band — if Sprint 57.60 1st validation under 0.45 also < 0.7 → escalate 0.30 OR fold into mechanical-pattern-reuse-heavy 0.30)
    mixed-multidomain-bundle-non-mechanical:      1.0    (3+ independent tracks of pure audit/docs/rules — NO mechanical pattern reuse; e.g. Sprint 57.51 + 57.52 both ratios > 1.20 at 0.65 = 2nd rollback-trigger MET; tier-3 SPLIT Sprint 57.52 retro effective 2026-05-27 onwards)
  partial (20-79% via agent):          0.75   (linear interpolation)
  human (<20% via agent):              1.0
  History: 0.55 (Sprint 57.42 activated) → 0.45 (Sprint 57.44 tighten) → 0.65 (Sprint 57.46 rollback) → Option B sub-class split (Sprint 57.48; mechanical-single-domain 0.45 + mixed-multidomain-bundle 0.65) → Option B tier-2 split (Sprint 57.50; closes AD-AgentFactor-Tier-2-Refinement-Proposal; mechanical-single-domain split into pattern-reuse-heavy 0.30 + greenfield 0.50; parallel Sprint 57.38 `-simple/-with-extras` precedent + Sprint 57.48 Option B precedent) → Option B tier-3 split (Sprint 57.52; mixed-multidomain-bundle split into -mechanical 0.65 unchanged + -non-mechanical 1.0 NEW; closes AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52; rollback rule "2 sprints with ratio > 1.20 → mandatory structural action" MET via Sprint 57.51=1.49 + Sprint 57.52=~1.85) → Option B tier-4 split (Sprint 57.55; mechanical-greenfield split into -port-style 0.45 RESERVED + -design-decisions 0.65 NEW; closes AD-Sub-Class-Greenfield-Port-vs-Design-Refinement Sprint 57.54 CONDITIONAL carryover; rollback rule MET via Sprint 57.54 ratio ~1.37-2.0 + Sprint 57.55 ratio ~1.57 — both > 1.20 at 0.50 baseline)
}
```

**When `agent-delegated` applies**: ≥ 80% of Day 1 work via code-implementer agent (or equivalent). 20-79% = `partial` (apply `agent_factor = 0.75` linear interpolation; record explicit tag in retro Q2). < 20% = `human` (apply `agent_factor = 1.0`; existing class multiplier alone).

**Rollback rule** (3-sprint window — parallel to existing `When to adjust the multiplier` discipline):
- If activated factor produces **2 sprints with `actual/committed-with-agent-factor` ratio < 0.7** → tighten to `0.45`
- If activated factor produces **1 sprint with ratio > 1.20** → roll back to `0.65` (single-data-point caution)
- If activated factor produces **≥ 2 sprints with ratio > 1.20** → roll back to `1.0` (drop the modifier — agent delegation didn't actually accelerate; class-multiplier alone sufficient)

**Escalation to Option B** (per-class sub-class split — fallback if Option A undershoots specific classes):
- If `0.55` produces ratio < 0.7 OR > 1.20 for **≥ 2 specific classes** over 3-sprint window → switch from Option A to Option B per-class split (add `+ agent-delegated` sub-row for each high-volume class; proposed baseline ranges: `-with-extras` 0.30-0.40 / `mockup-strict-rebuild` 0.25-0.35 / `verbatim-css-repoint -simple` 0.25-0.30; matches existing matrix granularity)

**Tracking discipline** (MANDATORY from Sprint 57.43+):

Each agent-delegated sprint MUST record in retrospective Q2:
1. `actual/bottom-up` ratio (existing)
2. `actual/committed` ratio (now `committed = bottom_up × scope_class_mult × agent_factor`)
3. **NEW**: explicit `agent-delegated: yes / no / partial` tag (≥ 80% = `yes`; 20-79% = `partial`; < 20% = `no`)

Sprint plan §Workload Calibration MUST state estimate in the **four-segment form** when agent delegation is anticipated:

> Bottom-up est ~X hr → class-calibrated commit ~Y hr (mult Z) → agent-adjusted commit ~Y' hr (agent_factor 0.55)

where `Y' = Y × 0.55 = X × Z × 0.55`. See §Workload Calibration §Four-segment form above.

---

### Step 2: Create Checklist File

**Immediately after plan approval**, create sprint checklist at `docs/03-implementation/agent-harness-planning/phase-XX-name/sprint-XX-Y-checklist.md`.

**Required Format**:
```markdown
# Sprint XX.Y — Checklist

[Link to plan]

## Day N — Task Group

### N.M Task Description
- [ ] **Specific deliverable**
  - DoD: Measurable definition of done
  - Command: `git ...` or `pytest ...`
- [ ] **Next deliverable**
  - ...
```

**Key Rules**:
- Use `- [ ]` format
- Each task should be a single logical unit (break down if checklist entry covers >1 commit's worth of work)
- Include DoD (Definition of Done) — how to verify
- Map each task to plan's acceptance criteria
- Assign to days (Day 1-5 for typical sprint)
- **DO NOT include time estimates in checklist** (since Sprint 55.3 / AD-Lint-2):
  - ❌ ~~`## Day N — Task Group (Estimated X hours)`~~ — drop "(Estimated X hours)" header
  - ❌ ~~`### N.M Task Description (Y min)`~~ — drop "(Y min)" suffix
  - ❌ ~~`- Estimated: Y min`~~ sub-bullets — drop entirely
  - ✅ Sprint-aggregate `Bottom-up est ~X hr → calibrated commit ~Y hr` lives in plan §Workload only
  - ✅ Per-day / per-task actuals (with informal estimates if useful) → progress.md Day entries (individual record, non-binding)
  - **Why** (Sprint 53.7 retrospective Q4 evidence): Day-level estimates have higher variance than sprint-level (banking offset Day N over-runs against budget). Per-day calibrated targets create false precision and trigger anxiety mid-sprint when Day N slips. Sprint-aggregate calibration is the only signal that survives 3-sprint moving evidence (per §Workload Calibration above).

**Reference Template** (FROZEN — REFACTOR-008, 2026-06-17): Mirror the **frozen canonical template** `claudedocs/templates/sprint-checklist-template.md` — an ABSOLUTE anchor, **NOT** the most-recent sprint's checklist (same drift rationale as §Step 1). Day 0-4 (5 days); each task = bold deliverable + DoD + Verify command; NO time estimates; header line SHORT (full description lives in the plan's `**Summary**`, not duplicated here).

**Format Consistency Rule**: Same Day count (5 days, Day 0-4), same per-task detail depth, same DoD/Verify command patterns. Scope differences expressed through **content** (more checkboxes inside a Day), **not structure** (don't add Day 5 / Day 6).

**Violation Pattern** ❌ (Phase 42 Sprint 147): Deleting unchecked `[ ]` items when scope shrinks. This hides what was planned vs. what shipped.

**Violation Pattern** ❌ (Sprint 52.1 v1-v2 — 2026-04-30): First draft used 6 days (Day 0-5); second draft was 27% shorter than 51.2 with insufficient per-task detail. Both required rewrites. **Lesson**: Match prior sprint's day count + detail depth before drafting.

✅ **Correct behavior**: Only change `[ ]` → `[x]`. If scope cuts, leave `[ ]` and note reason in progress.md.

---

### Step 2.5: Day-0 Plan-vs-Repo Verify (Sprint 55.3+ — closes AD-Plan-1; AD-Plan-3 promoted Sprint 55.6; AD-Plan-4 Schema-Grep promoted Sprint 57.1)

**Mandatory** between plan/checklist drafting and Day 1 code start. Plans drafted from session memory + retrospective context **drift from real repo** because:

- Class names get renamed between sprints (e.g. `_obs.py` may already exist when plan assumes new file)
- Table names change in Alembic migrations between PR drafts
- Test fixture paths shift when `conftest.py` is restructured
- Service/method signatures evolve in unrelated PRs while plan was being written
- **Wrong-content drift**: file exists but body diverged from plan's claim (e.g. plan asserts `_retry_policy` is dead but path verify alone can't see the body's call sites; or plan asserts ABC `ToolErrorDecision` exists but the ABC was never created)

**Cost when skipped**:
- Sprint 53.7 retrospective Q4 — 5 path-drift findings (D4-D12) cost ~1 hr Day 1+ re-work
- Sprint 55.3 Day 0 — 3 path-drift findings (D1-D3) caught in ~30 min before code starts
- Sprint 55.5 Day 0-2 — **5 wrong-content drifts** (D1+D2+D4+D5+D7) caught via AD-Plan-3 first application; ~55 min cost prevented ~3-4 hr re-work (4-8× ROI)
- Sprint 55.6 Day 0-3 — **11 wrong-content drifts** (D1-D11) caught via AD-Plan-3 second through sixth applications; ~75 min cost prevented ~9-10 hr re-work + 2 production-grade bugs (7-8× quantitative + 2 critical correctness saves)

#### Required actions (Day 0, before Day 1 code)

The verify is a **three-prong grep pass** (+ optional Prong 2.5 sub-prong for frontend page sprints); all prongs are mandatory when applicable (Prong 2.5 only when sprint involves frontend page re-point / restructure with existing child-component tree; Prong 3 only when sprint touches DB schema / migration / ORM models):

##### Prong 1 — Path Verify (AD-Plan-2 from Sprint 55.3)

Every file path mentioned in plan §File Change List or §Technical Spec → `Glob` or `ls` to confirm exists / does not exist as expected.

- New files (creates): `Glob("path/to/new_file.py")` returns 0 results
- Edited files (edits): `Glob("path/to/existing.py")` returns 1 result
- DB tables: check `infrastructure/db/models/*.py` + `alembic/versions/*.py`
- Fixture paths: check `tests/**/conftest.py`
- Imports / re-exports: confirm package-level `__init__.py` if plan asserts exposure
- Public ABC methods: read the actual ABC file to confirm signature
- Test-infra files (pytest markers, fixtures, e2e specs) cited in plan §Technical Spec / §Acceptance — Glob-verify they exist, NOT just product files. Sprint 57.66 D-DAY0: a phantom `test_chat_e2e_real_llm.py` + `real_llm` marker propagated across 3 plans before a Prong-1 sweep caught they never existed (`AD-Day0-Prong1-TestInfra-File-Verify`).

##### Prong 2 — Content Verify (AD-Plan-3 promoted Sprint 55.6)

Every plan §Technical Spec / §Background factual claim about existing code → **Grep** for the asserted symbol/pattern in real source. Path-verify alone (Prong 1) is **insufficient**: the file exists, but its body may have diverged from the plan's claim.

Common drift classes and matching grep query patterns:

| Drift class | Plan claim pattern | Grep verify pattern |
|-------------|--------------------|---------------------|
| **Claimed-but-unwired entry points** | "X is dead state" / "Y attribute is unused" | `grep -n "self\._{attribute}\b" {target_file}` — count call sites vs assignments (≥1 assignment / 0 call → confirmed dead) |
| **Claimed-but-missing imports** | "Z is publicly re-exported" / "consumer uses A" | `grep -rn "import {symbol}\|from .* import .*{symbol}" {target_dir}` — confirm import sites |
| **Claimed-but-renamed symbols** | "B was renamed to C" / "D class extends E" | `grep -rn "{old_name}\|{new_name}\|class .* {parent}" {target_dir}` — detect rename / inheritance drift |
| **Claimed-but-non-existent ABCs** | "extend ABC F" / "add G enum case" | `grep -rn "class F\|class G\|F\.{member}" {target_dir}` — confirm ABC actually exists before planning extension |
| **Claimed-but-wrong-units fields** | "uses backoff_seconds" / "stored as float" | `grep -n "{field_name}: " {target_file}` + read 1-3 lines — confirm unit / type assumption |
| **Claimed-but-silent-constraint-delta** | "frontend re-point shipped" / "+N tests added" / "bundle size unchanged" | `git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' \| grep -cE '^\+[^+].*oklch\('` — count delta against `HEX_OKLCH_BASELINE` in `check-mockup-fidelity.mjs`; same pattern applies to AP-N detector counts, Vite bundle size byte delta, pytest/Vitest count deltas. In agent-delegated migration sprints, the agent typically nails the visual/code change BUT silently exceeds baseline-constrained metrics (HEX_OKLCH literal count, AP-N count, bundle KB). Day 0 grep surfaces the delta upfront so baseline bump lands in same Day 1 commit (instead of next PR's CI hotfix). ROI evidence: Sprint 57.49 silent HEX_OKLCH +1 → PR #200 hotfix `74ed8a2f` post-merge fix-forward; AUDIT-001 (Sprint 57.51 Track C) Verdict A confirmed intended verbatim port + this rule extraction. |
| **Stale-docstring-Karpathy-3** | docstring/MHist claims "X uses Y" / "TODO remove Z next sprint" / "deprecated since Sprint N" | `grep -nE '"""\|^#\|^//\|^/\*' {target_file}` to find docstring/comment regions; then cross-grep the referenced symbol/file against repo reality. Docstrings + module-level comments + MHist entries are "code" for the dead-code rule (Karpathy §3) — when they reference symbols/features that have been removed, they're orphan claims that mislead Day 0 reviewers. ROI evidence: Sprint 57.50 D-DAY0-8 — `_fixtures.ts` L21 docstring referenced SEATS_FIXTURE which Sprint 57.49 had already removed; Day 0 caught the stale comment, Sprint 57.50 task 1.2.4 scope shrunk from ~5 min Day 1 surprise rework to ~1 min docstring cleanup. |
| **Claimed-but-missing-storage-path** (Sprint 57.57 PROMOTION) | "tenant overrides stored at `Tenant.<col>`" / "<Resource>OverrideStore table exists" / "PUT writes to dedicated `tenant_<resource>` table" | `grep -rn "meta_data\[.<key>.\]\|<Resource>Service\|class .*<Resource>.*Store\|tenant_<resource>" backend/src/` — discover actual storage architecture (dedicated table vs JSONB-on-registry-table vs JSONB-on-tenants-meta_data) BEFORE plan §4.1 commits to a Pydantic write shape. ROI evidence (3-data-point): Sprint 57.55 D-DAY0-B 🔴 RED (plan assumed `tenants.meta_data["tenant_overrides"]` → reality `feature_flags.tenant_overrides[str(tid)]` JSONB ON registry table; pivot saved ~30-45 min); Sprint 57.56 D-DAY0-A 🔴 RED (plan assumed Quotas has override storage → reality PlanQuota per-Plan template immutable; Option B `tenants.meta_data["quota_overrides"]` JSONB direct write; pivot saved ~60 min vs plan v0 abort); Sprint 57.57 D-DAY0-A ✅ GREEN inverse-validation (storage path `tenant.meta_data["rate_limits"]` established Sprint 57.48 Track D → no plan pivot needed; rule produces actionable outcome in BOTH directions). Codified Sprint 57.57 closeout per `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` PROMOTION. |
| **Claimed-but-missing-canonical-service** (Sprint 57.57 PROMOTION) | "extend `<Resource>Service.set_override` method" / "add `<Resource>Store.put()` upsert" / "call canonical service for audit chain auto-emit" | `grep -rn "class .*<Resource>Service\|class .*<Resource>Store\|def set_\|def put_\|def update_" backend/src/<scope>/` — discover canonical service availability (exists → use canonical method for cleaner audit chain + cache invalidation; doesn't exist → direct ORM UPDATE + manual `append_audit` pattern Sprint 57.3 + 57.56 precedent). ROI evidence (2-data-point both directions actionable): Sprint 57.55 D-DAY0-T 🆕 NOTABLE positive direction (`FeatureFlagsService.set_tenant_override` Sprint 56.1 IS canonical setter auto-emitting audit chain → clean V2 service path; REMOVED `AD-FeatureFlags-PerFlag-AuditLog-Phase58` carryover positive side-effect); Sprint 57.56 D-DAY0-D 🆕 NOTABLE inverse direction (NO canonical service for Quotas → architectural simplification path = direct ORM UPDATE + manual `append_audit`; Sprint 57.3 PATCH precedent); Sprint 57.57 D-DAY0-B inverse continued (NO canonical service for RateLimits → same direct ORM path as Sprint 57.56). Both directions produce actionable plan pivots — codified Sprint 57.57 closeout per `AD-Day0-Prong2-CanonicalService-Grep` PROMOTION. |
| **Claimed-but-nested-shape-mismatch** (Sprint 57.60 PROMOTION) | "stored as `{resource, window, limit}`" / "config items are typed objects" / "the JSONB holds `{key: value}` dicts" | when the plan asserts the NESTED shape of a stored blob (JSONB / dict / list-of-dicts), READ the actual Pydantic model / dataclass / TypedDict BODY — do NOT infer from the key name alone. `grep -rn "class .*<Model>\|<field>:" backend/src/` to locate, THEN Read the model body to confirm the real nested shape. ROI evidence (2-data-point): Sprint 57.58 D-DAY1-1 (stored `meta_data["rate_limits"]` shape is UI display strings `{label, value}` e.g. `{"label":"API requests","value":"100 / min"}` NOT the assumed `{resource, window, limit}` — the runtime gate had to normalize via `parse_rate_limit_item`; caught mid-Day-1); Sprint 57.59 reinforced (both the live normalizer + the inline `0019` migration parser keyed off the `{label, value}` shape, not the assumed typed object). Reading the model body at Day 0 surfaces the real shape before plan §4 commits to a parse/write contract. Codified Sprint 57.60 closeout per `AD-Day0-Prong2-Nested-Shape-Read` PROMOTION. |
| **Claimed-but-flat-codegen-shape** (Sprint 57.67 — 4 data points, fold-in) | "codegen TS event/DTO types from existing Python types" / "interface mirrors the dataclass" | when GENERATING consumer types/schemas from existing producer types, capture the STRUCTURAL SHAPE (envelope nesting), NOT just field names — Read the producer/serializer body first. Sprint 57.67 stage-1 emitted flat `{type, ...fields}` but the wire is nested `{type, data:{...}}`; recurred 4× → `AD-Day0-Codegen-Existing-Shape-Capture`. Verify the wire envelope nesting before drafting the consumer type. |
| **Claimed-but-no-live-producer** ("fill/wrap/instrument every X" scopes; Sprint 57.71 + 57.72) | "wrap every loop span" / "fill all N Inspector tabs" / "instrument every call site" | for "fill/wrap/instrument every X" scopes, grep that EACH X has a live producer / call-site BEFORE planning to surface it — else the slot is an AP-4 Potemkin. Sprint 57.71: 2 of 6 tracer spans had no loop-level call site (deferred, not faked); 57.72: only 1 of 3 Inspector tabs had a live event producer (Tree shipped; Trace/Memory → ComingSoon). |

##### Prong 2.5 — Child Component Tree Depth Audit (frontend page sprints only; AD-Plan-5 fold-in Sprint 57.40 — `chore/rules` ship via Item #2 of post-Sprint-57.39 4-AD micro-fix sequence)

**Applies when**: sprint plan involves frontend page re-point / restructure where the **entry component** (e.g. `frontend/src/pages/<route>/index.tsx`) and its **child components** (e.g. `frontend/src/features/<area>/components/*.tsx`) may carry DIFFERENT vintages of styling / structure. Prong 2 scopes only to the entry component file; this sub-prong extends grep depth into the child-component tree.

**Why this matters** (Sprint 57.39 D-DAY1-1 evidence): `/governance` + `/verification` entry components were migrated to mockup-ui `Tabs` primitive (closing the shell-level NEAR-PARITY), but the child components they import (`AuditLogViewer` / `VerificationList` / `CorrectionTraceView` / etc.) retained Sprint 57.5 / 57.9 / 57.11-vintage Tailwind shadcn-utility patterns. Day 0 plan-grep (Prong 2) only checked the entry component file → child drift was invisible until Day 1 code → mid-sprint scope expansion required (FIX-015 follow-up PR #183: +347 lines / 9 files).

**Required grep depth-2 sweep**:

For each target frontend page in plan §Technical Spec:

1. **Enumerate child component tree** (depth-1): `grep -nE "import.*from.*@/features/<area>" frontend/src/pages/<route>/index.tsx` → list child component file paths
2. **Per child file — anti-pattern grep**: run plan-relevant pattern greps against each enumerated child file. Common drift class queries:

| Drift class | Plan claim pattern (in §Technical Spec) | Grep verify pattern (on each child component file) |
|-------------|------------------------------------------|---------------------------------------------------|
| **Shadcn-utility token residue** (AP-Phase2-C) | "page is verbatim-CSS aligned" / "Phase-2 re-pointed" | `grep -E "bg-card\|text-foreground\|border-border\|bg-muted\|text-muted-foreground" {child_file}` — non-zero = residue (FIX-012 retired `--sc-border`; FIX-015 closed governance + verification residue) |
| **Inline `style=` missing escape comment** (STYLE.md §1 + §3) | "no inline style violations" / "STYLE.md §3 escape used" | `grep -E "style=\{\{" {child_file}` + verify each match has adjacent `eslint-disable-next-line no-restricted-syntax` comment (FIX-015 CI fail lesson: 28 sites missed by agent) |
| **Outer wrapper artifact** (AP-Phase2-A) | "mockup has no outer wrapper" / "matches mockup root" | `grep -nE "<div style=\{\{[^}]*padding" {child_file}` — production-only padding wrappers (FIX-011 lesson — Sprint 57.19 vintage drift) |
| **Layout-class fullBleed drop** (AP-FullBleed) | "preserves AppShellV2 chrome" / "fullBleed prop intact" | `grep -nE "fullBleed\|chat-shell\|loop-canvas\|page-head" {child_file}` (FIX-010 lesson) |
| **Tab-shell vs monolithic structural divergence** | "matches mockup tab structure" | compare entry component's `<Tabs>` children vs mockup file's `<>` fragment / `.tabs-shell` structure — structural mirror mismatch = production tab-shell wraps mockup-monolithic content (Sprint 57.39 D-DAY1-1 root cause) |

**Recursion depth**: typical N = 2 (entry → direct children). Recurse to N = 3 only when the page architecture involves nested feature-area imports (rare; e.g. `chat-v2` blocks-of-blocks).

**Cost / benefit**:
- Per-page cost: ~5-10 min (1 import-grep + N anti-pattern greps per child component)
- Benefit: catches Sprint 57.39-class scope expansion at Day 0 instead of Day 1+ (1-5 hr saved per drift caught, depending on child count)
- **Skip when**: scope is non-frontend, first-time scaffolding (no existing tree to audit), or pages with no `import.*@/features/` consumers (single-file pages)

##### Prong 3 — Schema Verify (AD-Plan-4 promoted Sprint 57.1)

**Applies when**: sprint plan introduces NEW DB tables / Alembic migrations / ORM models / DB schema fields. Path verify (Prong 1) confirms file existence; content verify (Prong 2) confirms code patterns. Neither catches **column-level schema drift** between plan-time assumed schema and reality.

For every new table / migration / ORM model in plan §Technical Spec → grep DB column declarations against asserted schema before Day 1 starts:

- New table columns: `grep -A 30 "CREATE TABLE {table_name}\|class {ORM}\|table_args" backend/src/infrastructure/db/` — list every column + type + nullable
- Cross-table FK references: `grep -rn "ForeignKey.*{ref_table}\|REFERENCES {ref_table}" backend/src/infrastructure/db/` — confirm referenced table.column exists with matching type
- Migration head version: `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` — confirm next available number not already occupied
- RLS policy presence: `grep -A 3 "ENABLE ROW LEVEL SECURITY\|tenant_isolation_{table}" {migration_file}` — multi-tenant rule check (per `.claude/rules/multi-tenant-data.md` 鐵律)
- Plan-asserted column drift catch: re-read plan §Technical Spec column list; for each column → grep ORM file to confirm field name + type + nullable + default match exactly

Common schema drift classes:

| Drift class | Plan claim pattern | Schema-grep verify pattern |
|-------------|--------------------|----------------------------|
| **Claimed-but-missing column** | "table X has column Y" | `grep -n "{column_name}" {orm_file}` — 0 results = drift |
| **Claimed-but-wrong-type column** | "column Z is VARCHAR(64)" / "is NUMERIC(20, 4)" | `grep -A 1 "{column_name}" {migration_file}` — type mismatch |
| **Claimed-but-renamed table** | "INSERT into table_a" / FK to "table_b" | `grep -rn "table_a\|table_b" backend/src/infrastructure/db/` — actual name drift |
| **Claimed-but-occupied migration head** | "Alembic 0014_xxx" | `ls migrations/versions/ | sort -V | tail -3` — 0014 already exists → use 0015 |
| **Missing RLS policy** | new tenant_id table without RLS | `grep "ENABLE ROW LEVEL SECURITY\|tenant_isolation_{table}" {migration}` — 0 results = lint will fail |
| **Physical-column-vs-ORM-alias** (Sprint 57.60 PROMOTION) | "raw SQL `UPDATE tenants SET meta_data ...`" / "migration reads the `meta_data` column" | when a migration / raw SQL touches a column whose ORM attribute is an ALIAS (`mapped_column("physical_name", ...)`), the raw SQL MUST use the PHYSICAL column name, not the ORM attr. `grep -n "mapped_column(\"" backend/src/infrastructure/db/models/*.py` — any `mapped_column("X", ...)` where `X` ≠ the Python attr name = alias; raw SQL must quote `"X"`. ROI evidence (2-data-point): Sprint 57.59 D-DAY1-1 (tenants JSONB ORM attr `meta_data` is `mapped_column("metadata", ...)` in `identity.py`; the `0019` data-migration raw SQL had to use `"metadata"` not `meta_data` — caught mid-Day-1); Sprint 57.60 D-DAY0-M (applied pre-emptively at plan-time — `0020` raw SQL uses `"metadata"` from the start; 0 mid-sprint surprise). Codified Sprint 57.60 closeout per `AD-Day0-Prong3-Physical-Column-Read` PROMOTION. |

##### Catalog drift findings

In `progress.md` Day 0 entry under "Drift findings" header:

- Format: `D{N}` ID + Finding + Implication
- Cross-reference to plan §Risks (where finding may shift scope or risk profile)
- **Do NOT silently update plan §Technical Spec** — instead, add finding to plan §Risks. This preserves audit trail of what was originally planned vs. what reality forced. (See `anti-patterns-checklist.md` AP-2 — "no orphan code".)

##### Decide go/no-go for Day 1

- Findings shift scope by ≤ 20% → continue Day 1 with risk noted in §Risks
- Findings shift scope by 20-50% → revise plan §Acceptance Criteria + §Workload, re-confirm with user
- Findings shift scope by > 50% → abort sprint; redraft plan with reality baseline

#### ROI evidence (Sprint 55.6 promotion validation)

AD-Plan-3 was logged Sprint 55.4 candidate, validated Sprint 55.5 first application (5 drifts → 4-8× ROI), and **promoted to validated rule via Sprint 55.6 fold-in** based on cumulative evidence:

| Sprint | Application count | Drifts caught | Cost | Benefit prevented | ROI |
|--------|-------------------|---------------|------|-------------------|-----|
| 55.5 | 1st (Day 0 + 1 + 2) | 5 (D1+D2+D4+D5+D7) | ~55 min | ~3-4 hr re-work | 4-8× |
| 55.6 | 2nd-6th (Day 0-3) | 11 (D1-D11) | ~75 min | ~9-10 hr re-work + 2 production-grade bugs | 7-8× + 2 saves |

**D3 critical scope reduction in Sprint 55.6 alone**: AD-Cat8-2 dropped from "design + wire ~10-12 hr" to "wire-only ~5-6 hr" — caught via content grep (Prong 2), invisible to path verify (Prong 1).

**AD-Plan-4 Schema-Grep promotion ROI (Sprint 57.1 fold-in based on cumulative evidence)**:

| Sprint | Schema-Grep application | Drifts caught | Cost | Benefit prevented | ROI |
|--------|-------------------------|---------------|------|-------------------|-----|
| 56.1 | 1st (Day 0) | 2 (D26+D27 column-level) | ~30 min | ~1-2 hr re-work | 2-4× |
| 56.3 | 2nd (Day 0) | 1 (D6 sessions.total_cost_usd column) | ~20 min | ~1 hr re-work | 3× |
| **Cumulative** | **2 sprints** | **3 column drifts caught Day-0** | ~50 min | ~2-3 hr re-work | 3-4× |

Schema-Grep extends Prong 2 from code-pattern level to DB-column level. Without it, column drift surfaces at first migration / first ORM test run, costing 1-2 hr re-work per occurrence. With it, drift surfaces in Day 0 plan-verify pass at <30 min cost.

**AD-Plan-5 Frontend-Tree-Depth promotion ROI (Sprint 57.40 fold-in based on Sprint 57.39 + FIX-015 evidence)**:

| Sprint / FIX | Prong 2.5 application | Drifts caught | Cost | Benefit prevented | ROI |
|-------------|------------------------|---------------|------|-------------------|-----|
| Sprint 57.39 D-DAY1-1 | (pre-Prong-2.5 escape — Day 0 grep only checked entry component) | 1 drift surfaced mid-Day-1 (governance + verification child shadcn residue) | n/a (escape) | ~3-5 hr scope-expansion absorbed into follow-up PR #183 | (negative — what Prong 2.5 was designed to prevent) |
| FIX-015 post-hoc | Manual Day 0 grep across 6 child components | 6 drift files (4 confirmed AD-list + 2 NEW: ApprovalList + DecisionModal) | ~5 min | ~3-5 hr scope-creep avoided in original Sprint 57.39 | 36-60× |
| **Cumulative** | **2 applications** | **6 files (~28 inline-style sites secondary)** | ~5-10 min per Day 0 | scope-expansion avoidance | **20-60×** |

Frontend-Tree-Depth extends Prong 2 from entry-component grep to child-component-tree grep (depth N = 2). Without it, child drift surfaces at Day 1+ during code → either mid-sprint scope expansion OR follow-up FIX PR (Sprint 57.39 → FIX-015 pattern). With it, drift surfaces at Day 0 at <10 min cost, allowing scope adjustment in plan §Technical Spec before code starts.

#### Examples

**Sprint 53.7 D4-D12** (9 path-drift findings cost ~1 hr re-work — _why Prong 1 exists_):
- D4: Plan referenced `check_promptbuilder.py --root` arg behavior that did not match script
- D7-D8: Plan assumed lint scripts would silently accept missing `--root` flag; reality = silent-OK or exit 2
- D10-D12: Plan-stated `pytest` count baselines off by 2-5 tests vs. real repo at branch-creation time

**Sprint 55.3 D1-D3** (3 path-drift findings caught _before_ Day 1 code — _Prong 1 ROI validation_):
- D1: Plan assumed sole-mutator refactor needed for `agent_harness/`; grep showed three target patterns already grep-zero → AD-Cat7-1 scope 收斂 to enforcement test + lint
- D2: Plan assumed `verification_span` would be created; `verification/_obs.py` already had it → AD-Cat12-Helpers-1 became `extract` (non-create)
- D3: Plan assumed DB-backed `HITLPolicy` already partially wired; `DefaultHITLManager.default_policy` was in-memory only → AD-Hitl-7 baseline confirmed cleanly

**Sprint 55.6 D3 critical catch** (Prong 2 content-verify — _why AD-Plan-3 promotion exists_):
- 55.4 retro Q4 + 55.5 retro Q4 both narrated "AD-Cat8-2 needs full retry-with-backoff design"
- Day-0 content grep on `loop.py:_handle_tool_error` revealed: ABC implemented, called from main exec, error_policy/error_budget/circuit_breaker ALL wired — **only `_retry_policy` attribute is dead**
- Scope dropped from ~10-12 hr to ~5-6 hr; saved ~5-6 hr scope-creep design work
- Path verify (Prong 1) alone could not catch this: all referenced files exist; content gap requires Prong 2 grep

#### Cross-references

- `anti-patterns-checklist.md` AP-2 (no orphan / phantom code references — drift findings preserve audit trail vs. silent plan rewrite)
- `.claude/rules/file-header-convention.md` §Modification History (drift findings during refactor go in MHist; AD-Lint-MHist-Verbosity char-count budget complements this rule)
- §Common Risk Classes below (recurring drift patterns deserve catalog entries)

✅ **Correct flow**: Plan drafted → Checklist drafted → **Day-0 探勘 grep (Prong 1 path-verify + Prong 2 content-verify + Prong 3 schema-verify when DB schema in scope) + drift findings catalogued in progress.md** → Day 1 code starts.

❌ **Wrong flow** (Sprint 53.7 pre-AD-Plan-1): Plan drafted → Day 1 code → discover plan-vs-repo gaps mid-implementation → re-work checklist + plan + commits.

❌ **Wrong flow** (Sprint 55.5 pre-AD-Plan-3 first application): Path verify only (Prong 1) → Day 1 code → discover content gaps mid-implementation (file exists but body wrong; ABC doesn't exist; field uses wrong units).

❌ **Wrong flow** (Sprint 56.1 pre-AD-Plan-4 first observation): Path + content verify only (Prong 1+2) → Day 1 migration / ORM code → discover column drift at first migration test run (D26+D27 — column type / nullable mismatch).

---

### Step 3: Implement Code

**Only after both plan + checklist exist**.

**Workflow**:
1. Review sprint plan + checklist
2. Create feature branch: `git checkout -b feature/sprint-XX-Y-<scope>` (use scope from git-workflow.md)
3. Code against checklist deliverables (one at a time)
4. Commit frequently (one logical unit per commit)

**Prohibited** ❌:
- Starting code before plan/checklist approved
- Committing without checklist entry
- Scope creep without updating plan + checklist

---

### Step 4: Update Checklist During Implementation

**Daily workflow**:
- Morning: Review today's checklist tasks
- As you complete: `[ ]` → `[x]` (change, never delete)
- If blocked: Add notation `🚧 阻塞：<reason>` below the task, continue working or escalate
- End of day: Commit checklist updates

**Sacred Rule** (Phase 42 Sprint 147 violation):
- ❌ **Never delete** `[ ]` items that weren't done
- ❌ **Never hide** scope cuts by removing lines
- ✅ **Always mark**: `[x]` when done, `[ ]` when not (or abandon formally)

**Why**: Traceability. In retrospective, we see what was planned vs. shipped.

---

### Step 5: Create Progress & Documentation

**Daily (evening)**:
- Update `docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/progress.md`

#### 🆕 Step 5.5: Spike Sprint Design Note Extract Pattern（2026-05-08+ — closes doc-level rolling discipline）

**When to apply**:
若 sprint 是 **spike sprint**（用於探索新領域 / 新 gap fill — 例：Phase 57.7 IAM Block A spike / 57.8 SOC 2 + SBOM spike / 57.9 Status Page + APAC compliance spike）：**Day 4 closeout 必須額外產出 1 份 design note**（extract from real implementation）。

**When NOT to apply**:
若 sprint 是 **feature continuation sprint**（單純擴充已驗證範疇 — 例：Phase 57.4 admin tenants list 是延伸 57.3 tenant settings pattern reuse）：**不需** design note；只需 progress.md + retrospective.md。

#### 8-Point Quality Gate（design note submission checklist）

每個 spike-extract design note **必須**通過下列 8 條（reviewer 逐點驗證）：

- [ ] **1. Section header 對應 spike user story**
  - ❌ Generic：「OIDC overview」/「Authentication design」
  - ✅ Specific：「US-A2: OIDC PKCE Flow as wired in Sprint 57.7」

- [ ] **2. 每個技術 claim 有 file:line**
  - ❌「we use RS256」/「JWT validated via JWKS」
  - ✅「`JWTManager.encode()` at `backend/src/platform_layer/identity/jwt.py:42-58`」

- [ ] **3. Decision rationale 含比較矩陣**
  - ❌「Best practice」/「industry standard」
  - ✅ 三/四欄 vendor matrix + Cost / SCIM / SAML / Decision + 否決原因

- [ ] **4. Verification command（reproducible）**
  - ✅ `pytest tests/integration/auth/test_oidc_flow.py::test_real_entra_callback`
  - ✅ 或具體 manual reproduce step（curl + expected response）

- [ ] **5. Test fixture reference**
  - ✅ Link 到實際 test data / mock setup file
  - ✅ 若 real-LLM 測試，標明 `pytest -m real_llm` 與 cost 估算

- [ ] **6. Open invariant 明確分界**
  - ✅「Verified in this spike: A, B, C」+「Deferred to Phase XX.Y (NOT verified): D, E, F」
  - ❌ 將 deferred 內容寫入主 section 偽裝 verified

- [ ] **7. Rollback / fallback 路徑**
  - ✅「若設計後續證明錯，revert API routes at `auth.py` + DB column `external_id`；估 1-2 day」
  - ✅ 識別 sentinel / fallback 是否已存在
  - ❌ 假設「不會錯」

- [ ] **8. Cross-reference 17.md single-source**
  - ✅ 任何新 contract 必須在 `17-cross-category-interfaces.md` 對應 §section 登記
  - ✅ 若新增 ABC，標明 owner category
  - ❌ 在 design note 平行定義 contract（違反 single-source）

#### Quality 不是頁數，是 verified ratio

| 維度 | 14.md 風格（high page low quality） | Spike-extract 風格（mid page high quality） |
|------|-------------------------------|------------------------------------------|
| Verified ratio | 10.6% (91/862 行) | ≥ 95% |
| 每 claim 對應 file:line | ❌ 大部分 pseudo-code | ✅ 強制 |
| Decision rationale | ❌ 「primary IdP = Entra」無矩陣 | ✅ vendor comparison matrix |
| Verification reproducibility | ❌ 無 | ✅ pytest command + fixture |
| Maintenance | ❌ 半年內過時（57.5 揭示） | ✅ 隨 PR 同步 |
| 結果頁數 | 800+ 行 | 通常 200-500（outcome，非 cap） |

**禁止**：用「regulated 200-300 行」當品質替代品。重點是**禁止 speculation 充頁數**，不是壓縮 verified content。若 spike 真的學到 600 行 worth verified invariants，就寫 600 行。

#### Template

每個 spike-extract design note 使用 `claudedocs/templates/spike-design-note-template.md` 結構（含 8 sections：Spike Summary / Decision Matrix / Verified Invariants / Cross-Category Contracts / Open Invariants / Rollback / References / Modification History）。

#### Day 4 closeout 自查 record

retrospective.md 必須記錄：

```markdown
## Design Note Extract（spike sprint only）

**File**: `docs/03-implementation/agent-harness-planning/<doc-number>-<topic>.md`
**Verified ratio (estimated)**: __%
**8-Point Quality Gate**:
- [ ] 1. Section header
- [ ] 2. file:line 引用
- [ ] 3. Decision matrix
- [ ] 4. Verification command
- [ ] 5. Test fixture
- [ ] 6. Open invariant 分界
- [ ] 7. Rollback path
- [ ] 8. 17.md cross-ref

**Reviewer pass**: <user / self-review>
```


- Format:
  ```markdown
  # Sprint XX.Y Progress — YYYY-MM-DD

  ## Today's Accomplishments
  - Task X.Y completed (approx. Z min under/over estimate)
  - Issue: blockers, discoveries

  ## Remaining for Next Day
  - Task X.Z (pre-work done)

  ## Notes
  - Learning / decision / risk
  ```

**Sprint end**:
- Create `retrospective.md` covering: did well / improve next sprint / action items + estimate accuracy %

**Per-day estimates live here** (Sprint 55.3+ — AD-Lint-2 follow-on):
- Since checklist no longer carries "(Estimated X hours)" / "(Y min)" headers, **progress.md is the single home for per-day / per-task time tracking**.
- Format inside "Today's Accomplishments": `Task X.Y — actual Z min (est ~W min, delta ±N%)`
- Sprint-aggregate ratio computed in retrospective.md Q2 from sum of progress.md actuals vs. plan §Workload committed hours.
- Per-task estimates here are **non-binding individual record** — they help calibrate next sprint's bottom-up estimates but do not gate Day N completion.

**What NOT to do** ❌:
- "We'll update docs after the sprint" → too late, details lost
- Skip retrospective → patterns repeat
- Generic notes ("worked on stuff") → no data for future planning

---

## Sprint Closeout: CLAUDE.md + MEMORY.md Update Policy (Sprint 57.22+ — closes REFACTOR-001 Step 2)

**Trigger**: After Day N retrospective.md written, before opening next sprint plan. The 5-step workflow (§Mandatory 5-Step Workflow above) writes sprint execution artifacts (plan / checklist / progress / retrospective / memory subfile); this policy governs the **navigator files** (CLAUDE.md / MEMORY.md) — keep them lean, never archive sprint records inside them.

### Core Principle

| File | Role | What belongs |
|------|------|-------------|
| **CLAUDE.md** | Navigator / Principle / Rule | Timeless statements (mission / 11+1 範疇 / 5 大約束 / Mockup-Fidelity rule / Sprint Workflow rules / Karpathy / file-header convention); navigators to authoritative sources (V2 規劃文件導航 21 份 / ClaudeDocs structure / V1 reference table); current-phase milestone (1 line, principle-level) |
| **MEMORY.md** | Quality Pointer Index | Per-topic 1 pointer entry: subfile link + 1-sentence topic + keywords for future retrieval |
| **Memory subfile** (`memory/project_phase57_XX_*.md`) | Per-sprint detail | Full retro highlights / calibration / carryover ADs / file change list |
| **Retrospective** (`docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/retrospective.md`) | Authoritative full Q1-Q7 retro | Sprint-level truth source |
| **Sprint plan §Workload** | Calibration source-of-truth | Multiplier / ratio per scope class |
| **`claudedocs/1-planning/next-phase-candidates.md`** | Open items / pending decisions | Next Phase 候選 / carryover AD list |
| **Git log + PR description** | Commit-level + sprint-level ground truth | Authoritative |

**Single-source rule**: Sprint detail lives in **memory subfile + retrospective.md** only. CLAUDE.md / MEMORY.md are pointers, NOT archive.

### CLAUDE.md Update at Sprint Closeout — Minimal Touch

**Allowed** ✅:
- Update `Current Sprint` row — 1 line. **Two cases**: (i) a next sprint is selected → next sprint id + branch name; (ii) **rolling-discipline interregnum** (sprint merged, next NOT yet selected) → `**No active sprint** (awaiting next-phase selection) — last shipped Sprint XX.YY MERGED (PR #N, main <sha>)`, NOT a stale `PR-pending`
- **Post-merge status flip** (codified 2026-06-16; closes the interregnum-staleness gap): closeout doc edits are written during Day 4 **before** the PR merges → they label the sprint `PR-pending` / `NOT pushed`. After a `gh`-verified merge, flip those labels → `MERGED (PR #N, main <sha>)` on the TWO current-status surfaces only — CLAUDE.md `Current Sprint` row + `next-phase-candidates.md` head carryover block. Older per-sprint carryover blocks are historical snapshots (each PR# is recoverable from its memory subfile + git log) — do a truthful batch `PR-pending → MERGED` sweep only if they accumulate misleadingly (one done 2026-06-16 for Sprint 57.112-126), not every closeout
- Update `Last Updated` footer line — 1 line: `**Last Updated**: YYYY-MM-DD (Sprint XX.YY — short goal); see memory/ for sprint history`
- Update `Phase` / `Roadmap` row IF milestone reached (e.g. V2 22/22 → SaaS Stage 1 1/3, Phase 57+ Frontend N/N+1)
- Update `Tech Stack` / `Architecture` / `Branch Protection` rows IF actually changed (rare; e.g. CI policy change)
- Add new principle / rule sections (e.g. Sprint 57.19's new "Frontend Mockup-Fidelity Hard Constraint" — that's a timeless rule, belongs here)

**Forbidden** ❌:
- Add `Latest Sprint` / `Prev Sprint` / `Prev-Prev Sprint` / `Prev³` / `Prev⁴` rows packed with retro detail
- Pack carryover ADs / calibration ratios / commit SHAs / PR numbers / Vitest counts / bundle KB sizes / file change lists into any table cell
- Add multi-paragraph history blocks to `Last Updated` footer
- Add `[Sprint XX historical row preserved below]` archive blocks at end of CLAUDE.md
- Inline `Next Phase 候選` 20-bullet pending lists into a table cell

**Violation Pattern** ❌ (pre-cleanup state captured by REFACTOR-001 audit 2026-05-18): CLAUDE.md grew from ~30 KB foundation to **77 KB** over 20+ Phase 57+ sprints; ~58 KB was duplicate sprint records (table cells × 6 sprints + footer multi-paragraph history + `[historical row preserved]` blocks + 20-bullet `Next Phase 候選`).

### MEMORY.md Update at Sprint Closeout — Quality Pointer

**Allowed** ✅ — Add 1 entry of this shape (~250-300 char total, 3-4 lines):
```markdown
- [project_phase57_XX_<topic>.md](project_phase57_XX_<topic>.md) — Sprint XX.YY closed YYYY-MM-DD; <1-sentence what>; <1 phrase distinguishing feature or anomaly>.
  Keywords: <feature/AD/class/anomaly names for future retrieval>
```

Example (good pointer):
```markdown
- [project_phase57_21_chatv2_mockup_fidelity_phase_1.md](project_phase57_21_chatv2_mockup_fidelity_phase_1.md) — Sprint 57.21 closed 2026-05-18; Chat-v2 Turn Block Model + 3-col shell + Inspector 4-tab + Composer scaffolding; bimodal calibration pattern emerging.
  Keywords: chatv2, mockup-fidelity Phase-1, Turn Block, Inspector 4-tab, frontend-mockup-direct-port class, bimodal ratio
```

**Forbidden** ❌:
- Dump retro Q1-Q7 content into the entry
- List specific calibration ratio numbers (those live in subfile + `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`)
- List commit SHAs / PR numbers / Vitest counts / bundle KB sizes (in subfile + retrospective)
- Make entry >500 char (~300 is comfortable ceiling; quality matters more than rigid limit per user 2026-05-18 — but >500 signals you're packing summary instead of pointing)

**Quality Criteria** — Does the pointer let future AI / dev find this sprint when they search by keyword?

| Quality | Example |
|---------|---------|
| ✅ Good keywords | feature name (`chatv2`, `mockup-fidelity`) / AD ID (`AD-Tailwind-v4`) / class name (`frontend-mockup-direct-port`) / anomaly pattern (`bimodal`, `silent CSS no-op`) |
| ❌ Bad keywords | generic terms ("frontend", "refactor") / date-only / sprint-id-only / numbers without context |

**Header rule statement** (in MEMORY.md opening): the prior「每行 ≤ 200 字符」hard limit is updated to「**quality pointer principle**: topic + keywords + subfile path; detail single-source in subfile; ~300 char comfortable ceiling, but quality matters more than character count」per user clarification 2026-05-18.

### Open Items / Pending Decisions Destination

**Forbidden** ❌:
- `Next Phase 候選` 20-bullet lists in CLAUDE.md table cells (was pre-cleanup case)
- Pending AD candidates / unresolved issues in CLAUDE.md table cells
- Time-bound TODOs / schedule notes in CLAUDE.md

**Allowed** ✅:
- Maintain `claudedocs/1-planning/next-phase-candidates.md` as **single-source** for open / pending items
- Sprint plan §Carryover section (in `docs/03-implementation/agent-harness-planning/phase-XX-*/sprint-XX-Y-plan.md`) lists carryover ADs for next sprint pickup
- Sprint retrospective.md §Carryover section accumulates per-sprint additions to the candidate pool
- `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` tracks cross-sprint calibration trends

### Self-Check at Sprint Closeout (Pre-Commit)

Before commit closeout MHist, verify:

- [ ] **CLAUDE.md changes**: Only navigator / principle / rule level? (NO sprint-by-sprint history record additions)
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)? (NOT a packed retro summary)
- [ ] **Sprint detail preserved**: Memory subfile + retrospective.md updated with full content? (YES — single-source preserved elsewhere)
- [ ] **Carryover / open items**: Documented in next sprint plan §Carryover or `claudedocs/1-planning/next-phase-candidates.md`? (NOT in CLAUDE.md table cell)
- [ ] **Calibration ratio**: Tracked in `sprint-workflow.md §Scope-class multiplier matrix`? (NOT in CLAUDE.md / MEMORY.md prose)

### Why This Policy Exists (REFACTOR-001 root cause analysis 2026-05-18)

V2 evolved organic CLAUDE.md + MEMORY.md bloat pattern over Phase 57+ ship sprints (20+ sprints accumulated):
- **CLAUDE.md** grew from ~30 KB foundation to **77 KB**; ~58 KB ≈ duplicate sprint records
- **MEMORY.md** exceeded its own ≤24.4 KB system limit (actual 28 KB); 12 entries violated own ≤200 char rule (worst: 57.17 entry at ~3000 char = 15× over)
- ~9-12% session context window consumed by duplicates at session start
- **Triple-source for same sprint detail**: CLAUDE.md table cell + CLAUDE.md footer + MEMORY.md entry + memory subfile + retrospective.md (5 copies of overlapping content)

**Root cause**:
1. AI sprint-closeout pattern dumped full retro Q1-Q7 highlights into "index" entries (forgot single-source principle)
2. Sprint table cells accumulated history without archive cutoff or policy
3. No enforcement (no lint, no review checkpoint)
4. "捨不得刪" mentality: each prev sprint row felt "still useful" → kept indefinitely

**Fix**: This policy (§Sprint Closeout) + REFACTOR-001 Step 3 cleanup execution.

### Cross-References

- `claudedocs/4-changes/refactoring/REFACTOR-001-claude-md-memory-md-bloat-audit.md` — initial trigger audit (Step 1/4)
- `.claude/rules/file-header-convention.md` §Modification History char-budget rules — sibling philosophy (MHist 1-line max, detail in commit body / 4-changes record)
- MEMORY.md header rule statement — quality pointer principle (post-2026-05-18 rewording)
- `claudedocs/1-planning/next-phase-candidates.md` — open items / Next Phase 候選 single-source (created in REFACTOR-001 Step 3)

---

## Common Risk Classes (Sprint 53.7+ — closes AD-CI-4)

When drafting plan §Risks, consider these recurring risk classes (V2 carryover evidence). Each entry: `Symptom → Workaround → Long-term fix`.

### Risk Class A: Paths-filter vs `required_status_checks` (CI infra) — ⚠️ RETIRED Sprint 55.6

**Status**: **NO LONGER APPLIES.** Sprint 55.6 removed the `paths` filter from `.github/workflows/backend-ci.yml` (Option Z, closes AD-CI-5) → **every PR now runs full backend CI + v2-lints**, including docs-only / `.gitignore`-only PRs. There is no paths-filter `BLOCKED` situation and **no touch-`backend-ci.yml` workaround is needed**. The `backend-ci.yml` header is the authoritative source.

**Historical (53.2.5 – 55.6, audit trail)**: docs-only PRs once didn't trigger the path-filtered backend-ci → required contexts never reported → `mergeStateStatus = BLOCKED`. Interim fix was a header-comment touch on `backend-ci.yml` (53.2.5). Retired permanently in 55.6 by dropping the paths filter (trade-off ~+1.5 min CI per docs-only PR; acceptable for solo-dev volume).

**Residual edge case (NOT paths-filter)**: a rare GitHub webhook miss/delay can still leave checks unreported (e.g. PR #203, Sprint 57.53) — a header touch re-triggers, but that is a webhook quirk, not the retired paths-filter issue.

### Risk Class B: Cross-platform `mypy --strict` `unused-ignore` (Python tooling)

**Symptom**: 同一 import / Optional unwrap 在 Linux runner 與 Windows 開發機 mypy 行為不同（缺 stub 包 vs 有 stub 包）。`# type: ignore[X]` 在一邊需要、在另一邊變 `unused-ignore` 報錯（`warn_unused_ignores=true` strict 模式下）。

**Source**: Sprint 52.6 retrospective Q4.

**Workaround**: 雙 ignore code → `# type: ignore[X, unused-ignore]`. 兩邊都不報錯. Documented in `.claude/rules/code-quality.md` §Cross-platform mypy pattern.

**Long-term fix**: Pin Python stub package versions in `pyproject.toml` so both platforms behave identically. Independent.

### Risk Class C: Module-level Singleton Across Test Event Loops (test isolation)

**Symptom**: TestClient-based integration tests 共用 module-level singletons (e.g. `service_factory` cache / `RiskPolicy` DB cache / `MetricsRegistry`) → 第二次 fixture activate 拿到上一個 event loop 的 cached instance → 「event loop closed」cascade fail.

**Source**: Sprint 53.6 Day 4 (US-5 ServiceFactory consolidation introduced; 5 governance / audit tests failed until autouse `reset_service_factory` fixture added).

**Workaround**: Per-suite `conftest.py` autouse fixture calling `reset_*()` for affected singletons. Pattern documented in `.claude/rules/testing.md` §Module-level Singleton Reset Pattern (since 53.7).

**Long-term fix**: Refactor singletons to be DI-injected per-request (no module-level cache); avoids root cause. Per-singleton scope; track as needed.

**Related (Sprint 57.68 reinforcement, `AD-Source-DB-Call-Test-Isolation`)**: Adding a NEW DB call to a previously DB-free endpoint can surface a latent isolation leak — TestClient overrides auth but NOT `get_db_session`, so the endpoint hits a non-test session. Symptom: tests that passed pre-change fail only after the endpoint gains a query. Fix: ensure the suite's `get_db_session` dependency override (or autouse session fixture) covers the newly-DB-touching endpoint.

### Risk Class D: ORM File Path Reference Style (sprint planning)

**Symptom**: Plan §8 Risks row references an ORM model with a speculation-based path like `backend/src/infrastructure/db/models/<table_name>.py` (e.g. `tenant.py`); Day 0.8 Prong 2 then wastes 3-5 min discovering the model lives elsewhere (e.g. `identity.py` per domain cohesion grouping).

**Source**: Sprint 57.50 D-DAY0-2 — plan referenced `Tenant.meta_data` JSONB; AI initially looked at `tenant.py` (did not exist); Prong 2 grep resolved to `identity.py` per `09-db-schema-design.md` Group 1 (Identity & Tenancy domain groups User + Role + OIDCProvider + Tenant in one file). Verified in Sprint 57.51 Day 0.8 D-DAY0-3.

**Workaround**: Cite `09-db-schema-design.md §Group N <Domain Name>` in plan §Risks rows touching ORM models, not the speculation-based `.py` path. Example: "Risk: `Tenant.X` field doesn't exist — mitigation: Day 0.8 Prong 2 read `Tenant` ORM in `09-db-schema-design.md §Group 1 Identity & Tenancy` (note: file is `identity.py`, not `tenant.py`)."

**Long-term fix**: Codify in Plan template stub (when Plan template doc is formalized as part of `.claude/rules/`).

### Risk Class E: Stale long-running `--reload` backend masks a wiring/startup fix (local verification)

**Symptom**: A fix that only takes effect at process startup (lifespan wiring, env load, DI singleton construction) appears NOT to work when verified against an already-running dev backend — because the running process started BEFORE the fix landed (or its `--reload` worker reloaded module code but did NOT re-run lifespan startup). Looks like a code bug; is actually process-state.

**Source**: 2026-06-03 C-11 `cost_ledger Δ=0` (`AD-RealLLM-CostLedger-ProcessState-Verify`). FIX-022 pricing-loader wiring was on disk, but the running backend had `cost_ledger_service=None` from its own stale startup → router gate skipped every cost row. A clean restart → startup log `pricing loader wired` (`main.py:149`) → `cost_ledger Δ=2`. Compounded by 2 stale `--reload` reloaders sharing :8000 via SO_REUSEADDR (Errno 10048 on re-bind).

**Workaround**: When verifying startup/wiring behavior locally, do a CLEAN restart first: kill ALL stale uvicorn reloader+worker processes on the port (not just the listener — a `--reload` worker is a `multiprocessing.spawn` child whose cmdline lacks `uvicorn`), confirm the port is free + your new process is the sole owner (no Errno 10048), then re-verify and capture the startup log line proving the wiring fired.

**Reinforcement (Sprint 57.97, D-DAY3-1 — orphaned spawn-worker)**: The drive-through verifying cheap-tier verification recorded the STRONG model on the first 2 chats despite a `dev.py restart` reporting a fresh PID — and it was NOT a code bug (a reproduce-script proved the builder built the cheap client). The real culprit: an orphaned `multiprocessing.spawn` worker (a child of a long-DEAD reloader from a PRIOR sprint) was STILL ALIVE serving :8000 via SO_REUSEADDR with old code + old `.env`. `dev.py stop` + `netstat` + `taskkill /PID <port-owner>` ALL missed it because the socket was attributed to the dead PARENT and the worker's cmdline is `python -c "from multiprocessing..."` (no "uvicorn"). **A clean restart must verify the LIVE serving process, not the port-owner PID.** The reliable check on Windows: `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` → inspect PID / PPID / StartTime → `Stop-Process -Force` any worker whose parent is dead or whose StartTime predates the current restart. For startup-only/env-loaded behavior (the cheap client is built at startup from `.env`), set the env BEFORE the restart and confirm the fresh PID is the SOLE live worker.

**Long-term fix**: Prefer `python scripts/dev.py restart backend` (kills by port owner) over assuming the running process is current; for one-off wiring checks, a no-`--reload` single process with log redirect gives a deterministic startup log. When SO_REUSEADDR orphans recur, fall back to the `Win32_Process` PID/PPID/StartTime sweep above (port-owner kills are insufficient against spawn-worker orphans).

### How to use this section

When drafting plan §Risks, scan this catalog. If any class applies to your sprint scope, copy the symptom + workaround text into your plan §Risks table. Add new classes here when 2+ sprints hit the same root cause.

---

## Change Record Conventions

When fixing bugs or implementing features, create corresponding document in `claudedocs/4-changes/`:

| Type | Directory | Naming | When |
|------|-----------|--------|------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` | Any bug fix |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` | Feature enhancement |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` | Code restructure |

**Format** (1 page):
```markdown
# FIX-123: <Description>

**Date**: 2026-05-15
**Sprint**: 50.2
**Scope**: <11+1 category or cross-cutting>

## Problem
2-3 sentences. What was broken?

## Root Cause
Analysis. Why did it happen?

## Solution
What we changed. Code location. PR reference.

## Verification
How we confirmed it's fixed (test name, manual steps).

## Impact
Scope of fix (backend-only? frontend? integration?).
```

**Daily Workflow**:
1. **Morning**: Check `claudedocs/3-progress/daily/` latest log
2. **When fixing bug**: Create `claudedocs/4-changes/bug-fixes/FIX-XXX-<issue>`
3. **When changing feature**: Create `claudedocs/4-changes/feature-changes/CHANGE-XXX-<feature>`
4. **End of day**: Use SITUATION-5 to save progress (which creates daily log entry)

---

## Sprint Naming & Directory Structure

**Standard format** (from 06-phase-roadmap.md):

```
phase-XX-name/
├── sprint-XX-Y-plan.md           ← Must exist before coding
├── sprint-XX-Y-checklist.md      ← Must exist before coding
└── ...

agent-harness-execution/
└── phase-XX/
    └── sprint-XX-Y/
        ├── progress.md           ← Daily entries during sprint
        ├── retrospective.md      ← End of sprint
        └── artifacts/            ← Evidence files
```

**Branch naming** (from git-workflow.md):
```
feature/sprint-XX-Y-<scope>
```

**Commit messages**:
```
feat(<scope>, sprint-XX-Y): <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Common Violation Patterns & Consequences

| Pattern | Evidence | Why Bad | Fix |
|---------|----------|---------|-----|
| **Skip Plan** | Code appears without plan.md | Unknown scope → unclear PR → rework | Always: plan → checklist → code |
| **Skip Checklist** | Implementation doesn't track tasks | Can't measure progress; retro blind | Checklist = truth table; mandatory |
| **Delete `[ ]` items** | Checklist shrinks mid-sprint | Hides scope cuts; retro can't diagnose (Phase 42) | Only mark `[x]` or note `[阻塞]` |
| **Update checklist after sprint** | Checklist retroactively filled in | Data quality → estimates useless | Update daily, during work |
| **Skip progress.md** | "Will write at end" | Details lost; retro weak | Write daily 10-min entry |
| **No Change records** | Bugs fixed in silence | No audit trail; same bug reappears | FIX/CHANGE/REFACTOR every time |
| **Vague DoD** | "Implement X" → what counts as done? | Infinite rework; unclear when to stop | DoD: testable + measurable |
| 🆕 **Format inconsistency** (Sprint 52.1 v1) | New plan has different section count / naming / Day count than prior completed sprint | Hard to navigate; mental overhead; user must matrix-correct | Read prior sprint's plan + checklist BEFORE drafting; mirror structure; scope differences expressed through content, not structure |

---

## Error Flow: Phase 35-38 Shortcut (DO NOT REPEAT)

```
❌ WRONG:
Phase README → Code (skip plan + checklist) → Progress Doc (scatter, incomplete)
            → Pull request with unclear scope
            → Retro says "we don't know what was planned"
```

```
✅ RIGHT:
Phase README → Sprint Plan (user stories + technical spec)
            → Sprint Checklist (task breakdown + DoD)
            → Code (implement against checklist)
            → Update Checklist (daily: [ ] → [x])
            → Progress Doc (daily progress + retrospective)
            → Pull request with full traceability
            → Retro: "estimate accuracy 85%; unblock story X.Y for next sprint"
```

---

## Daily Workflow Example

**Morning (9 AM)**:
1. Review `claudedocs/3-progress/daily/` latest entry
2. Open sprint checklist (e.g., `sprint-49-1-checklist.md`)
3. Today's tasks: **Day 2.1 — 2.4** (estimated 6 hours)
4. Create feature branch if first day

**During work**:
- Per-task estimate vs actual; mark `[x]` immediately upon completion
- If blocked, add `🚧 阻塞 (HH:MM): <reason>` and switch to another task
- Commit per logical unit with sprint scope in message

**End of day (4 PM)**:
1. Update checklist (today's done tasks `[x]`)
2. Commit checklist changes
3. Write `progress.md` entry (estimate vs actual + notes)
4. Create FIX/CHANGE/REFACTOR record if applicable

---

## Before Commit Checklist

Every commit must pass:

1. **Correspond to Sprint Checklist**
   - Commit message matches task ID
   - Checklist `[ ]` → `[x]` done before or immediately after commit

2. **Lint + Format** (from code-quality.md)
   - Backend (per-file format + type chain): `black . && isort . && flake8 . && mypy .`
   - Backend (V2 architecture lints — 6 scripts; closes AD-Lint-1 since Sprint 53.7): `python scripts/lint/run_all.py`
     - One-stop wrapper invokes 6 V2 lints with correct `--root` args (check_ap1: `backend/src` / check_promptbuilder: default `backend/src/agent_harness` / 4 auto-discover)
     - Exit 0 = all 6 green; non-zero = `<failed>/6` with per-script line summary
     - Replaces the prior 6 separate invocations (which silently mis-passed when `--root` arg mismatched script expectation — see Sprint 53.7 Day 0 drift D1)
   - Frontend: `npm run lint && npm run build` — **MUST run WITHOUT `--silent` flag** (Sprint 57.40 closes AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern). FIX-015 PR #183 CI failed in 30s with 28 ESLint `no-restricted-syntax` errors that local `npm run lint --silent` swallowed; the `--silent` flag suppresses lint error output along with package-manager noise. **Never** use `--silent` for the pre-push lint check; if you want clean output, redirect with `2>&1 | tail -20` instead (preserves errors while trimming noise).

3. **Tests Passing**
   - Backend: `pytest` (>= 80% coverage for new code)
   - Frontend: `npm run test` (>= 80% coverage)

4. **Sprint Workflow Compliance** (anti-patterns-checklist.md 11 points)

5. **No Prohibited Imports**
   - Backend agent_harness: no direct `import openai` / `import anthropic`

6. **File Headers Updated** (file-header-convention.md)

7. **Agent-delegated work — run ALL gates yourself; don't trust the agent's report** (Sprint 57.69 + 57.73)
   - Delegated FE work MUST run the FULL gate set incl. `npm run check:mockup-fidelity` (not just lint/build/test). Sprint 57.69: a delegated agent ran lint/build/test but skipped `check:mockup-fidelity`; 2 `oklch(...)` tints would have silently failed `HEX_OKLCH_BASELINE` at PR — parent re-verify caught it pre-PR.
   - Pin language / convention in the agent prompt: user-facing copy follows the codebase convention (English state strings, not 繁中). Sprint 57.73: a delegated agent wrote 繁中 state copy the parent had to rewrite.
   - Parent independent re-verify: re-run every gate yourself; treat the agent's "all green" as unverified until reproduced (57.66 stringified-float / 57.67 flat-vs-nested / 57.68 wrong isolation culprit were all caught this way).
   - Tooling: if Bash `grep` output looks corrupted (e.g. token substitution), re-read via a dedicated reader (Read/Grep tool) before acting on it (Sprint 57.70).

8. **Drive-Through Acceptance — user-facing features must be DRIVEN, not just gated** (2026-06-06; closes AD-Drive-Through-Acceptance; full rationale CLAUDE.md §Drive-Through Acceptance Hard Constraint + `memory/feedback_drive_through_over_paper_metrics.md`)
   - Any feature a human reaches through the UI MUST be verified by actually driving the real UI (dev server) + real backend + real LLM (NOT echo/mock) through its primary path BEFORE it can be marked done. Gate-pass + curl prove the parts work / the API responds; NEITHER proves the car drives.
   - Walk every control on the path: clickable? has an effect? label real (not hardcoded / fixture)? does the result actually render? (chat-v2 escape 2026-06-06: dead "New session" button + fixture session list + hardcoded `claude-haiku-4-5` badge + agent answer never rendered — all AP-4 Potemkin sitting on the 主流量, all green on every gate. PR #253 also wrote "~80-85% working" off curl-only verification with "UI 驅動未做" self-noted — exactly the trap.)
   - Do NOT write "verified" / "~X% working" for anything whose drive-through layer wasn't actually run — write "未驗證 (gate-only)" instead. Backend-not-ready widgets: render per mockup with fixture data BUT label DEMO (or leave blank) — never let fixture masquerade as real.
   - Evidence: screenshot + "observed vs intended flow" diff into progress.md / CHANGE record.
   - Scope: applies to any task touching a user-facing surface (frontend page / SSE-driven flow / API a human drives via UI). Pure-backend / pure-infra tasks that no human drives through a UI are exempt — but their reports MUST say "gate-only verified", not imply usability.

---

## Prohibited Actions

- ❌ Force push to main
- ❌ Commit without corresponding checklist entry
- ❌ Delete unchecked `[ ]` items from checklist
- ❌ Skip progress.md updates (update daily)
- ❌ Skip FIX/CHANGE/REFACTOR records for bug/feature changes
- ❌ Code before plan + checklist exist
- ❌ Commit secrets, large binaries, generated files
- ❌ Scope creep without updating plan
- ❌ Mark a user-facing feature done — or report it "verified / ~X% working" — without an actual drive-through (real UI + real backend + real LLM); gate-pass / curl is NOT drive-through (AD-Drive-Through-Acceptance; see Before Commit item 8)

---

## References

| Document | Purpose |
|----------|---------|
| CLAUDE.md §Sprint Execution Workflow | High-level discipline |
| CLAUDE.md §ClaudeDocs — Change Records | FIX/CHANGE/REFACTOR conventions |
| 06-phase-roadmap.md | 22 sprint overview + naming |
| sprint-49-1-plan.md | Plan template |
| sprint-49-1-checklist.md | Checklist template |
| git-workflow.md | Commit message format + scope |
| anti-patterns-checklist.md | 11-point code review checklist |
| category-boundaries.md | 11+1 scope isolation rules |
| file-header-convention.md | Header + Modification History format |

---

**Applies To**: V2 Phase 49+ (all 22 sprints)
