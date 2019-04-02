"""create imap table

Revision ID: c8d8a9737fe9
Revises: 30fdeff405b5
Create Date: 2019-04-01 21:08:32.964387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

revision = 'c8d8a9737fe9'
down_revision = '30fdeff405b5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'imap',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('data', JSONB),
    )


def downgrade():
    pass
