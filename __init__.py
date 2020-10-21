""" The main module for the home assistant integration.
Here the sniper can send home assistant events, and be configured using a home assistant instance.
"""
DOMAIN = "ToploggerSniper"


def setup(hass, config):
    def my_service(call):
        hass.states.set(f"{DOMAIN}.Hello_World", "Works!")

    hass.services.register(DOMAIN, "demo", my_service)
    hass.states.set(f"{DOMAIN}.Hello_World", "unknown")