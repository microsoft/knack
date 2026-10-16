# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import copy
from contextlib import redirect_stdout
from io import StringIO
import sys
import unittest
from unittest import mock

from knack.arguments import ArgumentsContext
from knack.commands import CLICommandsLoader, CommandGroup
from knack.events import EVENT_PARSER_GLOBAL_CREATE
from knack.help import (ArgumentGroupRegistry, CommandHelpFile, HelpAuthoringException,
                        HelpFile, HelpObject, HelpParameter)
from tests.util import DummyCLI, redirect_io


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
        self.assertEqual(obj.short_summary, '{}.'.format(original_summary))

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
                super().load_command_table(args)
                with CommandGroup(self, '', '{}#{{}}'.format(__name__)) as g:
                    g.command('n1', 'example_handler')
                    g.command('n2', 'example_handler')
                    g.command('n3', 'example_handler')
                    g.command('n4', 'example_handler')
                    g.command('n5', 'example_handler')
                    g.command('n6', 'example_handler')
                    g.command('n7', 'example_handler')
                    g.command('n8', 'example_handler')

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

                with ArgumentsContext(self, 'n6') as c:
                    c.argument('arg1', options_list=['--fmt'], default='my-default',
                               help='default=%(default)s prog=%(prog)s')

                with ArgumentsContext(self, 'n7') as c:
                    c.argument('arg1', options_list=['--pct'], help='ratio 100%%')

                with ArgumentsContext(self, 'n8') as c:
                    c.argument('arg1', options_list=['--bad'], help='bad % token')

                super().load_arguments(command)

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

        self.cli_ctx = DummyCLI(commands_loader_cls=HelpTestCommandLoader)

    @redirect_io
    def test_choice_list_with_ints(self):
        """ Ensure choice_list works with integer lists. """
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())
        actual = self.io.getvalue()
        expected = 'Allowed values: 1, 2, 3'
        self.assertIn(expected, actual)

    @redirect_io
    def test_help_param(self):
        """ Ensure both --help and -h produce the same output. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 --help'.split())

    @redirect_io
    def test_help_long_and_short_description_from_docstring(self):
        """ Ensure the first sentence of a docstring is parsed as the short summary and subsequent text is interpreted
        as the long summary. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n1 -h'.split())
        actual = self.io.getvalue()
        expected = '\nCommand\n    {} n1 : Short summary here.\n        Long summary here. Still long summary.'.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_long_and_short_description_from_yaml(self):
        """ Ensure the YAML version of short and long summary display correctly and override any values that may
        have been obtained through reflection. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n2 -h'.split())
        actual = self.io.getvalue()
        expected = '\nCommand\n    {} n2 : YAML short summary.\n        YAML long summary. More summary.'.format(self.cli_ctx.name)
        self.assertTrue(actual.startswith(expected))

    @redirect_io
    def test_help_long_description_multi_line(self):
        """ Ensure that multi-line help in the YAML is displayed correctly. """

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n3 -h'.split())
        actual = self.io.getvalue()
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
        actual = self.io.getvalue()
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
    --only-show-errors   : Only show errors, suppressing warnings.
    --output -o          : Output format.  Allowed values: json, jsonc, none, table, tsv, yaml,
                           yamlc.  Default: json.
    --query              : JMESPath query string. See http://jmespath.org/ for more information and
                           examples.
    --verbose            : Increase logging verbosity. Use --debug for full debug logs.

Examples
    foo example
        example details

"""
        actual = self.io.getvalue()
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
    -b      [Required] : Allowed values: a, b, c.
    --arg -a           : Allowed values: 1, 2, 3.
    --arg3

Global Arguments
    --debug            : Increase logging verbosity to show all debug logs.
    --help -h          : Show this help message and exit.
    --only-show-errors : Only show errors, suppressing warnings.
    --output -o        : Output format.  Allowed values: json, jsonc, none, table, tsv, yaml, yamlc.
                         Default: json.
    --query            : JMESPath query string. See http://jmespath.org/ for more information and
                         examples.
    --verbose          : Increase logging verbosity. Use --debug for full debug logs.

