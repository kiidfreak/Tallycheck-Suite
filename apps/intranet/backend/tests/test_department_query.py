"""The descendants CTE, checked by compiling it — no database required.

`descendant_ids_subquery` is what makes "everyone under this campus" a single
round trip. Its depth predicate is also the last line of defence against a cyclic
row: without it a bad edge would recurse until the connection died.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parents[2] / "libs"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from department_routes import descendant_ids_subquery  # noqa: E402


def compiled(root_id: int = 7, **kwargs) -> str:
    query = descendant_ids_subquery(root_id, **kwargs)
    return str(query.compile(compile_kwargs={"literal_binds": True}))


def test_is_a_recursive_cte() -> None:
    assert "WITH RECURSIVE" in compiled()


def test_anchors_on_the_requested_root() -> None:
    assert "departments.id = 7" in compiled(7)


def test_walks_children_via_the_parent_fk() -> None:
    sql = compiled()
    assert "departments.parent_department_id = descendants.id" in sql


def test_carries_a_depth_cap() -> None:
    # The cycle guard. A row loop that reached the database via a restore or a
    # manual edit terminates here instead of hanging the request.
    assert "descendants.depth < 20" in compiled()


@pytest.mark.parametrize("limit", [1, 5, 50])
def test_depth_cap_is_configurable(limit: int) -> None:
    assert f"descendants.depth < {limit}" in compiled(7, max_depth=limit)


def test_selects_only_ids() -> None:
    # Callers use this as an IN subquery, so it must project a single column.
    assert compiled().rstrip().endswith("FROM descendants")
