# FIX-034: "New session" button wipes the chat sidebar session list

**Date**: 2026-07-15
**Sprint**: drive-through-driven immediate fix (`AD-Chat-New-Session-Wipes-Sidebar`)
**Scope**: Frontend / chat_v2 (Zustand store + SessionList component)

## Problem

On the chat-v2 page, clicking the **[New session]** button made the **entire sidebar session list disappear**. Refreshing the page brought the list back. Reported via a user drive-through 2026-07-15.

## Root Cause

The "New session" button was wired to the store's `reset()`:

- `SessionList.tsx:151` — `onClick={() => reset()}`
- `chatStore.ts` `reset()` does `set({ ..._initial() })`
- `_initial()` includes `sessions: []`

So `reset()` zeroed the `sessions` sidebar list along with the conversation state. On refresh, `SessionList`'s mount effect calls `loadSessions()` (GET /sessions), which re-fetched and repopulated the list — hence "gone on click, back on refresh".

The codebase already knew this sharp edge: `loadSessionHistory`'s comment reads *"preserve `sessions` + `mode` — … NOT reset() which nukes the sidebar list"*. Both `loadSessionHistory` and `applyPivot` (HANDOFF pivot) do conversation-only resets that preserve `sessions`; only the "New session" button used the full-wipe `reset()`.

## Solution

Add a dedicated **`newSession()`** store action — a conversation-only reset that clears the live conversation + inspector slices (turns / sessionId / activeSessionId / rawEvents / approvals / verifications / subagents / spans / memoryOps / todos) but **preserves the `sessions` sidebar list** (and `mode`, which is preserved automatically since it is not part of `_initial()`'s `Pick`). Wire the button to `newSession()`.

`reset()` is left unchanged as the full wipe used by test teardown (`beforeEach`/`afterEach`) — separating the two avoids changing test-isolation semantics.

- `chatStore.ts` — add `newSession: () => void` to the store type + `newSession()` implementation (`set((s) => ({ ..._initial(), sessions: s.sessions }))`).
- `SessionList.tsx` — subscribe to `newSession` (was `reset`); button `onClick={() => newSession()}`.

## Verification

**Gate layer**:
- Vitest (4 affected files): 86 passed — new `chatStore.newSession.test.ts` (4 tests: preserves sidebar / clears conversation / preserves mode / reset() still full-wipes) + updated `SessionList.test.tsx` regression (button click → `activeSessionId` null **and** sidebar list preserved) + `chatStore.mergeEvent.test.ts` + `chatStore.historyReplay.test.ts` (no regression).
- ESLint (`npm run lint`, no `--silent`): exit 0.
- Build (tsc typecheck + vite): built, exit 0.

**Drive-through layer** (real dev server + real backend, 2026-07-15): user confirmed — after the fix, clicking [New session] starts a fresh conversation and the sidebar session list **no longer disappears**.

## Impact

- Frontend-only. No backend / API / migration change.
- `reset()` now has no production caller (only test teardown); intentional — it is the store's full-wipe primitive.

## Related

- `AD-Chat-New-Session-Wipes-Sidebar` — discovered + fixed in one session via drive-through; this FIX doc is the record (not pre-registered in next-phase-candidates.md).
- `chatStore.ts` `loadSessionHistory` / `applyPivot` — the pre-existing conversation-only-reset siblings this fix mirrors
- CLAUDE.md §Drive-Through Acceptance Hard Constraint (bug found + fix confirmed by drive-through)
