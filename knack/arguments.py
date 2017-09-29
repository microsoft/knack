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
        """A base CLI Argument Type that can be applied to multiple command arguments

        :param overrides: The base argument that you are overriding
        :type overrides: knack.arguments.CLIArgumentType
        :param kwargs: Possible values: `options_list`, `validator`, `completer`, `nargs`, `action`, `const`, `default`,
                       `type`, `choices`, `required`, `help`, `metavar`. See /docs/arguments.md.
        """
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

    NAMED_ARGUMENTS = ['options_list', 'validator', 'completer', 'arg_group']

    def __init__(self, dest=None, argtype=None, **kwargs):
        """An argument that has a specific destination parameter.

        :param dest: The parameter that this argument is for
        :type dest: str
        :param argtype: The argument type for this command argument
        :type argtype: knack.arguments.CLIArgumentType
        :param kwargs: see knack.arguments.CLIArgumentType
        """
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
        if name in self.NAMED_ARGUMENTS:
            return self.type.settings.get(name, None)
        elif name == 'name':
            return self.type.settings.get('dest', None)
        elif name == 'options':
            return {key: value for key, value in self.type.settings.items()
                    if key != 'options' and key not in self.NAMED_ARGUMENTS and
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
    """A registry of all the arguments registered"""

    def __init__(self):
        self.arguments = defaultdict(lambda: {})

    def register_cli_argument(self, scope, dest, argtype, **kwargs):
        """ Add an argument to the argument registry

        :param scope: The command level to apply the argument registration (e.g. 'mygroup mycommand')
        :type scope: str
        :param dest: The parameter/destination that this argument is for
        :type dest: str
        :param argtype: The argument type for this command argument
        :type argtype: knack.arguments.CLIArgumentType
        :param kwargs: see knack.arguments.CLIArgumentType
        """
        argument = CLIArgumentType(overrides=argtype,
                                   **kwargs)
        self.arguments[scope][dest] = argument

    def get_cli_argument(self, command, name):
        """ Get the argument for the command after applying the scope hierarchy

        :param command: The command that we want the argument for
        :type command: str
        :param name: The name of the argument
        :type name: str
        :return: The CLI command after all overrides in the scope hierarchy have been applied
        :rtype: knack.arguments.CLIArgumentType
        """
        parts = command.split()
        result = CLIArgumentType()
        for index in range(0, len(parts) + 1):
            probe = ' '.join(parts[0:index])
            override = self.arguments.get(probe, {}).get(name, None)
            if override:
                result.update(override)
        return result


class ArgumentsContext(object):
    def __init__(self, command_loader, command_scope):
        """ Context manager to register arguments

        :param command_loader: The command loader that arguments should be registered into
        :type command_loader: knack.commands.CLICommandsLoader
        :param command_scope: The scope to which arguments in this context apply.
                              More specific scopes will override less specific scopes in the event of a conflict.
        :type command_scope: str
        """
        self.command_loader = command_loader
        self.command_scope = command_scope

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def argument(self, argument_dest, arg_type=None, **kwargs):
        """ Register an argument for the given command scope using a knack.arguments.CLIArgumentType

        :param argument_dest: The destination argument to add this argument type to
        :type argument_dest: str
        :param arg_type: Predefined CLIArgumentType definition to register, as modified by any provided kwargs.
        :type arg_type: knack.arguments.CLIArgumentType
        :param kwargs: Possible values: `options_list`, `validator`, `completer`, `nargs`, `action`, `const`, `default`,
                       `type`, `choices`, `required`, `help`, `metavar`. See /docs/arguments.md.
        """
        self.command_loader.argument_registry.register_cli_argument(self.command_scope,
                                                                    argument_dest,
                                                                    arg_type,
                                                                    **kwargs)

    def ignore(self, argument_dest):
        """ Register an argument with type knack.arguments.ignore_type (hidden/ignored)

        :param argument_dest: The destination argument to apply the ignore type to
        :type argument_dest: str
        """
        self.argument(argument_dest, arg_type=ignore_type)

    def extra(self, argument_dest, **kwargs):
        """Register extra parameters for the given command. Typically used to augment auto-command built
        commands to add more parameters than the specific SDK method introspected.

        :param argument_dest: The destination argument to add this argument type to
        :type argument_dest: str
        :param kwargs: Possible values: `options_list`, `validator`, `completer`, `nargs`, `action`, `const`, `default`,
                       `type`, `choices`, `required`, `help`, `metavar`. See /docs/arguments.md.
        """
        self.command_loader.extra_argument_registry[self.command_scope][argument_dest] = CLICommandArgument(
            argument_dest, **kwargs)


class IgnoreAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """ Show the argument as unrecognized if it is called """

    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(None, 'unrecognized argument: {} {}'.format(
            option_string, values or ''))


class CaseInsensitiveList(list):
    """ Determine if a choice is in a choice list in a case-insensitive manner """

    def __contains__(self, other):
        return next((True for x in self if other.lower() == x.lower()), False)


def enum_choice_list(data):
    """ Creates the argparse choices and type kwargs for a supplied enum type or list of strings """

    # transform enum types, otherwise assume list of string choices
    if not data:
        return {}
    try:
        choices = [x.value for x in data]
    except AttributeError:
        choices = data

    def _type(value):
        return next((x for x in choices if x.lower() == value.lower()), value) if value else value
    params = {
        'choices': CaseInsensitiveList(choices),
        'type': _type
    }
    return params

# GLOBAL ARGUMENT DEFINITIONS


ignore_type = CLIArgumentType(
    help=argparse.SUPPRESS,
    nargs='?',
    action=IgnoreAction,
    required=False)
