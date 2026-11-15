"""Create initial Nexus tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('full_name', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('email'))
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(160), nullable=False),
        sa.Column('slug', sa.String(180), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('slug'))
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])
    op.create_table('memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(30), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_membership_org_user'))
    op.create_index('ix_memberships_organization_id', 'memberships', ['organization_id'])
    op.create_index('ix_memberships_user_id', 'memberships', ['user_id'])
    op.create_table('teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'name', name='uq_team_org_name'))
    op.create_index('ix_teams_organization_id', 'teams', ['organization_id'])

def downgrade():
    op.drop_index('ix_teams_organization_id', table_name='teams')
    op.drop_table('teams')
    op.drop_index('ix_memberships_user_id', table_name='memberships')
    op.drop_index('ix_memberships_organization_id', table_name='memberships')
    op.drop_table('memberships')
    op.drop_index('ix_organizations_slug', table_name='organizations')
    op.drop_table('organizations')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
