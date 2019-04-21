# -*- coding: UTF-8 -*-
"""
"""

from sqlalchemy import func, text

from . import sa, metadata, BaseModel

_PROCESSES_TABLE = sa.Table(
    'processes',
    metadata,
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

_SQL = """
SELECT
    {}
FROM processes t
WHERE name = :name  AND {}
"""

_COLUMN_AGG = """jsonb_agg(json_build_array(t.ts, t.{0}) ORDER BY t.ts) {0}
"""


class Process(BaseModel):
    table = _PROCESSES_TABLE

    counters = [
        column.name for column in _PROCESSES_TABLE.columns
        if column.name not in ['ts', 'name']
    ]

    @staticmethod
    async def stats(
            engine: 'aiopg._EngineContextManager',
            proc_name,
            time_filter,
            fields=None):
        if fields is None:
            fields = Process.counters
        else:
            fields = set(fields) & set(Process.counters)

        query = _SQL.format(
            ','.join([_COLUMN_AGG.format(field) for field in fields]),
            Process.time_range_str(time_filter)
        )
        print(query)
        async with engine.acquire() as conn:
            async for item in conn.execute(text(query), name=proc_name):
                for field in fields:
                    yield field, item[field]