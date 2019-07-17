# -*- coding: utf-8 -*-
# Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from collections import defaultdict

logger = logging.getLogger(__name__)


class Pubsub(object):
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._exception_handler = self.default_exception_handler

    def default_exception_handler(self, _, __, exception):
        logger.exception(exception)

    def set_exception_handler(self, exception_handler):
        '''Expected handler interface: handler(listener, message, exception)'''
        self._exception_handler = exception_handler

    def subscribe(self, topic, callback):
        logger.debug('Subscribing callback "%s" to topic "%s"', callback, topic)
        self._subscribers[topic].append(callback)

    def publish(self, topic, message):
        logger.debug('Publishing to topic "%s": "%s"', topic, message)
        for callback in self._subscribers[topic]:
            self.publish_one(callback, message)

    def publish_one(self, callback, message):
        logger.debug('Publishing to callback "%s": "%s"', callback, message)
        try:
            callback(message)
        except Exception as e:
            logger.debug(
                'Publishing failed. Running exception handler "%s"',
                self._exception_handler,
            )
            self._exception_handler(callback, message, e)

    def unsubscribe(self, topic, callback):
        logger.debug('Unsubscribing callback "%s" to topic "%s"', callback, topic)
        try:
            self._subscribers[topic].remove(callback)
        except ValueError:
            pass

        if not self._subscribers[topic]:
            self._subscribers.pop(topic, None)
