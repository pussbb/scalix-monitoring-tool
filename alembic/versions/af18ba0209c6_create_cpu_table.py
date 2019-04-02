"""create cpu table

Revision ID: af18ba0209c6
Revises: 4c3c5a217e93
Create Date: 2019-03-31 15:55:00.936922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func

revision = 'af18ba0209c6'
down_revision = '4c3c5a217e93'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cpu',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('data', sa.Integer),
    )


def downgrade():
    pass
