"""
Seed script -- creates the anthony admin user for PIN-based login.
Run via: docker compose exec backend python -m app.scripts.seed_admin
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid

import structlog

logger = structlog.get_logger(__name__)


async def seed() -> None:
    from sqlalchemy import select
    from app.auth.password import hash_password
    from app.database import AsyncSessionLocal, init_db
    from app.models.user import Role, User, UserRole

    await init_db()

    async with AsyncSessionLocal() as db:
        # Check existing anthony user
        result = await db.execute(select(User).where(User.username == "anthony"))
        if result.scalar_one_or_none():
            logger.info("Admin user 'anthony' already exists -- skipping")
            print("Admin user 'anthony' already exists.")
            return

        # Get or create admin role
        role_result = await db.execute(select(Role).where(Role.name == "admin"))
        role = role_result.scalar_one_or_none()
        if not role:
            role = Role(
                name="admin",
                description="Administrator",
                permissions=json.dumps(["*"]),
            )
            db.add(role)
            await db.flush()
            logger.info("Created admin role")

        # Create anthony user with random hashed password (PIN is the auth method)
        user = User(
            email="anthony@cortexos.local",
            username="anthony",
            full_name="Anthony Zed",
            hashed_password=hash_password(os.urandom(32).hex()),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        await db.commit()
        logger.info("Admin user created", username="anthony", user_id=str(user.id))
        print(f"Admin user created: {user.id}")


if __name__ == "__main__":
    asyncio.run(seed())
