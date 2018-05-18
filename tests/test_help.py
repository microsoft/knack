# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
import mock
from six import StringIO


from knack.help import ArgumentGroupRegistry, HelpObject
from knack.arguments import ArgumentsContext
from knack.commands import CLICommand, CLICommandsLoader, CommandGroup
from knack.events import EVENT_PARSER_GLOBAL_CREATE
from knack.invocation import CommandInvoker

from tests.util import MockContext, TestCLI

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

        from knack.help_files import helps

        class HelpTestCommandLoader(CLICommandsLoader):
            def load_command_table(self, args):
                super(HelpTestCommandLoader, self).load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('n1', 'example_handler')
                    g.command('n2', 'example_handler')
                    g.command('n3', 'example_handler')
                    g.command('n4', 'example_handler')
                    g.command('n5', 'example_handler')

                with CommandGroup(self, 'group alpha', '{}#{{}}'.format(__name__)) as g:
                    g.command('n1', 'example_handler')

                with CommandGroup(self, 'group beta', '{}#{{}}'.format(__name__)) as g:
                    g.command('n1', 'example_handler')

                return self.command_table

            def load_arguments(self, command):
                for scope in ['n1', 'group alpha', 'group beta']:
                    with ArgumentsContext(self, scope) as c:
                        c.argument('arg1', options_list=['--arg', '-a'], required=False, type=int, choices=[1, 2, 3])
                        c.argument('arg2', options_list=['-b'], required=True, choices=['a', 'b', 'c'])

                for scope in ['n4', 'n5']:
                    with ArgumentsContext(self, scope) as c:
                        c.argument('arg1', options_list=['--foobar'])
                        c.argument('arg2', options_list=['--foobar2'], required=True)
                        c.argument('arg3', options_list=['--foobar3'], help='the foobar3')

                super(HelpTestCommandLoader, self).load_arguments(command)

        helps['n2'] = """
    type: command
    short-summary: YAML short summary.
    long-summary: YAML long summary. More summary.
"""

        helps['n3'] = """
    type: command
    long-summary: |
        line1
        line2
"""

        helps['n4'] = """
    type: command
    parameters:
        - name: --foobar
          type: string
          required: false
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands:
            - mycli abc xyz
            - default
        - name: --foobar2
          type: string
          required: true
          short-summary: one line partial sentence
          long-summary: paragraph(s)
"""

        helps['n5'] = """
    type: command
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters:
        - name: --foobar
          type: string
          required: false
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands:
            - mycli abc xyz
            - default
        - name: --foobar2
          type: string
          required: true
          short-summary: one line partial sentence
          long-summary: paragraph(s)
    examples:
        - name: foo example
          text: example details
"""

        helps['group alpha'] = """
    type: group
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
"""

        helps['group alpha n1'] = """
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters:
        - name: --arg -a
          type: string
          required: false
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands:
            - mycli abc xyz
            - default
        - name: -b
          type: string
          required: true
          short-summary: one line partial sentence
          long-summary: paragraph(s)
    examples:
        - name: foo example
          text: example details
"""

        self.cli_ctx = TestCLI(commands_loader_cls=HelpTestCommandLoader)

    @redirect_io
    def test_choice_list_with_ints(self):
        """ Ensure choice_list works with integer lists. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())
        actual = io.getvalue()
        expected = 'Allowed values: 1, 2, 3'
        self.assertTrue(expected in actual)

    @redirect_io
    def test_help_param(self):
        """ Ensure both --help and -h produce the same output. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 --help'.split())

    @redirect_io
    def test_help_long_and_short_description_from_docstring(self):
        """ Ensure the first sentence of a docstring is parsed as the short summary and subsequent text is interpretted
        as the long summary. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())
        actual = io.getvalue()
        expected = '\nCommand\n    {} n1 : Short summary here.\n        Long summary here. Still long summary.'.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_long_and_short_description_from_yaml(self):
        """ Ensure the YAML version of short and long summary display correctly and override any values that may
        have been obtained through reflection. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n2 -h'.split())
        actual = io.getvalue()
        expected = '\nCommand\n    {} n2 : YAML short summary.\n        YAML long summary. More summary.'.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_long_description_multi_line(self):
        """ Ensure that multi-line help in the YAML is displayed correctly. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n3 -h'.split())
        actual = io.getvalue()
        expected = '\nCommand\n    {} n3 : Short summary here.\n        Line1\n        line2.\n'.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_params_documentations(self):
        """ Ensure argument help is rendered according to the YAML spec. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n4 -h'.split())
        expected = """
Command
    {} n4 : Short summary here.

Arguments
    --foobar  [Required] : One line partial sentence.  Values from: mycli abc xyz, default.
        Text, markdown, etc.
    --foobar2 [Required] : One line partial sentence.
        Paragraph(s).
    --foobar3            : The foobar3.
"""
        actual = io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_full_documentations(self):
        """ Test all features of YAML format. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n5 -h'.split())
        expected = """
