import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException

from pydantic import ValidationError

from app.schemas.member import MemberRoleUpdate
from app.services.authorization import require_permission


class AuthorizationTests(unittest.IsolatedAsyncioTestCase):
    def test_member_role_update_requires_exactly_one_role_source(self):
        MemberRoleUpdate(role="manager")
        MemberRoleUpdate(custom_role_id=uuid4())
        with self.assertRaises(ValidationError):
            MemberRoleUpdate()
        with self.assertRaises(ValidationError):
            MemberRoleUpdate(role="manager", custom_role_id=uuid4())

    async def test_owner_has_all_permissions(self):
        membership = SimpleNamespace(role="owner", custom_role_id=None)
        db = SimpleNamespace(scalar=AsyncMock(return_value=membership))

        result = await require_permission(db, uuid4(), uuid4(), "workspace.manage")

        self.assertIs(result, membership)
        db.scalar.assert_awaited_once()

    async def test_manager_can_manage_teams_but_not_members(self):
        membership = SimpleNamespace(role="manager", custom_role_id=None)
        db = SimpleNamespace(scalar=AsyncMock(return_value=membership))

        result = await require_permission(db, uuid4(), uuid4(), "teams.manage")
        self.assertIs(result, membership)

        with self.assertRaises(HTTPException) as raised:
            await require_permission(db, uuid4(), uuid4(), "members.manage")
        self.assertEqual(raised.exception.status_code, 403)

    async def test_non_member_cannot_access_organization(self):
        db = SimpleNamespace(scalar=AsyncMock(return_value=None))

        with self.assertRaises(HTTPException) as raised:
            await require_permission(db, uuid4(), uuid4(), "teams.read")

        self.assertEqual(raised.exception.status_code, 404)

    async def test_custom_role_permission_is_checked(self):
        membership = SimpleNamespace(role="custom", custom_role_id=uuid4())
        db = SimpleNamespace(scalar=AsyncMock(side_effect=[membership, uuid4()]))

        result = await require_permission(db, uuid4(), uuid4(), "workspace.manage")

        self.assertIs(result, membership)
        self.assertEqual(db.scalar.await_count, 2)

    async def test_custom_role_without_permission_is_denied(self):
        membership = SimpleNamespace(role="custom", custom_role_id=uuid4())
        db = SimpleNamespace(scalar=AsyncMock(side_effect=[membership, None]))

        with self.assertRaises(HTTPException) as raised:
            await require_permission(db, uuid4(), uuid4(), "workspace.manage")

        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()