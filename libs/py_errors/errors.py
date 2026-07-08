from typing import Any, Optional, Tuple
from flask import Response, jsonify
from http import HTTPStatus

# ==========================================================
# ERROR CODES
# Mirrors the ErrorCode enum in the OpenAPI spec.
# ==========================================================
class ErrorCode:
    # Auth
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_NOT_APPROVED = "account_not_approved"
    ACCOUNT_INACTIVE = "account_inactive"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

    # Attendance
    ALREADY_CLOCKED_IN = "already_clocked_in"
    NOT_CLOCKED_IN = "not_clocked_in"
    ATTENDANCE_RECORD_NOT_FOUND = "attendance_record_not_found"

    # Employees / Departments
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    EMPLOYEE_NOT_FOUND = "employee_not_found"
    DEPARTMENT_NOT_FOUND = "department_not_found"
    DEPARTMENT_HAS_EMPLOYEES = "department_has_employees"

    # General
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"
    NOT_FOUND = "not_found"


# ==========================================================
# BASE EXCEPTION
# All custom exceptions inherit from this.
# ==========================================================
class AppError(Exception):
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int,
        details: Optional[str] = None
    ) -> None:
        self.error = error          # ErrorCode constant
        self.message = message      # human-readable, shown to user
        self.status_code = status_code
        self.details = details      # raw exception detail, gated by debug mode

    def write_response(self, debug: bool = False) -> Tuple[Response, int]:
        body: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
            "details": self.details if debug or self.status_code == 422 else None
        }
        return jsonify(body), self.status_code


# ==========================================================
# CONCRETE EXCEPTIONS
# One class per error category.
# ==========================================================
class UnauthorizedError(AppError):
    def __init__(self, message: str = "Missing or invalid token.", details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.TOKEN_INVALID, message, HTTPStatus.UNAUTHORIZED, details)

class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action.", details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.INSUFFICIENT_PERMISSIONS, message, HTTPStatus.FORBIDDEN, details)

class NotFoundError(AppError):
    def __init__(self, error: str = ErrorCode.NOT_FOUND, message: str = "Resource not found.", details: Optional[str] = None) -> None:
        super().__init__(error, message, HTTPStatus.NOT_FOUND, details)

class AlreadyClockedInError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.ALREADY_CLOCKED_IN, "You are already clocked in.", HTTPStatus.CONFLICT, details)

class NotClockedInError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.NOT_CLOCKED_IN, "You are not clocked in.", HTTPStatus.CONFLICT, details)

class EmailExistsError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.EMAIL_ALREADY_EXISTS, "An employee with this email already exists.", HTTPStatus.CONFLICT, details)

class EmployeeNotFoundError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.EMPLOYEE_NOT_FOUND, "Employee not found.", HTTPStatus.NOT_FOUND, details)

class DepartmentNotFoundError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.DEPARTMENT_NOT_FOUND, "Department not found.", HTTPStatus.NOT_FOUND, details)

class DepartmentHasEmployeesError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.DEPARTMENT_HAS_EMPLOYEES, "Cannot delete a department with active employees.", HTTPStatus.CONFLICT, details)

class ValidationError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, "Request body failed validation.", HTTPStatus.UNPROCESSABLE_ENTITY, details)

class InternalError(AppError):
    def __init__(self, details: Optional[str] = None) -> None:
        super().__init__(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred.", HTTPStatus.INTERNAL_SERVER_ERROR, details)