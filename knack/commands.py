# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import types
import copy
from collections import OrderedDict
from importlib import import_module

import six

from .prompting import prompt_y_n, NoTTYException
from .util import CLIError
from .arguments import ArgumentRegistry, CLICommandArgument
from .introspection import extract_args_from_signature, extract_full_summary_from_signature
from .events import (EVENT_CMDLOADER_LOAD_COMMAND_TABLE, EVENT_CMDLOADER_LOAD_ARGUMENTS,
                     EVENT_COMMAND_CANCELLED)
from .log import get_logger

logger = get_logger(__name__)


class CLICommand(object):  # pylint:disable=too-many-instance-attributes

    # pylint: disable=unused-argument
    def __init__(self, ctx, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None, deprecate_info=None, **kwargs):
        self.ctx = ctx
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader if description_loader and self.should_load_description() else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer
        self.formatter_class = formatter_class
        self.deprecate_info = deprecate_info

    def should_load_description(self):
        return not self.ctx.data['completer_active']

    def load_arguments(self):
        if self.arguments_loader:
            self.arguments.update(self.arguments_loader())

    def add_argument(self, param_name, *option_strings, **kwargs):
        dest = kwargs.pop('dest', None)
        argument = CLICommandArgument(dest or param_name, options_list=option_strings, **kwargs)
        self.arguments[param_name] = argument

    def update_argument(self, param_name, argtype):
        arg = self.arguments[param_name]
        # self._resolve_default_value_from_cfg_file(arg, argtype)
        arg.type.update(other=argtype)

    def execute(self, **kwargs):
        return self(**kwargs)

    def __call__(self, *args, **kwargs):
        if self.deprecate_info is not None:
            text = 'This command is deprecating and will be removed in future releases.'
            if self.deprecate_info:
                text += " Use '{}' instead.".format(self.deprecate_info)
            logger.warning(text)
        return self.handler(*args, **kwargs)


class CLICommandsLoader(object):

    def __init__(self, ctx=None):
        self.ctx = ctx
        # A command table is a dictionary of name -> CLICommand instances
        self.command_table = dict()
        # An arguments registry stores all arguments for commands
        self.arguments_registry = ArgumentRegistry()

    def load_command_table(self, args):  # pylint: disable=unused-argument
        self.ctx.raise_event(EVENT_CMDLOADER_LOAD_COMMAND_TABLE, cmd_tbl=self.command_table)
        return OrderedDict(self.command_table)

    def load_arguments(self, command):
        self.ctx.raise_event(EVENT_CMDLOADER_LOAD_ARGUMENTS, cmd_tbl=self.command_table, command=command)
        try:
            self.command_table[command].load_arguments()
        except KeyError:
            return
        self._apply_parameter_info(command, self.command_table[command])

    def _apply_parameter_info(self, command_name, command):
        for argument_name in command.arguments:
            overrides = self.arguments_registry.get_cli_argument(command_name, argument_name)
            command.update_argument(argument_name, overrides)
        # Add any arguments explicitly registered for this command
        # for argument_name, argument_definition in _get_cli_extra_arguments(command_name):
        #     command.arguments[argument_name] = argument_definition
        #     command.update_argument(argument_name, _get_cli_argument(command_name, argument_name))

    def cli_command(self, module_name, name, operation, **kwargs):
        """ Add a command to the command table. """
        self.command_table[name] = self.create_command(module_name, name, operation, **kwargs)

    def create_command(self, module_name, name, operation, **kwargs):  # pylint: disable=unused-argument
        if not isinstance(operation, six.string_types):
            raise ValueError("Operation must be a string. Got '{}'".format(operation))

        name = ' '.join(name.split())

        confirmation = kwargs.get('confirmation', False)
        client_factory = kwargs.get('client_factory', None)

        def _command_handler(command_args):
            if confirmation \
                and not command_args.get('_confirm_yes') \
                and not self.ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False) \
                    and not CLICommandsLoader.user_confirmed(confirmation, command_args):
                self.ctx.raise_event(EVENT_COMMAND_CANCELLED, command=name, command_args=command_args)
                raise CLIError('Operation cancelled.')
            op = CLICommandsLoader.get_op_handler(operation)
            client = client_factory(command_args) if client_factory else None
            result = op(client, **command_args) if client else op(**command_args)
            return result

        def arguments_loader():
            return extract_args_from_signature(CLICommandsLoader.get_op_handler(operation))

        def description_loader():
            return extract_full_summary_from_signature(CLICommandsLoader.get_op_handler(operation))

        kwargs['arguments_loader'] = arguments_loader
        kwargs['description_loader'] = description_loader

        cmd = CLICommand(self.ctx, name, _command_handler, **kwargs)
        if confirmation:
            cmd.add_argument('yes', '--yes', '-y', dest='_confirm_yes',
                             action='store_true',
                             help='Do not prompt for confirmation')
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

    def register_cli_argument(self, scope, dest, arg_type=None, **kwargs):
        ''' Specify CLI specific metadata for a given argument for a given scope. '''
        self.arguments_registry.register_cli_argument(scope, dest, arg_type, **kwargs)


class CommandSuperGroup(object):
    def __init__(self, module_name, command_loader, operations_tmpl, **kwargs):
        self.module_name = module_name
        self.command_loader = command_loader
        self.operations_tmpl = operations_tmpl
        self.super_group_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def group(self, group_name, **kwargs):
        group_args = copy.deepcopy(self.super_group_kwargs)
        group_args.update(kwargs)
        return CommandGroup(self.module_name, self.command_loader, group_name, self.operations_tmpl, **group_args)


class CommandGroup(object):
    def __init__(self, module_name, command_loader, group_name, operations_tmpl, **kwargs):
        self.module_name = module_name
        self.command_loader = command_loader
        self.group_name = group_name
        self.operations_tmpl = operations_tmpl
        self.group_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def command(self, name, method_name, **kwargs):
        command_name = '{} {}'.format(self.group_name, name)
        command_kwargs = copy.deepcopy(self.group_kwargs)
        command_kwargs.update(kwargs)
        self.command_loader.cli_command(self.module_name,
                                        command_name,
                                        self.operations_tmpl.format(method_name),
                                        **command_kwargs)
