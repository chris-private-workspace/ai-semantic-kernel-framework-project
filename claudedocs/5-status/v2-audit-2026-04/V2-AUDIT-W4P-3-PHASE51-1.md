# V2 Audit W4P-3 — Sprint 51.1 (Cat 2 Tool Layer Level 3)

**Audit Date**: 2026-04-29
**Scope**: Commits `54683039 → 7595e606` (Days 1–5)
**Auditor**: Verification audit per W4-Pre series (mirror W4P-4 method)
**Result**: 🟡 **PASS WITH CRITICAL CAVEATS** — Cat 2 structurally Level 3, but sandbox isolation **far weaker than retrospective implies** and memory placeholder tests are **broken regression after 51.2**.

---

## Summary Table

| Dimension | Verdict | Evidence |
|-----------|---------|----------|
| Plan/Checklist alignment | ✅ HONEST | Retrospective explicitly logs 3 plan deviations + tool count mismatch (4→6) + 1 SKIPPED relaxation |
| ToolSpec hitl_policy / risk_level | ✅ REAL | First-class fields wired, 18 stubs migrated, `ToolHITLPolicy` enum (renamed from plan §決策 1 to avoid `_contracts/hitl.py` collision) |
| ToolRegistryImpl | ✅ REAL | Dict-based + JSONSchema validate at register + duplicate detection |
| ToolExecutorImpl | ✅ REAL | Permission gate + JSONSchema validate + tracer span + metric emit + concurrency batch |
| PermissionChecker (3-dim) | ✅ REAL | DENY > REQUIRE_APPROVAL > ALLOW; tested separately via `_AllowAllPermissionChecker` helper |
| **SubprocessSandbox isolation** | 🔴 **WEAK** | **Confirmed: can read entire C:/ from sandbox**; only wall-time + POSIX rlimit; **no fs/network isolation** |
| python_sandbox tool | ✅ via subprocess (not exec/eval) | `asyncio.create_subprocess_exec(sys.executable, code_file)` — proper argv-list, no shell |
| JSONSchema enforcement | ✅ REAL | `Draft202012Validator` cached; ToolResult.success=False on violation |
| Chat handler integration | ✅ **NOT Potemkin** (vs W4P-4) | `handler.py:78,135` calls `make_default_executor()` — main flow REALLY wired through ToolExecutorImpl |
| Tests mock vs real (AP-10) | ✅ **PASSED** (vs W4P-4) | `0 MagicMock/AsyncMock` in `tests/unit/agent_harness/tools/`; sandbox uses real subprocess |
| W3-2 / W4P-4 mirror anti-pattern | ⚠️ **PARTIAL** | `ExecutionContext.tenant_id` plumbed but **PermissionChecker.check() does NOT consult it** (CARRY-023 Phase 53.3) |
| tools_registry multi-tenancy | ❌ **W1-4 P2 carryover NOT addressed** | Registry is process-singleton; no per-tenant scoping; plan §決策 4 explicitly defers to 53.3 |
| Test suite | ⚠️ 48P / 2F / 1S | **2 unexpected FAIL** in builtin tests after 51.2 wired real memory handlers |
| Block 52.2? | 🟡 **NO**, but blocks 53.3 with 3 hard deps | See Phase F |

---

## Phase A — Plan/Checklist alignment

✅ Plan / checklist / retrospective all present (`phase-51-tools-memory/sprint-51-1-{plan,checklist}.md`, `agent-harness-execution/phase-51/sprint-51-1/retrospective.md`).

Retrospective is **unusually honest**:
- §"Improve Next" item 3 admits plan §決策 6 said "4 builtin tools" but reality is 6 (echo + python_sandbox + web_search + request_approval + memory×2)
- §"Improve Next" item 2 admits sandbox plan §3.3 "block /tmp/escape.txt" was **over-optimistic** — chroot/namespace not in 51.1 scope
- 3 architectural collisions logged with rationale (HITLPolicy enum collision, ExecutionContext relocation, sandbox scope rescope)
- DoD §10 e2e_with_mock_patrol marked "Partial" — explicitly notes HIGH-risk tools surface as REQUIRE_APPROVAL through production permission gate

Estimate accuracy 24% (V2 7-sprint avg ~20%). **No estimate inflation hiding scope gaps.**

---

## Phase B — ToolSpec / Registry / Executor structure

