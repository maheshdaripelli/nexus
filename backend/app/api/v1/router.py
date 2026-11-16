from fastapi import APIRouter
from app.api.v1 import auth, dashboard, members, organizations, platform, teams

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
api_router.include_router(members.router)
api_router.include_router(dashboard.router)
api_router.include_router(platform.router)
