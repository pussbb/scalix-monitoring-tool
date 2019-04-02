# -*- coding: UTF-8 -*-
"""
"""
import platform as pyplatform
import socket
from typing import AnyStr

from .jreinfo import JREInfo
from ..utils.shell_command import ShellCommand, ShellCommandRuntimeException

_SYS_INFO_TEMPLATE = """Linux Distribution: {linux_distribution}
Platform: {platform}
Architecture: {architecture}
Machine: {machine}
Node: {node}
System: {system}
Release: {release}
Version: {version}
FQDN: {fqdn}
"""


class Platform:
    """Platform information
    """
    __slots__ = ('architecture', 'platform', 'machine', 'node',
                 'system', 'release', 'version', 'linux_distribution',
                 '_fqdn')

    def __init__(self):
        self._fqdn = None
        for func in self.__slots__:
            val = getattr(pyplatform, func, lambda: None)()
            if isinstance(val, (tuple, set, list)):
                val = ' '.join(val)
            setattr(self, func, val)

    def __unicode__(self):
        return self.__str__().encode()

    def __repr__(self):
        return self.__str__()

    def items(self):
        for func in self.__slots__:
            yield func.lstrip('_'), getattr(self, func.lstrip('_'))

    def __str__(self):
        return _SYS_INFO_TEMPLATE.format(**dict(self.items()))

    def is_64bit(self):
        """Is current system x64 bit system
        :return: bool
        """
        return self.machine == 'x86_64'

    def is_32bit(self):
        """Is current system x86 bit system
        :return: bool
        """
        return self.machine in ['i386', 'i586', 'i686']

    @property
    def fqdn(self):
        """Get Fully qualified domain name (FQDN)
        :return: AnyString
        """
        if not self._fqdn:
            self._fqdn = socket.getfqdn()
        return self._fqdn

    @property
    def ip_addresses(self):
        """List of IP addresses available in system
        :return: list
        """
        try:
            return socket.gethostbyaddr(self.fqdn)[-1]
        except socket.error as _:
            return ['127.0.0.1']

    @property
    def ip_addr(self) -> AnyStr:
        """System IP address or 127.0.0.1
        :return: AnyStr
        """
        return self.ip_addresses[0]

    def assigned_to_local_ip(self) -> bool:
        """
        :return: bool
        """
        return self.ip_addr.startswith('127.')

    @property
    async def jre(self) -> JREInfo:
        return await self.jre_version()

    async def jre_version(self) -> JREInfo:
        """
        :return:
        """
        res = await ShellCommand('java', '-version').run()
        if res.exit_code == 0:
            return JREInfo(res.response)
        return None

    @property
    async def packages(self):
        """
        :return:
        """
        cmds = [
            ShellCommand('rpm', '-qa', "'*scalix*'"),
            ShellCommand('dpkg', '--list', "'*scalix*'")
        ]

        for cmd in cmds:
            try:
                res = await cmd()
                if res.exit_code == 0:
                    return res.response
            except ShellCommandRuntimeException as _:
                pass
        return None
