"""
File: backend/tests/unit/agent_harness/state_mgmt/test_todo_dag.py
Purpose: Unit tests for the dependency-DAG half of the task primitive (Sprint 57.156).
Category: Tests / 範疇 3 contract (task primitive DAG)
Scope: Phase 57 / Sprint 57.156

Description:
    DB-free unit tests for `Todo.depends_on`, the tolerant `depends_on` serde, the
    `ready_todos` topological-readiness helper (direct-dependency, cycle-safe,
    unknown-dep-ignored), and the dependency-aware `render_active_plan` (byte-
    identical to the Sprint 57.140 flat render when no todo carries a dependency).

Created: 2026-07-01 (Sprint 57.156)
"""

from __future__ import annotations

from agent_harness._contracts.todo import (
    Todo,
    _todo_from_dict,
    detect_cycles,
    plan_warnings,
    ready_todos,
    render_active_plan,
    todos_from_jsonb,
    todos_to_jsonb,
)

# ----- depends_on serde -------------------------------------------------------


def test_depends_on_round_trips() -> None:
    """depends_on survives todos_to_jsonb → todos_from_jsonb verbatim."""
    todos = [
        Todo(id="a", title="Design schema"),
        Todo(id="b", title="Write migration", depends_on=("a",)),
        Todo(id="c", title="Run tests", depends_on=("a", "b")),
    ]
    blob = todos_to_jsonb(todos)
    assert blob[1] == {
        "id": "b",
        "title": "Write migration",
        "status": "pending",
        "depends_on": ["a"],
    }
    assert todos_from_jsonb(blob) == todos


def test_depends_on_defaults_empty() -> None:
    """A todo written without depends_on serializes with an empty list + reloads as ()."""
    blob = todos_to_jsonb([Todo(id="1", title="x")])
    assert blob[0]["depends_on"] == []
    assert todos_from_jsonb(blob)[0].depends_on == ()


def test_depends_on_tolerant_non_list() -> None:
    """A non-list depends_on coerces to () (never raises)."""
    todo = _todo_from_dict({"id": "1", "title": "x", "depends_on": "not-a-list"})
    assert todo is not None
    assert todo.depends_on == ()


def test_depends_on_drops_self_ref_empties_and_dedups() -> None:
    """Self-reference + blank entries dropped; order-preserving dedup."""
    todo = _todo_from_dict({"id": "b", "title": "x", "depends_on": ["a", "", "b", "a", "c", "  "]})
    assert todo is not None
    assert todo.depends_on == ("a", "c")  # "b" (self) + "" + dup "a" dropped


# ----- ready_todos ------------------------------------------------------------


def test_ready_no_deps_is_ready() -> None:
    """A pending todo with no dependencies is trivially ready."""
    todos = [Todo(id="1", title="x"), Todo(id="2", title="y")]
    assert ready_todos(todos) == {"1", "2"}


def test_ready_chain_unblocks_progressively() -> None:
    """In a→b→c chain only the head is ready; completing it unblocks the next."""
    pending = [
        Todo(id="a", title="a"),
        Todo(id="b", title="b", depends_on=("a",)),
        Todo(id="c", title="c", depends_on=("b",)),
    ]
    assert ready_todos(pending) == {"a"}
    after_a = [
        Todo(id="a", title="a", status="completed"),
        Todo(id="b", title="b", depends_on=("a",)),
        Todo(id="c", title="c", depends_on=("b",)),
    ]
    assert ready_todos(after_a) == {"b"}


def test_ready_diamond_needs_both_parents() -> None:
    """A diamond d←(b,c)←a: d is ready only when BOTH b and c are completed."""
    todos = [
        Todo(id="a", title="a", status="completed"),
        Todo(id="b", title="b", status="completed", depends_on=("a",)),
        Todo(id="c", title="c", depends_on=("a",)),
        Todo(id="d", title="d", depends_on=("b", "c")),
    ]
    assert ready_todos(todos) == {"c"}  # d still blocked on c


def test_ready_ignores_unknown_dep() -> None:
    """A dep referencing a non-existent id is ignored (no permanent deadlock)."""
    todos = [Todo(id="1", title="x", depends_on=("ghost",))]
    assert ready_todos(todos) == {"1"}


