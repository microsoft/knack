# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile

from knack.cli import CLI, CLICommandsLoader

class MockContext(CLI):

    def __init__(self):
        super(MockContext, self).__init__(config_dir=tempfile.mkdtemp())
        loader = CLICommandsLoader(self)
        setattr(self, 'commands_loader', loader)
