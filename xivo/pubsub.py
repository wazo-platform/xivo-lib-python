# Copyright 2007-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import threading
import uuid
from collections import defaultdict
from functools import partial
from typing import Any, Callable, DefaultDict, Union

logger = logging.getLogger(__name__)

Callback = Callable[[Union[str, None]], None]
ExceptionHandler = Callable[[Callback, Union[str, None], Exception], None]


class Pubsub:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, list[Callback]] = defaultdict(list)
        self._exception_handler: ExceptionHandler = self.default_exception_handler

    def default_exception_handler(
        self, _: Callback, __: str | None, exception: Exception
    ) -> None:
        logger.exception(exception)

    def set_exception_handler(self, exception_handler: ExceptionHandler) -> None:
        """Expected handler interface: handler(listener, message, exception)"""
        self._exception_handler = exception_handler

    def subscribe(self, topic: str, callback: Callback) -> None:
        logger.debug('Subscribing callback "%s" to topic "%s"', callback, topic)
        self._subscribers[topic].append(callback)

    def publish(self, topic: str, message: str | None) -> None:
        logger.debug('Publishing to topic "%s": "%s"', topic, message)
        for callback in self._subscribers[topic]:
            self.publish_one(callback, message)

    def publish_one(self, callback: Callback, message: str | None) -> None:
        logger.debug('Publishing to callback "%s": "%s"', callback, message)
        try:
            callback(message)
        except Exception as e:
            logger.debug(
                'Publishing failed. Running exception handler "%s"',
                self._exception_handler,
            )
            self._exception_handler(callback, message, e)

    def unsubscribe(self, topic: str, callback: Callback) -> None:
        logger.debug('Unsubscribing callback "%s" to topic "%s"', callback, topic)
        try:
            self._subscribers[topic].remove(callback)
        except ValueError:
            pass

        if not self._subscribers[topic]:
            self._subscribers.pop(topic, None)


class CallbackCollector:
    _TOPIC = 'callback-collector'

    def __init__(self) -> None:
        self._pubsub = Pubsub()
        self._sources: set[uuid.UUID] = set()
        self._lock = threading.Lock()

    def _collect(self, source_id: uuid.UUID, *args: Any, **kwargs: Any) -> None:
        logger.debug('Collecting callback source "%s"', source_id)
        if not self._sources:
            logger.debug('Aborting collect')
            return

        with self._lock:
            self._sources.discard(source_id)
            if not self._sources:
                logger.debug('Collecting callbacks finished, publishing')
                self._publish()

    def _publish(self) -> None:
        self._pubsub.publish(self._TOPIC, message=None)

    def new_source(self) -> Callable[..., None]:
        source_id = uuid.uuid4()
        logger.debug('Creating new callback source "%s"', source_id)
        self._sources.add(source_id)
        return partial(self._collect, source_id)

    def subscribe(self, callback: Callable[[], None]) -> None:
        self._pubsub.subscribe(self._TOPIC, lambda arg: callback())
