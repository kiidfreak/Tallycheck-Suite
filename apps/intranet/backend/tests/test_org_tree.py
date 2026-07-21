"""Org-tree helpers. No fixtures, no database, no app context.

These cover the parts most likely to be wrong — cycle detection and depth limits
— and they run on any machine, unlike the suite's `app` fixture which needs
Postgres.
"""

from __future__ import annotations

import pytest

from helpers.org_tree_helper import (
    MAX_DEPTH,
    UNIT_TYPES,
    ancestors,
    assemble_tree,
    depth_of,
    is_valid_unit_type,
    subtree_height,
    violates_depth_limit,
    would_create_cycle,
)

# 1 root
#   2 site
#     3 division
#       4 team
# 5 standalone root
CHAIN = {1: None, 2: 1, 3: 2, 4: 3, 5: None}


class TestAncestors:
    def test_walks_to_the_root(self):
        assert ancestors(CHAIN, 4) == [3, 2, 1]

    def test_root_has_none(self):
        assert ancestors(CHAIN, 1) == []

    def test_terminates_on_a_pre_existing_cycle(self):
        # A cycle can reach the database via a restore or a manual edit. The walk
        # must end rather than hang the request that touched it.
        cyclic = {1: 2, 2: 3, 3: 1}
        assert len(ancestors(cyclic, 1)) < 10


class TestCycleDetection:
    def test_self_parenting(self):
        assert would_create_cycle(CHAIN, 2, 2) is True

    def test_direct_swap(self):
        # The old route check only compared parent_id == id, so this was accepted.
        assert would_create_cycle(CHAIN, 1, 2) is True

    def test_deep_descendant(self):
        # Moving the root under its own great-grandchild.
        assert would_create_cycle(CHAIN, 1, 4) is True

    def test_legitimate_move_is_allowed(self):
        assert would_create_cycle(CHAIN, 5, 3) is False

    def test_detaching_to_root_is_allowed(self):
        assert would_create_cycle(CHAIN, 3, None) is False

    def test_sibling_move_is_allowed(self):
        assert would_create_cycle(CHAIN, 4, 2) is False


class TestDepth:
    @pytest.mark.parametrize("node,expected", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 1)])
    def test_depth_counts_roots_as_one(self, node, expected):
        assert depth_of(CHAIN, node) == expected

    def test_subtree_height(self):
        assert subtree_height(CHAIN, 1) == 4
        assert subtree_height(CHAIN, 3) == 2
        assert subtree_height(CHAIN, 4) == 1

    def test_move_within_the_limit_is_allowed(self):
        assert violates_depth_limit(CHAIN, 5, 4) is False  # depth 4 + height 1 = 5

    def test_move_that_would_breach_the_limit_is_rejected(self):
        deep = {1: None, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
        assert depth_of(deep, 6) == MAX_DEPTH
        assert violates_depth_limit(deep, 6, 6) is True

    def test_accounts_for_the_whole_subtree_not_just_the_node(self):
        # Node 10 alone would fit under 4, but it carries two levels with it.
        branching = {**CHAIN, 10: None, 11: 10, 12: 11}
        assert subtree_height(branching, 10) == 3
        assert violates_depth_limit(branching, 10, 4) is True  # 4 + 3 = 7 > 6


class TestUnitType:
    def test_known_values(self):
        for value in UNIT_TYPES:
            assert is_valid_unit_type(value)

    @pytest.mark.parametrize("value", ["campus", "depot", "ward", "", None, 3, "DEPARTMENT"])
    def test_rejects_everything_else(self, value):
        # The enum is structural on purpose. Vertical nouns like campus/depot are
        # a display concern, mapped in the frontend per org type — putting them
        # here makes every new customer a schema change.
        assert not is_valid_unit_type(value)


class TestAssembleTree:
    def rows(self):
        return [
            {"id": 1, "name": "acme", "parent_department_id": None},
            {"id": 2, "name": "nairobi", "parent_department_id": 1},
            {"id": 3, "name": "engineering", "parent_department_id": 2},
            {"id": 5, "name": "standalone", "parent_department_id": None},
        ]

    def test_nests_children_under_parents(self):
        tree = assemble_tree(self.rows())
        assert [n["id"] for n in tree] == [1, 5]
        assert tree[0]["children"][0]["id"] == 2
        assert tree[0]["children"][0]["children"][0]["id"] == 3

    def test_leaves_get_an_empty_children_list(self):
        tree = assemble_tree(self.rows())
        assert tree[0]["children"][0]["children"][0]["children"] == []

    def test_preserves_other_fields(self):
        tree = assemble_tree(self.rows())
        assert tree[0]["name"] == "acme"

    def test_orphan_is_surfaced_as_a_root(self):
        # A partial or permission-filtered fetch must still render every row it
        # was given, rather than dropping branches whose parent is absent.
        tree = assemble_tree([{"id": 9, "name": "orphan", "parent_department_id": 404}])
        assert [n["id"] for n in tree] == [9]

    def test_cycle_does_not_hang_or_swallow_nodes(self):
        tree = assemble_tree(
            [
                {"id": 1, "name": "a", "parent_department_id": 2},
                {"id": 2, "name": "b", "parent_department_id": 1},
            ]
        )
        assert {n["id"] for n in tree} == {1, 2}

    def test_empty_input(self):
        assert assemble_tree([]) == []

    def test_does_not_mutate_its_input(self):
        rows = self.rows()
        assemble_tree(rows)
        assert "children" not in rows[0]
