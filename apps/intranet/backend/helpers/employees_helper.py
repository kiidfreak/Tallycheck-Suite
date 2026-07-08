from typing import Any, Optional
from utils.shift_data import *
from py_errors import ValidationError

def _validate_shift_fields(body: dict[str, Any]) -> None:
    """Validate shift_type, shift_hours and custom times. Raises ValidationError on bad input."""
    shift_type = body.get('shift_type')
    if shift_type is not None and shift_type not in ShiftType._value2member_map_:
        raise ValidationError(details=f"shift_type must be one of {[e.value for e in ShiftType]}")

    shift_hours = body.get('shift_hours')
    if shift_hours is not None and shift_hours not in ShiftHours._value2member_map_:
        raise ValidationError(details=f"shift_hours must be one of {[e.value for e in ShiftHours]}")

    if shift_hours == ShiftHours.CUSTOM.value:
        start: Optional[str] = body.get('custom_shift_start')
        end: Optional[str] = body.get('custom_shift_end')
        if not start or not end:
            raise ValidationError(details="custom_shift_start and custom_shift_end are required for custom shifts")
        try:
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
        except (ValueError, AttributeError):
            raise ValidationError(details="custom_shift_start and custom_shift_end must be in HH:MM 24-hour format")
        shift_type_val = body.get('shift_type', 'standard')
        expected_minutes = 570 if shift_type_val == 'extended' else 600
        expected_label = '9 hours 30 minutes' if shift_type_val == 'extended' else '10 hours'
        if (eh * 60 + em) - (sh * 60 + sm) != expected_minutes:
            raise ValidationError(details=f"Custom shift must be exactly {expected_label} for a {shift_type_val} shift")
