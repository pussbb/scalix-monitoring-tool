"""create diskio simplify

Revision ID: 0fafdaf3311a
Revises: c8d8a9737fe9
Create Date: 2019-04-14 08:31:36.697432

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision = '0fafdaf3311a'
down_revision = 'c8d8a9737fe9'
branch_labels = None
depends_on = None


def upgrade():
    table_name = 'disk_io'
    op.drop_column(table_name, 'data')
    op.execute('TRUNCATE {} RESTART IDENTITY;'.format(table_name))
    op.add_column(
        table_name,
        sa.Column('read_count', sa.BigInteger, comment='number of reads')
    )

    op.add_column(
        table_name,
        sa.Column('write_count', sa.BigInteger, comment='number of writes')
    )
    op.add_column(
        table_name,
        sa.Column('read_bytes', sa.BigInteger, comment='number of bytes read')
    )
    op.add_column(
        table_name,
        sa.Column('write_bytes', sa.BigInteger, comment='number of bytes written')
    )
    op.add_column(
        table_name,
        sa.Column('read_time', sa.BigInteger,
                  comment='time spent reading from disk (in ms)')
    )
    op.add_column(
        table_name,
        sa.Column('write_time', sa.BigInteger,
                  comment='time spent writing to disk (in ms)')
    )


def downgrade():
    pass
