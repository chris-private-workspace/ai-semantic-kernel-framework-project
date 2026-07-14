# REFACTOR-009: sprint-workflow.md matrix re-bloat extraction (REFACTOR-005 round 2)

**Date**: 2026-07-01
**Sprint**: cross-sprint chore (no sprint number — rules maintenance)
**Scope**: Development Process / always-loaded rule hygiene
**Status**: **DONE 2026-07-14 (①+②)** — user approved ①+② on 2026-07-14. Executed against the live file: the inventory had grown **36 → 56 bloated rows** (Sprint 57.155-165 closeouts kept re-bloating after this plan was drafted), all 56 extracted + 5 agent_factor tier-4 lines (②). **Actual saving: 76.7 KB (179,443 → 102,690 bytes, −43%)**. Verification all PASS: 0 matrix cells > 400 chars · mult/mean columns byte-identical across all 86 rows · all 56 original cells + tier-2 originals verbatim in calibration-log §1/§2 · prevention note (imperative ≤250-char rule) + §Self-Check closeout line added.
**Precedent**: [REFACTOR-005](./REFACTOR-005-sprint-workflow-calibration-extraction.md) (2026-05-31) — the same extraction, first pass; this doc re-applies it after re-bloat.

> **Modification History**
> - 2026-07-14: Executed ①+② — 56 rows (grown from 36) + 5 tier-4 lines extracted; −76.7 KB; prevention added
> - 2026-07-01: Initial plan draft — matrix re-bloat audit + row-by-row checklist + before/after spec

---

## Problem

`.claude/rules/sprint-workflow.md` is an **always-loaded** rule file (Claude Code reads every `.claude/rules/*.md` into context each session). It has grown to **1014 lines / ~156 KB**, consuming ~9-12% of session context at startup before any work begins.

Measured breakdown:

| Section | Lines | Chars | % of file |
|---------|-------|-------|-----------|
| **Scope-class multiplier matrix** (§Step 1) | 109-196 | **73,508** | **47%** |
| Step 2.5 Day-0 Plan-vs-Repo Verify | 295-477 | 24,471 | 16% |
| Sprint Closeout policy | 634-747 | 9,556 | 6% |
| Agent Delegation Factor Modifier | 197-248 | 8,343 | 5% |
| Common Risk Classes | 748-809 | 7,760 | 5% |
| Step 5.5 Spike Design Note | 512-632 | 5,544 | 4% |
| (everything else) | — | ~27,000 | 17% |

The single dominant offender is the **Scope-class multiplier matrix**: one table = 47% of the whole always-loaded file.

Within that table, the "Status (1-line)" column has re-ballooned into full-sprint narration:

- **36 of 67 rows exceed 800 chars** (should be a 1-line status)
- Worst rows are **2200-2329 chars** — a single table cell holding an entire sprint's design decisions + drive-through results + calibration rationale + `CHANGE-NNN` / `design note N` references
- The 36 bloated rows total **60,865 chars**; trimming them to true 1-line (~220 chars each, matching the existing lean rows) leaves ~7,920 chars → **net saving ~51 KB (~33% of the whole file)**

## Root Cause

This file **violates its own rules**, in two places:

1. **REFACTOR-005 rule (L113)** — 2026-05-31 already extracted per-cell narration to `calibration-log.md §1` and left this note in the matrix:
   > "Per-class data-point history + per-cell narration + the matrix change log moved → `calibration-log.md §1`. **The table below = current multiplier + 3-sprint mean + 1-line status only**."

   From ~Sprint 57.113 / 57.145 onward, every sprint closeout re-added full narration to the "Status (1-line)" column, silently drifting away from the REFACTOR-005 discipline.

2. **§Sprint Closeout policy (this file, L634-747)** — warns against exactly this "triple-source" anti-pattern (same content in CLAUDE.md cell + footer + MEMORY.md). Each bloated matrix cell is a **third/fourth copy** of narration already single-sourced in:
   - `memory/project_phase57_XXX_*.md` (the per-sprint subfile)
   - the sprint's `retrospective.md`

