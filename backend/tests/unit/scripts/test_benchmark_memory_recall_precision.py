"""
File: backend/tests/unit/scripts/test_benchmark_memory_recall_precision.py
Purpose: CI-safe offline coverage for benchmark_memory_recall_precision (Sprint 57.158) — oracle
         math, corpus discrimination, run_arm driving the REAL MemoryVectorIndex, and the verdict.
Category: Tests
Created: 2026-07-06 (Sprint 57.158)

Offline only (NO Azure/Qdrant): the semantic arm uses DeterministicEmbeddingClient (hash → vector,
no semantic structure) + a fake in-memory store, so these tests verify the MACHINERY + the oracle +
the corpus-discrimination property — NOT the semantic ADVANTAGE (that is the RUN_AZURE_INTEGRATION=1
run's job). The benchmark module is loaded via the register-before-exec importlib shadow idiom
(tests.unit.scripts would otherwise shadow backend/scripts at collection time).
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from adapters._testing.embedding import DeterministicEmbeddingClient
from agent_harness.memory.vector_index import MemoryVectorIndex
from infrastructure.vector.qdrant_client import VectorHit

# --- load the script module (register in sys.modules BEFORE exec: 3.12 dataclass resolution) ---
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_memory_recall_precision.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_memory_recall_precision_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_memory_recall_precision_under_test"] = _bench
_spec.loader.exec_module(_bench)

load_cases = _bench.load_cases
recall_at_k = _bench.recall_at_k
precision_at_k = _bench.precision_at_k
mrr = _bench.mrr
rank_profile = _bench.rank_profile
rank_keyword = _bench.rank_keyword
run_arm = _bench.run_arm
build_report = _bench.build_report
ArmScore = _bench.ArmScore
FactSpec = _bench.FactSpec
RecallCase = _bench.RecallCase
DEFAULT_K = _bench.DEFAULT_K
MATERIALITY_DELTA = _bench.MATERIALITY_DELTA

_FIXTURE = _ROOT / "tests" / "fixtures" / "memory" / "memory_recall_precision_cases.yaml"


# --- re-inlined fake store (D-fake-store-reuse: it is inlined per-file, not shared) ---
def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _match(payload_filter: Any, payload: dict[str, Any]) -> bool:
    if payload_filter is None:
        return True
    for clause in payload_filter["must"]:
        if payload.get(clause["key"]) != clause["match"]["value"]:
            return False
    return True


class _FakeMemStore:
    """In-memory QdrantVectorStore stand-in honoring the two-key payload filter + cosine rank."""

    def __init__(self) -> None:
        self.collections: dict[str, list[tuple[int, list[float], dict[str, Any]]]] = {}

    async def count(self, name: str, payload_filter: Any = None) -> int:
        pts = self.collections.get(name, [])
        return sum(1 for p in pts if _match(payload_filter, p[2]))

    async def ensure_collection(self, name: str, dim: int) -> None:
        self.collections.setdefault(name, [])

    async def upsert(
        self, name: str, points: list[tuple[int, list[float], dict[str, Any]]]
    ) -> None:
        bucket = self.collections.setdefault(name, [])
        by_id = {p[0]: p for p in bucket}
        for pt in points:
            by_id[pt[0]] = pt
        self.collections[name] = list(by_id.values())

    async def search(
        self, name: str, query_vector: list[float], top_k: int, payload_filter: Any = None
    ) -> list[VectorHit]:
        pts = [p for p in self.collections.get(name, []) if _match(payload_filter, p[2])]
        ranked = sorted(pts, key=lambda p: _cos(query_vector, p[1]), reverse=True)[:top_k]
        return [VectorHit(payload=pl, score=_cos(query_vector, vec)) for (_, vec, pl) in ranked]


def _index() -> MemoryVectorIndex:
    return MemoryVectorIndex(DeterministicEmbeddingClient(dim=48), cast(Any, _FakeMemStore()))


# === Oracle math ===


def test_recall_at_k_counts_gold_in_topk() -> None:
    assert recall_at_k(["a", "b", "c"], ["a", "c"], 5) == 1.0
    assert recall_at_k(["a", "x", "y"], ["a", "c"], 5) == 0.5
    assert recall_at_k(["x", "y"], ["a"], 5) == 0.0


def test_recall_at_k_respects_cutoff() -> None:
    # gold "c" is at rank 3 → excluded when k=2.
    assert recall_at_k(["a", "b", "c"], ["c"], 2) == 0.0
    assert recall_at_k(["a", "b", "c"], ["c"], 3) == 1.0


def test_precision_at_k_divides_by_k() -> None:
    assert precision_at_k(["a", "b", "c", "d", "e"], ["a", "b"], 5) == pytest.approx(2 / 5)
    assert precision_at_k(["a"], ["a"], 5) == pytest.approx(1 / 5)


def test_mrr_is_reciprocal_of_first_gold_rank() -> None:
    assert mrr(["x", "a", "y"], ["a"]) == pytest.approx(0.5)
    assert mrr(["a", "x"], ["a"]) == pytest.approx(1.0)
    assert mrr(["x", "y"], ["a"]) == 0.0


# === Arms (pure) ===


def test_rank_profile_is_confidence_desc_query_agnostic() -> None:
    facts = [
        FactSpec(id="lo", content="low conf fact", confidence=0.3),
        FactSpec(id="hi", content="high conf fact", confidence=0.9),
        FactSpec(id="mid", content="mid conf fact", confidence=0.6),
    ]
    assert rank_profile(facts, 5) == ["hi", "mid", "lo"]
    assert rank_profile(facts, 2) == ["hi", "mid"]


def test_rank_keyword_substring_then_confidence() -> None:
    facts = [
        FactSpec(id="a", content="we use PostgreSQL in prod", confidence=0.4),
        FactSpec(id="b", content="the cache is Redis", confidence=0.9),
        FactSpec(id="c", content="PostgreSQL has a replica", confidence=0.6),
    ]
    # query substring "postgresql" matches a + c; ordered by confidence desc.
    assert rank_keyword(facts, "postgresql", 5) == ["c", "a"]
    # a question is not a substring of any statement → empty.
    assert rank_keyword(facts, "what database do we use?", 5) == []


# === Corpus: parse + discrimination property ===


def test_corpus_loads_and_validates() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) >= 8
    for c in cases:
        assert c.facts and c.query and c.gold_fact_ids
        fact_ids = {f.id for f in c.facts}
        assert all(g in fact_ids for g in c.gold_fact_ids)


def test_corpus_is_discriminating() -> None:
    # >= 50% of cases must place the gold fact OUTSIDE top-5-by-confidence (profile misses it)
    # AND make the query a non-substring of every gold fact (keyword misses it) — else the A/B
    # cannot distinguish semantic from the baselines (plan §3.2 / D-corpus-discriminates).
    cases = load_cases(_FIXTURE)
    discriminating = 0
    for c in cases:
        top5 = set(rank_profile(c.facts, 5))
        gold_outside_top5 = all(g not in top5 for g in c.gold_fact_ids)
        by_id = {f.id: f for f in c.facts}
        q = c.query.lower()
        query_not_substring = all(q not in by_id[g].content.lower() for g in c.gold_fact_ids)
        if gold_outside_top5 and query_not_substring:
            discriminating += 1
    assert discriminating / len(cases) >= 0.5, f"only {discriminating}/{len(cases)} discriminate"


# === load_cases validation ===


def test_load_cases_rejects_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("cases:\n  - id: x\n    facts: []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(p)


def test_load_cases_rejects_gold_not_in_facts(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "cases:\n  - id: x\n    query: q\n    facts:\n      - {id: a, content: hi}\n"
        "    gold_fact_ids: [zzz]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not in facts"):
        load_cases(p)


def test_load_cases_rejects_duplicate_case_id(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "cases:\n"
        "  - {id: x, query: q, facts: [{id: a, content: hi}], gold_fact_ids: [a]}\n"
        "  - {id: x, query: q, facts: [{id: a, content: hi}], gold_fact_ids: [a]}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(p)


# === run_arm drives the REAL producers (semantic via the REAL MemoryVectorIndex, offline) ===


async def test_run_arm_profile_scores_real_corpus() -> None:
    cases = load_cases(_FIXTURE)
    score = await run_arm("profile", cases, k=DEFAULT_K)
    assert score.arm == "profile"
    assert score.n_cases == len(cases)
    assert 0.0 <= score.recall_at_k <= 1.0


async def test_run_arm_semantic_drives_real_index() -> None:
    cases = load_cases(_FIXTURE)
    score = await run_arm("semantic", cases, index=_index(), k=DEFAULT_K)
    assert score.arm == "semantic"
    assert score.n_cases == len(cases)
    # Machinery only: the hash embedder gives near-random recall — assert it RAN + is in range,
    # NOT that it wins (that is the real-Azure run's job).
    assert 0.0 <= score.recall_at_k <= 1.0


async def test_run_arm_semantic_requires_index() -> None:
    cases = load_cases(_FIXTURE)
    with pytest.raises(ValueError, match="requires a MemoryVectorIndex"):
        await run_arm("semantic", cases, index=None, k=DEFAULT_K)


# === build_report verdict (two-sided) ===


def _arm(name: str, recall: float) -> Any:
    return ArmScore(arm=name, n_cases=10, recall_at_k=recall, precision_at_k=recall / 5, mrr=recall)


def test_build_report_semantic_wins() -> None:
    report = build_report(_arm("profile", 0.40), _arm("keyword", 0.10), _arm("semantic", 0.70), k=5)
    assert report.verdict == "semantic-wins"
    assert report.semantic_vs_profile_recall_delta == pytest.approx(0.30)


def test_build_report_profile_sufficient() -> None:
    report = build_report(_arm("profile", 0.80), _arm("keyword", 0.10), _arm("semantic", 0.55), k=5)
    assert report.verdict == "profile-sufficient"


def test_build_report_tie_within_materiality() -> None:
    report = build_report(_arm("profile", 0.60), _arm("keyword", 0.10), _arm("semantic", 0.65), k=5)
    assert report.verdict == "tie"
    assert abs(report.semantic_vs_profile_recall_delta) < MATERIALITY_DELTA
