# DRIFT-REPORT-PHASE1 — chat-v2 vs mockup `page-chat.jsx`

**Sprint**: 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1
**Created**: 2026-05-17 (Day 0)
**Last Updated**: 2026-05-18 (Day 4 closeout)
**Scope**: Catalogue all delta between mockup `reference/design-mockups/page-chat.jsx` (533L) and current `frontend/src/features/chat_v2/` (9 files), classified by Phase-1 ship / Phase-2+ defer. Day 4 closeout: mark Phase-1 ship items as ✅ shipped with commit ref + fill verification verdicts + add 3 in-sprint reality-vs-paper fix section.

---

## Phase-1 Ship (this sprint)

| # | Mockup feature | Current baseline | Phase-1 action | Day | Commit | Status |
|---|---------------|------------------|----------------|-----|--------|--------|
| P1-1 | Turn `{ role, at, id, stopReason, duration, blocks: Block[] }` data shape | `Message = user \| assistant` flat | REWRITE types.ts | Day 1 | `7e236424` | ✅ shipped |
| P1-2 | 4 Block types (thinking / tool / verification / subagent_fork) | thinking + flat toolCalls; verification + subagent SSE → rawEvents (no UI) | NEW 4 block components | Day 2 | `199e1e4f` | ✅ shipped |
| P1-3 | TurnList role dispatch (UserTurn / AgentTurn / HITLTurn) | MessageList flat | NEW TurnList + 3 Turn role components | Day 2 | `199e1e4f` | ✅ shipped |
| P1-4 | SessionList sidebar (6 sessions w/ DomainDot + status + agent + turns + time) | None | NEW SessionList + fixture + demo banner | Day 3 | `5f069b5e` | ✅ shipped |
| P1-5 | 3-column collapsible ChatLayout (sessions / stream / inspector) | 2-column | REWRITE ChatLayout 3-col | Day 3 | `5f069b5e` | ✅ shipped |
| P1-6 | ChatInspector 4-tab frame | None | NEW ChatInspector tab frame | Day 4 | `3c70e02e` | ✅ shipped |
| P1-7 | InspectorTurn populated (KV + EventLine list + 2 buttons) | None | NEW InspectorTurn | Day 4 | `3c70e02e` | ✅ shipped |
| P1-8 | Composer skeleton (textarea + Send + 3 coming-soon) | InputBar (preserve state machine) | NEW Composer visual-only (Option C; NOT wired; InputBar untouched) | Day 4 | `3c70e02e` | ✅ shipped (visual-only) |
| P1-9 | ApprovalCard visual rewrite (severity + payload + rationale; 2-action preserve) | Basic 2-action card | REWRITE in-place | Day 2 | `199e1e4f` | ✅ shipped |

## Phase-2+ Defer (Sprint 57.22+ carryover)

