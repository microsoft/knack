# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from knack.events import EVENT_PARSER_GLOBAL_CREATE
from knack.query import CLIQuery
from tests.util import MockContext


class TestQueryEventHandling(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()
        self.cli_query = CLIQuery(cli_ctx=self.mock_ctx)

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            CLIQuery(cli_ctx=object())

    def test_query_argument_registrations(self):
        parser_arg_group_mock = mock.MagicMock()
        self.mock_ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=parser_arg_group_mock)
        parser_arg_group_mock.add_argument.assert_any_call('--query',
                                                           metavar=mock.ANY,
                                                           dest=mock.ANY,
                                                           help=mock.ANY,
                                                           type=mock.ANY)


class TestQuery(unittest.TestCase):
    '''Tests for the values that can be passed to the --query parameter.
    These tests ensure that we are handling invalid queries correctly and raising appropriate errors
    that argparse can then handle.
    (We are not testing JMESPath itself here)
    '''

    def test_query_valid_1(self):  # pylint: disable=no-self-use
        query = 'length(@)'
        # Should not raise any exception as it is valid
        CLIQuery.jmespath_type(query)

    def test_query_valid_2(self):  # pylint: disable=no-self-use
        query = "[?propertyX.propertyY.propertyZ=='AValue'].[col1,col2]"
        # Should not raise any exception as it is valid
        CLIQuery.jmespath_type(query)

    def test_query_empty(self):
        query = ''
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

    def test_query_unbalanced(self):
        query = 'length(@'
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

    def test_query_invalid_1(self):
        query = '[?asdf=asdf]'
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

    def test_query_invalid_2(self):
        query = '[?name=My Value]'
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

    def test_query_invalid_3(self):
        query = "[].location='westus'"
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

    def test_query_invalid_4(self):
        query = "length([?contains('id', 'Publishers'])"
        with self.assertRaises(ValueError):
            CLIQuery.jmespath_type(query)

if __name__ == '__main__':
    unittest.main()
