# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

EVENT_PARSER_GLOBAL_CREATE = 'CommandParser.OnGlobalArgumentsCreate'


class CLICommandParser(argparse.ArgumentParser):

    def create_global_parser(self):
        global_parser = argparse.ArgumentParser(prog=self.ctx.name, add_help=False)
        arg_group = global_parser.add_argument_group('global', 'Global Arguments')
        self.ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=arg_group)
        return global_parser

    def __init__(self, ctx=None, **kwargs):
        self.ctx = ctx
        self.subparsers = {}
        self._global_parser = self.create_global_parser()
        self.parents = [self._global_parser]
        super(CLICommandParser, self).__init__(**kwargs)

    def load_command_table(self, cmd_tbl):
        # If we haven't already added a subparser, we
        # better do it.
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command')
            sp.required = True
            self.subparsers = {(): sp}
        for cmd_name, metadata in cmd_tbl.items():  # pylint: disable=unused-variable
            # TODO P1 load the command table correctly.
            pass