**Code locations**:
- `agent_harness/tools/_abc.py` — ABC (49.1)
- `agent_harness/tools/registry.py:51 ToolRegistryImpl(ToolRegistry)` — concrete
- `agent_harness/tools/executor.py:91 ToolExecutorImpl` — concrete
- `agent_harness/tools/permissions.py` — PermissionChecker
- `agent_harness/tools/sandbox.py` — SandboxBackend ABC + SubprocessSandbox
- `agent_harness/_contracts/tools.py:110` — `ExecutionContext.tenant_id: UUID | None`

**ToolSpec extension (D-1)**: ✅ COMPLETE
- `hitl_policy: ToolHITLPolicy` (enum: ALWAYS_ASK / ASK_ONCE / AUTO)
- `risk_level: RiskLevel` (LOW / MEDIUM / HIGH / CRITICAL)
- 18 business stubs + 6 builtin migrated; 0 tags-encoded leftovers
- Plan §決策 1's `HITLPolicy.AUTO` would have **collided** with existing per-tenant `_contracts/hitl.py:HITLPolicy` dataclass — Day 1 caught + renamed to `ToolHITLPolicy` (logged in retro)

**ToolRegistryImpl** (`registry.py:51-72`): ✅
- Dict storage `_specs: dict[str, ToolSpec]`
- `register()` raises `ValueError` on duplicate name
- `register()` validates JSONSchema at registration (catches malformed spec early)
- `get()` / `list()` / `by_tag()` accessors

**Multi-tenancy gap** ❌:
- Registry is **single shared dict** — no `tenant_id` scoping
- Plan §決策 4 explicitly carved this out: "Tenant-aware permission … 留 51.x 或 Phase 53.x"
- W1-4 P2 carryover ("tools_registry 全局表多租戶設計評估") **NOT addressed in 51.1**
- All tenants share the same registry; tenant-private tools are not supported
- ExecutionContext carries `tenant_id` but PermissionChecker.check() never reads it (`permissions.py:87-105` — no tenant logic)

---

## Phase C — Sandbox + Permission realness (CRITICAL FINDINGS)

### C.1 SubprocessSandbox real-isolation test (live probe)

```python
sb = SubprocessSandbox()
r = await sb.execute('import os; print(os.listdir("C:/"))', timeout_seconds=5, memory_mb=128)
# RESULT: exit_code=0, stdout=['$Recycle.Bin', 'AI Project', 'Program Files', ...]
```

🔴 **CONFIRMED: sandbox can list entire C:/ drive contents from inside the "sandbox".**

**What sandbox actually does** (`sandbox.py:99-143`):
1. ✅ Wall-time timeout via `asyncio.wait_for()` — process killed at limit
2. ✅ POSIX `RLIMIT_AS` (memory) + `RLIMIT_CPU` via `preexec_fn` — POSIX only
3. ✅ Fresh `tempfile.TemporaryDirectory()` as CWD
4. ❌ **NO filesystem isolation** — full host fs read/write outside CWD
5. ❌ **NO network blocking** — `network_blocked=True` is `noqa: ARG002` (literal docstring "doc-only knob")
6. ❌ **NO process tree isolation** — can spawn host processes
7. ❌ **NO memory limit on Windows** (POSIX-only path; Windows test SKIPPED)

**Retro is partially honest** (§"Improve Next" item 2 admits "/tmp/escape.txt" requires chroot), but the **actual blast radius is wider**:
- LLM-generated python can read SSH keys / .env / credentials
- LLM-generated python can write to user home / project root
- LLM-generated python can `subprocess.run` host commands
- `network_blocked` parameter is **decorative** — code accepts it but doesn't enforce

This is the hallmark of **AP-4 Potemkin Feature**: structure (param + ABC + class) exists, but the security primitive doesn't actually enforce.

**Mitigating factors**:
- python_sandbox `risk_level=MEDIUM` (per `exec_tools.py:68`) → permission gate flags as MEDIUM, not blocked
- Plan/retro/file docstrings DO say "best-effort 51.1" / "Phase 53.x adds Docker" / "CARRY-022"
- The **abstraction** (ABC + tempdir + rlimit) is the right shape; only the isolation guarantee is partial

🚨 **CRITICAL**: production deployment of python_sandbox with current SubprocessSandbox would be a security incident waiting to happen. Must be docker-replaced before any internet-exposed tenant is allowed to invoke it.

### C.2 python_sandbox tool — `exec()` vs subprocess

