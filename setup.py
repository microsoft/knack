#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from setuptools import setup

VERSION = '0.9.1'

DEPENDENCIES = [
    'argcomplete',
    'jmespath',
    'pygments',
    'pyyaml',
    'tabulate',
    # On Windows, colorama is required for legacy terminals.
    'colorama; sys_platform == "win32"'
]

with open('README.rst', 'r') as f:
    README = f.read()

setup(
    name='knack',
    version=VERSION,
    description='A Command-Line Interface framework',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/microsoft/knack',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
    ],
    packages=['knack', 'knack.testsdk'],
    install_requires=DEPENDENCIES
)