Command
    {} n5 : This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Arguments
    --foobar  [Required] : One line partial sentence.  Values from: mycli abc xyz, default.
        Text, markdown, etc.
    --foobar2 [Required] : One line partial sentence.
        Paragraph(s).
    --foobar3            : The foobar3.

Global Arguments
    --debug              : Increase logging verbosity to show all debug logs.
    --help -h            : Show this help message and exit.
    --output -o          : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
    --query              : JMESPath query string. See http://jmespath.org/ for more information and
                           examples.
    --verbose            : Increase logging verbosity. Use --debug for full debug logs.

Examples
    foo example
        example details

"""
        actual = io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_with_param_specified(self):
        """ Ensure help appears even if some arguments are specified. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 --arg 1 -h'.split())
        expected = """
Command
    {} n1 : Short summary here.
        Long summary here. Still long summary.

Arguments
    -b [Required] : Allowed values: a, b, c.
    --arg -a      : Allowed values: 1, 2, 3.
    --arg3

Global Arguments
    --debug       : Increase logging verbosity to show all debug logs.
    --help -h     : Show this help message and exit.
    --output -o   : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
    --query       : JMESPath query string. See http://jmespath.org/ for more information and
                    examples.
    --verbose     : Increase logging verbosity. Use --debug for full debug logs.

"""
        actual = io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)

    @redirect_io
    def test_help_group_children(self):
        """ Ensure subgroups appear correctly. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group -h'.split())

        expected = """
Group
    {} group

Subgroups:
    alpha : This module does xyz one-line or so.
    beta

"""
        actual = io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)

    @redirect_io
    def test_help_missing_params(self):
        """ Ensure the appropriate error is thrown when a required argument is missing. """

        # work around an argparse behavior where output is not printed and SystemExit
        # is not raised on Python 2.7.9
        if sys.version_info < (2, 7, 10):
            try:
                self.cli_ctx.invoke('n1 -a 1 --arg 2'.split())
            except SystemExit:
                pass
        else:
            with self.assertRaises(SystemExit):
                self.cli_ctx.invoke('n1 -a 1 --arg 2'.split())

            actual = io.getvalue()
            self.assertTrue('required' in actual and '-b' in actual)

    @redirect_io
    def test_help_extra_params(self):
        """ Ensure appropriate error is thrown when an extra argument is used. """

        # work around an argparse behavior where output is not printed and SystemExit
        # is not raised on Python 2.7.9
        if sys.version_info < (2, 7, 10):
            try:
                self.cli_ctx.invoke('n1 -a 1 -b c -c extra'.split())
            except SystemExit:
                pass
        else:
            with self.assertRaises(SystemExit):
                self.cli_ctx.invoke('n1 -a 1 -b c -c extra'.split())

        actual = io.getvalue()
        expected = 'unrecognized arguments: -c extra'
        self.assertTrue(expected in actual)

    @redirect_io
    def test_help_group_help(self):
        """ Ensure group help appears correctly. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('group alpha -h'.split())
        expected = """
Group
    {} group alpha : This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Commands:
    n1 : This module does xyz one-line or so.

"""
        actual = io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)

    @redirect_io
    @mock.patch('knack.cli.CLI.register_event')
    def test_help_global_params(self, _):
        """ Ensure global parameters can be added and display correctly. """

        def register_globals(_, **kwargs):
            arg_group = kwargs.get('arg_group')
            arg_group.add_argument('--exampl',
                                   help='This is a new global argument.')

        self.cli_ctx._event_handlers[EVENT_PARSER_GLOBAL_CREATE].append(register_globals)  # pylint: disable=protected-access

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())
        s = """
Command
    {} n1 : Short summary here.
        Long summary here. Still long summary.

Arguments
    -b [Required] : Allowed values: a, b, c.
    --arg -a      : Allowed values: 1, 2, 3.
    --arg3

Global Arguments
    --debug       : Increase logging verbosity to show all debug logs.
    --exampl      : This is a new global argument.
    --help -h     : Show this help message and exit.
    --output -o   : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
    --query       : JMESPath query string. See http://jmespath.org/ for more information and
                    examples.
    --verbose     : Increase logging verbosity. Use --debug for full debug logs.

"""
        actual = io.getvalue()
        expected = s.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
