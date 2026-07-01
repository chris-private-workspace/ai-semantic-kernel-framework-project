# 58 — Cat 3 Memory Semantic Axis: user-layer vector recall (design note)

**Purpose**: Extract the verified design of the Sprint 57.155 memory semantic axis (CARRY-026 Slice 1) — the first vector/embedding recall on the L4 user memory layer, mirroring the 57.146/57.147 knowledge vector pattern.
**Category / Scope**: 範疇 3 (Memory) — semantic axis / Phase 57 / Sprint 57.155
**Created**: 2026-07-01
**Status**: Active
**Slice**: closes `CARRY-026` Slice 1 (L4 user; L1/L2/session = remaining slices)

> **Modification History**
> - 2026-07-01: Initial creation (Sprint 57.155) — user-layer semantic recall (KEEP; drive-through PASS)

---

## 1. Spike Summary (US: semantic recall on the user memory layer)

`CARRY-026` (logged Sprint 51.2, `sprint-51-2-plan.md:283`) asked for the Qdrant semantic axis on the memory layers; the whole `"semantic"` time-scale column was a `[]` stub (`user_layer.py:101-103`). 57.146 built the `EmbeddingClient` ABC + `QdrantVectorStore` and 57.147 the per-tenant `QdrantNamespaceStrategy` pattern — closing CARRY-026 for KB but leaving the **memory** half open ("unblocked, NOT wired", `50-...-design.md:68` / `51-...-design.md:73`). This spike wires the first slice (L4 user) so a semantic-only memory request returns cosine-ranked hits instead of `[]`, and proves it on the real chat flow.

**Verdict (drive-through, real Azure + real Qdrant)**: KEEP — the semantic axis is live + per-user isolated on the main flow; shipped opt-in (`MEMORY_VECTOR_ENABLED`, default OFF).

## 2. Decision Matrix

### 2.1 Ingest strategy — lazy-on-search vs embed-on-write

| Option | Touches 57.150 write path | Backfill of pre-flag rows | Verdict |
|--------|---------------------------|----------------------------|---------|
| **Lazy ingest-on-search (CHOSEN)** | NO — `read()` only | free (search ingests current rows) | ✅ mirrors `KnowledgeVectorIndex` exactly; per-user count guard keeps steady-state embed cost ~0; write path byte-untouched |
| Embed-on-write (incremental) | YES — the dedup upsert | needs a separate backfill pass | ❌ higher risk on the 57.150 hot path + extra backfill; deferred as a follow-on optimization |

### 2.2 Isolation — per-user collection vs per-tenant collection + user filter

| Option | Collections | Verdict |
|--------|-------------|---------|
| **Per-tenant collection + user_id payload filter (CHOSEN)** | 1 per tenant (`tenant_<hex>_user_memory`) | ✅ reuses the 49.3-reserved `"user_memory"` namespace + the 57.147 payload-filter doctrine; point id incorporates `user_id` so two users' identical facts are distinct points; search filters `tenant_id AND user_id` (defense-in-depth) |
| Per-tenant-per-user collection | 1 per (tenant, user) | ❌ collection explosion; `QdrantNamespaceStrategy` has no per-user layer; the payload filter already isolates cleanly (drive-through Leg 3 proved it) |

### 2.3 Read-branch shape — byte-identical off, merge on

| Option | Off-path fidelity | Verdict |
|--------|-------------------|---------|
| **No-semantic-hits → return keyword path unchanged (CHOSEN)** | byte-identical to 57.150 | ✅ `if not semantic_hits: return keyword_hints` preserves the SQL order + the semantic-only `[]` stub; only merges (dedup by row id, re-rank by relevance) when semantic hits exist |
| Always re-rank the merged set | changes keyword order even when off | ❌ breaks the 57.150 byte-identical guarantee for the flag-off / index-None path |

## 3. Verified Invariants (each with file:line + verification command)

- **The two arms differ only by an injected index** — `UserLayer.__init__(session_factory, vector_index=None)` (`user_layer.py:81`); `read()` semantic branch guarded by `self._vector_index is not None` (`user_layer.py` `want_semantic`). None → the 51.2 `[]` stub / keyword-only path.
  - Verify: `test_read_semantic_only_returns_empty` (None → `[]`) + `test_read_semantic_returns_vector_hits_when_index_injected` (index → cosine hits) + `test_read_semantic_fail_soft_on_index_error` (raise → `[]`) — `backend/tests/unit/agent_harness/memory/test_user_layer.py`.
- **Lazy ingest is per-user idempotent** — `MemoryVectorIndex._ingest` skips re-embed when `store.count(collection, payload_filter=user_filter) == len(rows)` (`vector_index.py`), so a repeated search re-uses the collection (no wasted embed) and a new fact (count+1) triggers re-ingest.
  - Verify: `test_lazy_ingest_idempotent_per_user` + `test_new_fact_triggers_reingest` + `test_ingest_batches_embedding_calls` — `test_memory_vector_index.py`; live: drive-through log `ingested 4 → 5 rows … user=04dc4ee0` then Leg-2 no re-ingest.