| # | Mockup feature | Defer reason | Carryover AD |
|---|---------------|--------------|--------------|
| P2-1 | Memory block (READ/WRITE inline) | No Cat 3 SSE `memory_accessed` event yet | AD-ChatV2-Memory-Block-Phase2 |
| P2-2 | HITL 4-action (Approve with edits / Escalate to L2) | Backend `governanceService.decide` only supports 2 actions; needs APPROVED_WITH_EDITS variant + payload editor | AD-ChatV2-HITL-FourAction-Phase2 |
| P2-3 | HITL SLA countdown timer + audit_id footer enrichment | Backend `ApprovalRequestedEvent.data` lacks `sla_seconds` + `audit_id` payload | AD-ChatV2-HITL-FourAction-Phase2 (folded) |
| P2-4 | Composer attachments (drag-drop + file upload) | No backend attachment upload endpoint | AD-ChatV2-Composer-Richness-Phase2 |
| P2-5 | Composer Tools(24) menu | No tool registry list endpoint surface | AD-ChatV2-Composer-Richness-Phase2 (folded) |
| P2-6 | Composer Memory scope filter | No memory scope selector backend | AD-ChatV2-Composer-Richness-Phase2 (folded) |
| P2-7 | Inspector Trace tab (Cat 12 OTel spans waterfall) | Cat 12 OTel spans-per-session list endpoint missing | AD-ChatV2-Inspector-Trace-Phase2 |
| P2-8 | Inspector Memory tab (Cat 3 memory ops list) | Cat 3 memory ops-per-session list endpoint missing | AD-ChatV2-Inspector-Memory-Phase2 |
| P2-9 | Inspector Subagent tree tab (Cat 11 live feed) | Cat 11 subagent live-tree-per-session endpoint missing | AD-ChatV2-Inspector-SubagentTree-Phase2 |
| P2-10 | SessionList backend wire (real session list) | No `GET /api/v1/sessions` list endpoint | AD-ChatV2-SessionList-Backend |
| P2-11 | Inspector Turn tab `trace_id` + `span_id` field source | SSE doesn't emit trace_id; need Cat 12 enrichment | AD-Cat12-SSE-Trace-Id-Phase2 (potential) |
| P2-12 | ChatHeader top toolbar (title + agent + model + provider-neutral + N turns + streaming dot + Loop/Audit buttons) | Sprint 57.20 NEW Topbar.tsx covers global topbar; chat-v2 page-level header out of Phase-1 scope | — (covered by Sprint 57.20 Topbar; chat-v2 keeps existing page header) |

---

## Phase-1 Out-of-Scope (explicit; not deferred, just not Phase-1)

- Inspector Trace / Memory / Subagent tree visual prototypes (coming-soon empty state only)
- Composer richness UI prototyping (3 disabled buttons with tooltip only)
- Mockup `domain` color palette in DomainDot (✅ implemented Day 3 fixture per mockup L154 — `incident: danger / audit: memory / patrol: tool / rca: thinking`)

---

## Verification

| Component | Mockup screenshot | Production screenshot | Pair-verify date | Verdict |
|-----------|-------------------|----------------------|------------------|---------|
| Full page | `screenshots/mockup-chat-v2.png` | `screenshots/prod-chat-v2-pre.png` (Day 0 baseline) + `screenshots/prod-chat-v2-day4-post-fix.png` (Day 4 post D-DAY4-6/7/8) | Day 0 / Day 4 | ✅ structural parity (Turn block model + SessionList + 3-col shell + Inspector 4-tab); 🚧 cosmetic Card visual polish folded into AD-Mockup-Direct-Port-Round-2 |
| Turn renderer | mockup `page-chat.jsx` L294-352 (TurnList + 3 Turn role components) | Day 2 `screenshots/prod-turn-list-day2.png` | Day 2 | ✅ role dispatch matches (UserTurn / AgentTurn / HITLTurn); D-DAY3-3 surgical fix preserved approval-card.spec.ts contract via outer wrapper role+aria-label |
| 4 blocks | mockup L168-292 (4 Block type renderers) | Day 2 `screenshots/prod-blocks-day2.png` | Day 2 | ✅ thinking/tool/verification/subagent_fork render parity; 🚧 memory Block deferred → AD-ChatV2-Memory-Block-Phase2 |
| SessionList sidebar | mockup L73-91 + L138-166 (sessions sidebar w/ DomainDot) | Day 3 `screenshots/prod-session-list-day3.png` | Day 3 | ✅ visual parity (6 fixtures); 🚧 backend wire deferred → AD-ChatV2-SessionList-Backend |
| Inspector Turn tab | mockup L376-471 (InspectorTurn KV + EventLine + 2 buttons) | Day 4 `screenshots/prod-inspector-day4.png` | Day 4 | ✅ Turn detail tab populated (KV + Block sequence); Trace/Memory/SubagentTree tabs = ComingSoonInspectorTab placeholders → 3 NEW Phase-2 ADs |
| Shell layout (3-col edge-to-edge) | mockup `styles.css §669-678 chat-shell` 240/minmax(480,1fr)/320 | Day 4 `screenshots/prod-chat-v2-day4-post-fix.png` (post D-DAY4-7 fullBleed + mockup-exact widths) | Day 4 | ✅ Playwright MCP runtime verify chat-shell rect x=240 y=48 width=1200 height=852 right=1440 bottom=900 edge-to-edge |
| Dark theme + Geist font | mockup `index.html class="dark"` + `font-family: Geist, ...` | Day 4 post D-DAY4-6 + D-DAY4-8 | Day 4 | ✅ `html.className === "dark"` + `bodyBg = rgb(2,8,23)` + `document.fonts.check('14px "Geist"') === true` |

