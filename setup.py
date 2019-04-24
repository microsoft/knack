#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from codecs import open
from setuptools import setup, find_packages

VERSION = '0.6.0'

DEPENDENCIES = [
    'argcomplete',
    'colorama',
    'jmespath',
    'pygments',
    'pyyaml',
    'six',
    'tabulate'
]

with open('README.rst', 'r', encoding='utf-8') as f:
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
    packages=['knack', 'knack.testsdk'],
    install_requires=DEPENDENCIES,
    extras_require={
        ':python_version<"3.4"': ['enum34']
    }
)
