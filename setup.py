#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

setup(
    name='xivo',
    version='1.0',
    description='These are useful python libraries to be used with XIVO code',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'wazo-config-from-consul = xivo.config_from_consul:get_configuration_from_consul'
        ]
    },
)
