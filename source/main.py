import os
import ruamel.yaml
import sniper
import shift_time
import time

if __name__ == "__main__":
    pwd = None
    usr = None
    area = None

    month = 10
    day = 25

    if not os.path.exists("secrets.yaml"):
        raise ValueError("Expected a 'secrets.yaml' file")

    with open("secrets.yaml") as fp:
        yaml = ruamel.yaml.YAML()
        data = yaml.load(fp)

        pwd = data.get("password")
        usr = data.get("username")
        area = data.get("area")

    if pwd is None:
        raise ValueError("Set the 'password' field in secrets.yaml")
    if usr is None:
        raise ValueError("Set the 'username' field in the secrets.yaml")

    sniper = sniper.ToploggerSniper(usr, pwd)
    check_time = shift_time.TimeSpec(20, 30)
    sniper.check_time("Bovenverdieping", 10, 25, check_time)

    time.sleep(10.0)
    print("retrying")
    sniper.check_time("Bovenverdieping", 10, 20, check_time)