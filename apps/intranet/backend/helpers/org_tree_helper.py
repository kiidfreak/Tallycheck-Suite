"""Org-tree logic, as pure functions over plain dicts.

Departments form a self-referencing tree (`parent_department_id`). The risky
parts — cycle detection, depth limits, flat-to-nested assembly — live here rather
than in the route handlers so they can be tested without a database, an app
context or Postgres. `tests/conftest.py` cannot build an app locally (Organization
is bound to the `public` schema, which SQLite has no concept of), so anything
that needs a fixture is effectively untested outside CI. These need none.

Cycle prevention is enforced here and in the routes, not by a database trigger:
a trigger is another per-schema object that `migrations/env.py` would have to fan
out across every tenant schema, and that fan-out is the riskiest part of the
whole migration story.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

# Deepest tree we accept: root > region > site > division > department > team.
# Anything deeper is far more likely to be a data-entry mistake than a real org.
MAX_DEPTH = 6

# Independent hard stop used when walking a chain. Guards against a cycle that
# reached the database some other way — a restore, a manual SQL edit, a bug in an
# older build — so a traversal terminates instead of hanging a request.
_WALK_LIMIT = 1000

UNIT_TYPES: tuple[str, ...] = (
    "root",
    "region",
    "site",
    "division",
    "department",
    "team",
)

DEFAULT_UNIT_TYPE = "department"


def is_valid_unit_type(value: Any) -> bool:
    return isinstance(value, str) and value in UNIT_TYPES


def ancestors(edges: Mapping[int, Optional[int]], node: int) -> list[int]:
    """Ids from `node`'s parent up to its root, nearest first.

    Stops on a repeat, so a pre-existing cycle yields a finite list rather than
    looping forever.
    """
    # `seen` deliberately starts empty rather than containing `node`. Seeding it
    # would stop the walk the moment it came back round to `node`, so a node
    # caught in a cycle would never appear in its own ancestor chain — and
    # `would_create_cycle` reads exactly that to detect one.
    seen: set[int] = set()
    chain: list[int] = []
    current = edges.get(node)
    steps = 0
    while current is not None and steps < _WALK_LIMIT:
        if current in seen:
            break
        seen.add(current)
        chain.append(current)
        current = edges.get(current)
        steps += 1
    return chain


def would_create_cycle(
    edges: Mapping[int, Optional[int]], node: int, new_parent: Optional[int]
) -> bool:
    """True if re-parenting `node` under `new_parent` closes a loop.

    Covers self-parenting and the longer case the routes previously missed: a
    node cannot be moved under one of its own descendants. The old check only
    compared `parent_id == id`, so A->B->A was accepted.
    """
    if new_parent is None:
        return False
    if new_parent == node:
        return True
    # Walking up from the prospective parent must never reach the node itself.
    return node in ancestors(edges, new_parent)


def depth_of(edges: Mapping[int, Optional[int]], node: int) -> int:
    """Depth of `node`, roots being 1."""
    return len(ancestors(edges, node)) + 1


def subtree_height(edges: Mapping[int, Optional[int]], node: int) -> int:
    """Levels in `node`'s subtree, counting `node` itself as 1."""
    children: dict[int, list[int]] = {}
    for child, parent in edges.items():
        if parent is not None:
            children.setdefault(parent, []).append(child)

    height = 0
    frontier = [node]
    seen: set[int] = set()
    while frontier and height < _WALK_LIMIT:
        height += 1
        nxt: list[int] = []
        for nid in frontier:
            if nid in seen:
                continue
            seen.add(nid)
            nxt.extend(children.get(nid, []))
        frontier = nxt
    return height


def violates_depth_limit(
    edges: Mapping[int, Optional[int]], node: int, new_parent: Optional[int]
) -> bool:
    """True if the move would push any part of the subtree past MAX_DEPTH.

    Checks the whole subtree, not just the node: moving a three-level branch
    under a deep parent can breach the limit even when the node itself would sit
    comfortably inside it.
    """
    parent_depth = 0 if new_parent is None else depth_of(edges, new_parent)
    return parent_depth + subtree_height(edges, node) > MAX_DEPTH


def assemble_tree(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Flat rows -> nested `children` lists, roots first.

    Rows need `id` and `parent_department_id`; everything else is copied through.
    A row whose parent is missing from the input is treated as a root, so a
    permission-filtered or partial fetch still renders instead of silently
    dropping branches. Any node caught in a cycle is likewise surfaced as a root
    rather than disappearing.
    """
    nodes: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    for row in rows:
        node = dict(row)
        node["children"] = []
        nodes[node["id"]] = node
        order.append(node["id"])

    edges = {nid: nodes[nid].get("parent_department_id") for nid in order}

    roots: list[dict[str, Any]] = []
    for nid in order:
        parent_id = edges.get(nid)
        in_cycle = parent_id is not None and nid in ancestors(edges, nid)
        if parent_id is None or parent_id not in nodes or in_cycle:
            roots.append(nodes[nid])
        else:
            nodes[parent_id]["children"].append(nodes[nid])
    return roots
