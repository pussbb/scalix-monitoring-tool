"""initial

Revision ID: 4c3c5a217e93
Revises: 
Create Date: 2019-03-28 07:57:02.267106

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
from sqlalchemy.dialects.postgresql import JSONB

revision = '4c3c5a217e93'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'per_cpu',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('data', JSONB),
    )


def downgrade():
    pass
