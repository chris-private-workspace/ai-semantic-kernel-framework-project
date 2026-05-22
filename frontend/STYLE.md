# Frontend Style Guide

> **🔴 AUTHORITATIVE METHOD**: The styling **method** for any mockup-derived page is
> defined in [`docs/rules-on-demand/frontend-mockup-fidelity.md`](../docs/rules-on-demand/frontend-mockup-fidelity.md)
> — verbatim-copy the mockup CSS into `frontend/src/styles-mockup.css`, consume mockup
> class names directly, oklch end-to-end, NO CSS translation. This STYLE.md covers
> orthogonal visual/UX patterns (loading / empty / error states, typography baselines,
> file structure). Where this doc and the mockup-fidelity rule appear to conflict, the
> mockup-fidelity rule wins.
>
> **Visual + UX rules** for V2 frontend. For convention rules (architecture / state /
> SSE / test patterns), see [`CONVENTION.md`](./CONVENTION.md).
> For React basic rules (ESLint / TypeScript / no inline styles), see
> [`.claude/rules/frontend-react.md`](../.claude/rules/frontend-react.md).
> For design philosophy + page roadmap, see
> [`docs/03-implementation/agent-harness-planning/16-frontend-design.md`](../docs/03-implementation/agent-harness-planning/16-frontend-design.md).

**Created**: 2026-05-09 (Sprint 57.10 codified from Sprint 53.5+57.7+57.8+57.9 emergent palette + UX patterns)
**Last Modified**: 2026-05-22
**Status**: Active

> **Modification History (newest-first)**
> - 2026-05-22: Align to validated mockup-fidelity method — §1 mockup CSS classes now PRIMARY (Tailwind SECONDARY); `styles-mockup.css` permitted+required; §2 oklch canonical (drop oklch→HSL approximation); shadcn = interaction-only; point to `docs/rules-on-demand/frontend-mockup-fidelity.md`
> - 2026-05-17: Sprint 57.19 — §2 indigo primary + accent (closes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap)
> - 2026-05-11: Sprint 57.16 — escape-hatch sub-§ no longer references ChatLayout (migrated; frontend/src now inline-style-clean) (AD-Inline-Style-Cleanup-Sweep-Round2)
> - 2026-05-11: Sprint 57.15 — §1 no-inline-style is now lint-enforced (`no-restricted-syntax`); add "Inline-style escape hatches" sub-section (AD-Inline-Style-Cleanup-Sweep)
> - 2026-05-09: Initial creation (Sprint 57.10 — closes style/UX drift identified by user 2026-05-09 reality check)

---

## Purpose

Frontend style + UX patterns historically drifted because Sprint 53.5 governance
shipped with inline styles + arbitrary hex values; Sprint 57.7 cost-dashboard ship
introduced Tailwind utility-first but reused 53.5's hex via `text-[#2e7d32]` arbitrary
value rather than canonical token. A deeper 10-sprint drift (57.18-57.27) was traced
in the 2026-05-22 investigation to a **wrong styling method** — translating mockup CSS
into Tailwind / shadcn. This doc codifies:
- **Styling mechanism rule** — mockup CSS classes primary, Tailwind secondary
  (full method in `frontend-mockup-fidelity.md`)
- **Canonical color token source** (verbatim oklch from `styles-mockup.css`)
- **Risk badge palette** as a single-source enum table
- **Typography / spacing baselines**
- **Standard UX patterns** (loading skeleton / empty state / error retry)

Future components reference this doc for style decisions instead of grep-ing past
sprints for ad-hoc precedents.

---

## 1. Styling Mechanism — Mockup CSS Primary, Tailwind Secondary

> Full method + 7 鐵律 + DoD: [`docs/rules-on-demand/frontend-mockup-fidelity.md`](../docs/rules-on-demand/frontend-mockup-fidelity.md).

V2 frontend styling for any mockup-derived page is driven by the **mockup CSS classes**
(from `frontend/src/styles-mockup.css` — the byte-identical verbatim copy of the mockup
`reference/design-mockups/styles.css`). Tailwind utilities are a **secondary** mechanism
for layout one-offs and a11y wrappers only — they are **never** used to re-express
styling that the mockup CSS already provides. shadcn/ui primitives are used for
**interaction behavior only** (focus trap / ESC / outside-click), never as a styling
substitute.

### Rules

- ✅ **Mockup CSS classes are the PRIMARY styling mechanism** — pages consume mockup
  class names directly (`className="card"` / `"grid-stats"` / `"badge"` …); do NOT
  re-build mockup styling out of Tailwind utilities.
- ✅ **`frontend/src/styles-mockup.css` is permitted and required** — it is the
  byte-identical verbatim copy of the mockup `styles.css`. Hand-writing OTHER custom
  CSS files is still discouraged (`index.css` holds only `@import "tailwindcss"` + a
  thin bridge).