---

## In-Sprint Reality-vs-Paper Fixes (3 D-DAY4 findings; honest close NOT pushed to Phase-2)

Sprint 57.20 paper layer specified shell + theme + font but runtime layer silent-failed on 3 dimensions. Surfaced during Sprint 57.21 Day 4 user-driven visual review. Honest close in Sprint 57.21 NOT deferred:

| ID | Symptom | Root cause | Sprint 57.20 paper claim | Fix commit | Files |
|----|---------|-----------|------------------------|-----------|-------|
| **D-DAY4-6** | Light theme rendered despite `index.html class="dark"` | ThemeProvider mount effect `resolveInitialTheme()` defaulted to `light` via matchMedia OS-preference path → mount-time `document.documentElement.classList.remove("dark")` stripped `index.html` initial dark class | "Sprint 57.20 US-B3 theme/density mechanism: html root receives `[data-variant="linear"] [data-density="default"] class="dark"` defaults set in main.tsx" | `d5a86f09` | `ThemeProvider.tsx` resolveInitialTheme() `light`→`dark` default + drop matchMedia OS-preference path; `AuthShell.test.tsx` ThemeProvider toggle test 倒置 |
| **D-DAY4-7** | chat-v2 page padding-gap not full-screen edge-to-edge | AppShellV2 `<main p-6>` 24px inset wrapped chat-shell; appropriate for dashboards (OverviewPage / Cost Dashboard / Tenant Settings) but mockup `chat-shell` expects full-bleed | (no paper claim — Sprint 57.20 shell rewrite assumed all pages inset) | `ca3fe39d` | `AppShellV2.tsx` NEW `fullBleed?: boolean` opt-in prop + chat-v2 `<AppShellV2 fullBleed>` declaration + ChatLayout `h-full` instead of `calc(100vh - 6.5rem)` + grid-cols mockup-exact `240px/minmax(480px,1fr)/320px` per `styles.css §669-678` |
| **D-DAY4-8** | Windows browser fell through to Segoe UI; Geist font not rendered | Sprint 57.20 `index.css body` declared `font-family: Geist, Noto Sans TC, ui-sans-serif, ...` but 0 webfont bundled (deferred to Phase 58+ AD-Geist-Font-Asset-Bundling carryover); Windows has no Geist installed → cascade fall-through | "Sprint 57.20 Day 1 B1e-f theme + font wire (... Geist/Noto Sans TC body wire via `@layer base body { font-family }`)" — paper declared font-family but did not bundle webfont | `ca3fe39d` | `npm install @fontsource/{geist-sans,geist-mono,noto-sans-tc}@5.1.0` + 9 NEW imports in `main.tsx` (Geist 400/500/600/700 + Geist Mono 400 + Noto Sans TC 400/500/600/700) + remove Google Fonts CDN @import from `index.css` |

**Pattern**: All 3 = Sprint 57.20 paper-vs-runtime gap (Sprint 57.5 Reality Check "code 95% / runtime 40%" extended to shell/theme/font layer). User-driven visual review surfaced; in-sprint honest close prevented Phase-2 carryover bloat.

**Closes**: AD-Geist-Font-Asset-Bundling (Sprint 57.20 carryover) early in Sprint 57.21 Day 4.

---

## Phase-1 Closeout Summary

