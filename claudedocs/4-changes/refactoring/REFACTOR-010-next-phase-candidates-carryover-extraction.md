# REFACTOR-010: next-phase-candidates.md per-sprint carryover archive extraction

**Date**: 2026-07-07
**Sprint**: cross-sprint chore (no sprint number — planning-doc hygiene)
**Scope**: Development Process / planning single-source hygiene
**Status**: **DONE — tier ① executed 2026-07-07** (user approved「執行 ①」; 大前提「不刪除」honored — verbatim moved, not deleted). Tier ② (front-matter narration) NOT done — left as a future optional pass.
**Precedent**: [REFACTOR-001](./REFACTOR-001-claude-md-memory-md-bloat-audit.md) (CLAUDE.md / MEMORY.md bloat) + [REFACTOR-005](./REFACTOR-005-sprint-workflow-calibration-extraction.md) / [REFACTOR-009](./REFACTOR-009-sprint-workflow-matrix-rebloat-extraction.md) (sprint-workflow.md matrix) — the SAME "navigator file re-accumulates single-sourced detail" anti-pattern, now applied to `1-planning/next-phase-candidates.md`.

> **Modification History**
> - 2026-07-07: Tier ① EXECUTED — 103 carryover blocks (L94–2143) moved verbatim → `next-phase-candidates-shipped-archive.md`; main file 445 KB → 155 KB (−66%); pointer index (103 rows, 99 w/ memory link) + Open Carryover ADs (37 sprints) + prevention rule added; HEAD/TAIL byte-identical verified
> - 2026-07-07: Initial plan draft — carryover archive audit + keep/move rule + region inventory + before/after + migration + prevention

---

## Execution outcome (tier ① — 2026-07-07)

| Metric | Result |
|--------|--------|
| Main file size | 445,788 → **154,571 bytes (−66%)** |
| Archive file created | `next-phase-candidates-shipped-archive.md` = 365,775 bytes (103 blocks verbatim) |
| Blocks moved | 103 (Sprint 57.29 → 57.161) |
| Pointer-index rows | 103 (99 with a resolvable `memory/project_phase57_*.md` link; 4 non-sprint blocks → archive fallback) |
| Open-AD sections kept in main | 37 sprints (225 lines — only the `NEW carryover` / `Still-open` portions, narration excluded) |
| HEAD (L1–92) integrity | byte-identical to pre-refactor backup ✅ |
| TAIL (§Top Candidates → §Modification History) integrity | byte-identical ✅ |
| Zero-loss check | archive holds all 103 `## Sprint` headers + the region verbatim; every memory pointer preserved ✅ |
| Telemetry residue in pointer region | 0 pytest/mypy/Vitest lines ✅ |

Method: a mechanical Python split (`head[L1–93] + new-middle + tail[L2144–end]`), region moved byte-for-byte to the archive — no paraphrase, no re-verdict, no re-calibration. Prevention wired into `next-phase-candidates.md` §Maintenance Notes + §Structure note + `.claude/rules/sprint-workflow.md` §Sprint Closeout Self-Check. Reversible via the pre-refactor backup / `git revert`.

---

## Problem

`claudedocs/1-planning/next-phase-candidates.md` is the **single-source for "what could be next sprint"** (open items / pending decisions / carryover ADs). It is NOT always-loaded, but it IS read in full whenever a sprint is being planned — and it has grown to **445 KB / 2495 lines**, so every planning read dumps ~445 KB into context.

Measured breakdown (byte counts via `sed -n 'A,Bp' | wc -c`):

| Section | Lines | Chars | % of file | Nature |
|---------|-------|-------|-----------|--------|
| Forward-looking front matter (roadmap / research status / grounding / next move) | 1–93 | 53,023 | 12% | ✅ keep (but embeds long SHIPPED narration — tier ②) |
| **per-sprint「Carryover」archive** | 94–2145 | **362,750** | **81%** | ⚠️ the offender |
| Numbered candidate list #1–#46 | 2146–2476 | 24,467 | 5.5% | ✅ keep (true open items) |
| Maintenance + Modification History | 2477–2495 | 3,053 | 1.5% | ✅ keep |

The single dominant offender is the **per-sprint carryover archive**: **103** `## Sprint 57.X Carryover` blocks (57.29 → 57.161) = **81% of the whole file**. Each block is a full SHIPPED-sprint narration paragraph (file:line refs + drive-through transcript + pytest/mypy/Vitest counts + `CHANGE-NNN` / `design note N` + calibration class + `MERGED PR #N, main <sha>`) plus `### Sprint scope` / `### ADs closed` / `### Calibration note` sub-sections.

**This SHIPPED narration is already single-sourced elsewhere:**

