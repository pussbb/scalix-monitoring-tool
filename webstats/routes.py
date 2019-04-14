# -*- coding: UTF-8 -*-
"""
"""
from aiohttp import web

from . import CURRENT_DIR
from .views import (
    index, cpu, per_cpu, swap_mem, physical_mem, disk_io,
    tomcat, tomcat_other_utilization,
    imap_other_utilization, imap, tomcat_cpu_utilization,
    tomcat_memory_utilization, tomcat_disk_io_utilization,
    tomcat_conn_utilization, imap_cpu_utilization, imap_memory_utilization,
    imap_disk_io_utilization, imap_conn_utilization, disk_io_bytes,
    disk_io_counts)


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
    app.router.add_get('/tomcat_cpu_utilization', tomcat_cpu_utilization)
    app.router.add_get('/tomcat_memory_utilization', tomcat_memory_utilization)
    app.router.add_get('/tomcat_disk_io_utilization',
                       tomcat_disk_io_utilization)
    app.router.add_get('/tomcat_conn_utilization', tomcat_conn_utilization)
    app.router.add_get('/tomcat_other_utilization', tomcat_other_utilization)
    app.router.add_get('/imap', imap)
    app.router.add_get('/imap_cpu_utilization', imap_cpu_utilization)
    app.router.add_get('/imap_memory_utilization', imap_memory_utilization)
    app.router.add_get('/imap_disk_io_utilization', imap_disk_io_utilization)
    app.router.add_get('/imap_conn_utilization', imap_conn_utilization)
    app.router.add_get('/imap_other_utilization', imap_other_utilization)
    app.add_routes([web.static('/static', CURRENT_DIR + '/../static')])
