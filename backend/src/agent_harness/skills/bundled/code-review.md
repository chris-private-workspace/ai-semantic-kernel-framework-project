---
name: code-review
description: Review a code snippet or diff and report concrete risks with severities and fixes
---

# Code Review

When the user shares a code snippet or diff, review it and report findings in this exact structure. Be direct and technical — no praise, no filler, no restating the code back to the user.

## Summary
One sentence: what the code does and your overall verdict (e.g. "Two correctness bugs and one injection risk; not safe to merge as-is").

## Risks
A markdown table — one row per concrete issue. If you find zero issues, omit the table and say so explicitly.

| Severity | Issue | Location |
|----------|-------|----------|
| High / Med / Low | What is wrong and why it matters | function / line / variable |

Cover, in this priority order: security (injection, auth bypass, hardcoded secrets, unsafe deserialization), then correctness (logic errors, missing null/None handling, off-by-one, race conditions), then performance (needless O(n^2), unbounded growth, blocking calls in async paths). Rank security and correctness above performance.

## Suggested fixes
For each High / Med risk, give the concrete change — a corrected line or a one-line description of the fix. Keep it minimal and surgical: fix the bug, do not rewrite the file or add unrequested features.
