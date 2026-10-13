"""
Central configuration for the Kindle dashboard.

Only non-secret settings live here. Secrets (the Google Calendar iCal URL and
the OpenWeatherMap API key) are read from environment variables / GitHub
Actions secrets - never hard-code them here.

Edit the values below to taste. Each one is documented inline.
"""

import os


def _env(name: str, default: str) -> str:
    """
    Read an env var, but treat an empty/whitespace value as 'not set'.

    This matters on GitHub Actions: an unset secret or variable is passed to the
    step as an empty string, which would otherwise clobber our sensible default
    (e.g. an empty TIMEZONE would crash ZoneInfo).
    """
    value = os.environ.get(name, "")
    value = value.strip()
    return value if value else default


# --- Display / device -------------------------------------------------------
# Paperwhite 4 (2018) panel size, portrait, in pixels.
WIDTH = 1072
HEIGHT = 1448

# Where the finished PNG is written. The GitHub Action publishes this folder.
# Using an unguessable slug keeps your schedule private on a public Pages site.
# Set OUTPUT_SLUG as a secret to override "dashboard".
OUTPUT_DIR = _env("OUTPUT_DIR", "public")
OUTPUT_SLUG = _env("OUTPUT_SLUG", "dashboard")

# --- Localisation -----------------------------------------------------------
# IANA timezone name. The runner is UTC, so this converts everything to your
# local time. Rochester, MN is US Central time.
TIMEZONE = _env("TIMEZONE", "America/Chicago")

# Text shown as the place name on the weather panel (purely cosmetic).
LOCATION_LABEL = _env("LOCATION_LABEL", "Rochester, MN")

# Units: "metric" -> Celsius, "imperial" -> Fahrenheit.
UNITS = _env("UNITS", "imperial")

# --- Weather ----------------------------------------------------------------
# Query the weather by city name (simplest) OR by coordinates (most precise).
# If OWM_LAT and OWM_LON are both set, coordinates win; otherwise OWM_CITY is used.
# Defaults below are Rochester, MN coordinates (avoids confusion with Rochester, NY).
OWM_CITY = _env("OWM_CITY", "Rochester,MN,US")
OWM_LAT = _env("OWM_LAT", "44.0121")   # Rochester, MN
OWM_LON = _env("OWM_LON", "-92.4802")  # Rochester, MN

# --- Calendar ---------------------------------------------------------------
# How many upcoming events to show, and how far ahead to look (in days).
MAX_EVENTS = int(_env("MAX_EVENTS", "5"))
LOOKAHEAD_DAYS = int(_env("LOOKAHEAD_DAYS", "7"))


# --- Secrets (read from environment) ----------------------------------------
def get_ical_url() -> str:
    """Google Calendar 'Secret address in iCal format'. Required for events."""
    return _env("ICAL_URL", "")


def get_owm_key() -> str:
    """OpenWeatherMap API key. Required for weather."""
    return _env("OWM_API_KEY", "")
