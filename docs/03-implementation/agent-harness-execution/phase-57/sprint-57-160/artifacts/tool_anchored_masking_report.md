# Tool-Anchored Masking A/B — 2026-01-01T00:00:00

- cases: **8** (single-user-turn tool-heavy transcripts)
- materiality floor: 10% · off no-op ceiling: 1%

| metric | value |
|--------|-------|
| mean off_reduction (user-anchored) | **0.00%** |
| mean on_reduction (tool-anchored) | **60.83%** |
| retention_ok_rate | **100.00%** |
| **recommend_default_on** | **True** |

| case | L0 | OFF | ON | off% | on% | retention |
|------|----|----:|---:|-----:|----:|:---------:|
| deep-tool-run | 12230 | 12230 | 3365 | 0.00% | 72.49% | ok |
| mid-tool-run | 5038 | 5038 | 2113 | 0.00% | 58.06% | ok |
| many-small-tools | 5102 | 5102 | 1670 | 0.00% | 67.27% | ok |
| few-large-tools | 12122 | 12122 | 4182 | 0.00% | 65.50% | ok |
| prose-balanced | 4876 | 4876 | 2174 | 0.00% | 55.41% | ok |
| long-single-send | 15374 | 15374 | 2879 | 0.00% | 81.27% | ok |
| keep-1-aggressive | 9194 | 9194 | 1229 | 0.00% | 86.63% | ok |
| keep-covers-all | 3068 | 3068 | 3068 | 0.00% | 0.00% | ok |

> off_reduction ~0 confirms the user-anchored no-op the fix targets (one user turn per send). on_reduction is the tool-anchored yield WITHIN that single user turn. retention_ok = the last N tool results + all tool_calls provenance + non-tool content survive intact. Behavioural retention → Sprint 57.160 drive-through.
