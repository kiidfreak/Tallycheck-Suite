import logging
import os
import re
import jwt
from flask import request, g
from models import db, Organization

logger = logging.getLogger(__name__)

# Schema names are interpolated into `SET search_path`, so they are restricted to
# a strict allowlist. Matches what seed_org.py generates: tenant_<lowercased id>.
SCHEMA_NAME_RE = re.compile(r"[a-z0-9_]+")

# Only hosts under one of these resolve a tenant from their subdomain. Override
# with a comma-separated TENANT_BASE_DOMAINS for staging or a second brand.
TENANT_BASE_DOMAINS = tuple(
    d.strip().lower()
    for d in os.environ.get("TENANT_BASE_DOMAINS", "tallycheck.co.ke").split(",")
    if d.strip()
)

# Reserved labels that are infrastructure, never tenants.
RESERVED_SUBDOMAINS = frozenset({"www", "api", "app", "admin", "staging", "localhost"})

def get_tenant_from_request():
    """
    Extracts the tenant identifier (org_id, domain, or subdomain) from the request:
    1. Authorization header (JWT claims)
    2. Request headers (X-Tenant-Subdomain)
    3. Hostname subdomain (e.g. acme.tallycheck.co.ke)
    """
    # 1. Check JWT token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Decode the token unverified to extract tenant metadata before formal auth verification
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            # Auth0 standard Organization ID claim
            org_id = unverified_payload.get("org_id")
            if org_id:
                return org_id, "jwt_org_id"
                
            # Fallback to custom claim
            custom_org = unverified_payload.get("https://tallycheck.co.ke/org_id")
            if custom_org:
                return custom_org, "jwt_custom_org"
        except Exception as e:
            logger.debug(f"[TenantMiddleware] Unverified token decode failed: {e}")

    # 2. Check custom HTTP header
    subdomain_header = request.headers.get("X-Tenant-Subdomain")
    if subdomain_header:
        return subdomain_header, "header"

    # 3. Check Hostname subdomain
    #
    # Matched against an explicit list of base domains rather than a part-count
    # heuristic. `len(parts) > 2` is wrong for every ccSLD: "tallycheck.co.ke"
    # is three parts, so the apex domain resolved as a tenant named "tallycheck"
    # and would have hijacked any org that ever claimed that subdomain.
    host = request.headers.get("Host", "").split(":")[0].strip().lower()
    for base in TENANT_BASE_DOMAINS:
        if host.endswith(f".{base}"):
            label = host[: -(len(base) + 1)]
            if label and "." not in label and label not in RESERVED_SUBDOMAINS:
                return label, "hostname"
            break

    return None, None

def set_tenant_schema():
    """
    Flask before_request handler to set the tenant schema context
    for the current request database session.
    """
    # Skip healthcheck, hello, or command execution requests
    if request.endpoint in ('hello', 'health_check', 'seed_db') or request.path.startswith('/static'):
        return

    tenant_identifier, source = get_tenant_from_request()
    
    if not tenant_identifier:
        g.tenant_id = None
        g.schema_name = "public"
        db.session.execute(db.text("SET search_path TO public"))
        return

    # Query the global organizations table in the public schema
    # Because db.session is scoped, we can search using the Organization model
    try:
        org = Organization.query.filter(
            (Organization.id == tenant_identifier) | 
            (Organization.domain == tenant_identifier) |
            (Organization.schema_name == f"tenant_{tenant_identifier.lower()}")
        ).first()
        
        if org and org.is_active:
            # SQL injection protection: the schema name is interpolated into a
            # SET statement below, so it must be validated as a strict allowlist
            # BEFORE it is used and before it is trusted onto `g`.
            if not SCHEMA_NAME_RE.fullmatch(org.schema_name or ""):
                logger.error(f"[TenantMiddleware] Malformed schema name: {org.schema_name!r}")
                raise ValueError("Invalid schema name")

            g.tenant_id = org.id
            g.schema_name = org.schema_name

            # Set search path to isolated tenant schema with public schema fallback
            db.session.execute(db.text(f'SET search_path TO "{org.schema_name}", public'))
            logger.info(f"[TenantMiddleware] Switched search_path to {org.schema_name} (Tenant: {org.name}) via {source}")
        else:
            # Fallback to public if tenant resolution is inactive or not found
            g.tenant_id = None
            g.schema_name = "public"
            db.session.execute(db.text("SET search_path TO public"))
            logger.warning(f"[TenantMiddleware] Active organization not found for identifier '{tenant_identifier}' via {source}. Defaulted to public schema.")
            
    except Exception as e:
        logger.error(f"[TenantMiddleware] Error during tenant resolution: {e}")
        # Default to public schema to prevent catastrophic failure of app
        db.session.execute(db.text("SET search_path TO public"))
        g.tenant_id = None
        g.schema_name = "public"
