"""Bus geo-fence alert daemon.

Designed to be triggered by cron. Polls the bus tracking API and fires alerts
when the bus enters the geo-fence. Re-alerts every REPEAT_ALERT_INTERVAL polls
while the bus remains inside the fence. Exits after MAX_ALERTS notifications.
"""
import argparse
import logging
import logging.handlers
import os
import sys
import time
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv

from geo import haversine
from notifiers import desktop, telegram, email_notify, ntfy

load_dotenv()

# ── Logging: console + rotating file ──────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python-bus-alert.log")
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_root = logging.getLogger()
_root.setLevel(logging.INFO)

# Console handler
_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FMT))
_root.addHandler(_console)

# Rotating file handler — max 1 MB per file, keep 3 backups
_file_handler = logging.handlers.RotatingFileHandler(
    _LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FMT))
_root.addHandler(_file_handler)

logger = logging.getLogger(__name__)

REQUIRED_ENV = ["BUS_API_URL", "HOME_LAT", "HOME_LONG", "GEOFENCE_RADIUS_KM"]


def validate_config() -> None:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        logger.error("Missing required config keys: %s", ", ".join(missing))
        logger.error("Copy .env.example to .env and fill in the values.")
        sys.exit(1)


def fetch_bus_location(api_url: str) -> Optional[dict]:
    try:
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            logger.warning("API returned success=false")
            return None
        loc = data["data"]["location"]
        return {
            "lat": float(loc["lat"]),
            "long": float(loc["long"]),
            "address": loc.get("address", ""),
            "speed": loc.get("speed_with_unit", {}).get("value", 0),
            "speed_unit": loc.get("speed_with_unit", {}).get("unit", "km/h"),
            "status": data["data"]["vehicle_movement_status"].get("movement_status", ""),
            "display_number": data["data"].get("display_number", "Bus"),
        }
    except requests.RequestException as exc:
        logger.warning("API request failed: %s", exc)
    except (KeyError, ValueError) as exc:
        logger.warning("Unexpected API response format: %s", exc)
    return None


def build_message(info: dict, distance: float, alert_count: int, max_alerts: int) -> Tuple[str, str]:
    title = "\U0001f68c " + info["display_number"] + " is approaching! (" + str(alert_count) + "/" + str(max_alerts) + ")"
    body = "\n".join([
        "Distance: " + str(round(distance, 2)) + " km from home",
        "Address: " + info["address"],
        "Speed: " + str(info["speed"]) + " " + info["speed_unit"] + " | Status: " + info["status"],
    ])
    return title, body


def fire_alerts(title: str, message: str, dry_run: bool) -> None:
    if dry_run:
        print("[DRY-RUN] Would fire alerts:")
        print("  Title: " + title)
        print("  Body:\n" + message)
        return
    #desktop.notify(title, message)
    #telegram.notify(title, message)
    #email_notify.notify(title, message)
    ntfy.notify(title, message)


def run(dry_run: bool = False) -> None:
    validate_config()

    api_url = os.environ["BUS_API_URL"]
    home_lat = float(os.environ["HOME_LAT"])
    home_long = float(os.environ["HOME_LONG"])
    radius_km = float(os.environ["GEOFENCE_RADIUS_KM"])
    interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
    max_alerts = int(os.environ.get("MAX_ALERTS", "3"))
    repeat_every = int(os.environ.get("REPEAT_ALERT_INTERVAL", "5"))
    max_runtime_minutes = int(os.environ.get("MAX_RUNTIME_MINUTES", "30"))

    logger.info("Daemon started. Will exit after %d alert(s) or %d minutes.", max_alerts, max_runtime_minutes)
    logger.info(
        "Home: (%.6f, %.6f)  Radius: %.2f km  Poll: %ds  Repeat every: %d polls",
        home_lat, home_long, radius_km, interval, repeat_every,
    )
    if dry_run:
        logger.info("DRY-RUN mode — no real alerts will be sent.")

    inside_fence = False
    alert_count = 0
    polls_inside = 0  # consecutive polls with bus inside fence
    start_time = time.monotonic()

    while True:
        elapsed_minutes = (time.monotonic() - start_time) / 60
        if elapsed_minutes >= max_runtime_minutes:
            logger.info("Max runtime of %d minutes reached — exiting.", max_runtime_minutes)
            sys.exit(0)
        info = fetch_bus_location(api_url)
        if info is not None:
            distance = haversine(info["lat"], info["long"], home_lat, home_long)
            logger.info("Bus %s — %.2f km from home", info["display_number"], distance)

            if distance <= radius_km:
                polls_inside += 1

                # Alert on first entry OR every repeat_every polls while inside
                if not inside_fence or polls_inside % repeat_every == 0:
                    alert_count += 1
                    logger.info(
                        "Alert %d/%d — bus inside fence for %d poll(s).",
                        alert_count, max_alerts, polls_inside,
                    )
                    title, message = build_message(info, distance, alert_count, max_alerts)
                    fire_alerts(title, message, dry_run)

                    if alert_count >= max_alerts:
                        logger.info("Reached max alerts (%d) — exiting.", max_alerts)
                        sys.exit(0)

                inside_fence = True

            else:
                if inside_fence:
                    logger.info("Bus LEFT geo-fence after %d poll(s) inside.", polls_inside)
                inside_fence = False
                polls_inside = 0

        else:
            logger.warning("Could not fetch bus location — will retry.")

        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bus geo-fence alert daemon")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate alerts without sending real notifications",
    )
    args = parser.parse_args()
    try:
        run(dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
