"""
Module handling the schedule configuration.
"""
import typing
import datetime
import calendar
import enum
from collections import defaultdict

import shift_time

DaySchedule = typing.Dict[int, typing.List[shift_time.TimeSpec]]
MonthSchedule = typing.Dict[int, DaySchedule]


class ShiftState(enum.Enum):
    """ The possible states for a shift."""

    AVAILABLE = 1
    FULL = 2
    TAKEN = 3
    UNKNOWN = 4


class ScheduleInstance:
    """ A single instance in of the schedule."""

    def __init__(
        self, datetime_spec: datetime.datetime, area: typing.Optional[str] = None
    ):
        self._datetime = datetime_spec
        self._area = area
        self._state: ShiftState = ShiftState.UNKNOWN
        self._statechange: bool = False

    def processed(self):
        """ Call this method once a statechange was processed."""
        self._statechange = False

    @property
    def time(self):
        """ The time of this instance."""
        return self._datetime

    @property
    def has_update(self) -> bool:
        """ True if a statechange happened."""
        return self._statechange

    @property
    def state(self) -> ShiftState:
        """ The current state."""
        return self._state

    @state.setter
    def state(self, new_state: ShiftState):
        """ Set the new state."""
        if self.state != new_state:
            self._state = new_state
            self._statechange = True


class ScheduleHandler:
    """ Obtain the schedule configuration and get the relevant timespecs."""

    def __init__(self, config):
        self.__plan_advance = config.get("days", 6)
        self._configs: typing.Dict[str, typing.List[shift_time.TimeSpec]] = defaultdict(
            list
        )

        self.__read_config(config["timespec"])

        self.__current_specs: typing.List[ScheduleInstance] = []
        self.__last_updateday = datetime.datetime.now()

    def get_dates(self) -> typing.Generator[ScheduleInstance, None, None]:
        """ Get the current dates that are not yet taken."""
        for inst in self.__current_specs:
            if not inst.state == ShiftState.TAKEN:
                yield inst

    def update(self):
        """ Update the schedule."""
        # First we should clear the passed times.
        today = datetime.datetime.now()

        # Remove any instances that have passed in time.
        self.__current_specs[:] = [x for x in self.__current_specs if x >= today]

        # Let's generate new specs if necessary
        generate_day = today + datetime.timedelta(days=self.__plan_advance)
        while self.__last_updateday.day != generate_day:
            self.__last_updateday += datetime.timedelta(days=1)

            self.__current_specs += self._generate_specs(self.__last_updateday)

    def _generate_specs(self, day: datetime.datetime) -> typing.List[ScheduleInstance]:
        dayname = calendar.day_name[day.weekday()].lower()
        ret_list = []

        for timespec in self._configs.get(dayname, []):
            timing = datetime.datetime.combine(day.date(), timespec)
            # TODO: We should get this area string from somewhere!
            ret_list.append(ScheduleInstance(timing, "Bovenverdieping"))
        return ret_list

    def __read_config(self, config: dict):
        """ Read the configuration into the class."""
        for day in calendar.day_name:
            day = day.lower()
            # We allow both the full day name (eg. monday) as the shortcut (eg. mon)
            input_list = config.get(day, []) + config.get(day[:3], [])

            for spec in input_list:
                new_spec = shift_time.TimeSpec(spec["hour"], spec.get("minute", 0))
                new_spec.area = spec["area"]
                self._configs[day].append(new_spec)