Because that narration is already preserved in 2 authoritative places, removing it from the always-loaded rule file is **zero information loss**.

**Why it regrew**: no enforcement. The L113 note is advisory; nothing at sprint closeout checks that a new matrix row is actually 1-line. Each closeout AI copied the prior sprint's rich cell as the template (the same relative-anchor drift REFACTOR-008 fixed for sprint plans).

## Solution

Re-apply the REFACTOR-005 extraction, plus a prevention note so it does not regrow a third time. Three scope tiers (user picks at execution time; **① is recommended** — highest ROI, lowest risk):

### ① Matrix rows (recommended, ~51 KB saving)

For each of the 36 bloated rows (inventory below):
- **Move** the full narration text **verbatim** into `calibration-log.md §1` (the designated archive, already exists, read-on-demand / NOT always-loaded).
- **Replace** the matrix cell with a true 1-line status matching the existing lean-row format.

**Target 1-line format** (mirror the rows that are already correct — e.g. `medium-backend`, `reality-check`, `iam-frontend-spike`):

```
| `class-name` | mult | 3-sprint mean | KEEP/re-point + <one-clause verdict> (Sprint 57.XXX ratio ~Y IN band; → calibration-log §1) |
```

Rules for the trimmed cell:
- Keep: the **verdict** (KEEP / re-point → 0.85), the **sprint id + ratio + IN/OVER/BELOW band**, the **rollback trigger** (e.g. "if a 2nd lands > 1.20 → re-point 0.75"), and the `→ calibration-log §1` pointer.
- Drop (→ §1): design-decision narration, file:line references, drive-through transcripts, `CHANGE-NNN` / `design note N` refs, kin-class comparisons, per-Day cost breakdowns.
- Ceiling: **≤ ~250 chars per cell** (matches the existing lean rows).

### ② + Agent_factor tier-4 evidence (~5-6 KB more)

The `agent_factor` formula block (L207-221) has a tier-4 sub-class table (L213-217) whose `( ... )` descriptions carry huge inline evidence paragraphs (L215 = 1499 chars). Keep the **active number** (0.30 / 0.45 / 0.65 / 0.45 / 1.0) + the one-line trigger definition; move the per-sprint validation evidence to `calibration-log.md §2` (already exists: "Agent_factor — activation & validation history").

### ③ + Step 2.5 drift-class ROI tables (~8-10 KB more, lower priority / more judgment)

Step 2.5 (L295-477) drift-class tables carry multi-sprint ROI narration in cells. Some of this is genuine rule content (the grep patterns ARE the rule); only the **per-sprint ROI evidence** ("Sprint 57.49 silent HEX_OKLCH +1 → PR #200 hotfix...") should move to calibration-log. Needs case-by-case judgment on which cells are rule vs evidence — hence lower priority.

### Prevention (all tiers)

- Update the L113 note to be **imperative + enforced-at-closeout**: add a line to §Sprint Closeout Self-Check: "☐ New scope-class matrix row is ≤ 1 line (~250 chars); full narration in calibration-log §1, NOT the matrix cell."
- Optionally add a lightweight lint idea (future): a checker that flags any `sprint-workflow.md` matrix row > 400 chars. (Note only — not building the lint in this refactor.)

---

## Before → After examples

**Example A — `memory-formation-combine-ab-spike` (L126, 2329 chars → ~230 chars)**

Before (excerpt):
> `| memory-formation-combine-ab-spike | 0.60 | n/a (1 pt) | KEEP pending 2-3 sprint validation (Sprint 57.154 ratio ~0.95-1.03 IN band; closes AD-Memory-Combined-Formation-AB-Quality (57.152 carryover) — a real-Azure A/B harness measuring whether MemoryFormationWorker's combined single-call formation (57.152) degrades either half's quality vs two focused calls. ZERO src change: NEW benchmark_combined_formation_quality.py drives the REAL form() under both arms via capturing sinks ... [2000+ more chars] ... CHANGE-121 + design note 57) |`

