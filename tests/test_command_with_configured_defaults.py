# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import os
import logging
import unittest
try:
    import mock
except ImportError:
    from unittest import mock
from six import StringIO
import sys

from knack.arguments import ArgumentsContext
from knack.commands import CLICommandsLoader, CLICommand, CommandGroup
from knack.config import CLIConfig
from tests.util import DummyCLI, redirect_io


# a dummy callback for arg-parse
def load_params(_):
    pass


def list_foo(my_param):
    print(str(my_param), end='')


class TestCommandWithConfiguredDefaults(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def _set_up_command_table(self, required):

        class TestCommandsLoader(CLICommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with CommandGroup(self, 'foo', '{}#{{}}'.format(__name__)) as g:
                    g.command('list', 'list_foo')
                return self.command_table

            def load_arguments(self, command):
                with ArgumentsContext(self, 'foo') as c:
                    c.argument('my_param', options_list='--my-param',
                               configured_default='param', required=required)
                super(TestCommandsLoader, self).load_arguments(command)
        self.cli_ctx = DummyCLI(commands_loader_cls=TestCommandsLoader)

    @mock.patch.dict(os.environ, {'CLI_DEFAULTS_PARAM': 'myVal'})
    @redirect_io
    def test_apply_configured_defaults_on_required_arg(self):
        self._set_up_command_table(required=True)
        self.cli_ctx.invoke('foo list'.split())
        actual = self.io.getvalue()
        expected = 'myVal'
        self.assertEqual(expected, actual)

    @redirect_io
    def test_no_configured_default_on_required_arg(self):
        self._set_up_command_table(required=True)
        with self.assertRaises(SystemExit):
            self.cli_ctx.invoke('foo list'.split())
        actual = self.io.getvalue()
        expected = 'required: --my-param'
        if sys.version_info[0] == 2:
            expected = 'argument --my-param is required'
        self.assertEqual(expected in actual, True)

    @mock.patch.dict(os.environ, {'CLI_DEFAULTS_PARAM': 'myVal'})
    @redirect_io
    def test_apply_configured_defaults_on_optional_arg(self):
        self._set_up_command_table(required=False)
        self.cli_ctx.invoke('foo list'.split())
        actual = self.io.getvalue()
        expected = 'myVal'
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
