"""
Time handling for the sniper.
"""


class TimeSpec:
    """ 24 Our time specification."""

    def __init__(self, hour: int, minute: int, am_pm: str = ""):
        self._hour = int(hour)
        self._minute = int(minute)
        if am_pm:
            self.__convert_am_pm(am_pm)

    def __convert_am_pm(self, am_pm: str):
        if am_pm.lower() == "am":
            if self._hour == 12:
                if self.minute == 0:
                    # Special (actually incorrect handling) of exactly midnight.
                    self._hour = 24
                    self._minute = 0
                else:
                    self._hour = 0
        elif am_pm.lower() == "pm":
            if self._hour != 12:
                self._hour += 12
        else:
            raise AttributeError(f"Invalid AM/PM string: '{am_pm}''")

    @property
    def hour(self) -> int:
        """ The hour part."""
        return self._hour

    @property
    def minute(self) -> int:
        """ The minute part."""
        return self._minute

    def __le__(self, other: "TimeSpec") -> bool:
        return self.hour < other.hour or (
            self.hour == other.hour and self.minute <= other.minute
        )

    def __gt__(self, other: "TimeSpec") -> bool:
        return self.hour > other.hour or (
            self.hour == other.hour and self.minute > other.minute
        )

    def __str__(self) -> str:
        return f"{self.hour:0>2}:{self.minute:0>2}"


def time_conversion(input_time: str) -> TimeSpec:
    """Convert a AM/PM time to 24 hours
    :param input_time: (str) A 12 hour time with AM/PM string.
    """
    stripped_time = input_time.strip()
    hour, minute = stripped_time[:-2].split(":")
    am_pm = stripped_time[-2:]
    return TimeSpec(int(hour), int(minute), am_pm)


class ShiftTime:
    """ A shift class, with start and end time."""

    def __init__(self, start_time: str, end_time: str):
        self._start_time: TimeSpec = time_conversion(start_time)
        self._end_time: TimeSpec = time_conversion(end_time)

    def is_time_in_shift(self, rel_time: TimeSpec) -> bool:
        """Check whether a time is within this shift.
        Meaning it is at or after the start time, and before the end time.
        """
        return self._start_time <= rel_time and self._end_time > rel_time

    def __str__(self) -> str:
        return f"{self._start_time} - {self._end_time}"
