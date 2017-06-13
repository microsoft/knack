# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from collections import defaultdict

from .log import get_logger

logger = get_logger(__name__)


class CLIArgumentType(object):
    REMOVE = '---REMOVE---'

    def __init__(self, overrides=None, **kwargs):
        if isinstance(overrides, str):
            raise ValueError("Overrides has to be a {} (cannot be a string)".format(CLIArgumentType.__name__))
        options_list = kwargs.get('options_list', None)
        if options_list and isinstance(options_list, str):
            kwargs['options_list'] = [options_list]
        self.settings = {}
        self.update(overrides, **kwargs)

    def update(self, other=None, **kwargs):
        if other:
            self.settings.update(**other.settings)
        self.settings.update(**kwargs)


class CLICommandArgument(object):  # pylint: disable=too-few-public-methods
    _NAMED_ARGUMENTS = ('options_list', 'validator', 'completer', 'arg_group')

    def __init__(self, dest=None, argtype=None, **kwargs):
        self.type = CLIArgumentType(overrides=argtype, **kwargs)
        if dest:
            self.type.update(dest=dest)

        # We'll do an early fault detection to find any instances where we have inconsistent
        # set of parameters for argparse
        if not self.options_list and 'required' in self.options:  # pylint: disable=access-member-before-definition
            raise ValueError(message="You can't specify both required and an options_list")
        if not self.options.get('dest', False):
            raise ValueError('Missing dest')
        if not self.options_list:  # pylint: disable=access-member-before-definition
            self.options_list = ('--{}'.format(self.options['dest'].replace('_', '-')),)

    def __getattr__(self, name):
        if name in self._NAMED_ARGUMENTS:
            return self.type.settings.get(name, None)
        elif name == 'name':
            return self.type.settings.get('dest', None)
        elif name == 'options':
            return {key: value for key, value in self.type.settings.items()
                    if key != 'options' and key not in self._NAMED_ARGUMENTS and
                    not value == CLIArgumentType.REMOVE}
        elif name == 'choices':
            return self.type.settings.get(name, None)
        else:
            raise AttributeError(message=name)

    def __setattr__(self, name, value):
        if name == 'type':
            return super(CLICommandArgument, self).__setattr__(name, value)
        self.type.settings[name] = value


class ArgumentRegistry(object):
    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, **kwargs):
        argument = CLIArgumentType(overrides=argtype,
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        parts = command.split()
        result = CLIArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override)
        return result


class ArgumentsContext(object):
    def __init__(self, command_loader, command):
        self.command_loader = command_loader
        self.commmand = command

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def ignore(self, argument_name):
        self.command_loader.register_cli_argument(self.commmand, argument_name, ignore_type)

    def argument(self, argument_name, arg_type=None, **kwargs):
        self.command_loader.register_cli_argument(self.commmand, argument_name, arg_type=arg_type, **kwargs)

    def register_alias(self, argument_name, options_list, **kwargs):
        self.command_loader.register_cli_argument(self.commmand, argument_name, options_list=options_list, **kwargs)

    def register(self, argument_name, options_list, **kwargs):
        self.command_loader.register_cli_argument(self.commmand, argument_name, options_list=options_list, **kwargs)


class IgnoreAction(argparse.Action):  # pylint: disable=too-few-public-methods

    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(None, 'unrecognized argument: {} {}'.format(
            option_string, values or ''))


# GLOBAL ARGUMENT DEFINITIONS

ignore_type = CLIArgumentType(
    help=argparse.SUPPRESS,
    nargs='?',
    action=IgnoreAction,
    required=False)