✅ Uses `asyncio.create_subprocess_exec(sys.executable, str(code_file), ...)` — argv list, no shell, no `exec()`/`eval()`. Proper isolation pattern even if rlimit is insufficient.

### C.3 PermissionChecker (`permissions.py:84-105`)

✅ 3-dim resolution per plan §決策 4:
1. `annotations.destructive=True AND not explicit_approval` → **DENY**
2. `hitl_policy in {ALWAYS_ASK, ASK_ONCE}` → **REQUIRE_APPROVAL**
3. `risk_level in {HIGH, CRITICAL}` → **REQUIRE_APPROVAL**
4. Else → ALLOW

Resolution order: DENY > REQUIRE_APPROVAL > ALLOW (most restrictive wins).

⚠️ **ASK_ONCE conservative behavior**: plan calls for "first-call only" semantics, but 51.1 treats every call as first-call (no per-session tracking). Retro logs this; per-session tracking lands with ApprovalManager in 53.3.

⚠️ **tenant_id captured but unused**: `ExecutionContext.tenant_id` is plumbed end-to-end but `check()` never reads it. **W3-2 / W4P-4 mirror anti-pattern is partially present**: tenant_id flows through executor signature but is currently a forward-compat decoration. Not as bad as W4P-4's `tenant_id from ToolCall.arguments` (which is LLM-controllable); 51.1 sources tenant_id from `ExecutionContext` (caller-controlled), so the security shape is correct — just not yet enforced.

### C.4 JSONSchema validation (`executor.py:225-245`)

✅ Real `jsonschema.Draft202012Validator`, **cached per spec name** (perf). Pre-execution validate; bad input → ToolResult(success=False, error=...). No try-except swallow.

---

## Phase D — Built-in tools + chat handler integration

### D.1 Built-in tools

| Tool | File | Real? |
|------|------|-------|
| echo_tool | echo_tool.py | ✅ trivial echo, real |
| python_sandbox | exec_tools.py | ✅ via SubprocessSandbox (caveat C.1) |
| web_search | search_tools.py | ✅ httpx + Bing API; CI uses mocked httpx; real key smoke = CARRY-024 (operator manual) |
| request_approval | hitl_tools.py | ✅ stub returns approval payload; ApprovalManager wiring = 53.3 |
| memory_search/write | memory_tools.py | ⚠️ post-51.2 wired to real Cat 3 (51.1 was placeholder; placeholder fallback **broken** — see Phase E) |

### D.2 Chat handler integration — **NOT Potemkin** (vs W4P-4)

```python
# api/v1/chat/handler.py:58
from business_domain._register_all import make_default_executor
# :78, :135
registry, executor = make_default_executor()
... tool_executor=executor
```

🟢 **Strong contrast with W4P-4 finding**: chat handler in W4P-4 had **0 hits** for `memory_search`/`memory_write` (Cat 3 Potemkin); in W4P-3, chat handler **really constructs and consumes** ProductionToolExecutor + Registry via `make_default_executor()`. **AP-4 Potemkin not present at integration layer**. Tools are routable from main flow.

---

## Phase E — Tests strength (compared to W4P-4 0.36s mock-only)

### E.1 Sprint 51.1 test run

```
tests/unit/agent_harness/tools/test_executor.py     ............... 19 PASS
tests/unit/agent_harness/tools/test_sandbox.py      .........s      9 PASS / 1 SKIP (Win RLIMIT)
tests/integration/agent_harness/tools/test_builtin_tools.py ......FF.... 10 PASS / 2 FAIL
tests/integration/business_domain/test_business_tools_via_registry.py 10 PASS

Result: 48 PASS / 2 FAIL / 1 SKIP in 1.87s
```

### E.2 Mock vs real strength

🟢 **Excellent vs W4P-4**:
- `MagicMock`/`AsyncMock` count in `tests/unit/agent_harness/tools/`: **0**
- Sandbox tests use real `asyncio.create_subprocess_exec` → real Python interpreter
- Permission tests use real PermissionChecker
- Total runtime 1.87s for 51 tests (W4P-4 was 0.36s for 69 mock tests — clear difference)

### E.3 Live sandbox isolation probe

🔴 (See C.1) Sandbox **fails** the cross-tenant escape test on Windows. POSIX rlimit memory test SKIPPED on Windows; macOS pending operator. **No platform** has full isolation guarantee in 51.1.

