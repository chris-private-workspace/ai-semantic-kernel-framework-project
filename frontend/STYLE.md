# Frontend Style Guide

> **Visual + UX rules** for V2 frontend. For convention rules (architecture / state /
> SSE / test patterns), see [`CONVENTION.md`](./CONVENTION.md).
> For React basic rules (ESLint / TypeScript / no inline styles), see
> [`.claude/rules/frontend-react.md`](../.claude/rules/frontend-react.md).
> For design philosophy + page roadmap, see
> [`docs/03-implementation/agent-harness-planning/16-frontend-design.md`](../docs/03-implementation/agent-harness-planning/16-frontend-design.md).

**Created**: 2026-05-09 (Sprint 57.10 codified from Sprint 53.5+57.7+57.8+57.9 emergent palette + UX patterns)
**Last Modified**: 2026-05-17
**Status**: Active

> **Modification History (newest-first)**
> - 2026-05-17: Sprint 57.19 — §2 indigo primary + accent (closes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap)
> - 2026-05-11: Sprint 57.16 — escape-hatch sub-§ no longer references ChatLayout (migrated; frontend/src now inline-style-clean) (AD-Inline-Style-Cleanup-Sweep-Round2)
> - 2026-05-11: Sprint 57.15 — §1 no-inline-style is now lint-enforced (`no-restricted-syntax`); add "Inline-style escape hatches" sub-section (AD-Inline-Style-Cleanup-Sweep)
> - 2026-05-09: Initial creation (Sprint 57.10 — closes style/UX drift identified by user 2026-05-09 reality check)

---

## Purpose

Frontend style + UX patterns historically drifted because Sprint 53.5 governance
shipped with inline styles + arbitrary hex values; Sprint 57.7 cost-dashboard ship
introduced Tailwind utility-first but reused 53.5's hex via `text-[#2e7d32]` arbitrary
value rather than canonical token. This doc codifies:
- **Tailwind utility-first rule** with shadcn primitives where available
- **Canonical color token table** (token name + hex + Tailwind class equivalents)
- **Risk badge palette** as a single-source enum table
- **Typography / spacing baselines**
- **Standard UX patterns** (loading skeleton / empty state / error retry)

Future components reference this doc for style decisions instead of grep-ing past
sprints for ad-hoc precedents.

---

## 1. Tailwind Utility-First

V2 frontend uses **Tailwind CSS utility-first** exclusively. shadcn/ui primitives are
available for common UI patterns.

### Rules

- ❌ **No inline styles** — the JSX `style=` prop (on DOM elements *and* components, whether the value is an inline literal, a variable, or a fn call) is **lint-enforced** by `no-restricted-syntax` in `eslint.config.js` (`error`, since Sprint 57.15 / AD-Inline-Style-Cleanup-Sweep). Use Tailwind utility classes; for the rare dynamic case see "Inline-style escape hatches" below.
- ❌ **No custom CSS files** except `index.css` (shadcn vars + global resets only)
- ❌ **No CSS-in-JS** libraries (styled-components / emotion forbidden)
- ✅ **shadcn primitives where available** (Button / Input / Dialog / Tabs / Dropdown / Tooltip)
- ✅ **Tailwind utility classes** for everything else
- ✅ **Arbitrary values `text-[#xxxxxx]` allowed only when no token exists** (prefer `text-success` over `text-[#10B981]`; arbitrary value should be exception, not default)

### Migration precedent (Sprint 57.9 US-2)

Sprint 57.9 migrated 3 governance components (ApprovalsPage / ApprovalList / DecisionModal)
from inline styles to Tailwind. Pattern:

❌ **Wrong** (Sprint 53.5 inline styles):
```tsx
const cardStyle = {
  padding: "1rem",
  border: "1px solid #ddd",
  borderRadius: "8px",
  backgroundColor: "#fafafa",
};

return <div style={cardStyle}>...</div>;
```

✅ **Right** (Sprint 57.9 Tailwind):
```tsx
return (
  <div className="rounded-lg border border-border bg-muted p-4">
    ...
  </div>
);
```

### Inline-style escape hatches (dynamic values)

The `no-restricted-syntax` guard is `error` — but a few values are genuinely runtime-computed (a progress bar's `width: ${pct}%`, a tree row's `marginLeft: depth*12px`). Three patterns, in order of preference:

