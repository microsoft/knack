# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock
import unittest

from knack.log import CLILogging, get_logger, CLI_LOGGER_NAME

class TestLogging(unittest.TestCase):

    def setUp(self):
        mock_ctx = mock.MagicMock()
        self.cli_logging = CLILogging('clitest', ctx=mock_ctx)

    # When running verbose level tests, we check that argv is empty
    # as we expect _determine_verbose_level to remove consumed arguments.

    def test_determine_verbose_level_default(self):
        argv = []
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_verbose(self):
        argv = ['--verbose']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_debug(self):
        argv = ['--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_v_v_v_default(self):
        argv = ['--verbose', '--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_other_args_verbose(self):
        argv = ['account', '--verbose']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_determine_verbose_level_other_args_debug(self):
        argv = ['account', '--debug']
        actual_level = self.cli_logging.determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_get_cli_logger(self):
        logger = get_logger()
        self.assertEqual(logger.name, CLI_LOGGER_NAME)

    def test_get_module_logger(self):
        module_logger = get_logger('my.cli.module')
        self.assertEqual(module_logger.name, 'my.cli.module')


if __name__ == '__main__':
    unittest.main()
