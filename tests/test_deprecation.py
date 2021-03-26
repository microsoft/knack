# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
try:
    import mock
except ImportError:
    from unittest import mock

from knack.arguments import ArgumentsContext
from knack.commands import CLICommandsLoader, CommandGroup

from tests.util import DummyCLI, redirect_io, assert_in_multi_line, disable_color


def example_handler(arg1, arg2=None, arg3=None):
    """ Short summary here. Long summary here. Still long summary. """
    pass


def example_arg_handler(arg1, opt1, arg2=None, opt2=None, arg3=None,
                        opt3=None, arg4=None, opt4=None, arg5=None, opt5=None):
    pass


# pylint: disable=line-too-long
class TestCommandDeprecation(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class DeprecationTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('cmd1', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd1'))
                    g.command('cmd2', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd2', hide='1.0.0'))
                    g.command('cmd3', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd3', hide='0.1.0'))
                    g.command('cmd4', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd4', expiration='1.0.0'))
                    g.command('cmd5', 'example_handler', deprecate_info=g.deprecate(redirect='alt-cmd5', expiration='0.1.0'))

                with CommandGroup(self, 'grp1', '{}#{{}}'.format(__name__), deprecate_info=self.deprecate(redirect='alt-grp1')) as g:
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
        self.cli_ctx = DummyCLI(commands_loader_cls=DeprecationTestCommandLoader)

    @redirect_io
    def test_deprecate_command_group_help(self):
        """ Ensure deprecated commands appear (or don't appear) correctly in group help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('-h'.split())
        actual = self.io.getvalue()
        expected = u"""
Group
    {}

Subgroups:
    grp1 [Deprecated] : A group.

Commands:
    cmd1 [Deprecated] : Short summary here.
    cmd2 [Deprecated] : Short summary here.
    cmd4 [Deprecated] : Short summary here.

""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    def test_deprecate_command_help_hidden(self):
        """ Ensure hidden deprecated command can be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('cmd3 -h'.split())
        actual = self.io.getvalue()
        expected = """
Command
    {} cmd3 : Short summary here.
        Long summary here. Still long summary.
        This command has been deprecated and will be removed in a future release. Use 'alt-
        cmd3' instead.

Arguments
    -b      [Required] : Allowed values: a, b, c.
    --arg -a           : Allowed values: 1, 2, 3.
    --arg3
""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    def test_deprecate_command_plain_execute(self):
        """ Ensure general warning displayed when running deprecated command. """
        self.cli_ctx.invoke('cmd1 -b b'.split())
        actual = self.io.getvalue()
        expected = "This command has been deprecated and will be removed in a future release. Use 'alt-cmd1' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_hidden_execute(self):
        """ Ensure general warning displayed when running hidden deprecated command. """
        self.cli_ctx.invoke('cmd3 -b b'.split())
        actual = self.io.getvalue()
        expected = "This command has been deprecated and will be removed in a future release. Use 'alt-cmd3' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_expiring_execute(self):
        """ Ensure specific warning displayed when running expiring deprecated command. """
        self.cli_ctx.invoke('cmd4 -b b'.split())
        actual = self.io.getvalue()
        expected = "This command has been deprecated and will be removed in version '1.0.0'. Use 'alt-cmd4' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_expiring_execute_no_color(self):
        """ Ensure warning is displayed without color. """
        self.cli_ctx.enable_color = False
        self.cli_ctx.invoke('cmd4 -b b'.split())
        actual = self.io.getvalue()
        expected = "WARNING: This command has been deprecated and will be removed in version '1.0.0'"
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_expired_execute(self):
        """ Ensure expired command cannot be reached. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('cmd5 -h'.split())
        actual = self.io.getvalue()
        expected = """cli: 'cmd5' is not in the 'cli' command group."""
        self.assertIn(expected, actual)

    @redirect_io
    @disable_color
    def test_deprecate_command_expired_execute_no_color(self):
        """ Ensure error is displayed without color. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('cmd5 -h'.split())
        actual = self.io.getvalue()
        expected = """ERROR: cli: 'cmd5' is not in the 'cli' command group."""
        self.assertIn(expected, actual)


class TestCommandGroupDeprecation(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class DeprecationTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)

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

                super().load_arguments(command)

        helps['group1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=DeprecationTestCommandLoader)

    @redirect_io
    def test_deprecate_command_group_help_plain(self):
        """ Ensure help warnings appear for deprecated command group help. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    cli group1 : A group.
        This command group has been deprecated and will be removed in a future release. Use
        'alt-group1' instead.

Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    def test_deprecate_command_group_help_hidden(self):
        """ Ensure hidden deprecated command can be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group3 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    {} group3
        This command group has been deprecated and will be removed in a future release. Use
        'alt-group3' instead.

Commands:
    cmd1 : Short summary here.

""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    def test_deprecate_command_group_help_expiring(self):
        """ Ensure specific warning displayed when running expiring deprecated command. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group4 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    {} group4
        This command group has been deprecated and will be removed in version '1.0.0'. Use
        'alt-group4' instead.
""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    @disable_color
    def test_deprecate_command_group_help_expiring_no_color(self):
        """ Ensure warning is displayed without color. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group4 -h'.split())
        actual = self.io.getvalue()
        expected = """
Group
    cli group4
        WARNING: This command group has been deprecated and will be removed in version \'1.0.0\'. Use
        'alt-group4' instead.
""".format(self.cli_ctx.name)
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_group_expired(self):
        """ Ensure expired command cannot be reached. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group5 -h'.split())
        actual = self.io.getvalue()
        expected = """The most similar choices to 'group5'"""
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_command_implicitly(self):
        """ Ensure help warning displayed for command deprecated because of a deprecated parent group. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group1 cmd1 -h'.split())
        actual = self.io.getvalue()
        expected = """
Command
    {} group1 cmd1 : Short summary here.
        Long summary here. Still long summary.
        This command is implicitly deprecated because command group 'group1' is deprecated and
        will be removed in a future release. Use 'alt-group1' instead.
""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)


class TestArgumentDeprecation(unittest.TestCase):

    def setUp(self):

        from knack.help_files import helps

        class DeprecationTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super().load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('arg-test', 'example_arg_handler')
                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, 'arg-test') as c:
                    c.argument('arg1', help='Arg1', deprecate_info=c.deprecate())
                    c.argument('opt1', help='Opt1', options_list=['--opt1', c.deprecate(redirect='--opt1', target='--alt1')])
                    c.argument('arg2', help='Arg2', deprecate_info=c.deprecate(hide='1.0.0'))
                    c.argument('opt2', help='Opt2', options_list=['--opt2', c.deprecate(redirect='--opt2', target='--alt2', hide='1.0.0')])
                    c.argument('arg3', help='Arg3', deprecate_info=c.deprecate(hide='0.1.0'))
                    c.argument('opt3', help='Opt3', options_list=['--opt3', c.deprecate(redirect='--opt3', target='--alt3', hide='0.1.0')])
                    c.argument('arg4', deprecate_info=c.deprecate(expiration='1.0.0'))
                    c.argument('opt4', options_list=['--opt4', c.deprecate(redirect='--opt4', target='--alt4', expiration='1.0.0')])
                    c.argument('arg5', deprecate_info=c.deprecate(expiration='0.1.0'))
                    c.argument('opt5', options_list=['--opt5', c.deprecate(redirect='--opt5', target='--alt5', expiration='0.1.0')])

                super().load_arguments(command)

        helps['grp1'] = """
    type: group
    short-summary: A group.
"""
        self.cli_ctx = DummyCLI(commands_loader_cls=DeprecationTestCommandLoader)

    @redirect_io
    def test_deprecate_arguments_command_help(self):
        """ Ensure deprecated arguments and options appear (or don't appear)
        correctly in command help view. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test -h'.split())
        actual = self.io.getvalue()
        expected = """
Command
    {} arg-test

Arguments
    --alt1 [Deprecated] [Required] : Opt1.
        Option '--alt1' has been deprecated and will be removed in a future release. Use '--
        opt1' instead.
    --arg1 [Deprecated] [Required] : Arg1.
        Argument 'arg1' has been deprecated and will be removed in a future release.
    --opt1              [Required] : Opt1.
    --alt2            [Deprecated] : Opt2.
        Option '--alt2' has been deprecated and will be removed in a future release. Use '--
        opt2' instead.
    --alt4            [Deprecated]
        Option '--alt4' has been deprecated and will be removed in version '1.0.0'. Use '--
        opt4' instead.
    --arg2            [Deprecated] : Arg2.
        Argument 'arg2' has been deprecated and will be removed in a future release.
    --arg4            [Deprecated]
        Argument 'arg4' has been deprecated and will be removed in version '1.0.0'.
    --opt2                         : Opt2.
    --opt3                         : Opt3.
    --opt4
    --opt5
""".format(self.cli_ctx.name)
        assert_in_multi_line(expected, actual)

    @redirect_io
    def test_deprecate_arguments_execute(self):
        """ Ensure deprecated arguments can be used. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar'.split())
        actual = self.io.getvalue()
        expected = "Argument 'arg1' has been deprecated and will be removed in a future release."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_arguments_execute_hidden(self):
        """ Ensure hidden deprecated arguments can be used. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --arg3 bar'.split())
        actual = self.io.getvalue()
        expected = "Argument 'arg3' has been deprecated and will be removed in a future release."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_arguments_execute_expiring(self):
        """ Ensure hidden deprecated arguments can be used. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --arg4 bar'.split())
        actual = self.io.getvalue()
        expected = "Argument 'arg4' has been deprecated and will be removed in version '1.0.0'."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_arguments_execute_expired(self):
        """ Ensure expired deprecated arguments can't be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --arg5 foo'.split())
        actual = self.io.getvalue()
        expected = 'unrecognized arguments: --arg5 foo'
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute(self):
        """ Ensure deprecated options can be used with a warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --alt1 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt1' has been deprecated and will be removed in a future release. Use '--opt1' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_non_deprecated(self):
        """ Ensure non-deprecated options don't show warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt1' has been deprecated and will be removed in a future release. Use '--opt1' instead."
        self.assertNotIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_hidden(self):
        """ Ensure hidden deprecated options can be used with warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --alt3 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt3' has been deprecated and will be removed in a future release. Use '--opt3' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_hidden_non_deprecated(self):
        """ Ensure hidden non-deprecated optionss can be used without warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --opt3 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt3' has been deprecated and will be removed in a future release. Use '--opt3' instead."
        self.assertNotIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_expired(self):
        """ Ensure expired deprecated options can't be used. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --alt5 foo'.split())
        actual = self.io.getvalue()
        expected = 'unrecognized arguments: --alt5 foo'
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_expired_non_deprecated(self):
        """ Ensure non-expired options can be used without warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --opt5 foo'.split())
        actual = self.io.getvalue()
        self.assertTrue(u'--alt5' not in actual and u'--opt5' not in actual)

    @redirect_io
    def test_deprecate_options_execute_expiring(self):
        """ Ensure expiring options can be used with warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --alt4 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt4' has been deprecated and will be removed in version '1.0.0'. Use '--opt4' instead."
        self.assertIn(expected, actual)

    @redirect_io
    @disable_color
    def test_deprecate_options_execute_expiring_no_color(self):
        """ Ensure error is displayed without color. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --alt4 bar'.split())
        actual = self.io.getvalue()
        expected = "WARNING: Option '--alt4' has been deprecated and will be removed in version '1.0.0'. Use '--opt4' instead."
        self.assertIn(expected, actual)

    @redirect_io
    def test_deprecate_options_execute_expiring_non_deprecated(self):
        """ Ensure non-expiring options can be used without warning. """
        self.cli_ctx.invoke('arg-test --arg1 foo --opt1 bar --opt4 bar'.split())
        actual = self.io.getvalue()
        expected = "Option '--alt4' has been deprecated and will be removed in version '1.0.0'. Use '--opt4' instead."
        self.assertNotIn(expected, actual)


if __name__ == '__main__':
    unittest.main()
