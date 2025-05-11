"""Initial migration

Revision ID: 01
Revises: 
Create Date: 2025-05-10 19:13:49.123037

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add timer_started_at column to the task table
    op.add_column('task', sa.Column('timer_started_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove timer_started_at column from the task table
    op.drop_column('task', 'timer_started_at')
