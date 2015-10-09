#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

requirements = [
    "psycopg2==2.4.5",
    "pyyaml==3.10",
    "pyopenssl==0.13",
    "python-consul",
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
