# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


def get_completion_args(is_completion=False, comp_line=None):
    """ Get the args that will be used to tab completion if completion is active. """
    is_completion = is_completion or os.environ.get('_ARGCOMPLETE')
    comp_line = comp_line or os.environ.get('COMP_LINE')
    # The first item is the exe name so ignore that.
    return comp_line.split()[1:] if is_completion and comp_line else None
