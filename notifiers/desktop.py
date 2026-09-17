"""Desktop OS notification via plyer."""
import logging

logger = logging.getLogger(__name__)


def notify(title: str, message: str) -> None:
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="BusAlert", timeout=10)
        logger.info("Desktop notification sent.")
    except NotImplementedError:
        logger.warning("Desktop notifications not supported on this platform.")
    except Exception as exc:
        logger.error("Desktop notification failed: %s", exc)
