# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import stat
import unittest
import tempfile
try:
    import mock
except ImportError:
    from unittest import mock
from six.moves import configparser

from knack.config import CLIConfig, get_config_parser


class TestCLIConfig(unittest.TestCase):

    def setUp(self):
        self.cli_config = CLIConfig(config_dir=tempfile.mkdtemp())

    def test_has_option(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.cli_config.set_value(section, option, value)
        self.assertTrue(self.cli_config.has_option(section, option))
        self.cli_config.set_to_use_local_config(True)
        self.assertTrue(self.cli_config.has_option(section, option))

    def test_has_option_env(self):
        with mock.patch.dict('os.environ', {self.cli_config.env_var_name('MySection', 'myoption'): 'myvalue'}):
            section = 'MySection'
            option = 'myoption'
            self.assertTrue(self.cli_config.has_option(section, option))
            self.cli_config.set_to_use_local_config(True)
            self.assertTrue(self.cli_config.has_option(section, option))

    def test_has_option_env_no(self):
        section = 'MySection'
        option = 'myoption'
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_to_use_local_config(True)
        self.assertFalse(self.cli_config.has_option(section, option))

    def test_options(self):
        section = 'MySection'
        option = 'myoption'
        option_other = 'option'
        option_local = 'myoptionlocal'
        option_other_local = 'optionlocal'
        value = 'myvalue'
        self.cli_config.set_value(section, option, value)
        self.cli_config.set_value(section, option_other, value)
        self.assertEqual(len(self.cli_config.options(section)), 2)
        self.assertIn(option, self.cli_config.options(section))
        self.assertIn(option_other, self.cli_config.options(section))
        self.cli_config.set_to_use_local_config(True)
        self.assertEqual(len(self.cli_config.options(section)), 2)
        self.assertIn(option, self.cli_config.options(section))
        self.assertIn(option_other, self.cli_config.options(section))
        self.cli_config.set_value(section, option_local, value)
        self.cli_config.set_value(section, option_other_local, value)
        self.assertEqual(len(self.cli_config.options(section)), 4)
        self.assertIn(option, self.cli_config.options(section))
        self.assertIn(option_other, self.cli_config.options(section))
        self.assertIn(option_local, self.cli_config.options(section))
        self.assertIn(option_other_local, self.cli_config.options(section))

    def test_get(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.get(section, option), value)
        self.cli_config.set_to_use_local_config(True)
        self.assertEqual(self.cli_config.get(section, option), value)

    def test_get_env(self):
        with mock.patch.dict('os.environ', {self.cli_config.env_var_name('MySection', 'myoption'): 'myvalue'}):
            section = 'MySection'
            option = 'myoption'
            value = 'myvalue'
            self.assertEqual(self.cli_config.get(section, option), value)
            self.cli_config.set_to_use_local_config(True)
            self.assertEqual(self.cli_config.get(section, option), value)

    def test_get_not_found_section(self):
        section = 'MySection'
        option = 'myoption'
        with self.assertRaises(configparser.NoSectionError):
            self.cli_config.get(section, option)
        self.cli_config.set_to_use_local_config(True)
        with self.assertRaises(configparser.NoSectionError):
            self.cli_config.get(section, option)

    def test_get_not_found_option(self):
        section = 'MySection'
        option = 'myoption'
        option_other = 'option'
        value = 'myvalue'
        self.cli_config.set_value(section, option_other, value)
        with self.assertRaises(configparser.NoOptionError):
            self.cli_config.get(section, option)
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option_other, value)
        with self.assertRaises(configparser.NoOptionError):
            self.cli_config.get(section, option)

    def test_get_fallback(self):
        section = 'MySection'
        option = 'myoption'
        self.assertEqual(self.cli_config.get(section, option, fallback='fallback'), 'fallback')
        self.cli_config.set_to_use_local_config(True)
        self.assertEqual(self.cli_config.get(section, option, fallback='fallback'), 'fallback')

    def test_getint(self):
        section = 'MySection'
        option = 'myoption'
        value = '123'
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.getint(section, option), int(value))
        self.cli_config.set_to_use_local_config(True)
        self.assertEqual(self.cli_config.getint(section, option), int(value))

    def test_getint_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_an_int'
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getint(section, option)
        self.cli_config.set_to_use_local_config(True)
        with self.assertRaises(ValueError):
            self.cli_config.getint(section, option)
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getint(section, option)

    def test_getfloat(self):
        section = 'MySection'
        option = 'myoption'
        value = '123.456'
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.getfloat(section, option), float(value))
        self.cli_config.set_to_use_local_config(True)
        self.assertEqual(self.cli_config.getfloat(section, option), float(value))

    def test_getfloat_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_float'
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getfloat(section, option)
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getfloat(section, option)

    def test_getboolean(self):
        section = 'MySection'
        option = 'myoption'
        value = 'true'
        self.cli_config.set_value(section, option, value)
        self.assertTrue(self.cli_config.getboolean(section, option))
        self.cli_config.set_to_use_local_config(True)
        self.assertTrue(self.cli_config.getboolean(section, option))

    def test_getboolean_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_boolean'
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getboolean(section, option)
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getboolean(section, option)

    def test_set_config_value(self):
        self.cli_config.set_value('test_section', 'test_option', 'a_value')
        config = get_config_parser()
        config.read(self.cli_config.config_path)
        self.assertEqual(config.get('test_section', 'test_option'), 'a_value')

    def test_set_config_value_duplicate_section_ok(self):
        self.cli_config.set_value('test_section', 'test_option', 'a_value')
        self.cli_config.set_value('test_section', 'test_option_another', 'another_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option'), 'a_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option_another'), 'another_value')
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value('test_section', 'test_option', 'a_value')
        self.cli_config.set_value('test_section', 'test_option_another', 'another_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option'), 'a_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option_another'), 'another_value')

    def test_set_config_value_not_string(self):
        with self.assertRaises(TypeError):
            self.cli_config.set_value('test_section', 'test_option', False)
        self.cli_config.set_to_use_local_config(True)
        with self.assertRaises(TypeError):
            self.cli_config.set_value('test_section', 'test_option', False)

    def test_set_config_value_file_permissions(self):
        self.cli_config.set_value('test_section', 'test_option', 'a_value')
        file_mode = os.stat(self.cli_config.config_path).st_mode
        self.assertTrue(bool(file_mode & stat.S_IRUSR))
        self.assertTrue(bool(file_mode & stat.S_IWUSR))
        self.assertFalse(bool(file_mode & stat.S_IXUSR))
        self.assertFalse(bool(file_mode & stat.S_IRGRP))
        self.assertFalse(bool(file_mode & stat.S_IWGRP))
        self.assertFalse(bool(file_mode & stat.S_IXGRP))
        self.assertFalse(bool(file_mode & stat.S_IROTH))
        self.assertFalse(bool(file_mode & stat.S_IWOTH))
        self.assertFalse(bool(file_mode & stat.S_IXOTH))

    def test_has_option_local(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, value)
        self.assertTrue(self.cli_config.has_option(section, option))
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_value(section, option, value)
        self.assertTrue(self.cli_config.has_option(section, option))

    def test_options_local(self):
        section = 'MySection'
        option = 'myoption'
        option_other = 'option'
        value = 'myvalue'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, value)
        self.cli_config.set_value(section, option_other, value)
        self.assertEqual(len(self.cli_config.options(section)), 2)
        self.assertIn(option, self.cli_config.options(section))
        self.assertIn(option_other, self.cli_config.options(section))
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertEqual(len(self.cli_config.options(section)), 0)

    def test_get_local(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        local_value = 'localvalue'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, local_value)
        self.assertEqual(self.cli_config.get(section, option), local_value)
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.get(section, option), value)

    def test_getint_local(self):
        section = 'MySection'
        option = 'myoption'
        value = '123'
        local_value = '1234'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, local_value)
        self.assertEqual(self.cli_config.getint(section, option), int(local_value))
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.getint(section, option), int(value))

    def test_getfloat_local(self):
        section = 'MySection'
        option = 'myoption'
        value = '123.456'
        local_value = '1234.56'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, local_value)
        self.assertEqual(self.cli_config.getfloat(section, option), float(local_value))
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_value(section, option, value)
        self.assertEqual(self.cli_config.getfloat(section, option), float(value))

    def test_getboolean_local(self):
        section = 'MySection'
        option = 'myoption'
        local_value = 'true'
        value = 'false'
        # check local config
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value(section, option, local_value)
        self.assertTrue(self.cli_config.getboolean(section, option))
        # check default config
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option(section, option))
        self.cli_config.set_value(section, option, value)
        self.assertFalse(self.cli_config.getboolean(section, option))

    def test_set_config_value_duplicate_section_ok_local(self):
        self.cli_config.set_to_use_local_config(True)
        self.cli_config.set_value('test_section', 'test_option', 'a_value')
        self.cli_config.set_value('test_section', 'test_option_another', 'another_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option'), 'a_value')
        self.assertEqual(self.cli_config.get('test_section', 'test_option_another'), 'another_value')
        self.cli_config.set_to_use_local_config(False)
        self.assertFalse(self.cli_config.has_option('test_section', 'test_option'))
        self.assertFalse(self.cli_config.has_option('test_section', 'test_option_another'))


if __name__ == '__main__':
    unittest.main()
