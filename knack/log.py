# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import logging
from logging.handlers import RotatingFileHandler

import colorama

from .util import ensure_dir
from .events import EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_PARSER_GLOBAL_CREATE

CLI_LOGGER_NAME = 'cli'


def get_logger(module_name=None):
    if module_name:
        logger_name = '{}.'.format(CLI_LOGGER_NAME) + module_name
    else:
        logger_name = CLI_LOGGER_NAME
    return logging.getLogger(logger_name)


class _CustomStreamHandler(logging.StreamHandler):

    def _color_wrapper(color_marker):  # pylint: disable=no-self-argument
        def wrap_msg_with_color(msg):
            return color_marker + msg + colorama.Style.RESET_ALL
        return wrap_msg_with_color

    COLOR_MAP = {
        logging.CRITICAL: _color_wrapper(colorama.Fore.RED),
        logging.ERROR: _color_wrapper(colorama.Fore.RED),
        logging.WARNING: _color_wrapper(colorama.Fore.YELLOW),
        logging.INFO: _color_wrapper(colorama.Fore.GREEN),
        logging.DEBUG: _color_wrapper(colorama.Fore.CYAN)
    }

    def _should_enable_color(self):
        try:
            # Color if tty stream available
            if self.stream.isatty():
                return True
        except AttributeError:
            pass
        return False

    def __init__(self, log_level_config, log_format):
        logging.StreamHandler.__init__(self)
        self.setLevel(log_level_config)
        if platform.system() == 'Windows':
            self.stream = colorama.AnsiToWin32(self.stream).stream
        self.enable_color = self._should_enable_color()
        self.setFormatter(logging.Formatter(log_format[self.enable_color]))

    def format(self, record):
        msg = logging.StreamHandler.format(self, record)
        if self.enable_color:
            try:
                msg = _CustomStreamHandler.COLOR_MAP[record.levelno](msg)
            except KeyError:
                pass
        return msg


class CLILogging(object):

    DEBUG_FLAG = '--debug'
    VERBOSE_FLAG = '--verbose'

    @staticmethod
    def on_global_arguments(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        # The arguments for verbosity don't get parsed by argparse but we add it here for help.
        arg_group.add_argument(CLILogging.VERBOSE_FLAG, dest='_log_verbosity_verbose', action='store_true',
                               help='Increase logging verbosity. Use --debug for full debug logs.')
        arg_group.add_argument(CLILogging.DEBUG_FLAG, dest='_log_verbosity_debug', action='store_true',
                               help='Increase logging verbosity to show all debug logs.')

    @staticmethod
    def remove_logger_flags(_, **kwargs):
        args = kwargs.get('args')
        try:
            args.remove(CLILogging.VERBOSE_FLAG)
        except ValueError:
            pass
        try:
            args.remove(CLILogging.DEBUG_FLAG)
        except ValueError:
            pass

    def __init__(self, name, ctx=None):
        self.logfile_name = '{}.log'.format(name)
        self.file_log_enabled = CLILogging._is_file_log_enabled(ctx)
        self.log_dir = CLILogging._get_log_dir(ctx)
        self.console_log_configs = CLILogging._get_console_log_configs()
        self.console_log_format = CLILogging._get_console_log_format()
        self.ctx = ctx
        self.ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, CLILogging.on_global_arguments)
        self.ctx.register_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, CLILogging.remove_logger_flags)

    def configure(self, args):
        verbose_level = self._determine_verbose_level(args)
        log_level_config = self.console_log_configs[verbose_level]
        root_logger = logging.getLogger()
        cli_logger = logging.getLogger(CLI_LOGGER_NAME)
        # Set the levels of the loggers to lowest level.
        # Handlers can override by choosing a higher level.
        root_logger.setLevel(logging.DEBUG)
        cli_logger.setLevel(logging.DEBUG)
        cli_logger.propagate = False
        if root_logger.handlers and cli_logger.handlers:
            # loggers already configured
            return
        self._init_console_handlers(root_logger, cli_logger, log_level_config)
        if self.file_log_enabled:
            self._init_logfile_handlers(root_logger, cli_logger)
            get_logger(__name__).debug("File logging enabled - writing logs to '%s'.", self.log_dir)

    def _determine_verbose_level(self, args):
        """ Get verbose level by reading the arguments.
            Remove any consumed args.
        """
        verbose_level = 0
        for arg in args:
            if arg == CLILogging.VERBOSE_FLAG:
                verbose_level += 1
            elif arg == CLILogging.DEBUG_FLAG:
                verbose_level += 2
        # Use max verbose level if too much verbosity specified.
        return min(verbose_level, len(self.console_log_configs) - 1)

    def _init_console_handlers(self, root_logger, cli_logger, log_level_config):
        root_logger.addHandler(_CustomStreamHandler(log_level_config['root'],
                                                    self.console_log_format['root']))
        cli_logger.addHandler(_CustomStreamHandler(log_level_config[CLI_LOGGER_NAME],
                                                   self.console_log_format[CLI_LOGGER_NAME]))

    def _init_logfile_handlers(self, root_logger, cli_logger):
        ensure_dir(self.log_dir)
        log_file_path = os.path.join(self.log_dir, self.logfile_name)
        logfile_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
        lfmt = logging.Formatter('%(process)d : %(asctime)s : %(levelname)s : %(name)s : %(message)s')
        logfile_handler.setFormatter(lfmt)
        logfile_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(logfile_handler)
        cli_logger.addHandler(logfile_handler)

    @staticmethod
    def _is_file_log_enabled(ctx):
        return ctx.config.getboolean('logging', 'enable_log_file', fallback=False)

    @staticmethod
    def _get_log_dir(ctx):
        default_dir = (os.path.join(ctx.config.config_dir, 'logs'))
        return os.path.expanduser(ctx.config.get('logging', 'log_dir', fallback=default_dir))

    @staticmethod
    def _get_console_log_configs():
        return [
            # (default)
            {
                CLI_LOGGER_NAME: logging.WARNING,
                'root': logging.CRITICAL,
            },
            # --verbose
            {
                CLI_LOGGER_NAME: logging.INFO,
                'root': logging.CRITICAL,
            },
            # --debug
            {
                CLI_LOGGER_NAME: logging.DEBUG,
                'root': logging.DEBUG,
            }]

    @staticmethod
    def _get_console_log_format():
        """ Formats for console logging if coloring is enabled or not.
            Show the level name if coloring is disabled (e.g. INFO).
            Also, Root logger should show the logger name.
        """
        return {
            CLI_LOGGER_NAME: {
                True: '%(message)s',
                False: '%(levelname)s: %(message)s',
            },
            'root': {
                True: '%(name)s : %(message)s',
                False: '%(levelname)s: %(name)s : %(message)s',
            }
        }
