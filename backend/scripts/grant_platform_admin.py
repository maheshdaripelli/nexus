"""Grant platform-admin access to an existing Nexus user.

Run from the backend directory:
    python -m scripts.grant_platform_admin --email admin@example.com

This is an operator-only local command. Do not expose it as a public API.
"""
import argparse
import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.platform_admin import PlatformAdmin
from app.models.user import User


async def grant(email: str) -> None:
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            raise SystemExit(f"No Nexus user exists for {email!r}. Register that account first.")
        admin = await session.get(PlatformAdmin, user.id)
        if admin is None:
            session.add(PlatformAdmin(user_id=user.id, access_level="super_admin"))
        else:
            admin.access_level = "super_admin"
        await session.commit()
        print(f"Platform Super Admin access granted to {user.email} ({user.id}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant Nexus Platform Super Admin access.")
    parser.add_argument("--email", required=True, help="Email address of an existing Nexus user")
    args = parser.parse_args()
    asyncio.run(grant(args.email.strip()))


if __name__ == "__main__":
    main()