- **69** of the 103 blocks end with an explicit `Detail: memory/project_phase57_XXX_*.md` pointer.
- All **160** `memory/project_phase57_*.md` subfiles exist on disk (verified — every recent-sprint pointer resolves).
- Each sprint additionally has an authoritative `retrospective.md` under `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/`.

So each carryover block's SHIPPED narration is a **third/fourth copy** of content that lives in ≥ 2 authoritative places. Removing it from this planning file is **zero information loss**.

**What in each block is NOT redundant** (must stay): the **open carryover ADs** (the `### NEW carryover` / `### Still-open` / `remaining` items still un-closed) — those are the actual forward-looking candidate seeds this file exists to hold. **99** lines across the archive carry open-AD markers.

## Root Cause

Same anti-pattern as REFACTOR-001 / 005 / 009. This file **violates the project's own §Sprint Closeout policy** (`.claude/rules/sprint-workflow.md` L634-747):

> "Sprint detail lives in **memory subfile + retrospective.md only**. Navigator files are **pointers, NOT archive**."

The policy explicitly forbids packing "carryover ADs / calibration ratios / commit SHAs / PR numbers / … file change lists" into navigator surfaces — yet every sprint closeout appends the full SHIPPED block here.

**Why it regrew** (identical to REFACTOR-009's finding): no enforcement. §Sprint Closeout says "append new carryover ADs here, NOT to CLAUDE.md" — which correctly keeps ADs out of CLAUDE.md, but nothing constrains the SHIPPED **narration** that rides along with each AD list. Each closeout AI copied the prior sprint's rich block as the template (the relative-anchor drift REFACTOR-008 fixed for sprint plans, recurring here).

**Not a memory-file problem** (explicitly ruled out): the 253 memory subfiles (2.0 MB) are **lazy-loaded** — only `MEMORY.md` (19 KB, already compacted 2026-06-26) hits session context. The memory subfile is the *cheapest* of the 5 per-sprint copies. The expensive copy is precisely this one — a 445 KB planning file read into context on every plan. The fix makes this file **point to** the (already-existing, lazy) subfiles instead of **copying** them.

## Solution

Re-apply the REFACTOR-001/005/009 extraction to this file, honoring the user's constraints:

1. **不刪除** — the SHIPPED narration is **moved verbatim** to a companion archive (not deleted).
2. **保持導向** — the main file keeps a compact pointer index so any AI / dev can find the full detail.
3. **不影響開發模式** — the sprint workflow is unchanged; only the closeout *destination* of the SHIPPED prose shifts by one file.
4. **持續優化** — a prevention rule stops a third regrowth.

Two scope tiers (user picks at execution time; **① is recommended** — highest ROI, lowest risk):

### ① Per-sprint carryover archive (recommended, ~300 KB off the main file)

Create a NEW companion file **`claudedocs/1-planning/next-phase-candidates-shipped-archive.md`** (same directory, lazy — NOT auto-loaded, NOT normally read during planning).

For each of the 103 carryover blocks (L94–2145):

- **MOVE verbatim → archive**: the SHIPPED narration paragraph(s) + `### Sprint scope` / `### ADs closed` / `### Validation` / `### Highlights` / `### Calibration note` / `### Process / Calibration` sub-sections. Keep the block's `## Sprint 57.X Carryover — …` header and its trailing `Detail: memory/…` pointer with the moved block.
- **KEEP in main file**, reformatted into two lean structures:
  1. A **"Shipped Sprints — Pointer Index"** table (newest-first), one row per block:
     ```
     | 57.XXX | <one-line what shipped> | closes <AD-X> | PR #N | → [detail](next-phase-candidates-shipped-archive.md#sprint-57xxx) · [memory](../../../memory/project_phase57_XXX_*.md) |
     ```
  2. An **"Open Carryover ADs"** section: the still-open AD names from each block's `### NEW carryover` / `### Still-open` lists, consolidated, **1 line each** (`AD-Name` — 1-phrase what + originating sprint). These are the real candidate pool and MUST NOT move to the archive.

**Keep/Move decision rule** (per block — apply mechanically):

| Content in block | Destination | Why |
|------------------|-------------|-----|
| SHIPPED narration (file:line / drive-through / test counts / CHANGE-NNN / design note / PR+sha / calibration ratio) | → archive (verbatim) | already in memory subfile + retrospective |
| `### Sprint scope` / `### ADs closed` / `### Calibration note` / `### Validation` | → archive (verbatim) | historical, single-sourced in retrospective |
| **Open** ADs (`### NEW carryover`, `### Still-open …`, `remaining`, `STILL OPEN`) that are **not** yet marked ✅ CLOSED | **stay** (→ Open Carryover ADs section, 1-line) | forward-looking = the file's purpose |
| ADs inside a block already struck through / marked ✅ CLOSED | → archive with the block | closed = historical |
| `## Sprint 57.X Carryover` header + `Detail:` pointer | one copy each place | header→pointer index; full header→archive |

### ② + Front-matter embedded SHIPPED narration (~30–40 KB more; more judgment)

The front matter (L27–90: "Research-Derived Candidates" + "Grounding pillars") lists the 8 research items and the knowledge/memory-formation arc — **most already ✅ DONE**, each with a full embedded SHIPPED paragraph (e.g. the grounding-pillar rows L56–69 are 1000–2000-char SHIPPED narratives). Trim each ✅-DONE item to a 1-line `✅ DONE Sprint 57.X → [archive]` pointer; **keep** the still-open guidance (the "🛡️守住不要動" guard, the "Recommended next move" ordering, any un-done item). The roadmap block (L9–24) stays — it is genuine forward-looking design rationale, not a sprint archive.

**Lower priority / needs case-by-case judgment**: some front-matter prose is genuine reconciliation reasoning (why an item is NOT a redo of shipped work) that has planning value — trim only the SHIPPED *result* narration, keep the *decision* rationale.

### Prevention (all tiers)

- Add to `.claude/rules/sprint-workflow.md` §Sprint Closeout Self-Check (Pre-Commit):
  > "☐ New sprint's SHIPPED narration goes to `next-phase-candidates-shipped-archive.md` + a **1-line** pointer-index row in `next-phase-candidates.md`; only the **open** carryover ADs (1-line each) go to the main file. NO full SHIPPED block in the main file."
- Update `next-phase-candidates.md` §Maintenance Notes accordingly (the "append here" instruction currently invites the full block).
- Update the archive file's own header to state the closeout append-target contract.

---

## Before → After examples

**Example A — a fully-shipped block (Sprint 57.161, L94–96, ~1900 chars → ~1 pointer row + 0-N open ADs)**

Before (excerpt of the main-file block):
> `## 🆕 Sprint 57.161 Carryover — structural compactor real token re-count …`
> `**SHIPPED → closes AD-Compaction-Structural-RealTokenCount (57.160 carryover).** StructuralCompactor.tokens_after was a message-count ratio (structural.py:192-193) blind to in-place tombstoning … [1600+ chars: fix / rollout / drive-through 22,925→10,584 / pytest 3206 / CHANGE-128 / design note 63] … Detail: memory/project_phase57_161_structural_realcount.md.`

After (main file — pointer index row + the one open AD):
> Pointer index: `| 57.161 | structural compactor real token re-count | closes AD-Compaction-Structural-RealTokenCount | PR #378 | → [archive](next-phase-candidates-shipped-archive.md#sprint-57161) · [memory](../../../memory/project_phase57_161_structural_realcount.md) |`
> Open Carryover ADs: `- AD-Compaction-Structural-TombstoneCount-Marker — mirror preclear's tombstoned count into StructuralCompactor.messages_compacted (57.161)`

After (archive file — the full narration, verbatim, under `## Sprint 57.161 …`). **Byte-for-byte the same text**, just relocated.

**Example B — a block with several open ADs (Sprint 57.157, L122–126)**

- SHIPPED narration paragraph (L124, ~1900 chars) → archive verbatim.
- The `**NEW carryover**` line (L126) has 5 open ADs → each becomes a 1-line entry in the Open Carryover ADs section (`AD-Scheduler-Burst-Stats-Aggregate-Phase58` — final loop_end reflects only last burst's counters (57.157); …).
- Pointer index row for 57.157 → main file.

**Example C — front-matter grounding pillar (tier ②, Sprint 57.155 row L69, ~2100 chars)**

Before: a 2100-char ✅-DONE SHIPPED narrative embedded in the "Grounding pillars" list.
After: `- ✅ CARRY-026 Slice 1 (L4 user-layer vector recall) — DONE Sprint 57.155 → [archive](…#sprint-57155). Remaining semantic-axis slices: AD-Memory-Semantic-Axis-System-Tenant-Layers · AD-Memory-Vector-Incremental-Write · … (open).`

---

## Region inventory (① — 103 blocks)

The extraction region is **L94–L2145** (from `## 🆕 Sprint 57.161 Carryover` to just before `## 🔴 Top Candidates`). It contains **103** `## Sprint 57.X Carryover` blocks spanning Sprint 57.29 → 57.161 (reverse-chronological, with a few out-of-order recent inserts). All 103 move their SHIPPED narration to the archive; their open ADs consolidate into the main file's Open Carryover ADs section.

**NOT touched** (stay in main file, unchanged):
- L1–26 (Purpose / Selection Rule / Harness Deepening Roadmap) — forward-looking design.
- L2146–2476 (numbered candidates #1–#46) — active open items (a later, separate pass could de-dupe these against the consolidated Open Carryover ADs, but out of scope here).
- L2477–2495 (Maintenance / Modification History) — updated per Prevention, not moved.

(Tier ② additionally touches L27–90 front-matter SHIPPED narration.)

---

## Migration procedure (when approved)

1. **Create** `claudedocs/1-planning/next-phase-candidates-shipped-archive.md` with a header (Purpose: verbatim SHIPPED-sprint carryover archive; closeout append-target contract; pointer back to the main file).
2. For each of the 103 blocks (process newest→oldest so anchors are stable): **cut** the SHIPPED narration + historical sub-sections **verbatim** into the archive under the same `## Sprint 57.X …` header (add an `#sprint-57xxx` anchor); **extract** its open ADs into the main file's new "Open Carryover ADs" section (1-line each); **add** its pointer-index row.
3. Insert the two new lean structures into the main file where the archive region was: "Shipped Sprints — Pointer Index" table + "Open Carryover ADs" section.
4. Update main-file §Maintenance Notes + the archive-file header with the new closeout append-target contract.
5. Add the §Sprint Closeout Self-Check line to `.claude/rules/sprint-workflow.md` (+ 1-line Modification History entry per file-header-convention).
6. (If ②) Trim the front-matter L27–90 ✅-DONE items to 1-line pointers; keep the guard + next-move guidance.
7. Update this REFACTOR-010 status PLAN → DONE with actual saved KB.

**Discipline** (same as REFACTOR-009): this is a mechanical **text-move**, NOT a rewrite. Do NOT paraphrase, re-verdict, or re-summarize any SHIPPED narration during the move — verbatim in the archive, 1-line pointer out. Deciding whether an AD is "open" vs "closed" is a **read**, not a judgment call — go by the ✅/struck-through markers already in the block. Any ambiguous case → keep the AD in the main file (fail toward preserving forward-looking content).

## Verification

- `wc -c claudedocs/1-planning/next-phase-candidates.md` → expect ~120–140 KB after ① (~60–80 KB if ② also done), from 445 KB.
- `wc -c claudedocs/1-planning/next-phase-candidates-shipped-archive.md` → ~360 KB (holds the moved narration).
- **Zero-loss check**: `grep -c 'memory/project_phase57' <archive>` ≥ 69 (the Detail pointers moved with their blocks); every `## Sprint 57.X` header present in exactly one of {main pointer index, archive}.
- **Open-AD preservation**: every AD name that was un-closed pre-move is present in the main file's Open Carryover ADs section (spot-check a sample of 10 across old + recent sprints).
- **No narration left in main**: `awk 'NR range' | grep -cE 'pytest [0-9]|CHANGE-[0-9]|design note [0-9]|drive-through'` in the former archive region → 0 (all telemetry/CHANGE/design-note prose moved).
- Front matter roadmap (L9–24) + numbered candidates (#1–#46) byte-identical unless tier ② selected.

## Impact

- **Scope**: docs / planning only. No code, no backend, no frontend, no CI behavior change, no memory-subfile change.
- **Risk**: low. Zero information loss — SHIPPED narration is triple-preserved (memory subfile + retrospective + now the verbatim archive) and **moved, not deleted** (honors 大前提「不刪除」). The forward-looking content (open ADs + numbered candidates + roadmap) stays in the main file and is unchanged in substance.
- **Benefit**: ~300 KB (①) → ~360 KB (①+②) off every planning read of the main file, permanently, plus a prevention rule to stop a third regrowth. Same "point, don't copy" discipline the project already codified 3× (REFACTOR-001/005/009).
- **Dev-model impact**: none. Sprint execution is unchanged; only the closeout narration's destination file shifts (full block → archive file; 1-line pointer + open ADs → main file).
- **Reversible**: fully — `git revert` restores the inline blocks; the archive keeps the verbatim text regardless.

---

## References

- [REFACTOR-001](./REFACTOR-001-claude-md-memory-md-bloat-audit.md) — CLAUDE.md / MEMORY.md bloat (the origin of the "pointer, not archive" policy)
- [REFACTOR-005](./REFACTOR-005-sprint-workflow-calibration-extraction.md) / [REFACTOR-009](./REFACTOR-009-sprint-workflow-matrix-rebloat-extraction.md) — sprint-workflow.md matrix extraction (same anti-pattern, sibling file; 009 is the direct template for this doc)
- `.claude/rules/sprint-workflow.md` §Sprint Closeout — the policy this file itself violates (pointer-not-archive; the Self-Check gains a new line here)
- `claudedocs/1-planning/next-phase-candidates.md` — the file being refactored
- `claudedocs/1-planning/next-phase-candidates-shipped-archive.md` — the extraction target (created at execution)
- `memory/MEMORY.md` + `memory/project_phase57_*.md` — the authoritative per-sprint single-source the main file will point to
- `.claude/rules/file-header-convention.md` §Modification History — sibling "detail lives elsewhere, header stays lean" philosophy