1. **Finite class lookup** — if the value comes from a small enum, map it to literal Tailwind classes (the JIT only sees literal strings, so `ml-[${n}px]` does *not* work — a lookup array does):
   ```tsx
   const RISK_TEXT_CLASS = { LOW: "text-green-700", MEDIUM: "text-orange-600", HIGH: "text-orange-800", CRITICAL: "text-red-800" };
   const DEPTH_INDENT = ["ml-0", "ml-3", "ml-6", "ml-9", "ml-12", "ml-[60px]"];   // bounded depth
   <span className={cn("font-bold", RISK_TEXT_CLASS[risk] ?? "text-muted-foreground")}>{risk}</span>
   <li className={cn("space-y-1", DEPTH_INDENT[depth] ?? "ml-[60px]")} />
   ```
   (See `features/chat_v2/components/ApprovalCard.tsx` + `features/subagent/components/SubagentTree.tsx`.)
2. **CSS custom property + Tailwind arbitrary value** — for truly continuous values (a percentage bar width, a computed pixel offset). Still a `style=`, so it carries an `eslint-disable` with a reason, but it sets *only* the variable:
   ```tsx
   // eslint-disable-next-line no-restricted-syntax -- CSS var only, dynamic bar width
   <div style={{ "--bar-w": `${pct}%` } as React.CSSProperties} className="w-[var(--bar-w)] bg-success" />
   ```
3. **Last-resort inline `style=` with an `eslint-disable-next-line no-restricted-syntax -- <reason>`** — only when neither of the above fits. The reason must say *what's dynamic*.

For a whole legacy file that hasn't been migrated yet, a top-of-file `/* eslint-disable no-restricted-syntax -- <AD reference> */` keeps the `error`-level guard on for everything else. (No live examples remain after Sprint 57.16 — the entire `frontend/src` is inline-style-clean — but the pattern stays documented for future bulk migrations.)

---

## 2. Color Tokens

Canonical color tokens per `16-frontend-design.md §245-262` + tailwind.config.ts theme.

> **Sprint 57.19 update (2026-05-17)**: production `primary` brand color moved from dark-slate `hsl(222.2 47.4% 11.2%)` → indigo `hsl(234 89% 60%)` (light) / `hsl(234 84% 70%)` (dark), HSL approximation of mockup's canonical `oklch(0.62 0.16 250)` cool indigo (closes AD-Brand-Primary-Color-Decision). `--accent` + `--accent-foreground` NOW defined in `src/index.css` :root + .dark (closes AD-Accent-Token-Gap; Sidebar `bg-accent`/`text-accent-foreground` now resolve to real tokens). Contrast-ratio audit of components consuming new indigo + accent tokens still scheduled for Sprint 57.19+ ongoing ports (AD-Post-Hotfix-Token-Audit contrast portion).
>
> **Sprint 57.18 update (2026-05-16)**: 7 semantic tokens + 4 risk levels NOW defined in `tailwind.config.ts` + `src/index.css` :root + .dark (closes AD-Style-Token-Config-Audit token-coverage portion).

| Token | Hex (reference) | Tailwind class | Usage |
|-------|-----------------|----------------|-------|
| `primary` | `oklch(0.62 0.16 250)` (mockup canonical) ≈ `hsl(234 89% 60%)` light / `hsl(234 84% 70%)` dark | `text-primary` / `bg-primary` / `border-primary` | Main actions (submit / nav active); cool indigo brand (Sprint 57.19+) |
| `accent` | `hsl(234 89% 60%)` light / `hsl(234 84% 70%)` dark (same hue as primary, used with /opacity modifier per mockup) | `bg-accent` / `text-accent-foreground` | Hover / focus emphasis / Sidebar active highlight (Sprint 57.19+) |
| `success` | `#10B981` ≈ `hsl(150 60% 45%)` | `text-success` / `bg-success` / `border-success` | Verified / approved / passed |
| `warning` | `#F59E0B` ≈ `hsl(38 92% 50%)` | `text-warning` / `bg-warning` | HITL pending / attention / DRAFT badge |
| `danger` | `#EF4444` ≈ `hsl(0 84% 60%)` | `text-danger` / `bg-danger` | Errors / tripwire / blocked |
| `thinking` | `#8B5CF6` ≈ `hsl(270 75% 60%)` | `text-thinking` / `bg-thinking` | Thinking blocks (LLM reasoning) / PROP badge |
| `tool` | `#06B6D4` ≈ `hsl(188 70% 50%)` | `text-tool` / `bg-tool` | Tool call cards |
| `memory` | `#EC4899` ≈ `hsl(326 80% 60%)` | `text-memory` / `bg-memory` | Memory operations |
| `info` | `#3B82F6` ≈ `hsl(217 91% 60%)` | `text-info` / `bg-info` | Info banners / Priority badge (Sprint 57.18 NEW) |

