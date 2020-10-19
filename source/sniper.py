import typing
import webbot
import calendar
import shift_time
import time

_TIMESPLIT = "—"


class ToploggerSniper:
    def __init__(self, username: str, password: str):
        self.__browser: webbot.Browser = webbot.Browser(showWindow=True)
        self.__browser.go_to("https://app.toplogger.nu")

        self.__usr = username
        self.__pwd = password

        # Intially we login
        self._do_login()

    def _do_login(self):
        # TODO: Probably we should check that the login/password fields are present.
        self.__browser.type(self.__usr, into="Email")
        self.__browser.type(self.__pwd, into="Password")
        self.__browser.click("SIGN IN")
        # TODO: How to check if the login was succesfull?

        # sleep till page is loaded
        # TODO: We should use some condition to wait till some webelement is present.
        time.sleep(5.0)

    def _goto_reservations(self, area: str = None):
        # Let's check if we're already in reservations
        header_title = self.__browser.find_elements(
            tag="div", classname="v-toolbar__title"
        )[0]
        if header_title.text == "Reservations":
            print("Already in reservations")
        else:
            # Now we navigate to the reservations page
            self.__browser.click(classname="v-input__slot")
            self.__browser.click("Reservations")
            time.sleep(0.5)

        # Now select the area (if applicable)
        if area is not None:
            # First expand the dropdown list.
            # Hopefully this will always work?
            self.__browser.click(tag="div", classname="v-input__slot")
            self.__browser.click(area, tag="div")

    def _goto_day(self, month: int, day: int):
        # Navigate to the correct date
        # TODO: Year picking!
        # TODO: We could check the current selected date
        #       or filter on if we request a different month than the current month?
        self.__browser.click(tag="div", classname="v-date-picker-header")
        month_name = calendar.month_name[month][:3].upper()
        self.__browser.click(month_name, tag="div")
        self.__browser.click(str(day), tag="div")

    def _find_shifts(self) -> typing.List[shift_time.ShiftTime]:
        # Let's get all the time elements
        shifts = []
        for shift in self.__browser.find_elements(" " + _TIMESPLIT + " "):
            # Only use the first line
            timespec = shift.text.splitlines()[0]
            start, end = timespec.split(_TIMESPLIT)
            shifts.append(shift_time.ShiftTime(start, end))
        return shifts

    def _find_available(self) -> typing.List[bool]:
        availables: typing.List[bool] = []
        for book_string in self.__browser.find_elements("ook"):
            if book_string.text == "BOOK":
                availables.append(True)
            elif book_string.text == "FULLY BOOKED":
                availables.append(False)
            else:
                print(f"UNKNOWN!! {book_string.text}")
                availables.append(False)

        return availables

    def check_time(
        self, area: str, month: int, day: int, check_time: shift_time.ShiftTime
    ):
        # Should we check whether we're still logged in?
        self._goto_reservations(area)
        self._goto_day(month, day)

        shifts = self._find_shifts()
        bookings = self._find_available()

        if len(shifts) != len(bookings):
            print(
                f"Unexpected unequal amount of bookings {len(shifts)} vs {len(bookings)}"
            )

        for idx, shift in enumerate(shifts):
            if shift.is_time_in_shift(check_time):
                print_str = "POSSIBLE" if bookings[idx] else "taken :-("
                print(f"The relevant shift is: {shift} which is : {print_str}")
