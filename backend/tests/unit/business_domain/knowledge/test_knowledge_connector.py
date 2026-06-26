"""
File: backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py
Purpose: Unit tests for LocalDocsConnector (Sprint 57.145 — first real connector).
Category: Tests
Created: 2026-06-26
"""

from __future__ import annotations

from pathlib import Path

import pytest

from business_domain.knowledge import LocalDocsConnector


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        LocalDocsConnector(tmp_path / "does-not-exist")


def test_list_collects_md_txt_only_recursive(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "# Alpha\nhello")
    _write(tmp_path, "b.txt", "beta content")
    _write(tmp_path, "c.json", "{ignored}")
    _write(tmp_path, "sub/d.md", "# Delta")
    names = {f.name for f in LocalDocsConnector(tmp_path).list_files()}
    assert names == {"a.md", "b.txt", "d.md"}  # .json skipped; recursive incl. sub/


def test_search_filename_scores_highest(tmp_path: Path) -> None:
    _write(tmp_path, "anti-patterns.md", "# Heading\nbody text")
    _write(tmp_path, "other.md", "mentions anti-patterns in body only")
    hits = LocalDocsConnector(tmp_path).search("anti-patterns", top_k=5)
    assert hits[0].source == "anti-patterns.md"  # filename match → 1.0 ranked first
    assert hits[0].score == 1.0
    other = next(h for h in hits if h.source == "other.md")
    assert hits[0].score >= other.score


def test_search_heading_beats_content(tmp_path: Path) -> None:
    _write(tmp_path, "h.md", "# Topic Zeta\nunrelated")
    _write(tmp_path, "c.md", "plain body mentioning zeta once")
    by_src = {h.source: h.score for h in LocalDocsConnector(tmp_path).search("zeta", top_k=5)}
    assert by_src["h.md"] == 0.7  # heading match
    assert by_src["c.md"] == 0.5  # content match


def test_search_empty_query_returns_empty(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "content")
    assert LocalDocsConnector(tmp_path).search("   ", top_k=5) == []


def test_search_no_match_excluded(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "nothing relevant here")
    assert LocalDocsConnector(tmp_path).search("absent-term", top_k=5) == []


def test_search_top_k_caps(tmp_path: Path) -> None:
    for i in range(10):
        _write(tmp_path, f"f{i}.md", "shared keyword apple")
    assert len(LocalDocsConnector(tmp_path).search("apple", top_k=3)) == 3


def test_search_multiword_query_or_match(tmp_path: Path) -> None:
    """Multi-word query matches files containing ANY token (Sprint 57.145 drive-through
    fix: a real LLM sends phrases like 'anti-pattern 反模式 定義'; whole-phrase substring
    match returned 0 hits because no single line holds that exact phrase)."""
    _write(tmp_path, "anti-patterns.md", "# Pipeline disguised as Loop\nthe anti-pattern body")
    _write(tmp_path, "unrelated.md", "nothing to see here")
    hits = LocalDocsConnector(tmp_path).search("anti-pattern 反模式 規劃 定義", top_k=10)
    assert hits, "multi-word query must return hits via OR token match (was 0 before fix)"
    assert hits[0].source == "anti-patterns.md"  # filename token 'anti-pattern' → 1.0 tier
    assert "unrelated.md" not in {h.source for h in hits}  # no token matches → excluded


def test_search_multitoken_bonus_ranks_higher(tmp_path: Path) -> None:
    """A doc matching MORE distinct query tokens ranks above one matching fewer (same tier)."""
    _write(tmp_path, "both.md", "alpha content and beta content together")
    _write(tmp_path, "one.md", "alpha content only here")
    hits = LocalDocsConnector(tmp_path).search("alpha beta", top_k=5)
    assert hits[0].source == "both.md"  # matches 2 tokens → content tier + bonus > one.md


def test_snippet_contains_match_and_source(tmp_path: Path) -> None:
    _write(tmp_path, "doc.md", "line one\nthe special marker here\nline three")
    hits = LocalDocsConnector(tmp_path).search("special marker", top_k=1)
    assert hits
    assert "special marker" in hits[0].snippet
    assert hits[0].source == "doc.md"


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    """A symlink inside root that resolves OUTSIDE root must be excluded (path-safety)."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("# SECRET\nsensitive data", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    (root / "ok.md").write_text("# OK\nfine", encoding="utf-8")
    try:
        (root / "escape.md").symlink_to(outside / "secret.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this platform")
    connector = LocalDocsConnector(root)
    names = {f.name for f in connector.list_files()}
    assert "ok.md" in names
    assert "escape.md" not in names  # resolves outside root → confined out
    assert connector.search("sensitive", top_k=5) == []  # cannot read the escaped file
