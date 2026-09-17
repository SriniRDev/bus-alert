"""ntfy.sh push notification — rings phone with urgent priority."""
import logging
import os

import requests

logger = logging.getLogger(__name__)

NTFY_BASE_URL = "https://ntfy.sh"


def notify(title: str, message: str) -> None:
    topic = os.environ.get("NTFY_TOPIC", "")
    if not topic:
        logger.warning("NTFY_TOPIC not configured — skipping ntfy notification.")
        return

    url = f"{NTFY_BASE_URL}/{topic}"
    try:
        resp = requests.post(
            url,
            data=message.encode("utf-8"),
            headers={
                "Title": title.encode("utf-8"),
                "Priority": "urgent",       # max priority — overrides silent mode
                "Tags": "rotating_light,bus",  # emoji tags shown in notification
                "Sound": "default",
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("ntfy notification sent to topic '%s'.", topic)
    except Exception as exc:
        logger.error("ntfy notification failed: %s", exc)
