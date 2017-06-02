# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import CommandResultItem
from ._parser import CLICommandParser

EVENT_APPLICATION_CMD_TBL_CREATE = 'Application.OnCommandTableCreate'
EVENT_APPLICATION_CMD_TBL_LOADED = 'Application.OnCommandTableLoaded'
EVENT_APPLICATION_PRE_PARSE_ARGS = 'Application.OnPreParseArgs'
EVENT_APPLICATION_POST_PARSE_ARGS = 'Application.OnPostParseArgs'


class Application(object):

    def __init__(self,
                 ctx=None,
                 parser_cls=CLICommandParser):
        self.ctx = ctx
        self.ctx.invocation_data['command'] = 'unknown'
        self.parser = parser_cls(ctx=self.ctx, prog=self.ctx.name)

    def execute(self, args):
        cmd_tbl = self.generate_command_table(args)
        self.ctx.raise_event(EVENT_APPLICATION_CMD_TBL_CREATE, cmd_tbl=cmd_tbl)
        self.parser.load_command_table(cmd_tbl)
        self.ctx.raise_event(EVENT_APPLICATION_CMD_TBL_LOADED, parser=self.parser)

        self.ctx.raise_event(EVENT_APPLICATION_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.ctx.raise_event(EVENT_APPLICATION_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        self.ctx.invocation_data['command'] = parsed_args.command

        return CommandResultItem([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}])

    def generate_command_table(self, args):  # pylint: disable=no-self-use,unused-argument
        # TODO Generate the command table appropriately
        return {'abc': 1, 'xyz': 2}
