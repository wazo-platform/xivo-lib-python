# -*- coding: utf-8 -*-
# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import re

from cheroot.ssl.builtin import BuiltinSSLAdapter
from flask import current_app, request
from six.moves.urllib.parse import unquote


class ReverseProxied(object):
    '''
    From http://flask.pocoo.org/snippets/35/
    '''

    def __init__(self, application):
        self.app = application

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name

        return self.app(environ, start_response)


def add_logger(app, logger):
    app.config['LOGGER_HANDLER_POLICY'] = 'never'
    app.logger.propagate = True


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
