"""Tests for the --fix autofix in scripts/lint/check_tool_descriptions.py.

Sprint 57.165 (③2 AD-Tool-Description-AutoFix). Day 1 covers collect_fix_targets +
the neutral self-validating drafter + the dry-run report. The module is loaded via
importlib file-path (mirroring test_tool_descriptions.py) because from backend/'s
pytest rootdir the top-level scripts.lint package is not importable. The drafter is
exercised with a fake ChatClient (NO Azure); the real client is covered by the
opt-in real-Azure smoke (Day 3).
"""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any


def _load_module() -> Any:
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
    *,
    description: str | None = '"A clear tool that does a useful thing."',
    schema: str | None = None,
) -> str:
    schema = schema or (
        '{"type": "object", "properties": '
        '{"q": {"type": "string", "description": "A query string."}}}'
    )
    desc_line = "" if description is None else f"    description={description},\n"
    return "ToolSpec(\n" '    name="t",\n' f"{desc_line}" f"    input_schema={schema},\n" ")\n"


# --- a fake neutral ChatClient (NO Azure) ----------------------------------


class _FakeResp:
    def __init__(self, text: str) -> None:
        self.content = text


class _FakeClient:
    """Async chat() returning queued replies; records the requests it saw."""

    def __init__(self, *replies: str) -> None:
        self._replies = list(replies)
        self.calls: list[Any] = []

    async def chat(self, request: Any, **_: Any) -> _FakeResp:
        self.calls.append(request)
        return _FakeResp(self._replies.pop(0))


# --- collect_fix_targets ----------------------------------------------------


def test_collect_wellformed_no_targets(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec())
    targets, unfixable = mod.collect_fix_targets(tmp_path)
    assert targets == []
    assert unfixable == 0


def test_collect_missing_desc_kwarg(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description=None))
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert len(targets) == 1
    assert targets[0].kind == "insert_tool_desc"
    assert targets[0].tool == "t"
    assert targets[0].param is None
    assert "ToolSpec" in targets[0].source_segment


def test_collect_short_desc_is_replace(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description='"too short"'))
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert [t.kind for t in targets] == ["replace_desc"]
    assert targets[0].param is None


def test_collect_placeholder_desc_is_replace(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(description='"A useful tool. TODO finish the docs later."'))
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert any(t.kind == "replace_desc" and t.param is None for t in targets)


def test_collect_missing_param_desc_is_insert(tmp_path: Path) -> None:
    mod = _load_module()
    _w(tmp_path, _spec(schema='{"type": "object", "properties": {"q": {"type": "string"}}}'))
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert len(targets) == 1
    assert targets[0].kind == "insert_param_desc"
    assert targets[0].param == "q"


def test_collect_empty_param_desc_is_replace(tmp_path: Path) -> None:
    mod = _load_module()
    _w(
        tmp_path,
        _spec(
            schema='{"type": "object", "properties": {"q": {"type": "string", "description": ""}}}'
        ),
    )
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert len(targets) == 1
    assert targets[0].kind == "replace_desc"
    assert targets[0].param == "q"


def test_collect_dynamic_param_desc_unfixable(tmp_path: Path) -> None:
    # A variable param description: lint-flagged, but not statically autofixable
    # (a splice would duplicate the key) → counted, not targeted.
    mod = _load_module()
    _w(
        tmp_path,
        _spec(
            schema='{"type": "object", "properties": {"q": {"type": "string", "description": _D}}}'
        ),
    )
    targets, unfixable = mod.collect_fix_targets(tmp_path)
    assert targets == []
    assert unfixable == 1


def test_collect_dynamic_tool_desc_skipped(tmp_path: Path) -> None:
    # An f-string tool description is lint-skipped (no violation) → no target.
    mod = _load_module()
    _w(tmp_path, _spec(description='f"Built for {agent}."'))
    targets, unfixable = mod.collect_fix_targets(tmp_path)
    assert targets == []
    assert unfixable == 0


