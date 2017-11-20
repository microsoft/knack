#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

# Style checks
python -m pylint knack --rcfile=.pylintrc -r n -d I0013
flake8 --statistics --append-config=.flake8 knack

# Tests
python -m unittest discover tests
python ./examples/test_exapp

# Misc.
python $scripts_root/license_verify.py

# Does it build?
python setup.py bdist_wheel
