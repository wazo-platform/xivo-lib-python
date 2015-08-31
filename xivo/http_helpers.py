# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
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

import urllib

from cherrypy.wsgiserver.ssl_pyopenssl import pyOpenSSLAdapter
from flask import current_app, request
from OpenSSL import SSL

DEFAULT_CIPHERS = 'ALL:!aNULL:!eNULL:!LOW:!EXP:!RC4:!3DES:!SEED:+HIGH:+MEDIUM'


def add_logger(app, logger):
    for handler in logger.handlers:
        app.logger.addHandler(handler)


def log_request(response):
    url = urllib.unquote(request.url)
    current_app.logger.info('(%s) %s %s %s', request.remote_addr, request.method, url, response.status_code)
    return response


def ssl_adapter(certificate, private_key, ciphers):
    adapter = pyOpenSSLAdapter(certificate, private_key)
    adapter.context = SSL.Context(SSL.SSLv23_METHOD)
    adapter.context.set_options(SSL.OP_NO_SSLv2)
    adapter.context.set_options(SSL.OP_NO_SSLv3)
    # adapter.context.set_options(SSL.OP_NO_COMPRESSION)  # Python 2.7.9+ only
    adapter.context.use_certificate_file(certificate)
    adapter.context.use_privatekey_file(private_key)
    adapter.context.set_cipher_list(ciphers)
    return adapter


def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, rule)
        output.append(line)

    return output
