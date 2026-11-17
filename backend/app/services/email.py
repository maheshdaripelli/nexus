import asyncio
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_resend_email(*, to_email: str, subject: str, html: str, text_body: str) -> None:
    recipient = (
        "delivered@resend.dev"
        if settings.EMAIL_TEST_MODE
        else to_email
    )
    payload = json.dumps({
        "from": settings.EMAIL_FROM,
        "to": [recipient],
        "subject": subject,
        "html": html,
        "text": text_body,
    }).encode("utf-8")
    request = Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Nexus-API",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Email provider rejected the request (HTTP {exc.code}): {detail[:500]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach the email provider: {exc}") from exc


async def send_invitation_email(*, to_email: str, organization_name: str, role: str, invitation_url: str, expires_at: str) -> bool:
    if not settings.RESEND_API_KEY or not settings.EMAIL_FROM:
        logger.warning("Invitation email not sent: RESEND_API_KEY or EMAIL_FROM is not configured")
        return False

    safe_org = organization_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_role = role.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#172033;line-height:1.6">
      <h1 style="font-size:24px">You're invited to join {safe_org}</h1>
      <p>You have been invited to join <strong>{safe_org}</strong> on Nexus as a <strong>{safe_role}</strong>.</p>
      <p style="margin:28px 0"><a href="{invitation_url}" style="background:#4f46e5;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;display:inline-block">Accept invitation</a></p>
      <p>If the button doesn't work, copy and paste this link into your browser:</p>
      <p style="word-break:break-all"><a href="{invitation_url}">{invitation_url}</a></p>
      <p>This invitation expires on {expires_at} (UTC). If you weren't expecting it, you can ignore this email.</p>
      <p>— The Nexus team</p>
    </div>
    """
    text_body = (
        f"You've been invited to join {organization_name} on Nexus as a {role}.\n\n"
        f"Accept your invitation: {invitation_url}\n\n"
        f"This invitation expires on {expires_at} (UTC). If you weren't expecting it, ignore this email."
    )
    try:
        await asyncio.to_thread(
            _send_resend_email,
            to_email=to_email,
            subject=f"You're invited to join {organization_name} on Nexus",
            html=html,
            text_body=text_body,
        )
        logger.info("Invitation email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send invitation email to %s", to_email)
        return False
