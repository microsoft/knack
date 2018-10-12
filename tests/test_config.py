# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import stat
import unittest
import tempfile
import mock
from six.moves import configparser

from knack.config import CLIConfig, get_config_parser


class TestCLIConfig(unittest.TestCase):

    def setUp(self):
        self.cli_config = CLIConfig(config_dir=tempfile.mkdtemp())

    def test_has_option(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        self.assertTrue(self.cli_config.has_option(section, option))

    def test_has_option_env(self):
        with mock.patch.dict('os.environ', {self.cli_config.env_var_name('MySection', 'myoption'): 'myvalue'}):
            section = 'MySection'
            option = 'myoption'
            self.assertTrue(self.cli_config.has_option(section, option))

    def test_has_option_env_no(self):
        section = 'MySection'
        option = 'myoption'
        self.assertFalse(self.cli_config.has_option(section, option))

    def test_get(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        self.assertEqual(self.cli_config.get(section, option), value)

    def test_get_env(self):
        with mock.patch.dict('os.environ', {self.cli_config.env_var_name('MySection', 'myoption'): 'myvalue'}):
            section = 'MySection'
            option = 'myoption'
            value = 'myvalue'
            self.assertEqual(self.cli_config.get(section, option), value)

    def test_get_not_found_section(self):
        section = 'MySection'
        option = 'myoption'
        with self.assertRaises(configparser.NoSectionError):
            self.cli_config.get(section, option)

    def test_get_not_found_option(self):
        section = 'MySection'
        option = 'myoption'
        self.cli_config.config_parser.add_section(section)
        with self.assertRaises(configparser.NoOptionError):
            self.cli_config.get(section, option)

    def test_get_fallback(self):
        section = 'MySection'
        option = 'myoption'
        self.assertEqual(self.cli_config.get(section, option, fallback='fallback'), 'fallback')

    def test_getint(self):
        section = 'MySection'
        option = 'myoption'
        value = '123'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        self.assertEqual(self.cli_config.getint(section, option), int(value))

    def test_getint_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_an_int'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getint(section, option)

    def test_getfloat(self):
        section = 'MySection'
        option = 'myoption'
        value = '123.456'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        self.assertEqual(self.cli_config.getfloat(section, option), float(value))

    def test_getfloat_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_float'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        with self.assertRaises(ValueError):
            self.cli_config.getfloat(section, option)

    def test_getboolean(self):
        section = 'MySection'
        option = 'myoption'
        value = 'true'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
        self.assertTrue(self.cli_config.getboolean(section, option))

    def test_getboolean_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_boolean'
        self.cli_config.config_parser.add_section(section)
        self.cli_config.config_parser.set(section, option, value)
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
        config = get_config_parser()
        config.read(self.cli_config.config_path)
        self.assertEqual(config.get('test_section', 'test_option'), 'a_value')
        self.assertEqual(config.get('test_section', 'test_option_another'), 'another_value')

    def test_set_config_value_not_string(self):
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


if __name__ == '__main__':
    unittest.main()
