"""
Rendering: turn the clock + weather + events into one grayscale PNG sized for
the Paperwhite 4 (1072 x 1448).

Design goals for e-ink:
  - Pure black text on white, large sizes, generous spacing.
  - No anti-aliasing surprises: mode "L" (8-bit gray), which the screensaver
    hack and `eips` handle well.

Layout, top to bottom:
  1. Clock (big) + date + "updated" line.
  2. Weather panel: location, big temp, description, hi/lo, short forecast row.
  3. Events panel: upcoming calendar entries.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

BLACK = 0
GRAY = 110
WHITE = 255

# Candidate scalable fonts per weight, covering the Ubuntu GitHub runner first
# and common Windows/macOS paths so local previews match. The first that loads
# wins; if none are found we fall back to Pillow's (tiny) bitmap default.
_REGULAR_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",   # Ubuntu runner
    "/Library/Fonts/Arial.ttf",                          # macOS
    "C:/Windows/Fonts/arial.ttf",                        # Windows
    "C:/Windows/Fonts/segoeui.ttf",                      # Windows fallback
]
_BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]


def _font(size: int, bold: bool = False):
    """Load a scalable font at the given size, or fall back to the default."""
    for path in (_BOLD_FONTS if bold else _REGULAR_FONTS):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
    return ImageFont.load_default()


def _fmt_time(dt: datetime) -> str:
    """12-hour time like '3:45 PM', portable across OSes."""
    return dt.strftime("%I:%M %p").lstrip("0")


def _center(draw, text, font, y, width):
    """Draw horizontally-centred text, return the y below it."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((width - w) / 2, y), text, font=font, fill=BLACK)
    return y + h


def render(config, weather: dict, events: dict) -> Image.Image:
    """Build and return the finished PIL image."""
    img = Image.new("L", (config.WIDTH, config.HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)
    tz = ZoneInfo(config.TIMEZONE)
    now = datetime.now(tz)
    margin = 60

    # --- 1. Clock + date ----------------------------------------------------
    y = 70
    y = _center(draw, _fmt_time(now), _font(190, bold=True), y, config.WIDTH)
    y += 30
    y = _center(draw, now.strftime("%A"), _font(70), y, config.WIDTH)
    y += 15
    y = _center(draw, now.strftime("%B %d, %Y"), _font(55), y, config.WIDTH)
    y += 20
    _center(draw, f"updated {_fmt_time(now)}", _font(32), y, config.WIDTH)
    y += 70

    _rule(draw, margin, y, config.WIDTH - margin)
    y += 40

    # --- 2. Weather ---------------------------------------------------------
    y = _draw_weather(draw, config, weather, y, margin)
    y += 30
    _rule(draw, margin, y, config.WIDTH - margin)
    y += 40

    # --- 3. Events ----------------------------------------------------------
    _draw_events(draw, config, events, y, margin)

    return img


def _rule(draw, x0, y, x1):
    """A thin horizontal divider."""
    draw.line([(x0, y), (x1, y)], fill=GRAY, width=2)


def _draw_weather(draw, config, weather: dict, y: int, margin: int) -> int:
    """Render the weather panel; return the y below it."""
    draw.text((margin, y), config.LOCATION_LABEL, font=_font(48, bold=True), fill=BLACK)
    y += 70

    if not weather.get("ok"):
        draw.text((margin, y), "Weather unavailable", font=_font(44), fill=GRAY)
        return y + 60

    sym = weather["units_symbol"]
    big = f"{weather['temp']}°{sym}"
    draw.text((margin, y), big, font=_font(130, bold=True), fill=BLACK)

    # Description + hi/lo to the right of the big number.
    right_x = margin + 360
    draw.text((right_x, y + 10), weather["description"], font=_font(46), fill=BLACK)
    draw.text(
        (right_x, y + 70),
        f"H {weather['temp_max']}°  L {weather['temp_min']}°   feels {weather['feels_like']}°",
        font=_font(40),
        fill=GRAY,
    )
    y += 160

    # Short forecast row.
    if weather.get("forecast"):
        col_w = (config.WIDTH - 2 * margin) // len(weather["forecast"])
        for i, step in enumerate(weather["forecast"]):
            cx = margin + i * col_w
            draw.text((cx, y), step["label"], font=_font(38, bold=True), fill=BLACK)
            draw.text((cx, y + 48), f"{step['temp']}°", font=_font(40), fill=BLACK)
            draw.text((cx, y + 98), step["main"], font=_font(30), fill=GRAY)
        y += 150
    return y


def _draw_events(draw, config, events: dict, y: int, margin: int) -> int:
    """Render the upcoming-events panel; return the y below it."""
    draw.text((margin, y), "Upcoming", font=_font(48, bold=True), fill=BLACK)
    y += 80

    if not events.get("ok"):
        draw.text((margin, y), "Calendar unavailable", font=_font(44), fill=GRAY)
        return y + 60

    if not events["events"]:
        draw.text((margin, y), "Nothing scheduled", font=_font(44), fill=GRAY)
        return y + 60

    for ev in events["events"]:
        when = _event_when(ev)
        draw.text((margin, y), when, font=_font(40, bold=True), fill=BLACK)
        # Title, truncated to fit on one line.
        title = _truncate(draw, ev["summary"], _font(40), config.WIDTH - margin - 360)
        draw.text((margin + 360, y), title, font=_font(40), fill=BLACK)
        y += 72
    return y


def _event_when(ev: dict) -> str:
    """Human label like 'Tue 3:45 PM' or 'Wed all-day'."""
    day = ev["start"].strftime("%a")
    if ev["all_day"]:
        return f"{day} all-day"
    return f"{day} {_fmt_time(ev['start'])}"


def _truncate(draw, text, font, max_width) -> str:
    """Trim a string with an ellipsis so it fits within max_width pixels."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    ell = "…"
    while text and draw.textlength(text + ell, font=font) > max_width:
        text = text[:-1]
    return text + ell
