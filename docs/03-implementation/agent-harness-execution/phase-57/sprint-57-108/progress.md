# Sprint 57.108 Progress — UX slice: chat-v2 HITL card real tool/reason + Inspector turn metadata wire

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-108-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-108-checklist.md)

---

## Day 0 — 2026-06-12 — Plan-vs-Repo verify + branch

Branch `feature/sprint-57-108-chatv2-hitl-inspector-wire` created from `main` `a42ed717`.

### Drift findings (three-prong; plan §8 cross-ref)

| ID | Finding | Implication |
|----|---------|-------------|
| D1 | `tokensIn` is ALREADY wired — `llm_request` handler (chatStore.ts:421-431) overwrites `tokensIn` from `ev.data.tokens_in` each call; `turn_start` creates a NEW AgentTurn per TAO turn → one LLM call per turn | Only `tokensOut` is actually missing. FE token capture uses **overwrite** (mirror the llm_request idiom), NOT the plan §3.3 "accumulate" assumption; llm_response additive pair still shipped (input actuals overwrite the pre-call estimate + output fills the gap) |
| D2 | Span linkage is EXPLICIT — spans carry `span_type: "TURN"` (`span_name="agent_loop.turn"`, loop.py:2173-2179; wire fields span_name/span_id/parent_span_id/span_type @ event_wire_schema.py:197-202) | `span_started` handler matches `span_type === "TURN"` → set active AgentTurn.spanId; no first-span-of-turn heuristic needed |
| D3 | NO `turn_end` event exists (wire has loop_start/turn_start/loop_end only); `AgentTurn.durationMs` is initialized null and NEVER set | Fold-in per plan §3.3 "wire if trivially broken": TURN `span_ended.duration_ms` → `durationMs` (same handler as the spanId linkage) |
| D4 | `stopReason` per turn is set only at `loop_end` for the LAST agent turn (chatStore.ts:519-530) | Semantically correct (intermediate TAO turns have no stop reason); no action |
| D5 | `HITLTurn.tsx` needs ZERO edits — renders `turn.tool` (:197-199), `rationale` gated `!== "—"` (:206-211), `payload` gated (:212); fully store-driven. `ApprovalCard.tsx` (legacy) renders risk-only header — never rendered tool | FE fix collapses to chatStore.ts ONLY; plan §4 file #8 becomes no-op; `approvals` dict extension dropped (nothing renders tool from it — YAGNI), so `types.ts` ApprovalEntry unchanged too |
| D6 | Verification escalate site reason IS in scope (`reason` local @ loop.py:1787, yield @ :1833) | All 5 sites pass a real `reason`; no `""` fallback needed |
| D7 | `ApprovalRequested(` constructors: ONLY the 5 loop yield sites + 3 test sites (test_sse.py:164/:176, test_event_wire_schema_parity.py:82), all keyword-style | Defaulted new fields are constructor-safe; no resume-replay / observer re-construction exists |
| D8 | Subagent relay does NOT carry ApprovalRequested (grep 0 in `agent_harness/subagent/`) | No relay change; child approvals out of scope by existing design |

### Prong results

- **Prong 1 (paths)**: all EDIT targets Glob-1 (`HITLTurn.tsx` actual path = `components/turns/HITLTurn.tsx`, not `components/` — minor path drift vs recon, catalogued); NO new files. ✅
- **Prong 2 (content)**: anchors verified per D1-D8; serializer insertion points confirmed (`sse.py` llm_response :158-176 after `cached_input_tokens` :174; approval :241-251). ✅
- **Prong 2.5 (FE tree)**: HITLTurn / InspectorTurn structurally untouched this sprint (store-driven); HITLTurn header documents styles-mockup.css classes — no shadcn residue introduced. Clean. ✅
- **Prong 3 (schema)**: N/A — no DB / no migration. ✅

### Go/no-go

**GO** — drift findings SHRINK scope (HITLTurn no-edit; tokens.in already wired; explicit TURN span match; durationMs bonus fold-in). Shift ≪20%.

---

## Day 1 — 2026-06-12 — Backend additive fields + wire + codegen (US-1 + US-3 backend)

- `ApprovalRequested` += `tool_name`/`reason` (events.py; defaulted, constructor-safe per D7); 5 loop.py yield sites pass `reason=` (tool site also `tool_name=tc.name`); wire + sse serializer pairs (`approval_requested` +2; `llm_response` +`input_tokens`/`output_tokens` — LLMResponded already carried them); codegen regen (both artifacts, same commit).
- Tests: 5 escalate-site assertions extended (tool=`sensitive_tool`+reason; 4 non-tool=None+reason) + test_sse defaults/tool-context/token-actuals (+2 net new tests); 0 deletions.
- Gates: mypy 0/359 · black/isort/flake8 0 (four-segment chain run — 57.107 isort lesson applied) · run_all 10/10 from repo root (count 24 unchanged; check_event_schema_sync green) · full pytest **2462+4skip (+2, 0 del)**.
- Actual ~1.5 hr (est ~2.5 hr bottom-up) — additive-field shape + D7 constructor safety made conversions thin.

