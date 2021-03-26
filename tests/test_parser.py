# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from io import StringIO

from knack.parser import CLICommandParser
from knack.commands import CLICommand
from knack.arguments import enum_choice_list
from tests.util import MockContext, redirect_io


class TestParser(unittest.TestCase):

    def setUp(self):
        self.io = StringIO()
        self.mock_ctx = MockContext()

    def tearDown(self):
        self.io.close()

    def test_register_simple_commands(self):
        def test_handler1():
            pass

        def test_handler2():
            pass

        command = CLICommand(self.mock_ctx, 'command the-name', test_handler1)
        command2 = CLICommand(self.mock_ctx, 'sub-command the-second-name', test_handler2)
        cmd_table = {'command the-name': command, 'sub-command the-second-name': command2}
        self.mock_ctx.commands_loader.command_table = cmd_table

        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)
        args = parser.parse_args('command the-name'.split())
        self.assertIs(args.func, command)

        args = parser.parse_args('sub-command the-second-name'.split())
        self.assertIs(args.func, command2)

        CLICommandParser.error = VerifyError(self,)
        parser.parse_args('sub-command'.split())
        self.assertTrue(CLICommandParser.error.called)

    def test_required_parameter(self):
        def test_handler(args):  # pylint: disable=unused-argument
            pass

        command = CLICommand(self.mock_ctx, 'test command', test_handler)
        command.add_argument('req', '--req', required=True)
        cmd_table = {'test command': command}
        self.mock_ctx.commands_loader.command_table = cmd_table

        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)

        args = parser.parse_args('test command --req yep'.split())
        self.assertIs(args.func, command)

        CLICommandParser.error = VerifyError(self)
        parser.parse_args('test command'.split())
        self.assertTrue(CLICommandParser.error.called)

    def test_nargs_parameter(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'test command', test_handler)
        command.add_argument('req', '--req', required=True, nargs=2)
        cmd_table = {'test command': command}
        self.mock_ctx.commands_loader.command_table = cmd_table

        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)

        args = parser.parse_args('test command --req yep nope'.split())
        self.assertIs(args.func, command)

        CLICommandParser.error = VerifyError(self)
        parser.parse_args('test command -req yep'.split())
        self.assertTrue(CLICommandParser.error.called)

    def _enum_parser(self):
        from enum import Enum

        class TestEnum(Enum):  # pylint: disable=too-few-public-methods

            opt1 = "ALL_CAPS"
            opt2 = "camelCase"
            opt3 = "snake_case"

        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'test command', test_handler)
        command.add_argument('opt', '--opt', required=True, **enum_choice_list(TestEnum))
        cmd_table = {'test command': command}
        self.mock_ctx.commands_loader.command_table = cmd_table

        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)
        return parser

    def test_case_insensitive_enum_choices(self):
        parser = self._enum_parser()
        args = parser.parse_args('test command --opt alL_cAps'.split())
        self.assertEqual(args.opt, 'ALL_CAPS')

        args = parser.parse_args('test command --opt CAMELCASE'.split())
        self.assertEqual(args.opt, 'camelCase')

        args = parser.parse_args('test command --opt sNake_CASE'.split())
        self.assertEqual(args.opt, 'snake_case')

    @redirect_io
    def test_check_value_invalid_command(self):
        parser = self._enum_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args('test command1'.split())  # 'command1' is invalid
        actual = self.io.getvalue()
        assert "is not in the" in actual and "command group" in actual

    @redirect_io
    def test_check_value_invalid_argument_value(self):
        parser = self._enum_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args('test command --opt foo'.split())  # 'foo' is invalid
        actual = self.io.getvalue()
        assert "is not a valid value for" in actual

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            CLICommandParser(cli_ctx=object())

    def test_extra_nonargparse_parameters(self):
        """ Add argument that has non argparse parameters.

            'mycustomarg' should be filtered out and load_command_table
            should complete successfully instead of throwing
            TypeError: __init__() got an unexpected keyword argument 'mycustomarg'
        """
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'test command', test_handler)
        command.add_argument('req', '--req', required=True, mycustomarg=True)
        cmd_table = {'test command': command}
        self.mock_ctx.commands_loader.command_table = cmd_table
        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)

    def test_prefix_file_expansion(self):
        import json, os

        def test_handler():
            pass

        def create_test_file(file, contents):
            with open(file, 'w') as f:
                f.write(contents)

        def remove_test_file(file):
            os.remove(file)

        json_test_data = json.dumps({'one': 1, 'two': 2, 'three': 3})
        create_test_file('test.json', json_test_data)

        command = CLICommand(self.mock_ctx, 'test command', test_handler)
        command.add_argument('json_data', '--param')
        cmd_table = {'test command': command}
        self.mock_ctx.commands_loader.command_table = cmd_table
        parser = CLICommandParser()
        parser.load_command_table(self.mock_ctx.commands_loader)

        args = parser.parse_args('test command --param @test.json'.split())
        self.assertEqual(json_test_data, args.json_data)

        remove_test_file('test.json')


class VerifyError(object):  # pylint: disable=too-few-public-methods

    def __init__(self, test, substr=None):
        self.test = test
        self.substr = substr
        self.called = False

    def __call__(self, message):
        if self.substr:
            self.test.assertGreaterEqual(message.find(self.substr), 0)
        self.called = True


if __name__ == '__main__':
    unittest.main()
