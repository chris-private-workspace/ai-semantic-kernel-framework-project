# Memory Recall-Strategy Precision A/B — 2026-07-06T22:46:53

- cases: **10** · k: **5**

| arm | recall@k | precision@k | MRR |
|-----|----------|-------------|-----|
| profile (confidence, query-agnostic) | 20.00% | 4.00% | 0.150 |
| keyword (substring) | 10.00% | 2.00% | 0.100 |
| **semantic (cosine, query-relevant)** | 100.00% | 22.00% | 1.000 |

- semantic − profile recall@k: **+80.00%**
- semantic − keyword recall@k: **+90.00%**
- materiality threshold: **10%**
- **verdict: semantic-wins**

> semantic-wins = the 57.155 vector axis materially out-recalls confidence-ranked profile() at scale (validates the axis). profile-sufficient = it does not (don't over-invest). tie = within the materiality band. Honest either way — the corpus is NOT tuned to force a semantic win.
