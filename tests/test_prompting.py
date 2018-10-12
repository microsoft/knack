# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
import mock
from six import StringIO

from knack.prompting import (verify_is_a_tty, NoTTYException, _INVALID_PASSWORD_MSG, prompt,
                             prompt_int, prompt_pass, prompt_y_n, prompt_t_f, prompt_choice_list)


@unittest.skipIf(sys.version_info[0] == 2, "Can't modify isatty in Python 2 as it's read-only")
class TestPrompting(unittest.TestCase):

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_tty_no_exception(self, _):
        verify_is_a_tty()

    @mock.patch('sys.stdin.isatty', return_value=False)
    def test_no_tty_should_raise_exception(self, _):
        with self.assertRaises(NoTTYException):
            verify_is_a_tty()

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_msg(self, _):
        expected_result = 'This is my response.'
        with mock.patch('knack.prompting._input', return_value=expected_result):
            actual_result = prompt('Please enter some text: ')
            self.assertEqual(expected_result, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_msg_empty_response(self, _):
        expected_result = ''
        with mock.patch('knack.prompting._input', return_value=expected_result):
            actual_result = prompt('Please enter some text: ')
            self.assertEqual(expected_result, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_msg_question_no_help_string(self, _):
        expected_result = '?'
        with mock.patch('knack.prompting._input', return_value='?'):
            actual_result = prompt('Please enter some text: ')
            self.assertEqual(expected_result, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_msg_question_with_help_string(self, _):
        expected_result = 'My response'
        with mock.patch('knack.prompting._input', side_effect=['?', expected_result]):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt('Please enter some text: ', help_string='Anything you want!')
                self.assertEqual(expected_result, actual_result)
                self.assertIn('Anything you want!', mock_stdout.getvalue())

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_int(self, _):
        my_response = '42'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_int('Please enter a number: ')
            self.assertEqual(int(my_response), actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_int_empty_response(self, _):
        my_response = ''
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('knack.prompting._input', side_effect=[my_response]):
                    prompt_int('Please enter some text: ')
            mock_log_warn.assert_called_once_with('%s is not a valid number', my_response)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_int_nan(self, _):
        my_response = 'This is clearly not a number.'
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('knack.prompting._input', side_effect=[my_response]):
                    prompt_int('Please enter some text: ')
            mock_log_warn.assert_called_once_with('%s is not a valid number', my_response)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_int_question_no_help_string(self, _):
        my_response = '?'
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('knack.prompting._input', side_effect=['?']):
                    prompt_int('Please enter a number: ')
            mock_log_warn.assert_called_once_with('%s is not a valid number', my_response)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_int_question_with_help_string(self, _):
        my_response = '42'
        with mock.patch('knack.prompting._input', side_effect=['?', my_response]):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt_int('Please enter a number: ', help_string='Anything you want!')
                self.assertEqual(int(my_response), actual_result)
                self.assertIn('Anything you want!', mock_stdout.getvalue())

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass(self, _):
        my_password = '7ndBkS3zKQazD5N3zzstubZq'
        with mock.patch('getpass.getpass', return_value=my_password):
            actual_result = prompt_pass()
            self.assertEqual(my_password, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_empty_response(self, _):
        my_password = ''
        with mock.patch('getpass.getpass', return_value=my_password):
            actual_result = prompt_pass()
            self.assertEqual(my_password, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_custom_msg(self, _):
        my_password = '7ndBkS3zKQazD5N3zzstubZq'
        with mock.patch('getpass.getpass', return_value=my_password):
            actual_result = prompt_pass(msg='A Custom password message: ')
            self.assertEqual(my_password, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_question_no_help_string(self, _):
        expected_result = '?'
        with mock.patch('getpass.getpass', return_value='?'):
            actual_result = prompt_pass()
            self.assertEqual(expected_result, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_question_with_help_string(self, _):
        my_password = '7ndBkS3zKQazD5N3zzstubZq'
        with mock.patch('getpass.getpass', side_effect=['?', my_password]):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt_pass(help_string='Anything you want!')
                self.assertEqual(my_password, actual_result)
                self.assertIn('Anything you want!', mock_stdout.getvalue())

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_confirm_valid(self, _):
        my_password = '7ndBkS3zKQazD5N3zzstubZq'
        with mock.patch('getpass.getpass', side_effect=[my_password, my_password]):
            actual_result = prompt_pass(confirm=True)
            self.assertEqual(my_password, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_confirm_invalid(self, _):
        my_password1 = '7ndBkS3zKQazD5N3zzstubZq'
        my_password2 = 'LTQ9haNMCSGp8p2uQHw2K9xf'
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('getpass.getpass', side_effect=[my_password1, my_password2]):
                    prompt_pass(confirm=True)
            mock_log_warn.assert_called_once_with(_INVALID_PASSWORD_MSG)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_pass_confirm_invalid_then_valid(self, _):
        my_password1 = '7ndBkS3zKQazD5N3zzstubZq'
        my_password2 = 'LTQ9haNMCSGp8p2uQHw2K9xf'
        with mock.patch('getpass.getpass', side_effect=[my_password1, my_password2, my_password2, my_password2]):
            with mock.patch('logging.Logger.warning') as mock_log_warn:
                actual_result = prompt_pass(confirm=True)
                mock_log_warn.assert_called_once_with(_INVALID_PASSWORD_MSG)
                self.assertEqual(my_password2, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_yes(self, _):
        my_response = 'y'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_y_n('Do you accept?')
            self.assertTrue(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_no(self, _):
        my_response = 'n'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_y_n('Do you accept?')
            self.assertFalse(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_yes_caps(self, _):
        my_response = 'Y'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_y_n('Do you accept?')
            self.assertTrue(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_no_caps(self, _):
        my_response = 'N'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_y_n('Do you accept?')
            self.assertFalse(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_empty_response(self, _):
        with self.assertRaises(StopIteration):
            with mock.patch('knack.prompting._input', side_effect=['']):
                prompt_y_n('Do you accept?')

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_question_no_help_string(self, _):
        with self.assertRaises(StopIteration):
            with mock.patch('knack.prompting._input', side_effect=['?']):
                prompt_y_n('Do you accept?')

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_question_with_help_string(self, _):
        with mock.patch('knack.prompting._input', side_effect=['?', 'y']):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt_y_n('Do you accept?', help_string='y to accept conditions; no otherwise')
                self.assertTrue(actual_result)
                self.assertIn('y to accept conditions; no otherwise', mock_stdout.getvalue())

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_y_n_default(self, _):
        with mock.patch('knack.prompting._input', return_value=''):
            actual_result = prompt_y_n('Do you accept?', default='y')
            self.assertTrue(actual_result)

# HERE
    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_yes(self, _):
        my_response = 't'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_t_f('Do you accept?')
            self.assertTrue(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_no(self, _):
        my_response = 'f'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_t_f('Do you accept?')
            self.assertFalse(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_yes_caps(self, _):
        my_response = 'T'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_t_f('Do you accept?')
            self.assertTrue(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_no_caps(self, _):
        my_response = 'F'
        with mock.patch('knack.prompting._input', return_value=my_response):
            actual_result = prompt_t_f('Do you accept?')
            self.assertFalse(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_empty_response(self, _):
        with self.assertRaises(StopIteration):
            with mock.patch('knack.prompting._input', side_effect=['']):
                prompt_t_f('Do you accept?')

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_question_no_help_string(self, _):
        with self.assertRaises(StopIteration):
            with mock.patch('knack.prompting._input', side_effect=['?']):
                prompt_t_f('Do you accept?')

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_question_with_help_string(self, _):
        with mock.patch('knack.prompting._input', side_effect=['?', 't']):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt_t_f('Do you accept?', help_string='t to accept conditions; no otherwise')
                self.assertTrue(actual_result)
                self.assertIn('t to accept conditions; no otherwise', mock_stdout.getvalue())

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_t_f_default(self, _):
        with mock.patch('knack.prompting._input', return_value=''):
            actual_result = prompt_t_f('Do you accept?', default='t')
            self.assertTrue(actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_choice_list(self, _):
        a_list = ['red', 'blue', 'yellow', 'green']
        with mock.patch('knack.prompting._input', return_value='3'):
            actual_result = prompt_choice_list('What is your favourite color?', a_list)
            self.assertEqual(2, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_choice_list_with_name_desc(self, _):
        a_list = [{'name': 'red', 'desc': ' A desc.'},
                  {'name': 'blue', 'desc': ' A desc.'},
                  {'name': 'yellow', 'desc': ' A desc.'},
                  {'name': 'green', 'desc': ' A desc.'}]
        with mock.patch('knack.prompting._input', return_value='2'):
            actual_result = prompt_choice_list('What is your favourite color?', a_list)
            self.assertEqual(1, actual_result)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_choice_list_invalid_choice(self, _):
        a_list = ['red', 'blue', 'yellow', 'green']
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('knack.prompting._input', side_effect=['5']):
                    prompt_choice_list('What is your favourite color?', a_list)
            mock_log_warn.assert_called_once_with('Valid values are %s', mock.ANY)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_choice_list_question_no_help_string(self, _):
        a_list = ['red', 'blue', 'yellow', 'green']
        with mock.patch('logging.Logger.warning') as mock_log_warn:
            with self.assertRaises(StopIteration):
                with mock.patch('knack.prompting._input', side_effect=['?']):
                    prompt_choice_list('What is your favourite color?', a_list)
            mock_log_warn.assert_called_once_with('Valid values are %s', mock.ANY)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_choice_list_question_with_help_string(self, _):
        a_list = ['red', 'blue', 'yellow', 'green']
        with mock.patch('knack.prompting._input', side_effect=['?', '1']):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                actual_result = prompt_choice_list('What is your favourite color?',
                                                   a_list,
                                                   help_string='Your real favourite.')
                self.assertEqual(0, actual_result)
            self.assertIn('Your real favourite.', mock_stdout.getvalue())



if __name__ == '__main__':
    unittest.main()