### Risk severity tokens (Sprint 57.18 NEW)

4 risk levels per design/operator-portal/styles.css; used by ApprovalCard + risk badges:

| Token | Hex (light) | Hex (dark) | Tailwind class | Usage |
|-------|-------------|------------|----------------|-------|
| `risk-low` | ≈ `hsl(150 60% 45%)` | ≈ `hsl(150 50% 55%)` | `text-risk-low` / `bg-risk-low` | LOW severity HITL approvals |
| `risk-medium` | ≈ `hsl(38 92% 50%)` | ≈ `hsl(38 80% 60%)` | `text-risk-medium` / `bg-risk-medium` | MEDIUM severity |
| `risk-high` | ≈ `hsl(20 90% 55%)` | ≈ `hsl(20 80% 60%)` | `text-risk-high` / `bg-risk-high` | HIGH severity |
| `risk-critical` | `#B71C1C` ≈ `hsl(0 70% 40%)` | ≈ `hsl(0 60% 50%)` | `text-risk-critical` / `bg-risk-critical` | CRITICAL severity (matches approval-card.spec.ts sentinel `#b71c1c`) |

### shadcn semantic tokens (additionally)

shadcn theme provides semantic tokens used widely in components:

| Token | Tailwind class | Usage |
|-------|----------------|-------|
| `foreground` | `text-foreground` | Primary text |
| `muted-foreground` | `text-muted-foreground` | Secondary text / labels |
| `background` | `bg-background` | Page background |
| `muted` | `bg-muted` | Subtle background (cards / sections) |
| `border` | `border-border` | Default border color |

### Preferred over arbitrary values

```tsx
// ❌ Wrong (arbitrary hex; bypasses theme; harder to maintain)
<span className="text-[#10B981]">Approved</span>

// ✅ Right (token; auto-respects dark mode + theme overrides)
<span className="text-success">Approved</span>
```

### When arbitrary values are acceptable

- Risk badge palette has 4 specific hex values not in primary tokens (LOW / MED / HIGH / CRITICAL — see §3)
- One-off external brand colors (logos / partner integrations)
- Prototype / spike code (must convert to token before merge to main)

---

## 3. Risk Badge Palette

Canonical 4-level risk palette per Sprint 53.5 governance ship. Used by HITL approval
cards / verifier results / guardrail alerts / audit log severity.

| Risk Level | Hex | Tailwind class | shadcn equivalent | Usage |
|------------|-----|----------------|-------------------|-------|
| **LOW** | `#2e7d32` | `text-[#2e7d32]` OR `text-green-700` | — | Acceptable risk; auto-approve eligible |
| **MEDIUM** | `#ed6c02` | `text-[#ed6c02]` OR `text-orange-600` | — | HITL approval required |
| **HIGH** | `#d84315` | `text-[#d84315]` OR `text-orange-800` | — | Senior approver required |
| **CRITICAL** | `#b71c1c` | `text-[#b71c1c]` OR `text-red-800` | — | Blocked unless explicit override |

### Reference component

`features/chat_v2/components/ApprovalCard.tsx` (Sprint 53.5 → 57.9 Tailwind migration; canonical reference. Note: the legacy `features/governance/components/ApprovalCard.tsx` path documented in this section prior to Sprint 57.18 was stale — file never existed at that path. Fixed by `chore/closeout-57-18`.)
is the canonical risk badge implementation. New components consuming risk levels MUST
import the same hex values OR use the same Tailwind classes (NOT introduce new shades).

### Future codification candidate

Risk palette currently uses arbitrary hex values (Sprint 57.9 trade-off — keeping
exact 53.5 colors for visual continuity). Phase 58.x candidate: add `risk-low / risk-medium /
risk-high / risk-critical` to tailwind.config.ts theme so `text-risk-critical` becomes
the canonical class. Tracked as informal AD-RiskPaletteTokenization.

---

## 4. Typography

Per `16-frontend-design.md §264-276` + tailwind.config.ts theme.

### Font families

| Token | Family | Usage |
|-------|--------|-------|
| `font-sans` | `Inter, system-ui, sans-serif` | All UI text |
| `font-mono` | `JetBrains Mono, monospace` | Code blocks / JSON / hash values / session IDs |

### Size tokens

