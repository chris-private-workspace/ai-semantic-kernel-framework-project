"""
File: backend/tests/unit/business_domain/knowledge/test_chunking.py
Purpose: Unit tests for split_sections (Sprint 57.146 — section-aware chunking).
Category: Tests
Created: 2026-06-27
"""

from __future__ import annotations

import pytest

from business_domain.knowledge.chunking import Section, split_sections


def test_splits_at_h2_headings() -> None:
    text = "# Title\nintro\n\n## A\nbody a\n\n## B\nbody b\n"
    secs = split_sections(text)
    assert [s.heading_path for s in secs] == ["Title", "A", "B"]  # preamble=H1, then each ##
    a = next(s for s in secs if s.heading_path == "A")
    assert "## A" in a.body and "body a" in a.body
    assert "body b" not in a.body  # no bleed into section B


def test_preamble_uses_h1_then_intro_fallback() -> None:
    with_h1 = split_sections("# My Doc\nlead\n## S\nx\n")
    assert with_h1[0].heading_path == "My Doc"
    no_h1 = split_sections("just text\nmore text\n## S\nx\n")
    assert no_h1[0].heading_path == "(intro)"
    assert "just text" in no_h1[0].body


def test_h3_stays_inside_parent_h2() -> None:
    text = "## Parent\nlead\n### Child\nchild body\nmore\n## Next\nn\n"
    secs = split_sections(text)
    parent = next(s for s in secs if s.heading_path == "Parent")
    assert "### Child" in parent.body  # ### did NOT start a new section
    assert "child body" in parent.body
    assert {s.heading_path for s in secs} == {"Parent", "Next"}  # only ## are boundaries


def test_no_heading_is_single_section() -> None:
    secs = split_sections("plain line one\nplain line two\n")
    assert len(secs) == 1
    assert secs[0].heading_path == "(intro)"
    assert "plain line one" in secs[0].body


def test_empty_doc_returns_no_sections() -> None:
    assert split_sections("") == []
    assert split_sections("\n\n   \n") == []  # whitespace-only → dropped


def test_start_line_tracks_section_offset() -> None:
    secs = split_sections("# T\nintro\n## A\nbody\n")
    a = next(s for s in secs if s.heading_path == "A")
    assert a.start_line == 2  # 0-based: line 2 is "## A"


def test_long_section_body_trimmed() -> None:
    secs = split_sections("## Big\n" + ("x" * 5000))
    assert len(secs) == 1
    assert len(secs[0].body) <= 1600  # near _MAX_SECTION_CHARS + ellipsis
    assert secs[0].body.endswith("…")


def test_section_is_frozen() -> None:
    s = Section(heading_path="h", body="b", start_line=0)
    with pytest.raises(Exception):
        s.heading_path = "x"  # type: ignore[misc]
