# Copyright 2015-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import itertools
import logging
import threading
import types
from collections.abc import Collection
from typing import TYPE_CHECKING, Callable, TypedDict, TypeVar

import requests

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from wazo_auth_client.client import AuthClient


Callback = Callable[[Collection[str]], None]


class CallbackDict(TypedDict):
    method: Callback
    details: bool


Self = TypeVar('Self', bound='TokenRenewer')


class TokenRenewer:
    DEFAULT_EXPIRATION = 6 * 3_600
    _RENEW_TIME_COEFFICIENT = 0.8

    def __init__(
        self, auth_client: AuthClient, expiration: int = DEFAULT_EXPIRATION
    ) -> None:
        self._auth_client = auth_client
        self._expiration = expiration
        self._callbacks: list[CallbackDict] = []
        self._callbacks_tmp: list[CallbackDict] = []
        self._started = False
        self._stopped = threading.Event()
        self._renew_time: float = 0
        self._callback_lock = threading.Lock()
        self._renew_time_failed = itertools.chain(
            (1, 2, 4, 8, 16), itertools.repeat(32)
        )

    def subscribe_to_token_change(self, callback: Callback) -> None:
        with self._callback_lock:
            self._callbacks.append({'method': callback, 'details': False})

    def subscribe_to_next_token_change(self, callback: Callback) -> None:
        with self._callback_lock:
            self._callbacks_tmp.append({'method': callback, 'details': False})

    def subscribe_to_next_token_details_change(self, callback: Callback) -> None:
        with self._callback_lock:
            self._callbacks_tmp.append({'method': callback, 'details': True})

    def start(self) -> None:
        if self._started:
            raise Exception('token renewer already started')

        self._renew_token()

        self._started = True
        self._thread = threading.Thread(target=self._run, name='token-renewer')
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        logger.debug('joining token renewer thread...')
        self._thread.join()

    def emit_stop(self) -> None:
        self._stopped.set()

    def _run(self) -> None:
        while True:
            self._stopped.wait(self._renew_time)
            if self._stopped.is_set():
                return

            self._renew_token()

    def _renew_token(self) -> None:
        logger.debug(
            'Creating token for "%s" with expiration %s',
            self._auth_client.username,
            self._expiration,
        )
        try:
            token = self._auth_client.token.new(expiration=self._expiration)
        except requests.exceptions.ConnectionError as error:
            logger.debug('Creating token with wazo-auth failed: %s', error)
            self._handle_renewal_error(error)
        except Exception as error:
            logger.debug('Creating token with wazo-auth failed', exc_info=True)
            self._handle_renewal_error(error)
        else:
            self._renew_time = self._RENEW_TIME_COEFFICIENT * self._expiration
            self._notify_all(token)

    def _handle_renewal_error(self, error: Exception) -> None:
        response = getattr(error, 'response', None)
        status_code = getattr(response, 'status_code', '')
        self._renew_time = next(self._renew_time_failed)
        logger.warning(
            'Creating token with wazo-auth failed (%s). Retrying in %s seconds...',
            status_code,
            self._renew_time,
        )

    def _notify_all(self, token: dict[str, str]) -> None:
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

    def __enter__(self: Self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: types.TracebackType | None,
    ) -> None:
        self.stop()
