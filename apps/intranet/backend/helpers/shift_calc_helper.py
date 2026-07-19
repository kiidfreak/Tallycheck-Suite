from utils.shift_data import ShiftHours

# Last-resort clock-in cutoff offset, in hours after shift start. Used only when
# the org_settings row cannot be read at all. Kept in sync with
# OrgSettings.DEFAULT_CUTOFF_HOURS_AFTER_START.
DEFAULT_CUTOFF_HOURS_AFTER_START = 5

@property  # type: ignore[misc]
def shift_start_hour(self) -> int:
    """Returns the hour (0-23) when this employee's shift starts."""
    if self.shift_hours in (ShiftHours.EARLY_MORN, ShiftHours.EXT_EARLY_MORN):
        return 7
    if self.shift_hours in (ShiftHours.LATE_MORN, ShiftHours.EXT_LATE_MORN):
        return 9
    if self.shift_hours == ShiftHours.CUSTOM and self.custom_shift_start:
        # IMPORTANT: custom_shift_start must be in 24h HH:MM format (e.g. '14:00').
        # This only works correctly if the frontend uses <input type="time">, which
        # natively outputs 24h values — do NOT use a 12-hour picker.
        h, _ = self.custom_shift_start.split(':')
        return int(h)
    return 7  # safe fallback

@property  # type: ignore[misc]
def shift_end_hour(self) -> int:
    """Returns the hour (0-23) when this employee's shift ends.
    Since all shifts are exactly 10 hours, this is always shift_start_hour + 10.
    """
    return self.shift_start_hour + 10

@property  # type: ignore[misc]
def shift_cutoff_hour(self) -> int:
    """Returns the clock-in cutoff hour. Employees cannot clock in after this
    point; they must contact HR.

    Resolution order, most specific first:
      1. checkin_cutoff_hour — a manager-set override on this employee
      2. shift start + OrgSettings.checkin_cutoff_hours_after_start (tenant default)
      3. shift start + 5h — used only when the settings row cannot be read
         (e.g. a tenant schema predating the org_settings table), so attendance
         never breaks on a missing settings row.
    """
    if self.checkin_cutoff_hour is not None:
        return self.checkin_cutoff_hour

    try:
        # Imported lazily: models.py star-imports this module, so a top-level
        # import here would be circular.
        from models import OrgSettings
        offset = OrgSettings.get().checkin_cutoff_hours_after_start
    except Exception:
        offset = DEFAULT_CUTOFF_HOURS_AFTER_START

    return self.shift_start_hour + offset

@property  # type: ignore[misc]
def shift_duration_hours(self) -> float:
    """Work-day length in hours — derived purely from shift_type.
    - extended → 9.5 h (570 min) for ALL shift_hours windows, including custom
    - standard → 10.0 h (600 min) for ALL shift_hours windows, including custom
    """
    from utils.shift_data import ShiftType
    if self.shift_type == ShiftType.EXT:
        return 9.5
    return 10.0
