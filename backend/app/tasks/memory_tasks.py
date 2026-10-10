"""Autonomous memory and knowledge graph growth tasks."""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

WORK_LOG_PATH = "/opt/openclaw/orchestration/EMPIRE-WORK-LOG.md"
AGENTS_DIR = "/data/agents"

ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
)


def _run_async(coro: Any) -> Any:
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.memory_tasks.ingest_work_log")
def ingest_work_log() -> dict[str, Any]:
    """Ingest new EMPIRE-WORK-LOG.md entries as episodic memories."""
    async def _run() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.models.memory_item import MemoryItem
        from sqlalchemy import select

        if not os.path.exists(WORK_LOG_PATH):
            return {"skipped": True, "reason": "work log not found"}

        text = Path(WORK_LOG_PATH).read_text(errors="replace")
        rows = []
        for line in text.splitlines():
            m = ROW_RE.match(line.strip())
            if not m:
                continue
            ts, agent, venture, action, result = [g.strip() for g in m.groups()]
            # Skip header rows
            if ts.lower() in ("date time awst", "date", "---", ":---"):
                continue
            if action.lower() in ("action", "---", ":---"):
                continue
            rows.append((ts, agent, venture, action, result))

        if not rows:
            return {"added": 0, "total_rows": 0}

        # Deduplicate via hash of (ts+agent+action)
        async with AsyncSessionLocal() as db:
            existing = set(
                (await db.execute(
                    select(MemoryItem.external_id).where(
                        MemoryItem.external_id.like("worklog:row:%")
                    )
                )).scalars().all()
            )

            added = 0
            # Take most recent 100 rows
            for ts, agent, venture, action, result in rows[-100:]:
                row_hash = hashlib.md5(f"{ts}|{agent}|{action}".encode()).hexdigest()[:16]
                ext_id = f"worklog:row:{row_hash}"
                if ext_id in existing:
                    continue
                content = (
                    f"[{ts}] {agent} ({venture}): {action}. "
                    f"Result: {result}"
                )
                summary = f"Work log: {agent} — {action[:80]}"
                db.add(MemoryItem(
                    external_id=ext_id,
                    summary=summary,
                    content=content,
                    memory_type="episodic",
                    category="empire",
                    importance_score=0.55,
                    tags='["work-log","empire","auto"]',
                ))
                existing.add(ext_id)
                added += 1

            await db.commit()
            return {"added": added, "total_rows": len(rows)}

    result = _run_async(_run())
    logger.info("ingest_work_log complete", **result)
    return result


@celery_app.task(name="app.tasks.memory_tasks.sync_agent_files")
def sync_agent_files() -> dict[str, Any]:
    """Sync /root/.claude/agents/*.md files into memory."""
    async def _run() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.models.memory_item import MemoryItem
        from sqlalchemy import select

        agents_path = Path(AGENTS_DIR)
        if not agents_path.exists():
            return {"skipped": True, "reason": "agents dir not found"}

        md_files = list(agents_path.glob("*.md"))
        if not md_files:
            return {"added": 0, "files": 0}

        async with AsyncSessionLocal() as db:
            existing = set(
                (await db.execute(
                    select(MemoryItem.external_id).where(
                        MemoryItem.external_id.like("agentfile:%")
                    )
                )).scalars().all()
            )

            added = 0
            for fpath in md_files:
                agent_name = fpath.stem
                ext_id = f"agentfile:{agent_name}"
                if ext_id in existing:
                    continue

                try:
                    raw = fpath.read_text(errors="replace")
                except Exception:
                    continue

                # Extract description from frontmatter or first paragraph
                desc = ""
                fm_match = re.search(
                    r"^---\s*\n(.*?)\n---", raw, re.DOTALL | re.MULTILINE
                )
                if fm_match:
                    fm = fm_match.group(1)
                    d_match = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", fm, re.MULTILINE)
                    if d_match:
                        desc = d_match.group(1).strip()
                if not desc:
                    # First non-empty non-frontmatter paragraph
                    body = re.sub(r"^---.*?---\s*", "", raw, flags=re.DOTALL).strip()
                    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
                    if paras:
                        desc = paras[0][:400]

                if not desc:
                    continue

                content = (
                    f"Empire agent file: {agent_name}. "
                    f"Description: {desc[:600]} "
                    f"File: {AGENTS_DIR}/{agent_name}.md"
                )
                db.add(MemoryItem(
                    external_id=ext_id,
                    summary=f"Agent file: {agent_name}",
                    content=content,
                    memory_type="semantic",
                    category="agents",
                    importance_score=0.6,
                    tags=f'["{agent_name}","agent-file","auto"]',
                ))
                existing.add(ext_id)
                added += 1

            await db.commit()
            return {"added": added, "files": len(md_files)}

    result = _run_async(_run())
    logger.info("sync_agent_files complete", **result)
    return result


