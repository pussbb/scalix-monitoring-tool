# -*- coding: UTF-8 -*-
"""
"""
from typing import List

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from . import sa, metadata, BaseModel

_tomcat = sa.Table(
    'tomcat',
    metadata,
    sa.Column('ts', sa.DateTime(True), nullable=False, default=func.now()),
    sa.Column('data', JSONB),
)

_SQL_MAIN = """
with dict as (
    select t.ts, jsonb_extract_path_text(t.data, '{}')::jsonb as data 
    from tomcat t
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

_SQL_INSTANCES = """
select jsonb_object_keys(t.data) as name
from tomcat t
where {}
group by name
"""


class Tomcat(BaseModel):
    table = _tomcat

    @staticmethod
    async def stats_for(engine: 'aiopg._EngineContextManager',
                        time_filter,
                        fields: List):
        return Tomcat.stats(
            engine,
            time_filter,
            _SQL_MAIN + _SQL_BY_FIELDS.format(fields)
        )

    @staticmethod
    async def stats(engine: 'aiopg._EngineContextManager',
                    time_filter,
                    sql_template=_SQL_ALL):
        time_range = Tomcat.time_range_str(time_filter)
        instances = []
        async with engine.acquire() as conn:
            for item in await conn.execute(_SQL_INSTANCES.format(time_range)):
                instances.append(item[0])

        async with engine.acquire() as conn:
            for instance in instances:
                res = conn.execute(sql_template.format(instance, time_range))
                async for values in res:
                    yield '{} ({})'.format(values[0], instance), values[1]
