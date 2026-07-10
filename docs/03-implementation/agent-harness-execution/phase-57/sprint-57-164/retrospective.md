# Sprint 57.164 Retrospective — Tool-error taxonomy surfaced in chat-v2 UI

**Closed**: 2026-07-10 · **Branch**: `feature/sprint-57-164-tool-taxonomy-ui` · **CHANGE-131** · NO design note

## Q1 — What shipped

Closes the Tool-range carryover **③3 `AD-Tool-Error-Taxonomy-UI`** — the `error_taxonomy` a failed tool carries (57.144) now surfaces as a typed-diagnosis chip on the chat-v2 ToolBlock. Three coupled parts:
- **Option B decouple** (user pick): `classify_tool_error` runs on EVERY failure (executor `_build_failure` + rare `loop.py:3068`); the `CHAT_TOOL_ERROR_REFLECTION` lever gates ONLY the LLM `content` reflection → taxonomy visible by default, agent behavior byte-identical.
- **Wire** (additive field on the existing `tool_call_result`, count 26): `ToolCallFailed += error_taxonomy` → loop 2 emits → sse.py both branches → wire schema → codegen regen → FE `ToolBlock` `.badge danger` chip.
- **Reachability fix** (drive-through-discovered, user pick Option a): emit `ToolCallFailed(+error_taxonomy)` before `LoopTerminated` at BOTH terminate sites (`loop.py:3113` dominant / `:3028` rare) so a Cat-8 FATAL tool failure ALSO surfaces the chip (it previously only yielded `loop_terminated`).

**Drive-through PASS** real Azure gpt-5.2: `get incident INC-99999` → mock 404 → ToolBlock renders **`failed_api`** chip + real 404 output + `terminated` badge.

## Q2 — Estimate accuracy / calibration

- Scope class **`frontend-feature-with-event-wire-addition` 0.55** (3-pt validated ~1.07; additive field on an existing event + codegen + FE store-capture + render + parity).
- **Agent-delegated: no** (parent-direct — the Option B decouple, the drive-through reachability judgement, and the loop.py terminate-path extension all needed the parent). `agent_factor` 1.0 → 3-segment.
- Bottom-up ~8.25 hr → class-calibrated commit ~4.5 hr (mult 0.55). **Actual ~6.5-7 hr equiv → ratio ~1.4-1.55, OVER band.** The PLANNED scope (decouple + wire + FE + tests) landed ~on-budget; the over-run is entirely the **drive-through-discovered mid-sprint scope expansion** — the reachability finding (3 real-Azure trigger attempts + the `loop.py:3101-3122` terminate-before-emit root-cause read) + the loop.py 2-site extension + a clean restart + re-login + re-drive (~2-3 hr). This is the exact upper-edge variance the plan §7 flagged ("expect the UPPER edge; if > 1.20 note a re-point"), amplified by a genuine discovered-necessity extension, NOT a mis-estimate of the planned scope. **KEEP 0.55** (single over-point; the 3-pt-validated class history holds; the cause is a mid-sprint expansion, not a class recalibration signal). If a 2nd `frontend-feature-with-event-wire-addition` sprint with a mandatory drive-through runs > 1.20, propose a `-with-drivethrough-trigger-hunt` sub-class ~0.75 (mirrors 57.130 `chatv2-fatal-terminate-wire-surface` at ~1.29).

## Q3 — What went well / key lesson

- **The drive-through did EXACTLY its job** — it caught that the chip was WIRED (all gates green) but NOT reachable on the live 主流量 (tool failures `loop_terminated` before the `ToolCallFailed` emit). Gate-green + curl would have shipped a near-Potemkin surface; the real UI + real Azure walk exposed it. This is the canonical Drive-Through-Acceptance win.
- The fix that resulted (emit `ToolCallFailed` before terminate) makes ③3 actually DELIVER its user-facing goal AND is a genuine UX improvement independent of the chip (a terminated tool failure now shows its real error + taxonomy, not just "terminated: fatal_exception").
- Honest escalation: surfaced the reachability finding + two paths to the user rather than silently shipping gate-only OR silently expanding scope.

## Q4 — What to improve next

- **Day-0 could have caught this pre-code.** For a "surface event X in the UI" sprint, Day-0 Prong-2 should verify event X is actually EMITTED on the 主流量 for the trigger case — the frozen-template drift row `AD-Day0-Codegen-Existing-Shape-Capture` / the "no-live-producer" check (`for fill/wrap/instrument every X, grep that each X has a live producer`). I verified the wire PATH but not the `loop.py:3101-3122` terminate-BEFORE-emit interaction — a targeted read of the tool-failure→terminate flow at Day-0 would have surfaced the reachability gap before the 3 Azure trigger attempts. Lesson recorded for the next event-surface sprint.
- The drive-through trigger hunt cost 3 Azure turns (close→HITL detour, 404→FATAL, schema→FATAL) before the reachability root cause was clear. A Day-0 `curl` of the mock 404 + a read of the FATAL-classification path would have front-loaded it.

## Q5 — Anti-pattern self-check

- AP-2 (side-track): the loop.py emit + FE chip are on the 主流量 (drive-through proves reachability) — ✅
- AP-4 (Potemkin): the chip is now genuinely reachable + renders real data (NOT a dead/empty label) — the whole point of the drive-through was to falsify this — ✅
- AP-6 (speculative abstraction): none (reuses the existing `.badge` primitive + `tool_call_result` type) — ✅
- AP-8 (PromptBuilder): N/A (no prompt change) — ✅
- AP-10 (mock/real divergence): the drive-through ran on real Azure + real mock 404, not a stub — ✅
- AP-11 (version suffix): none — ✅
- v2 lints 11/11.

## Q6 — Carryover

- **③2 `AD-Tool-Description-AutoFix`** — the lint `--fix` mode (LLM-assisted draft generation) → Sprint 57.165 (user-confirmed order).
- **NEW `AD-Tool-Taxonomy-HumanLabel`** — the chip shows the raw value (`failed_api`); a prettier human label ("External/API error") is a follow-on polish.
- **NEW `AD-RequestApproval-Placeholder-Deprecated`** (drive-through-surfaced, pre-existing) — the `request_approval` tool returns a DEPRECATED placeholder (`"bind HITLManager via make_request_approval_handler() for real persistence"`) so an approved close-incident doesn't actually execute; the real HITL persistence isn't wired on that tool. Not a 57.164 regression; log for a Cat 9 slice.
- **NEW `AD-Tool-Failure-Terminate-vs-Recoverable-Policy`** — on the live chat, the natural tool failures (httpx 4xx, schema, connection-exhausted) all Cat-8-terminate; whether a business-tool 404 SHOULD terminate the whole agent run (vs be LLM-recoverable so the agent can adjust) is a Cat 8 policy question worth revisiting.

## Q7 — Gate summary

mypy `src` 400/0 · run_all 11/11 · black/isort/flake8 clean · backend pytest **3231 passed, 5 skipped** (+1) · Vitest **933** (+3) · `npm run lint && npm run build` clean · mockup **51** (byte-identical) · **Drive-through PASS** (real Azure, `failed_api` chip on a live 404). NO migration / NO new wire event type / NO new CSS.
