# Sprint 57.115 Retrospective — Skills Slash-Command (`/skill-name` force-load)

**Closed**: 2026-06-14 · **Slice**: Skills System epic, 3rd thin vertical (closes `AD-Skills-Slash-Command`)
**Commits**: `2f09adfb` (D1) + `2b9b20e2` (D2) + `182a2c9c` (D3) + D4 closeout (this) · **PR-pending**

---

## Q1 — What was delivered?

The user-invoked half of the Skills System: a `/skill-name` composer picker + **deterministic force-load** (the picked skill's full instructions injected into the turn's system prompt under `## Active Skill`, model-independent). Full-stack: a DRY `render_skill_instructions` helper, `build_handler` force-load, a non-admin `GET /chat/skills` picker list, a `ChatRequest.force_load_skill` field + router validate-and-pass, a greenfield `SkillSlashMenu` + InputBar `/`-trigger/parse, `useChatSkills`. `make_default_executor`/`loop.py`/`read_skill` self-select/wire(24)/codegen/migration UNTOUCHED.

## Q2 — Estimate accuracy (calibration)

- **Scope class NEW `skills-slash-command-fullstack` 0.55** (1st data point). Bottom-up est ~17 hr → class-calibrated commit ~9.5 hr (mult 0.55).
- **Agent-delegated: NO** (parent-direct, like 57.114 — the plan said "partial" but no code-implementer agent was used; only 2 Explore recon agents at Day-0). → `agent_factor 1.0`; the 0.55 class mult alone is the calibration.
- **Actual ≈ committed** → ratio **~1.0 IN band** → KEEP 0.55 (1 data point; pending 2-3 sprint validation). The greenfield FE picker (the main net-new risk) landed cleanly via the InputBar precedent + mockup tokens; the backend was light mirror work (the 57.113 catalog seam made force-load a 1-append change).

## Q3 — What went well?

- **Day-0 三-prong paid off**: the `build_real_llm_handler` vs `build_handler` delegation + the exact `read_skill` string + the chat deps + the route-collision check were all confirmed before code → zero mid-sprint surprises on the backend.
- **DRY refactor byte-identical**: extracting `render_skill_instructions` kept the existing `test_skills_tool.py` green (Never-Delete satisfied, no test conversion).
- **The 57.113 catalog seam**: force-load was a single `## Active Skill` append after the existing catalog append — minimal blast radius.
- **Drive-through nailed the determinism proof**: Leg A's `read_skill: 0×` in the live Loop trace + the output following the skill structure is exactly the AP-4 guard the Drive-Through rule demands (the picker DRIVES the request, not a cosmetic menu).

## Q4 — What to improve / lessons (carryover)

- **`fill` replaces, doesn't append** (Playwright): a mid-drive-through `fill("task")` wiped the `/release-notes ` prefix → had to re-fill the FULL `/release-notes task` string. Lesson: for composer force-load drive-throughs, `fill` the complete `/skill task` in one go (the parse happens on send), OR use `pressSequentially` to append.
- **`env_file=".env"` is CWD-relative**: starting uvicorn from `backend/` missed the repo-root `.env` → no Azure. Restart from repo-root with `--env-file .env` (Risk Class E reinforcement — the env-load failure mode, distinct from stale-process).
- **mockup-fidelity color-literal budget**: a net-new floating element's shadow `oklch(0 0 0 / 0.3)` is a colour literal (51→52) → use the `var(--shadow)` token. The Day-0 silent-constraint-delta drift class in action (caught at the gate, fixed same-commit).
- **New FE hook breaks existing component tests**: InputBar importing `useChatSkills` (TanStack) broke `InputBar.test.tsx` (no QueryClientProvider) → added a `useChatSkills` mock there (Never-Delete-safe). Lesson: when a shared component gains a new hook dependency, grep its existing test files for the missing mock/provider.

## Q5 — Anti-pattern self-check

- **AP-4** (Potemkin): ✅ the drive-through proves force-load CHANGES the output + `read_skill` 0× (not a cosmetic menu); unknown `/token` is honest plain-text (no dead control / no fixture).
- **AP-2** (reachable main flow): ✅ composer → `send` → `streamChat` → chat POST → `build_handler` force-load; `GET /chat/skills` from the picker.
- **AP-3** (no scattering): ✅ helper in Cat 5, endpoint+field in api/v1/chat, picker in chat_v2.
- **AP-6** (no speculative): ✅ single `force_load_skill` (no multi-skill list); list endpoint name+description only.
- **AP-11** (no version suffix): ✅.

## Q6 — Gates

mypy `src` 0/370 · `run_all.py` 10/10 (wire 24, no codegen) · backend pytest **2616+5skip (+14, 0 del)** · FE lint 0 · build · Vitest **863 (+12)** · mockup-fidelity **51**. Drive-through ALL 3 legs PASS (real chat-v2 + Azure gpt-5.2).

## Q7 — Carryover (→ next-phase-candidates.md)

`AD-Skills-Slash-Command` **CLOSED**. Remaining Skills epic ADs: `AD-Skills-Inspector-Affordance` (a "skill force-loaded" SSE event + Inspector chip; force-load is invisible post-send), `AD-Skills-Authoring-UI`, `AD-Skills-Per-Tenant-Quota`, `AD-Skills-Bundled-Scripts`, multi-skill per command (YAGNI). The harness-deepening 10-slice set + the C-12 IAM legs (WebAuthn/recovery) remain the other open pools.

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/33-skills-slash-command.md`
**Verified ratio (estimated)**: ~96%
**8-Point Quality Gate**: [x] 1 section header (US-mapped) · [x] 2 file:line · [x] 3 decision matrix (A/B/C + sub-decisions) · [x] 4 verification (pytest/Vitest/drive-through) · [x] 5 test fixtures referenced · [x] 6 open invariants bounded · [x] 7 rollback path · [x] 8 17.md cross-ref (decision: NO new contract)
**Reviewer pass**: self-review
