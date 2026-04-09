import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_stock_alert(in_stock_products: list[dict]):
    """Send an email listing all in-stock products."""
    sender = os.environ["EMAIL_SENDER"]
    receiver = os.environ["EMAIL_RECEIVER"]
    password = os.environ["EMAIL_PASSWORD"]

    subject = "Amul Stock Alert! Products are available now"

    # Plain text body
    lines = ["The following Amul products are currently IN STOCK:\n"]
    for p in in_stock_products:
        lines.append(f"  - {p['name']}")
        lines.append(f"    {p['url']}\n")
    lines.append("\nBuy now before they sell out again!")
    text_body = "\n".join(lines)

    # HTML body
    html_items = ""
    for p in in_stock_products:
        html_items += (
            f'<li style="margin-bottom:12px;">'
            f'<strong>{p["name"]}</strong><br>'
            f'<a href="{p["url"]}">{p["url"]}</a>'
            f"</li>"
        )

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
      <h2 style="color:#e63946;">Amul Stock Alert!</h2>
      <p>The following products are currently <strong style="color:green;">IN STOCK</strong>:</p>
      <ul>{html_items}</ul>
      <p>Buy now before they sell out again!</p>
      <hr><small>Sent by your Amul Stock Monitor</small>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        logger.info(f"Alert email sent to {receiver}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
