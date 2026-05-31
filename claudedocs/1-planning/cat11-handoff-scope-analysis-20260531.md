# Cat 11 Subagent HANDOFF — Scope Analysis

**Purpose**: Assess what it takes to make `OutputType.HANDOFF` actually spawn + route a subagent on the production chat path, vs the current stub. Feeds a go/no-go + sizing decision (recommend a dedicated future sprint).
**Category / Scope**: Cat 11 (Subagent Orchestration); analysis only (no code)
**Created**: 2026-05-31
**Status**: Active (decision input)
**Source**: `claudedocs/5-status/breadth-probe-20260531.md` §3 + §4.2 item 6; codebase investigation 2026-05-31

> **Modification History**
> - 2026-05-31: Initial creation — Cat 11 HANDOFF scope from chat-path wiring investigation.

---

## 1. Current state (line-anchored)

- **4 modes** (`subagent/_abc.py:8-9`, `SubagentMode` enum): **FORK** (parallel), **TEAMMATE** (mailbox), **HANDOFF** (transfer control), **AS_TOOL** (LLM calls subagent as a tool). Worktree mode intentionally omitted (`_abc.py:11-12`).
- **HANDOFF stub in the loop** — `loop.py:1051-1058`: `if output_type == OutputType.HANDOFF:` → yields `LoopCompleted(stop_reason=TerminationReason.HANDOFF_NOT_IMPLEMENTED.value)` and returns. The loop never constructs or calls any dispatcher; the enum is recognized but terminates.
- **Already built** (`backend/src/agent_harness/subagent/`): `DefaultSubagentDispatcher` (`dispatcher.py:91`, `__init__(*, chat_client, mailbox=None, event_emitter=None)`) fully implements all 4 modes — `spawn()` (FORK/TEAMMATE), `wait_for()`, `handoff()`, `as_tool_factory()`. Mode executors: `modes/{fork,teammate,handoff,as_tool}.py`. Plus `mailbox.py` (`MailboxStore`), `budget.py` (`BudgetEnforcer`), `tools.py`, `exceptions.py`. **SSE events exist**: `SubagentSpawned` + `SubagentCompleted` (`dispatcher.py:183-243`; Sprint 57.12 closed AD-Cat11-SSEEvents). API surface: `backend/src/api/v1/subagents.py`.
- **The handoff executor is hollow**: `HandoffExecutor.execute(*, target_agent, context, trace_context)` (`modes/handoff.py`) validates a non-empty `target_agent` and returns `uuid4()` — i.e. it allocates a new `session_id` ONLY; it does NOT boot the target session. The actual "run the new session under `target_agent` with `context`" is explicitly delegated to the platform / chat-router layer (`handoff.py:9-12,52-56`) and **does not exist yet**.

---

## 2. Gap = two layers

### Layer A — Loop wiring (small, ~0.5 day)
1. Add a `subagent_dispatcher` keyword param to `AgentLoopImpl.__init__` (currently absent).
2. Construct `DefaultSubagentDispatcher(chat_client=..., event_emitter=...)` in `build_real_llm_handler` and inject it.
3. Replace the `loop.py:1051-1058` terminate-stub with a call to `dispatcher.handoff(...)`.
4. Extract `target_agent` from the parsed output (no extraction today).

### Layer B — Real handoff execution (large, multi-day; a genuine feature gap, not wiring)
- **Agent/persona registry + target resolution**: what agents/personas can be handed off to? (relates to the Phase 46 expert-registry worktree `feature/phase-46-agent-expert-registry`). Resolve `target_agent` → its system prompt / tools / model.
- **Boot the target session**: construct a new `AgentLoopImpl` for the target with its config and the handoff `context`, then stream its events into the SAME SSE response (mid-stream control transfer). This is exactly what `HandoffExecutor` delegates upward and which is unimplemented.
- **Tenant boundary / allowlist enforcement**: which targets a tenant may hand off to (deferred per `handoff.py:14-17`).
- **Semantics design**: does control transfer mid-response (target continues the turn) or is HANDOFF a routing decision returned to the client? Affects SSE event design + verification/HITL interaction.

---

## 3. Assessment

HANDOFF is **not** a "inject-a-dependency-and-it-works" activation like Cat 4/7/8. It is a small loop-wiring step (Layer A) plus a substantial platform feature (Layer B) that the codebase explicitly left unbuilt. The other three modes (FORK / TEAMMATE / AS_TOOL) reach the loop via tool auto-registration (`subagent/tools.py`); only the `OutputType.HANDOFF` branch is stubbed.

17.md §2.1 Contract: `SubagentDispatcher` L140 (ABC exists; the gap is the platform-side session-boot, not the contract).

---

## 4. Recommendation

1. **Do NOT bundle HANDOFF into the Cat 4/7/8/10 activation sprint (57.63)** — different shape (real feature vs wiring) and a likely dependency on an agent/persona registry.
2. Choose one:
   - **(A)** Schedule a dedicated **"Cat 11 HANDOFF real ship"** sprint AFTER 57.63: Layer A wiring + Layer B session-boot + target registry + tenant allowlist + SSE/HITL/verification interaction design. Estimate: multi-day; needs a design note (per doc-rolling discipline) extracted from a thin spike (e.g. handoff between two fixed personas within one tenant).
   - **(B)** Explicitly **document HANDOFF as deferred** and correct any "Cat 11 全 Level 4" headline to reflect that the `OutputType.HANDOFF` path is a stub (FORK/TEAMMATE/AS_TOOL usable via tools; HANDOFF not wired).
3. Either way, update the "11+1 全 Level 4" claim wording for Cat 11 to distinguish "primitives built + 3 modes via tools" from "HANDOFF OutputType branch = stub".

---

## 5. References

- Stub: `backend/src/agent_harness/orchestrator_loop/loop.py:1051-1058`
- Dispatcher: `backend/src/agent_harness/subagent/dispatcher.py:91` (+ `modes/handoff.py`, `mailbox.py`, `budget.py`, `tools.py`)
- SSE: `dispatcher.py:183-243` (`SubagentSpawned` / `SubagentCompleted`)
- API: `backend/src/api/v1/subagents.py`
- Spec: `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` §Cat 11; `17-cross-category-interfaces.md` §2.1 (SubagentDispatcher L140)
- Breadth probe: `claudedocs/5-status/breadth-probe-20260531.md` §3 + §4.2
