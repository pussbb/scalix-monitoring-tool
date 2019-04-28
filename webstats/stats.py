# -*- coding: UTF-8 -*-
"""
"""
import asyncio
import concurrent
import re
import time
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
import atexit

import psutil
from psutil import CONN_CLOSE_WAIT

from webstats.models.process import Process
from webstats.models.tomcat import Tomcat
from .models.disk_io import DiskIO
from .models.memory import Memory
from .models.per_cpu import PerCpu
from .models.cpu import Cpu


__all__ = ('per_cpu', 'cpu', 'data_clean_up', 'memory', 'vacuum', 'processes',
           'disk_io', 'tomcat', 'processes')

_PROC_EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=10)
_THREAD_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=50)


def _close_pool():
    try:
        _PROC_EXECUTOR.shutdown(False)
    except BaseException as _:
        pass

    try:
        _THREAD_EXECUTOR.shutdown(False)
    except BaseException as _:
        pass


#atexit.register(_close_pool)


def _run_blocking(*args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_THREAD_EXECUTOR, *args)


def _run_blocking_p(*args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_PROC_EXECUTOR, *args)


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


def _tomcat():
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

    if not java_procs:
        return {}

    time.sleep(1)
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
    return data


async def tomcat(local_app: 'web.Application'):
    data = await _run_blocking_p(_tomcat)
    if data:
        await Tomcat.add(local_app.db_engine, data=data)


def _processes(proc_names):
    data = defaultdict(list)
    for proc in psutil.process_iter():
        try:
            for needed in proc_names:
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

    def _grab_data(process, iob):
        proc_data = defaultdict(int)
        try:
            if process.status() == psutil.STATUS_ZOMBIE:
                proc_data['zombie'] = 1
            with process.oneshot():
                ioa = process.io_counters()
                proc_data['disks_read_per_sec'] += (
                    ioa.read_bytes - iob.read_bytes
                )
                proc_data['disks_write_per_sec'] += (
                    ioa.write_bytes - iob.write_bytes
                )
                mem_info = process.memory_full_info()
                proc_data['memory_uss'] = mem_info.uss
                proc_data['memory_swap'] = mem_info.swap
                proc_data['cpu'] = process.cpu_percent()
                proc_data['fds'] = process.num_fds()
                proc_data['threads'] = process.num_threads()
                connections = process.connections()
                proc_data['connections'] = len(connections)
                close_wait = 0
                for conn in connections:
                    if conn.status == CONN_CLOSE_WAIT:
                        close_wait += 1
                proc_data['close_wait_conn'] = close_wait
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exp:
            print(exp)
        return proc_data

    res = {}
    if not data:
        return res

    time.sleep(1)

    with ThreadPoolExecutor(max_workers=len(data)) as pool:
        threads = {}
        for name, procs in data.items():
            for proc in procs:
                ppid, piob = proc
                threads[pool.submit(_grab_data, ppid, piob)] = name

        for future in concurrent.futures.as_completed(threads):
            try:
                name, data = threads[future], future.result()
            except Exception as exc:
                print(exc)
            else:
                item = res.get(name, {})
                if not item:
                    data['procs'] = 1
                    res[name] = data
                    continue
                item['procs'] += 1
                for key, val in data.items():
                    item[key] = item.get(key, 0) + val
    return [(name, val) for name, val in res.items()]


async def processes(local_app: 'web.Application', procs=None):
    if not procs:
        procs = {
            item.name: item.stats for item in local_app.stats_config.processes
        }
    for proc, data in await _run_blocking_p(_processes, procs):
        data['name'] = proc
        await Process.add(local_app.db_engine, **data)
