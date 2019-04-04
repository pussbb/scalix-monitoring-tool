# -*- coding: UTF-8 -*-
"""
"""
import asyncio
import logging
import traceback

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.helpers import DEBUG
from aiopg import sa as aiopg_sa
from alembic import command, config as alembic_conf
from datetime import datetime


from .routes import setup_routes
from . import stats, CURRENT_DIR


class ServiceWebApplication(web.Application):
    """just to be happy
    """
    def __getattr__(self, key):
        return self[key]


APP = ServiceWebApplication()
setup_routes(APP)

ALEMBIC_CFG = alembic_conf.Config(CURRENT_DIR + '/../alembic.ini')
_LOGER = logging.getLogger('aiohttp.server')


async def init_db(local_app):

    async with local_app.get('db_engine').acquire() as conn:
        ALEMBIC_CFG.attributes['connection'] = conn
        command.upgrade(ALEMBIC_CFG, "head")


async def init_pg(local_app):
    local_app['db_engine'] = await aiopg_sa.create_engine(
        ALEMBIC_CFG.get_main_option('sqlalchemy.url').replace("+psycopg2", ""),
        loop=local_app.loop
    )


async def close_pg(local_app):
    """

    :param local_app:
    :return:
    """
    local_app.db_engine.close()
    await local_app.db_engine.wait_closed()


async def close_stats(local_app):
    """

    :param local_app:
    :return:
    """
    if local_app['stats_collector']:
        print("STOPPING stats_collector")
        local_app['stats_collector'].cancel()


async def init_task(local_app):
    """

    :param local_app:
    :return:
    """
    jobs = {
        'per_cpus': 20,
        'cpus': 20,
        'memory': 20,
        'disk_io': 20,
        'tomcat': 20,
        'imap': 20,
        'cpu_clean': 60 * 60 * 10,  # each 10 hours
        'vacuum': 60 * 60 * 24  # each day
    }

    async def _worker(func, timeout):
        while True:
            print(datetime.now(), func.__name__)
            try:
                await func(local_app['db_engine'])
                await asyncio.sleep(timeout)
            except Exception as excp:
                _LOGER.exception(excp)
                print(excp)
                traceback.print_exc()

    def __collect_workers():
        for name, timeout in jobs.items():
            func = getattr(stats, name)
            if not callable(func):
                continue
            yield _worker(func, timeout)

    local_app['stats_collector'] = asyncio.gather(*list(__collect_workers()))

    async def __task():
        await local_app['stats_collector']

    local_app.loop.create_task(__task())


def service():
    """

    :return:
    """
    APP.on_startup.append(init_pg)

    APP.on_cleanup.append(close_stats)
    APP.on_cleanup.append(close_pg)
    if DEBUG:
        import aiohttp_debugtoolbar
        aiohttp_debugtoolbar.setup(APP)
    aiohttp_jinja2.setup(APP,
                         loader=jinja2.FileSystemLoader(
                             CURRENT_DIR + "/../templates/")
                         )
    return APP


def run(host=None, port=8080, path=None):
    app_ = service()
    app_.on_startup.append(init_db)
    app_.on_startup.append(init_task)
    web.run_app(app_, host=host, port=port, path=path)
