"""One-off data backfill for agents.role_tier against the known org chart.

Explicit named lists only -- never inferred from is_specialist alone, since
nexus/einstein/zoe are specialists but not "consultant" in Anthony's sense
(Theodore/Alexander/Catherine/Hex/Bolt/Eleanor). Everything else falls back
to a reporting_manager_id/venture_id rule: top-of-venture = manager, has a
manager = worker. idea-lobster is 2ic explicitly; no "owner" row exists
(Anthony is not an agent row) so that tier stays unused until one is created.

Run once: docker exec -i cortexos-backend-1 python3 -m scripts.backfill_role_tier
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select, update

from app.database import AsyncSessionLocal
from app.models.agent import Agent

CONSULTANTS = {"theodore", "alexander", "catherine", "hex", "bolt", "eleanor"}
SECOND_IN_COMMAND = {"idea-lobster"}

# Known tag mistake found 2026-10-08: atlas's venture_id correctly points to
# kdp-colouring-books but the legacy `tags` text field still said
# "domain-flipping" -- fixed here as part of the same pass, not a separate one.
TAG_FIXES = {"atlas": "kdp-colouring-books"}


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Agent))
        agents = result.scalars().all()

        counts = {"consultant": 0, "2ic": 0, "manager": 0, "worker": 0}
        for agent in agents:
            name = agent.name.lower()
            if name in CONSULTANTS:
                tier = "consultant"
            elif name in SECOND_IN_COMMAND:
                tier = "2ic"
            elif agent.reporting_manager_id is None and agent.venture_id is not None:
                tier = "manager"
            else:
                tier = "worker"
            agent.role_tier = tier
            counts[tier] += 1

            if name in TAG_FIXES:
                agent.tags = f'["{TAG_FIXES[name]}"]'

        await session.commit()
        print(f"role_tier backfilled for {len(agents)} agents: {counts}")
        print(f"tag fixes applied: {list(TAG_FIXES.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
