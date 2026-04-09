import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from checker import check_stock
from notifier import send_stock_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


def run_check():
    logger.info("Starting stock check...")
    in_stock = check_stock()

    if in_stock:
        logger.info(f"{len(in_stock)} product(s) in stock — sending alert email.")
        send_stock_alert(in_stock)
    else:
        logger.info("No products in stock at this time.")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # suppress HTTP access logs


if __name__ == "__main__":
    # Run once immediately on startup
    run_check()

    scheduler = BackgroundScheduler(timezone=IST)

    # 8:00 AM IST
    scheduler.add_job(run_check, CronTrigger(hour=8, minute=0, timezone=IST))
    # 2:00 PM IST
    scheduler.add_job(run_check, CronTrigger(hour=14, minute=0, timezone=IST))
    # 8:00 PM IST
    scheduler.add_job(run_check, CronTrigger(hour=20, minute=0, timezone=IST))

    scheduler.start()
    logger.info("Scheduler started. Checks run at 8:00 AM, 2:00 PM, and 8:00 PM IST.")

    # Start HTTP server to satisfy Render's port binding requirement
    port = int(__import__("os").environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server listening on port {port}")
    server.serve_forever()
