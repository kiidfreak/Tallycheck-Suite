# @omni py_auth (`libs/py_auth`)

Shared **Python** auth helpers reused by every app backend (the JS/Angular side has its
own `@omni/auth`). Today it holds the **Auth0** JWT verification helper.

```python
from py_auth import verify_jwt

payload = verify_jwt(token, domain=AUTH0_DOMAIN, audience=AUTH0_AUDIENCE)
```

`verify_jwt` fetches the tenant's JWKS (cached), matches the token's `kid`, and validates
an RS256 token's signature, audience and issuer. Raises on any failure.

## Use it from a backend

Installed as a local package so backends can `import py_auth`:

```bash
# from a backend dir (e.g. apps/intranet/backend) with its venv active
pip install -e ../../../libs/py_auth
```

In Docker, the image installs it from the build context (see `apps/intranet/backend/Dockerfile`).
