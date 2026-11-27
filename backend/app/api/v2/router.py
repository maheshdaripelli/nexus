from fastapi import APIRouter
from fastapi.routing import APIRoute
from app.api.v1.router import api_router as v1_router
from app.api.v2.members import router as invitations_router

from app.api.v2.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(dashboard_router)
api_router.include_router(invitations_router)
# Reuse unchanged endpoints, excluding the replaced invitation POST.
for route in v1_router.routes:
    if isinstance(route, APIRoute) and route.path == "/organizations/{organization_id}/invitations" and "POST" in route.methods:
        continue
    if isinstance(route, APIRoute) and route.path == "/organizations/{organization_id}/dashboard/stats" and "GET" in route.methods:
        continue
    api_router.routes.append(route)
