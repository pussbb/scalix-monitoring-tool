"""create disk_io table

Revision ID: 27a01aaecaa7
Revises: 227bc5f0709c
Create Date: 2019-04-01 11:46:40.193630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

revision = '27a01aaecaa7'
down_revision = '227bc5f0709c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'disk_io',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('data', JSONB),
    )


def downgrade():
    pass
