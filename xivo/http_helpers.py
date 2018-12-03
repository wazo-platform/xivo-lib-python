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


class LazyHeaderFormatter(object):

    VISIBLE_TOKEN_SIZE = 8

    def __init__(self, raw_headers):
        self._raw_headers = raw_headers

    def __str__(self):
        headers_dict = self._to_dict(self._raw_headers)
        filtered_headers = self._filter_sensible_fields(headers_dict)
        return '{}'.format(filtered_headers)

    def _filter_sensible_fields(self, headers):
        if 'Authorization' in headers:
            if headers['Authorization'].startswith('Basic '):
                new_value = 'Basic <hidden>'
            else:
                new_value = '<hidden>'

            headers['Authorization'] = new_value

        if 'X-Auth-Token' in headers:
            value = headers['X-Auth-Token']
            visible_pos = len(value) - self.VISIBLE_TOKEN_SIZE
            new_value = []
            for i, c in enumerate(value):
                if i >= visible_pos or c == '-':
                    new_value.append(c)
                else:
                    new_value.append('X')
            headers['X-Auth-Token'] = ''.join(new_value)

        return headers

    def _to_dict(self, headers):
        return dict(headers)


def _log_request(url, response):
    current_app.logger.info('response: (%s) %s %s %s', request.remote_addr, request.method, url, response.status_code)


def log_before_request():
    not_printable_content_types = [
        'application/octet-stream',
    ]

    params = {
        'method': request.method,
        'url': unquote(request.url),
        'headers': LazyHeaderFormatter(request.headers),
    }

    if request.data and request.headers.get('Content-Type') not in not_printable_content_types:
        try:
            params['data'] = request.data.decode('utf-8')
        except UnicodeDecodeError:
            params['data'] = repr(request.data)
        fmt = "request: %(method)s %(url)s %(headers)s with data %(data)s"
    else:
        fmt = "request: %(method)s %(url)s %(headers)s"

    current_app.logger.info(fmt, params)


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