### E.4 🚨 **2 broken tests after 51.2 (regression)**

```
FAILED test_builtin_tools.py::test_memory_search_placeholder_raises
FAILED test_builtin_tools.py::test_memory_write_placeholder_raises
```

Root cause: 51.1 wrote placeholder handler returning `ToolResult(success=True, content='{"ok":false,...}')` (i.e. tool succeeded but reported the placeholder error in JSON body). 51.2 changed expected behavior to `success=False`. Tests assert `success is False` but actual `success is True`. The placeholder branch in `__init__.py:115-118` and `memory_placeholder_handler` were not updated when 51.2 wired real handlers.

This is a **carry-over regression from 51.2 audit** — discovered during W4P-3 because 51.1 tests are still running against 51.2 code. **Indicates lack of CI integration**: had CI been run after 51.2 closeout, this would have surfaced. ⚠️ **AP-10 Mock vs Real divergence in test fixtures vs production wiring** — placeholder branch is dead code now that production uses real handlers.

---

## Phase F — Cross-category + 17.md alignment

### F.1 17.md §3.1 alignment
✅ ToolSpec extended fields landed in §1.1 (Day 1 commit)
✅ 6 builtin tools registered in §3.1 (Day 4 commit)
⚠️ Action item AI-1 in retro: ExecutionContext + ToolHITLPolicy rows still pending in 17.md §1.1 (Day 5 closeout doc-only sync — not confirmed merged)

### F.2 Cat 2 ↔ Cat 1 (W3-1 carryover)
W3-1 audit flagged `ToolCallExecuted/Failed` events as Cat 1-emitted but Cat 2-owned. Status in 51.1: **NOT addressed** — events still emitted from `executor.py:158-200` inside Cat 2's tracer span (now correctly owned-by-Cat 2). ✅ Improvement vs W3-1.

### F.3 Cat 2 ↔ Cat 9 (Guardrails) hooks
- ToolSpec.hitl_policy + risk_level ARE the hooks for Phase 53.3 Guardrails
- PermissionDecision enum is the contract
- Phase 53.3 wires real ApprovalManager + tenant RBAC
- 🟢 **Cat 2 design is forward-compatible** with 53.3 without rework

---

## Findings ranked by criticality

### 🚨 CRITICAL (block production rollout, NOT 52.2)

**F-1: SubprocessSandbox isolation is decorative on Windows**
- Live test confirmed: `os.listdir("C:/")` succeeds from inside sandbox
- `network_blocked` parameter is `noqa: ARG002` literal — accepts but doesn't enforce
- Per `risk_level=MEDIUM`, permission gate doesn't auto-block; LLM-generated code with file/network access executes against host
- **Mitigation**: Block python_sandbox in production tenant config until CARRY-022 Docker sandbox lands (Phase 53.x)
- **Audit verdict**: Plan/retro/docstrings are honest about this being "best-effort 51.1"; no deception. But the GAP between docstring "best-effort" and real-world "fully open host" is wider than retro's "/tmp/escape.txt" framing implies.

**F-2: 2 broken tests after 51.2 wiring**
- `test_memory_search_placeholder_raises` + `test_memory_write_placeholder_raises` FAIL
- Memory placeholder handler returns `success=True, content='{"ok":false,...}'` but tests assert `success is False`
- Suggests no CI gate after 51.2 closeout (W4P-4 also flagged 0 chat router → memory tool calls — same Cat 3 wiring quality issue)

### 🟡 HIGH (block 53.3 governance sprint)

**F-3: tools_registry multi-tenancy NOT addressed (W1-4 P2 carryover)**
- Registry is process-singleton dict; no tenant scoping
- Plan §決策 4 explicitly defers to 53.3
- BUT W1-4 P2 carryover should have at least produced a design note in 17.md or retro CARRY — instead, silently deferred

**F-4: ExecutionContext.tenant_id plumbed but not consulted**
- W3-2 mirror anti-pattern: tenant_id flows through signature, doesn't gate access
- Better than W4P-4 (which read tenant_id from LLM-controllable `ToolCall.arguments`), but still not enforced
- 53.3 must add: `if spec.tenant_id and spec.tenant_id != context.tenant_id: return DENY`

### 🟢 MEDIUM (improvement actions for 51.x backlog)

**F-5**: AI-1 (17.md ExecutionContext + ToolHITLPolicy doc sync), AI-2 (handler docstring stale), AI-3 (echo_tool TYPE_CHECKING refactor), AI-4 (sandbox platform paths)

