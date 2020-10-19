"""
Main functionality.
"""

import os
import time

import ruamel.yaml
import sniper
from . import shift_time


def main():
    """ The actual running method."""
    pwd = None
    usr = None

    if not os.path.exists("secrets.yaml"):
        raise ValueError("Expected a 'secrets.yaml' file")

    with open("secrets.yaml") as config_file:
        yaml = ruamel.yaml.YAML()
        data = yaml.load(config_file)

        pwd = data.get("password")
        usr = data.get("username")

    if pwd is None:
        raise ValueError("Set the 'password' field in secrets.yaml")
    if usr is None:
        raise ValueError("Set the 'username' field in the secrets.yaml")

    sniper_obj = sniper.ToploggerSniper(usr, pwd)
    check_time = shift_time.TimeSpec(20, 30)
    sniper_obj.check_time("Bovenverdieping", 10, 25, check_time)

    time.sleep(10.0)
    print("retrying")
    sniper_obj.check_time("Bovenverdieping", 10, 20, check_time)


if __name__ == "__main__":
    main()
