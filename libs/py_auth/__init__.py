"""py_auth — shared Python auth helpers reused across app backends.

Currently: Auth0 RS256/JWKS verification (moved from the omni repo's
shared/auth/python/auth0.py).
"""

from .auth0 import get_rsa_key, verify_jwt

__all__ = ["verify_jwt", "get_rsa_key"]
