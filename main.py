import logging
import os
from apscheduler.schedulers.blocking import BlockingScheduler
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


if __name__ == "__main__":
    # Run once immediately on startup (useful to verify everything works on deploy)
    run_check()

    scheduler = BlockingScheduler(timezone=IST)

    # 8:00 AM IST
    scheduler.add_job(run_check, CronTrigger(hour=8, minute=0, timezone=IST))
    # 2:00 PM IST
    scheduler.add_job(run_check, CronTrigger(hour=14, minute=0, timezone=IST))
    # 8:00 PM IST
    scheduler.add_job(run_check, CronTrigger(hour=20, minute=0, timezone=IST))

    logger.info("Scheduler started. Checks run at 8:00 AM, 2:00 PM, and 8:00 PM IST.")
    scheduler.start()
