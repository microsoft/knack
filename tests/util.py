# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    import mock
except ImportError:
    from unittest import mock
import sys
import tempfile
import shutil
import os
from six import StringIO
import logging
from knack.log import CLI_LOGGER_NAME

from knack.cli import CLI, CLICommandsLoader, CommandInvoker

TEMP_FOLDER_NAME = "knack_temp"


def redirect_io(func):

    original_stderr = sys.stderr
    original_stdout = sys.stdout

    def wrapper(self):
        sys.stdout = sys.stderr = self.io = StringIO()
        func(self)
        self.io.close()
        sys.stdout = original_stderr
        sys.stderr = original_stderr

        # Remove the handlers added by CLI, so that the next invoke call init them again with the new stderr
        # Otherwise, the handlers will write to a closed StringIO from a preview test
        root_logger = logging.getLogger()
        cli_logger = logging.getLogger(CLI_LOGGER_NAME)
        root_logger.handlers = root_logger.handlers[:-1]
        cli_logger.handlers = cli_logger.handlers[:-1]
    return wrapper


def disable_color(func):
    def wrapper(self):
        self.cli_ctx.enable_color = False
        func(self)
        self.cli_ctx.enable_color = True
    return wrapper


def remove_space(str):
    return str.replace(' ', '').replace('\n', '')


class MockContext(CLI):

    def __init__(self):
        super(MockContext, self).__init__(config_dir=new_temp_folder())
        loader = CLICommandsLoader(cli_ctx=self)
        invocation = mock.MagicMock(spec=CommandInvoker)
        invocation.data = {}
        setattr(self, 'commands_loader', loader)
        setattr(self, 'invocation', invocation)


class DummyCLI(CLI):

    def get_cli_version(self):
        return '0.1.0'

    def __init__(self, **kwargs):
        kwargs['config_dir'] = new_temp_folder()
        super(DummyCLI, self).__init__(**kwargs)


def new_temp_folder():
    temp_dir = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)
    return temp_dir
