# -*- coding: UTF-8 -*-
"""
"""


from sqlalchemy import func

from . import sa, metadata, BaseModel

_CPUS_TABLE = sa.Table(
    'cpu',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', sa.Integer),
)


_SQL = """
select array_agg(array[t.ts::text, t.data::text] order by t.ts) as data 
from cpu t
where {}
"""


class Cpu(BaseModel):
    table = _CPUS_TABLE

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager', time_filter):
        time_range = Cpu.time_range_str(time_filter)
        async with engine.acquire() as conn:
            async for item in conn.execute(_SQL.format(time_range)):
                yield item
