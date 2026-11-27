from app.api.v1.router import api_router as v1
from app.api.v2.router import api_router as v2

def test_invitation_version_isolated():
    path = "/organizations/{organization_id}/invitations"
    def endpoint(router):
        matches = [r for r in router.routes if r.path == path and "POST" in r.methods]
        assert len(matches) == 1
        return matches[0].endpoint
    assert endpoint(v1).__module__ == "app.api.v1.members"
    assert endpoint(v2).__module__ == "app.api.v2.members"
