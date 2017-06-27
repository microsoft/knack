# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest

from knack.commands import CLICommandsLoader
from knack.arguments import CLIArgumentType
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
    def sample_command_handler(group_name, resource_name, opt_param=None, expand=None, custom_headers=None,
                               raw=False, **operation_config):
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
        :rtype: VirtualMachine
        :rtype: msrest.pipeline.ClientRawResponse if raw=True
        """
        pass



    def test_register_cli_argument(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = 'test register sample-command'
        cl.cli_command(None, command_name,
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
                                         TestCommandRegistration.sample_command_handler.__name__))
        cl.register_cli_argument(command_name, 'resource_name', CLIArgumentType(
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

    def test_register_command(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = 'test register sample-command'
        cl.cli_command(None, command_name,
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
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

    def test_register_cli_argument_with_overrides(self):
        cl = CLICommandsLoader(self.mock_ctx)
        global_vm_name_type = CLIArgumentType(
            options_list=('--foo', '-f'), metavar='FOO', help='foo help'
        )
        derived_vm_name_type = CLIArgumentType(base_type=global_vm_name_type,
                                               help='first modification')
        cl.cli_command(None, 'test sample-get',
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
                                         TestCommandRegistration.sample_command_handler.__name__))
        cl.cli_command(None, 'test command sample-get-1',
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
                                         TestCommandRegistration.sample_command_handler.__name__))
        cl.cli_command(None, 'test command sample-get-2',
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
                                         TestCommandRegistration.sample_command_handler.__name__))
        cl.register_cli_argument('test', 'resource_name', global_vm_name_type)
        cl.register_cli_argument('test command', 'resource_name', derived_vm_name_type)
        cl.register_cli_argument('test command sample-get-2', 'resource_name', derived_vm_name_type,
                                 help='second modification')
        cl.load_arguments('test sample-get')
        cl.load_arguments('test command sample-get-1')
        cl.load_arguments('test command sample-get-2')
        self.assertEqual(len(cl.command_table), 3, 'We expect exactly three commands in the command table')
        command1 = cl.command_table['test sample-get'].arguments['resource_name']
        command2 = cl.command_table['test command sample-get-1'].arguments['resource_name']
        command3 = cl.command_table['test command sample-get-2'].arguments['resource_name']
        self.assertTrue(command1.options['help'] == 'foo help')
        self.assertTrue(command2.options['help'] == 'first modification')
        self.assertTrue(command3.options['help'] == 'second modification')

    def test_register_extra_cli_argument(self):
        cl = CLICommandsLoader(self.mock_ctx)
        command_name = 'test register sample-command'
        cl.cli_command(None, command_name,
                       '{}#{}.{}'.format(__name__,
                                         TestCommandRegistration.__name__,
                                         TestCommandRegistration.sample_command_handler.__name__))
        cl.register_extra_cli_argument(command_name, 'added_param', options_list=('--added-param',),
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


if __name__ == '__main__':
    unittest.main()
