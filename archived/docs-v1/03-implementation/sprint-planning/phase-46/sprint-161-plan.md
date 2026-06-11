# Sprint 161: Frontend Expert Visualization

## Phase 46: Agent Expert Registry
**Sprint**: 161
**Story Points**: 8
**Dependencies**: Sprint 160 (Domain Tools) ✅

---

## User Stories

### U1: Domain Badge on AgentCard
**作為**使用者，**我希望**在 Agent Team panel 的 AgentCard 上看到 domain badge（如 network、database），**以便**快速識別每個專家的專業領域。

**Acceptance Criteria**:
- AgentCard 顯示 domain badge（含顏色和圖示）
- Domain badge 與現有 role/type badge 並列
- 支援 7 個 domain: network, database, application, security, cloud, general, custom

### U2: Expert Info in Detail Drawer
**作為**使用者，**我希望**在 AgentDetailDrawer 中看到專家的 capabilities 和 domain 資訊，**以便**了解專家的能力範圍。

**Acceptance Criteria**:
- AgentDetailHeader 顯示 domain badge
- Detail drawer 顯示 capabilities chips
- 從 SSE 事件的 metadata 取得 expert 資訊

---

## Technical Specification

### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/unified-chat/agent-team/ExpertBadges.tsx` | Domain badge + capabilities chips component |

### Files to Modify

| File | Change |
|------|--------|
| `frontend/src/components/unified-chat/agent-team/types/index.ts` | Add domain, capabilities to UIAgentSummary |
| `frontend/src/components/unified-chat/agent-team/AgentCard.tsx` | Render domain badge |
| `frontend/src/components/unified-chat/agent-team/AgentDetailHeader.tsx` | Render domain + capabilities |
| `backend/src/integrations/swarm/worker_executor.py` | Include domain/capabilities in SSE events |

### Domain Badge Config

```typescript
const DOMAIN_CONFIG: Record<string, { label: string; icon: Icon; color: string }> = {
  network:     { label: '網路',   icon: Globe,      color: 'blue' },
  database:    { label: '資料庫', icon: Database,    color: 'purple' },
  application: { label: '應用層', icon: Code,        color: 'green' },
  security:    { label: '資安',   icon: Shield,      color: 'red' },
  cloud:       { label: '雲端',   icon: Cloud,       color: 'cyan' },
  general:     { label: '通用',   icon: HelpCircle,  color: 'gray' },
  custom:      { label: '自訂',   icon: Settings,    color: 'orange' },
};
```

### Type Extension

```typescript
interface UIAgentSummary {
  // existing fields...
  domain?: string;
  capabilities?: string[];
  expertDisplayName?: string;
}
```

---

## Test Plan

- Visual inspection: AgentCard shows domain badges
- Domain badge color matches config
- Detail drawer shows capabilities
- No regression on existing agent team functionality
