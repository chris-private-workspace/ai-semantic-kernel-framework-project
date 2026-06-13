# Sprint 57.113 Retrospective — Skills System (thin vertical, model-invoked lazy-load)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-113-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-113-checklist.md) · [Progress](./progress.md)

**Closed**: 2026-06-13. Opens the Skills System epic (cc-parity row 9) — the first thin vertical: model-invoked lazy-load. Drive-through ALL 3 legs PASS.

---

## Q1 — What shipped?

A Claude-Code-style model-invoked lazy-load Skills System (first vertical): a system-global `SkillRegistry` (`agent_harness/skills/`, Cat 5) loads bundled `SKILL.md` files; a cheap "## Available Skills" name+description block is appended to the system prompt; a `read_skill` tool (Cat 2) lazy-loads a skill's full instructions on demand when the model self-selects one. Wired into the chat main flow (`make_default_executor` opt-in + `build_handler`/`build_real_llm_handler` + `router`). Two REAL bundled skills (`code-review`, `summarize`). No DB / no migration / no new wire event (count 24) / no frontend.

## Q2 — Estimate accuracy + calibration

- Bottom-up est ~13 hr → class-calibrated commit ~8 hr (NEW scope class `skills-system-spike` mult 0.60). Actual ≈ 7.5 hr (Day 0 ~1 + Day 1 ~2.5 + Day 2 ~4 wait, Day 2 actual ~4 incl. tests; Day 3 dt ~1; closeout ~1). Ratio **actual/committed ≈ 0.94** (IN band).
- **NEW scope class `skills-system-spike` 0.60 — 1st data point, ratio ≈0.94 IN band → KEEP** (pending 2-3 sprint validation). Greenfield cross-category (Cat 5 module + Cat 2 tool + frontmatter loader + main-flow wiring + drive-through); shape comparable to `subagent-child-loop-spike` 0.60 / `loop-injection-primitive-spike` 0.55.
- **Agent-delegated: no** — parent-direct (new domain with design decisions: registry shape, catalog-block format, read_skill contract, injection seam). `agent_factor = 1.0`, 3-segment form.

## Q3 — What went well?

- **Day-0 三-prong paid off**: the critical D1 (system_prompt → system message seam) was confirmed GREEN by tracing `loop.py:1899` + the persona precedent — so the injection rode the proven `system_prompt` seam (a 3-line append in `build_real_llm_handler`) instead of rewiring `make_chat_prompt_builder` / `DefaultPromptBuilder._build_system_section` (a much wider blast radius). D2 (capability-gate default-deny BUT chat path derives the matrix from the live registry) DROPPED a planned `capability_matrix.yaml` edit. D5/D6 (co-locate bundled + declare PyYAML) were caught before code.
- **The keystone fake-Azure test pattern** (`test_chat_keystone_wiring.py`) was directly reusable → CI-safe integration proof of the full chain (executor opt-in + system-prompt append + scripted read_skill on the SSE flow) without a live Azure call.
- **Drive-through was unambiguous**: the output shapes DISTINCTLY matched the skills (Summary/Risks-table/Fixes vs Decisions/Action-Items(owner—task)/Open-Questions), proving load+follow — exactly the AP-4 guard. The negative leg (2+2 → no read_skill) proved no false-positive coupling.

## Q4 — What to improve?

- **Pytest basename collision** (`skills/test_registry.py` vs `verification/test_registry.py`): the test dirs have no `__init__.py` → pytest rootdir import uses the bare module name → collision (the 57.109 D-DAY1-2 lesson + Risk Class C catalog). Caught only at the full-suite run, not the scoped run. **Lesson reinforced**: when adding a `test_<generic>.py`, grep the suite for the basename first, OR prefix with the area (`test_skills_*`). Already in the Risk Class catalog — applied the unique-basename remedy.
- The `agent_factor` was N/A (parent-direct) but the implementation half (after Day-0 design) was mechanical enough that a future Skills slice (e.g. per-tenant catalog) could be agent-delegated.

## Q5 — Anti-Pattern self-check (Q7 detail)

- **AP-1** (pipeline-as-loop): N/A — no new loop.
- **AP-2** (side-track): ✅ `read_skill` reaches the main flow (router → build_handler → make_default_executor → executor); the catalog block reaches the system prompt. No dead code. The drive-through proved both are live.
- **AP-3** (cross-dir scatter): ✅ skills concentrated in `agent_harness/skills/`; the tool registration in the established `_register_all.py` home.
- **AP-4** (Potemkin): ✅ the bundled skills are REAL (the drive-through output shape proves the model loaded + followed them, not a stub); `read_skill` actually returns instructions; the block actually lists skills. The negative-guard tests confirm absence-when-not-wired.
- **AP-8** (PromptBuilder single entry): ✅ the block rides the proven `system_prompt` seam (the loop's system message); no second prompt-assembly path, no bare messages list.
- AP-5/6/7/9/10/11: N/A or ✅ (no PoC, no future-proofing abstraction, no context-rot surface, no version suffix, no mock/real divergence — `read_skill` uses the same registry in tests + runtime).

## Q6 — Spike design note (§5.5 — spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/31-skills-system-spike.md`
**Verified ratio (estimated)**: ~95% (every §3 invariant has a file:line + a verification test/command; the only non-verified content is §5 Open Invariants, explicitly fenced as deferred).
**8-Point Quality Gate**:
- [x] 1. Section headers map to the spike US (US-1 substrate / US-2 wiring)
- [x] 2. Every technical claim has file:line
- [x] 3. Decision rationale has a comparison matrix (the 3 invocation options + sub-decisions)
- [x] 4. Verification commands (pytest + mypy + run_all + the drive-through)
- [x] 5. Test fixture reference (the named tests + the MockChatClient keystone pattern)
- [x] 6. Open invariants clearly fenced (§5 deferred, NOT presented as verified)
- [x] 7. Rollback path (§6 — < 1 hr, no data migration, default-None params)
- [x] 8. 17.md cross-ref (§4 — no new contract per the identity/MFA precedent)

**Reviewer pass**: self-review.

## Q7 — Carryover (→ next-phase-candidates)

Skills System epic OPENED (this spike DONE). Deferred ADs: `AD-Skills-Per-Tenant-Catalog` · `AD-Skills-Slash-Command` · `AD-Skills-Inspector-Affordance` · `AD-Skills-Authoring-UI` · `AD-Skills-Bundled-Scripts` · skill-aware prompt-caching boundary.
