"""
Entry point: fetch weather + calendar, render the dashboard PNG, and save it.

Run locally:
    pip install -r requirements.txt
    ICAL_URL=... OWM_API_KEY=... python generate.py

In GitHub Actions the same environment variables are supplied from secrets.
The image is written to <OUTPUT_DIR>/<OUTPUT_SLUG>.png (defaults: public/dashboard.png).
"""

from __future__ import annotations

import os
import traceback

import config
from src import calendar_events, render, weather


def _save(img, out_dir: str, slug: str) -> str:
    """Write the image as an 8-bit grayscale PNG and return its path."""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{slug}.png")
    img.save(out_path, format="PNG", optimize=True)
    return out_path


def main() -> None:
    # Step 1: gather data (each degrades gracefully on failure).
    print("Fetching weather...")
    w = weather.fetch_weather(config)
    print("  weather ok" if w.get("ok") else f"  weather failed: {w.get('error')}")

    print("Fetching calendar...")
    e = calendar_events.fetch_events(config)
    print("  calendar ok" if e.get("ok") else f"  calendar failed: {e.get('error')}")

    # Step 2: render the image.
    print("Rendering image...")
    img = render.render(config, w, e)

    # Step 3: save it.
    out_path = _save(img, config.OUTPUT_DIR, config.OUTPUT_SLUG)
    print(f"Saved {out_path} ({config.WIDTH}x{config.HEIGHT})")


if __name__ == "__main__":
    # If anything unexpected goes wrong, publish a fallback image showing the
    # error instead of failing the build. This keeps the Kindle fed with an
    # image and makes the real error visible in the published PNG.
    try:
        main()
    except Exception:  # noqa: BLE001
        tb = traceback.format_exc()
        print(tb)
        try:
            img = render.render_error(config, tb)
            out_path = _save(img, config.OUTPUT_DIR, config.OUTPUT_SLUG)
            print(f"Saved ERROR image to {out_path}")
        except Exception:  # noqa: BLE001 - last resort, don't mask original
            traceback.print_exc()
