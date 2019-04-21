# -*- coding: UTF-8 -*-
"""
"""
import asyncio
import logging
import os
import traceback
import warnings
from asyncio import CancelledError

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.helpers import DEBUG
from aiopg import sa as aiopg_sa
from alembic import command, config as alembic_conf
from datetime import datetime

from psutil import NoSuchProcess

from webstats.config import Config, StatsConfig
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


_DEFAULT_JOBS = (
    ('data_clean_up', 60 * 60 * 10),  # each 10 hours
    ('vacuum', 60 * 60 * 24)  # each day
)


async def init_task(local_app):
    """

    :param local_app:
    :return:
    """

    async def _worker(func, timeout):
        while True:
            print(datetime.now(), func.__name__)
            try:
                await func(local_app)
                await asyncio.sleep(timeout)
            except CancelledError as _:
                return
            except Exception as excp:
                _LOGER.exception(excp)
                print(excp)
                traceback.print_exc()

    def __collect_workers(*args):
        for group in args:
            for name, timeout in group:
                func = getattr(stats, name, None)
                if not callable(func):
                    warnings.warn('{} is not callable'.format(name))
                    continue
                yield _worker(func, timeout)

    local_app['stats_collector'] = asyncio.gather(
        *list(__collect_workers(_DEFAULT_JOBS, local_app.stats_config.system))
    )

    async def __task():
        await local_app['stats_collector']

    local_app.loop.create_task(__task())


def service():
    """

    :return: ServiceWebApplication
    """
    APP.on_startup.append(init_pg)
    APP.on_cleanup.append(close_pg)
    APP.stats_config = StatsConfig.find_config('sxmonitoring')
    if DEBUG:
        try:
            import aiohttp_debugtoolbar
        except ImportError as _:
            pass
        else:
            aiohttp_debugtoolbar.setup(APP)

    aiohttp_jinja2.setup(
        APP,
        loader=jinja2.FileSystemLoader(CURRENT_DIR + "/../templates/")
    )
    return APP


def run(host=None, port=8080, path=None, pid_file=None):
    app_ = service()
    app_.on_startup.append(init_db)
    app_.on_startup.append(init_task)
    app_.on_cleanup.insert(0, close_stats)
    __lock_file = pid_file
    if not pid_file:
        for lock_path in ['/run', '/var/run', app_.stats_config.config_path]:
            if os.path.exists(lock_path) and os.access(lock_path, os.W_OK):
                __lock_file = os.path.join(lock_path, 'sxmonitoring.lock')
                break
        else:
            raise SystemError('Could not create lock file')

    if os.path.exists(__lock_file):
        try:
            import psutil
            with open(__lock_file, 'r') as pid_file:
                psutil.Process(int(pid_file.read()))
        except ImportError as _:
            pass
        except (NoSuchProcess, ValueError) as _:
            os.remove(__lock_file)

    if os.path.exists(__lock_file):
        raise SystemExit('Application already running. {0}'.format(__lock_file))

    def _inner(*args):
        if os.path.exists(__lock_file):
            os.remove(__lock_file)

    import atexit
    atexit.register(_inner)

    try:
        with open(__lock_file, 'w+') as lock:
            lock.write(str(os.getpid()))
            lock.flush()
            web.run_app(app_, host=host, port=port, path=path)
    except Exception as _:
        if os.path.exists(__lock_file):
            os.remove(__lock_file)