# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from knack.completion import CLICompletion, CaseInsensitiveChoicesCompleter, ARGCOMPLETE_ENV_NAME
from tests.util import MockContext


class TestCompletion(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            CLICompletion(cli_ctx=object())

    @mock.patch.dict(os.environ, {})
    def test_completer_not_active(self):
        CLICompletion(cli_ctx=self.mock_ctx)
        self.assertFalse(self.mock_ctx.data['completer_active'])

    @mock.patch.dict(os.environ, {ARGCOMPLETE_ENV_NAME: '1'})
    def test_completer_active(self):
        CLICompletion(cli_ctx=self.mock_ctx)
        self.assertTrue(self.mock_ctx.data['completer_active'])

    def test_case_insensitive_choices_empty(self):
        choices = []
        prefix = ''
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        expected_result = []
        self.assertListEqual(actual_result, expected_result)

    def test_case_insensitive_choices_empty_with_prefix(self):
        choices = []
        prefix = 'abc'
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        expected_result = []
        self.assertListEqual(actual_result, expected_result)

    def test_case_insensitive_choices_list_same_case(self):
        choices = ['abc', 'xyz']
        prefix = ''
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        expected_result = ['abc', 'xyz']
        self.assertListEqual(actual_result, expected_result)

    def test_case_insensitive_choices_list_diff_case(self):
        choices = ['ABC', 'xyz']
        prefix = ''
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        expected_result = ['ABC', 'xyz']
        self.assertListEqual(actual_result, expected_result)

    def test_case_insensitive_choices_list_diff_case_with_prefix(self):
        choices = ['ABC', 'xyz']
        prefix = 'ab'
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        # Casing is returned the same as the original choice list
        expected_result = ['ABC']
        self.assertListEqual(actual_result, expected_result)

    def test_case_insensitive_choices_list_multi_case_with_prefix(self):
        choices = ['red', 'blue', 'YelLoW']
        prefix = 'y'
        actual_result = list(CaseInsensitiveChoicesCompleter(choices)(prefix))
        # Casing is returned the same as the original choice list
        expected_result = ['YelLoW']
        self.assertListEqual(actual_result, expected_result)


if __name__ == '__main__':
    unittest.main()
