"""Add invitations, RBAC, team membership, audit, refresh and platform admin tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_domain"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "membership_id", name="uq_team_member"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_membership_id", "team_members", ["membership_id"])

    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="member"),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_invitations_organization_id", "invitations", ["organization_id"])
    op.create_index("ix_invitations_email", "invitations", ["email"])

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(300)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "name", name="uq_role_org_name"),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(300), nullable=False),
    )
    op.create_index("ix_permissions_key", "permissions", ["key"])

    op.bulk_insert(
        sa.table("permissions",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("key", sa.String(100)),
            sa.column("description", sa.String(300)),
        ),
        [
            {"id": __import__("uuid").uuid4(), "key": "members.read", "description": "View organization members"},
            {"id": __import__("uuid").uuid4(), "key": "members.manage", "description": "Invite, update and remove members"},
            {"id": __import__("uuid").uuid4(), "key": "teams.read", "description": "View teams"},
            {"id": __import__("uuid").uuid4(), "key": "teams.manage", "description": "Create and manage teams"},
            {"id": __import__("uuid").uuid4(), "key": "roles.read", "description": "View roles and permissions"},
            {"id": __import__("uuid").uuid4(), "key": "roles.manage", "description": "Manage roles and permissions"},
            {"id": __import__("uuid").uuid4(), "key": "audit.read", "description": "View organization audit history"},
            {"id": __import__("uuid").uuid4(), "key": "workspace.manage", "description": "Manage workspace settings"},
        ],
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(80)),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for col in ("organization_id", "actor_user_id", "action", "created_at"):
        op.create_index(f"ix_audit_logs_{col}", "audit_logs", [col])

    op.create_table(
        "platform_admins",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("access_level", sa.String(30), nullable=False, server_default="super_admin"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("platform_admins")
    for col in ("organization_id", "actor_user_id", "action", "created_at"):
        op.drop_index(f"ix_audit_logs_{col}", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")
    op.drop_index("ix_permissions_key", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_roles_organization_id", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_invitations_email", table_name="invitations")
    op.drop_index("ix_invitations_organization_id", table_name="invitations")
    op.drop_table("invitations")
    op.drop_index("ix_team_members_membership_id", table_name="team_members")
    op.drop_index("ix_team_members_team_id", table_name="team_members")
    op.drop_table("team_members")
