"""
Re-sync the `ventures` table from app.seeds.ventures.VENTURE_SEED_DATA.

Migration 0002 performs the initial seed + agents.venture_id backfill.
Run this afterwards if VENTURE_SEED_DATA is edited (new venture added,
or an existing venture renamed / reassigned to a new manager) — it is
idempotent and matches existing rows by slug.

Run via: docker compose exec backend python -m app.scripts.seed_ventures
"""
from __future__ import annotations

import asyncio

import structlog
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.venture import Venture
from app.seeds.ventures import VENTURE_SEED_DATA

logger = structlog.get_logger(__name__)


async def seed_ventures() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Venture))
        existing = {v.slug: v for v in result.scalars().all()}

        created = updated = 0
        for row in VENTURE_SEED_DATA:
            venture = existing.get(row["slug"])
            if venture is None:
                db.add(Venture(**row))
                created += 1
                logger.info("Created venture", slug=row["slug"])
            elif (
                venture.name != row["name"]
                or venture.manager_name != row["manager_name"]
                or venture.category != row["category"]
            ):
                venture.name = row["name"]
                venture.manager_name = row["manager_name"]
                venture.category = row["category"]
                updated += 1
                logger.info("Updated venture", slug=row["slug"])

        await db.commit()
    logger.info("Venture sync complete", created=created, updated=updated)


if __name__ == "__main__":
    asyncio.run(seed_ventures())
