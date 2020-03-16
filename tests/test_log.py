# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
try:
    import mock
except ImportError:
    from unittest import mock
import logging
import colorama

from knack.events import EVENT_PARSER_GLOBAL_CREATE, EVENT_INVOKER_PRE_CMD_TBL_CREATE
from knack.log import CLILogging, get_logger, CLI_LOGGER_NAME, _CustomStreamHandler
from knack.util import CLIError
from tests.util import MockContext


class TestLoggingEventHandling(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MockContext()
        self.cli_logging = CLILogging('clitest', cli_ctx=self.mock_ctx)

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            CLILogging('myclitest', cli_ctx=object())

    def test_logging_argument_registrations(self):
        parser_arg_group_mock = mock.MagicMock()
        self.mock_ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=parser_arg_group_mock)
        parser_arg_group_mock.add_argument.assert_any_call(CLILogging.VERBOSE_FLAG, dest=mock.ANY, action=mock.ANY,
                                                           help=mock.ANY)
        parser_arg_group_mock.add_argument.assert_any_call(CLILogging.DEBUG_FLAG, dest=mock.ANY, action=mock.ANY,
                                                           help=mock.ANY)


class TestLoggingLevel(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MockContext()
        self.cli_logging = CLILogging('clitest', cli_ctx=self.mock_ctx)

    def test_determine_log_level_default(self):
        argv = []
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 2
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_verbose(self):
        argv = ['--verbose']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 3
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_debug(self):
        argv = ['--debug']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 4
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_v_v_v_default(self):
        argv = ['--verbose', '--debug']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 4
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_only_show_errors(self):
        argv = ['--only-show-errors']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 1
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_only_show_errors_config(self):
        argv = []
        self.mock_ctx.only_show_errors = True
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        self.mock_ctx.only_show_errors = False

    def test_determine_log_level_all_flags(self):
        argv = ['--verbose', '--debug', '--only-show-errors']
        with self.assertRaises(CLIError):
            self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access

    def test_determine_log_level_other_args_verbose(self):
        argv = ['account', '--verbose']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 3
        self.assertEqual(actual_level, expected_level)

    def test_determine_log_level_other_args_debug(self):
        argv = ['account', '--debug']
        actual_level = self.cli_logging._determine_log_level(argv)  # pylint: disable=protected-access
        expected_level = 4
        self.assertEqual(actual_level, expected_level)

    def test_get_cli_logger(self):
        logger = get_logger()
        self.assertEqual(logger.name, CLI_LOGGER_NAME)

    def test_get_module_logger(self):
        module_logger = get_logger('a.module')
        self.assertEqual(module_logger.name, 'cli.a.module')


class TestCustomStreamHandler(unittest.TestCase):
    expectation = {logging.CRITICAL: colorama.Fore.LIGHTRED_EX, logging.ERROR: colorama.Fore.LIGHTRED_EX,
                   logging.WARNING: colorama.Fore.YELLOW, logging.INFO: colorama.Fore.GREEN,
                   logging.DEBUG: colorama.Fore.CYAN}

    def test_get_color_wrapper(self):
        for level, prefix in self.expectation.items():
            message = _CustomStreamHandler.get_color_wrapper(level)('test')
            self.assertTrue(message.startswith(prefix))
            self.assertTrue(message.endswith(colorama.Style.RESET_ALL))


if __name__ == '__main__':
    unittest.main()
