#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

python -m pylint knack --rcfile=.pylintrc -r n -d I0013

flake8 --statistics --append-config=.flake8 knack

python $scripts_root/license_verify.py
