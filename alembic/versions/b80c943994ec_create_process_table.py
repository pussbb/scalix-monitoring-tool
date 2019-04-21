"""create process table

Revision ID: b80c943994ec
Revises: 0fafdaf3311a
Create Date: 2019-04-20 15:25:23.188900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func

revision = 'b80c943994ec'
down_revision = '0fafdaf3311a'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('imap')
    op.create_table(
        'processes',
        sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now(),
                  index=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('procs', sa.Integer, comment='number of running proc\'s'),
        sa.Column('zombie', sa.Integer, comment='number of zombie proc\'s'),
        sa.Column('disks_read_per_sec', sa.BigInteger,
                  comment='Disk io read per sec'),
        sa.Column('disks_write_per_sec', sa.BigInteger,
                  comment='Disk io write per sec'),
        sa.Column('memory_uss', sa.BigInteger, comment='virtual memory used'),
        sa.Column('memory_swap', sa.BigInteger, comment='swap memory used'),
        sa.Column('cpu', sa.Float, comment='cpu used'),
        sa.Column('fds', sa.BigInteger, comment='opened file descriptors'),
        sa.Column('threads', sa.BigInteger, comment='threads'),
        sa.Column('connections', sa.BigInteger, comment='connections in total'),
        sa.Column('close_wait_conn', sa.BigInteger,
                  comment='CLOSE_WAIT connections in total'),
    )


def downgrade():
    pass
