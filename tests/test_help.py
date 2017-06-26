# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
import mock
from six import StringIO


from knack.help import ArgumentGroupRegistry, HelpObject
from knack.commands import CLICommand, CLICommandsLoader
from tests.util import MockContext

io = {}


def redirect_io(func):
    def wrapper(self):
        global io
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sys.stderr = io = StringIO()
        func(self)
        io.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    return wrapper


class TestHelpArgumentGroupRegistry(unittest.TestCase):
    def test_help_argument_group_registry(self):
        groups = [
            'Z Arguments',
            'B Arguments',
            'Global Arguments',
            'A Arguments',
        ]
        group_registry = ArgumentGroupRegistry(groups)
        self.assertEqual(group_registry.get_group_priority('A Arguments'), '000002')
        self.assertEqual(group_registry.get_group_priority('B Arguments'), '000003')
        self.assertEqual(group_registry.get_group_priority('Z Arguments'), '000004')
        self.assertEqual(group_registry.get_group_priority('Global Arguments'), '001000')


class TestHelpObject(unittest.TestCase):
    def test_short_summary_no_fullstop(self):
        obj = HelpObject()
        original_summary = 'This summary has no fullstop'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary + '.')

    def test_short_summary_fullstop(self):
        obj = HelpObject()
        original_summary = 'This summary has fullstop.'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary)

    def test_short_summary_exclamation_point(self):
        obj = HelpObject()
        original_summary = 'This summary has exclamation point!'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary)


class TestHelp(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()

    @redirect_io
    def test_choice_list_with_ints(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False, choices=[1, 2, 3])
        command.add_argument('b', '-b', required=False, choices=['a', 'b', 'c'])
        cmd_table = {'n1': command}
        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())

    @redirect_io
    def test_help_param(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())

            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 --help'.split())


    @redirect_io
    def test_help_plain_short_description(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler, description='the description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
            self.assertTrue('n1: The description.' in io.getvalue())

if __name__ == '__main__':
    unittest.main()
