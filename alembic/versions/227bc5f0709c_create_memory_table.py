"""create memory table

Revision ID: 227bc5f0709c
Revises: af18ba0209c6
Create Date: 2019-04-01 10:11:45.326311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

revision = '227bc5f0709c'
down_revision = 'af18ba0209c6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'memory',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('type', sa.SmallInteger),
        sa.Column('data', JSONB),
    )


def downgrade():
    pass
