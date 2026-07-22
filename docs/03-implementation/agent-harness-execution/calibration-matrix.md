# Calibration Matrix — live scope-class multipliers + agent_factor

**Purpose**: THE live workload-calibration decision table (scope-class multiplier matrix + Active Agent Delegation Factor Modifier). Read on demand — extracted from the always-loaded `.claude/rules/sprint-workflow.md` so every session no longer pays its load cost.
**Category / Scope**: Development Process / cross-sprint (REFACTOR-011)
**Created**: 2026-07-14 (REFACTOR-011; content dates to Sprint 57.6+ / 57.42+)
**Last Modified**: 2026-07-14
**Status**: Active

> **Modification History**
> - 2026-07-14: REFACTOR-011 — extracted verbatim from sprint-workflow.md; no multiplier/verdict changed

---

## When to read / write this file

- **Plan drafting (Step 1 §Workload)**: look up the scope-class multiplier + agent_factor tier for the 3/4-segment commit form (`sprint-workflow.md §Workload Calibration`).
- **Day 4 closeout (retro Q2)**: append/update your class row — **≤ 1 line (~250 chars)**: verdict + sprint ratio/band + rollback trigger + `→ calibration-log §1` pointer ONLY; full narration → [`calibration-log.md` §1](./calibration-log.md). **Lint-enforced**: `scripts/lint/check_rules_hygiene.py` fails any table row here > 400 chars.
- Adjustment rule (when to re-point a multiplier) = `sprint-workflow.md §Workload Calibration §When to adjust the multiplier` (3-sprint moving window).

---

## Scope-class multiplier matrix (Sprint 57.6+ — closes AD-Reality-10 + AD-Sprint-Plan-7)

Per AD-Sprint-Plan-4 (logged Sprint 55.3) + 4-sprint window evidence,one-multiplier-fits-all approach loses signal when scope class differs。Below matrix記錄 active classes per scope。`mid-band` value 0.55 for default unclassified scopes;diversification per evidence。

> **Per-class data-point history + per-cell narration + the matrix change log moved** (REFACTOR-005, 2026-05-31; re-extracted REFACTOR-009, 2026-07-14) → [`calibration-log.md` §1](./calibration-log.md). **IMPERATIVE — a matrix cell is ≤ 1 line (~250 chars)**: verdict + sprint ratio/band + rollback trigger + `→ calibration-log §1` pointer ONLY; at closeout the full narration goes to calibration-log §1, NEVER into the cell (enforced via `sprint-workflow.md` §Self-Check at Sprint Closeout + the check_rules_hygiene lint). Adjustment rule = `sprint-workflow.md` §Workload Calibration §When to adjust the multiplier (3-sprint moving window).