After:
> `| memory-formation-combine-ab-spike | 0.60 | n/a (1 pt) | KEEP pending validation (57.154 ratio ~0.95-1.03 IN band; real-Azure A/B, KEEP combined default ON; if 2nd > 1.20 → 0.75; → calibration-log §1) |`

**Example B — `chatv2-userstop-resume-durability` (L163, 2301 chars → ~210 chars)**

After:
> `| chatv2-userstop-resume-durability | 0.60 | n/a (1 pt) | KEEP pending validation (57.143 ratio ~1.0 IN band; own-session DBMessageStore durability + Stop marker; if 2nd HITL/Stop-heavy > 1.20 → 0.85; → calibration-log §1) |`

**Example C — a re-pointed row `memory-formation-extract-spike` (L122, 2320 chars → ~215 chars)**

After:
> `| memory-formation-extract-spike | 0.60 → **0.85** (57.149) | n/a (1 pt) | KEEP 0.85 pending validation (57.149 1st pt ~1.3-1.4 OVER at 0.60 → re-point 0.85; ceremony-not-code-accelerated; if 2nd < 0.7 → lower; → calibration-log §1) |`

---

## Row-by-row checklist (① — 36 rows)

Each row: move verbatim narration → `calibration-log.md §1`, replace cell with ≤250-char 1-line.

| # | Line | Class | Current chars | mult |
|---|------|-------|---------------|------|
| 1 | L118 | `knowledge-connector-real-source-spike` | 1062 | 0.55 |
| 2 | L119 | `knowledge-embedding-vector-spike` | 1913 | 0.60 |
| 3 | L120 | `knowledge-per-tenant-isolation-spike` | 2195 | 0.55 |
| 4 | L121 | `memory-formation-identity-spike` | 1987 | 0.60 |
| 5 | L122 | `memory-formation-extract-spike` | 2320 | 0.60→0.85 |
| 6 | L123 | `memory-upsert-dedup-spike` | 2165 | 0.60 |
| 7 | L124 | `memory-session-recall-spike` | 2211 | 0.60 |
| 8 | L125 | `memory-formation-combine-spike` | 2248 | 0.60 |
| 9 | L126 | `memory-formation-combine-ab-spike` | 2329 | 0.60 |
| 10 | L144 | `mockup-author-and-port` | 1003 | 0.70 |
| 11 | L145 | `harness-loadbearing-gap-fix` | 1115 | 0.60→0.85 |
| 12 | L146 | `frontend-fixture-to-real-data-wiring` | 1018 | 0.75→0.90 |
| 13 | L158 | `chatv2-history-replay-fullstack` | 1464 | 0.60→0.85 |
| 14 | L159 | `chatv2-multiturn-rehydration-spike` | 1376 | 0.60 |
| 15 | L160 | `chatv2-resume-persistence-wiring` | 1244 | 0.55 |
| 16 | L161 | `chatv2-ledger-tool-roundtrips-wiring` | 1993 | 0.55→0.85 |
| 17 | L162 | `chatv2-resume-ledger-persist-wiring` | 1855 | 0.70→0.85 |
| 18 | L163 | `chatv2-userstop-resume-durability` | 2301 | 0.60 |
| 19 | L165 | `chatv2-fatal-terminate-wire-surface` | 1334 | 0.55 |
| 20 | L169 | `verification-context-hygiene-spike` | 1597 | 0.60 |
| 21 | L170 | `verification-keycondition-spike` | 1654 | 0.60 |
| 22 | L171 | `task-primitive-spike` | 1957 | 0.60 |
| 23 | L172 | `passk-reliability-spike` | 1876 | 0.60 |
| 24 | L173 | `otel-genai-semconv-spike` | 1868 | 0.60 |
| 25 | L174 | `layered-compaction-spike` | 1650 | 0.60 |
| 26 | L175 | `verification-memory-grounding-spike` | 2156 | 0.60 |
| 27 | L176 | `guardrail-restrict-spike` | 1962 | 0.60 |
| 28 | L177 | `tool-reflection-and-lint-spike` | 1761 | 0.60 |
| 29 | L181 | `per-tenant-catalog-table-backed` | 1111 | 0.60 |
| 30 | L182 | `config-validation-hardening` | 1227 | 0.55 |
| 31 | L183 | `skills-bundled-script-spike` | 1557 | 0.60 |
| 32 | L184 | `skills-admin-readonly-surface` | 1540 | 0.55 |
| 33 | L185 | `skills-slash-command-fullstack` | 1117 | 0.55 |
| 34 | L187 | `chatv2-inspector-existing-field-surface` | 2189 | 0.55→0.85 |
| 35 | L192 | `transcript-retention-apply-spike` | 991 | 0.60 |
| 36 | L193 | `scheduled-job-mirror-spike` | 1519 | 0.55→0.85 |

