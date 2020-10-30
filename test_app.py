import os
import threading

import ruamel.yaml
from app.toplogger import ToploggerApi
from app.schedule import ScheduleHandler, ShiftState


def update(sniper_obj: ToploggerApi, sched: ScheduleHandler):
    """ The update method."""
    sched.update()

    taken_shifts = sniper_obj.get_reservations()
    for inst in sched.get_dates():
        # First let's see if the shift is already taken.
        for s in taken_shifts:
            if s.area == inst.area and s.is_in(inst.time):
                inst.state = ShiftState.TAKEN
                break
        else:
            # Let's see if the shift is available or taken.
            for s in sniper_obj.get_available_shifts(inst.time, inst.area):
                if s.is_in(inst.time):
                    inst.state = ShiftState.AVAILABLE
                    break
            else:
                inst.state = ShiftState.FULL

    # And let's print all the updates
    for inst in sched.get_dates():
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
    sniper_obj = ToploggerApi()
    sniper_obj.login(usr, pwd)
    sniper_obj.pick_gym(data["gym"])

    update_thread = threading.Timer(30.0, update, args=(sniper_obj, sched))

    # update_thread.start()
    update(sniper_obj, sched)
    if update_thread.is_alive():
        input("Press [enter] to stop thread\n")
        update_thread.cancel()
        update_thread.join()


if __name__ == "__main__":
    main()