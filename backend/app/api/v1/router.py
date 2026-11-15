from fastapi import APIRouter
from app.api.v1 import auth, organizations, teams
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(teams.router)
