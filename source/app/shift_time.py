"""
Time handling for the sniper.
"""
import datetime


def __convert_am_pm(time: datetime.time, am_pm: str) -> datetime.time:
    """Convert a time object with the am/pm notation.
    Note 12:00 AM is converted to 23:59"""
    if am_pm.lower() == "am":
        if time.hour == 12 and time.minute == 00:
            time = datetime.time(23, 59)
    elif am_pm.lower() == "pm":
        if time.hour != 12:
            time = datetime.time(time.hour + 12, time.minute)
    else:
        raise AttributeError(f"Invalid AM/PM string: '{am_pm}''")
    return time


def time_conversion(input_time: str) -> datetime.time:
    """Convert a input string to datetime.time"""
    hour, minute = input_time.split(":")
    # TODO: There could be an am/pm time definition here?
    #       it seems that the side was updated to 24hr time
    return datetime.time(int(hour), int(minute))


class ShiftTime:
    """ A shift class, with start and end time."""

    def __init__(self, start_time: str, end_time: str):
        self._start_time: datetime.time = time_conversion(start_time)
        self._end_time: datetime.time = time_conversion(end_time)

    def is_time_in_shift(self, rel_time: datetime.time) -> bool:
        """Check whether a time is within this shift.
        Meaning it is at or after the start time, and before the end time.
        """
        return self._start_time <= rel_time and self._end_time > rel_time

    def __str__(self) -> str:
        return f"{self._start_time} - {self._end_time}"
