# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
import mock
from six import StringIO


from knack.arguments import ArgumentsContext
from knack.commands import CLICommand, CLICommandsLoader, CommandGroup

from tests.util import TestCLI

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


def example_handler(arg1, arg2=None, arg3=None):
    """ Short summary here. Long summary here. Still long summary. """
    pass


class TestCommandDeprecation(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class DeprecationTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(DeprecationTestCommandLoader, self).load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('cmd1', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd1'))
                    g.command('cmd2', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd2', hide='1.0.0'))
                    g.command('cmd3', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd3', hide='0.1.0'))
                    g.command('cmd4', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd4', expiration='1.0.0'))
                    g.command('cmd5', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd5', expiration='0.1.0'))

                with CommandGroup(self, 'group', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group')) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super(DeprecationTestCommandLoader, self).load_arguments(command)

        helps['group'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = TestCLI(commands_loader_cls=DeprecationTestCommandLoader)

    @redirect_io
    def test_deprecate_command_group_help(self):
        """ Ensure deprecated commands appear (or don't appear) correctly in group help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('-h'.split())
        actual = io.getvalue()
        expected = """
Group
    {}

Subgroups:
    group [Deprecated] : A group.

Commands:
    cmd1  [Deprecated] : Short summary here.
    cmd2  [Deprecated] : Short summary here.
    cmd4  [Deprecated] : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    def test_deprecate_command_help_hidden(self):
        """ Ensure hidden deprecated command can be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('cmd3 -h'.split())
        actual = io.getvalue()
        expected = """
Command
    {} cmd3 : Short summary here.
        Long summary here. Still long summary. This command has been deprecated and will be
        removed in a future release. Use 'alt-cmd3' instead.

Arguments
    -b [Required] : Allowed values: a, b, c.
    --arg -a      : Allowed values: 1, 2, 3.
    --arg3
""".format(self.cli_ctx.name)
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_expired(self):
        """ Ensure expired command cannot be reached. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('cmd5 -h'.split())
        actual = io.getvalue()
        expected = "invalid choice: 'cmd5' (choose from 'cmd1', 'cmd2', 'cmd3', 'cmd4', 'group')"
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_plain_execute(self):
        """ Ensure general warning displayed when running deprecated command. """
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = io.getvalue()
        expected = "This command has been deprecated and will be removed in a future release. Use 'alt-cmd1' instead."
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_hidden_execute(self):
        """ Ensure general warning displayed when running hidden deprecated command. """
        self.cli_ctx.invoke('cmd3 -b b'.split())
        actual = io.getvalue()
        expected = "This command has been deprecated and will be removed in a future release. Use 'alt-cmd3' instead."
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_expiring_execute(self):
        """ Ensure specific warning displayed when running expiring deprecated command. """
        self.cli_ctx.invoke('cmd4 -b b'.split())
        actual = io.getvalue()
        expected = "This command has been deprecated and will be removed in version '1.0.0'. Use 'alt-cmd4' instead."
        self.assertTrue(expected in actual)


class TestCommandGroupDeprecation(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class DeprecationTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(DeprecationTestCommandLoader, self).load_command_table(args)

                with CommandGroup(self, 'group1', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group1')) as g:
                    g.command('cmd1', 'example_handler')

                with CommandGroup(self, 'group2', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group2', hide='1.0.0')) as g:
                    g.command('cmd1', 'example_handler')

                with CommandGroup(self, 'group3', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group3', hide='0.1.0')) as g:
                    g.command('cmd1', 'example_handler')

                with CommandGroup(self, 'group4', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group4', expiration='1.0.0')) as g:
                    g.command('cmd1', 'example_handler')

                with CommandGroup(self, 'group5', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-group5', expiration='0.1.0')) as g:
                    g.command('cmd1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, '') as c:
                    c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                    c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                super(DeprecationTestCommandLoader, self).load_arguments(command)

        helps['group1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = TestCLI(commands_loader_cls=DeprecationTestCommandLoader)

    @redirect_io
    def test_deprecate_command_group_help_plain(self):
        """ Ensure help warnings appear for deprecated command group help. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 -h'.split())
        actual = io.getvalue()
        expected = """
Group
    cli group1 : A group.
        This command group has been deprecated and will be removed in a future release. Use
        'alt-group1' instead.

Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        self.assertEqual(expected, actual)

    @redirect_io
    def test_deprecate_command_group_help_hidden(self):
        """ Ensure hidden deprecated command can be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group3 -h'.split())
        actual = io.getvalue()
        expected = """
Group
    {} group3
        This command group has been deprecated and will be removed in a future release. Use
        'alt-group3' instead.

Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_group_help_expiring(self):
        """ Ensure specific warning displayed when running expiring deprecated command. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group4 -h'.split())
        actual = io.getvalue()
        expected = """
Group
    {} group4
        This command group has been deprecated and will be removed in version '1.0.0'. Use
        'alt-group4' instead.
""".format(self.cli_ctx.name)
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_group_expired(self):
        """ Ensure expired command cannot be reached. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group5 -h'.split())
        actual = io.getvalue()
        expected = "invalid choice: 'group5' (choose from 'group1', 'group2', 'group3', 'group4')"
        self.assertTrue(expected in actual)

    @redirect_io
    def test_deprecate_command_implicitly(self):
        """ Ensure help warning displayed for command deprecated because of a deprecated parent group. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 cmd1 -h'.split())
        actual = io.getvalue()
        expected = """
Command
    {} group1 cmd1 : Short summary here.
        Long summary here. Still long summary. This command is implicitly deprecated because
        command group 'group1' is deprecated and will be removed in a future release. Use 'alt-
        group1' instead.
""".format(self.cli_ctx.name)
        self.assertTrue(expected in actual)


if __name__ == '__main__':
    unittest.main()
