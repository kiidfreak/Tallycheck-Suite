from enum import Enum

class ShiftType(str, Enum):
    """Whether the employee works a 5-day (standard) or 6-day (extended) work week."""
    STD = 'standard'
    EXT = 'extended'


class ShiftHours(str, Enum):
    """The employee's daily working hours window."""
    EARLY_MORN = '7am-5pm'   # 07:00 – 17:00
    LATE_MORN  = '9am-7pm'   # 09:00 – 19:00
    EXT_EARLY_MORN = '7am-430pm' # 07:00 - 16:30
    EXT_LATE_MORN = '9am-630pm'  # 09:00 - 18:30
    CUSTOM     = 'custom'    # times stored in custom_shift_start / custom_shift_end
