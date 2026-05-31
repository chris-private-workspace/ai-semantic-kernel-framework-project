# A-3 Deep Analysis: Cat 11 Subagent Orchestration — HANDOFF Real Ship

**Purpose**: Single-point deep analysis of why subagent orchestration (esp. HANDOFF) is not live in the production loop, what it takes to ship it, and the important finding that 3 of the 4 modes are a cheap win while HANDOFF itself is the expensive, design-open part. Analysis only.
**Category / Scope**: 範疇 11 (Subagent Orchestration) / cross-cutting wiring / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for a future sprint)

> **Modification History**
> - 2026-05-31: Initial creation — A-3 of the Area-A wiring-gap deep-analysis series; 2-agent parallel audit (current-code-truth + planning-target) building on `claudedocs/1-planning/cat11-handoff-scope-analysis-20260531.md`

> **Related**
> - `integration-progress-20260531.md` — parent integration snapshot (Area A item 3)
> - `claudedocs/1-planning/cat11-handoff-scope-analysis-20260531.md` — the Sprint-57.63-era scope doc this builds on
> - `01-eleven-categories-spec.md §範疇11` / `17-cross-category-interfaces.md §Contract 11` / `06-phase-roadmap.md §Sprint 54.2`

---

## 0. Headline

Cat 11 is **different in kind from A-1/A-2**. Those were "inject a complete component via an existing ctor param; the guarded call-site activates" (the 57.63 pattern). Cat 11 cannot be activated that way because: (a) there is **no `subagent_dispatcher` ctor param on `AgentLoopImpl` at all**, (b) the HANDOFF executor is a **hollow stub** (not a complete component), (c) shipping HANDOFF **requires a loop.py behavioral change** (the HANDOFF branch must dispatch, not terminate), and (d) the plan itself leaves several HANDOFF contracts **TBD** (genuine open design). The high-value, low-cost win here is **not HANDOFF** — it is activating FORK/TEAMMATE/AS_TOOL, which have working executors.

---

## 1. Current state — correcting the earlier audit

> **Correction to the integration snapshot**: I previously wrote "FORK/TEAMMATE/AS_TOOL reach the loop via auto-registered tools; only HANDOFF is a stub." Ground-truth says: **all 4 modes are uninjected in production** — `make_default_executor` registers **no** Cat 11 tools, and `AgentLoopImpl` has **no** `subagent_dispatcher` param. The real distinction is: FORK/TEAMMATE/AS_TOOL are **singly broken** (no injection, but working executors ready to use); **HANDOFF is doubly broken** (no injection AND a hollow executor).

| Component | Status | Evidence |
|-----------|--------|----------|
| `SubagentDispatcher` ABC (`spawn`/`wait_for`/`handoff`) | ✅ built | `subagent/_abc.py:33` |
| `DefaultSubagentDispatcher` | ✅ built / ❌ never injected | `subagent/dispatcher.py:91` |
| `ForkExecutor` / `TeammateExecutor` / `AsToolWrapper` | ✅ implemented (working) | `subagent/modes/fork.py` / `teammate.py` / `as_tool.py` |
| `HandoffExecutor` | ❌ **hollow stub** (allocates `uuid4()` only; no session boot) | `subagent/modes/handoff.py:37` |
| No worktree mode | ✅ intentional | `subagent/_abc.py:10-11` |
| Contracts: `SubagentMode`(4) / `SubagentBudget` / `SubagentResult` / `AgentSpec` | ✅ | `_contracts/subagent.py:40/49/59/74` |
| `SubagentResultReducer` | ❌ **not in contracts** (plan references it) | absent from `_contracts/subagent.py` |
| `OutputType.HANDOFF` enum | ✅ live | `output_parser/types.py:57-63` |
| Parser detects handoff (tool name == `"handoff"`) | ✅ but unreachable in prod | `output_parser/classifier.py:65-69`; `make_handoff_tool` `tools.py:138-160` — **tool never registered in prod executor** |
| Loop HANDOFF branch | ❌ **terminate-stub** | `loop.py:1051-1058` → `LoopCompleted(HANDOFF_NOT_IMPLEMENTED)` + return (short-circuits before tool dispatch) |
| `subagent_dispatcher` ctor param on `AgentLoopImpl` | ❌ **does not exist** | zero grep hits across `orchestrator_loop/` |
| Cat 11 tools registered in chat executor | ❌ | `make_default_executor` (`_register_all.py`) registers no subagent tools |
| SSE `subagent_spawned`/`subagent_completed` | ✅ serialized | `sse.py:272-296` (no handoff-specific event) |
| Agent registry / `AgentDefinition` / tenant allowlist | ❌ **none exist** | zero grep hits; `modes/handoff.py:14-17` says "Phase 55+ may add allowlist / tenant boundary" |
| Tests | ⚠️ stub-only | `test_handoff.py` (3, against stub); `test_loop.py:311-330` asserts the `HANDOFF_NOT_IMPLEMENTED` stub; **no real-HANDOFF test** |

