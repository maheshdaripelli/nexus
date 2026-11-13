from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Release database connections when the API process shuts down."""
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Nexus User and Workspace Management Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "application": "Nexus",
        "message": "Welcome to Nexus API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Liveness check: confirms that the API process is responding."""
    return {
        "status": "healthy",
        "database": "not_checked",
    }


@app.get("/health/database", tags=["Health"])
async def database_health(db: AsyncSession = Depends(get_db)):
    """Readiness check: executes a lightweight query against PostgreSQL."""
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar_one()

        return {
            "status": "healthy",
            "database": "connected",
            "test_query": value,
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check server logs and database configuration.",
        )
