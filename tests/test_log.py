# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from knack.events import EVENT_PARSER_GLOBAL_CREATE, EVENT_INVOKER_PRE_CMD_TBL_CREATE
from knack.log import CLILogging, get_logger, CLI_LOGGER_NAME
from tests.util import MockContext


class TestLoggingEventHandling(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()
        self.cli_logging = CLILogging('clitest', ctx=self.mock_ctx)

    def test_logging_argument_registrations(self):
        parser_arg_group_mock = mock.MagicMock()
        self.mock_ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=parser_arg_group_mock)
        parser_arg_group_mock.add_argument.assert_any_call(CLILogging.VERBOSE_FLAG,
                                                           dest=mock.ANY,
                                                           action=mock.ANY,
                                                           help=mock.ANY)
        parser_arg_group_mock.add_argument.assert_any_call(CLILogging.DEBUG_FLAG,
                                                           dest=mock.ANY,
                                                           action=mock.ANY,
                                                           help=mock.ANY)

    def test_logging_arguments_removed(self):
        arguments = [CLILogging.VERBOSE_FLAG, CLILogging.DEBUG_FLAG]
        self.mock_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=arguments)
        # After the event is raised, the arguments should have been removed
        self.assertFalse(arguments)

class TestLoggingLevel(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()
        self.cli_logging = CLILogging('clitest', ctx=self.mock_ctx)

    def test_determine_verbose_level_default(self):
        argv = []
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)

    def test_determine_verbose_level_verbose(self):
        argv = ['--verbose']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)

    def test_determine_verbose_level_debug(self):
        argv = ['--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)

    def test_determine_verbose_level_v_v_v_default(self):
        argv = ['--verbose', '--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)

    def test_determine_verbose_level_other_args_verbose(self):
        argv = ['account', '--verbose']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)

    def test_determine_verbose_level_other_args_debug(self):
        argv = ['account', '--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)

    def test_get_cli_logger(self):
        logger = get_logger()
        self.assertEqual(logger.name, CLI_LOGGER_NAME)

    def test_get_module_logger(self):
        module_logger = get_logger('a.module')
        self.assertEqual(module_logger.name, 'cli.a.module')


if __name__ == '__main__':
    unittest.main()
