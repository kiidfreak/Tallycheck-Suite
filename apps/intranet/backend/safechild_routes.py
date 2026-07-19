from typing import Tuple
from datetime import datetime, timezone, timedelta
import random
import uuid
import hmac
import hashlib
import time
import os
from collections import defaultdict
from flask import Blueprint, request, Response, jsonify
from models import (
    db, Child, Guardian, ChildGuardian, PickupToken, Employee,
    SundaySchoolClass, ClassTeacher,
)
from helpers.auth_helper import require_auth, ADMIN_ROLES
from py_errors import ValidationError, NotFoundError, EmployeeNotFoundError
from py_success import SuccessResponse

safechild_bp = Blueprint('safechild', __name__, url_prefix='/safechild')

# In-memory rate limiting map: IP -> list of request timestamps
verification_attempts = defaultdict(list)

# HMAC signing key (loaded from env or fallback for local development)
HMAC_SECRET = os.getenv('SAFECHILD_HMAC_SECRET', 'tcheck_super_secret_safechild_key_2026')

def check_rate_limit(client_ip: str, limit: int = 5, window: int = 60) -> bool:
    """Lightweight sliding-window rate limiter for code verification."""
    now = time.time()
    # Keep only timestamps within the current window
    verification_attempts[client_ip] = [t for t in verification_attempts[client_ip] if now - t < window]
    if len(verification_attempts[client_ip]) >= limit:
        return False
    verification_attempts[client_ip].append(now)
    return True

def generate_signed_qr(token_id: str) -> str:
    """Generate a tamper-proof QR code payload using HMAC-SHA256."""
    sig = hmac.new(
        HMAC_SECRET.encode('utf-8'),
        token_id.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"{token_id}.{sig}"

def verify_signed_qr(payload: str) -> Tuple[bool, str]:
    """Verify QR code payload signature. Returns (is_valid, token_id)."""
    try:
        parts = payload.split('.')
        if len(parts) != 2:
            return False, ""
        token_id, signature = parts
        expected_sig = hmac.new(
            HMAC_SECRET.encode('utf-8'),
            token_id.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(expected_sig, signature):
            return True, token_id
        return False, ""
    except Exception:
        return False, ""


def current_employee() -> Employee:
    """The Employee behind the current token."""
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get('sub')).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()
    return employee


def scoped_class_ids(employee: Employee):
    """Class ids this user may see, or None for unrestricted.

    Sunday School runs separate classes with their own teachers, so a teacher
    sees only the children in classes they are assigned to -- never the whole
    church roster. Admins are unrestricted.

    A teacher with no assignment gets an empty list, not everything: failing
    closed is the right default when the roster is children's data.
    """
    role = employee.role.name if employee.role else None
    if role in ADMIN_ROLES:
        return None
    if role == 'teacher':
        return [link.class_id for link in employee.class_links]
    return None


def teacher_classes(employee: Employee):
    """SundaySchoolClass rows assigned to this employee."""
    return (
        SundaySchoolClass.query
        .join(ClassTeacher, ClassTeacher.class_id == SundaySchoolClass.id)
        .filter(ClassTeacher.teacher_id == employee.id)
        .order_by(SundaySchoolClass.name)
        .all()
    )


@safechild_bp.route('/my-classes', methods=['GET'])
@require_auth
def get_my_classes() -> Tuple[Response, int]:
    """Sunday School classes assigned to the authenticated teacher."""
    employee = current_employee()
    classes = teacher_classes(employee)

    return SuccessResponse(
        message="Classes retrieved successfully",
        data=[
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "child_count": Child.query.filter_by(class_id=c.id, is_active=True).count(),
            }
            for c in classes
        ],
        status_code=200
    ).write_response()


