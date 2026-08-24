"""Constants for the Iliad Italia integration."""

from datetime import timedelta

DOMAIN = "iliad_ita"
PLATFORMS = ["sensor", "binary_sensor", "button"]

CONF_NAME = "name"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DATA_THRESHOLD_GB = "data_threshold_gb"
CONF_DATA_THRESHOLD_PERCENT = "data_threshold_percent"
CONF_CREDIT_THRESHOLD_EUR = "credit_threshold_eur"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"

DEFAULT_NAME = "SIM Iliad"
DEFAULT_DATA_THRESHOLD_GB = 10.0
DEFAULT_DATA_THRESHOLD_PERCENT = 10.0
DEFAULT_CREDIT_THRESHOLD_EUR = 5.0
DEFAULT_UPDATE_INTERVAL_HOURS = 6
MIN_UPDATE_INTERVAL_HOURS = 1
MAX_UPDATE_INTERVAL_HOURS = 24

LOGIN_URL = "https://www.iliad.it/account/login"
CONSUMPTION_URL = "https://www.iliad.it/account/consumi-e-credito"

UPDATE_INTERVAL = timedelta(hours=DEFAULT_UPDATE_INTERVAL_HOURS)