# --- draft_description (fake client) ---------------------------------------


def _target(mod: Any, *, kind: str = "insert_tool_desc", param: str | None = None) -> Any:
    return mod.FixTarget(
        file=Path("tools.py"),
        kind=kind,
        tool="get_incident",
        param=param,
        lineno=1,
        source_segment='ToolSpec(name="get_incident", input_schema={"type": "object"})',
    )


def test_draft_returns_clean_sentence() -> None:
    mod = _load_module()
    client = _FakeClient("Fetch the incident record identified by the given id.")
    out = asyncio.run(mod.draft_description(client, _target(mod)))
    assert out == "Fetch the incident record identified by the given id."
    assert len(client.calls) == 1


def test_draft_strips_wrapping_quotes_and_collapses_lines() -> None:
    mod = _load_module()
    client = _FakeClient('  "Fetch the incident\n   record by its id."  ')
    out = asyncio.run(mod.draft_description(client, _target(mod)))
    assert out == "Fetch the incident record by its id."


def test_draft_retry_then_success() -> None:
    mod = _load_module()
    # First reply too short → retry → second reply good.
    client = _FakeClient("nope", "Fetch the incident record identified by the given id.")
    out = asyncio.run(mod.draft_description(client, _target(mod)))
    assert out == "Fetch the incident record identified by the given id."
    assert len(client.calls) == 2


def test_draft_needs_manual_when_both_attempts_fail() -> None:
    mod = _load_module()
    client = _FakeClient("short", "TODO later")  # too short, then placeholder
    out = asyncio.run(mod.draft_description(client, _target(mod)))
    assert out == mod.NEEDS_MANUAL
    assert len(client.calls) == 2


# --- render_report ----------------------------------------------------------


def test_render_report_is_dry_run_and_lists_drafts() -> None:
    mod = _load_module()
    drafts = [
        (_target(mod), "Fetch the incident record identified by the given id."),
        (
            _target(mod, kind="insert_param_desc", param="incident_id"),
            "The unique incident identifier to fetch.",
        ),
    ]
    report = mod.render_report(drafts, unfixable_dynamic=1)
    assert "Source UNCHANGED" in report
    assert "get_incident" in report
    assert "Fetch the incident record identified by the given id." in report
    assert "param 'incident_id'" in report
    assert "1 dynamic description(s) skipped" in report


# --- apply_fixes (--write splice) ------------------------------------------

_GOOD = "Fetch the incident record identified by its unique id."


def _apply(mod: Any, text: str, targets: list[Any], draft: str = _GOOD) -> tuple[str, int]:
    return mod.apply_fixes(text, [(t, draft) for t in targets])


def _remaining(mod: Any, tmp_path: Path, new_text: str) -> list[Any]:
    """Write new_text back + re-collect → the still-fixable targets (should be [])."""
    compile(new_text, "tools.py", "exec")  # asserts syntactically valid Python
    _w(tmp_path, new_text)
    return mod.collect_fix_targets(tmp_path)[0]


