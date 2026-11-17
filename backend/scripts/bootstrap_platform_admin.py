"""Create the first Platform Super Admin or promote an existing account.

Run from the backend directory:
    python -m scripts.bootstrap_platform_admin --email admin@example.com

The password is requested interactively and is never passed on the command line.
"""
import argparse
import asyncio
from getpass import getpass

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.platform_admin import PlatformAdmin
from app.models.user import User


async def bootstrap(email: str) -> None:
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == email))
        if user is None:
            full_name = input("Platform administrator full name: ").strip()
            if len(full_name) < 2 or len(full_name) > 120:
                raise SystemExit("Full name must contain between 2 and 120 characters.")
            password = getpass("Set password (minimum 12 characters): ")
            confirmation = getpass("Confirm password: ")
            if len(password) < 12 or len(password) > 128:
                raise SystemExit("Password must contain between 12 and 128 characters.")
            if password != confirmation:
                raise SystemExit("Passwords do not match.")
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                is_active=True,
            )
            session.add(user)
            await session.flush()

        admin = await session.get(PlatformAdmin, user.id)
        if admin is None:
            session.add(PlatformAdmin(user_id=user.id, access_level="super_admin"))
        else:
            admin.access_level = "super_admin"
        await session.commit()
        print(f"Platform Super Admin ready: {user.email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Nexus Platform Super Admin access.")
    parser.add_argument("--email", required=True, help="Email address for the initial operator")
    args = parser.parse_args()
    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email.strip())).lower()
    except Exception as exc:
        raise SystemExit("Please provide a valid email address.") from exc
    asyncio.run(bootstrap(email))


if __name__ == "__main__":
    main()