"""Zone validation, as pure functions.

Same reasoning as helpers/org_tree_helper.py: the rules live here so they can be
tested without a database, an app context or Postgres.
"""

from __future__ import annotations

from typing import Any, Optional

ZONE_TYPES: tuple[str, ...] = (
    "room",
    "classroom",
    "hall",
    "entrance",
    "gate",
    "loading_bay",
    "storage",
    "ward",
    "yard",
    "general",
)

DEFAULT_ZONE_TYPE = "general"

MAX_NAME_LENGTH = 120
MAX_CODE_LENGTH = 50


def is_valid_zone_type(value: Any) -> bool:
    return isinstance(value, str) and value in ZONE_TYPES


def normalise_name(raw: Any) -> str:
    """Zone names are stored as typed, only trimmed and whitespace-collapsed.

    Unlike Department.name these are NOT slugified. A zone name is a label a
    human reads off a wall — "Loading Bay 3", "Ward 2B" — and slugifying it would
    reintroduce the lossy round trip that forced `display_name` onto departments.
    """
    return " ".join(str(raw).split())


def validate_capacity(value: Any) -> Optional[int]:
    """Capacity is optional; when present it must be a non-negative integer."""
    if value is None:
        return None
    # bool is an int subclass in Python, and `True` is not a capacity.
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("capacity must be a whole number of people, or null.")
    if value < 0:
        raise ValueError("capacity cannot be negative.")
    return value


def validate_name(raw: Any) -> str:
    name = normalise_name(raw) if raw is not None else ""
    if not name:
        raise ValueError("Zone name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Zone name cannot exceed {MAX_NAME_LENGTH} characters.")
    return name


def validate_code(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    code = normalise_name(raw)
    if not code:
        return None
    if len(code) > MAX_CODE_LENGTH:
        raise ValueError(f"Zone code cannot exceed {MAX_CODE_LENGTH} characters.")
    return code
