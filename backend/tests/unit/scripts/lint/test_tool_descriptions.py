"""Tests for scripts/lint/check_tool_descriptions.py (Sprint 57.144, research #7 Half A)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module() -> object:
    repo_root = Path(__file__).resolve().parents[5]
    script = repo_root / "scripts" / "lint" / "check_tool_descriptions.py"
    spec = importlib.util.spec_from_file_location("check_tool_descriptions", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _w(tmp: Path, body: str) -> None:
    (tmp / "tools.py").write_text(body, encoding="utf-8")


def _spec(
    *, description: str = '"A clear tool that does a useful thing."', schema: str | None = None
) -> str:
    schema = schema or (
        '{"type": "object", "properties": ' '{"q": {"type": "string", "description": "A query."}}}'
    )
    return (
        "ToolSpec(\n"
        '    name="t",\n'
        f"    description={description},\n"
        f"    input_schema={schema},\n"
        ")\n"
    )


def test_wellformed_passes(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec())
    assert mod.find_violations(tmp_path) == []  # type: ignore[attr-defined]


def test_empty_description_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description='""'))
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("empty" in v.reason for v in vs)


def test_short_description_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description='"too short"'))
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("too short" in v.reason for v in vs)


def test_placeholder_uppercase_token_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description='"A useful tool. TODO finish the docs later."'))
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("placeholder" in v.reason for v in vs)


def test_lowercase_todos_word_passes(tmp_path: Path) -> None:
    # Regression: the English word "todos"/"todo" must NOT trip the placeholder
    # check (the write_todos false-positive — placeholder match is uppercase-only).
    mod = _load_module()
    _w(
        tmp_path,
        _spec(
            description='"Record your plan as a list of todos; update each todo as you go along."'
        ),
    )
    assert mod.find_violations(tmp_path) == []  # type: ignore[attr-defined]


def test_missing_param_description_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(schema='{"type": "object", "properties": {"q": {"type": "string"}}}'))
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("param 'q'" in v.reason for v in vs)


def test_missing_description_kwarg_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, 'ToolSpec(\n    name="t",\n    input_schema={"type": "object"},\n)\n')
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("missing description" in v.reason for v in vs)


def test_dynamic_description_skipped(tmp_path: Path) -> None:
    # An f-string / variable description is not statically checkable → no violation.
    mod = _load_module()
    _w(tmp_path, _spec(description='f"Built dynamically for {agent_name}."'))
    assert mod.find_violations(tmp_path) == []  # type: ignore[attr-defined]


def test_dynamic_schema_skipped(tmp_path: Path) -> None:
    # A non-literal input_schema (a variable) cannot be walked → no param violation.
    mod = _load_module()
    _w(tmp_path, _spec(schema="_BUILT_SCHEMA"))
    assert mod.find_violations(tmp_path) == []  # type: ignore[attr-defined]


def test_adjacent_string_concat_description_checked(tmp_path: Path) -> None:
    # Parenthesized adjacent string literals fold to a single Constant → checked.
    mod = _load_module()
    _w(tmp_path, _spec(description='("short " "x")'))  # 7 chars < MIN
    vs = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert any("too short" in v.reason for v in vs)
