"""Email alert via smtplib STARTTLS."""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def notify(title: str, message: str) -> None:
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    to_addr = os.environ.get("ALERT_EMAIL_TO", "")

    if not all([host, user, password, to_addr]):
        logger.warning("Email credentials not fully configured — skipping.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = title
    msg["From"] = user
    msg["To"] = to_addr
    msg.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_addr, msg.as_string())
        logger.info("Email sent to %s.", to_addr)
    except Exception as exc:
        logger.error("Email notification failed: %s", exc)
