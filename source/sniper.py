import webbot
import os
import ruamel.yaml
import calendar
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

    b = webbot.Browser()

    b.go_to("https://app.toplogger.nu")
    b.type(usr, into='Email')
    b.type(pwd, into="Password")
    b.click('SIGN IN')

    time.sleep(5.0)
    # Now we navigate to the reservations page
    b.click(classname='v-input__slot')
    b.click('Reservations')

    time.sleep(5.0)
    # Now select the area (if applicable)
    if area is not None:
        # First expand the dropdown list.
        # Hopefully this will always work?
        b.click(tag='div', classname='v-input__slot')
        b.click(area, tag='div')

    # Navigate to the correct date
    # TODO: Year picking!
    # TODO: We could check the current selected date
    #       or filter on if we request a different month than the current month?
    b.click(tag='div', classname='v-date-picker-header')
    month_name = calendar.month_name[month][:3].upper()
    b.click(month_name, tag='div')

    b.click(str(day), tag='div')
