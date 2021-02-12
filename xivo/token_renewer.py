# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import itertools
import logging
import requests
import threading

logger = logging.getLogger(__name__)


class TokenRenewer(object):

    DEFAULT_EXPIRATION = 6 * 3600
    _RENEW_TIME_COEFFICIENT = 0.8

    def __init__(self, auth_client, expiration=DEFAULT_EXPIRATION):
        self._auth_client = auth_client
        self._expiration = expiration
        self._callbacks = []
        self._callbacks_tmp = []
        self._started = False
        self._stopped = threading.Event()
        self._renew_time = 0
        self._callback_lock = threading.Lock()
        self._renew_time_failed = itertools.chain(
            (1, 2, 4, 8, 16), itertools.repeat(32)
        )

    def subscribe_to_token_change(self, callback):
        with self._callback_lock:
            self._callbacks.append({'method': callback, 'details': False})

    def subscribe_to_next_token_change(self, callback):
        with self._callback_lock:
            self._callbacks_tmp.append({'method': callback, 'details': False})

    def subscribe_to_next_token_details_change(self, callback):
        with self._callback_lock:
            self._callbacks_tmp.append({'method': callback, 'details': True})

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

    def emit_stop(self):
        self._stopped.set()

    def _run(self):
        while True:
            self._stopped.wait(self._renew_time)
            if self._stopped.is_set():
                return

            self._renew_token()

    def _renew_token(self):
        logger.debug(
            'Creating token for "%s" with expiration %s',
            self._auth_client.username,
            self._expiration,
        )
        try:
            token = self._auth_client.token.new(expiration=self._expiration)
        except Exception as e:
            debug_message = 'Creating token with wazo-auth failed'
            try:
                raise
            except requests.exceptions.ConnectionError as error:
                logger.debug('%s: %s', debug_message, error)
            except Exception:
                logger.debug(debug_message, exc_info=True)
            response = getattr(e, 'response', None)
            status_code = getattr(response, 'status_code', '')
            self._renew_time = next(self._renew_time_failed)
            logger.warning(
                'Creating token with wazo-auth failed (%s). Retrying in %s seconds...',
                status_code,
                self._renew_time,
            )
        else:
            self._renew_time = self._RENEW_TIME_COEFFICIENT * self._expiration
            self._notify_all(token)

    def _notify_all(self, token):
        with self._callback_lock:
            callbacks = list(self._callbacks + self._callbacks_tmp)
            self._callbacks_tmp = []

        for callback in callbacks:
            payload = token if callback['details'] else token['token']
            try:
                callback['method'](payload)
            except Exception:
                logger.warning(
                    'unexpected exception from token change callback', exc_info=True
                )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
