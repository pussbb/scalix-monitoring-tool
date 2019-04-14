# -*- coding: UTF-8 -*-
"""
"""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_MEMORY_TABLE = sa.Table(
    'memory',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('type', sa.SmallInteger),
    sa.Column('data', JSONB),
)

_SQL = """
select
       t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from (
      select t.ts, jsonb_object_keys(t.data) as key, t.data
      from memory t
      WHERE t.type = {}
      AND 
        {}
      order by t.ts ASC
      ) t2

group by t2.key
"""


class Memory(BaseModel):
    table = _MEMORY_TABLE
    PHYSICAL = 1
    SWAP = 2

    @staticmethod
    async def __get_stats(engine: 'aiopg._EngineContextManager',
                          time_filter,
                          type_):
        time_range = Memory.time_range_str(time_filter)
        async with engine.acquire() as conn:
            async for item in conn.execute(_SQL.format(type_, time_range)):
                yield item

    @staticmethod
    async def physical_stats(engine: 'aiopg._EngineContextManager',
                             time_filter):
        return Memory.__get_stats(engine, time_filter, Memory.PHYSICAL)

    @staticmethod
    async def swap_stats(engine: 'aiopg._EngineContextManager',
                         time_filter):
        return Memory.__get_stats(engine, time_filter, Memory.SWAP)
