"""Scheduled daily collection using APScheduler."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.db import SessionLocal
from app.collector import run_collection

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_collect():
    """Run collection and log results."""
    logger.info("=== Scheduled collection started ===")
    db = SessionLocal()
    try:
        result = run_collection(db)
        logger.info(f"Scheduled collection result: {result}")
    except Exception as e:
        logger.error(f"Scheduled collection failed: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler(hour: int = 6, minute: int = 0):
    """Start the daily scheduler."""
    scheduler.add_job(
        scheduled_collect,
        "cron",
        hour=hour,
        minute=minute,
        id="daily_collect",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: daily collection at {hour:02d}:{minute:02d} UTC")
