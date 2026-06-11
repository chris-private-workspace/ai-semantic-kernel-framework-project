# Phase 32 — Routing Performance Report

**Phase**: 32 — Platform Improvement (Sprint 114-118)
**Date**: 2026-02-24
**Test Environment**: Windows Server 2025 Datacenter, Python 3.13, Mock dependencies

---

## Executive Summary

All routing performance benchmarks meet or exceed targets. PatternMatcher operates at sub-millisecond latency, the full pipeline completes under 1ms P95 (with mocks), and throughput exceeds 2,900 req/s with 10 concurrent workers.

---

## Benchmark Results

### Layer Latency (P95)

| Layer | Target | P95 | Avg | Status |
|-------|--------|-----|-----|--------|
| PatternMatcher (53 rules) | < 5ms | 0.05ms | 0.02ms | PASS |
| SemanticRouter (13 routes, mock) | < 100ms | 0.37ms | 0.31ms | PASS |
| Full Pipeline (mixed inputs) | < 150ms | 0.84ms | 0.47ms | PASS |

### Throughput

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| 10 concurrent workers | > 50 req/s | 2,983 req/s | PASS |
| Burst (100 concurrent) | < 5,000ms | < 100ms | PASS |

### Pattern Matching Scalability

| Rule Count | Avg Latency |
|------------|-------------|
| 10 rules | ~0.01ms |
| 30 rules | ~0.01ms |
| 53 rules | ~0.02ms |

Pattern matching scales linearly and remains sub-millisecond even with 53 rules.

### Semantic Routing Accuracy

| Test Set | Queries | Correct | Accuracy |
|----------|---------|---------|----------|
| AD Scenarios (11 queries) | 11 | 11 | 100% |
| L1→L2→L3 Fallback Chain | 3 | 3 | 100% |
| Azure Unavailable Fallback | 2 | 2 | 100% |

### Route CRUD Operations

| Operation | Tests | Status |
|-----------|-------|--------|
| Create Route | 2 | PASS |
| Read Route | 2 | PASS |
| Update Route (metadata) | 1 | PASS |
| Update Route (utterances) | 1 | PASS |
| Delete Route | 1 | PASS |
| Full Lifecycle | 1 | PASS |
| Duplicate Detection | 1 | PASS |
| Not Found Handling | 1 | PASS |

---

## Caveats

1. **Mock Dependencies**: All SemanticRouter and LLM operations use mock implementations. Real Azure AI Search and Anthropic API latencies will be higher.
2. **Expected Real-World Latency**:
   - PatternMatcher: < 5ms (same — pure regex, no external calls)
   - SemanticRouter (Azure AI Search): 20-80ms (network + vector search)
   - LLMClassifier (Claude Haiku): 500-2000ms (API call)
   - Full Pipeline (no LLM): 30-100ms
3. **Windows Test Environment**: OS scheduling may introduce jitter; P99 values are less stable than P95.

---

## Recommendations

1. **Pattern Layer is production-ready** — sub-millisecond with 53 rules
2. **Semantic Layer needs Azure AI Search integration testing** — mock latency (0.37ms) will be 50-200x higher in production
3. **LLM fallback should be monitored** — keep track of fallback rate to optimize pattern/semantic coverage
4. **Consider pattern threshold adjustment** — current 0.90 threshold causes near-miss routing for some Chinese patterns (e.g., confidence 0.8997)
