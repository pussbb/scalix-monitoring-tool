# -*- coding: UTF-8 -*-
"""
"""
import os

from webstats import CURRENT_DIR, PARENT_DIR

try:
    from ConfigParser import ConfigParser
except ImportError as _:
    from configparser import ConfigParser


_CONFIG_PATH = (
    PARENT_DIR,
    CURRENT_DIR,
    os.path.join(os.sep, 'etc', 'opt'),
    os.path.join(os.sep, 'etc', 'opt', 'scalix'),
    os.path.join(os.sep, 'etc', 'opt', 'scalix-monitoring'),
)


class DictWrapper(dict):
    """Helper wrapper for a dict with a few helper things

    """

    def __getattr__(self, item):
        """ x.__getattr__('name') <==> x.name

        :param item:
        :return:
        """
        return self[item]


class Default(DictWrapper):
    """Generic class to ignore missing elements

    """

    def __getitem__(self, item):
        """  x.__getitem__(y) <==> x[y]

        :param item: str
        :return: Any
        """
        if item not in self:
            return ''
        return super(Default, self).__getitem__(item)

    def __missing__(self, key):
        """

        :param key: str
        :return: Any
        """
        return key


class Config(DictWrapper):
    """Base class to read configuration

    """

    def from_envvar(self, key):
        """Read filename path from environment variable

        :param key: string name of environment variable
        :return: self
        """
        value = os.environ.get(key)
        if not value:
            raise RuntimeError('Environment key {0} is empty'
                               ' or not found'.format(key))
        return self.from_config_file(value)

    def from_config_file(self, filename):
        """Read settings from configuration file

        :param filename: string settings filename
        :return:
        """
        filename = os.path.realpath(os.path.expanduser(filename))
        if not os.path.exists(filename):
            raise RuntimeError('File {0} does not exists'.format(filename))
        config_parser = ConfigParser(allow_no_value=True)
        config_parser.read(filename)
        for section in config_parser.sections():
            self[section] = Default(list(self.get(section, {}))
                                    + config_parser.items(section))
        return self

    @staticmethod
    def int_value(value):
        if not value:
            return 0
        return int(value)

    @staticmethod
    def to_list(value):
        """Converts coma separated string into list

        :param value: str
        :return: list
        """
        if not value:
            return
        for item in value.split(','):
            if not item:
                continue
            yield item.strip(' ')

    @staticmethod
    def boolean_value(val):
        """Converts string to boolean value

        :param val: str
        :return: boolean
        """
        if not val:
            return False
        return {'1': True, 'yes': True, 'true': True, 'on': True,
                '0': False, 'no': False, 'false': False,
                'off': False}.get(str(val).lower(), False)

    @classmethod
    def find_config(cls, name, **kwargs):
        """

        :param name:
        :param kwargs:
        :return:
        """
        config = cls({**{'name': name}, **kwargs})
        for path in _CONFIG_PATH:
            config_file = '{0}{1}{2}.ini'.format(path, os.sep, name)
            if os.path.exists(config_file):
                config.from_config_file(config_file)
                config.config_file = config_file
                config.config_path = path
                break
        else:
            raise RuntimeError('Could not find {}.ini'.format(name))
        return config


class StatsConfig(Config):

    @property
    def system(self):
        for name, timeout in self['system'].items():
            timeout = Config.int_value(timeout)
            if timeout <= 0:
                continue
            yield (name, timeout)

    @property
    def processes(self):
        for item in self:
            if not item.endswith('-process'):
                continue
            yield self[item]