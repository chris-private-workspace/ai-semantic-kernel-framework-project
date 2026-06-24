# Layered Compaction Yield — 2026-01-01T00:00:00

- cases: **6** (tool-heavy transcript specs)
- ACON band: [26%, 54%] · defer threshold: 33% (~1.5x over budget)

| metric | value |
|--------|-------|
| mean tool_clear_reduction | **33.72%** |
| in_acon_band | **True** |
| mean structural_reduction | 33.72% |
| mean semantic_reduction | 40.65% |
| semantic_deferred_rate | **66.67%** |
| **preclear_recommended** | **True** |

| case | L0 | L1 tool-clear | L2 structural | L3 semantic | tool-clear% | deferred |
|------|----|--------------:|--------------:|------------:|------------:|:--------:|
| tool-heavy-long | 12351 | 5456 | 5456 | 5236 | 55.83% | yes |
| tool-heavy-mid | 5131 | 3376 | 3376 | 3293 | 34.20% | yes |
| balanced | 5243 | 3313 | 3313 | 2730 | 36.81% | yes |
| text-heavy | 3691 | 3283 | 3283 | 2414 | 11.05% | no |
| rehydrated-deep | 12547 | 4462 | 4462 | 4024 | 64.44% | yes |
| single-turn-noop | 4032 | 4032 | 4032 | 4032 | 0.00% | no |

> tool_clear_reduction = fraction reclaimed by the LLM-free tool-result clear ALONE. in_acon_band confirms research #4's 26-54% claim. semantic_deferred_rate = how often the cheap layer alone drops below the semantic trigger (~1.5x-over assumption) — i.e. the expensive LLM summarize is avoided. NO-OP cases (single-user-turn) reflect the user-anchored masker limitation (→ AD-Compaction-ToolAnchored-Preclear-Phase58).
