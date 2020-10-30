import requests
import typing
import enum
import logging
import datetime
from collections import namedtuple

from requests import api
from requests.models import encode_multipart_formdata

URL = "https://api.toplogger.nu"

_LOGGER = logging.getLogger(__name__)


class _ApiPath(enum.Enum):
    LOGIN = URL + "/users/sign_in.json"
    RESERVATIONS = URL + "/v1/gyms/{}/reservations"
    ALL_GYMS = URL + "/v1/gyms"
    SHIFTS = URL + "/v1/gyms/{}/slots"
    AREAS = URL + "/v1/gyms/{}/reservation_areas"


def get_datetime(string_input: str) -> datetime.datetime:
    """ Convert a string to datetime. Note that for now all timezone info is stripped off."""
    # TODO Handle timezones?
    # We simply use only the date + HH:MM time spec.
    date_str = string_input.split(".", 2)[0]
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


class ClimbShift:
    def __init__(self, json_req: dict, area=""):
        # TODO: Some handling if values are not available?
        self._area = area
        if "start_at" in json_req:
            self._start = get_datetime(json_req["start_at"])
        else:
            self._start = get_datetime(json_req["slot_start_at"])

        if "start_at" in json_req:
            self._end = get_datetime(json_req["end_at"])
        else:
            self._end = get_datetime(json_req["slot_end_at"])

        # If possible we determine the area from the json data
        if "reservation_area" in json_req:
            self._area = json_req["reservation_area"]["name"]

    def is_in(self, time_inst: datetime.datetime) -> bool:
        return self._start <= time_inst and self._end > time_inst

    @property
    def area(self) -> str:
        return self._area

    def __str__(self) -> str:
        return f"Climbshift at {self._area} on {self._start:%A %d %B} from {self._start:%H:%M} till {self._end:%H:%M}"


class ToploggerApi:
    def __init__(self):
        self._gym_id: typing.Optional[int] = None
        self._email: typing.Optional[str] = None
        self._token: typing.Optional[str] = None
        self._session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        # First let's try to login
        r = self._session.post(
            _ApiPath.LOGIN.value,
            json={"user": {"email": username, "password": password}},
        )

        if r.status_code != 200:
            return False

        # We can save the username, and autorization token.
        self._email = username
        self._token = r.json()["authentication_token"]
        # TODO: If we save the password, we could login if the token expires.
        return True

    def pick_gym(self, gym: str) -> bool:
        """Which gym should we check?.
        returns true if the gym is valid.
        """
        r = self._session.get(_ApiPath.ALL_GYMS.value)
        json_data = r.json()

        for gym_inst in json_data:
            if gym_inst["name"].lower() == gym.lower():
                self._gym_id = gym_inst["id"]
                return True
        return False

    def get_reservations(self) -> typing.List[ClimbShift]:
        if self._gym_id is None or self._token is None:
            return []

        r = self._session.get(
            _ApiPath.RESERVATIONS.value.format(self._gym_id), headers=self.auth_header
        )

        return [ClimbShift(data) for data in r.json()]

    def get_area_id(self, area: str) -> typing.Optional[int]:
        if self._gym_id is None:
            _LOGGER.warn("The gym idea should be set!")
            return None
        r = self._session.get(_ApiPath.AREAS.value.format(self._gym_id))

        for check_area in r.json():
            if check_area["name"].lower() == area.lower():
                return check_area["id"]

        return None

    def get_available_shifts(
        self, date: datetime.date, area: str = ""
    ) -> typing.List[ClimbShift]:
        """ Get the shifts with open spots on a certain day."""
        if self._gym_id is None:
            return []

        # TODO: We should find the mapping reservation_id to string!
        payload: typing.Dict[str, typing.Any] = {
            "slim": "true",
            "date": date.strftime("%Y-%m-%d"),
        }

        if area:
            # Let's try to find the correct area.
            id = self.get_area_id(area)
            if id is None:
                _LOGGER.warn(f"Area '{area}' could not be found")
            else:
                payload["reservation_area_id"] = id

        r = self._session.get(
            _ApiPath.SHIFTS.value.format(self._gym_id), params=payload
        )

        return [
            ClimbShift(shift, area)
            for shift in r.json()
            if shift["spots_booked"] < shift["spots"]
        ]

    @property
    def auth_header(self) -> dict:
        """ The authentication header if a login has been done, otherwise an empty dict."""
        if self._email and self._token:
            return {"X-USER-EMAIL": self._email, "X-USER-TOKEN": self._token}
        return {}

    @property
    def gym_id_set(self) -> bool:
        return self._gym_id is not None

    @property
    def logged_in(self) -> bool:
        return self._token is not None
