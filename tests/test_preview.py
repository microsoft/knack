# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
try:
    import mock
except ImportError:
    from unittest import mock

import sys
import argparse

from knack.arguments import ArgumentsContext
from knack.commands import CLICommandsLoader, CommandGroup

from tests.util import DummyCLI, redirect_io, disable_color


def example_handler(arg1, arg2=None, arg3=None):
    """ Short summary here. Long summary here. Still long summary. """
    pass


def example_arg_handler(arg1, opt1, arg2=None, opt2=None, arg3=None,
                        opt3=None, arg4=None, opt4=None, arg5=None, opt5=None):
    pass


class TestCommandPreview(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class PreviewTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('cmd1', 'example_handler', is_preview=True)

                with CommandGroup(self, 'grp1', '{}#{{}}'.format(__name__), is_preview=True) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super().load_arguments(command)

        helps['grp1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=PreviewTestCommandLoader)

    @redirect_io
    def test_preview_command_group_help(self):
        """ Ensure preview commands appear correctly in group help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('-h'.split())
        actual = self.io.getvalue()
        expected = u"""
Group
    {}

Subgroups:
    grp1 [Preview] : A group.

Commands:
    cmd1 [Preview] : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    def test_preview_command_plain_execute(self):
        """ Ensure general warning displayed when running preview command. """
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "This command is in preview. It may be changed/removed in a future release."
        self.assertIn(expected, actual)

    @redirect_io
    def test_preview_command_plain_execute_only_show_error(self):
        """ Ensure warning is suppressed when running preview command. """
        # Directly use --only-show-errors
        self.cli_ctx.invoke('cmd1 -b b --only-show-errors'.split())
        actual = self.io.getvalue()
        self.assertNotIn("preview", actual)

        # Apply --only-show-errors with config
        self.cli_ctx.only_show_errors = True
        self.cli_ctx.config.set_value('core', 'only_show_errors', 'True')
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = self.io.getvalue()
        self.assertNotIn("preview", actual)
        self.cli_ctx.config.set_value('core', 'only_show_errors', '')
        self.cli_ctx.only_show_errors = False

    @redirect_io
    @disable_color
    def test_preview_command_plain_execute_no_color(self):
        """ Ensure warning is displayed without color. """
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = self.io.getvalue()
        self.assertIn("WARNING: This command is in preview. It may be changed/removed in a future release.", actual)

    @redirect_io
    def test_preview_command_implicitly_execute(self):
        """ Ensure general warning displayed when running command from a preview parent group. """
        self.cli_ctx.invoke('grp1 cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "Command group 'grp1' is in preview. It may be changed/removed in a future release."
        self.assertIn(expected, actual)

    @redirect_io
    @disable_color
    def test_preview_command_implicitly_no_color(self):
        """ Ensure warning is displayed without color. """
        self.cli_ctx.invoke('grp1 cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "WARNING: Command group 'grp1' is in preview. It may be changed/removed in a future release."
        self.assertIn(expected, actual)


class TestCommandGroupPreview(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class PreviewTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)

                with CommandGroup(self, 'group1', '{}#{{}}'.format(__name__), is_preview=True) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super().load_arguments(command)

        helps['group1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=PreviewTestCommandLoader)

    @redirect_io
    def test_preview_command_group_help_plain(self):
        """ Ensure help warnings appear for preview command group help. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    cli group1 : A group.
        This command group is in preview. It may be changed/removed in a future release.
Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    @disable_color
    def test_preview_command_group_help_plain_no_color(self):
        """ Ensure warning is displayed without color. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    cli group1 : A group.
        WARNING: This command group is in preview. It may be changed/removed in a future release.
Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    def test_preview_command_implicitly(self):
        """ Ensure help warning displayed for command in preview because of a preview parent group. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 cmd1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Command
    {} group1 cmd1 : Short summary here.
        Long summary here. Still long summary.
        Command group 'group1' is in preview. It may be changed/removed in a future
        release.
""".format(self.cli_ctx.name)
        self.assertIn(expected, actual)


class TestArgumentPreview(unittest.TestCase):

    def setUp(self):
        from knack.help_files import helps

        class LoggerAction(argparse.Action):

            def __call__(self, parser, namespace, values, option_string=None):
                print("Side-effect from some original action!", file=sys.stderr)

        class PreviewTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('arg-test', 'example_arg_handler')
                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, 'arg-test') as c:
                    c.argument('arg1', help='Arg1', is_preview=True, action=LoggerAction)

                super().load_arguments(command)

        helps['grp1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=PreviewTestCommandLoader)

    @redirect_io
    def test_preview_arguments_command_help(self):
        """ Ensure preview arguments appear correctly in command help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test -h'.split())
        actual = self.io.getvalue()
        expected = """
Arguments
    --arg1 [Preview] [Required] : Arg1.
        Argument '--arg1' is in preview. It may be changed/removed in a future release.
""".format(self.cli_ctx.name)
        self.assertIn(expected, actual)

    @redirect_io
    @disable_color
    def test_preview_arguments_command_help_no_color(self):
        """ Ensure warning is displayed without color. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test -h'.split())
        actual = self.io.getvalue()
        expected = """
Arguments
    --arg1 [Preview] [Required] : Arg1.
        WARNING: Argument '--arg1' is in preview. It may be changed/removed in a future release.
""".format(self.cli_ctx.name)
        self.assertIn(expected, actual)

    @redirect_io
    def test_preview_arguments_execute(self):
        """ Ensure deprecated arguments can be used. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar'.split())
        actual = self.io.getvalue()
        preview_expected = "Argument '--arg1' is in preview. It may be changed/removed in a future release."
        self.assertIn(preview_expected, actual)

        action_expected = "Side-effect from some original action!"
        self.assertIn(action_expected, actual)

    @redirect_io
    @disable_color
    def test_preview_arguments_execute_no_color(self):
        """ Ensure warning is displayed without color. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar'.split())
        actual = self.io.getvalue()
        preview_expected = "WARNING: Argument '--arg1' is in preview. It may be changed/removed in a future release."
        self.assertIn(preview_expected, actual)

        action_expected = "Side-effect from some original action!"
        self.assertIn(action_expected, actual)


    @redirect_io
    def test_preview_arguments_execute_only_show_error(self):
        """ Ensure warning is suppressed when using preview arguments. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --only-show-errors'.split())
        actual = self.io.getvalue()
        self.assertNotIn("preview", actual)

        action_expected = "Side-effect from some original action!"
        self.assertIn(action_expected, actual)

if __name__ == '__main__':
    unittest.main()
