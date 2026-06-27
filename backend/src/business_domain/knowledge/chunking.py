"""
File: backend/src/business_domain/knowledge/chunking.py
Purpose: Section-aware markdown chunking (## split) for richer snippets + embedding units.
Category: Business domain / knowledge (Cat 2 Tools support)
Scope: Phase 57 / Sprint 57.146

Description:
    Splits a markdown document into coherent sections at level-2 (##) ATX
    headings. Content before the first ## is the preamble (heading = the H1
    title, or "(intro)"). Level-3+ (###) headings stay inside their parent ##
    section. Each Section carries the heading line + body so a snippet / an
    embedding unit is a self-contained passage — fixing the 57.145 R2 finding
    (one-line snippets caused the agent to over-search into max_turns) and
    defining the unit the Slice-2 vector index embeds.

Key Components:
    - Section: one chunk (heading_path + body incl. heading line + start_line)
    - split_sections(text): -> list[Section]

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — section-aware chunking
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - connector.py (keyword snippet reuses this)
    - vector_index.py (embedding unit = a Section body)
    - 01-eleven-categories-spec.md §範疇 2 (Tools)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ATX heading: 1-6 '#' then space then non-empty text. Level == count of '#'.
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*\S)\s*$")
# Sections split at level-2 (##) headings; ### + stay inside their parent ##.
_SECTION_LEVEL = 2
# Trim each section body so a snippet / embedding unit is a usable passage,
# not the whole file. ~1500 chars ≈ 250 words — enough to answer in one shot.
_MAX_SECTION_CHARS = 1500
_PREAMBLE_HEADING = "(intro)"


@dataclass(frozen=True)
class Section:
    """One section of a markdown doc: heading + body (body INCLUDES the heading line)."""

    heading_path: str  # cleaned heading text, e.g. "Anti-Pattern 4：Potemkin Features"
    body: str  # heading line + section content, trimmed to _MAX_SECTION_CHARS
    start_line: int  # 0-based line index where the section starts


def _heading(line: str) -> tuple[int, str] | None:
    """Return (level, text) for an ATX heading line, else None."""
    m = _HEADING_RE.match(line)
    if not m:
        return None
    return len(m.group(1)), m.group(2).strip()


def split_sections(text: str) -> list[Section]:
    """Split markdown into sections at level-2 (##) headings.

    The preamble (everything before the first ##) is one section whose heading
    is the H1 title (or "(intro)"). Each ## starts a new section that runs
    until the next ##; ### + headings stay inside. Empty sections (no body
    beyond whitespace) are dropped. A doc with no ## is a single section.
    """
    lines = text.splitlines()
    sections: list[Section] = []

    # Preamble heading = the first H1 (# Title) if present, else "(intro)".
    preamble_heading = _PREAMBLE_HEADING
    for line in lines:
        h = _heading(line)
        if h is not None:
            if h[0] == 1:
                preamble_heading = h[1]
            break

    cur_heading = preamble_heading
    cur_start = 0
    cur_lines: list[str] = []

    def flush(heading: str, start: int, body_lines: list[str]) -> None:
        body = "\n".join(body_lines).strip()
        if not body:
            return
        if len(body) > _MAX_SECTION_CHARS:
            body = body[:_MAX_SECTION_CHARS].rstrip() + "…"
        sections.append(Section(heading_path=heading, body=body, start_line=start))

    for idx, line in enumerate(lines):
        h = _heading(line)
        if h is not None and h[0] == _SECTION_LEVEL:
            # Close the current section, open a new one at this ## heading.
            flush(cur_heading, cur_start, cur_lines)
            cur_heading = h[1]
            cur_start = idx
            cur_lines = [line]
        else:
            cur_lines.append(line)

    flush(cur_heading, cur_start, cur_lines)
    return sections


__all__ = ["Section", "split_sections"]
