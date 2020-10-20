"""
The sniper class for the Toplogger webapp.
"""
import typing
import calendar
import time
from functools import wraps

import webbot
from . import shift_time, schedule

_TIMESPLIT = "—"
_PRINT_TIMING = True


def timeit(method: typing.Callable):
    """ Time a method."""

    @wraps(method)
    def timed(*args, **kwargs):
        tic = time.perf_counter()
        ret_val = method(*args, **kwargs)
        toc = time.perf_counter()

        if _PRINT_TIMING:
            print(f"{method.__name__} took: {toc - tic:.4} seconds")
        return ret_val

    return timed


class ToploggerSniper:
    """ The sniper class."""

    def __init__(self, username: str = "", password: str = "", gym: str = ""):
        self.__browser: webbot.Browser = webbot.Browser(showWindow=True)
        self.__browser.go_to("https://app.toplogger.nu")

        self.__usr = username
        self.__pwd = password
        self.__gym = gym

        # Intially we login
        self._do_login()
        # self._pick_gym()

    def _pick_gym(self):
        """ Let's pick the correct gym. Can be used anonymously"""
        self.__browser.click(classname="v-input__slot")
        self.__browser.click("Select Gym")

        # Now wait till gyms loaded
        time.sleep(0.5)
        self.__browser.click(self.__gym)
        time.sleep(0.5)
        # TODO: How to check that the gym is available / chosen
        self.__browser.click("SELECT GYM")

    @property
    def browser(self):
        return self.__browser

    def _check_login(self) -> bool:
        """ Check whether we're currently logged in."""
        # Open the sidebar.
        self.__browser.click(classname="v-input__slot")
        signed_in = False

        relevent_txts = [
            i.text
            for i in self.__browser.find_elements(
                "Sign", tag="div", classname="v-list-item__title", loose_match=False
            )
        ]

        if any([i == "Sign out" for i in relevent_txts]):
            self.browser.click("Dashboard")
            signed_in = True
        elif any([i == "Sign in" for i in relevent_txts]):
            self.browser.click("Sign in")
            signed_in = False
        else:
            print("UNKNOWN SIGNIN STATUS!")

        # Close the sidebar
        return signed_in

    def _do_login(self):
        """ Log into the toplogger site. In principle not necessary to check availability."""
        # TODO: Probably we should check that the login/password fields are present.
        self._check_login()

        self.__browser.type(self.__usr, into="Email")
        self.__browser.type(self.__pwd, into="Password")
        self.__browser.click("SIGN IN")
        # TODO: How to check if the login was succesfull?

        # sleep till page is loaded
        # TODO: We should use some condition to wait till some webelement is present.
        time.sleep(2.0)
        self._check_login()
        time.sleep(0.5)

    @timeit
    def _goto_reservations(self, area: str = None):
        # Let's check if we're already in reservations
        tic = time.perf_counter()
        header_title = self.__browser.find_elements(
            "Reservations", tag="div", classname="v-toolbar__title", loose_match=False
        )[0]
        toc = time.perf_counter()
        print(f"This took {toc - tic:.4}")

        if header_title.text != "Reservations":
            # Now we navigate to the reservations page
            print("Going to reservation page")
            self.__browser.click(classname="v-input__slot")
            self.__browser.click("Reservations")
            time.sleep(0.5)

        # Now select the area (if applicable)
        if area is not None:
            # First expand the dropdown list.
            tic = time.perf_counter()
            curr_elems = self.__browser.find_elements(
                area, tag="div", classname="v-select__selection", loose_match=False
            )
            toc = time.perf_counter()
            print(f"Getting area took {toc - tic}")

            if not curr_elems or curr_elems[0].text != area:
                if curr_elems:
                    print(f"Changing area {curr_elems[0].text} into {area}")
                # Hopefully this will always work?
                self.__browser.click(tag="div", classname="v-input__slot")
                self.__browser.click(area, tag="div")

    @timeit
    def _goto_day(self, month: int, day: int):
        # Navigate to the correct date
        # TODO: Year picking!
        # TODO: We could check the current selected date
        #       or filter on if we request a different month than the current month?
        self.__browser.click(tag="div", classname="v-date-picker-header")
        month_name = calendar.month_name[month][:3].upper()
        time.sleep(0.1)
        self.__browser.click(month_name, tag="div")
        time.sleep(0.1)
        self.__browser.click(str(day), tag="div")

    @timeit
    def _find_shifts(self) -> typing.List[shift_time.ShiftTime]:
        # Let's get all the time elements
        shifts = []
        for shift in self.__browser.find_elements(" " + _TIMESPLIT + " "):
            # Only use the first line
            timespec = shift.text.splitlines()[0]
            start, end = timespec.split(_TIMESPLIT)
            shifts.append(shift_time.ShiftTime(start, end))
        return shifts

    @timeit
    def _find_shift_states(self) -> typing.List[schedule.ShiftState]:
        states: typing.List[schedule.ShiftState] = []

        for book_string in self.__browser.find_elements(
            "ook", tag="button", loose_match=False
        ):
            if book_string.text == "BOOK":
                states.append(schedule.ShiftState.AVAILABLE)
            elif book_string.text == "FULLY BOOKED":
                states.append(schedule.ShiftState.FULL)
            elif book_string.text == "CANCEL BOOKING":
                # We've already taken this slot
                states.append(schedule.ShiftState.TAKEN)
            else:
                print(f"UNKNOWN!! '{book_string.text}''")
                states.append(schedule.ShiftState.UNKNOWN)

        return states

    def update_shift_state(self, sched_inst: schedule.ScheduleInstance):
        """ Update the shift state of the given schedule instance."""
        # Should we check whether we're still logged in? / gym chosen
        self._goto_reservations(sched_inst.area)

        self._goto_day(sched_inst.time.month, sched_inst.time.day)

        shifts = self._find_shifts()
        states = self._find_shift_states()

        if len(shifts) != len(states):
            print(
                f"Unexpected unequal amount of bookings {len(shifts)} vs {len(states)}"
            )

        for state, shift in zip(states, shifts):
            if shift.is_time_in_shift(sched_inst.time.time()):
                sched_inst.state = state
                break
        else:
            # There is no shift for the configured time
            sched_inst.state = schedule.ShiftState.UNKNOWN
