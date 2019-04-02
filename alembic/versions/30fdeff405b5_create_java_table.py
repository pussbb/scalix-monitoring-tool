"""create java table

Revision ID: 30fdeff405b5
Revises: 27a01aaecaa7
Create Date: 2019-04-01 19:08:58.515609

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

revision = '30fdeff405b5'
down_revision = '27a01aaecaa7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tomcat',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('data', JSONB),
    )


def downgrade():
    pass
