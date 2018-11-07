# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest

from knack.commands import CLICommandsLoader, CommandGroup
from knack.arguments import CLIArgumentType, CLICommandArgument, ArgumentsContext
from tests.util import MockContext


def _dictContainsSubset(expected, actual):
    """Checks whether actual is a superset of expected.
       Helper for deprecated assertDictContainsSubset"""
    missing = False
    mismatched = False
    for key, value in expected.items():
        if key not in actual:
            missing = True
        elif value != actual[key]:
            mismatched = True
    return False if missing or mismatched else True


class TestCommandRegistration(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()

    @staticmethod
    def sample_command_handler(group_name, resource_name, opt_param=None, expand=None):
        """
        The operation to get a virtual machine.

        :param group_name: The name of the group.
        :type group_name: str
        :param resource_name: The name of the resource.
        :type resource_name: str
        :param opt_param: Used to verify reflection correctly
        identifies optional params.
        :type opt_param: object
        :param expand: The expand expression to apply on the operation.
        :type expand: str
        :param dict custom_headers: headers that will be added to the request
        :param boolean raw: returns the direct response alongside the
            deserialized response
        """
        pass

    @staticmethod
    def sample_command_handler2(group_name, resource_name, opt_param=None, expand=None, custom_headers=None,
                                raw=False, **operation_config):
        pass

    def _set_command_name(self, command):
        self.mock_ctx.invocation.data['command_string'] = command
        return command

    def test_register_cli_argument(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test register sample-command')
        with CommandGroup(cl, 'test register', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__))
        with ArgumentsContext(cl, command_name) as ac:
            ac.argument('resource_name', CLIArgumentType(
                options_list=('--wonky-name', '-n'), metavar='RNAME', help='Completely WONKY name...',
                required=False
            ))
        cl.load_arguments(command_name)
        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'group_name': CLIArgumentType(dest='group_name', required=True),
            'resource_name': CLIArgumentType(dest='resource_name', required=False),
        }
        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            contains_subset = _dictContainsSubset(some_expected_arguments[existing].settings,
                                                  command_metadata.arguments[existing].options)
            self.assertTrue(contains_subset)
        self.assertEqual(command_metadata.arguments['resource_name'].options_list, ('--wonky-name', '-n'))

    def test_register_command_custom_excluded_params(self):
        command_name = self._set_command_name('test sample-command')
        ep = ['self', 'raw', 'custom_headers', 'operation_config', 'content_version', 'kwargs', 'client']
        cl = CLICommandsLoader(self.mock_ctx, excluded_command_handler_args=ep)
        with CommandGroup(cl, 'test', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler2.__name__))
        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        cl.load_arguments(command_name)
        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        self.assertIn(command_name, cl.command_table)

    def test_register_command(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test register sample-command')
        with CommandGroup(cl, 'test register', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__))

        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        cl.load_arguments(command_name)
        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'group_name': CLIArgumentType(dest='group_name',
                                          required=True,
                                          help='The name of the group.'),
            'resource_name': CLIArgumentType(dest='resource_name',
                                             required=True,
                                             help='The name of the resource.'),
            'opt_param': CLIArgumentType(required=False,
                                         help='Used to verify reflection correctly identifies optional params.'),
            'expand': CLIArgumentType(required=False,
                                      help='The expand expression to apply on the operation.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            contains_subset = _dictContainsSubset(some_expected_arguments[existing].settings,
                                                  command_metadata.arguments[existing].options)
            self.assertTrue(contains_subset)
        self.assertEqual(command_metadata.arguments['resource_name'].options_list, ['--resource-name'])

    def test_register_command_group_with_no_group_name(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('sample-command')
        with CommandGroup(cl, None, '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__))

        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        self.assertIn(command_name, cl.command_table)

    def test_register_command_confirmation_bool(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test sample-command')
        with CommandGroup(cl, 'test', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__),
                      confirmation=True)
        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        cl.load_arguments(command_name)
        command_metadata = cl.command_table[command_name]
        self.assertIn('yes', command_metadata.arguments)
        self.assertEqual(command_metadata.arguments['yes'].type.settings['action'], 'store_true')
        self.assertIs(command_metadata.confirmation, True)

    def test_register_command_confirmation_callable(self):
        cl = CLICommandsLoader(self.mock_ctx)

        def confirm_callable(_):
            pass
        command_name = self._set_command_name('test sample-command')
        with CommandGroup(cl, 'test', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__),
                      confirmation=confirm_callable)
        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        cl.load_arguments(command_name)
        command_metadata = cl.command_table[command_name]
        self.assertIn('yes', command_metadata.arguments)
        self.assertEqual(command_metadata.arguments['yes'].type.settings['action'], 'store_true')
        self.assertIs(command_metadata.confirmation, confirm_callable)

    def test_register_cli_argument_with_overrides(self):
        cl = CLICommandsLoader(self.mock_ctx)
        base_type = CLIArgumentType(options_list=['--foo', '-f'], metavar='FOO', help='help1')
        derived_type = CLIArgumentType(base_type=base_type, help='help2')
        with CommandGroup(cl, 'test', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-get', '{}.{}'.format(TestCommandRegistration.__name__,
                                                   TestCommandRegistration.sample_command_handler.__name__))
            g.command('command sample-get-1', '{}.{}'.format(TestCommandRegistration.__name__,
                                                             TestCommandRegistration.sample_command_handler.__name__))
            g.command('command sample-get-2', '{}.{}'.format(TestCommandRegistration.__name__,
                                                             TestCommandRegistration.sample_command_handler.__name__))
        self.assertEqual(len(cl.command_table), 3, 'We expect exactly three commands in the command table')

        def test_with_command(command, target_value):
            self._set_command_name(command)
            with ArgumentsContext(cl, 'test') as c:
                c.argument('resource_name', base_type)
            with ArgumentsContext(cl, 'test command') as c:
                c.argument('resource_name', derived_type)
            with ArgumentsContext(cl, 'test command sample-get-2') as c:
                c.argument('resource_name', derived_type, help='help3')
            cl.load_arguments(command)
            command1 = cl.command_table[command].arguments['resource_name']
            self.assertEqual(command1.options['help'], target_value)

        test_with_command('test sample-get', 'help1')
        test_with_command('test command sample-get-1', 'help2')
        test_with_command('test command sample-get-2', 'help3')

    def test_register_extra_cli_argument(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test register sample-command')
        with CommandGroup(cl, 'test register', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__))
        with ArgumentsContext(cl, command_name) as ac:
            ac.extra('added_param', options_list=('--added-param',),
                     metavar='ADDED', help='Just added this right now!', required=True)
        cl.load_arguments(command_name)
        self.assertEqual(len(cl.command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 5, 'We expected exactly 5 arguments')

        some_expected_arguments = {
            'added_param': CLIArgumentType(dest='added_param', required=True)
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            contains_subset = _dictContainsSubset(some_expected_arguments[existing].settings,
                                                  command_metadata.arguments[existing].options)
            self.assertTrue(contains_subset)

    def test_register_ignore_cli_argument(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test register sample-command')
        self.mock_ctx.invocation.data['command_string'] = command_name
        with CommandGroup(cl, 'test register', '{}#{{}}'.format(__name__)) as g:
            g.command('sample-command', '{}.{}'.format(TestCommandRegistration.__name__,
                                                       TestCommandRegistration.sample_command_handler.__name__))
        with ArgumentsContext(cl, 'test register') as ac:
            ac.argument('resource_name', options_list=['--this'])
        with ArgumentsContext(cl, 'test register sample-command') as ac:
            ac.ignore('resource_name')
            ac.argument('opt_param', options_list=['--this'])
        cl.load_arguments(command_name)
        self.assertNotEqual(cl.command_table[command_name].arguments['resource_name'].options_list,
                            cl.command_table[command_name].arguments['opt_param'].options_list,
                            "Name conflict in options list")

    def test_command_build_argument_help_text(self):
        def sample_sdk_method_with_weird_docstring(param_a, param_b, param_c):  # pylint: disable=unused-argument
            """
            An operation with nothing good.

            :param dict param_a:
            :param param_b: The name
            of
            nothing.
            :param param_c: The name
            of

            nothing2.
            """
            pass

        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('test command foo')
        setattr(sys.modules[__name__], sample_sdk_method_with_weird_docstring.__name__,
                sample_sdk_method_with_weird_docstring)
        with CommandGroup(cl, 'test command', '{}#{{}}'.format(__name__)) as g:
            g.command('foo', sample_sdk_method_with_weird_docstring.__name__)
        cl.load_arguments(command_name)
        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = {
            'param_a': CLIArgumentType(dest='param_a', required=True, help=''),
            'param_b': CLIArgumentType(dest='param_b', required=True, help='The name of nothing.'),
            'param_c': CLIArgumentType(dest='param_c', required=True, help='The name of nothing2.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            contains_subset = _dictContainsSubset(some_expected_arguments[existing].settings,
                                                  command_metadata.arguments[existing].options)
            self.assertTrue(contains_subset)

    def test_override_existing_option_string(self):
        arg = CLIArgumentType(options_list=('--funky', '-f'))
        updated_options_list = ('--something-else', '-s')
        arg.update(options_list=updated_options_list, validator=lambda: (), completer=lambda: ())
        self.assertEqual(arg.settings['options_list'], updated_options_list)
        self.assertIsNotNone(arg.settings['validator'])
        self.assertIsNotNone(arg.settings['completer'])

    def test_dont_override_existing_option_string(self):
        existing_options_list = ('--something-else', '-s')
        arg = CLIArgumentType(options_list=existing_options_list)
        arg.update()
        self.assertEqual(arg.settings['options_list'], existing_options_list)

    def test_override_remove_validator(self):
        existing_options_list = ('--something-else', '-s')
        arg = CLIArgumentType(options_list=existing_options_list,
                              validator=lambda *args, **kwargs: ())
        arg.update(validator=None)
        self.assertIsNone(arg.settings['validator'])

    def test_override_using_register_cli_argument(self):
        def sample_sdk_method(param_a):  # pylint: disable=unused-argument
            pass

        def test_validator_completer():
            pass

        cl = CLICommandsLoader(self.mock_ctx)
        command_name = self._set_command_name('override_using_register_cli_argument foo')
        setattr(sys.modules[__name__], sample_sdk_method.__name__, sample_sdk_method)
        with CommandGroup(cl, 'override_using_register_cli_argument', '{}#{{}}'.format(__name__)) as g:
            g.command('foo', sample_sdk_method.__name__)
        with ArgumentsContext(cl, 'override_using_register_cli_argument') as ac:
            ac.argument('param_a',
                        options_list=('--overridden', '-r'),
                        validator=test_validator_completer,
                        completer=test_validator_completer,
                        required=False)
        cl.load_arguments(command_name)

        command_metadata = cl.command_table[command_name]
        self.assertEqual(len(command_metadata.arguments), 1, 'We expected exactly 1 arguments')

        actual_arg = command_metadata.arguments['param_a']
        self.assertEqual(actual_arg.options_list, ('--overridden', '-r'))
        self.assertEqual(actual_arg.validator, test_validator_completer)
        self.assertEqual(actual_arg.completer, test_validator_completer)
        self.assertFalse(actual_arg.options['required'])

    def test_override_argtype_with_argtype(self):
        existing_options_list = ('--default', '-d')
        arg = CLIArgumentType(options_list=existing_options_list, validator=None, completer='base',
                              help='base', required=True)
        overriding_argtype = CLIArgumentType(options_list=('--overridden',), validator='overridden',
                                             completer=None, overrides=arg, help='overridden',
                                             required=CLIArgumentType.REMOVE)
        self.assertEqual(overriding_argtype.settings['validator'], 'overridden')
        self.assertIsNone(overriding_argtype.settings['completer'])
        self.assertEqual(overriding_argtype.settings['options_list'], ('--overridden',))
        self.assertEqual(overriding_argtype.settings['help'], 'overridden')
        self.assertEqual(overriding_argtype.settings['required'], CLIArgumentType.REMOVE)

        cmd_arg = CLICommandArgument(dest='whatever', argtype=overriding_argtype,
                                     help=CLIArgumentType.REMOVE)
        self.assertNotIn('required', cmd_arg.options)
        self.assertNotIn('help', cmd_arg.options)

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            CLICommandsLoader(cli_ctx=object())


if __name__ == '__main__':
    unittest.main()
