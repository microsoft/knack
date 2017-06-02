# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import CommandResultItem
from ._parser import CLICommandParser
from .commands import CLICommandsLoader
from ._events import (EVENT_APPLICATION_PRE_CMD_TBL_CREATE, EVENT_APPLICATION_POST_CMD_TBL_CREATE,
                      EVENT_APPLICATION_CMD_TBL_LOADED, EVENT_APPLICATION_PRE_PARSE_ARGS,
                      EVENT_APPLICATION_POST_PARSE_ARGS)


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

        # TODO should pass in the args here to func.
        cmd_result = parsed_args.func()

        # self.raise_event(self.TRANSFORM_RESULT, cmd_result=cmd_result)
        # self.raise_event(self.FILTER_RESULT, cmd_result=cmd_result)

        return CommandResultItem(cmd_result)
