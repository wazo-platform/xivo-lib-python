#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

requirements = [
    "flask==0.10.1",
    "psycopg2==2.5.4",
    "pyyaml==3.11",
    "pyopenssl==0.14",
    "python-consul==0.4.7",
    "stevedore==0.14.1",
    "xivo_auth_client==0.1",
]

dependency_links = [
    'git+https://github.com/xivo-pbx/xivo-auth-client.git#egg=xivo_auth_client-0.1'
]

setup(
    name='xivo',
    version='1.0',
    description='These are useful python libraries to be used with XIVO code',
    author='Avencall',
    author_email='xivo-dev@lists.proformatique.com',
    url='http://projects.xivo.io/',
    packages=find_packages(),
    install_requires=requirements,
    dependency_links=dependency_links
)
