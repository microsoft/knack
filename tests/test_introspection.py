# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from knack.introspection import extract_full_summary_from_signature, option_descriptions, extract_args_from_signature


def op1(self, arg1, arg2=False, arg3='mydefaultvalue', **kwargs):  # pylint: disable=unused-argument
    """ This is the command description.
    :param arg3: This is an arg for a test.
    """
    pass


def op2(self, **kwargs):  # pylint: disable=unused-argument
    # This operation has no summary
    pass


class TestExtractArgs(unittest.TestCase):

    def test_extract_args_simple(self):
        arguments = dict(extract_args_from_signature(op1))

        self.assertEqual(len(arguments), 3)
        self.assertNotIn('self', arguments)
        self.assertNotIn('kwargs', arguments)

        self.assertIn('arg1', arguments)
        self.assertListEqual(arguments['arg1'].options_list, ['--arg1'])
        self.assertTrue(arguments['arg1'].options['required'])

        self.assertIn('arg2', arguments)
        self.assertListEqual(arguments['arg2'].options_list, ['--arg2'])
        self.assertFalse(arguments['arg2'].options['required'])
        self.assertEqual(arguments['arg2'].options['action'], 'store_true')

        self.assertIn('arg3', arguments)
        self.assertListEqual(arguments['arg3'].options_list, ['--arg3'])
        self.assertFalse(arguments['arg3'].options['required'])
        self.assertEqual(arguments['arg3'].options['default'], 'mydefaultvalue')
        self.assertEqual(arguments['arg3'].options['help'], 'This is an arg for a test.')

    def test_extract_args_custom_exclude(self):
        excluded_params = ['self', 'kwargs', 'arg2', 'arg3']
        arguments = dict(extract_args_from_signature(op1, excluded_params=excluded_params))
        self.assertEqual(len(arguments), 1)
        for param in excluded_params:
            self.assertNotIn(param, arguments)


class TestOptionDescriptions(unittest.TestCase):

    def test_option_desc_simple(self):
        option_descs = option_descriptions(op1)
        self.assertIn('arg3', option_descs)
        self.assertEqual(option_descs['arg3'], 'This is an arg for a test.')


class TestExtractSummary(unittest.TestCase):

    def test_extract_summary(self):
        summary = extract_full_summary_from_signature(op1)
        self.assertEqual(summary, 'This is the command description.')

    def test_extract_summary_no_summary(self):
        summary = extract_full_summary_from_signature(op2)
        self.assertEqual(summary, '')


if __name__ == '__main__':
    unittest.main()
