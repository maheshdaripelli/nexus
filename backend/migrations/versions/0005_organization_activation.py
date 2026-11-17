"""Add organization activation status for platform-level suspension."""
from alembic import op
import sqlalchemy as sa

revision = "0005_organization_activation"
down_revision = "0004_invitation_pending_unique"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("organizations", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])

def downgrade():
    op.drop_index("ix_organizations_is_active", table_name="organizations")
    op.drop_column("organizations", "is_active")