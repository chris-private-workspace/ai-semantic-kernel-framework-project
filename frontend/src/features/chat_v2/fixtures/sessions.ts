/**
 * File: frontend/src/features/chat_v2/fixtures/sessions.ts
 * Purpose: 6-session fixture for SessionList sidebar (Sprint 57.21 Day 3 §3.1).
 * Category: Frontend / chat_v2 / fixtures
 * Scope: Phase 57.21 Day 3 §3.1 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Verbatim port of mockup `SESSIONS` array (L5-12 of page-chat.jsx) to drive
 *   the SessionList sidebar before backend wire ships. Backend list endpoint
 *   pending Sprint 57.22+ (AD-ChatV2-SessionList-Backend); session_id selection
 *   does NOT yet rebuild a live conversation stream — only updates
 *   chatStore.activeSessionId for highlight.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 3 §3.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L5-12 (SESSIONS array source)
 *   - ../types.ts (Session type)
 *   - ../components/SessionList.tsx (consumer)
 */

import type { Session } from "../types";

export const FIXTURE_SESSIONS: Session[] = [
  {
    id: "sess_4tk2p",
    title: "payment-gateway 5xx spike",
    agent: "incident-responder",
    turns: 17,
    status: "running",
    time: "now",
    domain: "incident",
  },
  {
    id: "sess_91kxu",
    title: "Q4 compliance audit — PCI scope",
    agent: "compliance-auditor",
    turns: 42,
    status: "hitl",
    time: "8m ago",
    domain: "audit",
  },
  {
    id: "sess_2afpw",
    title: "Nightly patrol — APAC clusters",
    agent: "patrol-runner",
    turns: 28,
    status: "done",
    time: "1h ago",
    domain: "patrol",
  },
  {
    id: "sess_88vqc",
    title: "RCA: cache eviction storm 2026-05-12",
    agent: "rca-bot",
    turns: 64,
    status: "done",
    time: "yesterday",
    domain: "rca",
  },
  {
    id: "sess_kpw01",
    title: "Change request CHG-4821 review",
    agent: "change-reviewer",
    turns: 9,
    status: "done",
    time: "yesterday",
    domain: "incident",
  },
  {
    id: "sess_qqx88",
    title: "Anomaly: tenant_3kp9 token spike",
    agent: "compliance-auditor",
    turns: 12,
    status: "done",
    time: "2d ago",
    domain: "audit",
  },
];