def test_ready_cycle_leaves_both_blocked() -> None:
    """A a↔b cycle simply leaves both not-ready (the pass never loops)."""
    todos = [
        Todo(id="a", title="a", depends_on=("b",)),
        Todo(id="b", title="b", depends_on=("a",)),
    ]
    assert ready_todos(todos) == set()


def test_ready_empty_list() -> None:
    """An empty plan has no ready todos."""
    assert ready_todos([]) == set()


def test_ready_excludes_non_pending() -> None:
    """completed / in_progress todos are never 'ready' (ready = next to START)."""
    todos = [
        Todo(id="1", title="x", status="completed"),
        Todo(id="2", title="y", status="in_progress"),
    ]
    assert ready_todos(todos) == set()


# ----- render_active_plan -----------------------------------------------------


def test_render_no_deps_is_byte_identical_to_57140() -> None:
    """With NO dependency anywhere the render matches the Sprint 57.140 flat output."""
    todos = [
        Todo(id="1", title="Research", status="completed"),
        Todo(id="2", title="Draft", status="in_progress"),
        Todo(id="3", title="Review"),
    ]
    expected = (
        "## Active Plan\n"
        "You have an existing task plan from earlier in this task. Continue from "
        "it — do NOT restart. As you finish each step, call `write_todos` again "
        "with the WHOLE updated list to move items to in_progress / completed.\n"
        "\n"
        "- [completed] Research\n"
        "- [in_progress] Draft\n"
        "- [pending] Review"
    )
    assert render_active_plan(todos) == expected


def test_render_annotates_ready_and_blocked() -> None:
    """With deps, pending dependents are annotated (ready) / (blocked by: <titles>)."""
    todos = [
        Todo(id="a", title="Design schema", status="completed"),
        Todo(id="b", title="Write migration", depends_on=("a",)),
        Todo(id="c", title="Run tests", depends_on=("a", "b")),
    ]
    out = render_active_plan(todos)
    assert "Work the steps marked (ready) first" in out
    assert "- [pending] Write migration (ready)" in out
    assert "- [pending] Run tests (blocked by: Write migration)" in out  # a done, b not


def test_render_no_deps_has_no_annotation_line() -> None:
    """A no-dep pending todo carries no (ready)/(blocked) suffix."""
    out = render_active_plan([Todo(id="1", title="Solo task")])
    assert out.endswith("- [pending] Solo task")


# ----- detect_cycles (Sprint 57.162) ------------------------------------------


def test_detect_cycles_none_for_acyclic() -> None:
    """A DAG (no back-edge) reports no cycle members."""
    todos = [
        Todo(id="a", title="A"),
        Todo(id="b", title="B", depends_on=("a",)),
        Todo(id="c", title="C", depends_on=("a", "b")),
    ]
    assert detect_cycles(todos) == set()


def test_detect_cycles_two_node() -> None:
    """A a↔b mutual dependency is a cycle of both nodes."""
    todos = [
        Todo(id="a", title="A", depends_on=("b",)),
        Todo(id="b", title="B", depends_on=("a",)),
    ]
    assert detect_cycles(todos) == {"a", "b"}


def test_detect_cycles_three_node() -> None:
    """A a→c→b→a loop marks all three nodes cyclic."""
    todos = [
        Todo(id="a", title="A", depends_on=("c",)),
        Todo(id="b", title="B", depends_on=("a",)),
        Todo(id="c", title="C", depends_on=("b",)),
    ]
    assert detect_cycles(todos) == {"a", "b", "c"}


def test_detect_cycles_partial_only_the_loop() -> None:
    """Only the nodes in the loop are cyclic; an acyclic sibling is not."""
    todos = [
        Todo(id="a", title="A"),
        Todo(id="b", title="B", depends_on=("c",)),
        Todo(id="c", title="C", depends_on=("b",)),
    ]
    assert detect_cycles(todos) == {"b", "c"}


def test_detect_cycles_ignores_unknown_dep() -> None:
    """A dep on a non-existent id is not a cycle (consistent with ready_todos)."""
    todos = [Todo(id="a", title="A", depends_on=("ghost",))]
    assert detect_cycles(todos) == set()