- ✅ **Tailwind utilities are SECONDARY** — layout one-offs / a11y wrappers where the
  mockup has no corresponding class. Never to re-express mockup styling.
- ✅ **shadcn primitives for INTERACTION behavior only** (Dialog / Tabs / Dropdown /
  Tooltip) — their visual styling still comes from mockup CSS classes; do NOT rely on
  shadcn `Card` / `Badge` / `Button` defaults to stand in for mockup padding / radius /
  shadow / color.
- ❌ **No inline styles** — the JSX `style=` prop (on DOM elements *and* components, whether the value is an inline literal, a variable, or a fn call) is **lint-enforced** by `no-restricted-syntax` in `eslint.config.js` (`error`, since Sprint 57.15 / AD-Inline-Style-Cleanup-Sweep). Use mockup CSS classes (or Tailwind utilities for layout one-offs); for the rare dynamic case see "Inline-style escape hatches" below.
- ❌ **No CSS-in-JS** libraries (styled-components / emotion forbidden)
- ❌ **No translation of mockup CSS into Tailwind utilities** — this is the root drift
  cause of Sprint 57.18-57.27; see `frontend-mockup-fidelity.md` §禁止項.

### Migration precedent — inline styles → class names

Sprint 57.9 migrated 3 governance components (ApprovalsPage / ApprovalList / DecisionModal)
away from inline `style=` objects. The takeaway is **no inline `style=`** — styling
belongs in class names. For mockup-derived pages, that means the **mockup CSS class**;
the Tailwind form below is acceptable only for layout one-offs with no mockup equivalent.

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

✅ **Right** (mockup CSS class — primary, for any mockup-derived element):
```tsx
return <div className="card">...</div>;   // .card defined verbatim in styles-mockup.css
```

✅ **Acceptable** (Tailwind utilities — secondary, layout one-off with no mockup class):
```tsx
return <div className="flex items-center gap-2">...</div>;
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

> **🔴 Token source = `styles-mockup.css`, verbatim, in oklch.**
> Design tokens come **verbatim** from `frontend/src/styles-mockup.css` (the
> byte-identical copy of the mockup `styles.css`), which declares every token as
> `oklch(...)` in its `:root` / `[data-theme="dark"]` blocks. **There is NO
> oklch→HSL approximation step** — oklch and HSL are non-equivalent color spaces, and
> every approximation introduces visible color drift. Consume the token via
> `var(--X)` (the variable already contains the full `oklch()`); never re-express it
> as `hsl(var(--X))` or eyeball an HSL substitute.
>
> The oklch→HSL "approximation" tables that previously lived in this section codified
> the forbidden lossy step (it was the root cause of Sprint 57.18-57.27 drift) and have
> been removed. The historical Sprint 57.18 / 57.19 token notes are preserved below for
> audit trail, but the method they describe is **superseded**.
>
> See [`docs/rules-on-demand/frontend-mockup-fidelity.md`](../docs/rules-on-demand/frontend-mockup-fidelity.md)
> §鐵律 #3 + §4-layer 同步協定.

> **Superseded historical notes (audit trail — method no longer followed)**:
> - *Sprint 57.19 (2026-05-17)*: production `primary` was given an HSL approximation
>   of the mockup's canonical `oklch(0.62 0.16 250)` cool indigo. The HSL step is now
>   forbidden — the oklch value from `styles-mockup.css` is canonical.
> - *Sprint 57.18 (2026-05-16)*: 7 semantic tokens + 4 risk levels were added to
>   `tailwind.config.ts` + `src/index.css` as HSL approximations. Superseded — token
>   definitions come verbatim from `styles-mockup.css` in oklch.

### Token usage

Pages consume mockup CSS classes (`.card` / `.badge` / `.stat` …) which already carry
the correct token-driven colors. Where a Tailwind utility is genuinely needed for a
layout one-off, bridge to the mockup token via `var(--X)` — never hand-pick a hex/HSL.

```tsx
// ❌ Wrong — arbitrary hex / eyeballed HSL bypasses the verbatim oklch token
<span className="text-[#10B981]">Approved</span>

// ✅ Right — consume the mockup class (token-driven, oklch end-to-end)
<span className="badge badge-success">Approved</span>
```

Risk-severity colors (LOW / MEDIUM / HIGH / CRITICAL) are likewise defined as oklch
tokens in `styles-mockup.css` and consumed via the mockup risk-badge classes; see §3.

---

## 3. Risk Badge Palette

> **Note (2026-05-22)**: For mockup-derived pages, risk colors come from the oklch
> risk tokens in `styles-mockup.css`, consumed via the mockup risk-badge classes — NOT
> the arbitrary hex below. The hex table is retained as the historical Sprint 53.5
> reference (and as the sentinel values some `*.spec.ts` tests still assert), but new
> components MUST consume the mockup risk-badge classes. See
> [`docs/rules-on-demand/frontend-mockup-fidelity.md`](../docs/rules-on-demand/frontend-mockup-fidelity.md).

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