def test_apply_replace_short_tool_desc(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(description='"too short"')
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, n = _apply(mod, body, targets)
    assert n == 1
    assert _GOOD in new_text
    assert "too short" not in new_text
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_insert_tool_desc_multiline(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(description=None)  # multi-line ToolSpec, no description=
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, n = _apply(mod, body, targets)
    assert n == 1
    assert f'description="{_GOOD}"' in new_text
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_insert_tool_desc_singleline(tmp_path: Path) -> None:
    mod = _load_module()
    body = (
        'ToolSpec(name="t", input_schema={"type": "object", "properties": '
        '{"q": {"type": "string", "description": "A query."}}})\n'
    )
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert [t.kind for t in targets] == ["insert_tool_desc"]
    new_text, n = _apply(mod, body, targets)
    assert n == 1
    assert f'description="{_GOOD}"' in new_text
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_insert_param_desc(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(schema='{"type": "object", "properties": {"q": {"type": "string"}}}')
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, n = _apply(mod, body, targets)
    assert n == 1
    assert f'"description": "{_GOOD}"' in new_text
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_replace_empty_param_desc(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(
        schema='{"type": "object", "properties": {"q": {"type": "string", "description": ""}}}'
    )
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, n = _apply(mod, body, targets)
    assert n == 1
    assert _GOOD in new_text
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_multi_edit_one_file(tmp_path: Path) -> None:
    # A tool missing its description AND a param missing its description → 2 ops.
    mod = _load_module()
    body = _spec(
        description=None,
        schema='{"type": "object", "properties": {"q": {"type": "string"}}}',
    )
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    assert len(targets) == 2
    new_text, n = _apply(mod, body, targets)
    assert n == 2
    assert _remaining(mod, tmp_path, new_text) == []


def test_apply_idempotent(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(description='"too short"')
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, _ = _apply(mod, body, targets)
    _w(tmp_path, new_text)
    # After applying, nothing remains → a second collect+apply is a no-op.
    targets2, _ = mod.collect_fix_targets(tmp_path)
    assert targets2 == []
    again_text, n2 = mod.apply_fixes(new_text, [])
    assert n2 == 0
    assert again_text == new_text


def test_apply_skips_needs_manual(tmp_path: Path) -> None:
    mod = _load_module()
    body = _spec(description='"too short"')
    _w(tmp_path, body)
    targets, _ = mod.collect_fix_targets(tmp_path)
    new_text, n = mod.apply_fixes(body, [(targets[0], mod.NEEDS_MANUAL)])
    assert n == 0
    assert new_text == body


# --- run_fix orchestration (fake client + drafting; NO Azure) ---------------


def _stub_drafting(mod: Any, monkeypatch: Any, draft: str = _GOOD) -> None:
    """Replace the real client build + drafting so run_fix runs without Azure."""
    monkeypatch.setattr(mod, "_build_cheap_client", lambda: object())

    async def _fake_draft_all(_client: Any, targets: list[Any]) -> list[tuple[Any, str]]:
        return [(t, draft) for t in targets]

    monkeypatch.setattr(mod, "_draft_all", _fake_draft_all)


def test_run_fix_write_applies_across_files(tmp_path: Path, monkeypatch: Any) -> None:
    mod = _load_module()
    (tmp_path / "a.py").write_text(_spec(description='"too short"'), encoding="utf-8")
    (tmp_path / "b.py").write_text(
        _spec(schema='{"type": "object", "properties": {"q": {"type": "string"}}}'),
        encoding="utf-8",
    )
    _stub_drafting(mod, monkeypatch)
    assert mod.run_fix(tmp_path, write=True) == 0
    # Both files now clear the lint, and each carries the drafted text.
    assert mod.collect_fix_targets(tmp_path)[0] == []
    assert _GOOD in (tmp_path / "a.py").read_text(encoding="utf-8")
    assert _GOOD in (tmp_path / "b.py").read_text(encoding="utf-8")


def test_run_fix_dry_run_does_not_write(tmp_path: Path, monkeypatch: Any, capsys: Any) -> None:
    mod = _load_module()
    (tmp_path / "a.py").write_text(_spec(description='"too short"'), encoding="utf-8")
    original = (tmp_path / "a.py").read_text(encoding="utf-8")
    _stub_drafting(mod, monkeypatch)
    assert mod.run_fix(tmp_path, write=False) == 0
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == original  # untouched
    assert "Source UNCHANGED" in capsys.readouterr().out


def test_run_fix_no_targets_short_circuits_without_client(tmp_path: Path, monkeypatch: Any) -> None:
    # A well-formed tool → run_fix must return before building the (Azure) client.
    mod = _load_module()
    _w(tmp_path, _spec())

    def _boom() -> Any:
        raise AssertionError("_build_cheap_client must not be called when there are no targets")

    monkeypatch.setattr(mod, "_build_cheap_client", _boom)
    assert mod.run_fix(tmp_path, write=True) == 0