**F-6**: ASK_ONCE policy treats every call as first-call (no per-session tracking) — 53.3 ApprovalManager fixes

---

## Anti-pattern gradient

| AP # | Status | Notes |
|------|--------|-------|
| AP-1 (Pipeline-as-Loop) | N/A | Cat 2 not loop-based |
| AP-2 (Side-track) | ✅ Pass | Reachable from `api/v1/chat/handler.py` |
| AP-3 (Cross-dir scatter) | ✅ Pass | All in `agent_harness/tools/` |
| AP-4 (Potemkin) | 🔴 **PRESENT** in sandbox isolation; ✅ NOT in chat integration | network_blocked param is decorative; isolation guarantees on Windows are weaker than docstrings imply |
| AP-7 (Context rot) | N/A | |
| AP-8 (No PromptBuilder) | N/A | Cat 5 |
| AP-9 (No verification) | ⚠️ Partial | Permission ≠ output verification (Phase 54.1) |
| **AP-10 (Mock vs Real)** | ✅ **Pass** | 0 MagicMock; real subprocess sandbox; **strong contrast vs W4P-4** |
| AP-11 (Version suffix) | ✅ Pass | `_inmemory.py` deleted; no `_v1`/`_v2` |

---

## Block 52.2? Verdict: 🟡 **NO, but with quarantine**

Sprint 52.2 (Cat 5 Prompt Construction) does **not** depend on:
- Sandbox isolation (52.2 doesn't run code)
- Multi-tenant tool registry (52.2 doesn't dispatch tools)
- ApprovalManager wiring (52.2 doesn't gate)

Sprint 52.2 **does** depend on:
- ✅ ToolSpec stable (provided)
- ✅ ToolRegistry.list() / by_tag() for prompt assembly (provided)

→ **52.2 unblocked.**

But:
- 🚨 **Production rollout of python_sandbox MUST be quarantined** until Docker sandbox (CARRY-022, Phase 53.x)
- 🚨 **53.3 has 3 hard blockers** introduced/inherited here:
  1. tools_registry multi-tenant scoping (W1-4 P2 carryover)
  2. PermissionChecker tenant_id consultation
  3. Real ApprovalManager wiring
- 🚨 **2 failing tests** must be fixed before next merge to main (FIX-XXX-memory-placeholder-success-flag)

---

## Recommendations (highest impact first)

1. **Disable python_sandbox in production tenant config** until CARRY-022 lands (1-line config; flag tool as `enabled_tenants=[]`)
2. **Fix F-2 placeholder test regression** (decide: should placeholder return `success=False` or `success=True+ok:false`? Update either test or handler; cannot have both)
3. **Document SubprocessSandbox real blast radius** in `sandbox.py` docstring — current "best-effort" understates Windows reality (no rlimit + no fs/net isolation = essentially no enforcement)
4. **CI gate** to prevent future 51.2-style regressions (run `tests/integration/agent_harness/tools/` in pre-merge)
5. **Schedule 53.3 dependency map**: F-3 + F-4 + ApprovalManager — all three needed for tenant-aware Cat 2

---

## Compared to W4P-4 (Cat 3 Memory)

| Dimension | W4P-3 (Cat 2) | W4P-4 (Cat 3) |
|-----------|---------------|---------------|
| Chat handler integration | ✅ REAL (`make_default_executor()` called) | ❌ Potemkin (0 memory_search/write hits) |
| Mock vs real (AP-10) | ✅ 0 MagicMock | ❌ All 69 tests mock-only, 0.36s |
| tenant_id source | ExecutionContext (caller-controlled) | ToolCall.arguments (LLM-controllable) |
| Multi-tenancy enforcement | Plumbed but not consulted | Layer-level enforced (64 grep) but bypassed by tools handler |
| Critical security gap | Sandbox isolation decorative | tenant_id from LLM = privilege escalation |

**W4P-3 is structurally healthier than W4P-4** at integration + test layer, but harbors a **larger production security risk** at the sandbox layer.

---

**Audit duration**: ~75 min
**Files inspected**: 11 source + 4 test + 3 planning
**Live probes**: 1 (real sandbox C:/ listing)
**Block 52.2**: NO
**Block 53.3**: YES (3 hard deps)
**Production caveat**: python_sandbox must be quarantined until Docker sandbox
