# Sprint 161 Checklist: Frontend Expert Visualization

## Type Extension
- [x] `types/index.ts` — add domain, capabilities, expertDisplayName to UIAgentSummary

## ExpertBadges Component
- [x] `ExpertBadges.tsx` — DOMAIN_CONFIG with label/icon/color for 7 domains
- [x] `ExpertBadges.tsx` — DomainBadge component
- [x] `ExpertBadges.tsx` — CapabilitiesChips component

## AgentCard Integration
- [x] `AgentCard.tsx` — import and render DomainBadge

## AgentDetailHeader Integration
- [x] `AgentDetailHeader.tsx` — render DomainBadge + CapabilitiesChips

## Backend SSE Enhancement
- [x] `worker_executor.py` — include domain/capabilities in SWARM_WORKER_START event

## Verification
- [x] TypeScript compiles without errors
- [x] No regression on existing agent team panel
- [x] Domain badges visible in AgentCard
- [x] Capabilities chips visible in detail drawer
