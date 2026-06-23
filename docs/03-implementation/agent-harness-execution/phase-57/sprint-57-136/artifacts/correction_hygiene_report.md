# Correction-Context Hygiene A/B — 2026-06-23T20:40:49

- cases: **10**

| metric | keep | summarize | delta (summ−keep) |
|--------|------|-----------|-------------------|
| retry_pass_rate | 100.00% | 100.00% | +0.00% |
| repeat_error_rate | 0.207 | 0.165 | -0.043 |
| mean_prompt_tokens | 80.0 | 62.8 | -17.2 |

- self-conditioning delta threshold: **5%**
- **verdict: KEEP default (keep)**

> repeat_error_rate = token-Jaccard(retry, failed_answer); LOWER = less self-conditioning. A NEGATIVE repeat_delta or a POSITIVE pass_delta beyond the threshold flips the default.
