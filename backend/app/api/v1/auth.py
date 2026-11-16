from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, hash_password, hash_refresh_token, verify_password
from app.core.config import settings
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RefreshRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    raw_refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_refresh_token(raw_refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)))
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=raw_refresh, user=user)

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = str(payload.email).lower()
    if await db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()
    return await issue_tokens(db, user)

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return await issue_tokens(db, user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False)))
    now = datetime.now(timezone.utc)
    if stored is None or stored.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
    user = await db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is unavailable")
    stored.revoked = True
    return await issue_tokens(db, user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token), RefreshToken.user_id == user.id))
    if stored is not None:
        stored.revoked = True
        await db.commit()

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
