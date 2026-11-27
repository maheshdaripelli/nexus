import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.api.v2.router import api_router as v2_router
from app.messaging.broker import Broker
from app.db.session import engine, get_db
from app.models import Membership, Organization, Team, User  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbitmq = Broker()
    try:
        yield
    finally:
        await app.state.rabbitmq.close()
        await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, description="Nexus User and Workspace Management Platform", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
if settings.ENABLE_API_V2:
    app.include_router(v2_router, prefix="/api/v2")


@app.get("/", tags=["Health"])
async def root():
    return {"application": "Nexus", "message": "Welcome to Nexus API", "status": "running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "database": "not_checked"}


@app.get("/health/database", tags=["Health"])
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "test_query": result.scalar_one()}
    except Exception as exc:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database connection failed. Check the server logs and database configuration.") from exc
