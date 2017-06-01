# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import CommandResultItem


class Application(object):

    def __init__(self, ctx=None):
        self.ctx = ctx

    def execute(self, args):  # pylint: disable=unused-argument
        # TODO
        self.ctx.invocation_data['output'] = self.ctx.config.get('core', 'output', fallback='json')
        return CommandResultItem([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}])
