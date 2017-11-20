# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from .events import EVENT_PARSER_GLOBAL_CREATE
from .util import CtxTypeError


# List of keyword arguments supported in argparse
# from https://github.com/python/cpython/blob/master/Lib/argparse.py#L748
ARGPARSE_SUPPORTED_KWARGS = [
    'option_strings',
    'dest',
    'nargs',
    'const',
    'default',
    'type',
    'choices',
    'required',
    'help',
    'metavar',
    'action'
]


class CLICommandParser(argparse.ArgumentParser):

    @staticmethod
    def create_global_parser(cli_ctx=None):
        global_parser = argparse.ArgumentParser(prog=cli_ctx.name, add_help=False)
        arg_group = global_parser.add_argument_group('global', 'Global Arguments')
        cli_ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=arg_group)
        return global_parser

    @staticmethod
    def _add_argument(obj, arg):
        """ Only pass valid argparse kwargs to argparse.ArgumentParser.add_argument """
        options_list = arg.options_list
        argparse_options = {name: value for name, value in arg.options.items() if name in ARGPARSE_SUPPORTED_KWARGS}
        return obj.add_argument(*options_list, **argparse_options)

    def __init__(self, cli_ctx=None, cli_help=None, **kwargs):
        """ Create the argument parser

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param kwargs: These kwargs are typically used by argparse when creating the subparsers
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.cli_help = cli_help
        self.subparsers = {}
        self.parents = kwargs.get('parents', [])
        self.help_file = kwargs.pop('help_file', None)
        # We allow a callable for description to be passed in in order to delay-load any help
        # or description for a command. We better stash it away before handing it off for
        # "normal" argparse handling...
        self._description = kwargs.pop('description', None)
        super(CLICommandParser, self).__init__(**kwargs)

    def load_command_table(self, cmd_tbl):
        """ Process the command table and load it into the parser

        :param cmd_tbl: A dictionary containing the commands
        :type cmd_tbl: dict
        """
        if not cmd_tbl:
            raise ValueError('The command table is empty. At least one command is required.')
        # If we haven't already added a subparser, we
        # better do it.
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command')
            sp.required = True
            self.subparsers = {(): sp}
        for command_name, metadata in cmd_tbl.items():
            subparser = self._get_subparser(command_name.split())
            command_verb = command_name.split()[-1]
            # To work around http://bugs.python.org/issue9253, we artificially add any new
            # parsers we add to the "choices" section of the subparser.
            subparser.choices[command_verb] = command_verb
            # inject command_module designer's help formatter -- default is HelpFormatter
            fc = metadata.formatter_class or argparse.HelpFormatter

            command_parser = subparser.add_parser(command_verb,
                                                  description=metadata.description,
                                                  parents=self.parents,
                                                  conflict_handler='error',
                                                  help_file=metadata.help,
                                                  formatter_class=fc,
                                                  cli_help=self.cli_help)

            command_validator = metadata.validator
            argument_validators = []
            argument_groups = {}
            for arg in metadata.arguments.values():
                if arg.validator:
                    argument_validators.append(arg.validator)
                if arg.arg_group:
                    try:
                        group = argument_groups[arg.arg_group]
                    except KeyError:
                        # group not found so create
                        group_name = '{} Arguments'.format(arg.arg_group)
                        group = command_parser.add_argument_group(arg.arg_group, group_name)
                        argument_groups[arg.arg_group] = group
                    param = CLICommandParser._add_argument(group, arg)
                else:
                    param = CLICommandParser._add_argument(command_parser, arg)
                param.completer = arg.completer

            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _command_validator=command_validator,
                _argument_validators=argument_validators,
                _parser=command_parser)

    def _get_subparser(self, path):
        """For each part of the path, walk down the tree of
        subparsers, creating new ones if one doesn't already exist.
        """
        for length in range(0, len(path)):
            parent_subparser = self.subparsers.get(tuple(path[0:length]), None)
            if not parent_subparser:
                # No subparser exists for the given subpath - create and register
                # a new subparser.
                # Since we know that we always have a root subparser (we created)
                # one when we started loading the command table, and we walk the
                # path from left to right (i.e. for "cmd subcmd1 subcmd2", we start
                # with ensuring that a subparser for cmd exists, then for subcmd1,
                # subcmd2 and so on), we know we can always back up one step and
                # add a subparser if one doesn't exist
                grandparent_subparser = self.subparsers[tuple(path[0:length - 1])]
                new_parser = grandparent_subparser.add_parser(path[length - 1], cli_help=self.cli_help)

                # Due to http://bugs.python.org/issue9253, we have to give the subparser
                # a destination and set it to required in order to get a meaningful error
                parent_subparser = new_parser.add_subparsers(dest='_subcommand')
                parent_subparser.required = True
                self.subparsers[tuple(path[0:length])] = parent_subparser
        return parent_subparser

    def validation_error(self, message):
        return super(CLICommandParser, self).error(message)

    def is_group(self):
        """ Determine if this parser instance represents a group
            or a command. Anything that has a func default is considered
            a group. This includes any dummy commands served up by the
            "filter out irrelevant commands based on argv" command filter """
        cmd = self._defaults.get('func', None)
        return not (cmd and cmd.handler)

    def __getattribute__(self, name):
        """ Since getting the description can be expensive (require module loads), we defer
            this until someone actually wants to use it (i.e. show help for the command)
        """
        if name == 'description':
            if self._description:
                self.description = self._description() \
                    if callable(self._description) else self._description
                self._description = None
        return object.__getattribute__(self, name)

    def format_help(self):
        is_group = self.is_group()
        self.cli_help.show_help(self.prog.split()[0],
                                self.prog.split()[1:],
                                self._actions[-1] if is_group else self,
                                is_group)
        self.exit()
