#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock
from collections import OrderedDict
from io import StringIO

from knack.output import OutputProducer, format_json, format_json_color, format_yaml, format_yaml_color, \
    format_table, format_tsv
from knack.util import CommandResultItem, normalize_newlines
from tests.util import MockContext


class TestOutput(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MockContext()
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_cli_ctx_type_error(self):
        with self.assertRaises(TypeError):
            OutputProducer(cli_ctx=object())

    # JSON output tests

    def test_out_json_valid(self):
        """
        The JSON output when the input is a dict should be the dict serialized to JSON
        """
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'id': '0b1f6472'}),
                            formatter=format_json, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """{
  "active": true,
  "id": "0b1f6472"
}
"""))

    def test_out_json_from_ordered_dict(self):
        """
        The JSON output when the input is OrderedDict should be serialized to JSON
        """
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem(OrderedDict({'active': True, 'id': '0b1f6472'})),
                            formatter=format_json, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """{
  "active": true,
  "id": "0b1f6472"
}
"""))

    def test_out_json_byte(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': b'0b1f6472'}),
                            formatter=format_json, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """{
  "active": true,
  "contents": "0b1f6472"
}
"""))

    def test_out_json_byte_empty(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': b''}),
                            formatter=format_json, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """{
  "active": true,
  "contents": ""
}
"""))

    def test_out_json_non_ASCII(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': '生活很糟糕'}),
                            formatter=format_json, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """{
  "active": true,
  "contents": "生活很糟糕"
}
"""))

    # YAML output tests

    def test_out_yaml_valid(self):
        """
        Test Dict serialized to YAML
        """
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'id': '0b1f6472'}),
                            formatter=format_yaml, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """active: true
id: 0b1f6472
"""))

    def test_out_yaml_from_ordered_dict(self):
        """
        Test OrderedDict serialized to YAML
        """
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem(OrderedDict({'active': True, 'id': '0b1f6472'})),
                            formatter=format_yaml, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """active: true
id: 0b1f6472
"""))

    def test_out_yaml_byte(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': b'0b1f6472'}),
                            formatter=format_yaml, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """active: true
contents: !!binary |
  MGIxZjY0NzI=
"""))

    def test_out_yaml_byte_empty(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': b''}),
                            formatter=format_yaml, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """active: true
contents: !!binary ""
"""))

    def test_out_yaml_non_ASCII(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        output_producer.out(CommandResultItem({'active': True, 'contents': 'こんにちは'}),
                            formatter=format_yaml, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """active: true
contents: こんにちは
"""))

    # TABLE output tests

    def test_out_table(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = OrderedDict()
        obj['active'] = True
        obj['val'] = '0b1f6472'
        obj['lun'] = 0
        output_producer.out(CommandResultItem(obj), formatter=format_table, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Active    Lun    Val
--------  -----  --------
True      0      0b1f6472
"""))

    def test_out_table_list_of_lists(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = [['a', 'b'], ['c', 'd']]
        output_producer.out(CommandResultItem(obj), formatter=format_table, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Column1    Column2
---------  ---------
a          b
c          d
"""))

    def test_out_table_complex_obj(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = OrderedDict()
        obj['name'] = 'qwerty'
        obj['val'] = '0b1f6472qwerty'
        obj['sub'] = {'1'}
        result_item = CommandResultItem(obj)
        output_producer.out(result_item, formatter=format_table, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Name    Val
------  --------------
qwerty  0b1f6472qwerty
"""))

    def test_out_table_no_query_no_transformer_order(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = {'name': 'qwerty', 'val': '0b1f6472qwerty', 'active': True, 'sub': '0b1f6472'}
        result_item = CommandResultItem(obj, table_transformer=None, is_query_active=False)
        output_producer.out(result_item, formatter=format_table, out_file=self.io)
        # Should be alphabetical order as no table transformer and query is not active.
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Active    Name    Sub       Val
--------  ------  --------  --------------
True      qwerty  0b1f6472  0b1f6472qwerty
"""))

    def test_out_table_no_query_yes_transformer_order(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = {'name': 'qwerty', 'val': '0b1f6472qwerty', 'active': True, 'sub': '0b1f6472'}

        def transformer(r):
            return OrderedDict([('Name', r['name']), ('Val', r['val']),
                                ('Active', r['active']), ('Sub', r['sub'])])

        result_item = CommandResultItem(obj, table_transformer=transformer, is_query_active=False)
        output_producer.out(result_item, formatter=format_table, out_file=self.io)
        # Should be table transformer order
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Name    Val             Active    Sub
------  --------------  --------  --------
qwerty  0b1f6472qwerty  True      0b1f6472
"""))

    def test_out_table_no_query_yes_jmespath_table_transformer(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = {'name': 'qwerty', 'val': '0b1f6472qwerty', 'active': True, 'sub': '0b1f6472'}

        result_item = CommandResultItem(obj,
                                        table_transformer='{Name:name, Val:val, Active:active}',
                                        is_query_active=False)
        output_producer.out(result_item, formatter=format_table, out_file=self.io)
        # Should be table transformer order
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Name    Val             Active
------  --------------  --------
qwerty  0b1f6472qwerty  True
"""))

    def test_out_table_with_number(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)
        obj = OrderedDict()
        obj['Sku'] = '6.10'
        output_producer.out(CommandResultItem(obj), formatter=format_table, out_file=self.io)
        self.assertEqual(normalize_newlines(self.io.getvalue()), normalize_newlines(
            """Sku
-----
6.10
"""))

    # TSV output tests
    def test_output_format_dict(self):
        obj = {}
        obj['A'] = 1
        obj['B'] = 2
        result = format_tsv(CommandResultItem(obj))
        self.assertEqual(result, '1\t2\n')

    def test_output_format_dict_sort(self):
        obj = {}
        obj['B'] = 1
        obj['A'] = 2
        result = format_tsv(CommandResultItem(obj))
        self.assertEqual(result, '2\t1\n')

    def test_output_format_ordereddict_not_sorted(self):
        obj = OrderedDict()
        obj['B'] = 1
        obj['A'] = 2
        result = format_tsv(CommandResultItem(obj))
        self.assertEqual(result, '1\t2\n')

    def test_output_format_ordereddict_list_not_sorted(self):
        obj1 = OrderedDict()
        obj1['B'] = 1
        obj1['A'] = 2

        obj2 = OrderedDict()
        obj2['A'] = 3
        obj2['B'] = 4
        result = format_tsv(CommandResultItem([obj1, obj2]))
        self.assertEqual(result, '1\t2\n3\t4\n')

    def test_remove_color_no_tty(self):
        output_producer = OutputProducer(cli_ctx=self.mock_ctx)

        self.mock_ctx.enable_color = False
        formatter = output_producer.get_formatter('jsonc')
        self.assertEqual(formatter, format_json)
        formatter = output_producer.get_formatter('yamlc')
        self.assertEqual(formatter, format_yaml)

        self.mock_ctx.enable_color = True
        formatter = output_producer.get_formatter('jsonc')
        self.assertEqual(formatter, format_json_color)
        formatter = output_producer.get_formatter('yamlc')
        self.assertEqual(formatter, format_yaml_color)


if __name__ == '__main__':
    unittest.main()
