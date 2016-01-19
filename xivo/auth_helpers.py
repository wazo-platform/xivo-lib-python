# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016 Avencall
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

import logging
import requests
import threading

from flask import request
from functools import wraps
from xivo_auth_client import Client

from xivo import rest_api_helpers

logger = logging.getLogger(__name__)


class TokenRenewer(object):

    DEFAULT_EXPIRATION = 6 * 3600
    DEFAULT_BACKEND = 'xivo_service'
    _RENEW_TIME_COEFFICIENT = 0.8
    _RENEW_TIME_FAILED = 20

    def __init__(self, auth_client, backend=DEFAULT_BACKEND, expiration=DEFAULT_EXPIRATION):
        self._auth_client = auth_client
        self._backend = backend
        self._expiration = expiration
        self._callbacks = []
        self._started = False
        self._stopped = threading.Event()
        self._renew_time = 0

    def subscribe_to_token_change(self, callback):
        if self._started:
            raise Exception('token renewer already started')

        self._callbacks.append(callback)
        self._notify(callback, None)

    def start(self):
        if self._started:
            raise Exception('token renewer already started')

        self._renew_token()

        self._started = True
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self._stopped.set()

    def _run(self):
        while True:
            self._stopped.wait(self._renew_time)
            if self._stopped.is_set():
                return

            self._renew_token()

    def _renew_token(self):
        try:
            token = self._auth_client.token.new(self._backend, expiration=self._expiration)
        except Exception:
            logger.warning('create token with xivo-auth failed', exc_info=True)
            self._renew_time = self._RENEW_TIME_FAILED
        else:
            self._renew_time = self._RENEW_TIME_COEFFICIENT * self._expiration
            self._notify_all(token['token'])

    def _notify_all(self, token_id):
        for callback in self._callbacks:
            self._notify(callback, token_id)

    def _notify(self, callback, token_id):
        try:
            callback(token_id)
        except Exception:
            logger.warning('unexpected exception from token change callback', exc_info=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


def required_acl(acl):
    def wrapper(func):
        func.acl = acl
        return func
    return wrapper


class Unauthorized(rest_api_helpers.APIException):

    def __init__(self, token):
        super(Unauthorized, self).__init__(
            status_code=401,
            message='Unauthorized',
            error_id='unauthorized',
            details={
                'invalid_token': token
            }
        )


class AuthServerUnreachable(rest_api_helpers.APIException):

    def __init__(self, host, port, error):
        super(AuthServerUnreachable, self).__init__(
            status_code=503,
            message='Authentication server unreachable',
            error_id='authentication-server-unreachable',
            details={
                'auth_server_host': host,
                'auth_server_port': port,
                'original_error': str(error),
            }
        )


class AuthVerifier(object):

    def __init__(self, auth_config=None):
        self._auth_client = None
        self._auth_config = auth_config

    def set_config(self, auth_config):
        self._auth_config = dict(auth_config)
        self._auth_config.pop('username', None)
        self._auth_config.pop('password', None)
        self._auth_config.pop('key_file', None)

    def set_client(self, auth_client):
        self._auth_client = auth_client

    def verify_token(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            assert self._auth_config or self._auth_client, 'AuthVerifier is not configured'

            token = self.token()
            required_acl = self.acl(func, *args, **kwargs)

            try:
                token_is_valid = self.client().token.is_valid(token, required_acl)
            except requests.RequestException as e:
                return self.handle_unreachable(e)

            if token_is_valid:
                return func(*args, **kwargs)

            return self.handle_unauthorized(token)
        return wrapper

    def token(self):
        return request.headers.get('X-Auth-Token', '')

    def acl(self, decorated_function, *args, **kwargs):
        return getattr(decorated_function, 'acl', '').format(**kwargs)

    def handle_unreachable(self, error):
        raise AuthServerUnreachable(self._auth_config['host'], self._auth_config['port'], error)

    def handle_unauthorized(self, token):
        raise Unauthorized(token)

    def client(self):
        if not self._auth_client:
            self._auth_client = Client(**self._auth_config)
        return self._auth_client
