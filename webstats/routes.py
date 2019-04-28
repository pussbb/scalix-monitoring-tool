# -*- coding: UTF-8 -*-
"""
"""
from aiohttp import web

from . import CURRENT_DIR
from .views import (
    index, cpu, per_cpu, swap_mem, physical_mem, disk_io,
    tomcat, tomcat_other_utilization, tomcat_cpu_utilization,
    tomcat_memory_utilization, tomcat_disk_io_utilization,
    tomcat_conn_utilization, disk_io_bytes, disk_io_counts, process,
    scalix_server_logs, scalix_tomcat_logs)


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/cpu', cpu)
    app.router.add_get('/per_cpu', per_cpu)
    app.router.add_get('/swap_mem', swap_mem)
    app.router.add_get('/physical_mem', physical_mem)
    app.router.add_get('/disk_io', disk_io)
    app.router.add_get('/disk_io_bytes', disk_io_bytes)
    app.router.add_get('/disk_io_counts', disk_io_counts)
    app.router.add_get('/tomcat', tomcat)
    app.router.add_get('/scalix_server_logs', scalix_server_logs)
    app.router.add_get('/scalix_tomcat_logs', scalix_tomcat_logs)
    app.router.add_get('/tomcat_cpu_utilization', tomcat_cpu_utilization)
    app.router.add_get('/tomcat_memory_utilization', tomcat_memory_utilization)
    app.router.add_get('/tomcat_disk_io_utilization',
                       tomcat_disk_io_utilization)
    app.router.add_get('/tomcat_conn_utilization', tomcat_conn_utilization)
    app.router.add_get('/tomcat_other_utilization', tomcat_other_utilization)
    app.router.add_get(r'/process/{name:[\w\d\.]+}/', process)
    app.router.add_get(r'/process/{name:[\w\d\.]+}/{fields_key:\w+}', process)
    app.add_routes([web.static('/static', CURRENT_DIR + '/../static')])
