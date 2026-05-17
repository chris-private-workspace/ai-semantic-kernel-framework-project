# DRIFT-REPORT-PHASE1 — chat-v2 vs mockup `page-chat.jsx`

**Sprint**: 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1
**Created**: 2026-05-17 (Day 0)
**Last Updated**: 2026-05-17 (Day 0)
**Scope**: Catalogue all delta between mockup `reference/design-mockups/page-chat.jsx` (533L) and current `frontend/src/features/chat_v2/` (9 files), classified by Phase-1 ship / Phase-2+ defer.

---

## Phase-1 Ship (this sprint)

| # | Mockup feature | Current baseline | Phase-1 action |
|---|---------------|------------------|----------------|
| P1-1 | Turn `{ role, at, id, stopReason, duration, blocks: Block[] }` data shape | `Message = user \| assistant` flat | REWRITE types.ts (Day 1) |
| P1-2 | 4 Block types (thinking / tool / verification / subagent_fork) | thinking + flat toolCalls; verification + subagent SSE → rawEvents (no UI) | NEW 4 block components (Day 2) |
| P1-3 | TurnList role dispatch (UserTurn / AgentTurn / HITLTurn) | MessageList flat | NEW TurnList + 3 Turn role components (Day 2) |
| P1-4 | SessionList sidebar (6 sessions w/ DomainDot + status + agent + turns + time) | None | NEW SessionList + fixture + demo banner (Day 3) |
| P1-5 | 3-column collapsible ChatLayout (sessions / stream / inspector) | 2-column | REWRITE ChatLayout 3-col (Day 3) |
| P1-6 | ChatInspector 4-tab frame | None | NEW ChatInspector tab frame (Day 4) |
| P1-7 | InspectorTurn populated (KV + EventLine list + 2 buttons) | None | NEW InspectorTurn (Day 4) |
| P1-8 | Composer skeleton (textarea + Send + 3 coming-soon) | InputBar (preserve state machine) | NEW Composer + InputBar shim (Day 4) |
| P1-9 | ApprovalCard visual rewrite (severity + payload + rationale; 2-action preserve) | Basic 2-action card | REWRITE in-place (Day 2) |

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
| Full page | `screenshots/mockup-chat-v2.png` | `screenshots/prod-chat-v2-pre.png` (Day 0 baseline) | (Day 0) | _pending_ |
| Turn renderer | (Day 2) | (Day 2) | (Day 2) | _pending_ |
| 4 blocks | (Day 2) | (Day 2) | (Day 2) | _pending_ |
| SessionList sidebar | (Day 3) | (Day 3) | (Day 3) | _pending_ |
| Inspector Turn tab | (Day 4) | (Day 4) | (Day 4) | _pending_ |

---

## Modification History

- 2026-05-17: Initial creation (Sprint 57.21 Day 0)
