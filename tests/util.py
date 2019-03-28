# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock
import sys
import tempfile
from six import StringIO

from knack.cli import CLI, CLICommandsLoader, CommandInvoker

def redirect_io(func):

    original_stderr = sys.stderr
    original_stdout = sys.stdout

    def wrapper(self):
        sys.stdout = sys.stderr = self.io = StringIO()
        func(self)
        self.io.close()
        sys.stdout = original_stderr
        sys.stderr = original_stderr
    return wrapper


class MockContext(CLI):

    def __init__(self):
        super(MockContext, self).__init__(config_dir=tempfile.mkdtemp())
        loader = CLICommandsLoader(cli_ctx=self)
        invocation = mock.MagicMock(spec=CommandInvoker)
        invocation.data = {}
        setattr(self, 'commands_loader', loader)
        setattr(self, 'invocation', invocation)


class DummyCLI(CLI):

    def get_cli_version(self):
        return '0.1.0'

    def __init__(self, **kwargs):
        kwargs['config_dir'] = tempfile.mkdtemp()
        super(DummyCLI, self).__init__(**kwargs)
