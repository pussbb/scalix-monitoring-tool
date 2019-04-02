# -*- coding: UTF-8 -*-
"""
"""
import asyncio
import concurrent
import re
from collections import defaultdict

import psutil

from webstats.models.imap import Imap
from webstats.models.tomcat import Tomcat
from .models.disk_io import DiskIO
from .models.memory import Memory
from .models.per_cpu import PerCpu
from .models.cpu import Cpu


__all__ = ('per_cpus', 'cpus', 'cpu_clean', 'memory')

_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=30)


def _run_blocking(*args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_EXECUTOR, *args)


async def per_cpus(db_engine: 'aiopg._EngineContextManager'):
    if db_engine is None:
        return enumerate(await _run_blocking(psutil.cpu_percent, 1, True))

    await PerCpu.add(db_engine,
                     data=await _run_blocking(psutil.cpu_percent, 1, True))


async def cpus(db_engine: 'aiopg._EngineContextManager'):
    if db_engine is None:
        return enumerate(await _run_blocking(psutil.cpu_percent, 1))
    await Cpu.add(db_engine, data=await _run_blocking(psutil.cpu_percent, 1))


async def cpu_clean(db_engine: 'aiopg._EngineContextManager'):
    sql_clean = "delete from {} t where t.ts < (NOW() - INTERVAL '2 week')"
    async with db_engine.acquire() as conn:
        for table in [PerCpu, Cpu, Memory, DiskIO, Tomcat]:
            try:
                await conn.execute(sql_clean.format(table.table.fullname))
            except Exception as exp:
                print(exp)


async def vacuum(db_engine: 'aiopg._EngineContextManager'):
    async with db_engine.acquire() as conn:
        await conn.execute('VACUUM FULL')


_MEM_PHYSICAL = (['available', 'used', 'free', 'cached'], Memory.PHYSICAL)
_MEM_SWAP = (['total', 'used', 'free'], Memory.SWAP)


async def memory(db_engine: 'aiopg._EngineContextManager'):
    physical = psutil.virtual_memory()
    swap = psutil.swap_memory()
    for item in [_MEM_PHYSICAL + (physical,), _MEM_SWAP + (swap,)]:
        fields, type_id, container = item
        data = {field: getattr(container, field) for field in fields}
        await Memory.add(db_engine, data=data, type=type_id)


_DISK_IO = ['read_count', 'write_count', 'read_bytes', 'write_bytes',
            'read_time', 'write_time', 'busy_time']


async def disk_io(db_engine: 'aiopg._EngineContextManager'):
    """
    https://github.com/giampaolo/psutil/blob/master/scripts/iotop.py
    :param db_engine:
    :return:
    """
    disks_before = psutil.disk_io_counters()
    await asyncio.sleep(1)
    disks_after = psutil.disk_io_counters()
    disks_read_per_sec = disks_after.read_bytes - disks_before.read_bytes
    disks_write_per_sec = disks_after.write_bytes - disks_before.write_bytes
    data = {
        'disks_read_per_sec': disks_read_per_sec,
        'disks_write_per_sec': disks_write_per_sec,
    }
    await DiskIO.add(db_engine, data=data)


_RE_INSTANCE = re.compile(r'/var/opt/scalix/(\w{,2})/tomcat/.*')


async def tomcat(db_engine: 'aiopg._EngineContextManager'):
    java_procs = []
    for proc in psutil.process_iter():
        if 'java' not in proc.name():
            continue
        instance_name = _RE_INSTANCE.findall(''.join(proc.cmdline()))
        if not instance_name:
            continue
        proc._before_disk_io = proc.io_counters()
        proc._instance_name = instance_name[0]
        java_procs.append(proc)

    await asyncio.sleep(1)

    data = {}
    for proc in java_procs[:]:
        pdata = {}
        with proc.oneshot():
            io_counters = proc.io_counters()
            pdata['disks_read_per_sec'] = (
                    io_counters.read_bytes - proc._before_disk_io.read_bytes
            )
            pdata['disks_write_per_sec'] = (
                    io_counters.write_bytes - proc._before_disk_io.write_bytes
            )

            mem_info = proc.memory_full_info()
            pdata['memory_uss'] = mem_info.uss
            pdata['memory_swap'] = mem_info.swap
            pdata['cpu'] = proc.cpu_percent()
            pdata['fds'] = proc.num_fds()
            pdata['threads'] = proc.num_threads()
            connections = proc.connections()
            pdata['connections'] = len(connections)
            close_wait = 0
            close_wait_to_java = 0
            close_wait_to_imap = 0
            for conn in connections:
                if 'CLOSE_WAIT' in conn.status:
                    if conn.raddr:
                        if '80' in str(conn.raddr.port):
                            close_wait_to_java += 1
                        elif '143' in str(conn.raddr.port):
                            close_wait_to_imap += 1
                    close_wait += 1
            pdata['close_wait_conn'] = close_wait
            pdata['close_wait_to_java'] = close_wait_to_java
            pdata['close_wait_to_imap'] = close_wait_to_imap
            data[proc._instance_name] = pdata
    await Tomcat.add(db_engine, data=data)


async def imap(db_engine: 'aiopg._EngineContextManager'):
    imap_procs = []
    for proc in psutil.process_iter():
        proc._zombie = False
        try:
            if not proc.is_running():
                continue
            if 'in.imap41d' not in proc.name():
                continue
            proc._zombie = proc.status() == psutil.STATUS_ZOMBIE
            proc._before_disk_io = proc.io_counters()
            imap_procs.append(proc)
        except psutil.ZombieProcess as _:
            proc._zombie = True

    await asyncio.sleep(1)

    data = defaultdict(int)
    data['zombie'] = 0
    for proc in imap_procs[:]:
        data['procs'] += 1
        if proc._zombie:
            data['zombie'] += 1
        with proc.oneshot():
            io_counters = proc.io_counters()
            data['disks_read_per_sec'] += (
                    io_counters.read_bytes - proc._before_disk_io.read_bytes
            )
            data['disks_write_per_sec'] += (
                    io_counters.write_bytes - proc._before_disk_io.write_bytes
            )

            mem_info = proc.memory_full_info()
            data['memory_uss'] += mem_info.uss
            data['memory_swap'] += mem_info.swap
            data['cpu'] = +proc.cpu_percent()
            data['fds'] = +proc.num_fds()
            data['threads'] += proc.num_threads()
            connections = proc.connections()
            data['connections'] += len(connections)
            close_wait = 0
            for conn in connections:
                if 'CLOSE_WAIT' in conn.status:
                    close_wait += 1
            data['close_wait_conn'] = close_wait
    await Imap.add(db_engine, data=data)
