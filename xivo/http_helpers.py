# Copyright 2016-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import re
import time
from logging import Logger
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from cheroot.ssl.builtin import BuiltinSSLAdapter
from flask import current_app, Flask, g, request, Response

from json.decoder import JSONDecodeError

PRINTABLE_CONTENT_TYPES = [
    'application/json',
]

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIApplication, WSGIEnvironment
    from werkzeug.datastructures import Headers


class ReverseProxied:
    """
    From https://stackoverflow.com/questions/30743696/create-proxy-for-python-flask-application
    """

    def __init__(self, application: WSGIApplication) -> None:
        self.app = application

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name

        return self.app(environ, start_response)


def reverse_proxy_fix_api_spec(api_spec: dict[str, Any]) -> None:
    prefix = request.headers.get('X-Script-Name')
    if prefix:
        api_spec['schemes'] = ['https']
        base_path = api_spec.get('basePath', '')
        api_spec['basePath'] = f'{prefix}{base_path}'


def add_logger(app, logger: Logger) -> None:
    app.config['LOGGER_HANDLER_POLICY'] = 'never'
    app.logger.propagate = True


class BodyFormatter:

    _HIDDEN_VALUE = '<hidden>'

    def __init__(self, raw_body: bytes, hidden_fields: list[str] | None) -> None:
        self._hidden_fields = hidden_fields
        self._raw_body = raw_body

    def __str__(self) -> str:
        try:
            printable_body = self._raw_body.decode('utf-8')
        except UnicodeDecodeError:
            printable_body = repr(self._raw_body)

        if not self._hidden_fields:
            return printable_body

        try:
            serialized_body = json.loads(printable_body)
        except JSONDecodeError:
            for field in self._hidden_fields:
                if field in printable_body:
                    return self._HIDDEN_VALUE
            return printable_body

        for field in self._hidden_fields:
            if field in serialized_body:
                serialized_body[field] = self._HIDDEN_VALUE

        return json.dumps(serialized_body)


class LazyHeaderFormatter:

    VISIBLE_TOKEN_SIZE = 8

    def __init__(self, raw_headers: Headers | dict[str, str]) -> None:
        self._raw_headers = raw_headers

    def __str__(self) -> str:
        headers_dict = self._to_dict(self._raw_headers)
        filtered_headers = self._filter_sensible_fields(headers_dict)
        return f'{filtered_headers}'

    def _filter_sensible_fields(self, headers: dict[str, str]) -> dict[str, str]:
        # should be "sensitive"
        if 'Authorization' in headers:
            if headers['Authorization'].startswith('Basic '):
                new_header = 'Basic <hidden>'
            else:
                new_header = '<hidden>'

            headers['Authorization'] = new_header

        if 'X-Auth-Token' in headers:
            value = headers['X-Auth-Token']
            visible_pos = len(value) - self.VISIBLE_TOKEN_SIZE
            new_value: list[str] = []
            for i, c in enumerate(value):
                if i >= visible_pos or c == '-':
                    new_value.append(c)
                else:
                    new_value.append('X')
            headers['X-Auth-Token'] = ''.join(new_value)

        return headers

    def _to_dict(self, headers: Headers | dict[str, str]) -> dict[str, str]:
        return dict(headers)


def _log_request(
    url, response: Response, hidden_fields: list[str] | None = None
) -> None:
    current_app.logger.info(
        'response to %s%s: %s %s %s',
        request.remote_addr,
        (
            f' in {time.time() - g.request_time:.2f}s'
            if hasattr(g, 'request_time')
            else ''
        ),
        request.method,
        url,
        response.status_code,
    )
    if response.headers.get('Content-Type') not in PRINTABLE_CONTENT_TYPES:
        content_type = response.headers.get('Content-Type')
        current_app.logger.debug(
            """response body: not printable: "%s" """, content_type
        )
    elif not response.data:
        current_app.logger.debug("response body empty")
    else:
        body = BodyFormatter(response.data, hidden_fields)
        current_app.logger.debug("response body: %s", body)


def log_before_request(hidden_fields: list[str] | None = None) -> None:
    params = {
        'method': request.method,
        'url': unquote(request.url),
        'headers': LazyHeaderFormatter(request.headers),
    }

    if request.data and request.headers.get('Content-Type') in PRINTABLE_CONTENT_TYPES:
        params['data'] = BodyFormatter(request.data, hidden_fields)
        fmt = "request: %(method)s %(url)s %(headers)s with data %(data)s"
    else:
        fmt = "request: %(method)s %(url)s %(headers)s"

    current_app.logger.info(fmt, params)
    g.request_time = time.time()


def log_request(response: Response) -> Response:
    url = unquote(request.url)
    _log_request(url, response)
    return response


_REPLACE_TOKEN_REGEX = re.compile(r'\btoken=[-0-9a-zA-Z]+')


def log_request_hide_token(response: Response) -> Response:
    url = unquote(request.url)
    url = _REPLACE_TOKEN_REGEX.sub('token=<hidden>', url)
    _log_request(url, response)
    return response


def ssl_adapter(certificate: str, private_key: str) -> BuiltinSSLAdapter:
    _check_file_readable(certificate)
    _check_file_readable(private_key)

    return BuiltinSSLAdapter(certificate, private_key)


def _check_file_readable(file_path: str) -> None:
    with open(file_path):
        pass


def list_routes(app: Flask) -> list[str]:
    output: list[str] = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = f"{rule.endpoint:50s} {methods:20s} {rule}"
        output.append(line)
    return output
