import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import Config

logger = logging.getLogger(__name__)


def send_price_drop_email(to_email: str, product_name: str, product_url: str,
                          target_price: float, current_price: float, store: str) -> bool:
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        logger.warning("SMTP not configured — skipping email to %s", to_email)
        return False

    subject = f"Price Drop Alert: {product_name}"
    body = f"""
    <html><body>
    <h2>Price Drop Alert!</h2>
    <p>Good news! <strong>{product_name}</strong> on {store} has dropped below your target price.</p>
    <table>
      <tr><td><strong>Current Price:</strong></td><td>${current_price:.2f}</td></tr>
      <tr><td><strong>Your Target:</strong></td><td>${target_price:.2f}</td></tr>
    </table>
    <p><a href="{product_url}">View product</a></p>
    <hr>
    <small>Price Tracker — unsubscribe by visiting your dashboard.</small>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = Config.ALERT_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.ALERT_FROM_EMAIL, to_email, msg.as_string())
        logger.info("Alert email sent to %s for %s", to_email, product_name)
        return True
    except Exception as exc:
        logger.error("Failed to send alert email: %s", exc)
        return False