@safechild_bp.route('/class-history', methods=['GET'])
@require_auth
def get_class_history() -> Tuple[Response, int]:
    """Drop-off / pickup history for the classes this user can see.

    Optional ?days=N (default 30, max 365) bounds the window.
    """
    employee = current_employee()
    allowed = scoped_class_ids(employee)

    try:
        days = int(request.args.get('days', 30))
    except (TypeError, ValueError):
        raise ValidationError(details="days must be an integer.")
    if not 1 <= days <= 365:
        raise ValidationError(details="days must be between 1 and 365.")

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        PickupToken.query
        .join(Child, Child.id == PickupToken.child_id)
        .filter(PickupToken.created_at >= since)
    )
    if allowed is not None:
        if not allowed:
            return SuccessResponse(
                message="No classes assigned", data=[], status_code=200
            ).write_response()
        query = query.filter(Child.class_id.in_(allowed))

    tokens = query.order_by(PickupToken.created_at.desc()).limit(500).all()

    return SuccessResponse(
        message="Class history retrieved successfully",
        data=[
            {
                "id": str(t.id),
                "child_id": str(t.child_id),
                "child_name": t.child.name if t.child else None,
                "class_name": t.child.sunday_class.name if t.child and t.child.sunday_class else t.child.group_name if t.child else None,
                "guardian_name": t.guardian.name if t.guardian else None,
                "dropped_off_at": t.created_at.isoformat() if t.created_at else None,
                "picked_up_at": t.verified_at.isoformat() if t.verified_at else None,
                "status": t.status,
            }
            for t in tokens
        ],
        status_code=200
    ).write_response()


@safechild_bp.route('/children', methods=['GET'])
@require_auth
def get_children() -> Tuple[Response, int]:
    """Children visible to the caller.

    Teachers see only their assigned classes; admins see the whole roster.
    """
    employee = current_employee()
    allowed = scoped_class_ids(employee)

    query = Child.query
    if allowed is not None and len(allowed) > 0:
        query = query.filter(Child.class_id.in_(allowed))

    children = query.order_by(Child.name).all()
    serialized = []
    for child in children:
        guardians = [
            {
                "id": str(link.guardian.id),
                "name": link.guardian.name,
                "phone": link.guardian.phone,
                "relation": link.guardian.relation,
                "is_primary": link.is_primary,
                "photo_url": link.guardian.photo_url
            }
            for link in child.guardian_links
        ]
        active_token = PickupToken.query.filter_by(child_id=child.id, status='pending').first()
        serialized.append({
            "id": str(child.id),
            "name": child.name,
            "group_name": child.group_name,
            "class_id": child.class_id,
            "class_name": child.sunday_class.name if child.sunday_class else child.group_name,
            "photo_url": child.photo_url,
            "is_active": child.is_active,
            "status": "checked_in" if active_token else "absent",
            "check_in_time": active_token.created_at.isoformat() if active_token else None,
            "guardians": guardians
        })
    return SuccessResponse(
        message="Children retrieved successfully",
        data=serialized,
        status_code=200
    ).write_response()


@safechild_bp.route('/drop-off', methods=['POST'])
@require_auth
def drop_off_child() -> Tuple[Response, int]:
    """Log a child drop-off, generating a single-use PIN & signed QR pickup token."""
    data = request.json or {}
    child_id_str = data.get('child_id')
    guardian_id_str = data.get('guardian_id')
    employee_id_str = data.get('employee_id')

    if not child_id_str:
        raise ValidationError(details="child_id is required")

    try:
        child_id = uuid.UUID(child_id_str)
    except ValueError:
        raise ValidationError(details="Invalid child_id format")

    child = Child.query.get(child_id)
    if not child:
        raise NotFoundError(message="Child not found")

    guardian_id = None
    if guardian_id_str:
        try:
            guardian_id = uuid.UUID(guardian_id_str)
        except ValueError:
            raise ValidationError(details="Invalid guardian_id format")
        guardian = Guardian.query.get(guardian_id)
        if not guardian:
            raise NotFoundError(message="Guardian not found")

    # Invalidate any existing active tokens for this child
    active_tokens = PickupToken.query.filter_by(child_id=child_id, status='pending').all()
    for tok in active_tokens:
        tok.status = 'expired'

    # Generate single-use credentials
    token_id = uuid.uuid4()
    qr_payload = generate_signed_qr(str(token_id))
    pin = f"{random.randint(1000, 9999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

    created_by_id = None
    if employee_id_str:
        try:
            created_by_id = uuid.UUID(employee_id_str)
        except ValueError:
            pass

    token = PickupToken(
        id=token_id,
        child_id=child_id,
        guardian_id=guardian_id,
        token_type='both',
        qr_payload=qr_payload,
        pin=pin,
        expires_at=expires_at,
        status='pending',
        created_by=created_by_id
    )

    db.session.add(token)
    db.session.commit()

    return SuccessResponse(
        message="Child drop-off logged successfully",
        data={
            "token_id": str(token.id),
            "child_name": child.name,
            "pin": pin,
            "qr_payload": qr_payload,
            "expires_at": expires_at.isoformat()
        },
        status_code=201
    ).write_response()


