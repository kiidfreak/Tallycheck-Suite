from typing import Tuple
from datetime import datetime, timezone, timedelta
import random
import uuid
from flask import Blueprint, request, Response
from models import db, Child, Guardian, ChildGuardian, PickupToken
from helpers.auth_helper import require_auth
from py_errors import ValidationError, NotFoundError
from py_success import SuccessResponse

safechild_bp = Blueprint('safechild', __name__, url_prefix='/safechild')

@safechild_bp.route('/children', methods=['GET'])
@require_auth
def get_children() -> Tuple[Response, int]:
    """Retrieve all children in the active tenant."""
    children = Child.query.order_by(Child.name).all()
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
        serialized.append({
            "id": str(child.id),
            "name": child.name,
            "group_name": child.group_name,
            "photo_url": child.photo_url,
            "is_active": child.is_active,
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
    """Log a child drop-off, generating a single-use PIN & QR pickup token."""
    data = request.json or {}
    child_id_str = data.get('child_id')
    guardian_id_str = data.get('guardian_id')
    employee_id_str = data.get('employee_id')

    if not child_id_str:
        raise ValidationError(message="child_id is required")

    try:
        child_id = uuid.UUID(child_id_str)
    except ValueError:
        raise ValidationError(message="Invalid child_id format")

    child = Child.query.get(child_id)
    if not child:
        raise NotFoundError(message="Child not found")

    guardian_id = None
    if guardian_id_str:
        try:
            guardian_id = uuid.UUID(guardian_id_str)
        except ValueError:
            raise ValidationError(message="Invalid guardian_id format")
        guardian = Guardian.query.get(guardian_id)
        if not guardian:
            raise NotFoundError(message="Guardian not found")

    # Invalidate any existing active tokens for this child
    active_tokens = PickupToken.query.filter_by(child_id=child_id, status='pending').all()
    for tok in active_tokens:
        tok.status = 'expired'

    # Generate single-use credentials
    pin = f"{random.randint(1000, 9999)}"
    qr_payload = f"tcheck_qr_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

    created_by_id = None
    if employee_id_str:
        try:
            created_by_id = uuid.UUID(employee_id_str)
        except ValueError:
            pass

    token = PickupToken(
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
    data = request.json or {}
    code = data.get('code')
    verifier_id_str = data.get('verifier_id')

    if not code:
        raise ValidationError(message="Verification code or PIN is required")

    # Look up token by QR or PIN
    if len(code) == 4 and code.isdigit():
        token = PickupToken.query.filter_by(pin=code, status='pending').first()
    else:
        token = PickupToken.query.filter_by(qr_payload=code, status='pending').first()

    if not token:
        # Check if code exists but was already verified/expired
        any_token = PickupToken.query.filter((PickupToken.pin == code) | (PickupToken.qr_payload == code)).order_by(PickupToken.created_at.desc()).first()
        if any_token:
            if any_token.status == 'verified':
                raise ValidationError(message=f"This code was already used for pickup at {any_token.verified_at.isoformat()}")
            if any_token.status == 'expired' or any_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise ValidationError(message="This pickup token has expired")
        raise NotFoundError(message="Invalid or unrecognized verification code")

    # Check expiration
    if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        token.status = 'expired'
        db.session.commit()
        raise ValidationError(message="This pickup token has expired")

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
