from app.api.v1.router import api_router as v1
from app.api.v2.router import api_router as v2

def test_dashboard_version_isolated():
    path = "/organizations/{organization_id}/dashboard/stats"
    for router, version in [(v1, "v1"), (v2, "v2")]:
        matches = [r for r in router.routes if r.path == path and "GET" in r.methods]
        assert len(matches) == 1
        assert matches[0].endpoint.__module__ == f"app.api.{version}.dashboard"
