# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals, print_function

import unittest
try:
    import mock
except ImportError:
    from unittest import mock

import sys
import argparse

from knack.arguments import ArgumentsContext
from knack.commands import CLICommandsLoader, CommandGroup

from tests.util import DummyCLI, redirect_io, remove_space


def example_handler(arg1, arg2=None, arg3=None):
    """ Short summary here. Long summary here. Still long summary. """
    pass


def example_arg_handler(arg1, opt1, arg2=None, opt2=None, arg3=None,
                        opt3=None, arg4=None, opt4=None, arg5=None, opt5=None):
    pass


class TestCommandExperimental(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class ExperimentalTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(ExperimentalTestCommandLoader, self).load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('cmd1', 'example_handler', is_experimental=True)

                with CommandGroup(self, 'grp1', '{}#{{}}'.format(__name__), is_experimental=True) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super(ExperimentalTestCommandLoader, self).load_arguments(command)

        helps['grp1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=ExperimentalTestCommandLoader)

    @redirect_io
    def test_experimental_command_implicitly_execute(self):
        """ Ensure general warning displayed when running command from an experimental parent group. """
        self.cli_ctx.invoke('grp1 cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "Command group 'grp1' is experimental and not covered by customer support. " \
                   "Please use with discretion."
        self.assertIn(remove_space(expected), remove_space(actual))

    @redirect_io
    def test_experimental_command_group_help(self):
        """ Ensure experimental commands appear correctly in group help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('-h'.split())
        actual = self.io.getvalue()
        expected = u"""
Group
    {}

Subgroups:
    grp1 [Experimental] : A group.

Commands:
    cmd1 [Experimental] : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    def test_experimental_command_plain_execute(self):
        """ Ensure general warning displayed when running experimental command. """
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "This command is experimental and not covered by customer support. Please use with discretion."
        self.assertIn(remove_space(expected), remove_space(actual))


class TestCommandGroupExperimental(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class ExperimentalTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(ExperimentalTestCommandLoader, self).load_command_table(args)

                with CommandGroup(self, 'group1', '{}#{{}}'.format(__name__), is_experimental=True) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super(ExperimentalTestCommandLoader, self).load_arguments(command)

        helps['group1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=ExperimentalTestCommandLoader)

    @redirect_io
    def test_experimental_command_group_help_plain(self):
        """ Ensure help warnings appear for experimental command group help. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    cli group1 : A group.
        This command group is experimental and not covered by customer support. Please use with discretion.
Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        self.assertIn(remove_space(expected), remove_space(actual))

    @redirect_io
    def test_experimental_command_implicitly(self):
        """ Ensure help warning displayed for command in experimental because of a experimental parent group. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 cmd1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Command
    {} group1 cmd1 : Short summary here.
        Long summary here. Still long summary.
        Command group 'group1' is experimental and not covered by customer support. Please use with discretion.
""".format(self.cli_ctx.name)
        self.assertIn(remove_space(expected), remove_space(actual))


class TestArgumentExperimental(unittest.TestCase):

    def setUp(self):
        from knack.help_files import helps

        class LoggerAction(argparse.Action):

            def __call__(self, parser, namespace, values, option_string=None):
                print("Side-effect from some original action!", file=sys.stderr)

        class ExperimentalTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(ExperimentalTestCommandLoader, self).load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('arg-test', 'example_arg_handler')
                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, 'arg-test') as c:
                    c.argument('arg1', help='Arg1', is_experimental=True, action=LoggerAction)

                super(ExperimentalTestCommandLoader, self).load_arguments(command)

        helps['grp1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=ExperimentalTestCommandLoader)

    @redirect_io
    def test_experimental_arguments_command_help(self):
        """ Ensure experimental arguments appear correctly in command help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test -h'.split())
        actual = self.io.getvalue()
        expected = """
Arguments
    --arg1 [Experimental] [Required] : Arg1.
        Argument '--arg1' is experimental and not covered by customer support. Please use with discretion.
""".format(self.cli_ctx.name)
        self.assertIn(remove_space(expected), remove_space(actual))

    @redirect_io
    def test_experimental_arguments_execute(self):
        """ Ensure deprecated arguments can be used. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar'.split())
        actual = self.io.getvalue()
        experimental_expected = "Argument '--arg1' is experimental and not covered by customer support. " \
                                "Please use with discretion."
        self.assertIn(experimental_expected, actual)

        action_expected = "Side-effect from some original action!"
        self.assertIn(action_expected, actual)


if __name__ == '__main__':
    unittest.main()
