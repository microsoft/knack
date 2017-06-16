# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import platform
from collections import defaultdict

from .invocation import CommandInvoker
from .completion import CLICompletion
from .output import OutputProducer
from .log import CLILogging, get_logger
from .util import CLIError
from .config import CLIConfig
from .query import CLIQuery
from .events import EVENT_CLI_PRE_EXECUTE, EVENT_CLI_POST_EXECUTE
from .parser import CLICommandParser
from .commands import CLICommandsLoader
from .help import CLIHelp

logger = get_logger(__name__)


class CLI(object):  # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 cli_name='cli',
                 config_dir=None,
                 config_env_var_prefix=None,
                 out_file=sys.stdout,
                 config_cls=CLIConfig,
                 logging_cls=CLILogging,
                 invocation_cls=CommandInvoker,
                 output_cls=OutputProducer,
                 completion_cls=CLICompletion,
                 query_cls=CLIQuery,
                 parser_cls=CLICommandParser,
                 commands_loader_cls=CLICommandsLoader,
                 help_cls=CLIHelp):
        self.name = cli_name
        self.out_file = out_file
        self.config_cls = config_cls
        self.logging_cls = logging_cls
        self.output_cls = output_cls
        self.parser_cls = parser_cls
        self.help_cls = help_cls
        self.commands_loader_cls = commands_loader_cls
        self.invocation_cls = invocation_cls
        self.invocation = None
        self._event_handlers = defaultdict(lambda: [])
        # Data that's typically backed to persistent storage
        self.config = config_cls(config_dir=config_dir, config_env_var_prefix=config_env_var_prefix)
        # In memory collection of key-value data for this current cli. This persists between invocations.
        self.data = defaultdict(lambda: None)
        self.completion = completion_cls(ctx=self)
        self.logging = logging_cls(self.name, ctx=self)
        self.output = self.output_cls(ctx=self)
        self.query = query_cls(ctx=self)

    @staticmethod
    def _should_show_version(args):
        return args and (args[0] == '--version' or args[0] == '-v')

    def get_cli_version(self):  # pylint: disable=no-self-use
        return ''

    def get_runtime_version(self):  # pylint: disable=no-self-use
        version_info = '\n\n'
        version_info += 'Python ({}) {}'.format(platform.system(), sys.version)
        version_info += '\n\n'
        version_info += 'Python location \'{}\''.format(sys.executable)
        version_info += '\n'
        return version_info

    def show_version(self):
        version_info = self.get_cli_version()
        version_info += self.get_runtime_version()
        print(version_info, file=self.out_file)

    def register_event(self, event_name, handler):
        """ Register a callable that will be called when event is raised.
            A handler will only be registered once. """
        self._event_handlers[event_name].append(handler)

    def unregister_event(self, event_name, handler):
        """ Unregister a callable that will be called when event is raised. """
        try:
            self._event_handlers[event_name].remove(handler)
        except ValueError:
            pass

    def raise_event(self, event_name, **kwargs):
        """ Raise an event. """
        handlers = list(self._event_handlers[event_name])
        logger.debug('Event: %s %s', event_name, handlers)
        for func in handlers:
            func(self, **kwargs)

    def exception_handler(self, ex):  # pylint: disable=no-self-use
        logger.exception(ex)
        return 1

    def invoke(self, args, initial_invocation_data=None, out_file=None):
        """ Invoke a command. """
        if not isinstance(args, (list, tuple)):
            raise TypeError('args should be a list or tuple.')
        try:
            args = self.completion.get_completion_args() or args
            out_file = out_file or self.out_file

            self.logging.configure(args)
            logger.debug('Command arguments: %s', args)

            self.raise_event(EVENT_CLI_PRE_EXECUTE)
            if CLI._should_show_version(args):
                self.show_version()
            else:
                self.invocation = self.invocation_cls(ctx=self,
                                                      parser_cls=self.parser_cls,
                                                      commands_loader_cls=self.commands_loader_cls,
                                                      help_cls=self.help_cls,
                                                      initial_data=initial_invocation_data)
                cmd_result = self.invocation.execute(args)
                output_type = self.invocation.data['output']
                if cmd_result and cmd_result.result is not None:
                    formatter = self.output.get_formatter(output_type)
                    self.output.out(cmd_result, formatter=formatter, out_file=out_file)
            self.raise_event(EVENT_CLI_POST_EXECUTE)
            exit_code = 0
        except CLIError as ex:
            logger.error(ex)
            exit_code = 1
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as ex:  # pylint: disable=broad-except
            exit_code = self.exception_handler(ex)
        finally:
            pass
        return exit_code
