# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import threading

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

    def unsubscribe_from_token_change(self, callback):
        if threading.current_thread() != self._thread:
            raise UserWarning('unsubscribe_from_token_change is not threadsafe')

        self._callbacks.remove(callback)

    def start(self):
        if self._started:
            raise Exception('token renewer already started')

        self._renew_token()

        self._started = True
        self._thread = threading.Thread(target=self._run, name='token-renewer')
        self._thread.start()

    def stop(self):
        self._stopped.set()
        logger.debug('joining token renewer thread...')
        self._thread.join()

    def _run(self):
        while True:
            self._stopped.wait(self._renew_time)
            if self._stopped.is_set():
                return

            self._renew_token()

    def _renew_token(self):
        logger.debug(
            'Creating token for "%s" with backend "%s", expiration %s',
            self._auth_client.username,
            self._backend,
            self._expiration
        )
        try:
            token = self._auth_client.token.new(self._backend, expiration=self._expiration)
        except Exception:
            logger.warning('create token with wazo-auth failed', exc_info=True)
            self._renew_time = self._RENEW_TIME_FAILED
        else:
            self._renew_time = self._RENEW_TIME_COEFFICIENT * self._expiration
            self._notify_all(token['token'])

    def _notify_all(self, token_id):
        for callback in list(self._callbacks):
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
