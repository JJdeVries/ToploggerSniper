import os
import threading

import ruamel.yaml
from app.sniper import ToploggerSniper
from app.schedule import ScheduleHandler


def update(sniper_obj: ToploggerSniper, sched: ScheduleHandler):
    """ The update method."""
    sched.update()

    for inst in sched.get_dates():
        sniper_obj.update_shift_state(inst)

        if inst.has_update:
            print(inst)
            inst.processed()


def main():
    """ The actual running method."""
    pwd = None
    usr = None
    yaml = ruamel.yaml.YAML()

    # Read in the username / password
    if not os.path.exists("secrets.yaml"):
        raise ValueError("Expected a 'secrets.yaml' file")

    with open("secrets.yaml") as config_file:
        data = yaml.load(config_file)
    pwd = data.get("password")
    usr = data.get("username")
    if pwd is None:
        raise ValueError("Set the 'password' field in secrets.yaml")
    if usr is None:
        raise ValueError("Set the 'username' field in the secrets.yaml")

    # Read in the schedule configuration
    if not os.path.exists("schedule.yaml"):
        raise ValueError("Expected a 'schedule.yaml' file")
    with open("schedule.yaml") as config_file:
        data = yaml.load(config_file)

    sched = ScheduleHandler(data)
    sniper_obj = ToploggerSniper(usr, pwd, sched.gym)

    update_thread = threading.Timer(30.0, update, args=(sniper_obj, sched))

    update_thread.start()
    # update(sniper_obj, sched)
    if update_thread.is_alive():
        input("Press [enter] to stop thread\n")
        update_thread.cancel()
        update_thread.join()


if __name__ == "__main__":
    main()