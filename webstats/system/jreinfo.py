# -*- coding: UTF-8 -*-
"""
"""
import re
from typing import Any, AnyStr

from ..utils.common import is_iterable


MIN_VER = 8.0
MAX_VER = 11.9999


def _clean_up_ver(ver: AnyStr) -> AnyStr:
    """Removes any characters that are not a digit and limits number of
    integers divided by '.'

    :param ver: AnyStr
    :return: clean version number
    """
    if not ver:
        return b''
    return b'.'.join([item for item in ver.split(b'.') if item.isdigit()][:3])


class JREInfo:
    """
    """

    __slots__ = ('version', 'origin_version', '_raw')

    __version_reg_expr = re.compile(rb'^(java|openjdk|[\w\d\.,]+)'
                                    rb' version "(.*)"(.*)$')

    __ibm_check_reg_expr = re.compile(rb'IBM\s(\w+)\sVM')

    def __init__(self, data: Any):
        self._raw = []
        self.version = None
        self.origin_version = None
        if not is_iterable(data):
            if not isinstance(data, (bytes, str)):
                raise RuntimeError('Not supported type')
            self._raw = data.splitlines()
        self.__parse()

    def __parse(self):
        for line in self._raw:
            version = self.__version_reg_expr.search(line.strip())
            if not version:
                continue
            self.origin_version = version.group(2)
            self.version = _clean_up_ver(self.origin_version)

    def is_ibm_jre(self) -> bool:
        """
        :return:
        """
        for line in self._raw:
            if self.__ibm_check_reg_expr.search(line):
                return True
        return False

    def __repr__(self):
        return self.version

    def __bytes__(self):
        return self.__str__().encode()

    def __str__(self):
        return "\n".join([i.decode() for i in self._raw])

    def is_supported(self) -> bool:
        """Check if current jre version is in range of supported JRE

        :return: bool
        """
        if not self.version:
            return False
        if self.version.startswith(b'1.'):
            ver = self.version[2:]
        else:
            ver = self.version
        return MIN_VER <= float(b'.'.join(ver.split(b'.')[:2])) <= MAX_VER
