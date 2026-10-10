"""Backfill agents.venture_id + agents.reporting_manager_id from real data:
ventures.manager_name (authoritative per-venture manager) crossed with
registry.json's per-agent venture slug (325 agents, each already tagged with
their venture -- stale since 2026-07-27 but name/venture pairing is still
real, not invented).

Run once: docker exec -i cortexos-backend-1 python3 -m scripts.backfill_manager_links
"""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.agent import Agent
from app.models.venture import Venture

REGISTRY_PATH = "/opt/openclaw/orchestration/registry.json"

# registry.json (stale since 2026-07-27) uses slightly different venture
# slugs than the real ventures table for a handful of ventures -- found by
# diffing both slug sets directly, not guessed.
SLUG_ALIASES = {
    "bloom-and-bub": "bloom-bub",
    "gtt-center-perth": "gtt-perth",
    "kids-milestones": "kidsmilestones",
    "personal-finance": "personal-finance-dashboard",
    "weeklywonder": "weekly-wonder",
}


async def main() -> None:
    registry = json.load(open(REGISTRY_PATH))
    name_to_venture_slug = {
        a["name"].lower(): a["venture"]
        for a in registry.get("agents", [])
        if isinstance(a, dict) and a.get("name") and a.get("venture")
    }

    async with AsyncSessionLocal() as session:
        ventures = (await session.execute(select(Venture))).scalars().all()
        slug_to_venture = {v.slug: v for v in ventures}

        agents = (await session.execute(select(Agent))).scalars().all()
        name_to_agent = {a.name.lower(): a for a in agents}

        linked = 0
        manager_confirmed = 0
        skipped_tbd = 0
        skipped_no_venture_match = 0

        for agent in agents:
            slug = name_to_venture_slug.get(agent.name.lower())
            if not slug:
                skipped_no_venture_match += 1
                continue
            slug = SLUG_ALIASES.get(slug, slug)
            venture = slug_to_venture.get(slug)
            if venture is None:
                skipped_no_venture_match += 1
                continue

            manager_name = (venture.manager_name or "").lower()
            if not manager_name or manager_name == "tbd":
                skipped_tbd += 1
                continue

            manager_agent = name_to_agent.get(manager_name)
            if manager_agent is None:
                skipped_no_venture_match += 1
                continue

            if agent.id == manager_agent.id:
                # agent IS the manager -- just confirm their own venture_id
                if agent.venture_id is None:
                    agent.venture_id = venture.id
                    manager_confirmed += 1
                continue

            agent.venture_id = venture.id
            agent.reporting_manager_id = manager_agent.id
            linked += 1

        await session.commit()
        print(
            f"linked={linked} manager_confirmed={manager_confirmed} "
            f"skipped_tbd_manager={skipped_tbd} skipped_no_match={skipped_no_venture_match} "
            f"total_agents={len(agents)}"
        )


if __name__ == "__main__":
    asyncio.run(main())
