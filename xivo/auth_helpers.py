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

import logging
import threading

logger = logging.getLogger(__name__)


class TokenRenewer(object):

    DEFAULT_EXPIRATION = 6 * 3600
    DEFAULT_BACKEND = 'xivo_service'
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
            self._renew_time = 0.8 * self._expiration
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
