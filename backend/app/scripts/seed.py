"""
Seed script — creates default admin user and populates default agents.
Run via: docker compose exec backend python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid

import structlog

logger = structlog.get_logger(__name__)

DEFAULT_AGENTS = [
    {
        "name": "ceo",
        "agent_type": "ceo",
        "purpose": "Strategic planning, delegation, and cross-agent coordination",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.7,
        "max_tokens": 8192,
    },
    {
        "name": "research",
        "agent_type": "research",
        "purpose": "Market research, competitor analysis, and trend discovery",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.3,
        "max_tokens": 8192,
    },
    {
        "name": "product",
        "agent_type": "product",
        "purpose": "Digital product creation, packaging, and asset generation",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.8,
        "max_tokens": 8192,
    },
    {
        "name": "seo",
        "agent_type": "seo",
        "purpose": "Keyword discovery, SEO strategy, and content optimisation",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.4,
        "max_tokens": 4096,
    },
    {
        "name": "content",
        "agent_type": "content",
        "purpose": "Blog posts, product descriptions, and landing pages",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.8,
        "max_tokens": 8192,
    },
    {
        "name": "marketing",
        "agent_type": "marketing",
        "purpose": "Social media, email campaigns, and distribution strategy",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    {
        "name": "support",
        "agent_type": "support",
        "purpose": "Support workflows, FAQ generation, and customer responses",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.5,
        "max_tokens": 4096,
    },
    {
        "name": "finance",
        "agent_type": "finance",
        "purpose": "Revenue analysis, cost tracking, and financial reporting",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    {
        "name": "operations",
        "agent_type": "operations",
        "purpose": "SOP creation, workflow management, and process optimisation",
        "model_provider": "claude",
        "model_name": "claude-sonnet-4-6",
        "temperature": 0.5,
        "max_tokens": 4096,
    },
]


async def seed() -> None:
    from sqlalchemy import select
    from app.auth.password import hash_password
    from app.auth.rbac import ROLE_PERMISSIONS
    from app.database import AsyncSessionLocal, init_db
    from app.models.agent import Agent
    from app.models.user import Role, User

    await init_db()

    async with AsyncSessionLocal() as db:
        # ── Roles ─────────────────────────────────────────────────────────────
        for role_name, permissions in ROLE_PERMISSIONS.items():
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalar_one_or_none():
                role = Role(
                    name=role_name,
                    description=f"Default {role_name} role",
                    permissions=json.dumps(permissions),
                )
                db.add(role)
                logger.info("Created role", role=role_name)

        await db.commit()

        # ── Admin user ────────────────────────────────────────────────────────
        result = await db.execute(select(User).where(User.email == "admin@cortexos.ai"))
        if not result.scalar_one_or_none():
            admin_role_result = await db.execute(select(Role).where(Role.name == "admin"))
            admin_role = admin_role_result.scalar_one_or_none()

            from app.models.user import UserRole
            admin = User(
                email="admin@cortexos.ai",
                username="admin",
                hashed_password=hash_password("cortexos-admin-change-me"),
                full_name="CortexOS Admin",
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            await db.flush()
            if admin_role:
                db.add(UserRole(user_id=admin.id, role_id=admin_role.id))
            await db.commit()
            logger.info("Created admin user", email="admin@cortexos.ai")
        else:
            logger.info("Admin user already exists — skipping")

        # ── Default agents ────────────────────────────────────────────────────
        for agent_data in DEFAULT_AGENTS:
            result = await db.execute(
                select(Agent).where(Agent.name == agent_data["name"])
            )
            if not result.scalar_one_or_none():
                agent = Agent(**agent_data)
                db.add(agent)
                logger.info("Created agent", name=agent_data["name"])
            else:
                logger.info("Agent already exists — skipping", name=agent_data["name"])

        await db.commit()

    logger.info("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
