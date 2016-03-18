# -*- coding: utf-8 -*-

# Copyright (C) 2007-2016 Avencall
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

from collections import defaultdict

logger = logging.getLogger(__name__)


class Pubsub(object):
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, topic, callback):
        self._subscribers[topic].append(callback)

    def publish(self, topic, message):
        for callback in self._subscribers[topic]:
            self.publish_one(callback, message)

    def publish_one(self, callback, message):
        callback(message)

    def unsubscribe(self, topic, callback):
        try:
            self._subscribers[topic].remove(callback)
        except ValueError:
            pass

        if not self._subscribers[topic]:
            self._subscribers.pop(topic, None)


class ExceptionLoggingPubsub(Pubsub):
    def publish_one(self, callback, message):
        try:
            callback(message)
        except Exception as e:
            logger.exception(e)
