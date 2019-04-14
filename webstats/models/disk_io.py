# -*- coding: UTF-8 -*-
"""
"""

from sqlalchemy import func

from . import sa, metadata, BaseModel

_DISK_IO_TABLE = sa.Table(
    'disk_io',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('read_count', sa.Integer, comment='number of reads'),
    sa.Column('write_count', sa.Integer, comment='number of writes'),
    sa.Column('read_bytes', sa.Integer, comment='number of bytes read'),
    sa.Column('write_bytes', sa.Integer, comment='number of bytes written'),
    sa.Column('read_time', sa.Integer,
              comment='time spent reading from disk (in ms)'),
    sa.Column('write_time', sa.Integer,
              comment='time spent writing to disk (in ms)')
)

_SQL = """
SELECT
    {}
FROM disk_io t
WHERE {}
"""

_COLUMN_AGG = """jsonb_agg(json_build_array(t.ts, t.{0}) ORDER BY t.ts) {0}
"""


class DiskIO(BaseModel):
    table = _DISK_IO_TABLE

    counters = ('read_count', 'write_count', 'read_bytes', 'write_bytes',
                'read_time', 'write_time')

    @staticmethod
    async def stats(
            engine: 'aiopg._EngineContextManager',
            time_filter,
            fields=None):
        if fields is None:
            fields = DiskIO.counters
        else:
            fields = set(fields) & set(DiskIO.counters)

        select = ','.join([_COLUMN_AGG.format(field) for field in fields])
        time_range = DiskIO.time_range_str(time_filter)
        async with engine.acquire() as conn:
            async for item in conn.execute(_SQL.format(select, time_range)):
                for field in fields:
                    yield field, item[field]
