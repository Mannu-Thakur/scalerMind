"""Insert small, idempotent local curriculum samples and optional demo users."""
import asyncio
import os

from sqlalchemy import select

from app.auth.passwords import hash_password
from app.db.engine import engine, session_factory
from app.db.models import Course, Topic, User


async def seed() -> None:
    async with session_factory() as session:
        course = await session.scalar(
            select(Course).where(Course.slug == "computer-science-foundations")
        )
        if course is None:
            course = Course(
                slug="computer-science-foundations",
                title="Computer Science Foundations",
                description="A starter course for core computer science concepts.",
                is_published=False,
            )
            session.add(course)
            await session.flush()

        topic = await session.scalar(
            select(Topic).where(
                Topic.course_id == course.id,
                Topic.slug == "getting-started",
            )
        )
        if topic is None:
            session.add(
                Topic(
                    course_id=course.id,
                    slug="getting-started",
                    title="Getting Started",
                    description="A placeholder topic for the first learning path.",
                    position=0,
                )
            )

        for role, env_name, email, display_name in (
            ("learner", "SEED_LEARNER_PASSWORD", "learner@example.com", "Demo Learner"),
            ("admin", "SEED_ADMIN_PASSWORD", "admin@example.com", "Demo Admin"),
        ):
            password = os.getenv(env_name)
            if not password:
                continue
            existing = await session.scalar(select(User).where(User.email == email))
            if existing is None:
                session.add(
                    User(
                        email=email,
                        display_name=display_name,
                        password_hash=hash_password(password),
                        role=role,
                    )
                )

        await session.commit()


async def main() -> None:
    await seed()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