**Not touched** (already lean, 31 rows): `mixed`, `medium-backend`, `medium-frontend`, `large multi-domain`, `reality-check`, `reality-gap-fix`, `iam-*-spike`, `frontend-*` foundation/e2e/refactor/repoint rows, `mixed-multidomain-bundle`, `subagent-*`, `multi-model-profile-spike`, `verification-in-loop-spike`, `frontend-feature-with-event-wire-addition`, `loop-*`, etc. — these already follow the target format.

---

## Migration procedure (when approved)

1. **Append** a new dated sub-section to `calibration-log.md §1` header note: "2026-07-01 (REFACTOR-009): 36 spike-class rows (57.113→57.154) re-extracted from sprint-workflow.md after re-bloat; full narration below, lean rows in sprint-workflow.md."
2. For each of the 36 rows: paste the **exact current cell text** into calibration-log §1 (grouped under its class name), then `Edit` the sprint-workflow.md row down to the ≤250-char 1-line.
3. Update the L113 note wording from advisory → imperative + add the closeout self-check line.
4. (If ②) Repeat for the agent_factor tier-4 evidence → calibration-log §2.
5. Update sprint-workflow.md `Last Modified` + Modification History (1-line, per file-header-convention).
6. Update REFACTOR-009 status PLAN → DONE with actual saved KB.

**Discipline**: this is a mechanical text-move, NOT a rewrite. Do NOT paraphrase, re-verdict, or re-calibrate any number during the move — verbatim in, ≤250-char summary out. Any multiplier/verdict change is out of scope (would be a separate calibration decision).

## Verification

- `wc -c .claude/rules/sprint-workflow.md` → expect ~95 KB after ① (from 156 KB).
- `awk 'NR>=115 && NR<=160 && length($0)>400' ...` → 0 rows (no matrix cell over 400 chars).
- `grep -c 'calibration-log §1' .claude/rules/sprint-workflow.md` → 36 pointers present.
- Spot-check 3 moved rows: verbatim text present in calibration-log §1; multiplier/verdict in the trimmed cell unchanged.
- No multiplier value changed: `diff` the `| mult |` column before/after → identical set.

## Impact

- **Scope**: docs / rules only. No code, no backend, no frontend, no CI behavior change.
- **Risk**: low. Zero information loss (narration double-preserved in memory subfiles + retrospectives + now calibration-log §1). The active decision table (multipliers + rollback rules) stays in sprint-workflow.md and is unchanged.
- **Benefit**: ~51 KB (① ) → ~57 KB (①+②) off every session's startup context, permanently, plus a prevention note to stop a third regrowth.
- **Reversible**: fully — `git revert` restores the inline narration; calibration-log §1 keeps it regardless.

---

## References

- [REFACTOR-005](./REFACTOR-005-sprint-workflow-calibration-extraction.md) — first extraction (the precedent this repeats)
- [REFACTOR-001](./REFACTOR-001-claude-md-memory-md-bloat-audit.md) — CLAUDE.md / MEMORY.md bloat audit (same anti-pattern, different file)
- `docs/03-implementation/agent-harness-execution/calibration-log.md` — extraction target (§1 scope-class / §2 agent_factor / §3 change log)
- `.claude/rules/sprint-workflow.md` §Sprint Closeout — the policy this file itself violates
- `.claude/rules/file-header-convention.md` §Modification History — sibling "detail lives elsewhere, header stays lean" philosophy
