# -*- coding: UTF-8 -*-
"""
"""
from typing import List

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_imap = sa.Table(
    'imap',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', JSONB),
)

_SQL_MAIN = """
with dict as (
    select t.ts, t.data 
    from imap t
    where {}
    order by t.ts ASC
)
"""


_SQL_ALL = _SQL_MAIN + """
select t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from ( select ts, jsonb_object_keys(dict.data) as key, dict.data as data from dict) t2
group by t2.key
"""


_SQL_BY_FIELDS = """
select t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from
     (
       select
              unnest(ARRAY{}) as key,
              ts,
              dict.data as data
       from dict

       )
     as t2
group by t2.key

"""


class Imap(BaseModel):

    table = _imap

    @staticmethod
    async def stats_for(engine: 'aiopg._EngineContextManager',
                        time_filter,
                        fields: List):
        return Imap.stats(
            engine,
            time_filter,
            _SQL_MAIN + _SQL_BY_FIELDS.format(fields)
        )

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager',
                    time_filter, sql_template=_SQL_ALL):
        time_range = Imap.time_range_str(time_filter)

        async with engine.acquire() as conn:
            res = conn.execute(sql_template.format(time_range))
            async for values in res:
                yield values
