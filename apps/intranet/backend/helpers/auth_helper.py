import os
from typing import TypeVar, Callable, Any, cast, Optional
from functools import wraps
from flask import request, jsonify
from models import Employee
from py_errors import UnauthorizedError, ForbiddenError, EmployeeNotFoundError
from py_auth import verify_jwt

F = TypeVar('F', bound=Callable[..., Any])

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