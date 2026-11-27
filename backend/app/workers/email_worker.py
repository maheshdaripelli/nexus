import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from app.core.config import settings
from app.db.session import AsyncSessionLocal, engine
from app.messaging.broker import connect, topology
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.services.email import send_invitation_email

logger = logging.getLogger(__name__)

async def handle(message):
    async with message.process(requeue=False):
        payload = json.loads(message.body)
        invitation_id = UUID(payload["invitation_id"])
        token = payload["token"]
        async with AsyncSessionLocal() as db:
            invitation = await db.get(Invitation, invitation_id)
            if invitation is None or invitation.status != "pending" or invitation.expires_at <= datetime.now(timezone.utc):
                return
            if not hmac.compare_digest(invitation.token_hash, hashlib.sha256(token.encode()).hexdigest()):
                raise ValueError("Invalid invitation token")
            org = await db.get(Organization, invitation.organization_id)
            if org is None:
                return
            data = dict(to_email=invitation.email, organization_name=org.name,
                role=invitation.role,
                invitation_url=f"{settings.FRONTEND_ORIGIN.rstrip('/')}/accept-invitation?organization_id={org.id}&token={token}",
                expires_at=invitation.expires_at.isoformat())
        if not await send_invitation_email(**data):
            raise RuntimeError("Email provider did not confirm acceptance")
        logger.info("Invitation email accepted: %s", invitation_id)

async def main():
    try:
        async with await connect() as connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            _, queue = await topology(channel)
            await queue.consume(handle)
            logger.info("Invitation worker ready")
            await asyncio.Future()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
