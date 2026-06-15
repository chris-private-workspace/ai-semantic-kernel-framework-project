# 34 — Skills Bundled Scripts (system-bundled `run_skill_script`)

**Purpose**: Design note extracted from Sprint 57.118 — a system-bundled skill may carry an executable script, run on demand via a new `run_skill_script` Cat-2 tool through the existing sandbox, closing the system-bundled leg of `AD-Skills-Bundled-Scripts`.
**Category / Scope**: 範疇 5 (Prompt Construction — `Skill.script` + loader) + 範疇 2 (Tool Layer — `run_skill_script` + `SandboxBackend` reuse) + business_domain wiring / Sprint 57.118
**Created**: 2026-06-15
**Last Modified**: 2026-06-15
**Status**: Active (spike-extract; verified ratio ~96%)

> **Modification History**
> - 2026-06-15: Initial creation (Sprint 57.118) — system-bundled `run_skill_script` (4th Skills slice)

> **Epic chain**: `31-skills-system-spike.md` (bundled model-invoked lazy-load) → `32-skills-per-tenant-catalog.md` (per-tenant overlay) → `33-skills-slash-command.md` (user-invoked force-load) → **this** (bundled executable scripts).

---

## 1. Spike Summary (US-1..US-6 as wired in Sprint 57.118)

A SYSTEM-BUNDLED skill may now ship a sibling executable script alongside its `SKILL.md`. When a skill's instructions tell the model to run its script, the model calls the new `run_skill_script(skill_name)` Cat-2 tool → the handler looks up `Skill.script` (the SERVER-controlled source, loaded from disk at registry build — never an LLM-supplied arg) → it runs through the SAME `SandboxBackend` that powers `python_sandbox` (Docker in prod, Subprocess in dev/CI) → returns JSON `{stdout, stderr, exit_code, duration_seconds, killed_by_timeout}`. The model reports the script's stdout. The trust boundary is **supply-chain-at-authorship (git + code review) + isolation-at-runtime (sandbox)**: tenant-authored scripts are explicitly out of scope.

- **Verified period**: 2026-06-15 (Day 0–3, single-day spike)
- **Calibration**: bottom-up ~6.5 hr → class-calibrated commit ~3.9 hr (`skills-bundled-script-spike` 0.60, 1st data point) → actual ~3.6 hr → ratio ~0.92 (parent-direct; `agent_factor` 1.0)
- **Verification**: backend pytest **+14** (2630 → 2644); mypy `src` 0/371 (+1 `digest.py`); run_all 10/10 (wire count 24); Vitest 873 unchanged / mockup 51 unchanged (NO frontend touched); 1 drive-through leg (real Docker sandbox)

## 2. Decision Matrix

### 2.1 Trust model — whose scripts run

| Option | How | Pros | Cons | Decision |
|--------|-----|------|------|----------|
| **A. System-bundled only** | the script is the source of a git-authored `bundled/<stem>.py`; loaded at registry build; tenants CANNOT supply scripts | Trust = supply-chain-at-authorship (PR review) + sandbox-isolation-at-runtime; no untrusted-code-author surface; smallest verifiable slice | tenants can't ship custom scripts yet (deferred) | ✅ **CHOSEN** (user-confirmed 2026-06-15) |
| B. Tenant-authored scripts | a tenant uploads script text into `tenant_skills.script` (DB) → run in sandbox | self-service per tenant | a tenant becomes an untrusted code author; needs deny-list scanning + stricter sandbox quota + abuse/billing controls before it is safe — a much bigger slice | ❌ deferred (`AD-Skills-Bundled-Scripts` tenant leg) |

### 2.2 Tool — how the model runs the script

| Option | How | Pros | Cons | Decision |
|--------|-----|------|------|----------|
| **A. Dedicated `run_skill_script(skill_name)`** | a new Cat-2 tool; the only arg is the SKILL NAME; the source comes from `Skill.script` server-side | the LLM cannot supply / tamper with the code (only names a skill); the value is provably script-produced; clean audit | one more tool spec | ✅ **CHOSEN** |
| B. Reuse `python_sandbox(code)` | tell the model to paste the skill's script into the existing `python_sandbox` tool | no new tool | the code would pass THROUGH the LLM (it could fabricate / mutate it) — defeats the "provably the bundled script ran" property; also `RiskyActionDetector` scans the `code` arg, the skill path shouldn't | ❌ rejected |