---

## 2. Target design recap (from `01.md §範疇11`, `17.md §Contract 11`)

The 4 modes' control flow:

| Mode | Parent after call | Returns to parent? | Context |
|------|-------------------|--------------------|---------|
| FORK | continues, awaits | ✅ `SubagentResult` (via `SubagentResultReducer`) | copy of parent |
| TEAMMATE | continues, mailbox | via mailbox | independent |
| **HANDOFF** | **exits permanently** | **❌ no return path** | full `LoopContext` transferred |
| AS_TOOL | continues, awaits | ✅ `ToolResult` | per-call |

**HANDOFF end-to-end (the plan's intent)**: parser → `OutputType.HANDOFF` → loop reads `target_agent: AgentSpec` → `dispatcher.handoff_to(target_agent, full_context, trace_context)` → `Checkpointer.snapshot()` (Cat 7) before exit → target boots its own `AgentLoop.run()` with transferred `DurableState` → emit `SubagentSpawned` → **parent emits `LoopCompleted` and exits** (does NOT await) → target runs independently → `SubagentCompleted` → result goes to the user, not merged back to parent (so `SubagentResultReducer` is N/A for HANDOFF, unlike FORK).

**Cat 11 target maturity = Level 4** (Sprint 54.2), NOT L5.

---

## 3. The gap, in two layers (building on the scope doc)

### Layer A — activate FORK / TEAMMATE / AS_TOOL (cheap, ~0.5-1 day, no loop.py change)
These three have **working executors**; they only lack wiring:
1. Inject a `DefaultSubagentDispatcher` (new factory `make_chat_subagent_dispatcher(...)`).
2. Register `make_task_spawn_tool` (FORK/TEAMMATE) + `as_tool` wrappers in the chat executor (extend `make_default_executor` / `register_builtin_tools`, same gap as A-1's memory tools).
3. The dispatcher needs to reach the loop. **Caveat**: there is no `subagent_dispatcher` ctor param yet — but FORK/TEAMMATE/AS_TOOL flow through **tool handlers** that close over the dispatcher, so they can work via the tool-registration path **without** a new loop ctor param (the tool handler holds the dispatcher reference). This keeps Layer A a no-loop.py-change change.
4. Tests: a loop run actually spawns a FORK subagent and gets a `SubagentResult` back.

### Layer B — HANDOFF real ship (expensive, multi-day, needs loop.py change + design decisions)
HANDOFF is doubly broken and design-open:
1. **`loop.py` behavioral change**: replace the `loop.py:1051-1058` terminate-stub with real dispatch (resolve target → `handoff_to` → snapshot → boot target loop → stream its events → parent exits). This is loop.py churn — the 57.63 "inject-and-guard-activates" pattern does NOT apply.
2. **`HandoffExecutor` real session boot**: today it only allocates a UUID. Needs to actually boot a new `AgentLoopImpl` under the target agent identity and stream its events into the same SSE response.
3. **Agent registry / catalog**: HANDOFF needs to resolve a `target_agent` to a real bootable agent. No registry exists. Decide: are the IT-ops business agents (patrol/correlation/rootcause/audit/incident) the handoff targets? Is the dormant `feature/phase-46-agent-expert-registry` worktree relevant?
4. **Tenant allowlist (security 鐵律 area)**: which agent roles a tenant may hand off to. The plan leaves this unspecified; cross-tenant handoff must be impossible (RLS + an explicit allowlist).
5. **Missing contracts**: `HandoffResult` is referenced in the dispatcher signature but **never defined**; `AgentSpec` as a handoff target descriptor is referenced but thin; the `handoff` tool's `risk_level` + `hitl_policy` are **TBD** in `17.md §3.1`.
6. **Governance**: no `max_handoff_chain_depth` / loop-prevention counter exists (budget caps give only indirect protection); add a `GuardrailEngine.check_tool_call()` rule for the handoff tool; add SSE handoff events for visibility.
7. **Cat 7 state transfer semantics**: snapshot `DurableState` before parent exit; transfer to target session.

---

## 4. Key strategic finding — HANDOFF may be the wrong thing to ship first

1. **Cost asymmetry**: Layer A (3 modes) is ~0.5-1 day and ships real capability; Layer B (HANDOFF) is multi-day, needs loop.py churn, **and** needs design decisions the plan itself left TBD.
2. **Product fit**: for an IT-ops orchestrator, **delegate-and-return** (AS_TOOL / FORK) is usually more useful than **give-up-control** (HANDOFF). An orchestrator that hands a subtask to a "rootcause" agent and gets the analysis back (AS_TOOL/FORK) fits the patrol→correlation→rootcause→incident flow better than permanently transferring control (HANDOFF). HANDOFF's value is mostly "route to a more specialised agent and never come back" — less common in this domain.
3. **Risk**: HANDOFF touches multi-tenant security (allowlist, cross-tenant) — a 鐵律 area — so it deserves a spike + design-note (per the project's spike-extract discipline), not a quick wire.

**Therefore the A-3 recommendation is to SPLIT**:
- **A-3a (recommended next, cheap)**: activate FORK/TEAMMATE/AS_TOOL via dispatcher + tool registration. No loop.py change. Ships 3 of 4 modes.
- **A-3b (HANDOFF, defer to a design spike)**: needs loop.py change + agent registry + tenant allowlist + `HandoffResult`/`AgentSpec` contract definition + governance. Run as a thin spike → design-note → sprint, because the plan left it TBD.

---

## 5. Risks / open research questions

1. **loop.py churn** for HANDOFF dispatch (B1) — first Area-A item that genuinely requires it.
2. **Plan TBDs**: `HandoffResult` undefined, `AgentSpec` thin, handoff tool `risk_level`/`hitl_policy` = TBD — these are design decisions, not just wiring.
3. **Agent registry** does not exist; is the `feature/phase-46-agent-expert-registry` work relevant, or build fresh from the business-domain agents?
4. **Tenant allowlist** (cross-tenant handoff prevention) — security 鐵律; must be designed, not assumed.
5. **Infinite handoff chains** — no depth counter; budget caps are indirect only.
6. **SSE mid-stream control transfer** — streaming the target agent's events into the same response after parent exit is non-trivial (session/identity switch within one SSE stream).
7. **`SubagentResultReducer` absent from contracts** despite plan references — needed for FORK/AS_TOOL result merge (Layer A), so resolve this in Layer A.

---

## 6. Recommendation

- **Re-scope Area A item 3**: ship **A-3a (FORK/TEAMMATE/AS_TOOL activation)** as the cheap, high-value next step — it can even bundle with the A-1/A-2 tool-registration work (all three share the "register builtin tools into the chat executor" gap).
- **Treat A-3b (HANDOFF) as a separate design spike**, not a wiring sprint, because of the loop.py change + multi-tenant allowlist + undefined contracts. Produce a design-note (8-point quality gate) before coding.
- This makes A-3 the first Area-A item where "wire it" is the wrong frame for part of the work.

**Dependency note**: Layer A shares the chat-executor tool-registration gap with A-1 Tier 1 (memory tools) — a single "register builtin tools (memory + subagent) into `make_default_executor`" change unlocks both. Worth bundling.

---

## 7. Definition-of-done signals (for the eventual sprint)

- **A-3a (FORK/TEAMMATE/AS_TOOL)**: a `real_llm` loop run spawns a FORK subagent and merges its `SubagentResult` via `SubagentResultReducer`; `SubagentSpawned`/`SubagentCompleted` SSE events observed; subagent failure does not crash the parent (fail_soft); budget enforced.
- **A-3b (HANDOFF)**: parser emits `OutputType.HANDOFF` from a registered handoff tool; loop resolves a registry target within the tenant allowlist; `Checkpointer.snapshot()` runs before parent exit; target agent boots and streams events; cross-tenant handoff is impossible (test); a max-chain-depth guard prevents infinite handoff; `HandoffResult`/`AgentSpec` contracts defined; handoff tool `risk_level`/`hitl_policy` assigned.

---

## 8. Method note

Synthesized from a 2-agent parallel read-only audit (current-code-ground-truth + planning-target-spec) building on the existing `cat11-handoff-scope-analysis-20260531.md`, on main `526be549` (Sprint 57.63 merged). Effort/tier framing are judgement estimates, not commitments.
