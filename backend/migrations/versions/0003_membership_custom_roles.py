"""Allow organization memberships to use custom roles."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_membership_custom_roles"
down_revision = "0002_domain"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "memberships",
        sa.Column("custom_role_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_memberships_custom_role_id_roles",
        "memberships",
        "roles",
        ["custom_role_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_memberships_custom_role_id", "memberships", ["custom_role_id"])


def downgrade():
    op.drop_index("ix_memberships_custom_role_id", table_name="memberships")
    op.drop_constraint("fk_memberships_custom_role_id_roles", "memberships", type_="foreignkey")
    op.drop_column("memberships", "custom_role_id")
