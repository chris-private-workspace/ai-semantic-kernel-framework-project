---
paths: frontend/**/*.{ts,tsx}
---

# React Frontend Rules

> Rules for TypeScript/React code in the frontend.

## Component Structure

```tsx
// 1. Imports
import { FC, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';

// 2. Types
interface MyComponentProps {
  title: string;
  onAction: () => void;
}

// 3. Component
export const MyComponent: FC<MyComponentProps> = ({ title, onAction }) => {
  // Hooks first
  const [state, setState] = useState('');
  const { data, isLoading } = useQuery({...});

  // Event handlers
  const handleClick = () => onAction();

  // Early returns for loading/error
  if (isLoading) return <Loading />;

  // Main render
  return (
    <div>
      <h1>{title}</h1>
      <Button onClick={handleClick}>Action</Button>
    </div>
  );
};
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `AgentCard.tsx` |
| Hooks | camelCase + use | `useAgents.ts` |
| Utils | camelCase | `formatDate.ts` |
| Types | PascalCase | `Agent`, `AgentProps` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |

## State Management

```tsx
// Zustand for global state
import { useAgentStore } from '@/store/agentStore';
const { agents, selectAgent } = useAgentStore();

// React Query for server state
const { data, isLoading } = useQuery({
  queryKey: ['agents'],
  queryFn: () => api.getAgents(),
});

// useState for local state
const [isOpen, setIsOpen] = useState(false);
```

## Styling

Styling follows the authoritative mockup-fidelity method in
[`frontend-mockup-fidelity.md`](./frontend-mockup-fidelity.md): mockup CSS classes
(from `frontend/src/styles-mockup.css`) are the **primary** styling mechanism; Tailwind
utilities are **secondary** (layout one-offs / a11y wrappers only, never to re-express
mockup styling); shadcn primitives are for interaction behavior only. Do NOT translate
mockup CSS into Tailwind. See that rule for the full 4-layer protocol + 7 鐵律.

## Prohibited

- ❌ `any` type (use proper types)
- ❌ `console.log` in production
- ❌ Inline styles (use mockup CSS classes / Tailwind per `frontend-mockup-fidelity.md`)
- ❌ Direct DOM manipulation
- ❌ Class components (use functional)

---

## Detailed Conventions

The rules above cover React / TypeScript / styling basics. For comprehensive
operational rules + visual style guide, see the dedicated frontend docs codified
in Sprint 57.10:

- **`frontend/CONVENTION.md`** — Page architecture pattern (auth gate + AppShellV2 + nested Routes), `features/<X>/` folder convention, routes.config.ts single-source registry, Zustand UI-only post-TanStack-migration pattern, TanStack Query `*_QUERY_KEY_BASE` single-source export, fetchWithAuth API service convention, **SSE event 3-edit audit checklist** (D-PRE-13 lesson — adding new SSE event requires types.ts LoopEvent union + KNOWN_LOOP_EVENT_TYPES set + chatStore.mergeEvent case branch), test convention with seedAuthJwt beforeEach + retryClicked flag pattern.

- **`frontend/STYLE.md`** — Tailwind utility-first rule, canonical color tokens table (token name + hex + Tailwind class), risk badge palette (LOW / MEDIUM / HIGH / CRITICAL canonical hex), typography (Inter sans + JetBrains Mono code; 5 size tokens), spacing convention (`p-4` / `gap-4` / `mb-4` baseline), loading skeleton pattern (5-row table / 3-card), empty state pattern, error retry UX with StrictMode-safe `retryClicked` flag.

These docs codify emergent patterns from Sprint 57.7 (IAM + frontend foundation),
Sprint 57.8 (AppShellV2 architecture + chat-v2 ship), Sprint 57.9 (governance ship +
TanStack 4-page migration), and Sprint 53.5 (governance backend + risk palette).

**When to update CONVENTION.md / STYLE.md**: pattern appears in ≥ 2 sprint examples
(avoids premature 1-data-point baseline per AD-Plan-3). Periodic re-audit per
AD-Convention-Drift-Audit-Cycle (Phase 58.x; every 4-6 sprints).
