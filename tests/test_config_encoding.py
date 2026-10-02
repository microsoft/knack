# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser
import os
import tempfile
import unittest
from unittest import mock

from knack.config import CLIConfig


class TestConfigEncoding(unittest.TestCase):

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config = CLIConfig(config_dir=directory.name)

        def legacy_open(filename, mode='r', *, encoding=None):
            # Emulate a non-UTF-8 locale even when the test host uses UTF-8.
            if encoding in (None, 'locale'):
                encoding = 'cp1252'
            return open(filename, mode, encoding=encoding)

        patcher = mock.patch('configparser.open', side_effect=legacy_open, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_set_value_preserves_non_ascii_in_memory(self):
        value = 'Montr\u00e9al'
        self.config.set_value('defaults', 'location', value)
        self.assertEqual(self.config.get('defaults', 'location'), value)

    def test_update_preserves_existing_utf8_values_on_disk(self):
        value = 'Montr\u00e9al'
        with open(self.config.config_path, 'w', encoding='utf-8') as config_file:
            config_file.write('[defaults]\nlocation = {}\n'.format(value))

        self.config.set_value('defaults', 'output', 'json')

        saved = configparser.ConfigParser()
        saved.read(self.config.config_path, encoding='utf-8')
        self.assertEqual(saved.get('defaults', 'location'), value)
        self.assertEqual(saved.get('defaults', 'output'), 'json')
        restored = CLIConfig(config_dir=os.path.dirname(self.config.config_path))
        self.assertEqual(restored.get('defaults', 'location'), value)


if __name__ == '__main__':
    unittest.main()
