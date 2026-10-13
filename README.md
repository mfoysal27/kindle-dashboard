# Kindle Dashboard (calendar + weather + clock)

A clock, weather, and your next calendar events rendered as a single grayscale
PNG sized for a **Kindle Paperwhite 4 (1072 × 1448)**. A free hourly **GitHub
Action** builds the image and publishes it to GitHub Pages; the Kindle downloads
that one image and shows it as its sleep screen via the **Online Screensaver**
KUAL extension.

Nothing runs on the Kindle except downloading a picture, so the fragile parts
(HTTPS, recurring-event expansion) happen in the cloud.

```
GitHub Action (hourly) ──► generate.py ──► public/<slug>.png ──► GitHub Pages
                                                                     │
                                            Kindle Online Screensaver ◄┘ (downloads on a timer)
```

## 1. Local test (optional)

```bash
pip install -r requirements.txt

# Linux/macOS
ICAL_URL="https://calendar.google.com/.../basic.ics" \
OWM_API_KEY="your_key" \
TIMEZONE="America/Chicago" \
OWM_CITY="Chicago,US" \
UNITS="imperial" \
python generate.py

# Windows PowerShell
$env:ICAL_URL="..."; $env:OWM_API_KEY="..."; python generate.py
```

The image appears at `public/dashboard.png`.

## 2. Secrets you need

- **ICAL_URL** — Google Calendar → the calendar's **Settings → Integrate
  calendar → Secret address in iCal format**. Keeps the calendar private.
- **OWM_API_KEY** — a free key from <https://openweathermap.org/api>.

## 3. GitHub setup

1. Create a repo and push these files.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. **Settings → Secrets and variables → Actions → Secrets**: add `ICAL_URL`,
   `OWM_API_KEY`, and (recommended) a random `OUTPUT_SLUG` so your image URL is
   unguessable.
4. **Variables** (same page, non-secret): optionally set `TIMEZONE`,
   `LOCATION_LABEL`, `UNITS`, `OWM_CITY` (or `OWM_LAT`/`OWM_LON`), `MAX_EVENTS`,
   `LOOKAHEAD_DAYS`.
5. Run the workflow once from the **Actions** tab.

Your image URL will be:

```
https://<username>.github.io/<repo>/<OUTPUT_SLUG>.png
```

## 4. Kindle setup (PW4, firmware 5.17.x)

1. Install the **ScreenSavers hack** (and run the one-time 5.17 symlink fix via
   USBNetLite/SSH — see chat notes) so custom sleep images work.
2. Install the **Online Screensaver** KUAL extension.
3. Point it at your image URL above, and set the refresh interval (e.g. 60 min).

The "clock" is the time of the last refresh, so pick an interval that balances
freshness against battery.

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Orchestrates fetch → render → save |
| `config.py` | Non-secret settings (env-overridable) |
| `src/weather.py` | OpenWeatherMap fetch |
| `src/calendar_events.py` | iCal fetch + recurring-event expansion |
| `src/render.py` | Draws the 1072×1448 PNG |
| `.github/workflows/build.yml` | Hourly build + Pages deploy |
