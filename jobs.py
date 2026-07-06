import os
from telegram.ext import Application

from tp_sl_engine import check_all_positions


async def tp_sl_job(context) -> None:
    await check_all_positions(context.application)


def setup_jobs(app: Application) -> None:
    """
    Call this once after app is created.
    Requires python-telegram-bot[job-queue].
    """
    interval = int(os.getenv("TPSL_CHECK_INTERVAL_SECONDS", "60"))
    app.job_queue.run_repeating(tp_sl_job, interval=interval, first=15)
