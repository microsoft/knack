# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
from datetime import date, time, datetime, timedelta
from enum import Enum


class CommandResultItem(object):  # pylint: disable=too-few-public-methods
    def __init__(self, result, table_transformer=None, is_query_active=False):
        self.result = result
        self.table_transformer = table_transformer
        self.is_query_active = is_query_active


class CLIError(Exception):
    """Base class for exceptions that occur during
    normal operation of the CLI.
    Typically due to user error and can be resolved by the user.
    """
    pass


class CtxTypeError(TypeError):

    def __init__(self, obj):
        from .cli import CLI
        super(CtxTypeError, self).__init__('expected instance of {} got {}'.format(CLI.__name__,
                                                                                   obj.__class__.__name__))


def ensure_dir(d):
    """ Create a directory if it doesn't exist """
    if not os.path.isdir(d):
        os.makedirs(d)


def normalize_newlines(str_to_normalize):
    return str_to_normalize.replace('\r\n', '\n')


KEYS_CAMELCASE_PATTERN = re.compile('(?!^)_([a-zA-Z])')


def to_camel_case(s):
    return re.sub(KEYS_CAMELCASE_PATTERN, lambda x: x.group(1).upper(), s)


def to_snake_case(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def todict(obj, value_filter=None):  # pylint: disable=too-many-return-statements
    """ 
    Convert an object to a dictionary. Use 'value_filter' to ignore specified values
    """
    if isinstance(obj, dict):
        return {k: todict(v, value_filter) for (k, v) in obj.items() if (not value_filter or value_filter(obj, k, v))}
    elif isinstance(obj, list):
        return [todict(a, value_filter) for a in obj]
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, (date, time, datetime)):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        return str(obj)
    elif hasattr(obj, '_asdict'):
        return todict(obj._asdict(), value_filter)
    elif hasattr(obj, '__dict__'):
        return dict([(to_camel_case(k), todict(v, value_filter))
                     for k, v in obj.__dict__.items()
                     if not callable(v) and not k.startswith('_') and (not value_filter or value_filter(obj, k, v))])
    return obj