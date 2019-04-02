# -*- coding: UTF-8 -*-
"""
"""
import asyncio

import aiohttp_jinja2
from aiohttp import web
from yarl import URL

from webstats.models.cpu import Cpu
from webstats.models.disk_io import DiskIO
from webstats.models.imap import Imap
from webstats.models.memory import Memory
from webstats.models.tomcat import Tomcat
from .system.platform import Platform
from .models.per_cpu import PerCpu


@aiohttp_jinja2.template('index.html')
async def index(request):
    platform = Platform()
    jre, packages = await asyncio.gather(platform.jre, platform.packages)
    data = dict(platform.items())
    data['jre'] = jre
    data['packages'] = packages
    data['static_base_url'] = URL.build(scheme='', host=request.host)
    return data


_TIME_FROM_MAP = (
    ('fromWeek', '{:d} week'),
    ('fromDays', '{:d} day'),
    ('fromHours', '{:d} hour'),
    ('fromMin', '{:d} minute'),
)

_TIME_TO_MAP = (
    ('toWeek', '{:d} week'),
    ('toDays', '{:d} day'),
    ('toHours', '{:d} hour'),
    ('toMin', '{:d} minute'),
)


def build_time_range(request):
    """

    :param request:
    :return:
    """
    def __build(items):
        res = ''
        for item in items:
            val = request.query.get(item[0])
            if val and val.isdigit():
                res += ' ' + item[1].format(int(val))
        return res
    from_query = __build(_TIME_FROM_MAP)
    to_query = __build(_TIME_TO_MAP)

    if not to_query:
        to_query = ' NOW() '
    else:
        to_query = "(NOW() - INTERVAL '{}')".format(to_query)
    if not from_query:
        from_query = "(NOW() - INTERVAL '1 hour')"
    else:
        from_query = "(NOW() - INTERVAL '{}')".format(from_query)
    return from_query, to_query


async def per_cpu(request):
    res = PerCpu.stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in res
    })


async def cpu(request):
    res = Cpu.stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        0: item[0] async for item in res
    })


async def physical_mem(request):
    res = Memory.physical_stats(request.app.db_engine,
                                build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })


async def swap_mem(request):
    res = Memory.swap_stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })


async def disk_io(request):
    res = DiskIO.stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in res
    })


async def tomcat(request):
    res = Tomcat.stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in res
    })


async def tomcat_utilization(request):
    res = Tomcat.utilization_stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })


async def tomcat_other_utilization(request):
    res = Tomcat.utilization_other_stats(request.app.db_engine,
                                         build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })


async def imap(request):
    res = Imap.stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in res
    })


async def imap_utilization(request):
    res = Imap.utilization_stats(request.app.db_engine, build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })


async def imap_other_utilization(request):
    res = Imap.utilization_other_stats(request.app.db_engine,
                                         build_time_range(request))
    return web.json_response({
        item[0]: item[1] async for item in await res
    })
