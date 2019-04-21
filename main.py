# -*- coding: UTF-8 -*-
"""
"""
import argparse
from pathlib import Path

from webstats import service


async def web_app():
    return service.service()


def cron():
    service.run(host=None, port=None, path='/tmp/webstats.sock')


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Process some stats.')
    PARSER.add_argument('--daemon', '-d',
                        dest="daemonize",
                        action='store_true')
    PARSER.add_argument('--pid',
                        type=Path,
                        help="Path to the data directory"
                        )
    ARGS = PARSER.parse_args()
    if ARGS.daemonize:
        service.run(host=None, port=None, path='/tmp/webstats.sock',
                    pid_file=ARGS.pid)
    else:
        service.run(pid_file=ARGS.pid)
