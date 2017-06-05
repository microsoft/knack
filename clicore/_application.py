# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import CommandResultItem
from ._parser import CLICommandParser
from .commands import CLICommandsLoader
from ._events import (EVENT_APPLICATION_PRE_CMD_TBL_CREATE, EVENT_APPLICATION_POST_CMD_TBL_CREATE,
                      EVENT_APPLICATION_CMD_TBL_LOADED, EVENT_APPLICATION_PRE_PARSE_ARGS,
                      EVENT_APPLICATION_POST_PARSE_ARGS, EVENT_APPLICATION_TRANSFORM_RESULT,
                      EVENT_APPLICATION_FILTER_RESULT)


class Application(object):

    def __init__(self,
                 ctx=None,
                 parser_cls=CLICommandParser,
                 commands_loader_cls=CLICommandsLoader):
        self.ctx = ctx
        self.ctx.invocation_data['command'] = 'unknown'
        self._global_parser = parser_cls.create_global_parser(ctx=self.ctx)
        self.parser = parser_cls(ctx=self.ctx, prog=self.ctx.name, parents=[self._global_parser])
        self.commands_loader = commands_loader_cls(ctx=self.ctx)

    def _filter_params(self, args):  # pylint: disable=no-self-use
        # Consider - we are using any args that start with an underscore (_) as 'private'
        # arguments and remove them from the arguments that we pass to the actual function.
        params = dict([(key, value)
                       for key, value in args.__dict__.items()
                       if not key.startswith('_')])
        params.pop('func', None)
        params.pop('command', None)
        return params

    def execute(self, args):
        self.ctx.raise_event(EVENT_APPLICATION_PRE_CMD_TBL_CREATE, args=args)
        cmd_tbl = self.commands_loader.generate_command_table(args)
        self.ctx.raise_event(EVENT_APPLICATION_POST_CMD_TBL_CREATE, cmd_tbl=cmd_tbl)
        self.parser.load_command_table(cmd_tbl)
        self.ctx.raise_event(EVENT_APPLICATION_CMD_TBL_LOADED, parser=self.parser)

        self.ctx.raise_event(EVENT_APPLICATION_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.ctx.raise_event(EVENT_APPLICATION_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        self.ctx.invocation_data['command'] = parsed_args.command

        params = self._filter_params(parsed_args)

        cmd_result = parsed_args.func(params)

        event_data = {'result': cmd_result}
        self.ctx.raise_event(EVENT_APPLICATION_TRANSFORM_RESULT, event_data=event_data)
        self.ctx.raise_event(EVENT_APPLICATION_FILTER_RESULT, event_data=event_data)

        return CommandResultItem(event_data['result'],
                                 table_transformer=cmd_tbl[parsed_args.command].table_transformer,
                                 is_query_active=self.ctx.invocation_data['query_active'])
