from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = decode_access_token(token)
    except (InvalidTokenError, ValueError, KeyError):
        raise error
    user = await db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise error
    return user
