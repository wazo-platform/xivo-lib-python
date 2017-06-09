# -*- coding: utf-8 -*-

# Copyright 2016-2017 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import re

from cheroot.ssl.builtin import BuiltinSSLAdapter
from flask import current_app, request
from six.moves.urllib.parse import unquote


def add_logger(app, logger):
    for handler in logger.handlers:
        app.logger.addHandler(handler)


def _log_request(url, response):
    current_app.logger.info('(%s) %s %s %s', request.remote_addr, request.method, url, response.status_code)


def log_request(response):
    url = unquote(request.url)
    _log_request(url, response)
    return response


_REPLACE_TOKEN_REGEX = re.compile(r'\btoken=[-0-9a-zA-Z]+')

def log_request_hide_token(response):
    url = unquote(request.url)
    url = _REPLACE_TOKEN_REGEX.sub('token=<hidden>', url)
    _log_request(url, response)
    return response


def ssl_adapter(certificate, private_key):
    _check_file_readable(certificate)
    _check_file_readable(private_key)

    return BuiltinSSLAdapter(certificate, private_key)


def _check_file_readable(file_path):
    with open(file_path, 'r'):
        pass


def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, rule)
        output.append(line)

    return output
