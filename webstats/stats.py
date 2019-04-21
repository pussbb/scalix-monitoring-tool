# -*- coding: UTF-8 -*-
"""
"""
import asyncio
import concurrent
import re
import time
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor

import psutil
from psutil import CONN_CLOSE_WAIT

from webstats.models.process import Process
from webstats.models.tomcat import Tomcat
from .models.disk_io import DiskIO
from .models.memory import Memory
from .models.per_cpu import PerCpu
from .models.cpu import Cpu


__all__ = ('per_cpu', 'cpu', 'data_clean_up', 'memory', 'vacuum')

_EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=10)


def _run_blocking(*args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_EXECUTOR, *args)


async def per_cpu(local_app: 'web.Application'):
    await PerCpu.add(local_app.db_engine,
                     data=await _run_blocking(psutil.cpu_percent, 1, True))


async def cpu(local_app: 'web.Application'):
    await Cpu.add(local_app.db_engine,
                  data=await _run_blocking(psutil.cpu_percent, 1))


async def data_clean_up(local_app: 'web.Application'):
    sql_clean = "delete from {} t where t.ts < (NOW() - INTERVAL '1 week')"
    async with local_app.db_engine.acquire() as conn:
        for table in [PerCpu, Cpu, Memory, DiskIO, Tomcat, Process]:
            try:
                await conn.execute(sql_clean.format(table.table.fullname))
            except Exception as exp:
                print(exp)


async def vacuum(local_app: 'web.Application'):
    async with local_app.db_engine.acquire() as conn:
        await conn.execute('VACUUM FULL')


_MEM_PHYSICAL = (['available', 'used', 'free', 'cached'], Memory.PHYSICAL)
_MEM_SWAP = (['total', 'used', 'free'], Memory.SWAP)


async def memory(local_app: 'web.Application'):
    physical, swap = psutil.virtual_memory(), psutil.swap_memory()
    for item in [_MEM_PHYSICAL + (physical,), _MEM_SWAP + (swap,)]:
        fields, type_id, container = item
        data = {field: getattr(container, field) for field in fields}
        await Memory.add(local_app.db_engine, data=data, type=type_id)


async def disk_io(local_app: 'web.Application'):
    """
    https://github.com/giampaolo/psutil/blob/master/scripts/iotop.py
    :param db_engine:
    :return:
    """
    iob = await _run_blocking(psutil.disk_io_counters)
    await asyncio.sleep(1)
    ioa = await _run_blocking(psutil.disk_io_counters)
    data = {item: getattr(ioa, item) - getattr(iob, item)
            for item in DiskIO.counters}
    await DiskIO.add(local_app.db_engine, **data)


_RE_INSTANCE = re.compile(r'/var/opt/scalix/(\w{,2})/tomcat/.*')


async def tomcat(local_app: 'web.Application'):
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
                if conn.status == CONN_CLOSE_WAIT:
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
    await Tomcat.add(local_app.db_engine, data=data)


def _processes(processes):
    data = defaultdict(list)
    for proc in psutil.process_iter():
        try:
            for needed in processes:
                if needed in proc.name():
                    io_counts = 0
                    try:
                        io_counts = proc.io_counters()
                    except (psutil.AccessDenied, psutil.NoSuchProcess) as _:
                        pass
                    data[needed].append([proc, io_counts])
                    break
            else:
                continue
        except psutil.NoSuchProcess as _:
            pass

    def _grab_data(procs):
        data = defaultdict(int)
        data['zombie'] = 0
        for proc, iob in procs:
            data['procs'] += 1
            try:
                if proc.status() == psutil.STATUS_ZOMBIE:
                    data['zombie'] += 1
                    continue
                with proc.oneshot():
                    ioa = proc.io_counters()
                    data['disks_read_per_sec'] += (
                        ioa.read_bytes - iob.read_bytes
                    )
                    data['disks_write_per_sec'] += (
                        ioa.write_bytes - iob.write_bytes
                    )
                    mem_info = proc.memory_full_info()
                    data['memory_uss'] += mem_info.uss
                    data['memory_swap'] += mem_info.swap
                    data['cpu'] += proc.cpu_percent()
                    data['fds'] += proc.num_fds()
                    data['threads'] += proc.num_threads()
                    connections = proc.connections()
                    data['connections'] += len(connections)
                    close_wait = 0
                    for conn in connections:
                        if conn.status == CONN_CLOSE_WAIT:
                            close_wait += 1
                    data['close_wait_conn'] = close_wait
            except (psutil.NoSuchProcess, psutil.AccessDenied) as exp:
                print(exp)
        return data

    time.sleep(1)
    res = []
    with ThreadPoolExecutor(max_workers=len(data)) as pool:
        procs = {
            pool.submit(_grab_data, val): name for name, val in data.items()
        }
        for future in concurrent.futures.as_completed(procs):
            try:
                name, data = procs[future], future.result()
            except Exception as exc:
                print(exc)
            else:
                res.append((name, data))
    return res


async def processes(local_app: 'web.Application'):
    procs = {
        item.name: item.stats for item in local_app.stats_config.processes
    }
    for proc, data in await _run_blocking(_processes, procs):
        data['name'] = proc
        await Process.add(local_app.db_engine, **data)
