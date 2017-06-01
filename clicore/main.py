# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import platform
from collections import defaultdict

from ._application import Application
from ._completion import get_completion_args
from ._output import OutputProducer
from .log import CLILogging, get_logger
from .util import CLIError
from .config import CLIConfig

logger = get_logger(__name__)


class CLI(object):  # pylint: disable=too-many-instance-attributes

    EVENT_PRE_EXECUTE = 'Cli.PreExecute'
    EVENT_POST_EXECUTE = 'Cli.PostExecute'

    def __init__(self,
                 cli_name='cli',
                 config_dir_name='cli',
                 config_env_var_name=None,
                 out_file=sys.stdout,
                 config_cls=CLIConfig,
                 logging_cls=CLILogging,
                 application_cls=Application,
                 output_cls=OutputProducer):
        self.name = cli_name
        self.out_file = out_file
        self.config_cls = config_cls
        self.logging_cls = logging_cls
        self.output_cls = output_cls
        self.application_cls = application_cls
        self._event_handlers = defaultdict(lambda: [])
        # Data that's typically backed to persistent storage
        self.config = config_cls(config_dir_name, config_env_var_name)
        # In memory collection of key-value data for this current cli. This persists between invocations.
        self.cli_data = defaultdict(lambda: None)
        # In memory collection of key-value data for this current invocation This does not persist between invocations.
        self.invocation_data = defaultdict(lambda: None)
        self.logging = logging_cls(self.name, ctx=self)

    def _execute(self, args):
        application = self.application_cls(ctx=self)
        cmd_result = application.execute(args)
        output_type = self.invocation_data['output']
        if cmd_result and cmd_result.result is not None:
            formatter = self.output_cls.get_formatter(output_type)
            self.output_cls(formatter=formatter, out_file=self.out_file).out(cmd_result)

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

    def _remove_logger_flags(self, args):
        return [x for x in args if x not in (self.logging_cls.VERBOSE_FLAG, self.logging_cls.DEBUG_FLAG)]

    def register_event(self, event_name, handler):
        """ Register a callable that will be called when event is raised.
            A handler will only be registered once. """
        self._event_handlers[event_name].append(handler)

    def unregister_event(self, event_name, handler):
        """ Unregister a callable that will be called when event is raised. """
        try:
            self._event_handlers[event_name].remove(handler)
        except KeyError:
            pass

    def raise_event(self, event_name, **kwargs):
        """ Raise an event. """
        for func in list(self._event_handlers[event_name]):
            func(self, **kwargs)

    def exception_handler(self, ex):  # pylint: disable=no-self-use
        logger.exception(ex)
        return 1

    def run(self, args):
        """ Run the CLI and return the exit code """
        # Reset invocation data
        self.invocation_data = defaultdict(lambda: None)
        try:
            args = get_completion_args() or args

            self.logging.configure(args)
            args = self._remove_logger_flags(args)
            logger.debug('Command arguments %s', args)

            self.raise_event(CLI.EVENT_PRE_EXECUTE)
            if CLI._should_show_version(args):
                self.show_version()
            else:
                self._execute(args)
            self.raise_event(CLI.EVENT_POST_EXECUTE)
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
