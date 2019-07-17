# -*- coding: utf-8 -*-
# Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import print_function

"""Backend support for PostgreSQL for anysql

Copyright (C) 2010  Avencall

"""

__version__ = "$Revision$ $Date$"

import psycopg2
import psycopg2.extensions

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)  # noqa: E402
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)  # noqa: E402

from six.moves.urllib import parse

from xivo import anysql

__typemap = {
    "host": str,
    "user": str,
    "passwd": str,
    "db": str,
    "port": int,
    "unix_socket": str,
    "compress": bool,
    "connect_timeout": int,
    "read_default_file": str,
    "read_default_group": str,
    "use_unicode": (lambda x: bool(int(x))),
    "conv": None,
    "quote_conv": None,
    "cursorclass": None,
    "charset": str,
}


def __apply_types(params, typemap):
    for k in typemap.iterkeys():
        if k in params:
            if typemap[k] is not None:
                params[k] = typemap[k](params[k])
            else:
                del params[k]


def __dict_from_query(query):
    print("dfQ=", query)
    if not query:
        return {}
    return dict(query)


def connect_by_uri(uri):
    """General URI syntax:

    postgresql://user:passwd@host:port/db

    NOTE: the authority and the path parts of the URI have precedence
    over the query part, if an argument is given in both.

        conv,quote_conv,cursorclass
    are not (yet?) allowed as complex Python objects are needed, hard to
    transmit within an URI...
    """

    puri = parse.urlsplit(uri)
    params = {}

    if puri.username:
        params['user'] = puri.username
    if puri.password:
        params['password'] = puri.password
    if puri.hostname:
        params['host'] = puri.hostname
    if puri.port:
        params['port'] = puri.port
    if puri.path:
        params['database'] = puri.path
        if params['database'] and params['database'][0] == '/':
            params['database'] = params['database'][1:]

    # __apply_types(params, __typemap)

    return psycopg2.connect(**params)


def escape(s):
    return '.'.join(['"%s"' % comp for comp in s.split('.')])


def cast(fieldname, type):
    return "%s::%s" % (fieldname, type)


anysql.register_uri_backend('postgresql', connect_by_uri, psycopg2, None, escape, cast)
