# -*- coding: UTF-8 -*-
"""
"""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_imap = sa.Table(
    'imap',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', JSONB),
)

__SQL_MAIN = """
with dict as (
    select t.ts, t.data 
    from imap t
    where {}
    order by t.ts ASC
)
"""


_SQL_ALL = __SQL_MAIN + """
select t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from ( select ts, jsonb_object_keys(dict.data) as key, dict.data as data from dict) t2
group by t2.key
"""


_SQL_UTILIZATION = __SQL_MAIN + """
select t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from
     (
       select
              unnest(ARRAY['disks_write_per_sec', 'disks_read_per_sec', 
              'memory_swap', 'memory_uss', 'cpu']) as key,
              ts,
              dict.data as data
       from dict

       )
     as t2
group by t2.key

"""

_SQL_UTILIZATION_OTHER = __SQL_MAIN + """
select t2.key,
       jsonb_agg(jsonb_build_array(t2.ts, t2.data ->> t2.key)) as data
from
     (
       select
              unnest(ARRAY['fds', 'zombie', 'close_wait_to_imap', 'threads', 
              'connections', 'procs']) as key,
              ts,
              dict.data as data
       from dict

       )
     as t2
group by t2.key

"""

_SQL_INSTANCES = """
select jsonb_object_keys(t.data) as name
from tomcat t
{}
group by name
"""


class Imap(BaseModel):

    table = _imap

    @staticmethod
    async def utilization_stats(engine: 'aiopg._EngineContextManager',
                                time_filter):
        return Imap.stats(engine, time_filter, _SQL_UTILIZATION)

    @staticmethod
    async def utilization_other_stats(engine: 'aiopg._EngineContextManager',
                                      time_filter):
        return Imap.stats(engine, time_filter, _SQL_UTILIZATION_OTHER)

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager',
                    time_filter, sql_template=_SQL_ALL):
        time_range = Imap.time_range_str(time_filter)

        async with engine.acquire() as conn:
            res = conn.execute(sql_template.format(time_range))
            async for values in res:
                yield values
