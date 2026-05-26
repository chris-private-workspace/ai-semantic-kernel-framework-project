# CHANGE-007: Mockup-Fidelity AuditDocSync Rule Codification

**Date**: 2026-05-26
**Sprint**: 57.46 (Track A of multi-domain bundle)
**Scope**: Docs / Frontend mockup-fidelity rule corpus
**Closes**: `AD-MockupFidelity-AuditDocSync-Rule` (Sprint 57.45 NEW carryover)

## Problem

Audit-derived documents (audit-report.md / drift-audit verdicts / NEAR-PARITY / CATASTROPHIC tags) are derived artifacts from human transcription of mockup screenshots + page read-through. Transcription errors propagate forward: once Sprint N's audit doc states "tab order is A/B/C/D", Sprints N+1, N+2, ... cite that audit doc without re-checking the mockup source.

**Sprint 57.45 evidence**: audit row 9 claimed `/chat-v2` Inspector tabs should be `Run/Tools/Memory/Verify`, but mockup `reference/design-mockups/page-chat.jsx:378-381` actually shows `Turn/Trace/Memory/Tree`. The audit doc carried this transcription error from Sprint 57.22 onward, propagating for **23 sprints unchallenged** until Path B audit overrule grep-verified the mockup source.

This represents a systemic risk: as audit corpus grows over more sprints, transcription error probability compounds. Production-vs-audit-doc verify is **insufficient** — the canonical source must be the mockup file itself.

## Root Cause

No documented rule that:
1. Names mockup source as the canonical source of truth
2. Mandates audit-derivative doc claims be grep-validated against mockup file at Day 0 Prong 2
3. Specifies audit-doc update protocol when transcription error detected (vs. silent rewrite)

The rule existed implicitly (Path B Sprint 57.45 closure used the methodology successfully) but wasn't codified, so future AI / dev sprints had no formal Day 0 obligation.

## Solution

Added new section `🛡️ Mockup File is Canonical (AuditDocSync Rule)` to `docs/rules-on-demand/frontend-mockup-fidelity.md` containing:

- **Statement of rule**: mockup file wins; audit doc updated to match mockup, never reverse
- **Why this rule exists**: explains transcription error propagation mechanism with Sprint 57.45 concrete case
- **Day 0 Prong 2 enforcement**: 3-step protocol (read mockup source / grep against audit claim / fix audit doc if discrepancy)
- **Audit doc update protocol**: 4-step process (inline note + verdict update + retrospective cross-ref + carryover AD)
- **Why rule corpus, not case study only**: explains why we hard-load this vs. leaving as Sprint 57.45 retro-only

Also added `📸 Mockup Capture Method` section formalizing Option B (`python -m http.server` + Playwright via existing `mockup-sweep.mjs`) as the canonical capture convention (resolves AD-MockupCapture-Method-Resolution simultaneously since Track C investigation revealed Option B was already implemented).

Cross-references added:
- `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 (content verify methodology)
- Sprint 57.45 retrospective (Path B narrative)
- Sprint 57.22 retrospective (transcription error introduction point)

## Verification

- `grep "AuditDocSync" docs/rules-on-demand/frontend-mockup-fidelity.md` → 1 section header + 1 cross-ref match
- `grep "🛡️ Mockup File is Canonical" docs/rules-on-demand/frontend-mockup-fidelity.md` → 1 match (new section anchor)
- `grep "📸 Mockup Capture Method" docs/rules-on-demand/frontend-mockup-fidelity.md` → 1 match (new section anchor)
- MHist 1-line entry added at file footer per `.claude/rules/file-header-convention.md`

## Impact

- **Scope**: docs-only; no code change
- **Downstream**: every future frontend sprint Day 0 Prong 2 now has explicit obligation to grep against mockup source; future Sprint 57.22-class transcription errors caught at Day 0 instead of 23 sprints later
- **Audit corpus quality**: provides standard update protocol so audit-doc transcription errors are explicitly versioned, not silently rewritten

## Cross-references

- `docs/rules-on-demand/frontend-mockup-fidelity.md` (modified — 2 new sections + MHist)
- `claudedocs/4-changes/feature-changes/CHANGE-008-tenant-settings-schema-extension.md` (sibling track B)
- `claudedocs/4-changes/feature-changes/CHANGE-009-mockup-capture-method.md` (sibling track C; companion record for capture method portion)
- Sprint 57.45 retro — Path B audit overrule narrative
- Sprint 57.46 plan §4.1 — full rule text source
