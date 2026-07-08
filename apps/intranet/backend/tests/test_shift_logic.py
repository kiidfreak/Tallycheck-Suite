import pytest
from models import Employee
from helpers.shift_calc_helper import shift_duration_hours
from utils.shift_data import ShiftType, ShiftHours
from py_errors import ValidationError
from helpers.employees_helper import _validate_shift_fields

def test_shift_duration_hours():
    emp_standard = Employee(shift_type=ShiftType.STD)
    assert emp_standard.shift_duration_hours == 10.0

    emp_extended = Employee(shift_type=ShiftType.EXT)
    assert emp_extended.shift_duration_hours == 9.5

def test_validate_shift_fields_standard_custom():
    # 600 minutes (10 hours) is valid for standard
    body = {
        'shift_hours': 'custom',
        'shift_type': 'standard',
        'custom_shift_start': '08:00',
        'custom_shift_end': '18:00'
    }
    # Should not raise
    _validate_shift_fields(body)

def test_validate_shift_fields_standard_invalid():
    # 570 minutes (9.5 hours) should be invalid for standard
    body = {
        'shift_hours': 'custom',
        'shift_type': 'standard',
        'custom_shift_start': '08:00',
        'custom_shift_end': '17:30'
    }
    with pytest.raises(ValidationError) as exc:
        _validate_shift_fields(body)
    assert exc.value.details is not None
    assert "exactly 10 hours" in exc.value.details
    assert "standard" in exc.value.details

def test_validate_shift_fields_extended_custom():
    # 570 minutes (9.5 hours) is valid for extended
    body = {
        'shift_hours': 'custom',
        'shift_type': 'extended',
        'custom_shift_start': '08:00',
        'custom_shift_end': '17:30'
    }
    # Should not raise
    _validate_shift_fields(body)

def test_validate_shift_fields_extended_invalid():
    # 600 minutes (10 hours) should be invalid for extended
    body = {
        'shift_hours': 'custom',
        'shift_type': 'extended',
        'custom_shift_start': '08:00',
        'custom_shift_end': '18:00'
    }
    with pytest.raises(ValidationError) as exc:
        _validate_shift_fields(body)
    assert exc.value.details is not None
    assert "exactly 9 hours 30 minutes" in exc.value.details
    assert "extended" in exc.value.details
