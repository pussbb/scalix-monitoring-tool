# -*- coding: UTF-8 -*-
"""
"""
from aiohttp import web

from . import CURRENT_DIR
from .views import (
    index, cpu, per_cpu, swap_mem, physical_mem, disk_io,
    tomcat, tomcat_other_utilization, tomcat_utilization,
    imap_other_utilization, imap, imap_utilization)


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/cpu', cpu)
    app.router.add_get('/per_cpu', per_cpu)
    app.router.add_get('/swap_mem', swap_mem)
    app.router.add_get('/physical_mem', physical_mem)
    app.router.add_get('/disk_io', disk_io)
    app.router.add_get('/tomcat', tomcat)
    app.router.add_get('/tomcat_other_utilization', tomcat_other_utilization)
    app.router.add_get('/tomcat_utilization', tomcat_utilization)
    app.router.add_get('/imap', imap)
    app.router.add_get('/imap_other_utilization', imap_other_utilization)
    app.router.add_get('/imap_utilization', imap_utilization)
    app.add_routes([web.static('/static', CURRENT_DIR + '/../static')])