## 3. Verified Invariants (file:line; gate + drive-through proven)

- **`Skill.script` field** — `agent_harness/skills/registry.py:54-68`: a `frozen` dataclass gains `script: str | None = None` (keyword-defaulted LAST → `with_overlay` keyword construction at `platform_layer/skills/service.py` and all existing call sites stay valid). Tenant-overlay skills and bundled skills with no sibling `.py` stay `script=None`. Verified `test_skills_registry.py` (`Skill.script` defaults None; overlay skills → None).
- **Sibling-script loader** — `registry.py:130-160` `from_dir` globs `*.md` only; after frontmatter validation it reads a sibling `md_path.with_suffix(".py")` (`is_file()` guard; `OSError` → warn + `None`) into `Skill.script`. A lone `.py` with no `.md` is never registered (the glob is `*.md`). Verified `test_skills_registry.py` (loads a sibling `<stem>.py`; no sibling → None; lone `.py` ignored).
- **`run_skill_script` tool spec** — `agent_harness/skills/tool.py:114-144`: `RUN_SKILL_SCRIPT_TOOL_SPEC` — input `{skill_name}` required, `additionalProperties:False`; `read_only=False` / `risk_level=MEDIUM` (code execution, mirrors `python_sandbox`) / `hitl_policy=AUTO` / `tags=("skills","exec")`.
- **Handler runs the SERVER source, recoverable on miss** — `tool.py:164-202` `make_run_skill_script_handler(registry, sandbox=None)`: unknown skill → `"Unknown skill … Available skills: …"` (recoverable message, NOT an exception); `skill.script is None` → `"Skill … has no bundled script to run."`; else `backend.execute(skill.script, timeout_seconds=10.0, memory_mb=256, network_blocked=True)` → JSON. The script source is `Skill.script` (server-loaded), never `call.arguments`.
- **Lazy process-wide sandbox singleton** — `tool.py:153-161` `_get_default_sandbox()` resolves `default_sandbox()` (`tools/sandbox.py:399`) ONCE on first call. `make_default_executor` runs per chat request, so resolving at handler-build time would probe the Docker daemon every request; the singleton probes once. Tests inject an explicit backend and never touch the singleton.
- **Chat-path wiring (opt-in) + risk-blind auto-PASS** — `business_domain/_register_all.py:306-310`: inside the `if skill_registry is not None:` block (the same 57.113 opt-in), after `read_skill`, `registry.register(RUN_SKILL_SCRIPT_TOOL_SPEC)` + `handlers["run_skill_script"] = make_run_skill_script_handler(skill_registry)` (sandbox=None → the lazy singleton; NO `default_sandbox` import here → NO per-request Docker probe). The chat permission matrix is derived risk-blind from `registry.list()` at `api/v1/chat/handler.py:588-592` (`requires_approval = name in escalate_tools`), so the new MEDIUM-risk tool auto-PASSes like `read_skill` — no `capability_matrix.yaml` entry needed. Negative guard: with NO registry, neither `read_skill` nor `run_skill_script` is registered (`test_skills_wiring.py`).
- **Real-sandbox execution (test layer)** — `tests/integration/api/test_skills_wiring.py::test_run_skill_script_runs_bundled_digest_in_real_sandbox`: the bundled `digest` script runs in a directly-injected **`SubprocessSandbox()`** (deterministic, runs on Windows + Docker-less CI — chosen over a Docker-availability skip) and `stdout.strip()` EQUALS the locally-computed `hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()`.
- **Drive-through (real chat-v2 :3007 + Azure gpt-5.2 + REAL DockerSandbox 29.5.2, tenant acme-skills)** — prompt "use the digest skill to compute the canonical digest by running its bundled script". Loop: turn 0 `read_skill("digest")` → instructions; turn 1 `run_skill_script({"skill_name":"digest"})` → span 546 ms → `{"stdout":"039e824c…517b8b1e\n","exit_code":0,"duration_seconds":0.484,"killed_by_timeout":false}`; turn 2 final answer `039e824cfd166d0c491ca12b290e28b6da2d89b0eaceca4b33a57231517b8b1e` (== local ground truth byte-for-byte) + verification 0.99. `default_sandbox()` → `DockerSandbox` confirmed here → ran in a hardened container (`--cap-drop=ALL` / `read_only` / `network=none` / non-root). **First main-flow proof of sandboxed execution** — the LLM cannot fabricate a sha256, so a matching value proves the sandbox actually ran the bundled script. Screenshot `…/sprint-57-118/artifacts/sprint-57-118-drivethrough-digest.png`.

