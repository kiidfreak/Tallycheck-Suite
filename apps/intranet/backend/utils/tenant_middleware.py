import logging
import jwt
from flask import request, g
from models import db, Organization

logger = logging.getLogger(__name__)

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
    host = request.headers.get("Host", "")
    parts = host.split(".")
    if len(parts) > 2 and parts[0] not in ("www", "api", "localhost", "127"):
        return parts[0], "hostname"

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
            g.tenant_id = org.id
            g.schema_name = org.schema_name
            
            # SQL Injection Protection: validate schema name characters
            if not org.schema_name.isalnum() and '_' not in org.schema_name:
                logger.error(f"[TenantMiddleware] Malformed schema name: {org.schema_name}")
                raise ValueError("Invalid schema name")
                
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
