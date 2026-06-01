# FIX-025: SSE `_jsonable` stringifies float wire fields (`cache_hit_rate` / `duration_ms`)

**Date**: 2026-06-02
**Sprint**: 57.66 (A-5a+ — events→SSE serialize)
**Severity**: Medium (wire-type defect; no crash)
**Scope**: Cat 12 / api/v1/chat SSE serialization (`backend/src/api/v1/chat/sse.py`)
**Status**: ✅ Fixed

## Problem

Float-typed SSE payload fields are emitted on the wire as **JSON strings** instead of numbers. The Sprint 57.66 `loop_end` payload's new `cache_hit_rate` field (a `float`) round-trips to the client as `"0.5"` (string) rather than `0.5` (number); the pre-existing `tool_call_result.duration_ms` (and the new `prompt_built`/`context_compacted` `duration_ms`) are affected the same way.

Discovered during Sprint 57.66 Stage 1 while writing the router-level e2e test (`TestDiagnosticEventsE2E`) — the only test that round-trips a float through `format_sse_message` (the unit serializer tests assert on `serialize_loop_event` output, before `_jsonable`, so they never saw the wire form).

## Root Cause

`sse.py:_jsonable()` coerces UUIDs to strings via a fragile duck-typing heuristic:

```python
if hasattr(value, "hex") and not isinstance(value, (bytes, bytearray, str, int)):
    return str(value)  # UUID
```

Python `float` **has** a `.hex` method (`(0.5).hex()` → `'0x1.0000000000000p-1'`) and is **not** an `int`, so any non-integral float falls into the UUID-stringify branch → `str(0.5)` → `"0.5"` → `json.dumps` emits it quoted. (Integral floats like `2.0` also; `int` is correctly excluded because `int` has no `.hex` method, but `float` does. `bool` would also have matched but no bool wire field exists.)

The bug pre-dates 57.66 (`duration_ms` has been emitted as a string since Sprint 50.2) but went unnoticed because no test asserted the wire-level numeric type — the existing `test_chat_e2e` echo flow asserts `tool_call_result` content/flags but not `duration_ms`'s type.

## Solution

Match `UUID` explicitly instead of duck-typing on `.hex`:

```python
from uuid import UUID
...
    # datetime → ISO string; UUID → canonical hyphenated string.
    if hasattr(value, "isoformat"):  # datetime
        return value.isoformat()
    # FIX-025: match UUID explicitly. The prior `hasattr(value, "hex")` heuristic
    # also matched float (float.hex exists) + bool, stringifying them — so float
    # wire fields (cache_hit_rate / duration_ms) were emitted as JSON strings.
    if isinstance(value, UUID):
        return str(value)
    return value
```

Now `float` / `int` / `bool` / `None` fall through to `json.dumps`'s native handling (numbers / booleans / null). UUID + datetime handling is unchanged. Intent-revealing (the function's docstring says "UUIDs"); no behavior change for any real payload field except correcting the float types.

**File**: `backend/src/api/v1/chat/sse.py` (`_jsonable` + `from uuid import UUID` import + MHist).

## Verification

- NEW unit regression: `test_sse.py::TestFormatSseMessage::test_float_wire_fields_serialize_as_json_numbers` — round-trips a `LoopCompleted(cache_hit_rate=0.5)` through `format_sse_message` + `json.loads` and asserts `isinstance(parsed["cache_hit_rate"], float)` (would fail with the old `"0.5"` string).
- Router e2e `test_chat_e2e.py::TestDiagnosticEventsE2E` now asserts `loop_end["data"]["cache_hit_rate"] == 0.5` + `isinstance(..., float)` directly (was tolerating the string via `float(...)`).
- Full backend suite green; `mypy src/ --strict` clean; 9/9 V2 lints.

## Impact

- Backend-only; api/v1/chat SSE serializer. Corrects `cache_hit_rate` (Sprint 57.66 new) + `duration_ms` (`tool_call_result` pre-existing, `prompt_built`/`context_compacted` new) wire types from string → number.
- The Sprint 57.66 frontend TS types (`LoopEndEvent.data.cache_hit_rate: number`, etc.) are now truthful — the FE receives JSON numbers, not strings. (This fix is a prerequisite for Stage 2's FE type correctness.)
- No new event, no DB change, no LLM-provider coupling.