| Class | Size | Usage |
|-------|------|-------|
| `text-xs` | 0.75rem (12px) | Labels / metadata / tooltips / table cell metadata |
| `text-sm` | 0.875rem (14px) | Body text / form inputs / table cells |
| `text-base` | 1rem (16px) | Default; reading body content |
| `text-lg` | 1.125rem (18px) | Section sub-headers (h3) |
| `text-xl` | 1.25rem (20px) | Section headers (h2 inside page content) |
| `text-2xl` | 1.5rem (24px) | Page titles (rendered via AppShellV2 pageTitle as h1) |

### Font weight conventions

- `font-medium` (500) — labels / nav items / button text
- `font-semibold` (600) — table headers / section sub-headers
- `font-bold` (700) — page titles / emphasis (use sparingly)

### Code / JSON display

```tsx
// ❌ Wrong (uses default sans-serif)
<pre>{JSON.stringify(args, null, 2)}</pre>

// ✅ Right (mono + appropriate background)
<pre className="font-mono text-xs bg-muted rounded p-2 overflow-auto">
  {JSON.stringify(args, null, 2)}
</pre>
```

---

## 5. Spacing Convention

V2 frontend uses Tailwind's 4-base spacing scale (1 = 0.25rem = 4px).

### Standard spacing values (use these by default)

| Class | Value | Usage |
|-------|-------|-------|
| `p-2` | 8px | Compact cells / dense lists |
| `p-4` | 16px | Standard card / dialog body padding |
| `p-6` | 24px | Page body padding (top-level container) |
| `gap-2` | 8px | Flex / grid item spacing (compact) |
| `gap-4` | 16px | Flex / grid item spacing (standard) |
| `mb-4` | 16px | Section bottom spacing (canonical) |
| `mb-6` | 24px | Major section breaks |
| `space-y-2` | 8px | Vertical stack compact |
| `space-y-4` | 16px | Vertical stack standard |

### Page-level layout

Standard page layout (per Sprint 57.9 governance + admin-tenants):

```tsx
<AppShellV2 pageTitle="My Page">
  <div className="p-6">  {/* page-level padding */}
    <div className="mb-4">  {/* page-level summary / actions */}
      ...
    </div>
    <div className="space-y-4">  {/* main content sections */}
      <Section1 />
      <Section2 />
    </div>
  </div>
</AppShellV2>
```

### Avoid arbitrary spacing

```tsx
// ❌ Wrong (arbitrary; not in scale)
<div className="p-[13px] mt-[7px]">...</div>

// ✅ Right (snap to scale)
<div className="p-3 mt-2">...</div>
```

---

## 6. Loading Skeleton Pattern

While TanStack Query `isLoading` is true, render a skeleton matching the final UI's
shape (per Sprint 57.9 ApprovalList + admin-tenants TenantListTable).

### 5-row table skeleton (canonical)

```tsx
{isLoading ? (
  <table className="w-full">
    <tbody>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i} className="border-b border-border">
          {Array.from({ length: 6 }).map((__, j) => (
            <td key={j} className="p-2">
              <div className="h-4 w-full animate-pulse rounded bg-muted" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
) : (
  <ActualTable data={data} />
)}
```

### 3-card skeleton (for dashboards)

```tsx
{isLoading ? (
  <div className="grid grid-cols-3 gap-4">
    {Array.from({ length: 3 }).map((_, i) => (
      <div key={i} className="rounded-lg border border-border p-4 space-y-2">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-8 w-32 animate-pulse rounded bg-muted" />
        <div className="h-3 w-20 animate-pulse rounded bg-muted" />
      </div>
    ))}
  </div>
) : (
  <ActualDashboard data={data} />
)}
```

### Why skeletons over spinners

- ✅ Reduces perceived loading time (user sees structure immediately)
- ✅ Prevents layout shift when data arrives
- ✅ Communicates expected content shape
- ❌ Spinners (`<Spinner />` / `Loading...`) are acceptable ONLY for instant operations (button mid-click) — NOT for page-level loads

---

## 7. Empty State Pattern

When a query returns 0 items (filter too restrictive / no data yet), render an empty
state with optional reset / retry action (per Sprint 57.9 governance + admin-tenants).

### Canonical layout

```tsx
{!isLoading && data && data.items.length === 0 ? (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <p className="text-muted-foreground mb-4">
      No approvals match your filters.
    </p>
    <Button variant="outline" onClick={resetFilters}>
      Reset Filters
    </Button>
  </div>
) : (
  <ActualList items={data.items} />
)}
```

