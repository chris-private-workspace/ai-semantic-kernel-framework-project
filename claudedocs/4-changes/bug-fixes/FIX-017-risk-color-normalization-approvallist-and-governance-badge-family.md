# FIX-017: governance risk-colour map normalization — 4 hex sentinels → mockup `var(--risk-X)` tokens (ApprovalList + Badge + AuditChainBadge)

**Date**: 2026-05-25
**Sprint**: AD `AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels` application (not a sprint — single bundled FIX; post-4-AD-sequence next item per user authorization)
**Scope**: 3 governance files × token swap (4-color risk palette) + 1 Vitest spec assertion update + HEX_OKLCH_BASELINE 50→45 + 2 file-header MHist entries + check-mockup-fidelity.mjs comment refresh
**Branch**: `fix/risk-color-normalization-approvallist-and-chatv2`
**PR**: (filled after open)
**Class**: Risk-tone normalization micro-fix (closes Sprint 53.5 hex sentinel debt)

---

## Problem

`ApprovalList.tsx` L34-39 kept 4 Tailwind arbitrary-value hex classes (`text-[#2e7d32]` / `text-[#ed6c02]` / `text-[#d84315]` / `text-[#b71c1c]`) as Sprint 53.5 "test sentinels". FIX-015 closeout logged this as a deferred carryover AD (#47.5 in `next-phase-candidates.md`) for a future risk-tone normalization sprint that should map them to the mockup `var(--risk-low | --risk-medium | --risk-high | --risk-critical)` tokens already defined in `styles-mockup.css:20-23`.

Day 0 grep extended the scope: the same 4-colour palette also lives in **2 sibling files**:
- `components/ui/badge.tsx` L39-42 — shadcn cva `risk-low/medium/high/critical` variants (central source-of-truth for the 4-colour palette)
- `features/governance/components/AuditChainBadge.tsx` L77 — standalone "valid state" badge (only the `#2e7d32` LOW colour used; per-instance className)

All 3 files cite STYLE.md §3 as the source palette; the original Sprint 53.5 design baked the same 4 hex values into Tailwind utility classes across all governance risk-display surfaces. The mockup risk tokens cover the same semantic intent with oklch precision; bringing them in retires the per-class drift surface.

---

## Day 0 audit findings (scope adjustment from AD #47.5 spec)

AD #47.5 named `ApprovalList.tsx` + suggested coordination with `chat_v2` risk-color map normalization. Day 0 grep returned:

| File | Sites | Hex literals | AD-spec listed? | FIX-017 decision |
|------|-------|--------------|------------------|------------------|
| `components/ui/badge.tsx` L39-42 | 4 cva variants × `bg-[#hex]/10 text-[#hex]` | 8 hex literals (4 distinct colours) | ❌ (NEW finding) | ✅ Re-point (central source; same drift class) |
| `features/governance/components/ApprovalList.tsx` L36-39 | 4 lookup entries × `text-[#hex]` | 4 hex literals | ✅ (AD target) | ✅ Re-point |
| `features/governance/components/AuditChainBadge.tsx` L77 | 1 inline className × `bg-[#hex]/10 text-[#hex]` | 2 hex literals | ❌ (NEW finding) | ✅ Re-point |
| `features/chat_v2/components/ApprovalCard.tsx` L35 | 1 docstring reference | 0 live literals | (AD-spec coordination target) | ❌ Skip — only a comment historical reference; chat_v2 already migrated |

**Final scope: 3 governance files** (1 AD-target + 2 NEW sibling findings; chat_v2 already migrated).

Scope expansion to NEW findings rationalised: all 3 files share the same 4-colour palette, same drift root cause (Sprint 53.5 hex sentinels), and the same translation target (mockup `--risk-X` tokens). Per FIX-015 precedent (AP-Phase2-C systemic anti-pattern cleanup), bundling same-class drift into one PR is preferred over splitting.

---

## Solution (Tailwind v4 typed arbitrary value with CSS var)

DOM structure / props / state / API shape (`RISK_COLOR_CLASS[level]` lookup map + `<Badge variant="risk-low">` cva consumer) all preserved. Only `className` token values change.

### Translation table

| Old (Sprint 53.5 hex) | Risk level | New mockup token | Token value (styles-mockup.css:20-23) |
|-----------------------|-----------|------------------|---------------------------------------|
| `#2e7d32` | LOW | `var(--risk-low)` | `var(--success)` (alias) |
| `#ed6c02` | MEDIUM | `var(--risk-medium)` | `var(--warning)` (alias) |
| `#d84315` | HIGH | `var(--risk-high)` | `oklch(0.65 0.20 40)` (≈ #EA580C) |
| `#b71c1c` | CRITICAL | `var(--risk-critical)` | `oklch(0.55 0.22 25)` (≈ #B71C1C) |

### Per-file change summary

**`badge.tsx` L38-42** — 4 cva variants:
```diff
- // STYLE.md §3 risk palette (hex matches features/governance/components/ApprovalCard.tsx).
- "risk-low":      "border-transparent bg-[#2e7d32]/10 text-[#2e7d32]",
- "risk-medium":   "border-transparent bg-[#ed6c02]/10 text-[#ed6c02]",
- "risk-high":     "border-transparent bg-[#d84315]/10 text-[#d84315]",
- "risk-critical": "border-transparent bg-[#b71c1c]/10 text-[#b71c1c]",
+ // STYLE.md §3 risk palette → mockup --risk-X tokens (FIX-017 normalization
+ // from Sprint 53.5 hex sentinels). styles-mockup.css L20-23 owns the
+ // oklch values; this Badge component now consumes them via Tailwind
+ // arbitrary value with `color:` type hint (supports the `/10` opacity
+ // modifier exactly like the original hex literals did).
+ "risk-low":      "border-transparent bg-[color:var(--risk-low)]/10 text-[color:var(--risk-low)]",
+ "risk-medium":   "border-transparent bg-[color:var(--risk-medium)]/10 text-[color:var(--risk-medium)]",
+ "risk-high":     "border-transparent bg-[color:var(--risk-high)]/10 text-[color:var(--risk-high)]",
+ "risk-critical": "border-transparent bg-[color:var(--risk-critical)]/10 text-[color:var(--risk-critical)]",
```

**`ApprovalList.tsx` L34-40** — RISK_COLOR_CLASS lookup map:
```diff
- // Preserve exact 53.5 palette via Tailwind arbitrary-value class (test sentinel).
+ // FIX-017: re-point Sprint 53.5 hex sentinels (#2e7d32/#ed6c02/#d84315/#b71c1c)
+ // to mockup --risk-X tokens. styles-mockup.css L20-23 owns the oklch values;
+ // Tailwind arbitrary value with `color:` type hint preserves the class-lookup
+ // API shape (consumers use RISK_COLOR_CLASS[level] unchanged).
  const RISK_COLOR_CLASS: Record<RiskLevelLabel, string> = {
-   LOW: "text-[#2e7d32]",
-   MEDIUM: "text-[#ed6c02]",
-   HIGH: "text-[#d84315]",
-   CRITICAL: "text-[#b71c1c]",
+   LOW: "text-[color:var(--risk-low)]",
+   MEDIUM: "text-[color:var(--risk-medium)]",
+   HIGH: "text-[color:var(--risk-high)]",
+   CRITICAL: "text-[color:var(--risk-critical)]",
  };
```

**`AuditChainBadge.tsx` L77** — valid-state inline className:
```diff
- className="rounded-md bg-[#2e7d32]/10 px-2 py-1 text-xs font-semibold text-[#2e7d32]"
+ className="rounded-md bg-[color:var(--risk-low)]/10 px-2 py-1 text-xs font-semibold text-[color:var(--risk-low)]"
```

### Why typed arbitrary value (`bg-[color:var(--X)]/10`)

Tailwind v4 needs the `color:` type hint inside arbitrary value brackets when the value is a CSS var (otherwise the compiler can't infer the property type — color vs length vs etc.). With the hint, the `/10` opacity modifier still works exactly as it did with the hex literal (Tailwind compiles it to `color-mix(in oklch, var(--risk-low), transparent 90%)` automatically).

### Vitest spec assertion update

`tests/unit/components/ui/components.test.tsx:91-94` had a Sprint 57.13 spec asserting `className.toContain("#b71c1c")` for the risk-critical variant. Updated to assert the new token reference:

```diff
- it("risk-critical variant uses the STYLE.md §3 hex", () => {
-   const { container } = render(<Badge variant="risk-critical">CRITICAL</Badge>);
-   expect((container.firstChild as HTMLElement).className).toContain("#b71c1c");
- });
+ it("risk-critical variant maps to mockup --risk-critical token", () => {
+   // FIX-017: assertion updated from Sprint 53.5 hex sentinel `#b71c1c` to
+   // the mockup `var(--risk-critical)` token; styles-mockup.css L23 owns
+   // the oklch value (≈ #B71C1C; same visual intent).
+   const { container } = render(<Badge variant="risk-critical">CRITICAL</Badge>);
+   expect((container.firstChild as HTMLElement).className).toContain("var(--risk-critical)");
+ });
```

Test intent preserved: "the risk-critical variant produces the STYLE.md §3 risk-critical color"; the assertion target changed from hex literal to token reference. Spec name + comment document the migration rationale.

### Bonus: HEX_OKLCH_BASELINE 50 → 45

`check-mockup-fidelity.mjs` grep guard live count dropped from 50 to 45 (5 lines retired per guard's auto-suggestion). Baseline tightened + extended comment cites FIX-017 as the source of the -5 along with FIX-015's earlier -1.

---

## Verification (all green vs FIX-016 baseline)

| Check | Result |
|-------|--------|
| TypeScript strict (`npx tsc --noEmit`) | 0 errors |
| Frontend lint (`npm run lint`; **non-silent** per Item #4 rule + FIX-015 CI fail lesson) | ✅ 0 errors (only upstream `jsx-ast-utils` TSSatisfiesExpression warnings — unchanged baseline noise) |
| Mockup-fidelity guard (`node scripts/check-mockup-fidelity.mjs`) | ✅ pass — diff guard OK / grep guard **45** (was 50, tightened) |
| Vitest (`npx vitest run`) | ✅ 478/478 (96 files) after spec fix — baseline restored |
| Vite build (`npm run build`) | ✅ built in 3.44s — main 336.52 kB (no bundle delta) |

**Mid-fix CI iteration**: Vitest initially failed 1/478 because `components.test.tsx:91` had hardcoded the old `#b71c1c` assertion. Fix folded into same PR (1-line spec update + WHY comment). Same pattern as FIX-015 → patch commit `4c05be67` — caught locally this time because non-silent lint + Vitest both ran (Item #4 rule application).

---

## Impact

### Visual

- All consumers of `<Badge variant="risk-low|medium|high|critical">` (shadcn-ui Badge component) now render with mockup oklch tokens, auto-inheriting `[data-theme][data-variant]` scope (8 variants: dark/light × neutral/warm/cool + dark/light default)
- `ApprovalList.tsx` table cells using `RISK_COLOR_CLASS[level]` (governance approvals list) render new tokens
- `AuditChainBadge.tsx` "✓ Valid" badge renders new `--risk-low` token (visually similar green; semantically aligned with mockup design system)

### Structural

- Class lookup map API unchanged in ApprovalList (`RISK_COLOR_CLASS[level]` still works for consumers)
- shadcn cva variants in Badge unchanged externally (`<Badge variant="risk-low">` callers don't need to update)
- `.row` mockup class + STYLE.md §3 escape hatches unaffected
- No backend / API / DB schema changes

### Phase-2 epic indirect impact

- Sprint 57.39 retro Q3 noted "AP-Phase2-C systemic shadcn-token residue" as the remaining drift class to close on already-re-pointed pages
- FIX-012 retired `--sc-border` globally; FIX-015 cleared `bg-card`/`text-foreground`/etc. on governance + verification children; FIX-017 now retires the 4-colour risk palette hex literals — sequence converges toward zero hex/oklch literals in `.tsx`/`.ts` (target = mockup-fidelity guard baseline 0)
- HEX_OKLCH_BASELINE now at 45; remaining 45 lines are mostly in chat_v2 mockup-token references (per check-mockup-fidelity.mjs L72-73 comment) — those are intentional verbatim token references, not drift

### AD lifecycle

- ✅ **`AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels`** (#47.5 in next-phase-candidates) — RESOLVED
- ✅ **STYLE.md §3 risk palette** — now sourced from mockup verbatim tokens (Sprint 53.5 hex sentinels retired; STYLE.md rule can update to reference `var(--risk-X)` instead of hex values, optional follow-up nice-to-have)

### Backward compatibility

- ✅ Fully compatible — all consumers of the 3 modified files continue to work; only the underlying className strings change
- Visual shift: minor — `--risk-low/medium` map to `--success`/`--warning` (slightly different green/orange shades); `--risk-high/critical` are oklch with comments noting near-identical hex equivalents
- No regressions caught by Vitest 478/478 + build clean + lint clean

---

## Carryover

### Not included (deliberate scope cuts per Karpathy §3)

- **STYLE.md §3 rule update** — could update STYLE.md to reference `var(--risk-X)` tokens instead of hex values (the rule still cites the old hex). Out of scope for FIX-017 (code change focus); nice-to-have follow-up `chore(docs)` PR. Estimated ~10 min.
- **VerifierTypeBadge / MemoryScopeBadge** — `badge.tsx` docstring mentions these "keep their own colour logic for now". Not flagged in Day 0 grep (no hex literals), but a future Phase-2 sweep could check whether they have any non-mockup token residue. Defer until evidence emerges.

### Already cleaned (verified Day 0)

- **chat_v2 risk-color map** — only docstring historical reference remains in `ApprovalCard.tsx:35`; no live hex literals. AD #47.5's coordination target already migrated pre-FIX-017.

---

## References

- AD source: `claudedocs/1-planning/next-phase-candidates.md` §47.5 (FIX-015 carryover)
- Related anti-pattern: `docs/rules-on-demand/frontend-mockup-fidelity.md` §AP-Phase2-C
- Predecessors closing same hex-literal drift class: FIX-012 (`--sc-border` retire), FIX-015 (6 child component re-point)
- Mockup truth: `frontend/src/styles-mockup.css:20-23` (`--risk-X` token definitions) + L532-538 (`.badge.risk-X` companion classes)
- Vitest spec: `frontend/tests/unit/components/ui/components.test.tsx:91-99` (assertion updated in same PR)
- Sprint 53.5 origin: STYLE.md §3 risk palette (hex values baked into Tailwind utility classes at that sprint)

---

## Modification History (newest-first)

- 2026-05-25: Initial creation (FIX-017 — 3 governance files risk-colour normalization + 1 Vitest spec update + HEX_OKLCH_BASELINE 50→45)