| Scope class | Mult | 3-sprint mean | Status (1-line) |
|-------------|------|---------------|-----------------|
| `mixed` (greenfield + reuse) | 0.60 | 0.79 ⬇ | KEEP; AD-Sprint-Plan-6 propose split greenfield 0.60 / pattern-reuse 0.40 |
| `knowledge-connector-real-source-spike` | 0.55 | n/a (1 pt) | KEEP pending validation (57.145 ratio ~1.15-1.25 upper-edge IN band; first real external connector — drive-through-found bug fix = normal spike cost; if a 2nd lands > 1.2 → 0.65; → calibration-log §1) |
| `knowledge-embedding-vector-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.146 ratio ~1.05-1.15 IN band; first EmbeddingClient ABC + Qdrant infra; if a 2nd lands > 1.2 → 0.70 — external-dep drive-through is the variance driver; → calibration-log §1) |
| `knowledge-per-tenant-isolation-spike` | 0.55 | n/a (1 pt) | KEEP pending validation (57.147 ratio ~1.0-1.15 IN band; wires pre-existing pieces, mirrors memory_search; if a 2nd (e.g. Slice 3b RBAC) lands > 1.20 → 0.65 — multi-tenant drive-through setup is the variance driver; → calibration-log §1) |
| `memory-formation-identity-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.148 ratio ~1.0-1.1 IN band; real-code core held the spike mult per the 57.137 lesson; if a 2nd memory-formation-* lands > 1.20 → 0.85; → calibration-log §1) |
| `memory-formation-extract-spike` | 0.60 → **0.85** (re-pointed Sprint 57.149) | n/a (1 pt) | KEEP 0.85 pending validation (57.149 1st pt ~1.3-1.4 OVER at 0.60 → re-point 0.85; Day-3 drive-through-found BackgroundTask re-architecture = the over-run; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |
| `memory-upsert-dedup-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.150 ratio ~1.07 IN band; migration + write rewrite held the 0.60, landed clean — dedup fired on send 1; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `memory-session-recall-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.151 ratio ~1.05 IN band; Day-0 reuse-table catch balanced by the JOIN read + 3-leg drive-through; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `memory-formation-combine-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.152 ratio ~1.0-1.05 IN band; real composition + 2 dispatch refactors held the 0.60, drive-through on-budget; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `memory-formation-combine-ab-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.154 ratio ~0.95-1.03 IN band; real-Azure A/B → KEEP combined default ON; if a 2nd lands > 1.20 → 0.75 — real-Azure staging + oracle tuning is the variance risk; → calibration-log §1) |
| `memory-vector-recall-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.155 ratio ~1.0 IN band; new index + layer read-branch = real design content, ran clean; if a 2nd (e.g. L1/L2 layers) lands > 1.20 → 0.70 — real-embeddings + Qdrant drive-through is the variance driver; → calibration-log §1) |
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
| `mockup-author-and-port` | 0.70 | n/a (1 pt) | KEEP pending validation (57.121 ratio ~1.17 IN band; authoring half has no prior source — the ceremony-aware 0.70 confirmed; if a 2nd lands > 1.20 → 0.85; → calibration-log §1) |
| `harness-loadbearing-gap-fix` | 0.60 → **0.85** (re-pointed Sprint 57.122) | n/a (1 pt) | KEEP 0.85 pending validation (57.122 1st pt ~1.8 OVER at 0.60 → re-point 0.85; ceremony-not-code-accelerated — full-ceremony parent-direct + design note + drive-through lands ~0.85-1.0; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |
| `frontend-fixture-to-real-data-wiring` | 0.75 → **0.90** (re-pointed Sprint 57.123) | n/a (1 pt) | KEEP 0.90 pending validation (57.123 1st pt ~1.33 OVER at 0.75 → re-point 0.90; ceremony-not-code-accelerated + a Risk-E orphan-worker detour; if a 2nd lands < 0.7 at 0.90 → lower; → calibration-log §1) |
| `frontend-mockup-fidelity-audit` | 0.85 | n/a (1 pt) | KEEP; if recurs →0.45-0.55 |
| `frontend-mockup-strict-rebuild` | 0.60 | ~0.63 | KEEP — agent-confound resolved at agent_factor sub-class layer |
| `frontend-foundation-token-correction` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-foundation` | 0.55 | n/a (1 pt) | KEEP |
| `frontend-verbatim-css-repoint -simple` | 0.50 | ~1.0 | KEEP (criteria: ≤3 files / no AP-2 banner / no dual-mount / no playback widgets / oklch bump <4) |
| `frontend-verbatim-css-repoint -with-extras` | 0.65 | ~1.04 | KEEP (criteria: any of multi-file >3 / AP-2 banner / dual-mount / playback widgets / oklch bump ≥4) |
| `frontend-page-bug-fix` | 0.45 | n/a (1 pt) | KEEP; if >1.20 recurs →0.55-0.60 |
| `mixed-multidomain-bundle` | 0.65 | ~0.9-1.0 (latest 57.124) | KEEP — 57.124 (3 tracks) ratio ≈1.0-1.1 IN band parent-direct + 57.107 B3 ≈0.8-0.9 IN band; the prior 0.42 mean was the agent-confound era (→ calibration-log §1) |
| `subagent-child-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.94 ratio ~0.93 IN band; Cat 11 new-domain spike, parent-direct) |
| `subagent-sse-relay-wiring` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.95 ratio ~0.9-1.0 IN band; Cat 11→12 backend composition wiring, parent-direct) |
| `chatv2-transcript-persistence-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.125 ratio ~1.0 IN band; mirrors the proven persist observer + read endpoint, NO migration; the Day-0 re-scope saved building the wrong thing; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `chatv2-history-replay-fullstack` | 0.60 → **0.85** (re-pointed Sprint 57.126) | n/a (1 pt) | KEEP 0.85 pending validation (57.126 1st pt ~1.43 OVER at 0.60 → re-point 0.85; Day-0 flipped FE-only → full-stack + an Option-C dead-end investigation; ceremony-not-code-accelerated; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |
| `chatv2-multiturn-rehydration-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.127 ratio ~0.98 IN band; pure-backend new-ABC spike (MessageStore) — Day-0 net scope-reduction offset the serde relocation; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `chatv2-resume-persistence-wiring` | 0.55 | n/a (1 pt) | KEEP pending validation (57.128 ratio ~1.13 near band-top IN band; tiny mirror-wiring but the HITL drive-through SETUP dominated wall-clock; if a 2nd HITL-drive-through sprint lands > 1.20 → 0.65; → calibration-log §1) |
| `chatv2-ledger-tool-roundtrips-wiring` | 0.55 → **0.85** (re-pointed Sprint 57.129) | n/a (1 pt) | KEEP 0.85 pending validation (57.129 1st pt ~1.9 OVER at 0.55 → re-point 0.85; code on-budget, the drive-through (HITL setup + content-filter chase) dominated; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |
| `chatv2-resume-ledger-persist-wiring` | 0.70 → **0.85** (re-pointed Sprint 57.132) | n/a (1 pt) | KEEP 0.85 pending validation (57.132 1st pt ~1.4-1.6 OVER at 0.70 → re-point 0.85; tiny code + a mandatory HITL drive-through + a Leg-2 output-escalate dead-end; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |
| `chatv2-userstop-resume-durability` | 0.60 | n/a (1 pt) | KEEP pending validation (57.143 ratio ~1.0 IN band; real-code core (own-session refactor + RLS + cancel + FE) held the 0.60 — the ceremony risk did NOT fire; if a 2nd Stop/HITL-drive-through-heavy sprint lands > 1.20 → 0.85; → calibration-log §1) |
| `subagent-child-turnstream-nesting` | 0.55 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.96 ratio ~0.9-1.1 IN band; Cat 11×12 multi-layer feature — new wrapper event + executor forward + frontend store/render, parent-direct) |
| `chatv2-fatal-terminate-wire-surface` | 0.55 | n/a (1 pt) | KEEP single-data-point (57.130 ratio ~1.29 slightly OVER band-top; cross-stack code on-budget, the drive-through trigger hunt = the over-run; if a 2nd *-wire-surface lands > 1.20 → 0.65; → calibration-log §1) |
| `multi-model-profile-spike` | 0.55 | ~1.0 (2 pt) | KEEP — 57.97 ~0.93 + 57.109 ~1.1-1.2 both IN band (2-consec). Shape: a ChatClient consumer retiered to cheap + cost attribution + drive-through, parent-direct (57.109 C2: compaction retier + `_compaction` ledger mirror + 2 env knobs; the upper-edge ratio = the dt discovery loop — D-DAY3-1 semantic-unreachable finding forced a knob pivot) |
| `subagent-child-governance` | 0.55 | n/a (1 pt) | KEEP pending validation (57.110 B4 ratio ~1.1-1.2 IN band upper edge; composition over the proven child-loop machinery; the upper edge = the dt discovery loop (popen fix-forward + re-drive); → calibration-log §1) |
| `verification-in-loop-spike` | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.98 ratio ~0.92 IN band; Cat 1×10×7×12 loop.py-core new-domain spike — in-loop verify gate + durable counter on checkpoint metadata + wrapper retire + drive-through, parent-direct; agent_factor 1.0) |
| `verification-context-hygiene-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.136 ratio ~1.0 IN band; real-code spike (loop branch + env wire + A/B harness), A/B verdict KEEP default; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `verification-keycondition-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.138 ratio ~0.98 IN band; ZERO src change — a template data file + harness; the ~3 hr harness core held the 0.60 (57.137 lesson); if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `task-primitive-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.140 ratio ~0.95-1.0 IN band; full vertical slice anchored to skills-system-spike 0.60 — every pipeline had a precedent; drive-through STRONG PASS; if a 2nd lands > 1.20 → 0.70; → calibration-log §1) |
| `task-primitive-dag-spike` | 0.60 | ~1.0-1.1 (2 pt) | KEEP — 2 pts IN band (57.156 ~0.95-1.0 + 57.162 ~1.0-1.1; serde-transparent reuse of the 57.140 machinery; the 57.162 upper edge = drive-through staging (Risk-E + Playwright recovery); if a 3rd DAG-family w/ drive-through lands > 1.20 → 0.70; → calibration-log §1) |
| `scheduler-cross-burst-spike` | 0.60 → **0.70** | ~1.5-1.7 (2 pt) | **RE-POINT 0.70** — 2 pts both over (57.157 ~1.15-1.3 + 57.166 ~1.9-2.1); code+tests held 0.60 BOTH times, the entire over-edge is drive-through determinism (rare ceiling path needs a lever: 57.166 took 6 legs — LLM won't self-loop, HITL froze burst 2); budget the lever at Day 0; → calibration-log §1 |
| `memory-vector-recall-precision-ab-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.158 ratio ~1.0-1.05 IN band; ZERO-src A/B harness, verdict semantic-wins (+80pp recall@k); ran clean — deterministic cosine, no re-drive; if a 2nd *-ab-spike lands > 1.20 → 0.75; → calibration-log §1) |
| `chatv2-compaction-drivethrough-surface` | 0.85 | n/a (1 pt) | KEEP pending validation (57.159 ratio ~1.06 IN band; anchored to chatv2-inspector-existing-field-surface 0.85 — tiny-code + full-ceremony + mandatory drive-through; if a 2nd lands > 1.20 → 1.0 — long-conversation drive-through staging is the variance driver; → calibration-log §1) |
| `compaction-tool-anchored-masking-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.160 ratio ~1.0 IN band; masker mode + A/B harness held the 0.60; the wall-clock driver = the Day-3 drive-through discovery loop; if a 2nd lands > 1.20 → 0.75; → calibration-log §1) |
| `compaction-structural-realcount-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.161 ratio ~1.0 IN band; mirrored the preclear pattern 1:1, drive-through first try; if a 2nd lands > 1.20 → 0.75, if < 0.7 → 0.50; → calibration-log §1) |
| `passk-reliability-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.141 ratio ~1.0 IN band; ZERO-src-edit 4-axis harness — the real-code core held the 0.60; if a 2nd lands > 1.20 → 0.75 — the 4-axis breadth is the variance risk; → calibration-log §1) |
| `otel-genai-semconv-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.142 ratio ~0.95-1.0 IN band; translation-at-tracer schema mapping + conformance harness, fixed a latent token-attr bug; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `layered-compaction-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.139 ratio ~0.97 IN band; 2 new compactors + yield harness = a real-code core, LLM-free ACON band verified; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `verification-memory-grounding-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.153 ratio ~1.0 IN band; TransientState-field design (0 verifier-impl churn) + A/B fabrication-catch 0→100%; if a 2nd lands > 1.20 → 0.75 — the 2-leg drive-through staging is the variance risk; → calibration-log §1) |
| `guardrail-restrict-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.137 ratio ~0.97 IN band; the ceremony risk did NOT fire — a real-code core holds the spike mult, a ~10-line surface change needs ~0.85 (the 57.137 lesson); if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `tool-autofix-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.165 ratio ~1.0-1.08 IN band; self-validating drafter + 3-kind splicer held the 0.60; NO drive-through (dev/CI tooling) — real-Azure smoke instead; if a 2nd lands > 1.20 → 0.75; → calibration-log §1) |
| `tool-reflection-and-lint-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.144 ratio ~1.05-1.1 IN band upper edge; the upper edge = the user-approved +40-param expansion, not ceremony; lesson: a delegated-agent gate MUST include flake8 E501; if a 2nd lands > 1.20 → 0.75; → calibration-log §1) |
| `tool-reflection-drivethrough-evidence-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.163 ratio ~1.0 IN band; the Day-0 方案-A re-scope (rare branch near-unreachable → gate-only) dropped drive-through staging, net on-budget; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `verification-trace-and-benchmark-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.111 ratio ~1.0-1.1 IN band upper edge; loop trace-threading + a greenfield eval harness; the over-edge = the dt+tooling discovery loop, same shape as 57.109/110; → calibration-log §1) |
| `loop-pause-point-feature` | 0.50 | n/a (1 pt) | KEEP pending validation (57.99 ratio ~0.93 IN band; the 4th pause leg A2 verification-ESCALATE; 0.50 = the ~0.40 pause-leg baseline + the bounded REJECT continuation; → calibration-log §1) |
| `skills-system-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.113 ratio ~0.94 IN band; greenfield Cat 5 module + lazy-load tool + main-flow wiring; a clean Day-0 三-prong kept it IN band; → calibration-log §1) |
| `per-tenant-catalog-table-backed` | 0.60 | n/a (1 pt) | KEEP pending validation (57.114 ratio ~0.92 IN band; DB-backed overlay — table + RLS + CRUD + FE tab; the backend wiring was 1 line; parent-direct despite the plan's partial; → calibration-log §1) |
| `config-validation-hardening` | 0.55 | n/a (1 pt) | KEEP pending validation (57.117 ratio ~0.95-1.0 IN band; write-path guardrails on the 57.114 catalog, NO migration; if a 2nd hardening sprint diverges > 30% → re-point; → calibration-log §1) |
| `skills-bundled-script-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.118 ratio ~0.92 IN band; a bundled script via the existing SandboxBackend — 2 Day-0 scope-reducing refinements held; drive-through PASS in a real DockerSandbox; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `skills-admin-readonly-surface` | 0.55 | n/a (1 pt) | KEEP pending validation (57.119 ratio ~0.97 IN band; a read-only endpoint + FE section/modal; the only friction = the modal a11y lint ~10 min; if a 2nd read-only-surface diverges > 30% → re-point; → calibration-log §1) |
| `skills-slash-command-fullstack` | 0.55 | n/a (1 pt) | KEEP pending validation (57.115 ratio ~1.0 IN band; the greenfield FE slash-autocomplete offset by a light backend mirror; the drive-through proved deterministic injection; → calibration-log §1) |
| `frontend-feature-with-event-wire-addition` | 0.55 | ~1.16 (4 pt) | KEEP — 3-consec validated (57.100/108/116 IN band); 57.164 ~1.4-1.55 single over-point (a drive-through-found terminate-before-emit scope expansion); if a 2nd event-surface w/ mandatory drive-through > 1.20 → propose -with-drivethrough-trigger-hunt ~0.75; → calibration-log §1 |
| `chatv2-inspector-existing-field-surface` | 0.55 → **0.85** (re-pointed Sprint 57.120) | ~0.87 (3 pt) | KEEP 0.85 — 3 pts IN band VALIDATE the class (57.120 ~1.6 OVER at 0.55 → re-point 0.85; 57.131 ~0.82-0.93 + 57.133 ~0.94-1.03 confirm); a tiny-code + full-ceremony parent-direct sprint sits ~0.85, NOT 0.45-0.55; → calibration-log §1 |
| `loop-injection-primitive-spike` | 0.55 | n/a (1 pt) | KEEP pending validation (57.101 B1 IN band; a cross-stack new primitive (inbox ABC + drain seam + new event TYPE, codegen 23→24) but each layer thin over proven machinery → 0.55; → calibration-log §1) |
| `subagent-teammate-multiturn-spike` | 0.55 | n/a (1 pt) | KEEP pending validation (57.102 B2a ratio ~0.95-1.0 IN band; reuses 3 proven assets vs building the child-loop machinery → 0.55 under the 0.60 sibling; → calibration-log §1) |
| `subagent-inject-to-teammate` | 0.55 | n/a (1 pt) | KEEP pending validation (57.103 B2b ratio ~1.15-1.25 slightly OVER; a build-then-revert tax — the drive-through found the inject UI un-drivable → US-4/6 built then removed per Option A; → calibration-log §1) |
| `config-tiering-model-policy-spike` | 0.60 | ~0.98 (2 pt) | KEEP — validated 2-consec (C1 57.104 ~0.9-0.95 + C3 57.106 ~1.02 both IN band); the full-stack config-tiering family — blended full-stack so NO single agent_factor; → calibration-log §1 |
| `transcript-retention-apply-spike` | 0.60 | n/a (1 pt) | KEEP pending validation (57.134 ratio ~1.0-1.1 IN band; a Day-1 pivot dropped an AP-6 parallel-config trap — the write-then-drop offset the saved config work; if a 2nd diverges > 30% → re-point; → calibration-log §1) |
| `scheduled-job-mirror-spike` | 0.55 → **0.85** (re-pointed Sprint 57.135) | n/a (1 pt) | KEEP 0.85 pending validation (57.135 1st pt ~1.4-1.5 OVER at 0.55 → re-point 0.85; the mirror-code was small but the background-job drive-through ceremony (a Risk-E orphan hunt) dominated; if a 2nd lands < 0.7 at 0.85 → lower; → calibration-log §1) |

