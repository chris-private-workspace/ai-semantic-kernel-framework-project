"""Tests for scripts/lint/check_rules_hygiene.py (REFACTOR-011)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module() -> object:
    repo_root = Path(__file__).resolve().parents[5]
    script = repo_root / "scripts" / "lint" / "check_rules_hygiene.py"
    spec = importlib.util.spec_from_file_location("check_rules_hygiene", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_all_budgeted(mod: object, tmp: Path, matrix_rows: str = "") -> None:
    """Create every budgeted file small + a lean matrix table."""
    for rel in mod.SIZE_BUDGETS:  # type: ignore[attr-defined]
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# small\n", encoding="utf-8")
    matrix = tmp / mod.MATRIX_FILE  # type: ignore[attr-defined]
    matrix.write_text(
        "# matrix\n\n| Scope class | Mult | mean | Status |\n"
        "|---|---|---|---|\n"
        "| `lean-class` | 0.60 | n/a | KEEP (57.1 ratio ~1.0 IN band) |\n" + matrix_rows,
        encoding="utf-8",
    )


def test_all_within_budget_passes(tmp_path: Path) -> None:
    mod = _load_module()
    _seed_all_budgeted(mod, tmp_path)
    assert mod.find_violations(tmp_path) == []  # type: ignore[attr-defined]


def test_matrix_row_over_400_fails(tmp_path: Path) -> None:
    mod = _load_module()
    fat = "| `fat-class` | 0.60 | n/a | KEEP (" + "x" * 400 + ") |\n"
    _seed_all_budgeted(mod, tmp_path, matrix_rows=fat)
    violations = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert len(violations) == 1
    v = violations[0]
    assert v.kind == "matrix_row"
    assert "calibration-log" in v.detail


def test_file_over_budget_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _seed_all_budgeted(mod, tmp_path)
    rel = ".claude/rules/README.md"
    budget = mod.SIZE_BUDGETS[rel]  # type: ignore[attr-defined]
    (tmp_path / rel).write_text("x" * (budget + 1), encoding="utf-8")
    violations = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert len(violations) == 1
    assert violations[0].kind == "over_budget"
    assert violations[0].file == rel


def test_missing_always_loaded_file_fails(tmp_path: Path) -> None:
    mod = _load_module()
    _seed_all_budgeted(mod, tmp_path)
    (tmp_path / "CLAUDE.md").unlink()
    violations = mod.find_violations(tmp_path)  # type: ignore[attr-defined]
    assert [v.kind for v in violations] == ["missing"]
    assert violations[0].file == "CLAUDE.md"


def test_real_repo_is_currently_clean() -> None:
    """The live repo must pass its own hygiene lint (guards this refactor)."""
    mod = _load_module()
    repo_root = Path(__file__).resolve().parents[5]
    assert mod.find_violations(repo_root) == []  # type: ignore[attr-defined]
