# -*- coding: UTF-8 -*-
"""
"""

import collections
from typing import Any


def is_iterable(item: Any) -> bool:
    """Checks if variable is sequence excluding string and bytes
    :param item: Any
    :return: boolean
    """
    return isinstance(item, collections.Iterable) and not \
        isinstance(item, (bytes, str))