> Collapsed/closed historical classes (`frontend-mockup-strict-rebuild — historical`; `frontend-verbatim-css-repoint` pre-57.38 single-baseline, CLOSED Sprint 57.38) → calibration-log.md §1. For verbatim-css-repoint use `-simple` (0.50) or `-with-extras` (0.65) per criteria above.

## Active Agent Delegation Factor Modifier (ACTIVATED 2026-05-25 — Sprint 57.42 retro structural decision per `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`)

> **Per-sprint activation/validation history moved** (REFACTOR-005, 2026-05-31): activation evidence, tier-2/3/4 split evolution, per-sprint history (Sprint 57.42→57.62), deprecated baselines → [`calibration-log.md` §2](./calibration-log.md). Below = active rules only (Status + Formula tier-4 table + When + Rollback + Escalation + Tracking discipline).

**Status**: **ACTIVE — Option A multiplicative `agent_factor` coefficient with mid-band start `0.55`**. Closes `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`. Activation criteria FULLY MET at Sprint 57.42 retro Q4 (5 cross-class data points + 4 consecutive `mockup-strict-rebuild` agent-delegated < 0.7).

**Hypothesis (validated)**: code-implementer agent-delegated frontend work shows ~3-5× speedup vs the human-rewrite cadence the bottom-up estimates assume. Existing per-class multipliers (0.45-0.85) bake in a human-cadence haircut; agent-delegated sprints consistently undershoot the calibrated band lower edge because the haircut isn't enough. Validated by 5 data points (full activation evidence → calibration-log.md §2).

