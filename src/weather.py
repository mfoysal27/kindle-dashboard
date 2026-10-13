"""
Weather fetching via OpenWeatherMap (free 2.5 endpoints, no card required).

We use two calls:
  - /data/2.5/weather   -> current conditions
  - /data/2.5/forecast  -> 3-hour steps, from which we derive a short outlook

Everything is wrapped in try/except so a weather outage never blocks the rest
of the dashboard; callers get a dict with an "ok" flag.
"""

from __future__ import annotations

import requests

BASE = "https://api.openweathermap.org/data/2.5"
TIMEOUT = 20  # seconds


def _location_params(config) -> dict:
    """Build the lat/lon or city query for OpenWeatherMap."""
    if config.OWM_LAT and config.OWM_LON:
        return {"lat": config.OWM_LAT, "lon": config.OWM_LON}
    return {"q": config.OWM_CITY}


def fetch_weather(config) -> dict:
    """
    Return a normalised weather dict:
      {
        "ok": bool,
        "temp": float, "feels_like": float,
        "temp_min": float, "temp_max": float,
        "description": str, "main": str,
        "forecast": [ {"label": "6 PM", "temp": float, "main": str}, ... ],
        "units_symbol": "C" | "F",
      }
    On failure, {"ok": False, "error": "..."}.
    """
    key = config.get_owm_key()
    if not key:
        return {"ok": False, "error": "OWM_API_KEY not set"}

    params = {"appid": key, "units": config.UNITS}
    params.update(_location_params(config))
    symbol = "F" if config.UNITS == "imperial" else "C"

    try:
        # Step 1: current conditions.
        cur = requests.get(f"{BASE}/weather", params=params, timeout=TIMEOUT)
        cur.raise_for_status()
        c = cur.json()

        # Step 2: short forecast (next few 3-hour steps).
        fc = requests.get(f"{BASE}/forecast", params=params, timeout=TIMEOUT)
        fc.raise_for_status()
        forecast = _summarise_forecast(fc.json(), config, steps=4)

        return {
            "ok": True,
            "temp": round(c["main"]["temp"]),
            "feels_like": round(c["main"]["feels_like"]),
            "temp_min": round(c["main"]["temp_min"]),
            "temp_max": round(c["main"]["temp_max"]),
            "description": c["weather"][0]["description"].title(),
            "main": c["weather"][0]["main"],
            "forecast": forecast,
            "units_symbol": symbol,
        }
    except Exception as exc:  # noqa: BLE001 - we want to degrade gracefully
        return {"ok": False, "error": str(exc)}


def _summarise_forecast(data: dict, config, steps: int = 4) -> list[dict]:
    """Turn the 3-hour forecast list into a few compact labelled points."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(config.TIMEZONE)
    out = []
    for item in data.get("list", [])[:steps]:
        when = datetime.fromtimestamp(item["dt"], tz)
        out.append(
            {
                "label": when.strftime("%-I %p") if _supports_dash() else when.strftime("%I %p").lstrip("0"),
                "temp": round(item["main"]["temp"]),
                "main": item["weather"][0]["main"],
            }
        )
    return out


def _supports_dash() -> bool:
    """`%-I` works on Linux (the GitHub runner) but not on Windows."""
    import platform

    return platform.system() != "Windows"
