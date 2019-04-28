# -*- coding: UTF-8 -*-
"""
"""
import json


def to_json(data, **kwargs):
    """Helper class to dump data from DB.Model(SQLAlchemy) class
    :param data:
    :param kwargs:
    :return:
    """

    def default(obj):
        """wrapper function
        :param obj:
        :return:
        """
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode()

        if obj and hasattr(obj, 'dump'):
            return obj.dump()

        if isinstance(data, dict):
            return {str(key): to_json(data[key]) for key in data}

        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder().default(obj)

    kwargs['indent'] = 0
    kwargs['default'] = default
    kwargs['ensure_ascii'] = False
    kwargs['skipkeys'] = True
    return json.dumps(data, **kwargs)
