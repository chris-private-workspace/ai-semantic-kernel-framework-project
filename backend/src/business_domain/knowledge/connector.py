"""
File: backend/src/business_domain/knowledge/connector.py
Purpose: REAL local-docs knowledge connector — keyword-searches .md/.txt files under a root.
Category: Business domain / knowledge (REAL connector — NOT a mock_executor)
Scope: Phase 57 / Sprint 57.145

Description:
    The platform's FIRST real external data-source connector (vision pillar 1 —
    "連接公司既有外部系統", audited at ~15% with ZERO real connectors on 2026-06-26).
    Unlike the sibling 5 business domains (audit/correlation/incident/patrol/
    rootcause) which route to a mock_services HTTP backend, this connector reads
    REAL files from a configured directory on disk and returns real snippets with
    source paths. Retrieval is simple keyword scoring (Slice 1); embedding/Qdrant
    is Slice 2. Path-safety: all reads are confined to the resolved root (symlink
    escapes / traversal rejected).

Key Components:
    - KnowledgeHit: one search result (relative source path + snippet + score)
    - LocalDocsConnector: reads + keyword-searches a docs root

Created: 2026-06-26 (Sprint 57.145)
Last Modified: 2026-06-26

Modification History (newest-first):
    - 2026-06-26: Sprint 57.145 Day 3 — tokenize query OR-match (fix: multi-word → 0 hits)
    - 2026-06-26: Initial creation (Sprint 57.145) — first real connector
      (AD-Knowledge-Connector-First-Real-Source)

Related:
    - 01-eleven-categories-spec.md §範疇 2 (Tools)
    - v2-reality-audit-engine-vs-grounding-20260626.md §10 #2 (first real connector)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Only plain-text document types in Slice 1; PDF/Office parsing is a later slice.
_SUFFIXES = frozenset({".md", ".txt"})
# Snippet = matched line + this many context lines on each side.
_SNIPPET_CONTEXT_LINES = 1
_MAX_SNIPPET_CHARS = 400

# Keyword score tiers (mirror the mock kb _score ordering: filename > heading > body).
_SCORE_FILENAME = 1.0
_SCORE_HEADING = 0.7
_SCORE_CONTENT = 0.5


@dataclass(frozen=True)
class KnowledgeHit:
    """A single keyword-search result from the docs root."""

    source: str  # path relative to the docs root, e.g. "01-eleven-categories-spec.md"
    snippet: str  # matched line + a small context window
    score: float


class LocalDocsConnector:
    """REAL connector: reads + keyword-searches .md/.txt files under a root directory.

    This is the platform's first real external data-source connector (NOT a mock).
    Slice 1 uses simple keyword scoring; Slice 2 will add embedding/Qdrant. All reads
    are confined to the resolved root for path-safety.
    """

    def __init__(self, root: Path | str) -> None:
        resolved = Path(root).resolve()
        if not resolved.is_dir():
            raise ValueError(
                f"LocalDocsConnector: docs root does not exist or is not a directory: {resolved}"
            )
        self._root = resolved

    @property
    def root(self) -> Path:
        return self._root

    def list_files(self) -> list[Path]:
        """Recursively collect .md/.txt files confined to the root (traversal-safe)."""
        files: list[Path] = []
        for path in self._root.rglob("*"):
            if path.suffix.lower() not in _SUFFIXES:
                continue
            # Path-safety: resolve + confine to root (reject symlink escapes).
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if not resolved.is_relative_to(self._root) or not resolved.is_file():
                continue
            files.append(resolved)
        return sorted(files)

    def search(self, query: str, top_k: int = 5) -> list[KnowledgeHit]:
        """Keyword-search the docs root; return up to top_k hits ranked by score.

        The query is tokenized on whitespace and matched with OR semantics — a
        file scores if it contains ANY token. This is essential for real-LLM use:
        agents send multi-word semantic queries (e.g. "anti-pattern 反模式 定義"),
        and a whole-phrase substring match returns 0 hits because no single line
        holds that exact phrase (Sprint 57.145 drive-through finding). Docs that
        match more distinct tokens rank slightly higher (a small relevance bonus);
        a single-token query keeps the exact filename/heading/content tier.
        """
        tokens = [t for t in query.casefold().split() if t]
        if not tokens:
            return []
        top_k = max(1, min(top_k, 20))
        hits: list[KnowledgeHit] = []
        for path in self.list_files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            score, snippet = self._score_and_snippet(path, text, tokens)
            if score <= 0.0:
                continue
            rel = path.relative_to(self._root).as_posix()
            hits.append(KnowledgeHit(source=rel, snippet=snippet, score=score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def _score_and_snippet(self, path: Path, text: str, tokens: list[str]) -> tuple[float, str]:
        """Score a file for the query tokens (OR match) + snippet around first hit.

        tier = best of filename(1.0) / heading(0.7) / content(0.5) across ANY
        token; a +0.01-per-extra-distinct-token bonus rewards docs matching more
        of the query (single-token query → bonus 0 → exact tier preserved).
        """
        stem = path.stem.casefold()
        tier = 0.0
        matched: set[str] = set()
        stem_hits = [t for t in tokens if t in stem]
        if stem_hits:
            tier = max(tier, _SCORE_FILENAME)
            matched.update(stem_hits)
        lines = text.splitlines()
        match_idx = -1
        for idx, line in enumerate(lines):
            low = line.casefold()
            line_hits = [t for t in tokens if t in low]
            if not line_hits:
                continue
            if match_idx < 0:
                match_idx = idx
            matched.update(line_hits)
            # A markdown heading match is a stronger signal than a body match.
            if line.lstrip().startswith("#"):
                tier = max(tier, _SCORE_HEADING)
            else:
                tier = max(tier, _SCORE_CONTENT)
        if tier <= 0.0:
            return 0.0, ""
        # Multi-token relevance bonus: reward docs matching more distinct tokens.
        bonus = 0.01 * (len(matched) - 1)
        return tier + bonus, self._build_snippet(lines, match_idx)

    def _build_snippet(self, lines: list[str], match_idx: int) -> str:
        """Matched line ± context, trimmed to a max length."""
        if match_idx < 0:
            return ""
        start = max(0, match_idx - _SNIPPET_CONTEXT_LINES)
        end = min(len(lines), match_idx + _SNIPPET_CONTEXT_LINES + 1)
        snippet = "\n".join(lines[start:end]).strip()
        if len(snippet) > _MAX_SNIPPET_CHARS:
            snippet = snippet[:_MAX_SNIPPET_CHARS].rstrip() + "…"
        return snippet
