# Sprint 57.150 Drive-Through Snapshot — memory write-side dedup

**Date**: 2026-06-30 · real chat-v2 (vite :3007) + fresh backend (PID 43620, branch code, migrated dev DB) + real Azure gpt-5.2 · dan@acme.com / tenant acme-prod.

## Observed vs intended

| Step | Intended | Observed | Verdict |
|------|----------|----------|---------|
| Send 1 — agent saves verbatim fact | agent `memory_write` writes the exact fact | `memory_write(content="Project Helix DT150 is built in Rust and ships in November 2027.", conf 0.6)` → "Saved", verify 0.99 | ✅ |
| After send 1 (DB) | 1 row, not 2, despite memory_write + auto_extract both writing it | **1 row** `key=dd16b505` `conf=0.99` `created=07:08:54` `updated=07:09:01 BUMPED`; source kept = first writer (none) | ✅ intra-send dedup LIVE (greatest conf 0.6→0.99, bumped) |
| Send 2 — re-affirm same fact | another `memory_write` of same content → still 1 row | **STILL 1 row** same `key=dd16b505`, `created` unchanged, `updated=07:10:14 BUMPED again` | ✅ cross-send dedup |
| New session — recall | profile() surfaces the deduped fact ONCE | "I remember that Project Helix DT150 is built in Rust and ships in November 2027." (single, clean) | ✅ no dilution |

**Net**: pre-57.150 the same fact → 2-4 `memory_user` rows (memory_write + auto_extract × sends) diluting `profile()` top-k; post-57.150 → **1 row** (greatest confidence, latest content, first-writer provenance), recalled once.

## Files
- `dt150-chat-dedup.png` — send 1+2 with the two `memory_write` tool calls.
- `dt150-clean-recall.png` — new-session single clean recall.
- DB inspector `scratchpad/dt150_db.py`; session `69b0b5ec-76c4-435f-9867-33c856497295`.

## Honesty note
Real UI + real backend + real LLM (NOT gate-only / curl). Deterministic dedup logic additionally covered by 6 real-Postgres integration tests (`test_user_layer_dedup.py`).