@safechild_bp.route('/pickup/verify', methods=['POST'])
@require_auth
def verify_pickup() -> Tuple[Response, int]:
    """Verify a pickup token (QR or PIN) and release the child."""
    # Apply Rate Limiting (IP-based) to prevent PIN brute force
    client_ip = request.remote_addr or 'unknown'
    if not check_rate_limit(client_ip, limit=5, window=60):
        return jsonify({
            "status": "error",
            "message": "Too many verification attempts. Please wait 60 seconds."
        }), 429

    data = request.json or {}
    code = data.get('code')
    verifier_id_str = data.get('verifier_id')

    if not code:
        raise ValidationError(details="Verification code or PIN is required")

    token = None

    # Handle PIN input (4-digit code)
    if len(code) == 4 and code.isdigit():
        token = PickupToken.query.filter_by(pin=code, status='pending').first()
        if not token:
            # Check if it was recently used/expired
            any_token = PickupToken.query.filter_by(pin=code).order_by(PickupToken.created_at.desc()).first()
            if any_token:
                if any_token.status == 'verified':
                    raise ValidationError(details=f"This PIN was already used for pickup at {any_token.verified_at.isoformat()}")
                if any_token.status == 'expired' or any_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                    raise ValidationError(details="This pickup PIN has expired")
            raise NotFoundError(message="Invalid or unrecognized verification PIN")
            
    # Handle signed QR code input
    else:
        # Validate HMAC signature first to prevent query pollution
        is_valid, token_id_str = verify_signed_qr(code)
        if not is_valid:
            raise ValidationError(details="Invalid or tampered QR code payload signature")

        try:
            token_id = uuid.UUID(token_id_str)
        except ValueError:
            raise ValidationError(details="Invalid QR payload token ID format")

        token = PickupToken.query.filter_by(id=token_id, status='pending').first()
        if not token:
            any_token = PickupToken.query.get(token_id)
            if any_token:
                if any_token.status == 'verified':
                    raise ValidationError(details=f"This QR code was already used for pickup at {any_token.verified_at.isoformat()}")
                if any_token.status == 'expired' or any_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                    raise ValidationError(details="This pickup QR code has expired")
            raise NotFoundError(message="Unrecognized or inactive pickup token")

    # Check expiration timestamp
    if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        token.status = 'expired'
        db.session.commit()
        raise ValidationError(details="This pickup token has expired")

    # Perform release
    verifier_id = None
    if verifier_id_str:
        try:
            verifier_id = uuid.UUID(verifier_id_str)
        except ValueError:
            pass

    token.status = 'verified'
    token.verified_by = verifier_id
    token.verified_at = datetime.now(timezone.utc)
    db.session.commit()

    child = token.child
    guardian = token.guardian

    return SuccessResponse(
        message=f"Pickup verified successfully! {child.name} released.",
        data={
            "child_name": child.name,
            "child_photo": child.photo_url,
            "guardian_name": guardian.name if guardian else "Authorized Guardian",
            "guardian_relation": guardian.relation if guardian else None,
            "verified_at": token.verified_at.isoformat()
        },
        status_code=200
    ).write_response()