@celery_app.task(name="app.tasks.memory_tasks.snapshot_empire_health")
def snapshot_empire_health() -> dict[str, Any]:
    """Create a periodic empire health snapshot memory."""
    async def _run() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.models.agent import Agent
        from app.models.memory_item import MemoryItem
        from app.models.venture import Venture
        from sqlalchemy import func, select

        async with AsyncSessionLocal() as db:
            total_agents = (await db.execute(select(func.count(Agent.id)))).scalar()
            total_ventures = (await db.execute(select(func.count(Venture.id)))).scalar()
            total_memory = (await db.execute(select(func.count(MemoryItem.id)))).scalar()

            managed = (await db.execute(
                select(func.count(Venture.id)).where(Venture.manager_name != "tbd")
            )).scalar()

            tagged = (await db.execute(
                select(func.count(Agent.id)).where(
                    Agent.tags.notin_(["specialist", "[]", ""])
                )
            )).scalar()

            now = datetime.now(tz=timezone.utc)
            date_key = now.strftime("%Y-%m-%d")
            ext_id = f"empire:health:{date_key}"

            # Update or insert
            existing = (await db.execute(
                select(MemoryItem).where(MemoryItem.external_id == ext_id)
            )).scalar_one_or_none()

            content = (
                f"Empire health snapshot {date_key}: "
                f"{total_ventures} ventures ({managed} with managers), "
                f"{total_agents} agents ({tagged} venture-tagged), "
                f"{total_memory} memory items. "
                f"Target: AUD 50K/month by 2026-07-22 (Day 90). "
                f"Snapshot captured at {now.isoformat()}."
            )
            summary = f"Empire health {date_key}: {total_ventures} ventures, {total_agents} agents, {total_memory} memories"

            if existing:
                existing.content = content
                existing.summary = summary
            else:
                db.add(MemoryItem(
                    external_id=ext_id,
                    summary=summary,
                    content=content,
                    memory_type="episodic",
                    category="empire",
                    importance_score=0.8,
                    tags='["health-snapshot","empire","auto"]',
                ))

            await db.commit()
            return {
                "ventures": total_ventures,
                "agents": total_agents,
                "memory": total_memory,
                "date": date_key,
            }

    result = _run_async(_run())
    logger.info("snapshot_empire_health complete", **result)
    return result


@celery_app.task(name="app.tasks.memory_tasks.decay_old_memories")
def decay_old_memories() -> dict[str, Any]:
    """Reduce importance of old, unaccessed low-importance memories."""
    async def _run() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.models.memory_item import MemoryItem
        from sqlalchemy import select

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MemoryItem).where(
                    MemoryItem.importance_score < 0.5,
                    MemoryItem.access_count == 0,
                    MemoryItem.created_at < cutoff,
                    # Never decay structured empire facts
                    ~MemoryItem.tags.contains("empire"),
                ).limit(200)
            )
            items = result.scalars().all()
            decayed = 0
            for item in items:
                new_score = max(0.05, (item.importance_score or 0.5) * 0.85)
                item.importance_score = new_score
                decayed += 1

            await db.commit()
            return {"decayed": decayed}

    result = _run_async(_run())
    logger.info("decay_old_memories complete", **result)
    return result