"""
        actual = self.io.getvalue()
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
        actual = self.io.getvalue()
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

            actual = self.io.getvalue()
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

        actual = self.io.getvalue()
        expected = 'unrecognized arguments: -c extra'
        self.assertIn(expected, actual)

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
        actual = self.io.getvalue()
        expected = expected.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)

    @redirect_io
    def test_help_argparse_default_and_prog_placeholders(self):
        """Ensure argparse placeholders are expanded in help text."""

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n6 -h'.split())

        actual = self.io.getvalue()
        self.assertIn('Default=my-default prog=', actual)
        self.assertNotIn('%(default)s', actual)
        self.assertNotIn('%(prog)s', actual)

    @redirect_io
    def test_help_argparse_escaped_percent(self):
        """Ensure escaped percent signs render as a single literal percent."""

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n7 -h'.split())

        actual = self.io.getvalue()
        self.assertIn('Ratio 100%.', actual)
        self.assertNotIn('Ratio 100%%.', actual)

    @redirect_io
    def test_help_argparse_bad_percent_falls_back(self):
        """Ensure malformed formatting falls back to the original help text."""

        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('n8 -h'.split())

        actual = self.io.getvalue()
        self.assertIn('Bad % token.', actual)

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
    -b      [Required] : Allowed values: a, b, c.
    --arg -a           : Allowed values: 1, 2, 3.
    --arg3

Global Arguments
    --debug            : Increase logging verbosity to show all debug logs.
    --exampl           : This is a new global argument.
    --help -h          : Show this help message and exit.
    --only-show-errors : Only show errors, suppressing warnings.
    --output -o        : Output format.  Allowed values: json, jsonc, none, table, tsv, yaml, yamlc.
                         Default: json.
    --query            : JMESPath query string. See http://jmespath.org/ for more information and
                         examples.
    --verbose          : Increase logging verbosity. Use --debug for full debug logs.

"""
        actual = self.io.getvalue()
        expected = s.format(self.cli_ctx.name)
        self.assertEqual(actual, expected)


