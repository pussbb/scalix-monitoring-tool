#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module to group log entries in tomcat logs

"""
from __future__ import unicode_literals, with_statement, print_function
import re
import shutil
import sys
import os
import glob
from collections import defaultdict


CURRENT_DIR = os.path.realpath(os.path.dirname(__file__)).encode()

EXPR = re.compile(
    r'^(?P<datetime>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}.\d{1,})\s+'
    r'\[(?P<level>.*?)\](.*)\[(?P<caller>\S+\.\S+?):\d+\](?P<descr>.*)'
    r'$'.encode()
)

IGNORE_LEVELS = [
    b'INFO',
    None
]

IGNORE_CALLERS = [
    None,
    b'Observance.getLatestOnset',
    b'Message.parseRecipientHeader',
    b'ContactsFormatter.formatMessage'
]

CONFIG_PATH = (
    os.path.realpath(os.path.dirname(__file__)),
    os.path.join(os.sep, 'etc', 'opt'),
    os.path.join(os.sep, 'etc', 'opt', 'scalix'),
    os.path.join(os.sep, 'etc', 'opt', 'scalix-tomcat'),
)


class ErrorDescription(object):
    """Helper class for first line with error description

    """
    __slots__ = ('datetime', 'level', 'caller', 'description')

    def __init__(self, datetime, level, caller, descr):
        self.datetime = datetime
        self.level = level.strip()
        self.caller = caller
        self.description = descr

    @property
    def caller_class(self):
        """Class name of caller

        :return: str
        """
        return self.caller.split(b'.')[0]


def log_files(path):
    """List of log files in directory

    :param path:
    :return: list
    """
    if not os.path.isdir(path):
        return []
    return glob.glob(os.path.join(os.path.realpath(path), "*.log"))


def get_line_description(line):
    """Checks line if its starting line of exception

    :param line:
    :return: ErrorDescription
    """
    if not line:
        return None
    match = EXPR.match(line)
    if match:
        return ErrorDescription(**match.groupdict())
    return None


def ignore_error(error):
    """Should we ignore this log entry or not

    :param error: dict
    :return: boolean
    """
    if not error:
        return True

    return (error.level in IGNORE_LEVELS
            or error.caller in IGNORE_CALLERS)


def group_errors(filename):
    """

    :param filename:
    :return:
    """
    res = defaultdict(list)
    stacktrace = []
    summary = defaultdict(int)

    def __save_data(err):
        if not err:
            return
        summary[err.caller_class] += 1
        res[err.caller_class].extend(stacktrace[:-1])

    if not os.path.isfile(filename):
        print('Found `{0}` but its directory '.format(filename))
        return res, summary

    with open(filename, 'rb') as lfd:
        prev = None
        for line in lfd:
            stacktrace.append(line)
            error = get_line_description(line)
            if ignore_error(error):
                if error:
                    __save_data(prev)
                    prev = None
                    del stacktrace[:]
                continue
            __save_data(prev)
            prev = error
            del stacktrace[:-1]
    del stacktrace[:]
    return res, summary


def parse_files(path):
    """Walks thru .log files in specified directory. Creates directory with
    log file filename and each log entry(caller) is in separate file

    :param path:  AnyStr
    :return:
    """
    for file_ in log_files(path):
        print('Proccessing', file_, '...')
        grouped_errors, summary = group_errors(file_)
        if not grouped_errors:
            continue
        result_dir = os.path.join(CURRENT_DIR, os.path.basename(file_).encode())
        if os.path.exists(result_dir):
            print('Directory {0} exists. Deleting ...'.format(result_dir))
            shutil.rmtree(result_dir)
        os.mkdir(result_dir)
        for key, value in grouped_errors.items():
            print("Instance `{0}` has"
                  "logged {1} item('s)".format(key.decode(), summary.get(key)))
            with open(os.path.join(result_dir, key + b'.log'), 'ab') as dest_fd:
                dest_fd.writelines(value)


def process_dirs(*args):
    """Parse log files in specified directories

    :param args: list of directories
    :return:
    """
    for directory in args:
        if os.path.isdir(directory):
            print('Searching for log files in directory', directory)
            parse_files(directory)
        else:
            print('Directory', directory, 'is not a directory')


def get_config_file(filename):
    """Get absolute filename for existing config filename

    :param filename: AnyStr
    :return:
    """
    for config_path in CONFIG_PATH:
        conf_file = os.path.join(config_path, filename)
        if not os.path.isfile(conf_file):
            continue
        return conf_file


def load_ignore_list():
    """

    :return:
    """
    ignore_ = (("ignore_java_levels", IGNORE_LEVELS),
               ("ignore_java_callers", IGNORE_CALLERS))
    for filename, dest in ignore_:
        conf_file = get_config_file(filename)
        if not conf_file:
            continue
        with open(conf_file, "rb") as conf_fd:
            dest.extend(conf_fd.read().splitlines())


load_ignore_list()

if __name__ == '__main__':
    process_dirs(*sys.argv[1:] or [os.getcwd()])
