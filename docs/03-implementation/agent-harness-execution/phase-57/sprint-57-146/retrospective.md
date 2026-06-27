# Sprint 57.146 Retrospective — knowledge Slice 2: section-aware snippets + embedding/Qdrant vector search

**Sprint goal**: upgrade the 57.145 keyword connector to real semantic retrieval — section-aware chunking (fixes R2 over-search) + Azure embeddings + Qdrant vector search, opt-in with a keyword fail-soft fallback. Close the Slice-2 half of `AD-Knowledge-Connector-First-Real-Source`.

**Outcome**: ✅ achieved. Drive-through PASS (real chat-v2 + real Azure gpt-5.2 + real `text-embedding-3-large` + real Qdrant): a semantic query with no literal keyword overlap retrieved the right docs by similarity and the agent answered citing each real source path + section.

---

## Q1 — What went well

- **Day-0 三-prong de-risked the big greenfield**: recon found Qdrant + namespace strategy already exist (so the work was the embedding ABC, not the infra), and resolved D-config-shape (drop a planned config file) before any code.
- **Section-aware chunking was the right single abstraction**: it fixed R2 (richer keyword snippet) AND defined the embedding unit — two consumers, one `split_sections`.
- **Opt-in + fail-soft kept it safe**: `KNOWLEDGE_VECTOR_ENABLED=0` → 57.145 byte-identical; the lazy singleton means zero cost when off; the keyword fallback means the tool never goes dark.
- **Drive-through delivered its whole reason for existing**: the full backend gate was green (33 unit tests, mypy, lints) yet TWO real bugs only surfaced on the live Azure/Qdrant connection (env-name mismatch + 429). Both caught + fixed + regression-tested in-sprint.
- **Semantic retrieval is honestly real**: the query had no literal "adapter"/"neutrality"; Qdrant returned exactly those sections; the answer quoted + cited the real `.md` content (Chinese + ASCII diagram + SOP code), not training.

## Q2 — Estimate accuracy (calibration)

- **Class**: `knowledge-embedding-vector-spike` **0.60** (NEW, 1st data point). Parent-direct, **agent_factor 1.0** (no code-implementer agent used).
- **Plan**: bottom-up ~20.5 hr → class-calibrated commit ~12.3 hr (mult 0.60).
- **Actual**: ~13-14 hr equivalent. Day 0-2 ≈ committed (the Qdrant container + namespace strategy already existing offset the new ABC). **Day 3 ran ~2× the plan's single-round assumption** — 2 real-connection bugs (env-name rename + 429 batching) + the 418-file corpus discovery + the clean-restart orphan-worker hunt. Day 4 ≈ committed.
- **Ratio ≈ 1.05-1.15** (IN band, upper half). **KEEP 0.60** — single data point; the over-edge is the drive-through-found bug fixes, the *normal* cost of a real-connection spike (a vector path you can't drive-through is a Potemkin). Same shape as `knowledge-connector-real-source-spike` 0.55 (57.145 landed ~1.15-1.25 for the same reason). If a 2nd `knowledge-embedding-vector-spike` lands > 1.2, re-point toward 0.70 (the external-dep drive-through is the variance driver).

## Q3 — What to improve

- **Anticipate the corpus-scale problem at plan time**: the plan assumed the default planning-docs root was fine to embed; it is 418 files / 3818 sections via recursion. A Day-0 note "measure the ingest corpus size before assuming startup-blocking ingest is viable" would have pre-empted the 429 + the bounded-corpus pivot.
- **Plan a batched ingest from the start**: embedding all sections in one call is obviously TPM-risky in hindsight; the plan should have specified batching as the default, not discovered it via 429.
- **Startup-blocking ingest is a smell**: blocking app startup on a corpus embed is fragile at scale. A background/offline ingest job is the right production shape (noted as an open invariant).

## Q4 — Lessons / ADs

- **`AD-Knowledge-Connector-RBAC-Citation-Slice3`** (carryover): per-tenant KB collection isolation (`QdrantNamespaceStrategy` `"kb"`) + RBAC per-doc filter + structured citation report.
- **`AD-Knowledge-Connector-Ingest-Scale`** (NEW): the startup-blocking ingest works for a bounded corpus but not 3818 sections; a background/offline idempotent ingest job (not blocking startup) is needed for the full default corpus.
- **Lesson (reusable)**: when an upfront-ingest feature points at a *recursive* default folder, MEASURE the corpus size at Day 0 — a folder that is fine for on-demand keyword reads (57.145) can be 1.1M tokens for upfront embedding. Recursion + upfront cost interact badly.
- **Lesson (reinforces 57.145)**: a real-connection spike's drive-through WILL find a connection-shape bug the green gate cannot (57.145: tokenize; 57.146: env-name + 429). Budget for it; it is the feature, not the miss.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ reachable from chat main flow via opt-in handler thread — drive-through proved the path.
- **AP-4** (Potemkin): ✅ NOT — drive-through proved real embed call (1750ms span) + real Qdrant retrieval + grounded cited answer; the 429 + env bugs were found + fixed precisely because of the drive-through.
- **AP-6** (speculative abstraction): ✅ the `EmbeddingClient` ABC is mandated by 約束 3 (not speculative); ONE Azure concrete + a test double, no other providers; opt-in not premature.
- **AP-11** (naming): ✅ `EmbeddingClient` / `QdrantVectorStore` / `KnowledgeVectorIndex` / `deployment_embedding` (renamed to match the `.env` + the `DEPLOYMENT_NAME` convention) — names match behavior.
- **v2 lints**: 11/11 green (incl. `check_llm_sdk_leak` — embedding SDK confined to `adapters/azure_openai/embeddings.py`).

## Q6 — Carryover

- `AD-Knowledge-Connector-RBAC-Citation-Slice3` (Slice 3) + `AD-Knowledge-Connector-Ingest-Scale` (background ingest) + `AD-Knowledge-Connector-Hybrid-Rerank` + `AD-Knowledge-Connector-External-Source` + `AD-Knowledge-Connector-DocTypes`. Recorded in `next-phase-candidates.md`.

## Q7 — Drive-through evidence

- trace_id `f5b394db524b4d4d89b6a2c1203a8e11`. Qdrant `knowledge_local_docs` green / 129 points / dim 3072. Screenshot `artifacts/sprint-57-146-drivethrough-semantic-knowledge.png`. Full narrative: progress.md Day 3.

---

## Design Note Extract (spike sprint — §5.5)

**File**: `docs/03-implementation/agent-harness-planning/50-knowledge-embedding-vector-design.md`
**Verified ratio (estimated)**: ~95% (every §3 invariant has file:line + a verification command or the real-Azure drive-through; §5 deferred items explicitly marked NOT verified)
**8-Point Quality Gate**:
- [x] 1. Section headers map to spike US (US-1..US-6 in §1)
- [x] 2. Each technical claim has file:line (§3 invariants 1-9)
- [x] 3. Decision rationale has comparison matrices (§2: embedding provider + vector store + chunk unit)
- [x] 4. Verification commands reproducible (§3: pytest per invariant + the drive-through reproduce)
- [x] 5. Test fixture reference (§3: deterministic double + mocked client + the real bounded corpus)
- [x] 6. Open invariants explicitly bounded (§5 verified-vs-deferred table + boundary statement)
- [x] 7. Rollback path (§6: disable-via-flag + full revert < 1 hr, no migration/sentinel)
- [x] 8. 17.md cross-ref (§4: EmbeddingClient = adapter-internal ABC, no new contract row; explicit when-to-register)

**Reviewer pass**: self-review (solo-dev).
