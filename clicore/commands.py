# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from .log import get_logger

logger = get_logger(__name__)


# TODO DELETE THIS
def a_test_command_handler(_):
    return [{'a': 1, 'b': 1234}, {'a': 3, 'b': 4}]


class CliCommand(object):  # pylint:disable=too-many-instance-attributes

    def __init__(self, name, handler, description=None, table_transformer=None,
                 arguments_loader=None, description_loader=None,
                 formatter_class=None, deprecate_info=None):
        self.name = name
        self.handler = handler
        self.help = None
        self.description = description_loader if description_loader and self.should_load_description() else description
        self.arguments = {}
        self.arguments_loader = arguments_loader
        self.table_transformer = table_transformer
        self.formatter_class = formatter_class
        self.deprecate_info = deprecate_info

    def should_load_description(self):  # pylint: disable=no-self-use
        # TODO self.ctx should be passed in somehow...
        # return not self.ctx.cli_data['completer_active']
        return True

    def load_arguments(self):
        if self.arguments_loader:
            self.arguments.update(self.arguments_loader())

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
        # A command table is a dictionary of name -> CliCommand instances
        self.command_table = dict()

    def generate_command_table(self, args):  # pylint: disable=unused-argument
        # TODO Generate the command table appropriately
        cmd_name = 'abc xyz'
        self.command_table[cmd_name] = CliCommand(cmd_name, a_test_command_handler)
        return OrderedDict(self.command_table)
