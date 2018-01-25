# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
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
    """ The main driver for the CLI """

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
        """
        :param cli_name: The name of the CLI (e.g. the executable name 'az')
        :type cli_name: str
        :param config_dir: Path to store config files for this CLI
        :type config_dir: str
        :param config_env_var_prefix: The prefix for configuration environment variables
        :type config_env_var_prefix: str
        :param out_file: File to write output to
        :type out_file: file-like object
        :param config_cls: Class to handle configuration
        :type config_cls: knack.config.CLIConfig
        :param logging_cls: Class to handle logging
        :type logging_cls: knack.log.CLILogging
        :param invocation_cls: Class to handle command invocations
        :type invocation_cls: knack.invocation.CommandInvoker
        :param output_cls: Class to handle output processing of commands
        :type output_cls: knack.output.OutputProducer
        :param completion_cls: Class to handle completions
        :type completion_cls: knack.completion.CLICompletion
        :param query_cls: Class to handle command queries
        :type query_cls: knack.query.CLIQuery
        :param parser_cls: Class to handler command parsing
        :type parser_cls: knack.parser.CLICommandParser
        :param commands_loader_cls: Class to handle loading commands
        :type commands_loader_cls: knack.commands.CLICommandsLoader
        :param help_cls: Class to handle help
        :type help_cls: knack.help.CLIHelp
        """
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
        self.completion = completion_cls(cli_ctx=self)
        self.logging = logging_cls(self.name, cli_ctx=self)
        self.output = self.output_cls(cli_ctx=self)
        self.query = query_cls(cli_ctx=self)

    @staticmethod
    def _should_show_version(args):
        return args and (args[0] == '--version' or args[0] == '-v')

    def get_cli_version(self):  # pylint: disable=no-self-use
        """ Get the CLI Version. Override this to define how to get the CLI version

        :return: The CLI version
        :rtype: str
        """
        return ''

    def get_runtime_version(self):  # pylint: disable=no-self-use
        """ Get the runtime information.

        :return: Runtime information
        :rtype: str
        """
        import platform

        version_info = '\n\n'
        version_info += 'Python ({}) {}'.format(platform.system(), sys.version)
        version_info += '\n\n'
        version_info += 'Python location \'{}\''.format(sys.executable)
        version_info += '\n'
        return version_info

    def show_version(self):
        """ Print version information to the out file. """
        version_info = self.get_cli_version()
        version_info += self.get_runtime_version()
        print(version_info, file=self.out_file)

    def register_event(self, event_name, handler):
        """ Register a callable that will be called when event is raised.
            A handler will only be registered once.

        :param event_name: The name of the event (see knack.events for in-built events)
        :type event_name: str
        :param handler: A callback to handle the event
        :type handler: function
        """
        self._event_handlers[event_name].append(handler)

    def unregister_event(self, event_name, handler):
        """ Unregister a callable that will be called when event is raised.

        :param event_name: The name of the event (see knack.events for in-built events)
        :type event_name: str
        :param handler: The callback that was used to register the event
        :type handler: function
        """
        try:
            self._event_handlers[event_name].remove(handler)
        except ValueError:
            pass

    def raise_event(self, event_name, **kwargs):
        """ Raise an event. Calls each handler in turn with kwargs

        :param event_name: The name of the event to raise
        :type event_name: str
        :param kwargs: Kwargs to be passed to all event handlers
        """
        handlers = list(self._event_handlers[event_name])
        logger.debug('Event: %s %s', event_name, handlers)
        for func in handlers:
            func(self, **kwargs)

    def exception_handler(self, ex):  # pylint: disable=no-self-use
        """ The default exception handler """
        if isinstance(ex, CLIError):
            logger.error(ex)
        else:
            logger.exception(ex)
        return 1

    def invoke(self, args, initial_invocation_data=None, out_file=None):
        """ Invoke a command.

        :param args: The arguments that represent the command
        :type args: list, tuple
        :param initial_invocation_data: Prime the in memory collection of key-value data for this invocation.
        :type initial_invocation_data: dict
        :param out_file: The file to send output to. If not used, we use out_file for knack.cli.CLI instance
        :type out_file: file-like object
        :return: The exit code of the invocation
        :rtype: int
        """
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
                self.invocation = self.invocation_cls(cli_ctx=self,
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
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as ex:  # pylint: disable=broad-except
            exit_code = self.exception_handler(ex)
        finally:
            pass
        return exit_code
