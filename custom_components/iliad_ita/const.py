"""Constants for the Iliad Italia integration."""

from datetime import timedelta

DOMAIN = "iliad_ita"
PLATFORMS = ["sensor", "button"]

CONF_NAME = "name"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_NAME = "SIM Iliad"

LOGIN_URL = "https://www.iliad.it/account/login"
CONSUMPTION_URL = "https://www.iliad.it/account/consumi-e-credito"

UPDATE_INTERVAL = timedelta(hours=6)
