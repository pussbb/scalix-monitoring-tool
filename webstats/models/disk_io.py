# -*- coding: UTF-8 -*-
"""
"""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_disk_io = sa.Table(
    'disk_io',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', JSONB),
)

_SQL = """
select
       t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from (
      select t.ts, jsonb_object_keys(t.data) as key, t.data
      from disk_io t
      where {}
      order by t.ts ASC
      ) t2

group by t2.key
"""


class DiskIO(BaseModel):
    table = _disk_io

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager', time_filter):
        time_range = DiskIO.time_range_str(time_filter)
        async with engine.acquire() as conn:
            async for item in conn.execute(_SQL.format(time_range)):
                yield item