**Quality gates final** (Day 4 EOD):
- tsc: 0 errors
- Vitest: **348/348 PASS** (Sprint 57.20 baseline 277 + 71 NEW; 0 regression)
- Lint: silent (--max-warnings 0)
- Build: 2.94s
- Main bundle: 320.76→**321.92 kB** (+1.16 kB; within +30 kB target; Inspector + Composer tree-shake absorbed by Tabs primitive + lucide-react chunks pre-loaded)
- Anti-Pattern: 11/11 PASS
- Backend changes: 0
- LLM SDK leak: 0
- i18n drift: 0 (24 NEW keys symmetric en+zh-TW)

**Behavioral preservation 100%**:
- 14 SSE events preserved (TurnStarted / ThinkingTextDelta / ToolCallStarted / ToolCallResultReceived / ApprovalRequested / ApprovalReceived / etc.)
- HITL approval workflow (governanceService.decide + optimistic store update + SSE ApprovalReceived overwrite) untouched
- InputBar.tsx 5-state pill + send/cancel + 14 SSE handling preserved (Composer Option C visual-only NOT wired)
- chatStore.mergeEvent dual-emit (legacy slices + Turn blocks) for backwards compatibility during Phase-1+2 transition

**Karpathy §3 orphan cleanup**:
- DELETE MessageList.tsx + ToolCallCard.tsx + _mockup-source.jsx.bak (3 files; ~200L 舊 ship code; 0 production importers post-Day-3 TurnList swap; 0 Vitest specs)

**D-DAY3-3 surgical e2e contract preservation**: 2-line edit `turns/HITLTurn.tsx` outer wrapper (role="region" + aria-label="HITL approval") preserves `approval-card.spec.ts` `getByRole` selector after MessageList→TurnList swap.

**Calibration** (closes Sprint 57.21 retro Q2):
- Class: `frontend-mockup-direct-port` 0.55 (HYBRID weighted blend)
- 2nd application ratio actual/committed = **1.20** ✅ TOP of [0.85, 1.20] band
- Validates Sprint 57.20 retro footer prediction: "if 57.21+ hits AD-ChatV2-Full-Mockup-Fidelity with genuine structural rewrite → ratio swings back into band"
- Bimodal pattern confirmed: 57.20 token-sweep ~0.50 below band / 57.21 structural ~1.20 top of band
- 2-data-point mean 0.85 at lower band edge
- KEEP 0.55 baseline per `When to adjust` 3-sprint window rule
- If 3rd app continues bimodal → AD-Sprint-Plan-NEW propose split into `-token-sweep` (0.40) vs `-structural` (0.85)

**Phase-2 Carryover** (10 NEW ADs; see SITUATION §第八部分 §Phase 57.21 carryover):
1. 🔴 **AD-ChatV2-Full-Mockup-Fidelity Phase-2** (multi-sprint epic continuation)
2. **AD-ChatV2-Memory-Block-Phase2** (5th Block type)
3. **AD-ChatV2-HITL-FourAction-Phase2** (Approve-with-edits / Escalate-to-L2)
4. **AD-ChatV2-Composer-Richness-Phase2** (attach / memory hint / tool select wire)
5. **AD-ChatV2-Composer-Wire-Phase2** (wire vs revert vs hybrid decision)
6. **AD-ChatV2-Inspector-Trace-Phase2** (Cat 12 OTel spans)
7. **AD-ChatV2-Inspector-Memory-Phase2** (Cat 3 memory ops feed)
8. **AD-ChatV2-Inspector-SubagentTree-Phase2** (Cat 11 live feed)
9. **AD-ChatV2-SessionList-Backend** (Cat 1 GET /api/v1/sessions list)
10. **AD-Cat12-SSE-Trace-Id-Phase2** (trace_id propagation Turn → Inspector)

---

## Modification History

- 2026-05-18: Day 4 closeout — mark Phase-1 ship items ✅ + fill verification verdicts + add 3 in-sprint reality-vs-paper fix section (D-DAY4-6/7/8) + Phase-1 closeout summary + 10 Phase-2 carryover ADs
- 2026-05-17: Initial creation (Sprint 57.21 Day 0)
