#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

requirements = [
    "psycopg2==2.5.4",
    "pyyaml==3.11",
    "pyopenssl==0.14",
    "python-consul==0.4.7",
]

setup(
    name='xivo',
    version='1.0',
    description='These are useful python libraries to be used with XIVO code',
    author='Avencall',
    author_email='xivo-dev@lists.proformatique.com',
    url='http://projects.xivo.io/',
    packages=find_packages(),
    install_requires=requirements
)