---

## Day 2 — 2026-06-12 — FE store captures + Vitest (US-2 + US-3 FE)

- **D9 (new drift finding, Day-2)**: `SpanStarted(TURN)` is emitted BEFORE `TurnStarted` (loop.py :2173-2186 → :2188) — the plan's "link in span_started" would attach the span to the PREVIOUS turn. Inverted: `turn_start` links the newest RUNNING TURN span from the spans slice (it was just pushed). `durationMs` fills on `span_ended` TURN by spanId match (order-independent).
- chatStore.ts 4 captures: approval tool/rationale real (D5 — HITLTurn.tsx/ApprovalCard.tsx ZERO edits, store-driven; approvals-dict extension dropped, YAGNI) · turn_start traceId + spanId · llm_response token actuals overwrite-when->0 (D1 overwrite not accumulate; 0/absent keeps prior → honest "—" for old frames) · span_ended TURN → durationMs (D3 — no turn_end event exists).
- Type-contract ripple: `demoLoopEvents.ts` (/loop-debug fixture) gained the new required literals (same 57.66 precedent).
- Vitest +8 (mergeEvent 46→54); ChatInspector suite unchanged (component untouched; null-fallback test stays valid).
- Gates: lint 0 (non-silent) · build ✓ · Vitest **836 (+8, 0 del)** · mockup-fidelity 51==51 byte-identical.
- Actual ~1.5 hr (est ~2 hr bottom-up US-2 + ~1 hr of US-3 FE).

---

## Day 3 — 2026-06-12 — Full gates + drive-through (US-4) + CHANGE-075

### Gate sweep
mypy 0/359 · black/isort/flake8 0 · run_all 10/10 (count 24) · full pytest 2462+4skip (0 del) · FE lint 0 / build ✓ / Vitest 836 / mockup-fidelity 51==51 · `loop.py` diff = 5 yield kwargs + header (verified via `git diff main`) · wire schema diff additive-only.

### Drive-through (real UI :3007 + fresh no-reload backend PID 33124 + real Azure gpt-5.2; zero dev-login — founder@dt57105.test password-login, tenant `dt57105-rbac`)

Risk Class E clean restart: killed stale 57.107 backend PID 9680 (sole python on :8000, no orphan spawn workers per Win32_Process sweep) → fresh PID 33124 on 57.108 code, startup log clean.

| Leg | Intended | Observed | Verdict |
|-----|----------|----------|---------|
| A — HITL card real tool context (kind="tool") | risky sandbox ask → tool-escalate card shows REAL tool + reason | "run os.system via python_sandbox" → LLM first REFUSED (turn 2; verifier flagged "refuses or deflects" + coached) → retried with `subprocess.check_output` → RiskyActionDetector caught the detour (`risky_action: sandbox code matched '\bsubprocess\b'`) → card shows **tool: python_sandbox** + the real rationale (was `tool: —`/`rationale: —` pre-57.108) | ✅ PASS |
| A2 — approve resumes | Approve → pending tool execs → run continues | `Decision: APPROVED` on card → python_sandbox executed (real output: getpass `Chris` / `desktop-tj564jj\chris`) → turn 5 final answer + verification_passed 0.99 | ✅ PASS |
| B — non-tool fallback (kind="input") | input-phrase escalate → card tool falls back "—", reason real | message containing "approval required" → input pause BEFORE any LLM call → card shows **tool: —** (honest) + **Rationale: input matched escalation phrase: 'approval required'** | ✅ PASS (rejected to clean up — input-kind reject terminates) |
| C — Inspector turn metadata reality | trace_id / span_id / tokens / duration real; cost + thinking stay "—" | Turn pane: **tokens.in 2,301** (llm_response actuals OVERWROTE the llm_request estimate which streamed `tokens_in=0` — the D1 overwrite design proved live) · **tokens.out 75** · **trace_id 35f3bc98…** (matches span frames) · **span_id aac95c3a…** = exactly the turn-1 TURN span (D9 strategy correct) · duration "—" while awaiting_approval (TURN span not yet ended — honest), then **· 5.33s / · 6.45s** on completed turns (TURN span_ended fill, D3) · **cost — / tokens.thinking —** (by design) | ✅ PASS |

Screenshots ×3: `artifacts/dt57108-{A-hitl-card-real-tool, B-approved-run-continues, C-nontool-fallback-real-reason}.png` (never-commit).

Unplanned observations: (1) the model initially refusing + the in-loop verifier coaching it into a `subprocess` retry gave a LIVE proof that the deny-list's multi-pattern design catches paraphrased risk — the card's reason made that legible to the approver for the first time. (2) `llm_request` streams `tokens_in=0` on this adapter — pre-57.108 the Inspector tokens.in relied on it (would have shown 0/—); the response-actuals overwrite is what makes the field real.

### CHANGE-075
`claudedocs/4-changes/feature-changes/CHANGE-075-chatv2-hitl-card-inspector-metadata-wire.md` created. No design note (feature continuation — not a new-domain spike; §Step 5.5 NOT-apply branch).
