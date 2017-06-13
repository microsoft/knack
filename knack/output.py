# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function, unicode_literals

import errno
import platform
import json
import traceback
from collections import OrderedDict
from six import StringIO, text_type, u, string_types

from .util import CLIError, CommandResultItem
from .events import EVENT_INVOKER_POST_PARSE_ARGS, EVENT_PARSER_GLOBAL_CREATE
from .log import get_logger

logger = get_logger(__name__)


def _decode_str(output):
    if not isinstance(output, text_type):
        output = u(str(output))
    return output


class _ComplexEncoder(json.JSONEncoder):

    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, bytes) and not isinstance(o, str):
            return o.decode()
        return json.JSONEncoder.default(self, o)


def _format_json(obj):
    result = obj.result
    # OrderedDict.__dict__ is always '{}', to persist the data, convert to dict first.
    input_dict = dict(result) if hasattr(result, '__dict__') else result
    return json.dumps(input_dict, indent=2, sort_keys=True, cls=_ComplexEncoder,
                      separators=(',', ': ')) + '\n'


def _format_json_color(obj):
    from pygments import highlight, lexers, formatters
    return highlight(_format_json(obj), lexers.JsonLexer(), formatters.TerminalFormatter())  # pylint: disable=no-member


def _format_table(obj):
    result = obj.result
    try:
        if obj.table_transformer and not obj.is_query_active:
            result = obj.table_transformer(result)
        result_list = result if isinstance(result, list) else [result]
        should_sort_keys = not obj.is_query_active and not obj.table_transformer
        to = _TableOutput(should_sort_keys)
        return to.dump(result_list)
    except:
        logger.debug(traceback.format_exc())
        raise CLIError("Table output unavailable. "
                       "Use the --query option to specify an appropriate query. "
                       "Use --debug for more info.")


def _format_tsv(obj):
    result = obj.result
    result_list = result if isinstance(result, list) else [result]
    return _TsvOutput.dump(result_list)


class OutputProducer(object):

    ARG_DEST = '_output_format'

    _FORMAT_DICT = {
        'json': _format_json,
        'jsonc': _format_json_color,
        'table': _format_table,
        'tsv': _format_tsv,
    }

    @staticmethod
    def on_global_arguments(ctx, **kwargs):
        arg_group = kwargs.get('arg_group')
        arg_group.add_argument('--output', '-o', dest=OutputProducer.ARG_DEST,
                               choices=list(OutputProducer._FORMAT_DICT),
                               default=ctx.config.get('core', 'output', fallback='json'),
                               help='Output format',
                               type=str.lower)

    @staticmethod
    def handle_output_argument(ctx, **kwargs):
        args = kwargs.get('args')
        # Set the output type for this invocation
        ctx.invocation.data['output'] = getattr(args, OutputProducer.ARG_DEST)
        # We've handled the argument so remove it
        delattr(args, OutputProducer.ARG_DEST)

    def __init__(self, ctx=None):
        self.ctx = ctx
        self.ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, OutputProducer.on_global_arguments)
        self.ctx.register_event(EVENT_INVOKER_POST_PARSE_ARGS, OutputProducer.handle_output_argument)

    def out(self, obj, formatter=None, out_file=None):  # pylint: disable=no-self-use
        if not isinstance(obj, CommandResultItem):
            raise TypeError('Expected {} got {}'.format(CommandResultItem.__name__, type(obj)))
        import colorama
        if platform.system() == 'Windows':
            out_file = colorama.AnsiToWin32(out_file).stream
        output = formatter(obj)
        try:
            print(output, file=out_file, end='')
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                pass
            else:
                raise
        except UnicodeEncodeError:
            print(output.encode('ascii', 'ignore').decode('utf-8', 'ignore'),
                  file=out_file, end='')

    def get_formatter(self, format_type):  # pylint: disable=no-self-use
        return OutputProducer._FORMAT_DICT[format_type]


class _TableOutput(object):  # pylint: disable=too-few-public-methods

    SKIP_KEYS = ['id', 'type', 'etag']

    def __init__(self, should_sort_keys=False):
        self.should_sort_keys = should_sort_keys

    @staticmethod
    def _capitalize_first_char(x):
        return x[0].upper() + x[1:] if x else x

    def _auto_table_item(self, item):
        new_entry = OrderedDict()
        try:
            keys = sorted(item) if self.should_sort_keys and isinstance(item, dict) else item.keys()
            for k in keys:
                if k in _TableOutput.SKIP_KEYS:
                    continue
                if item[k] and not isinstance(item[k], (list, dict, set)):
                    new_entry[_TableOutput._capitalize_first_char(k)] = item[k]
        except AttributeError:
            # handles odd cases where a string/bool/etc. is returned
            if isinstance(item, list):
                for col, val in enumerate(item):
                    new_entry['Column{}'.format(col + 1)] = val
            else:
                new_entry['Result'] = item
        return new_entry

    def _auto_table(self, result):
        if isinstance(result, list):
            new_result = []
            for item in result:
                new_result.append(self._auto_table_item(item))
            return new_result
        return self._auto_table_item(result)

    def dump(self, data):
        from tabulate import tabulate
        table_data = self._auto_table(data)
        table_str = tabulate(table_data, headers="keys", tablefmt="simple") if table_data else ''
        if table_str == '\n':
            raise ValueError('Unable to extract fields for table.')
        return table_str + '\n'


class _TsvOutput(object):  # pylint: disable=too-few-public-methods

    @staticmethod
    def _dump_obj(data, stream):
        if isinstance(data, list):
            stream.write(str(len(data)))
        elif isinstance(data, dict):
            # We need to print something to avoid mismatching
            # number of columns if the value is None for some instances
            # and a dictionary value in other...
            stream.write('')
        else:
            to_write = data if isinstance(data, string_types) else str(data)
            stream.write(to_write)

    @staticmethod
    def _dump_row(data, stream):
        separator = ''
        if isinstance(data, (dict, list)):
            if isinstance(data, OrderedDict):
                values = data.values()
            elif isinstance(data, dict):
                values = [value for _, value in sorted(data.items())]
            else:
                values = data

            # Iterate through the items either sorted by key value (if dict) or in the order
            # they were added (in the cases of an ordered dict) in order to make the output
            # stable
            for value in values:
                stream.write(separator)
                _TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, list):
            for value in data:
                stream.write(separator)
                _TsvOutput._dump_obj(value, stream)
                separator = '\t'
        elif isinstance(data, bool):
            _TsvOutput._dump_obj(str(data).lower(), stream)
        else:
            _TsvOutput._dump_obj(data, stream)
        stream.write('\n')

    @staticmethod
    def dump(data):
        io = StringIO()
        for item in data:
            _TsvOutput._dump_row(item, io)

        result = io.getvalue()
        io.close()
        return result
