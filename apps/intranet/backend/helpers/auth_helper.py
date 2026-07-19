import os
from typing import TypeVar, Callable, Any, cast, Optional
from functools import wraps
from flask import request, jsonify
from models import Employee
from py_errors import UnauthorizedError, ForbiddenError, EmployeeNotFoundError
from py_auth import verify_jwt

F = TypeVar('F', bound=Callable[..., Any])

# ─── Role vocabulary ─────────────────────────────────────────────────
# Canonical role set, mirroring RoleKey in libs/auth/src/roles.ts. Seeding
# works from this list, so a role added here and there is available to every
# tenant. Legacy names ('hr', 'manager', 'call_centre_*') are deliberately
# absent: existing rows are never deleted, but new tenants stop inheriting
# corporate-only roles that the frontend has no permission entry for.
ALL_ROLES: tuple[str, ...] = (
    'staff',
    'company_admin',
    'hr_admin',
    'department_manager',
    'school_admin',
    'lecturer',
    'teacher',
    'guardian',
    'super_admin',
    'it_admin',
)

# ─── Role groups ─────────────────────────────────────────────────────
# The backend's original role names ('hr', 'manager') predate the frontend
# RoleKey set in libs/auth/src/roles.ts, which uses 'hr_admin',
# 'department_manager', 'school_admin', etc. Education tenants seed the newer
# names, corporate tenants may still hold the old ones, so both are listed
# here and guards reference these groups instead of bare literals.
#
# This is a compatibility layer, not the end state: these checks should move to
# permission-based gating that mirrors PERMISSION_MATRIX in libs/auth/src/roles.ts,
# so adding a role never again requires touching every route decorator.
ADMIN_ROLES: tuple[str, ...] = (
    'super_admin',
    'school_admin',
    'company_admin',
    'hr_admin',
    'hr',
)

# Admins plus line managers / heads of department.
MANAGER_ROLES: tuple[str, ...] = ADMIN_ROLES + ('department_manager', 'manager')

def get_token_auth_header() -> str:
    """Obtains the Access Token from the Authorization Header"""
    auth: Optional[str] = request.headers.get("Authorization", None)
    if not auth:
        raise UnauthorizedError(message="Authorization header is expected")

    parts: list[str] = auth.split()
    if parts[0].lower() != "bearer":
        raise UnauthorizedError(message="Authorization header must start with Bearer")
    elif len(parts) == 1 or len(parts) > 2:
        raise UnauthorizedError(message="Authorization header must be Bearer token")

    return parts[1]

def require_auth(f: F) -> F:
    """Decorator to validate the JWT and attach the payload to the request."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        AUTH0_DOMAIN: Optional[str] = os.getenv('AUTH0_DOMAIN')
        AUTH0_AUDIENCE: Optional[str] = os.getenv('AUTH0_AUDIENCE')
        
        if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
            return jsonify({"error": "Auth0 configuration (AUTH0_DOMAIN / AUTH0_AUDIENCE) is missing in backend environment"}), 500
        
        try:
            token: str = get_token_auth_header()
            payload: dict[str, Any] = verify_jwt(token, AUTH0_DOMAIN, AUTH0_AUDIENCE)
            request.user_payload = payload  # type: ignore[attr-defined]
        except UnauthorizedError:
            raise
        except Exception as e:
            raise UnauthorizedError(message=str(e))
        return f(*args, **kwargs)
    return cast(F, decorated)

def roles_required(*required_roles: str) -> Callable[[F], F]:
    """Role Guard Decorator: Blocks route if role doesn't match."""
    def decorator(f: F) -> F:
        @wraps(f)
        @require_auth
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
            auth0_id: str = payload['sub']
            
            employee = Employee.query.filter_by(auth0_id=auth0_id).first()
            if not employee or not employee.role:
                raise EmployeeNotFoundError()
            
            if not employee.is_approved:
                raise ForbiddenError(message="Your account is pending administrator approval.")

            if employee.role.name not in required_roles:
                raise ForbiddenError()
                
            return f(*args, **kwargs)
        return cast(F, decorated_function)
    return decorator