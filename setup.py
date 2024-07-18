#!/usr/bin/env python3
# Copyright 2007-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages, setup

setup(
    name='wazo',
    version='1.0',
    description='These are useful python libraries to be used with Wazo code',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
)
