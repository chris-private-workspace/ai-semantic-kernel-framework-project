"""
File: backend/scripts/benchmark_memory_recall_precision.py
Purpose: A/B benchmark of memory recall STRATEGIES — measures whether the Sprint 57.155 semantic
         vector recall (cosine, query-relevant) surfaces MORE relevant user facts than the Sprint
         57.148 profile() recall (confidence-ranked, query-independent) at many-fact scale.
Category: 範疇 3 (Memory) — eval tooling
Scope: Phase 57 / Sprint 57.158 (AD-Memory-Vector-Recall-Precision-AB)

Description:
    Settles the honest gap 57.155's retro deferred: its drive-through proved the semantic vector
    machinery is LIVE, but NOT that cosine recall behaviourally BEATS confidence-ranked profile()
    at scale (profile() + knowledge_search co-supported that recall). This harness isolates the
    ranking strategy over a discriminating many-fact corpus and returns a two-sided verdict.

    Three recall arms rank the SAME per-case fact set for a query, top-k:
      - profile  : confidence-desc, QUERY-AGNOSTIC top-k — a faithful reproduction of
                   UserLayer.read(query="") ORDER BY confidence.desc().limit(k) (user_layer.py:141;
                   how MemoryRetrieval.profile() ranks, retrieval.py:161-197).
      - keyword  : substring filter then confidence-desc — a faithful reproduction of
                   content.ilike(f"%{query}%") + confidence.desc().limit(k) (user_layer.py:133,141).
      - semantic : the REAL 57.155 producer MemoryVectorIndex.search(rows=..., query=..., top_k=k)
                   (vector_index.py:169-205) — cosine over embeddings; rows are a PARAMETER (the
                   layer fetches them from DB then passes them in), so the arm needs NO DB, only an
                   EmbeddingClient + a vector store.
    Only `semantic` is a real code path; profile/keyword replicate a 2-line SQL ORDER BY (an
    acceptable AP-10 tradeoff vs a DB dependency that would make the harness un-runnable offline —
    NOT a prompt/logic re-implementation).

    Oracle over each case's gold_fact_ids (the facts a good recall SHOULD surface):
      - recall@k    — fraction of gold facts present in the arm's top-k (PRIMARY; the AD is about
                      surfacing the relevant facts).
      - precision@k — gold facts in top-k / k.
      - mrr         — mean reciprocal rank of the first gold fact.
    Two-sided verdict on recall@k (semantic − profile): >= +Δ semantic-wins (validates 57.155),
    <= −Δ profile-sufficient (don't over-invest in the axis), else tie. Honest EITHER way.

    A hash-based DeterministicEmbeddingClient has NO semantic structure, so the OFFLINE (CI) arm can
    only verify the machinery + oracle + corpus-discrimination — the semantic ADVANTAGE is provable
    ONLY with real embeddings (the RUN_AZURE_INTEGRATION=1 run is the substantive verification).

    Reusable logic (importable as `scripts.benchmark_memory_recall_precision`):
      - load_cases(path)                       — parse + schema-validate the golden YAML
      - recall_at_k / precision_at_k / mrr     — deterministic ranking oracle
      - rank_profile / rank_keyword            — faithful confidence / substring reproductions
      - run_arm(arm, cases, *, index, k)       — rank each case, score (semantic drives real index)
      - build_report(profile, keyword, semantic, k) — pure A/B metrics + two-sided verdict
      - main()                                 — CLI: build Azure embedder + real Qdrant, run 3 arms
    CI-safe unit coverage: tests/unit/scripts/test_benchmark_memory_recall_precision.py
    (DeterministicEmbeddingClient + a fake store, NO Azure). Real run on demand:
      RUN_AZURE_INTEGRATION=1 python scripts/benchmark_memory_recall_precision.py

LLM Provider Neutrality: the core operates on the EmbeddingClient ABC + the QdrantVectorStore
interface; only main() builds the concrete Azure embedder (mirrors the sibling benchmark scripts).

Created: 2026-07-06 (Sprint 57.158)

Modification History (newest-first):
    - 2026-07-06: Initial creation (Sprint 57.158) — memory recall-strategy precision A/B

Related:
    - backend/tests/fixtures/memory/memory_recall_precision_cases.yaml (the golden dataset)
    - backend/src/agent_harness/memory/vector_index.py (MemoryVectorIndex.search — the semantic arm)
    - backend/src/agent_harness/memory/layers/user_layer.py (the profile/keyword reproductions)
    - backend/scripts/benchmark_combined_formation_quality.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import yaml

from agent_harness.memory.vector_index import MemoryRow, MemoryVectorIndex

# A recall@k gap must reach this (10 percentage points) to be material; below it the arms tie.
MATERIALITY_DELTA = 0.10
# Default retrieval cutoff — matches profile()'s top_k=5 (retrieval.py:165).
DEFAULT_K = 5

_ARM_PROFILE = "profile"
_ARM_KEYWORD = "keyword"
_ARM_SEMANTIC = "semantic"

_VERDICT_SEMANTIC_WINS = "semantic-wins"
_VERDICT_TIE = "tie"
_VERDICT_PROFILE_SUFFICIENT = "profile-sufficient"


@dataclass(frozen=True)
class FactSpec:
    """One seeded user fact: a stable id + its content + its stored confidence."""

    id: str
    content: str
    confidence: float


@dataclass(frozen=True)
class RecallCase:
    """One recall case: a single user's facts + a query + the gold-relevant fact ids."""

    id: str
    facts: list[FactSpec]
    query: str
    gold_fact_ids: list[str]


