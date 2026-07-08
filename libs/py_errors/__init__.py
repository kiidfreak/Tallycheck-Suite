"""py_errors — shared Python error classes for Omni app backends."""

from .errors import (
    AppError,
    ErrorCode,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    AlreadyClockedInError,
    NotClockedInError,
    EmailExistsError,
    EmployeeNotFoundError,
    DepartmentNotFoundError,
    DepartmentHasEmployeesError,
    ValidationError,
    InternalError,
)

__all__ = [
    "AppError",
    "ErrorCode",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "AlreadyClockedInError",
    "NotClockedInError",
    "EmailExistsError",
    "EmployeeNotFoundError",
    "DepartmentNotFoundError",
    "DepartmentHasEmployeesError",
    "ValidationError",
    "InternalError",
]