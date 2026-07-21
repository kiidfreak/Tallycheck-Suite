"""Zone validation helpers. No fixtures, no database."""

from __future__ import annotations

import pytest

from helpers.zone_helper import (
    MAX_CODE_LENGTH,
    MAX_NAME_LENGTH,
    ZONE_TYPES,
    is_valid_zone_type,
    normalise_name,
    validate_capacity,
    validate_code,
    validate_name,
)


class TestZoneType:
    def test_known_values(self):
        for value in ZONE_TYPES:
            assert is_valid_zone_type(value)

    @pytest.mark.parametrize("value", ["Room", "office", "", None, 7, "loading bay"])
    def test_rejects_everything_else(self, value):
        assert not is_valid_zone_type(value)


class TestName:
    def test_trims_and_collapses_whitespace(self):
        assert normalise_name("  Loading   Bay 3 ") == "Loading Bay 3"

    def test_preserves_case(self):
        # Zone names are NOT slugified. A zone name is a label read off a wall,
        # and slugifying it would reintroduce the lossy round trip that forced
        # display_name onto departments.
        assert validate_name("Ward 2B") == "Ward 2B"
        assert validate_name("iCU Annex") == "iCU Annex"

    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_rejects_empty(self, value):
        with pytest.raises(ValueError, match="required"):
            validate_name(value)

    def test_rejects_overlong(self):
        with pytest.raises(ValueError, match="exceed"):
            validate_name("x" * (MAX_NAME_LENGTH + 1))

    def test_accepts_exactly_max_length(self):
        assert len(validate_name("x" * MAX_NAME_LENGTH)) == MAX_NAME_LENGTH


class TestCode:
    def test_none_stays_none(self):
        assert validate_code(None) is None

    def test_blank_becomes_none(self):
        assert validate_code("   ") is None

    def test_trims(self):
        assert validate_code(" LB-3 ") == "LB-3"

    def test_rejects_overlong(self):
        with pytest.raises(ValueError, match="exceed"):
            validate_code("x" * (MAX_CODE_LENGTH + 1))


class TestCapacity:
    def test_none_is_allowed(self):
        assert validate_capacity(None) is None

    def test_zero_is_allowed(self):
        assert validate_capacity(0) == 0

    def test_positive(self):
        assert validate_capacity(30) == 30

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="negative"):
            validate_capacity(-1)

    @pytest.mark.parametrize("value", ["30", 3.5, [1]])
    def test_rejects_non_integers(self, value):
        with pytest.raises(ValueError, match="whole number"):
            validate_capacity(value)

    def test_rejects_booleans(self):
        # bool subclasses int in Python, so True would otherwise sail through as
        # a capacity of 1.
        with pytest.raises(ValueError, match="whole number"):
            validate_capacity(True)