- **Per-user isolation (two mechanisms)** — collection `QdrantNamespaceStrategy.collection_name(tid, "user_memory")` (`qdrant_namespace.py:75-89`) + `_user_filter(tid, uid)` two-key payload filter; point id `_point_id(user_id, dedup_key)` per-user-unique.
  - Verify: `test_user_a_cannot_retrieve_user_b_fact` (unit) + `test_semantic_recall_is_per_user_isolated` (real-DB) + **drive-through Leg 3** (priya's search of jamie's memory-only "Project Lodestar" → 0 hits; Qdrant `tenant_09eb…_user_memory` = 7 pts, jamie 5 / priya 2).
- **`count` gains a filter without breaking callers** — `QdrantVectorStore.count(name, payload_filter=None)` (`qdrant_client.py:88`), the sole prior caller (`knowledge/vector_index.py:135`) is no-arg.
  - Verify: `test_count_no_filter_passes_none` + `test_count_with_payload_filter_scopes_to_subset` — `test_qdrant_client.py`.
- **Full-suite green** — `cd backend && python -m pytest -q` → **3123 passed / 6 skipped**; `mypy src` → 399 files / 0; `python scripts/lint/run_all.py` → 11/11.

## 4. Cross-Category Contracts

**No new contract.** The slice consumes EXISTING contracts: the `EmbeddingClient` ABC (`17-cross-category-interfaces.md §2.1`, reused unchanged) + `QdrantVectorStore` / `QdrantNamespaceStrategy` (infra, 57.146/57.147) + the 範疇 3 `MemoryLayer` ABC (`UserLayer.read` signature unchanged — the `vector_index` is a ctor dep, not a method-signature change). No new ABC / event / DB column. Wire count unchanged (26).

## 5. Open Invariants (verified vs deferred)

**Verified in this spike**: L4 user-layer semantic recall (embed + per-user Qdrant cosine + dedup-merge into the retrieval path); per-user isolation at the vector-store + answer layers; count-idempotency; fail-soft; byte-identical flag-off; the machinery LIVE on the real chat flow (real Azure `text-embedding-3-large` 3072-dim + real Qdrant).

**Deferred (NOT verified here)**:
- **Semantic-axis attribution vs `profile()`**: the drive-through's keyword-disjoint recall (Leg 2) is co-supported by the always-on `profile()` (57.148) so the ANSWER cannot isolate the semantic axis; its distinctive value (relevance-ranked recall among MANY facts) is proven at the machinery layer, not behaviourally — a many-fact A/B (semantic-on vs -off recall precision) is a follow-on (`AD-Memory-Vector-Recall-Precision-AB`).
- **L1 system + L2 tenant semantic layers** — `AD-Memory-Semantic-Axis-System-Tenant-Layers` (CARRY-026 remaining).
- **Session-summary semantic ranking** (57.151 recency-only) — `AD-Memory-Session-Summary-Semantic-Rank`.
- **Semantic near-dup write dedup** (extend 57.150 exact-normalized) — `AD-Memory-Semantic-NearDup-Dedup`.
- **Incremental embed-on-write** + **orphan cleanup on fact deletion** (no user-memory delete path exists today, so the count guard is correct now) — `AD-Memory-Vector-Incremental-Write`.
- **Per-tenant `MEMORY_VECTOR_ENABLED` override** (C3 seam) — `AD-Memory-Vector-PerTenant-Phase58`.

## 6. Rollback / Fallback

Ships behind `MEMORY_VECTOR_ENABLED` (default False) → the shipped state is byte-identical to 57.154. To disable after enabling: set the env flag False (or drop it) → `get_memory_vector_index()` returns None → the UserLayer is built without an index → `read()` takes the 57.150 keyword/`[]` path. Any embed/Qdrant runtime failure already fail-softs to `[]` (recall never breaks). No data migration (no schema change; Qdrant collections are derived + idempotently re-ingested). Est: 1 line (flag) + a restart.

## 7. References

- `backend/src/agent_harness/memory/vector_index.py` — `MemoryVectorIndex`
- `backend/src/agent_harness/memory/layers/user_layer.py` — `read()` semantic branch + `_semantic_hits`
- `backend/src/api/v1/chat/memory_vector_index.py` — the composition singleton
- `backend/src/infrastructure/vector/qdrant_client.py` — `count(payload_filter=)`
- `backend/tests/{unit/agent_harness/memory/test_memory_vector_index.py, unit/api/v1/chat/test_memory_vector_index_singleton.py, integration/memory/test_memory_vector_recall.py}` — tests
- `docs/.../sprint-57-155/progress.md` Day 3 + `artifacts/` — the drive-through evidence (4 screenshots + Qdrant/log)
- `50-knowledge-embedding-vector-design.md` / `51-knowledge-per-tenant-isolation-design.md` — the mirrored knowledge pattern (57.146/57.147)
- `17-cross-category-interfaces.md §2.1` — `EmbeddingClient` ABC (sole contract consumed)
- CHANGE-122

## 8. Modification History

- 2026-07-01: Initial creation (Sprint 57.155) — user-layer semantic vector recall (CARRY-026 Slice 1; KEEP, drive-through PASS)
