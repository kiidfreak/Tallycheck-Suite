import json
import logging
import requests
import jwt
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Simple in-memory cache for JWKS to avoid network calls on every request
_JWKS_CACHE: Optional[dict[str, Any]] = None


def get_rsa_key(domain: str, unverified_header: dict[str, Any]) -> Optional[dict[str, str]]:
    """Fetches the JWKS keys and finds the one matching the token's kid."""
    global _JWKS_CACHE
    jwks_url: str = f'https://{domain}/.well-known/jwks.json'
    
    if _JWKS_CACHE is None:
        logger.info(f'[Auth0] Fetching JWKS from: {jwks_url}')
        _JWKS_CACHE = requests.get(jwks_url, timeout=5).json()

    jwks: dict[str, Any] = _JWKS_CACHE
    rsa_key: Optional[dict[str, str]] = _find_key(jwks, unverified_header['kid'])

    if not rsa_key:
        logger.info('[Auth0] Key ID not in cache. Refetching JWKS...')
        _JWKS_CACHE = requests.get(jwks_url, timeout=5).json()
        jwks = _JWKS_CACHE
        rsa_key = _find_key(jwks, unverified_header['kid'])
        
    return rsa_key


def _find_key(jwks: dict[str, Any], kid: str) -> Optional[dict[str, str]]:
    for key in jwks['keys']:
        if key['kid'] == kid:
            return {
                'kty': key['kty'], 'kid': key['kid'], 'use': key['use'],
                'n': key['n'], 'e': key['e']
            }
    return None


def verify_jwt(token: str, domain: str, audience: str) -> dict[str, Any]:
    """
    Decodes and verifies an Auth0 JWT token.
    Returns the decoded payload if successful, otherwise raises an Exception.
    """
    try:
        unverified_header: dict[str, Any] = jwt.get_unverified_header(token)
        rsa_key: Optional[dict[str, str]] = get_rsa_key(domain, unverified_header)
        
        if rsa_key:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(rsa_key))
            payload: dict[str, Any] = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=audience,
                issuer=f'https://{domain}/',
                leeway=60  # 60s tolerance for clock skew between Auth0 and this server
            )
            return payload
        else:
            raise Exception('Unable to find appropriate key in JWKS.')
            
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired.')
    except Exception as e:
        logger.error(f'[Auth0] Auth error: {e}')
        raise Exception(str(e))
