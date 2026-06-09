"""Revenue sync scheduler — runs Gumroad sync every 15 minutes via APScheduler."""
from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import AsyncSessionLocal

logger = structlog.get_logger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _run_revenue_sync() -> None:
    """Called by APScheduler every 15 minutes."""
    async with AsyncSessionLocal() as db:
        try:
            from app.integrations.gumroad import sync_gumroad_sales
            inserted = await sync_gumroad_sales(db)
            if inserted > 0:
                logger.info("Revenue sync: new records", gumroad=inserted)
        except Exception as exc:
            logger.error("Revenue sync failed", error=str(exc))
            await db.rollback()


def start_revenue_sync_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_revenue_sync,
        trigger="interval",
        minutes=15,
        id="revenue_sync",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    _scheduler.start()
    logger.info("Revenue sync scheduler started (interval=15min)")
    return _scheduler


def stop_revenue_sync_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Revenue sync scheduler stopped")