def test_detect_cycles_self_dep_is_safe() -> None:
    """A directly-constructed self-dependency is dropped, not reported as a cycle."""
    todos = [Todo(id="x", title="X", depends_on=("x",))]
    assert detect_cycles(todos) == set()


def test_detect_cycles_empty() -> None:
    """An empty plan has no cycle."""
    assert detect_cycles([]) == set()


# ----- plan_warnings (Sprint 57.162) ------------------------------------------


def test_plan_warnings_clean_is_empty() -> None:
    """An in-order acyclic plan produces no advisory."""
    todos = [
        Todo(id="a", title="A", status="completed"),
        Todo(id="b", title="B", status="in_progress", depends_on=("a",)),
        Todo(id="c", title="C", depends_on=("b",)),
    ]
    assert plan_warnings(todos) == []


def test_plan_warnings_out_of_order_in_progress() -> None:
    """A dependent marked in_progress before its prerequisite completes → advisory."""
    todos = [
        Todo(id="a", title="Design", status="pending"),
        Todo(id="b", title="Build", status="in_progress", depends_on=("a",)),
    ]
    warnings = plan_warnings(todos)
    assert warnings == ["'Build' is marked in_progress but prerequisite 'Design' is not completed."]


def test_plan_warnings_out_of_order_completed() -> None:
    """A dependent marked completed while its prerequisite is unfinished → advisory."""
    todos = [
        Todo(id="a", title="Design", status="pending"),
        Todo(id="b", title="Build", status="completed", depends_on=("a",)),
    ]
    warnings = plan_warnings(todos)
    assert any("marked completed but prerequisite 'Design'" in w for w in warnings)


def test_plan_warnings_cycle() -> None:
    """A dependency cycle among pending todos → a single cycle advisory."""
    todos = [
        Todo(id="a", title="A", depends_on=("b",)),
        Todo(id="b", title="B", depends_on=("a",)),
    ]
    warnings = plan_warnings(todos)
    assert warnings == [
        "Dependency cycle detected among: A, B — these steps can never become "
        "ready; fix their depends_on."
    ]


def test_plan_warnings_ignores_unknown_prereq() -> None:
    """An out-of-order status against an UNKNOWN prereq id is not flagged."""
    todos = [Todo(id="a", title="A", status="in_progress", depends_on=("ghost",))]
    assert plan_warnings(todos) == []


# ----- render_active_plan cycle branch (Sprint 57.162) ------------------------


def test_render_cycle_annotates_distinctly() -> None:
    """A cyclic pending node renders (blocked by cycle: ...), not plain (blocked by:)."""
    todos = [
        Todo(id="a", title="Alpha", depends_on=("b",)),
        Todo(id="b", title="Beta", depends_on=("a",)),
    ]
    out = render_active_plan(todos)
    assert "- [pending] Alpha (blocked by cycle: Alpha, Beta)" in out
    assert "- [pending] Beta (blocked by cycle: Alpha, Beta)" in out
    # the cycle guidance sentence is present; a normal (blocked by: ...) is NOT used here
    assert "(blocked by cycle: ...)" in out  # instruction mentions the cycle marker
    assert "(blocked by: Alpha)" not in out and "(blocked by: Beta)" not in out


def test_render_non_cycle_block_unchanged() -> None:
    """A normal (non-cyclic) block still renders the plain (blocked by: <title>)."""
    todos = [
        Todo(id="a", title="Design schema", status="completed"),
        Todo(id="b", title="Write migration", depends_on=("a",)),
        Todo(id="c", title="Run tests", depends_on=("b",)),
    ]
    out = render_active_plan(todos)
    assert "- [pending] Write migration (ready)" in out
    assert "- [pending] Run tests (blocked by: Write migration)" in out
    # the instruction text mentions the "(blocked by cycle: ...)" marker, but no
    # todo LINE carries a cycle annotation for an acyclic plan.
    todo_lines = [ln for ln in out.splitlines() if ln.startswith("- [")]
    assert not any("blocked by cycle" in ln for ln in todo_lines)