**Formula** (applies from Sprint 57.43+ onwards):

```
effective_calibrated_hours = bottom_up × scope_class_multiplier × agent_factor

where agent_factor = {
  human (default):      1.0
  agent-delegated (tier-4 sub-class table — Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATED effective 2026-05-28 onwards):
    mechanical-pattern-reuse-heavy:               0.30   (≥ 4 mechanical repetitions of the same template in 1 sprint; KEEP — 57.49 retroactive 0.21 + 57.60 1st forward pt ~1.09 IN band; if a future ≥20×-repetition sprint at 0.30 lands < 0.7 → consider a -high-repetition tier; evidence → calibration-log §2)
    mechanical-greenfield-port-style:             0.45   (single NEW component-pair via mirror-port of existing service shape; predecessor template ≥ 95% internalized; NO NEW Pydantic schema design / UX state design — RESERVED for future port-only sprints)
    mechanical-greenfield-design-decisions:       0.65   (single NEW component-pair WITH new Pydantic schema + UX-state design; tier-4 split VALIDATED 57.56 1.02 + 57.57 1.15 IN band; WATCH: 57.61 0.74 + 57.62 0.77 = 2 consec below cross-shape → next -design-decisions pt < 0.85 → tighten 0.65 → 0.55 (AD-AgentFactor-DesignDecisions-Below-Band-Watch); evidence → calibration-log §2)
    mixed-multidomain-bundle-mechanical:          0.45   (3+ independent tracks WITH a mechanical pattern-reuse component; tightened 0.65 → 0.45 effective 57.60+ after 57.58 + 57.59 2-consec < 0.7; if the next pt under 0.45 is also < 0.7 → escalate 0.30 OR fold into mechanical-pattern-reuse-heavy; evidence → calibration-log §2)
    mixed-multidomain-bundle-non-mechanical:      1.0    (3+ independent tracks of pure audit/docs/rules — NO mechanical reuse; tier-3 split effective 2026-05-27 after 57.51 + 57.52 both > 1.20 at 0.65; evidence → calibration-log §2)
  partial (20-79% via agent):          0.75   (linear interpolation)
  human (<20% via agent):              1.0
  History: 0.55 (57.42 activated) → 0.45 (57.44 tighten) → 0.65 (57.46 rollback) → tier-2/3/4 Option-B sub-class splits (57.48 / 57.50 / 57.52 / 57.55) — full history + rationale → calibration-log §2
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

where `Y' = Y × 0.55 = X × Z × 0.55`. See `sprint-workflow.md` §Four-segment form.

---

