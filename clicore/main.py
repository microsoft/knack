# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import platform

from .completion import get_completion_args
from .cli_logging import CLILogging, get_logger

logger = get_logger(__name__)

class CLI(object):

    _DEFAULT_CONFIG = {
        'supports_telemetry': True
    }

    def __init__(self,
                 name,
                 config=None,
                 on_pre_execute=None,
                 on_post_execute=None,
                 on_execute_exception=None,
                 on_get_version=None,
                 out_file=sys.stdout):
        self.cli_name = name
        self.config = config or CLI._DEFAULT_CONFIG
        self.on_pre_execute = on_pre_execute or (lambda: None)
        self.on_post_execute = on_post_execute or (lambda: None)
        self.on_execute_exception = on_execute_exception or (lambda _: 1)
        self.on_get_version = on_get_version or (lambda: None)
        self.out_file = out_file
        self.logging = CLILogging(self.cli_name)

    def _execute(self, args):
        print(args)
        return
        # APPLICATION.initialize(Configuration())
        # cmd_result = APPLICATION.execute(args)
        # if cmd_result and cmd_result.result is not None:
        #     from azure.cli.core._output import OutputProducer
        #     formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
        #     OutputProducer(formatter=formatter, file=file).out(cmd_result)

    def _should_show_version(self, args):
        return args and (args[0] == '--version' or args[0] == '-v')

    def _show_version_info(self):
        version_info = self.on_get_version() or ''
        version_info += '\n\n'
        version_info += 'Python ({}) {}'.format(platform.system(), sys.version)
        version_info += '\n\n'
        version_info += 'Python location \'{}\''.format(sys.executable)
        version_info += '\n'
        print(version_info, file=self.out_file)

    @staticmethod
    def _remove_logger_flags(args):
        return filter(lambda x: x not in (CLILogging.VERBOSE_FLAG, CLILogging.DEBUG_FLAG), args)

    def run(self, args):
        """ Run the CLI and return the exit code """
        try:
            args = get_completion_args() or args

            self.logging.configure(args)
            args = CLI._remove_logger_flags(args)
            logger.debug('Command arguments %s', args)
 
            # TODO Add telemetry support
            self.on_pre_execute()
            if self._should_show_version(args):
                self._show_version_info()
            else:
                self._execute(args)
            self.on_post_execute()
            exit_code = 0
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as ex:  # pylint: disable=broad-except
            # logger.exception(ex)
            # TODO Remove this
            print(ex)
            exit_code = self.on_execute_exception(ex)
        finally:
            pass
        return exit_code

