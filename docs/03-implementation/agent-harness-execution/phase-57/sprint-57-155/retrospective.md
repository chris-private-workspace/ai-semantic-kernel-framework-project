# Sprint 57.155 Retrospective — CARRY-026 Slice 1: user-layer semantic memory recall

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-155-plan.md) · [Progress](./progress.md) · CHANGE-122 · design note 58

## Q1 — What did we deliver?

The first vector/embedding recall on the Cat 3 memory L4 user layer (CARRY-026 Slice 1, logged Sprint 51.2, unblocked 57.146/57.147). NEW `MemoryVectorIndex` (mirrors `KnowledgeVectorIndex`) + `UserLayer.read` semantic branch (off = byte-identical / on = cosine-ranked, fail-soft) + `MEMORY_VECTOR_ENABLED` opt-in singleton + `QdrantVectorStore.count(payload_filter)` + factory injection. Backend-only: NO migration / wire / frontend. 17 new tests (9 index + 3 qdrant + 2 UserLayer + 3 singleton + 2 real-DB integration). Drive-through PASS (real Azure `text-embedding-3-large` + real Qdrant; clean per-user isolation).

## Q2 — Estimate accuracy (calibration)

- Scope class **NEW `memory-vector-recall-spike` 0.60** (1st data point). Bottom-up est ~12.5 hr → class-calibrated commit ~7.5 hr (mult 0.60), parent-direct `agent_factor 1.0` (3-segment).
- **Actual ≈ committed → ratio ~1.0, IN band → KEEP 0.60.** The sprint ran clean: Day-0 三-prong was 0-drift (1 scope REDUCTION — AP-8 needed no allowlist), the code mirrored a proven pattern (57.146/147), and the drive-through went smoothly first try (no re-architecture, no re-drive; the one mid-run HITL pause on priya was an unrelated 57.106 per-tenant policy, approved to continue). This matches the anchor siblings `knowledge-embedding-vector-spike` 0.60 (57.146) + the `memory-*` spikes 0.60 — a real-code core (new index + layer branch + singleton + 17 tests ≥~3.5 hr) that HELD the 0.60 per the 57.137 lesson (NOT a tiny-code 0.85 re-point).
- If a 2nd `memory-vector-recall-spike` (e.g. L1/L2 layers) lands > 1.20, re-point toward 0.70 (the real-Azure-embeddings + real-Qdrant drive-through is the variance driver, per the 57.146 note).

## Q3 — What went well?

- **Mirror-a-proven-pattern paid off**: reusing `EmbeddingClient`/`QdrantVectorStore`/`QdrantNamespaceStrategy` (49.3 pre-reserved `"user_memory"`) meant ZERO new ABC/infra — the slice was wiring + one new index class. The knowledge arc (57.145-147) de-risked every pipeline.
- **Day-0 三-prong caught the AP-8 scope reduction**: reading `check_promptbuilder_usage.py:132` (flags only `.chat()`/`.stream()`) confirmed the embed/search-only index needs no allowlist — one fewer file than the plan's conditional.
- **Byte-identical-when-off design held**: the `if not semantic_hits: return keyword_hints` short-circuit preserved the 57.150 keyword path + the semantic-only `[]` stub — the kept stub test + full suite (3123) prove no regression.
- **Machinery-level drive-through evidence**: the backend log (`built` + per-user `ingested`) + direct Qdrant inspection (7 pts, jamie 5 / priya 2, 3072-dim Cosine) gave concrete, attribution-free proof the semantic axis is LIVE + isolated — independent of the `profile()` confound.

## Q4 — What to improve next sprint?

- **The `profile()` attribution confound** (Q3 of the drive-through): the always-on `profile()` (57.148) surfaces the same fact keyword-independently, so a few-fact behavioural drive-through cannot isolate the semantic axis's recall value from `profile()`. Next time (or for a follow-on A/B) construct a MANY-fact scenario where `profile()`'s top-k cap drops the query-relevant fact, so the semantic axis is the ONLY path that surfaces it. Logged `AD-Memory-Vector-Recall-Precision-AB`.
- **`knowledge_search` muddied Leg 2**: the agent reached for the KB tool on a "who owns…" query. A cleaner personal-memory phrasing ("what do you remember about ME") would avoid the KB detour. Noted for future memory drive-throughs.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ the index is reached from the chat main flow via `make_chat_memory_deps` → `build_handler` (drive-through proved it runs). No orphan.
- **AP-3** (cross-dir scatter): ✅ index in `agent_harness/memory/`, singleton in the api composition layer (mirrors `knowledge_index.py`). No scatter.
- **AP-4** (Potemkin): ✅ NOT a stub — drive-through shows real Qdrant points + isolation; the semantic-only `[]` is the honest OFF path, not a Potemkin.
- **AP-6** (future-proofing): ✅ opt-in flag has a real use-case (drive-through); per-tenant override deferred (not pre-built).
- **AP-8** (PromptBuilder / neutrality): ✅ index imports only the `EmbeddingClient` ABC + Qdrant (no provider SDK); embed/search ≠ chat → no AP-8 allowlist needed; `run_all` 11/11 (llm_sdk_leak + check_promptbuilder green).
- **AP-11** (version suffix): ✅ no `_v2`/`_new` names.
- v2 lints: **11/11 green**.

## Q6 — Carryover (→ next-phase-candidates)

`AD-Memory-Semantic-Axis-System-Tenant-Layers` (L1/L2 slices) · `AD-Memory-Session-Summary-Semantic-Rank` (57.151 recency→semantic) · `AD-Memory-Semantic-NearDup-Dedup` (extend 57.150) · `AD-Memory-Vector-Incremental-Write` (embed-on-write + orphan cleanup) · `AD-Memory-Vector-PerTenant-Phase58` (C3 override) · `AD-Memory-Vector-Recall-Precision-AB` (many-fact semantic-vs-profile A/B) · `AD-Memory-Vector-Inspector-Phase58` (chat-v2 "semantic hit this turn" surface).

## Q7 — Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/58-memory-vector-recall-design.md`
**Verified ratio (estimated)**: ~95% (every claim has a file:line + a test/verify command; the one honest un-verified item — semantic-vs-profile attribution — is explicitly split into §5 Open Invariants).
**8-Point Quality Gate**:
- [x] 1. Section header maps to the spike US (§1 "semantic recall on the user memory layer")
- [x] 2. file:line per claim (§3 invariants)
- [x] 3. Decision matrices (§2.1 ingest / §2.2 isolation / §2.3 read-branch)
- [x] 4. Verification commands (§3 pytest names + full-suite command)
- [x] 5. Test fixtures referenced (§7: the 4 test files)
- [x] 6. Open-invariant split (§5 verified vs deferred — incl. the honest `profile()` attribution caveat)
- [x] 7. Rollback path (§6 flag→False, 1 line + restart)
- [x] 8. 17.md cross-ref (§4 — reuses `EmbeddingClient` ABC §2.1, no new contract)

**Reviewer pass**: self-review.
