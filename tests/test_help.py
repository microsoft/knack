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
from knack.events import EVENT_PARSER_GLOBAL_CREATE

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
        self.cliname = self.mock_ctx.name

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

    @redirect_io
    def test_help_plain_long_description(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
            self.assertTrue(io.getvalue().startswith('\nCommand\n    {} n1\n        Long description.'.format(self.cliname)))

    @redirect_io
    def test_help_long_description_and_short_description(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler, description='short description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
            self.assertTrue(io.getvalue().startswith('\nCommand\n    {} n1: Short description.\n        Long description.'.format(self.cliname)))  # pylint: disable=line-too-long

    @redirect_io
    def test_help_description_from_docstring(self):
        def test_handler():
            """ Short summary here. Long summary here. Still long summary. """
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        cmd_table = {'n1': command}
        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
            actual = io.getvalue()
            expected = '\nCommand\n    {} n1: Short summary here.\n        Long summary here. Still long summary.'.format(self.cliname)
            msg = 'ACT: {}\nEXP: {}'.format(actual, expected)
            self.fail(msg)

    @redirect_io
    def test_help_docstring_description_overrides_short_description(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler, description='short description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'short-summary: docstring summary'
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
            self.assertTrue('n1: Docstring summary.' in io.getvalue())

    @redirect_io
    def test_help_long_description_multi_line(self):
        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
            """
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())

            self.assertTrue(io.getvalue().startswith('\nCommand\n    {} n1\n        Line1\n        line2.'.format(self.cliname)))  # pylint: disable=line-too-long

    @redirect_io
    @mock.patch('knack.cli.CLI.register_event')
    def test_help_params_documentations(self, _):
        def test_handler():
            pass

        self.mock_ctx = MockContext()
        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.add_argument('foobar3', '--foobar3', '-fb3', required=False, help='the foobar3')
        command.help = """
            parameters:
                - name: --foobar -fb
                  type: string
                  required: false
                  short-summary: one line partial sentence
                  long-summary: text, markdown, etc.
                  populator-commands:
                    - mycli abc xyz
                    - default
                - name: --foobar2 -fb2
                  type: string
                  required: true
                  short-summary: one line partial sentence
                  long-summary: paragraph(s)
            """
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
        s = """
Command
    {} n1

Arguments
    --foobar2 -fb2 [Required]: One line partial sentence.
        Paragraph(s).
    --foobar -fb             : One line partial sentence.  Values from: mycli abc xyz, default.
        Text, markdown, etc.
    --foobar3 -fb3           : The foobar3.

Global Arguments
    --help -h                : Show this help message and exit.
"""
        self.assertEqual(s.format(self.cliname), io.getvalue())

    @redirect_io
    @mock.patch('knack.cli.CLI.register_event')
    def test_help_full_documentations(self, _):
        def test_handler():
            pass

        self.mock_ctx = MockContext()
        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.help = """
                short-summary: this module does xyz one-line or so
                long-summary: |
                    this module.... kjsdflkj... klsfkj paragraph1
                    this module.... kjsdflkj... klsfkj paragraph2
                parameters:
                    - name: --foobar -fb
                      type: string
                      required: false
                      short-summary: one line partial sentence
                      long-summary: text, markdown, etc.
                      populator-commands:
                        - mycli abc xyz
                        - default
                    - name: --foobar2 -fb2
                      type: string
                      required: true
                      short-summary: one line partial sentence
                      long-summary: paragraph(s)
                examples:
                    - name: foo example
                      text: example details
            """
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())
        s = """
Command
    {} n1: This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Arguments
    --foobar2 -fb2 [Required]: One line partial sentence.
        Paragraph(s).
    --foobar -fb             : One line partial sentence.  Values from: mycli abc xyz, default.
        Text, markdown, etc.

Global Arguments
    --help -h                : Show this help message and exit.

Examples
    foo example
        example details

"""
        self.assertEqual(s.format(self.cliname), io.getvalue())

    @redirect_io
    @mock.patch('knack.cli.CLI.register_event')
    def test_help_with_param_specified(self, _):
        def test_handler():
            pass

        self.mock_ctx = MockContext()
        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 --arg foo -h'.split())

        s = """
Command
    {} n1

Arguments
    --arg -a
    -b

Global Arguments
    --help -h: Show this help message and exit.
"""

        self.assertEqual(s.format(self.cliname), io.getvalue())

    @redirect_io
    def test_help_group_children(self):
        def test_handler():
            pass

        def test_handler2():
            pass

        command = CLICommand(self.mock_ctx, 'group1 group3 n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)

        command2 = CLICommand(self.mock_ctx, 'group1 group2 n1', test_handler2)
        command2.add_argument('foobar', '--foobar', '-fb', required=False)
        command2.add_argument('foobar2', '--foobar2', '-fb2', required=True)

        cmd_table = {'group1 group3 n1': command, 'group1 group2 n1': command2}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('group1 -h'.split())
            s = '\nGroup\n    {} group1\n\nSubgroups:\n    group2\n    group3\n\n'.format(self.cliname)
            self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_extra_missing_params(self):
        def test_handler(foobar2, foobar=None):  # pylint: disable=unused-argument
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            # work around an argparse behavior where output is not printed and SystemExit
            # is not raised on Python 2.7.9
            if sys.version_info < (2, 7, 10):
                try:
                    self.mock_ctx.invoke('n1 -fb a --foobar value'.split())
                except SystemExit:
                    pass

                try:
                    self.mock_ctx.invoke('n1 -fb a --foobar2 value --foobar3 extra'.split())
                except SystemExit:
                    pass
            else:
                with self.assertRaises(SystemExit):
                    self.mock_ctx.invoke('n1 -fb a --foobar value'.split())
                with self.assertRaises(SystemExit):
                    self.mock_ctx.invoke('n1 -fb a --foobar2 value --foobar3 extra'.split())

                self.assertTrue('required' in io.getvalue() and
                                '--foobar/-fb' not in io.getvalue() and
                                '--foobar2/-fb2' in io.getvalue() and
                                'unrecognized arguments: --foobar3 extra' in io.getvalue())

    @redirect_io
    def test_help_group_help(self):
        def test_handler():
            pass
        from knack.help_files import helps
        helps['test_group1 test_group2'] = """
            type: group
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            examples:
                - name: foo example
                  text: example details
            """

        command = CLICommand(self.mock_ctx, 'test_group1 test_group2 n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.help = """
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            parameters:
                - name: --foobar -fb
                  type: string
                  required: false
                  short-summary: one line partial sentence
                  long-summary: text, markdown, etc.
                  populator-commands:
                    - mycli abc xyz
                    - default
                - name: --foobar2 -fb2
                  type: string
                  required: true
                  short-summary: one line partial sentence
                  long-summary: paragraph(s)
            examples:
                - name: foo example
                  text: example details
        """
        cmd_table = {'test_group1 test_group2 n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('test_group1 test_group2 --help'.split())
        s = """
Group
    {} test_group1 test_group2: This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Commands:
    n1: This module does xyz one-line or so.


Examples
    foo example
        example details

"""
        self.assertEqual(s.format(self.cliname), io.getvalue())
        del helps['test_group1 test_group2']

    @redirect_io
    @mock.patch('knack.cli.CLI.register_event')
    def test_help_global_params(self, _):

        def register_globals(_, **kwargs):
            arg_group = kwargs.get('arg_group')
            arg_group.add_argument('--exampl',
                                   help='This is a new global argument.')

        self.mock_ctx = MockContext()
        self.mock_ctx._event_handlers[EVENT_PARSER_GLOBAL_CREATE].append(register_globals)  # pylint: disable=protected-access

        def test_handler():
            pass

        command = CLICommand(self.mock_ctx, 'n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
        """
        cmd_table = {'n1': command}

        with mock.patch.object(CLICommandsLoader, 'load_command_table', return_value=cmd_table):
            with self.assertRaises(SystemExit):
                self.mock_ctx.invoke('n1 -h'.split())

        s = """
Command
    {} n1
        Line1
        line2.

Arguments
    --arg -a
    -b

Global Arguments
    --exampl : This is a new global argument.
    --help -h: Show this help message and exit.
"""
        self.assertEqual(s.format(self.cliname), io.getvalue())


if __name__ == '__main__':
    unittest.main()
