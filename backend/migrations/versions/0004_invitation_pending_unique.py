"""Allow historical invitations while enforcing one active invitation per address."""
from alembic import op

revision = "0004_invitation_pending_unique"
down_revision = "0003_membership_custom_roles"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_invitation_org_email_status", "invitations", type_="unique")
    op.create_index(
        "uq_invitation_pending_org_email",
        "invitations",
        ["organization_id", "email"],
        unique=True,
        postgresql_where="status = 'pending'",
    )


def downgrade():
    op.drop_index("uq_invitation_pending_org_email", table_name="invitations")
    op.create_unique_constraint(
        "uq_invitation_org_email_status",
        "invitations",
        ["organization_id", "email", "status"],
    )