# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import types
import copy
from collections import OrderedDict, defaultdict
from importlib import import_module

import six

from .prompting import prompt_y_n, NoTTYException
from .util import CLIError, CtxTypeError
from .arguments import ArgumentRegistry, CLICommandArgument
from .introspection import extract_args_from_signature, extract_full_summary_from_signature
from .events import (EVENT_CMDLOADER_LOAD_COMMAND_TABLE, EVENT_CMDLOADER_LOAD_ARGUMENTS,
                     EVENT_COMMAND_CANCELLED)
from .log import get_logger

logger = get_logger(__name__)


class CLICommand(object):  # pylint:disable=too-many-instance-attributes

    # pylint: disable=unused-argument
    def __init__(self, cli_ctx, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None, deprecate_info=None, validator=None, confirmation=None, **kwargs):
        """ The command object that goes into the command table.

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param name: The name of the command (e.g. 'mygroup mycommand')
        :type name: str
        :param handler: The function that will handle this command
        :type handler: function
        :param description: The description for the command
        :type description: str
        :param table_transformer: A function that transforms the command output for displaying in a table
        :type table_transformer: function
        :param arguments_loader: The function that defines how the arguments for the command should be loaded
        :type arguments_loader: function
        :param description_loader: The function that defines how the description for the command should be loaded
        :type description_loader: function
        :param formatter_class: The formatter for how help should be displayed
        :type formatter_class: class
        :param deprecate_info: Deprecation message to display when this command is invoked
        :type deprecate_info: str
        :param validator: The command validator
        :param confirmation: User confirmation required for command
        :type confirmation: bool, str, callable
        :param kwargs: Extra kwargs that are currently ignored
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader if description_loader and self.should_load_description() else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer
        self.formatter_class = formatter_class
        self.deprecate_info = deprecate_info
        self.confirmation = confirmation
        self.validator = validator

    def should_load_description(self):
        return not self.cli_ctx.data['completer_active']

    def load_arguments(self):
        if self.arguments_loader:
            cmd_args = self.arguments_loader()
            if self.confirmation:
                cmd_args.append(('yes',
                                 CLICommandArgument(dest='yes', options_list=['--yes', '-y'],
                                                    action='store_true', help='Do not prompt for confirmation.')))
            self.arguments.update(cmd_args)

    def add_argument(self, param_name, *option_strings, **kwargs):
        dest = kwargs.pop('dest', None)
        argument = CLICommandArgument(dest or param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        arg.type.update(other=argtype)

    def execute(self, **kwargs):
        return self(**kwargs)

    def __call__(self, *args, **kwargs):
        cmd_args = args[0]
        if self.deprecate_info is not None:
            text = 'This command is deprecating and will be removed in future releases.'
            if self.deprecate_info:
                text += " Use '{}' instead.".format(self.deprecate_info)
            logger.warning(text)

        confirm = self.confirmation and not cmd_args.pop('yes', None) \
            and not self.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)

        if confirm and not CLICommandsLoader.user_confirmed(self.confirmation, cmd_args):
            self.cli_ctx.raise_event(EVENT_COMMAND_CANCELLED, command=self.name, command_args=cmd_args)
            raise CLIError('Operation cancelled.')
        return self.handler(*args, **kwargs)


class CLICommandsLoader(object):

    def __init__(self, cli_ctx=None, command_cls=CLICommand, excluded_command_handler_args=None):
        """ The loader of commands. It contains the command table and argument registries.

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param command_cls: The command type that the command table will be populated with
        :type command_cls: knack.commands.CLICommand
        :param excluded_command_handler_args: List of params to ignore and not extract from a commands handler.
                                              By default we ignore ['self', 'kwargs'].
        :type excluded_command_handler_args: list of str
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.command_cls = command_cls
        self.excluded_command_handler_args = excluded_command_handler_args
        # A command table is a dictionary of name -> CLICommand instances
        self.command_table = dict()
        # An argument registry stores all arguments for commands
        self.argument_registry = ArgumentRegistry()
        self.extra_argument_registry = defaultdict(lambda: {})

    def load_command_table(self, args):  # pylint: disable=unused-argument
        """ Load commands into the command table

        :param args: List of the arguments from the command line
        :type args: list
        :return: The ordered command table
        :rtype: collections.OrderedDict
        """
        self.cli_ctx.raise_event(EVENT_CMDLOADER_LOAD_COMMAND_TABLE, cmd_tbl=self.command_table)
        return OrderedDict(self.command_table)

    def load_arguments(self, command):
        """ Load the arguments for the specified command

        :param command: The command to load arguments for
        :type command: str
        """
        self.cli_ctx.raise_event(EVENT_CMDLOADER_LOAD_ARGUMENTS, cmd_tbl=self.command_table, command=command)
        try:
            self.command_table[command].load_arguments()
        except KeyError:
            return
        self._apply_parameter_info(command, self.command_table[command])

    def _apply_parameter_info(self, command_name, command):
        for argument_name in command.arguments:
            overrides = self.argument_registry.get_cli_argument(command_name, argument_name)
            command.update_argument(argument_name, overrides)
        # Add any arguments explicitly registered for this command
        for argument_name, argument_definition in self.extra_argument_registry[command_name].items():
            command.arguments[argument_name] = argument_definition
            command.update_argument(argument_name, self.argument_registry.get_cli_argument(command_name, argument_name))

    def create_command(self, module_name, name, operation, **kwargs):  # pylint: disable=unused-argument
        """ Constructs the command object that can then be added to the command table """
        if not isinstance(operation, six.string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        name = ' '.join(name.split())

        client_factory = kwargs.get('client_factory', None)

        def _command_handler(command_args):
            op = CLICommandsLoader.get_op_handler(operation)
            client = client_factory(command_args) if client_factory else None
            result = op(client, **command_args) if client else op(**command_args)
            return result

        def arguments_loader():
            return list(extract_args_from_signature(CLICommandsLoader.get_op_handler(operation),
                                                    excluded_params=self.excluded_command_handler_args))

        def description_loader():
            return extract_full_summary_from_signature(CLICommandsLoader.get_op_handler(operation))

        kwargs['arguments_loader'] = arguments_loader
        kwargs['description_loader'] = description_loader

        cmd = self.command_cls(self.cli_ctx, name, _command_handler, **kwargs)
        return cmd

    @staticmethod
    def get_op_handler(operation):
        """ Import and load the operation handler """
        try:
            mod_to_import, attr_path = operation.split('#')
            op = import_module(mod_to_import)
            for part in attr_path.split('.'):
                op = getattr(op, part)
            if isinstance(op, types.FunctionType):
                return op
            return six.get_method_function(op)
        except (ValueError, AttributeError):
            raise ValueError("The operation '{}' is invalid.".format(operation))

    @staticmethod
    def user_confirmed(confirmation, command_args):
        if callable(confirmation):
            return confirmation(command_args)
        try:
            if isinstance(confirmation, six.string_types):
                return prompt_y_n(confirmation)
            return prompt_y_n('Are you sure you want to perform this operation?')
        except NoTTYException:
            logger.warning('Unable to prompt for confirmation as no tty available. Use --yes.')
            return False


class CommandSuperGroup(object):
    def __init__(self, module_name, command_loader, operations_tmpl, **kwargs):
        """ Context manager for registering commands that share common properties.

        Example:
            with CommandSuperGroup(__name__, self, '__main__#{}') as sg:
                with sg.group('hello') as g:
                    g.command('world', 'hello_command_handler', confirmation=True)

        :param module_name: The module this command comes from (e.g. '__name__')
        :type module_name: str
        :param command_loader: The command loader that commands will be registered into
        :type command_loader: knack.commands.CLICommandsLoader
        :param operations_tmpl: The template for handlers for this group of commands (e.g. '__main__#{}')
        :type operations_tmpl: str
        :param kwargs: Kwargs to apply to all commands in this super group.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`.
        """
        self.module_name = module_name
        self.command_loader = command_loader
        self.operations_tmpl = operations_tmpl
        self.super_group_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def group(self, group_name, **kwargs):
        """ Creates a new group of commands that inherits from the super group.

        :param group_name: The name of this group of commands in the command hierarchy
        :type group_name: str
        :param kwargs: Kwargs to apply to all commands in this group.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`.
        :return: The created command group
        :rtype: knack.commands.CommandGroup
        """
        group_args = copy.deepcopy(self.super_group_kwargs)
        group_args.update(kwargs)
        return CommandGroup(self.module_name, self.command_loader, group_name, self.operations_tmpl, **group_args)


class CommandGroup(object):
    def __init__(self, module_name, command_loader, group_name, operations_tmpl, **kwargs):
        """ Context manager for registering commands that share common properties.

        :param module_name: The module this command comes from (e.g. '__name__')
        :type module_name: str
        :param command_loader: The command loader that commands will be registered into
        :type command_loader: knack.commands.CLICommandsLoader
        :param group_name: The name of the group of commands in the command hierarchy
        :type group_name: str
        :param operations_tmpl: The template for handlers for this group of commands (e.g. '__main__#{}')
        :type operations_tmpl: str
        :param kwargs: Kwargs to apply to all commands in this group.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`.
        """
        self.module_name = module_name
        self.command_loader = command_loader
        self.group_name = group_name
        self.operations_tmpl = operations_tmpl
        self.group_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def command(self, name, handler_name, **kwargs):
        """ Register a command into the command table

        :param name: The name of the command
        :type name: str
        :param handler_name: The name of the handler that will be applied to the operations template
        :type handler_name: str
        :param kwargs: Kwargs to apply to the command.
                       Possible values: `client_factory`, `arguments_loader`, `description_loader`, `description`,
                       `formatter_class`, `table_transformer`, `deprecate_info`, `validator`, `confirmation`.
        """
        command_name = '{} {}'.format(self.group_name, name) if self.group_name else name
        command_kwargs = copy.deepcopy(self.group_kwargs)
        command_kwargs.update(kwargs)
        self.command_loader.command_table[command_name] = self.command_loader.create_command(
            self.module_name,
            command_name,
            self.operations_tmpl.format(handler_name),
            **command_kwargs)
