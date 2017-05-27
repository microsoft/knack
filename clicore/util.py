# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


class CLIError(Exception):
    """Base class for exceptions that occur during
    normal operation of the application.
    Typically due to user error and can be resolved by the user.
    """
    def __init__(self, message):  # pylint: disable=useless-super-delegation
        super(CLIError, self).__init__(message)


def ensure_dir(d):
    """ Create a directory if it doesn't exist """
    if not os.path.isdir(d):
        os.makedirs(d)