@dataclass(frozen=True)
class ArmScore:
    """Aggregated recall metrics for one arm (profile | keyword | semantic) over the cases."""

    arm: str
    n_cases: int
    recall_at_k: float
    precision_at_k: float
    mrr: float


@dataclass(frozen=True)
class RecallReport:
    """Computed A/B metrics + the two-sided verdict."""

    total: int
    k: int
    profile: ArmScore
    keyword: ArmScore
    semantic: ArmScore
    semantic_vs_profile_recall_delta: float  # semantic − profile; POSITIVE = semantic surfaces more
    semantic_vs_keyword_recall_delta: float  # semantic − keyword
    verdict: str  # semantic-wins | tie | profile-sufficient


def load_cases(path: str | Path) -> list[RecallCase]:
    """Parse + schema-validate the golden YAML fixture into RecallCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("recall fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[RecallCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "facts", "query", "gold_fact_ids"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        facts = _coerce_facts(cid, rc["facts"])
        fact_ids = {f.id for f in facts}
        gold = [str(g) for g in _as_list(cid, rc["gold_fact_ids"])]
        if not gold:
            raise ValueError(f"case '{cid}': gold_fact_ids must be non-empty")
        missing = [g for g in gold if g not in fact_ids]
        if missing:
            raise ValueError(f"case '{cid}': gold_fact_ids {missing} not in facts")
        cases.append(RecallCase(id=cid, facts=facts, query=str(rc["query"]), gold_fact_ids=gold))
    return cases


def _as_list(cid: str, value: object) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"case '{cid}': expected a list, got {type(value).__name__}")
    return value


def _coerce_facts(cid: str, value: object) -> list[FactSpec]:
    facts: list[FactSpec] = []
    seen: set[str] = set()
    for fact in _as_list(cid, value):
        if not isinstance(fact, dict) or "id" not in fact or "content" not in fact:
            raise ValueError(f"case '{cid}': each fact needs 'id' + 'content'")
        fid = str(fact["id"])
        if fid in seen:
            raise ValueError(f"case '{cid}': duplicate fact id '{fid}'")
        seen.add(fid)
        facts.append(
            FactSpec(
                id=fid, content=str(fact["content"]), confidence=float(fact.get("confidence", 0.5))
            )
        )
    if not facts:
        raise ValueError(f"case '{cid}': facts must be non-empty")
    return facts


# === Ranking oracle (deterministic; the arms produce ordered fact-id lists) ===
# Why: recall/precision/MRR over gold_fact_ids objectively compares the three strategies' top-k
# without an LLM (CI-safe). recall@k is primary — the AD is about SURFACING the relevant facts.


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """Fraction of gold facts present in the top-k retrieved. Empty gold → 1.0 (vacuous)."""
    if not gold_ids:
        return 1.0
    top = set(retrieved_ids[:k])
    hit = sum(1 for g in gold_ids if g in top)
    return hit / len(gold_ids)


def precision_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """Gold facts in the top-k / k (the fixed cutoff)."""
    if k <= 0:
        return 0.0
    gold = set(gold_ids)
    hit = sum(1 for r in retrieved_ids[:k] if r in gold)
    return hit / k


def mrr(retrieved_ids: list[str], gold_ids: list[str]) -> float:
    """Reciprocal rank of the FIRST gold fact in the retrieved order; 0.0 if none retrieved."""
    gold = set(gold_ids)
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in gold:
            return 1.0 / rank
    return 0.0


# === Arms: three ranking strategies over the same fact set ===
# profile/keyword faithfully reproduce the UserLayer SQL ORDER BY (a 2-line rule, anchored below);
# semantic is the REAL 57.155 producer. All operate on the case's facts — no DB.


def rank_profile(facts: list[FactSpec], k: int) -> list[str]:
    """Confidence-desc query-agnostic top-k ids (mirrors UserLayer.read q="", user_layer.py:141)."""
    ordered = sorted(facts, key=lambda f: f.confidence, reverse=True)
    return [f.id for f in ordered[:k]]


def rank_keyword(facts: list[FactSpec], query: str, k: int) -> list[str]:
    """Substring + confidence-desc top-k ids (mirrors content.ilike, user_layer.py:133,141)."""
    q = query.lower()
    matched = [f for f in facts if q in f.content.lower()]
    ordered = sorted(matched, key=lambda f: f.confidence, reverse=True)
    return [f.id for f in ordered[:k]]


async def rank_semantic(
    index: MemoryVectorIndex, facts: list[FactSpec], query: str, k: int
) -> list[str]:
    """Cosine top-k via the REAL MemoryVectorIndex.search (vector_index.py:169-205).

    dedup_key carries the fact id so the returned hits map straight back to gold ids.
    A fresh tenant+user per case → per-case isolation + correct ingest idempotency.
    """
    rows = [MemoryRow(dedup_key=f.id, content=f.content, confidence=f.confidence) for f in facts]
    hits = await index.search(tenant_id=uuid4(), user_id=uuid4(), rows=rows, query=query, top_k=k)
    return [h.dedup_key for h in hits]


async def _rank(
    arm: str, case: RecallCase, *, index: MemoryVectorIndex | None, k: int
) -> list[str]:
    if arm == _ARM_PROFILE:
        return rank_profile(case.facts, k)
    if arm == _ARM_KEYWORD:
        return rank_keyword(case.facts, case.query, k)
    if arm == _ARM_SEMANTIC:
        if index is None:
            raise ValueError("semantic arm requires a MemoryVectorIndex")
        return await rank_semantic(index, case.facts, case.query, k)
    raise ValueError(f"unknown arm '{arm}'")


async def run_arm(
    arm: str, cases: list[RecallCase], *, index: MemoryVectorIndex | None = None, k: int = DEFAULT_K
) -> ArmScore:
    """Rank each case under one arm, score recall@k/precision@k/MRR, aggregate the means."""
    recalls: list[float] = []
    precisions: list[float] = []
    rrs: list[float] = []
    for case in cases:
        retrieved = await _rank(arm, case, index=index, k=k)
        recalls.append(recall_at_k(retrieved, case.gold_fact_ids, k))
        precisions.append(precision_at_k(retrieved, case.gold_fact_ids, k))
        rrs.append(mrr(retrieved, case.gold_fact_ids))
    return ArmScore(
        arm=arm,
        n_cases=len(cases),
        recall_at_k=_mean(recalls),
        precision_at_k=_mean(precisions),
        mrr=_mean(rrs),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_report(
    profile: ArmScore, keyword: ArmScore, semantic: ArmScore, *, k: int
) -> RecallReport:
    """Pure A/B metrics + the two-sided verdict on recall@k (semantic − profile).

    semantic-wins iff semantic materially out-recalls the confidence baseline (>= +Δ) — validates
    the 57.155 axis; profile-sufficient iff semantic materially UNDER-recalls (<= −Δ) — don't
    over-invest in the axis; else tie. Honest either way (keyword is a reference column).
    """
    svp = semantic.recall_at_k - profile.recall_at_k
    svk = semantic.recall_at_k - keyword.recall_at_k
    if svp >= MATERIALITY_DELTA:
        verdict = _VERDICT_SEMANTIC_WINS
    elif svp <= -MATERIALITY_DELTA:
        verdict = _VERDICT_PROFILE_SUFFICIENT
    else:
        verdict = _VERDICT_TIE
    return RecallReport(
        total=semantic.n_cases,
        k=k,
        profile=profile,
        keyword=keyword,
        semantic=semantic,
        semantic_vs_profile_recall_delta=svp,
        semantic_vs_keyword_recall_delta=svk,
        verdict=verdict,
    )


def report_to_markdown(report: RecallReport, *, stamp: str) -> str:
    """Render a human-readable A/B report (for the design-note verdict)."""
    lines = [
        f"# Memory Recall-Strategy Precision A/B — {stamp}",
        "",
        f"- cases: **{report.total}** · k: **{report.k}**",
        "",
        "| arm | recall@k | precision@k | MRR |",
        "|-----|----------|-------------|-----|",
        f"| profile (confidence, query-agnostic) | {report.profile.recall_at_k:.2%} | "
        f"{report.profile.precision_at_k:.2%} | {report.profile.mrr:.3f} |",
        f"| keyword (substring) | {report.keyword.recall_at_k:.2%} | "
        f"{report.keyword.precision_at_k:.2%} | {report.keyword.mrr:.3f} |",
        f"| **semantic (cosine, query-relevant)** | {report.semantic.recall_at_k:.2%} | "
        f"{report.semantic.precision_at_k:.2%} | {report.semantic.mrr:.3f} |",
        "",
        f"- semantic − profile recall@k: **{report.semantic_vs_profile_recall_delta:+.2%}**",
        f"- semantic − keyword recall@k: **{report.semantic_vs_keyword_recall_delta:+.2%}**",
        f"- materiality threshold: **{MATERIALITY_DELTA:.0%}**",
        f"- **verdict: {report.verdict}**",
        "",
        "> semantic-wins = the 57.155 vector axis materially out-recalls confidence-ranked "
        "profile() at scale (validates the axis). profile-sufficient = it does not (don't "
        "over-invest). tie = within the materiality band. Honest either way — the corpus is NOT "
        "tuned to force a semantic win.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path, k: int) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require the Azure
    # adapter env (mirrors benchmark_combined_formation_quality.py).
    from adapters.azure_openai.config import AzureOpenAIConfig
    from adapters.azure_openai.embeddings import AzureOpenAIEmbeddingClient
    from core.config import get_settings
    from infrastructure.vector.qdrant_client import QdrantVectorStore

    config = AzureOpenAIConfig()
    if not config.is_embedding_configured():
        print("ERROR: Azure embedding not configured (need AZURE_OPENAI_DEPLOYMENT_EMBEDDING).")
        return 2
    settings = get_settings()
    index = MemoryVectorIndex(
        AzureOpenAIEmbeddingClient(config), QdrantVectorStore(settings.qdrant_url)
    )

    cases = load_cases(fixture)
    profile = await run_arm(_ARM_PROFILE, cases, k=k)
    keyword = await run_arm(_ARM_KEYWORD, cases, k=k)
    semantic = await run_arm(_ARM_SEMANTIC, cases, index=index, k=k)
    report = build_report(profile, keyword, semantic, k=k)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "memory_recall_precision_report.md").write_text(md, encoding="utf-8")
    (out_dir / "memory_recall_precision_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "k": report.k,
                "profile": report.profile.__dict__,
                "keyword": report.keyword.__dict__,
                "semantic": report.semantic.__dict__,
                "semantic_vs_profile_recall_delta": report.semantic_vs_profile_recall_delta,
                "semantic_vs_keyword_recall_delta": report.semantic_vs_keyword_recall_delta,
                "verdict": report.verdict,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− · ≥); force UTF-8 stdout so a Windows
    # cp950 console can't crash the print (mirrors benchmark_combined_formation_quality.py).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(
        description="Memory recall-strategy precision A/B (Sprint 57.158)."
    )
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "memory"
            / "memory_recall_precision_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.fixture), Path(args.out), cast(int, args.k)))


if __name__ == "__main__":
    sys.exit(main())
