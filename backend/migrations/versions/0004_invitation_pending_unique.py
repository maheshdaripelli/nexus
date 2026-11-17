"""Allow historical invitations while enforcing one active invitation per address."""
from alembic import op

revision = "0004_invitation_pending_unique"
down_revision = "0003_membership_custom_roles"
branch_labels = None
depends_on = None


def upgrade():
    # The original 0002 migration never created uq_invitation_org_email_status.
    # Create the partial unique index directly; it applies only to pending invites.
    op.create_index(
        "uq_invitation_pending_org_email",
        "invitations",
        ["organization_id", "email"],
        unique=True,
        postgresql_where="status = 'pending'",
    )


def downgrade():
    op.drop_index("uq_invitation_pending_org_email", table_name="invitations")