class TestHelpParameterNames(unittest.TestCase):

    def setUp(self):
        from knack.invocation import CommandInvoker
        cli_ctx = DummyCLI()
        cli_ctx.invocation = CommandInvoker(cli_ctx)
        self.help_ctx = cli_ctx.invocation.help

    @staticmethod
    def _parser():
        parser = argparse.ArgumentParser(prog='test copy')
        parser.add_argument('--source', '-s', help='Original source')
        parser.add_argument('--source-path', help='Original path')
        parser.add_argument('destination', metavar='destination file', help='Original destination')
        return parser

    def _render(self, parameters):
        parser = self._parser()
        # Use the public renderer and the same YAML decoder as authored help files.
        import yaml
        parser.help_file = yaml.safe_dump({'parameters': parameters})
        output = StringIO()
        with redirect_stdout(output):
            self.help_ctx.show_help('test', ['copy'], parser, False)
        return output.getvalue()

    def test_alias_names_render_authored_help(self):
        for name in ['--source', '-s', '-s --source', '--source -s',
                     ' --source ', '\t-s\n', '  -s\t--source\n']:
            with self.subTest(name=name):
                output = self._render([{
                    'name': name, 'short-summary': 'Authored source',
                    'long-summary': 'More source details',
                    'populator-commands': ['test sources']
                }])
                self.assertIn('Authored source.', output)
                self.assertIn('More source details.', output)
                self.assertIn('Values from: test sources.', output)
                self.assertIn('--source -s', output)
                self.assertNotIn('Original source.', output)
                self.assertIn('--source-path', output)
                self.assertIn('Original path.', output)

    def test_exact_match_precedes_alias_regardless_of_entry_order(self):
        exact = {'name': '--source -s', 'short-summary': 'Exact summary'}
        alias = {'name': '--source', 'short-summary': 'Alias summary'}
        for entries in [[alias, exact], [exact, alias]]:
            with self.subTest(entries=entries):
                output = self._render(entries)
                self.assertIn('Exact summary.', output)
                self.assertNotIn('Alias summary.', output)

    def test_unrelated_and_partial_names_do_not_override_help(self):
        for name in ['--sour', 'source', '--source-path -s', '--source --unknown',
                     '--source -s extra', '--source -s -s', 'destination',
                     'file destination', 'destination file extra']:
            with self.subTest(name=name):
                output = self._render([{'name': name, 'short-summary': 'Wrong summary'}])
                self.assertNotIn('Wrong summary.', output)
                self.assertIn('Original source.', output)
                self.assertIn('Original destination.', output)

    def test_positional_name_with_spaces_is_exact(self):
        output = self._render([{'name': 'destination file', 'short-summary': 'Authored destination'}])
        self.assertIn('destination file', output)
        self.assertIn('Authored destination.', output)

    def test_loading_does_not_modify_authored_data_or_canonical_names(self):
        data = {'parameters': [{'name': '-s --source', 'short-summary': 'Authored source'}]}
        original = copy.deepcopy(data)
        help_file = CommandHelpFile(self.help_ctx, 'copy', self._parser())
        names = [p.name for p in help_file.parameters]
        help_file._load_from_data(data)  # pylint: disable=protected-access
        self.assertEqual(data, original)
        self.assertEqual([p.name for p in help_file.parameters], names)
        self.assertEqual(help_file.parameters[1].short_summary, 'Authored source.')

    def test_direct_update_accepts_only_single_alias_or_complete_alias_list(self):
        for name in ['--source', '-s', '--src', '-s --src --source', '--source --src -s',
                     ' --source ', '\t-s\n', ' --src\t--source  -s ']:
            with self.subTest(name=name):
                parameter = HelpParameter(['--source', '-s', '--src'], 'Original', False,
                                          is_positional=False)
                data = {'name': name, 'type': 'integer', 'short-summary': 'Updated'}
                original = copy.deepcopy(data)
                parameter.update_from_data(data)
                self.assertEqual(parameter.short_summary, 'Updated.')
                self.assertEqual(parameter.type, 'integer')
                self.assertEqual(parameter.name, '--source --src -s')
                self.assertEqual(data, original)

    def test_direct_update_rejects_invalid_names(self):
        for name in [None, '', 1, ['--source'], '--sour', 'source',
                     '--source -s', '--source --unknown -s', '--source --src -s -s']:
            with self.subTest(name=name):
                parameter = HelpParameter(['--source', '-s', '--src'], 'Original', False,
                                          is_positional=False)
                with self.assertRaises(HelpAuthoringException):
                    parameter.update_from_data({'name': name, 'short-summary': 'Wrong'})
                self.assertEqual(parameter.short_summary, 'Original.')

    def test_direct_update_preserves_positional_name_boundaries(self):
        parameter = HelpParameter(['source file'], 'Original', False)
        for name in ['source', 'file', 'file source']:
            with self.subTest(name=name), self.assertRaises(HelpAuthoringException):
                parameter.update_from_data({'name': name})
        parameter.update_from_data({'name': 'source file', 'short-summary': 'Updated'})
        self.assertEqual(parameter.short_summary, 'Updated.')

    def test_dash_prefixed_positional_metavars_match_exactly(self):
        import yaml
        for metavar in ['-FILE', '--input', '--destination', '-', '-FILE -OTHER']:
            for name in [metavar, ' ' + metavar + ' ', '\t' + metavar + '\n',
                         ' '.join(reversed(metavar.split()))]:
                with self.subTest(metavar=metavar, name=name):
                    parser = self._parser()
                    parser.add_argument('input_file', metavar=metavar, help='Original input')
                    parser.help_file = yaml.safe_dump({'parameters': [
                        {'name': name, 'short-summary': 'Authored input'}
                    ]})
                    output = StringIO()
                    with redirect_stdout(output):
                        self.help_ctx.show_help('test', ['copy'], parser, False)
                    if name == metavar:
                        self.assertIn('Authored input.', output.getvalue())
                    else:
                        self.assertNotIn('Authored input.', output.getvalue())
                        self.assertIn('Original input.', output.getvalue())
                    help_file = CommandHelpFile(self.help_ctx, 'copy', parser)
                    parameter = next(p for p in help_file.parameters if p.name == metavar)
                    if name == metavar:
                        parameter.update_from_data({'name': name})
                    else:
                        with self.assertRaises(HelpAuthoringException):
                            parameter.update_from_data({'name': name})

    def test_deprecated_and_current_alias_groups_remain_separate(self):
        from knack.arguments import CLICommandArgument
        from knack.deprecation import Deprecated
        from knack.parser import CLICommandParser
        cli_ctx = self.help_ctx.cli_ctx
        parser = self._parser()
        deprecated = Deprecated(cli_ctx, target='--old-source', redirect='--current')
        argument = CLICommandArgument('current', options_list=['--current', '-c', deprecated],
                                      help='Original grouped')
        CLICommandParser._add_argument(parser, argument)  # pylint: disable=protected-access
        data = {'parameters': [
            {'name': '-c', 'short-summary': 'Current summary'},
            {'name': '--old-source', 'short-summary': 'Deprecated summary'}
        ]}
        help_file = CommandHelpFile(self.help_ctx, 'copy', parser)
        help_file._load_from_data(data)  # pylint: disable=protected-access
        current = next(p for p in help_file.parameters if p.name == '--current -c')
        old = next(p for p in help_file.parameters if p.name == '--old-source')
        self.assertEqual(current.short_summary, 'Current summary.')
        self.assertEqual(old.short_summary, 'Deprecated summary.')
        self.assertIsNotNone(old.deprecate_info)
        for parameter, name in [(current, '--old-source'), (old, '--current'),
                                (current, '--current -c --old-source')]:
            with self.subTest(name=name), self.assertRaises(HelpAuthoringException):
                parameter.update_from_data({'name': name})

    def test_unknown_direct_identity_is_exact_only(self):
        # Legacy calls omit identity: neither dash prefixes nor group labels prove it.
        for source in [['--FILE'], ['-FILE -OTHER'], ['--source', '-s']]:
            parameter = HelpParameter(source, 'Original', False)
            canonical = ' '.join(sorted(source))
            parameter.update_from_data({'name': canonical})
            for name in [' ' + canonical + ' ', '\t' + canonical + '\n', '-s']:
                if name == canonical:
                    continue
                with self.subTest(source=source, name=name):
                    with self.assertRaises(HelpAuthoringException):
                        parameter.update_from_data({'name': name})

    def test_optional_in_positional_display_group(self):
        parser = self._parser()
        group = parser.add_argument_group('display', 'Positional')
        group.add_argument('--other', '-o', help='Original other')
        help_file = CommandHelpFile(self.help_ctx, 'copy', parser)
        help_file._load_from_data({'parameters': [  # pylint: disable=protected-access
            {'name': ' -o ', 'short-summary': 'Authored other'}]})
        parameter = next(p for p in help_file.parameters if p.name == '--other -o')
        self.assertEqual(parameter.short_summary, 'Authored other.')
        parameter.group_name = 'Renamed display group'
        parameter.update_from_data({'name': '--other', 'short-summary': 'Still optional'})
        self.assertEqual(parameter.short_summary, 'Still optional.')

    def test_source_extracted_azure_constructor_and_loader(self):
        # Azure 8112200cfa7dc7db7825ec6fc003a6fccf0d208f _help.py:
        # exact constructor/loader and parameter update below (only indentation changed).
        # Minimal help-file base, NOT an installed/integrated Azure CLI test.
        KnackCommandHelpFile = CommandHelpFile
        from knack.help import HelpParameter as KnackHelpParameter

        class CliHelpFile(HelpFile):
            pass

        class HelpParameter(KnackHelpParameter):  # pylint: disable=redefined-outer-name
            def update_from_data(self, data):
                super().update_from_data(data)
                # original help.py value_sources are strings, update command strings to value-source dict
                if self.value_sources:
                    self.value_sources = [str_or_dict if isinstance(str_or_dict, dict) else {"link": {"command": str_or_dict}}
                                          for str_or_dict in self.value_sources]

        class CliCommandHelpFile(KnackCommandHelpFile, CliHelpFile):

            def __init__(self, help_ctx, delimiters, parser):
                super().__init__(help_ctx, delimiters, parser)
                self.type = 'command'
                self.command_source = getattr(parser, 'command_source', None)

                self.parameters = []

                for action in [a for a in parser._actions if a.help != argparse.SUPPRESS]:  # pylint: disable=protected-access
                    if action.option_strings:
                        self._add_parameter_help(action)
                    else:
                        # use metavar for positional parameters
                        param_kwargs = {
                            'name_source': [action.metavar or action.dest],
                            'deprecate_info': getattr(action, 'deprecate_info', None),
                            'preview_info': getattr(action, 'preview_info', None),
                            'experimental_info': getattr(action, 'experimental_info', None),
                            'default_value_source': getattr(action, 'default_value_source', None),
                            'description': action.help,
                            'choices': action.choices,
                            'required': False,
                            'default': None,
                            'group_name': 'Positional'
                        }
                        self.parameters.append(HelpParameter(**param_kwargs))

                help_param = next(p for p in self.parameters if p.name == '--help -h')
                help_param.group_name = 'Global Arguments'

                # update parameter type so we can use overriden update_from_data method to update value sources.
                for param in self.parameters:
                    param.__class__ = HelpParameter

            def _load_from_data(self, data):
                super()._load_from_data(data)

                if isinstance(data, str) or not self.parameters or not data.get('parameters'):
                    return

                loaded_params = []
                loaded_param = {}
                for param in self.parameters:
                    loaded_param = next((n for n in data['parameters'] if n['name'] == param.name), None)
                    if loaded_param:
                        param.update_from_data(loaded_param)
                    loaded_params.append(param)

                self.parameters = loaded_params

        self.assertEqual(CliCommandHelpFile.__mro__[1:4],
                         (CommandHelpFile, CliHelpFile, HelpFile))
        for metavar in ['--FILE', '-FILE -OTHER', ' -FILE ', 'source file']:
            for authored in [metavar, ' ' + metavar + ' ', '\t' + metavar + '\n']:
                with self.subTest(metavar=metavar, authored=authored):
                    parser = self._parser()
                    parser.add_argument('input', metavar=metavar, help='Original input')
                    help_file = CliCommandHelpFile(self.help_ctx, 'copy', parser)
                    help_file._load_from_data({'parameters': [  # pylint: disable=protected-access
                        {'name': ' -s ', 'short-summary': 'Authored option'},
                        {'name': authored, 'short-summary': 'Authored input'}]})
                    option = next(p for p in help_file.parameters if p.name == '--source -s')
                    positional = next(p for p in help_file.parameters if p.name == metavar)
                    self.assertEqual(option.short_summary, 'Authored option.')
                    expected = 'Authored input.' if authored == metavar else 'Original input.'
                    self.assertEqual(positional.short_summary, expected)


if __name__ == '__main__':
    unittest.main()
