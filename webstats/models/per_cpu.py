# -*- coding: UTF-8 -*-
"""
"""


from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_PER_CPU_TABLE = sa.Table(
    'per_cpu',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', JSONB),
)


_SQL = """
SELECT t2.cpu_id as cpu,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.cpu_id)) as data
FROM (
       SELECT generate_series(0, jsonb_array_length(t.data) - 1)
            AS cpu_id, t.ts, t.data
       FROM per_cpu t
       where {}
       ORDER BY t.ts ASC
     ) AS t2
GROUP BY t2.cpu_id
"""


class PerCpu(BaseModel):
    table = _PER_CPU_TABLE

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager', time_filter):
        time_range = PerCpu.time_range_str(time_filter)
        async with engine.acquire() as conn:
            async for item in conn.execute(_SQL.format(time_range)):
                yield item