**Verification commands**: `pytest tests/unit/agent_harness/skills tests/integration/api/test_skills_wiring.py` (45 passed, incl. the real-SubprocessSandbox digest run); drive-through reproduce — `GET /api/v1/chat/skills` (dev-login acme-skills) lists `digest`; chat-v2 `real_llm` → ask for the canonical digest → reported value must equal `python -c "import hashlib;print(hashlib.sha256(b'agent-harness-bundled-skill').hexdigest())"`.

**Test fixtures**: `bundled/digest.md` + `bundled/digest.py` ARE the fixtures (a real bundled skill, not a mock); `test_skills_tool.py` uses a `_StubSandbox(SandboxBackend)` for the unit unknown/no-script/JSON-shape cases.

## 4. Cross-Category Contracts (17.md)

**Decision: NO new contract in 17.md.** `Skill.script` is an intra-Cat-5 field on the existing `Skill` dataclass; `run_skill_script` is a Cat-2 tool that REUSES the existing `SandboxBackend` ABC (`tools/sandbox.py`) — no new ABC, no provider-neutral type change. This mirrors the 57.113/57.114/57.115 precedent: the Skills registry seam rides the existing `build_handler(skill_registry=)` parameter and was never registered as a 17.md contract. The Day-0 §17.md question ("does `run_skill_script` warrant a §registry line?") resolves **no** — it is one more `ToolSpec` over the same seam, like `read_skill`.

## 5. Open Invariants (deferred — NOT verified here)

- **Tenant-authored scripts** (`AD-Skills-Bundled-Scripts` tenant leg) — `tenant_skills.script` + sandbox quota + deny-list scan of the tenant source + abuse/billing controls; a tenant becomes an untrusted code author. NOT in this slice.
- **Multi-file script resources** — a skill bundling a directory (helper modules / data files) rather than a single `<stem>.py`; the loader reads ONE sibling `.py` only.
- **Script input / arguments** — `run_skill_script` takes only `skill_name`; passing runtime args to the script is additive (YAGNI).
- **Deny-list scan of bundled scripts** — `RiskyActionDetector` scans the `python_sandbox` `code` arg, NOT the bundled-script path (the trust model is authorship-time review). A bundled script is assumed reviewed; an automated scan of `Skill.script` at load is deferred.
- **Skills authoring UI / inspector affordance** — `AD-Skills-Authoring-UI` / `AD-Skills-Inspector-Affordance` (separate ADs); not touched here.

## 6. Rollback / Fallback

- The feature is purely additive + opt-in. `Skill.script` defaults `None` (existing skills unaffected); `run_skill_script` is registered ONLY when `skill_registry` is supplied (the 57.113 opt-in). NO DB / migration / wire event / codegen this sprint — reverting the 3 code commits (`2cedace8` + `5de95ef5`) restores the exact 57.117 state with nothing to undo.
- The sandbox is the SAME backend `python_sandbox` already trusts; no new isolation surface. Removing the demo `bundled/digest.{md,py}` only drops the demo skill (the loader simply registers one fewer skill).
- Fallback already in place: if Docker is unreachable at runtime, `default_sandbox()` resolves to `SubprocessSandbox` (a WARN is logged) — the tool still executes, just in the weaker isolation tier.

## 7. References

- `31-skills-system-spike.md` (model-invoked core) · `32-skills-per-tenant-catalog.md` (per-tenant overlay) · `33-skills-slash-command.md` (user-invoked force-load)
- `claudedocs/5-status/agent-harness-cc-parity-20260607.md` row 9 (Skills System cc-parity gap)
- `CHANGE-085-skills-bundled-scripts.md` · `.../sprint-57-118/{plan,checklist,progress,retrospective}.md`
- `.claude/rules/sprint-workflow.md` §Drive-Through Acceptance + §Scope-class matrix (NEW `skills-bundled-script-spike` 0.60)
- Reused: `agent_harness/tools/sandbox.py` (`SandboxBackend` / `default_sandbox`) · `agent_harness/tools/exec_tools.py` (`python_sandbox` — the JSON shape mirrored)

## 8. Modification History

- 2026-06-15: Initial creation (Sprint 57.118)