### Variants

- **Filter-empty**: "No X match your filters" + Reset Filters button (recommended; respect user filter)
- **No-data-yet**: "No X yet. {CTA}" + primary action button (e.g. onboarding flow)
- **Error-empty**: handled separately by Error Retry pattern (see §8)

### Avoid bare empty

❌ **Wrong** (no actionable next step):
```tsx
{data.items.length === 0 && <p>No data</p>}
```

✅ **Right** (actionable + branded):
```tsx
{data.items.length === 0 && (
  <div className="flex flex-col items-center py-12">
    <p className="text-muted-foreground mb-4">No tenants match filters.</p>
    <Button variant="outline" onClick={reset}>Reset Filters</Button>
  </div>
)}
```

---

## 8. Error Retry UX Pattern

When TanStack Query returns `isError`, render an error state with explicit Retry button
that triggers `refetch()` (per Sprint 57.9 cost-dashboard / sla-dashboard ship +
**D-PRE-15 retryClicked flag pattern** for StrictMode mock idempotency).

### Canonical layout

```tsx
{isError && error && (
  <div className="flex flex-col items-center py-12 text-center">
    <p className="text-danger mb-2">Failed to load data</p>
    <p className="text-muted-foreground text-sm mb-4">
      {error.message ?? "Unknown error"}
    </p>
    <Button variant="outline" onClick={() => refetch()}>
      Retry
    </Button>
  </div>
)}
```

### StrictMode mock pattern (D-PRE-15 codified)

For Playwright e2e tests of error retry flow, use **`retryClicked` flag** to gate mock
behavior on user-action (button click) NOT call count. Survives any number of
StrictMode double-renders.

❌ **Wrong** (brittle under StrictMode):
```ts
let firstCall = true;
await page.route("**/api/v1/x", (route) => {
  if (firstCall) {
    firstCall = false;
    return route.fulfill({ status: 500 });  // first call fails
  }
  return route.fulfill({ json: { ... } });  // subsequent succeed
});
// Problem: StrictMode double-renders → firstCall flips on the duplicate call
// before user sees the error → "Retry" button never shows.
```

✅ **Right** (robust under StrictMode):
```ts
let retryClicked = false;
await page.route("**/api/v1/x", (route) => {
  if (!retryClicked) {
    return route.fulfill({ status: 500 });  // initial + StrictMode duplicate both fail
  }
  return route.fulfill({ json: { ... } });  // post-retry-click succeeds
});

await page.goto("/my-page");
await expect(page.getByText("Failed to load data")).toBeVisible();

await page.getByRole("button", { name: "Retry" }).click();
retryClicked = true;  // ← gate flips ONLY on user action

await expect(page.getByText("Loaded item 1")).toBeVisible();
```

### Why this pattern

- Survives any number of React StrictMode double-renders (4 / 8 / 16 — doesn't matter)
- Clear semantic: "before retry click = error; after retry click = success"
- No timing dependency (no `setTimeout` / waitForTimeout hacks)
- Reproducible across browser engines

### Toast notifications (Sonner)

For non-blocking errors (mutation failures), use Sonner toasts (installed Sprint 57.7):

```tsx
import { toast } from "sonner";

const mutation = useMutation({
  mutationFn: ...,
  onError: (err) => {
    toast.error(`Save failed: ${err.message}`);
  },
});
```

For blocking errors (page-level fetch failures), use the inline error pattern above
(NOT toasts — user needs Retry button visibility).

---

## Cross-References

- Convention rules (architecture / state / SSE / test) → [`CONVENTION.md`](./CONVENTION.md)
- React basic rules → [`.claude/rules/frontend-react.md`](../.claude/rules/frontend-react.md)
- Design philosophy + page roadmap → [`docs/03-implementation/agent-harness-planning/16-frontend-design.md`](../docs/03-implementation/agent-harness-planning/16-frontend-design.md)
- File header convention → [`.claude/rules/file-header-convention.md`](../.claude/rules/file-header-convention.md)

---

## Change Process

When a NEW visual / UX pattern emerges (3rd consecutive component using it ad-hoc),
add to STYLE.md within the same sprint OR in next periodic Convention Drift Audit Cycle
(per AD-Convention-Drift-Audit-Cycle, Phase 58.x).

**Threshold for codification**: pattern appears in ≥ 2 component examples (avoid
premature 1-data-point baseline per AD-Plan-3).

**End of STYLE.md**
