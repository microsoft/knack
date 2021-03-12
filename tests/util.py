# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    import mock
except ImportError:
    from unittest import mock
import logging
import os
import re
import shutil
import sys
import tempfile
from io import StringIO

from knack.cli import CLI, CLICommandsLoader, CommandInvoker
from knack.log import CLI_LOGGER_NAME

TEMP_FOLDER_NAME = "knack_temp"


def redirect_io(func):

    original_stderr = sys.stderr
    original_stdout = sys.stdout

    def wrapper(self):
        # Ensure a clean startup - no log handlers
        root_logger = logging.getLogger()
        cli_logger = logging.getLogger(CLI_LOGGER_NAME)
        root_logger.handlers.clear()
        cli_logger.handlers.clear()

        sys.stdout = sys.stderr = self.io = StringIO()
        func(self)
        self.io.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        # Remove the handlers added by CLI, so that the next invoke call init them again with the new stderr
        # Otherwise, the handlers will write to a closed StringIO from a preview test
        root_logger.handlers.clear()
        cli_logger.handlers.clear()
    return wrapper


def disable_color(func):
    def wrapper(self):
        self.cli_ctx.enable_color = False
        func(self)
        self.cli_ctx.enable_color = True
    return wrapper


def _remove_control_sequence(string):
    return re.sub(r'\x1b[^m]+m', '', string)


def _remove_whitespace(string):
    return re.sub(r'\s', '', string)


def assert_in_multi_line(sub_string, string):
    # assert sub_string is in string, with all whitespaces, line breaks and control sequences ignored
    assert _remove_whitespace(sub_string) in _remove_control_sequence(_remove_whitespace(string))


class MockContext(CLI):

    def __init__(self):
        super().__init__(config_dir=new_temp_folder())
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
        super().__init__(**kwargs)
        # Force to enable color
        self.enable_color = True


def new_temp_folder():
    temp_dir = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)
    return temp_dir
